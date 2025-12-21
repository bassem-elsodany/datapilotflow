"""
Job Processor for Knowledge Processing Jobs.

This module provides a dedicated processor for handling knowledge processing jobs
in the event-driven architecture, optimized for job-specific configurations.
"""

import asyncio
import signal
import sys
import time
import traceback
from typing import Any, Dict, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from datapilotflow.infrastructure.vectordb.processor import (
    MilvusProcessor,
    create_milvus_processor,
)
from datapilotflow.domain.knowledge.knowledge_job import JobStatus, KnowledgeJob
from datapilotflow.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig
from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
from datapilotflow.processors.document.web_document_processor import (
    extract_with_batch_processing_callback,
)
from datapilotflow.services.knowledge.vectordb_collection_service import (
    get_vectordb_collection_service,
)


class KnowledgeJobProcessor:
    """
    Dedicated processor for knowledge processing jobs.

    This class handles the complete job processing pipeline:
    1. Document extraction from knowledge sources
    2. Document chunking with job-specific settings
    3. Vector embedding and storage
    4. Progress tracking and status updates
    """

    def __init__(self):
        """Initialize the job processor."""
        self._cancellation_requested = False
        self._current_job_id = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful job cancellation."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, requesting job cancellation...")
            self._cancellation_requested = True
            if self._current_job_id:
                logger.info(f"Cancellation requested for job {self._current_job_id}")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _check_cancellation(self):
        """Check if job cancellation has been requested."""
        if self._cancellation_requested:
            raise InterruptedError("Job cancellation requested")

    def _update_job_status_to_cancelled(self, job_id: str, user_id: str):
        """Update job status to cancelled in the database."""
        try:
            from datetime import datetime

            from datapilotflow.domain.knowledge.knowledge_job import JobStatus
            from datapilotflow.infrastructure.dao.knowledge import JobTimelineDAO

            timeline_dao = JobTimelineDAO()

            # Create a cancelled timeline entry
            timeline_data = {
                "job_id": job_id,
                "user_id": user_id,
                "status": JobStatus.CANCELLED,
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": "Job was cancelled by user",
                "triggered_by": "cancellation",
            }

            timeline_dao.create_timeline_entry(timeline_data, user_id)
            logger.info(f"Updated job {job_id} status to cancelled")

        except Exception as e:
            logger.error(f"Failed to update job {job_id} status to cancelled: {e}")

    async def _generate_embeddings_for_chunks(
        self,
        knowledge_chunks: list[KnowledgeChunk],
        provider_id: str,
        model_name: str,
        user_id: str,
    ) -> list[list[float]]:
        """
        Generate embeddings for knowledge chunks using the specified model provider.

        Args:
            knowledge_chunks: List of knowledge chunks to generate embeddings for
            provider_id: ID of the model provider to use
            model_name: Name of the embedding model to use
            user_id: ID of the user who owns the model provider

        Returns:
            List of embedding vectors for each chunk
        """
        try:
            # Import here to avoid circular imports
            from datapilotflow.services.model_provider.model_provider_service import (
                ModelProviderService,
            )

            # Get the model provider
            model_provider_service = ModelProviderService()
            provider = model_provider_service.get_model_provider(provider_id, user_id)

            if not provider:
                raise ValueError(f"Model provider with ID {provider_id} not found")

            # Debug: Check the type of provider
            logger.debug(f"Provider type: {type(provider)}")
            logger.debug(f"Provider: {provider}")

            # If provider is a dict, convert it to ModelProvider object
            if isinstance(provider, dict):
                from datapilotflow.domain.model_provider.model_provider import ModelProvider

                provider = ModelProvider.model_validate(provider)

            if not provider.embedding:
                raise ValueError(
                    f"Model provider {provider.name} does not support embedding models"
                )

            if model_name not in provider.embedding.models:
                raise ValueError(
                    f"Model {model_name} not available in provider {provider.name}. Available models: {provider.embedding.models}"
                )

            # Generate actual embeddings using LiteLLM
            vectors = self._generate_embeddings_with_litellm(
                knowledge_chunks, provider, model_name
            )

            logger.info(
                f"Generated {len(vectors)} embeddings using provider {provider.name} "
                f"with model {model_name} (dimension: {len(vectors[0]) if vectors else 0})"
            )

            return vectors

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't use fallback vectors - this is a critical error that should fail the job
            raise ValueError(f"Critical error: Failed to generate embeddings: {e}")

    def _generate_embeddings_for_chunks_sync(
        self,
        knowledge_chunks: list[KnowledgeChunk],
        provider_id: str,
        model_name: str,
        user_id: str,
        vector_dimension: int = None,
    ) -> list[list[float]]:
        """
        Generate embeddings for knowledge chunks using the specified model provider (synchronous version).

        Args:
            knowledge_chunks: List of knowledge chunks to generate embeddings for
            provider_id: ID of the model provider to use
            model_name: Name of the embedding model to use
            user_id: ID of the user who owns the model provider
            vector_dimension: Optional dimension for the embeddings

        Returns:
            List of embedding vectors for each chunk
        """
        try:
            # Import here to avoid circular imports
            from datapilotflow.services.model_provider.model_provider_service import (
                ModelProviderService,
            )

            # Get the model provider
            model_provider_service = ModelProviderService()
            provider = model_provider_service.get_model_provider(provider_id, user_id)

            if not provider:
                raise ValueError(f"Model provider with ID {provider_id} not found")

            # If provider is a dict, convert it to ModelProvider object
            if isinstance(provider, dict):
                from datapilotflow.domain.model_provider.model_provider import ModelProvider

                provider = ModelProvider.model_validate(provider)

            if not provider.embedding:
                raise ValueError(
                    f"Model provider {provider.name} does not support embedding models"
                )

            if model_name not in provider.embedding.models:
                raise ValueError(
                    f"Model {model_name} not available in provider {provider.name}. Available models: {provider.embedding.models}"
                )

            # Generate actual embeddings using LiteLLM
            vectors = self._generate_embeddings_with_litellm(
                knowledge_chunks, provider, model_name
            )

            logger.debug(
                f"Generated {len(vectors)} embeddings using provider {provider.name} "
                f"with model {model_name} (dimension: {len(vectors[0]) if vectors else 0})"
            )

            return vectors

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't use fallback vectors - this is a critical error that should fail the job
            raise ValueError(f"Critical error: Failed to generate embeddings: {e}")

    def _generate_embeddings_with_litellm(
        self,
        knowledge_chunks: list[KnowledgeChunk],
        provider,
        model_name: str,
        vector_dimension: int = None,
    ) -> list[list[float]]:
        """
        Generate embeddings using LiteLLM with the specified model provider.

        Args:
            knowledge_chunks: List of knowledge chunks to generate embeddings for
            provider: Model provider configuration
            model_name: Name of the embedding model to use
            vector_dimension: Optional dimension for the embeddings

        Returns:
            List of embedding vectors for each chunk
        """
        try:
            import litellm

            # Get API key from user's model provider configuration
            if not provider.api_key:
                raise ValueError(
                    f"No API key configured for provider: {provider.name}. Please set the API key in your model provider configuration."
                )

            api_key = provider.api_key

            # Prepare texts for embedding and validate content
            texts = [chunk.page_content for chunk in knowledge_chunks]

            # Filter out empty or invalid content
            valid_texts = []
            valid_chunks = []
            for i, text in enumerate(texts):
                if text and text.strip() and len(text.strip()) > 0:
                    valid_texts.append(text)
                    valid_chunks.append(knowledge_chunks[i])
                else:
                    logger.warning(
                        f"Skipping empty or invalid content for chunk {i}: '{text[:50]}...' (length: {len(text)})"
                    )

            # If no valid content, return empty vectors and log the issue
            if not valid_texts:
                logger.warning(
                    "No valid content found for embedding generation - all chunks are empty or invalid"
                )
                return []

            # Configure LiteLLM parameters with valid texts only
            litellm_params = {
                "model": f"{provider.provider_type}/{model_name}",
                "input": valid_texts,
            }

            # Add API key if required
            if api_key:
                litellm_params["api_key"] = api_key

            # Add custom endpoint if provided
            if provider.endpoint:
                litellm_params["api_base"] = provider.endpoint

            # Add timeout from provider configuration
            if provider.timeout:
                litellm_params["timeout"] = provider.timeout

            # Add any additional configuration from provider
            if provider.embedding.config:
                litellm_params.update(provider.embedding.config)

            # Add dimensions parameter if provided
            if vector_dimension:
                litellm_params["dimensions"] = vector_dimension

            # Generate embeddings using LiteLLM
            response = litellm.embedding(**litellm_params)

            # Extract embeddings from response
            if hasattr(response, "data") and response.data:
                # Handle both object and dict responses from LiteLLM
                vectors = []
                for item in response.data:
                    if hasattr(item, "embedding"):
                        vectors.append(item.embedding)
                    elif isinstance(item, dict) and "embedding" in item:
                        vectors.append(item["embedding"])
                    else:
                        logger.error(
                            f"Unexpected response item format: {type(item)} - {item}"
                        )
                        raise ValueError(
                            f"Unexpected response item format: {type(item)}"
                        )

                logger.debug(f"Successfully generated {len(vectors)} embeddings")
                return vectors
            else:
                raise ValueError("No embedding data received from LiteLLM response")

        except Exception as e:
            logger.error(f"LiteLLM embedding generation failed: {e}")
            raise e

    async def process_job(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        status_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Process a knowledge processing job.

        Args:
            knowledge_job: The knowledge processing job to execute
            knowledge_source_config: The knowledge source configuration
            status_callback: Optional callback for status updates

        Returns:
            Dictionary containing processing results and statistics
        """
        try:
            logger.debug(f"Starting job processing for job {knowledge_job.id}")
            self._current_job_id = knowledge_job.id
            self._cancellation_requested = False  # Reset cancellation flag
            start_time = time.time()  # Track processing start time

            # Check for cancellation before starting
            self._check_cancellation()

            # Get splitter configuration from job
            from datapilotflow.processors.splitters import create_splitter
            from datapilotflow.services.knowledge.document_splitter_service import (
                get_document_splitter_service,
            )

            if not knowledge_job.splitter_id:
                raise ValueError(
                    f"Job {knowledge_job.id} has no splitter_id configured"
                )

            # Get the splitter configuration from the job
            splitter_service = get_document_splitter_service()
            splitter_config = splitter_service.get_splitter_for_job(
                knowledge_job.splitter_id
            )

            # Create splitter using the new modular system
            splitter = create_splitter(splitter_config)

            logger.info(
                f"Using splitter '{splitter_config.name}' (type: {splitter_config.splitter_type}) for job {knowledge_job.id}"
            )

            # Create Milvus processor for this job
            milvus_processor = self._create_milvus_processor(
                knowledge_job=knowledge_job
            )

            # Process the knowledge source
            results = await self._process_knowledge_source(
                knowledge_job=knowledge_job,
                knowledge_source_config=knowledge_source_config,
                splitter=splitter,
                milvus_processor=milvus_processor,
                status_callback=status_callback,
                start_time=start_time,
            )

            logger.debug(f"Job {knowledge_job.id} completed successfully")
            return results

        except InterruptedError as e:
            logger.info(f"Job {knowledge_job.id} was cancelled: {e}")
            # Update job status to cancelled
            self._update_job_status_to_cancelled(
                knowledge_job.id, knowledge_job.user_id
            )
            raise
        except Exception as e:
            logger.error(f"Error processing job {knowledge_job.id}: {e}")
            raise
        finally:
            # Clear current job ID
            self._current_job_id = None

    def _load_chunk_configuration(self, knowledge_job: KnowledgeJob) -> tuple[int, int]:
        """
        Load chunk configuration from VectorDB collection.

        Args:
            knowledge_job: The knowledge job to get chunk configuration for

        Returns:
            Tuple of (chunk_size, chunk_overlap)
        """
        try:
            logger.info(
                f"CHUNK CONFIG DEBUG - Loading config for job {knowledge_job.id}, collection {knowledge_job.vectordb_collection_id}, user {knowledge_job.user_id}"
            )
            vectordb_collection_service = get_vectordb_collection_service()
            vectordb_collection = vectordb_collection_service.get_collection(
                knowledge_job.vectordb_collection_id, knowledge_job.user_id
            )

            if vectordb_collection:
                chunk_size = vectordb_collection.chunk_size
                chunk_overlap = vectordb_collection.chunk_overlap
                logger.info(
                    f"CHUNK CONFIG LOADED - Collection: {vectordb_collection.collection_name}, size: {chunk_size}, overlap: {chunk_overlap}"
                )
                return chunk_size, chunk_overlap
            else:
                logger.warning(
                    f"CHUNK CONFIG ERROR - VectorDB collection {knowledge_job.vectordb_collection_id} not found, using defaults"
                )
                return 256, 32  # Default values
        except Exception as e:
            logger.error(f"Error loading chunk configuration: {e}")
            logger.debug("Using default chunk configuration")
            return 256, 32  # Default values

    def _create_milvus_processor(self, knowledge_job: KnowledgeJob) -> MilvusProcessor:
        """
        Create a Milvus processor for the job.

        Args:
            knowledge_job: The knowledge processing job

        Returns:
            Configured MilvusProcessor
        """
        # Get the VectorDB collection to retrieve the collection name
        vectordb_collection_service = get_vectordb_collection_service()
        vectordb_collection = vectordb_collection_service.get_collection(
            knowledge_job.vectordb_collection_id, knowledge_job.user_id
        )

        if not vectordb_collection:
            raise ValueError(
                f"VectorDB collection {knowledge_job.vectordb_collection_id} not found"
            )

        return create_milvus_processor(
            milvus_model=KnowledgeChunk,  # Use generic KnowledgeChunk model
            milvus_collection_name=vectordb_collection.collection_name,
            vector_dimension=vectordb_collection.vector_dimension,
        )

    async def _process_knowledge_source(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        splitter: RecursiveCharacterTextSplitter,
        milvus_processor: MilvusProcessor,
        status_callback: Optional[callable] = None,
        start_time: float = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> Dict[str, Any]:
        """
        Process a knowledge source and store documents.

        Args:
            knowledge_job: The knowledge processing job
            knowledge_source_config: The knowledge source configuration
            splitter: Text splitter for document chunking
            milvus_processor: Milvus processor for storage
            status_callback: Optional callback for status updates

        Returns:
            Dictionary containing processing results
        """
        try:
            logger.info(
                f"Job {knowledge_job.id} clear_collection_before_start flag: {knowledge_job.clear_collection_before_start}"
            )
            if knowledge_job.clear_collection_before_start:
                # Clear existing data for this job
                logger.info(
                    f"Job {knowledge_job.id}: Clearing existing data from collection before starting..."
                )
                if status_callback:
                    status_callback("Clearing existing data...")

                try:
                    # Get collection stats before clearing
                    stats_before = milvus_processor.get_statistics()
                    logger.info(
                        f"Job {knowledge_job.id}: Collection stats BEFORE clearing: {stats_before}"
                    )

                    # Clear the collection
                    milvus_processor.clear_all()

                    # Get collection stats after clearing to verify
                    stats_after = milvus_processor.get_statistics()
                    logger.info(
                        f"Job {knowledge_job.id}: Collection stats AFTER clearing: {stats_after}"
                    )
                    logger.info(
                        f"Job {knowledge_job.id}: Collection cleared successfully - verified empty"
                    )

                except Exception as clear_error:
                    logger.error(
                        f"Job {knowledge_job.id}: CRITICAL - Failed to clear collection: {clear_error}"
                    )
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise Exception(
                        f"Failed to clear collection before job execution: {clear_error}"
                    )
            else:
                logger.info(
                    f"Job {knowledge_job.id}: Skipping collection clear (flag is False)"
                )

            # Track processing statistics
            stats = {
                "job_id": knowledge_job.id,
                "config_name": knowledge_source_config.name,
                "total_documents": 0,
                "total_chunks": 0,
                "processing_time": 0,
                "errors": [],
            }

            # Process documents with batch callback
            def batch_callback(client, batch, batch_number, total_processed):
                """Handle each batch of processed documents."""
                try:
                    # Check for cancellation before processing each batch
                    self._check_cancellation()

                    # Documents are already chunked by the base processor, no need to split again
                    chunks = batch

                    # Convert chunks to KnowledgeChunk objects
                    knowledge_chunks = []
                    for i, chunk in enumerate(chunks):
                        knowledge_chunk = KnowledgeChunk(
                            page_content=chunk.page_content,
                            source_url=chunk.metadata.get("source_url", ""),
                            job_id=knowledge_job.id,  # Add job_id to track which job created this chunk
                            knowledge_source=knowledge_source_config.name,
                            title=chunk.metadata.get("title", ""),
                            chunk_id=f"{knowledge_source_config.id}_chunk_{batch_number}_{i}",
                            chunk_index=i,
                            total_chunks=len(chunks),
                        )
                        knowledge_chunks.append(knowledge_chunk)

                    # Get the VectorDB collection to retrieve the embedding model information
                    vectordb_collection_service = get_vectordb_collection_service()
                    vectordb_collection = vectordb_collection_service.get_collection(
                        knowledge_job.vectordb_collection_id, knowledge_job.user_id
                    )

                    if not vectordb_collection:
                        raise ValueError(
                            f"VectorDB collection {knowledge_job.vectordb_collection_id} not found"
                        )

                    # Generate embeddings for chunks using the collection's assigned model provider
                    vectors = self._generate_embeddings_for_chunks_sync(
                        knowledge_chunks,
                        vectordb_collection.embedding_model_provider_id,
                        vectordb_collection.embedding_model_name,
                        knowledge_job.user_id,
                        vectordb_collection.vector_dimension,
                    )

                    # Only store chunks in Milvus if we have valid content and vectors
                    if vectors and len(vectors) > 0:
                        milvus_processor.process_documents(knowledge_chunks, vectors)
                        logger.info(
                            f"Successfully stored {len(vectors)} chunks with embeddings in Milvus"
                        )
                    else:
                        logger.warning(
                            "No valid content found for embedding generation - skipping Milvus storage"
                        )
                        # Still update statistics to track that we processed the batch
                        logger.info(
                            f"Processed batch {batch_number} with {len(knowledge_chunks)} chunks (all empty/invalid)"
                        )

                    # Update statistics
                    stats["total_documents"] += len(batch)
                    stats["total_chunks"] += len(knowledge_chunks)

                    # Log progress
                    logger.debug(
                        f"Job {knowledge_job.id}: Processed batch {batch_number} - "
                        f"{len(batch)} docs → {len(knowledge_chunks)} chunks "
                        f"(total: {total_processed} docs)"
                    )

                    # Update status if callback provided
                    if status_callback:
                        # Send detailed batch progress information with CUMULATIVE values
                        batch_info = {
                            "batch_number": batch_number,
                            "total_processed": stats[
                                "total_documents"
                            ],  # CUMULATIVE: total docs processed so far
                            "documents_in_batch": len(batch),  # Current batch only
                            "chunks_created": len(
                                knowledge_chunks
                            ),  # Current batch only
                            "total_chunks": stats[
                                "total_chunks"
                            ],  # CUMULATIVE: total chunks created so far
                            "processing_time": time.time()
                            - (start_time or time.time()),
                        }
                        status_callback(
                            f"Batch {batch_number}: {len(batch)} docs → {len(knowledge_chunks)} chunks (CUMULATIVE: {stats['total_documents']} docs, {stats['total_chunks']} chunks)",
                            batch_info,
                        )

                except Exception as e:
                    error_msg = f"Error processing batch {batch_number}: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    # Re-raise the exception to ensure job status is updated to FAILED
                    raise

            # Extract and process documents
            if status_callback:
                status_callback("Extracting documents from knowledge source...")

            await extract_with_batch_processing_callback(
                knowledge_job=knowledge_job,
                knowledge_source_config=knowledge_source_config,  # Use config directly as it has all crawler settings
                client=milvus_processor,
                batch_callback=batch_callback,
                output_file=None,  # No output file specified for job processing
                check_duplicates=knowledge_job.check_duplicates_before_insert,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            # Calculate total processing time
            total_processing_time = time.time() - (start_time or time.time())
            stats["processing_time_seconds"] = total_processing_time

            # Final status update
            if status_callback:
                status_callback(
                    f"Completed: {stats['total_documents']} documents, {stats['total_chunks']} chunks in {total_processing_time:.1f}s"
                )

            logger.debug(f"Job {knowledge_job.id} processing completed: {stats}")
            return stats

        except Exception as e:
            error_msg = f"Error processing knowledge source: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            raise


# Global instance for reuse
_knowledge_job_processor: Optional[KnowledgeJobProcessor] = None


def get_knowledge_job_processor() -> KnowledgeJobProcessor:
    """Get the global knowledge job processor instance."""
    global _knowledge_job_processor

    if _knowledge_job_processor is None:
        _knowledge_job_processor = KnowledgeJobProcessor()

    return _knowledge_job_processor
