"""
Knowledge Job Service.

This service handles business logic for knowledge processing jobs,
delegating data access to DAOs.
"""

from datetime import datetime
from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.document_splitter import SplitterType
from datapilotflow.domain.knowledge.job_timeline import JobTimeline, JobTimelineCreate
from datapilotflow.domain.knowledge.knowledge_job import (
    JobStatus,
    KnowledgeJob,
    KnowledgeJobCreate,
    KnowledgeJobExpanded,
    KnowledgeJobUpdate,
)
from datapilotflow.domain.knowledge.vectordb_collection import (
    VectorDBCollectionCreate,
    VectorDBCollectionUpdate,
)
from datapilotflow.persistence.dao.knowledge_job_dao import KnowledgeJobDAO
from datapilotflow.persistence.dao.job_timeline_dao import JobTimelineDAO
from datapilotflow.services.knowledge.document_splitter_service import (
    get_document_splitter_service,
)
from datapilotflow.services.knowledge.knowledge_source_service import get_knowledge_source_service
from datapilotflow.services.knowledge.vectordb_collection_service import (
    get_vectordb_collection_service,
)


class KnowledgeJobService:
    """Service for managing knowledge processing jobs."""

    def __init__(self):
        self.knowledge_job_dao = KnowledgeJobDAO()
        self.knowledge_source_service = get_knowledge_source_service()
        self.vectordb_collection_service = get_vectordb_collection_service()
        self.document_splitter_service = get_document_splitter_service()
        self.job_timeline_dao = JobTimelineDAO()

    def create_knowledge_job(
        self, config_id: str, user_id: str, job_data: KnowledgeJobCreate
    ) -> Optional[KnowledgeJob]:
        """Create a new knowledge processing job from a configuration."""

        # Get the knowledge source configuration
        config = self.knowledge_source_service.get_knowledge_source_config(
            config_id, user_id
        )
        if not config:
            return None

        # Handle VectorDB Collection configuration
        if job_data.existing_collection_id:
            # Use existing collection
            vectordb_collection = self.vectordb_collection_service.get_collection(
                job_data.existing_collection_id, user_id
            )
            if not vectordb_collection:
                raise ValueError("Existing vector DB collection not found")
        else:
            # Create new collection
            if not all(
                [
                    job_data.embedding_model_provider_id,
                    job_data.embedding_model_name,
                    job_data.vector_dimension,
                    job_data.collection_name,
                ]
            ):
                raise ValueError(
                    "Missing required fields for creating new vector DB collection"
                )

            vectordb_collection_data = VectorDBCollectionCreate(
                description=job_data.vectordb_collection_description,
                embedding_model_provider_id=job_data.embedding_model_provider_id,
                embedding_model_name=job_data.embedding_model_name,
                vector_dimension=job_data.vector_dimension,
                collection_name=job_data.collection_name,
            )

            vectordb_collection = self.vectordb_collection_service.create_collection(
                vectordb_collection_data, user_id
            )
            if not vectordb_collection:
                raise ValueError("Failed to create vector DB collection configuration")

        # Handle Document Splitter configuration
        if job_data.splitter_id:
            # Use existing splitter
            splitter = self.document_splitter_service.get_splitter_by_id(
                job_data.splitter_id
            )
            if not splitter:
                raise ValueError(f"Document splitter not found: {job_data.splitter_id}")

            splitter_id = job_data.splitter_id

            # Additional validation for text splitters
            if splitter.splitter_type == SplitterType.TEXT:
                # Use custom values if provided, otherwise use splitter defaults
                chunk_size = job_data.custom_chunk_size or splitter.chunk_size or 256
                chunk_overlap = (
                    job_data.custom_chunk_overlap
                    or splitter.get_effective_chunk_overlap()
                )
                self._validate_chunking_config(
                    chunk_size, chunk_overlap, job_data.batch_size
                )
        else:
            # Create new splitter inline
            if not job_data.splitter_name or not job_data.splitter_type:
                raise ValueError(
                    "Either splitter_id OR (splitter_name + splitter_type) must be provided"
                )

            from datapilotflow.domain.knowledge.document_splitter import DocumentSplitterCreate

            # Map string to SplitterType enum (already imported at module level)
            try:
                splitter_type_enum = SplitterType(job_data.splitter_type.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid splitter_type: {job_data.splitter_type}. Must be 'text' or 'document'"
                )

            # Create splitter configuration
            splitter_data = DocumentSplitterCreate(
                name=job_data.splitter_name,
                description=job_data.splitter_description,
                splitter_type=splitter_type_enum,
                chunk_size=(
                    job_data.custom_chunk_size
                    if splitter_type_enum == SplitterType.TEXT
                    else None
                ),
                chunk_overlap=(
                    job_data.custom_chunk_overlap
                    if splitter_type_enum == SplitterType.TEXT
                    else None
                ),
            )

            # Create the splitter
            new_splitter = self.document_splitter_service.create_splitter(
                splitter_data, user_id
            )
            if not new_splitter:
                raise ValueError("Failed to create document splitter configuration")

            splitter_id = new_splitter.id

            # Validate chunking config for text splitters
            if splitter_type_enum == SplitterType.TEXT:
                chunk_size = job_data.custom_chunk_size or 256
                chunk_overlap = job_data.custom_chunk_overlap or int(chunk_size * 0.15)
                self._validate_chunking_config(
                    chunk_size, chunk_overlap, job_data.batch_size
                )

        # Update job_data with the splitter_id (either existing or newly created)
        job_data.splitter_id = splitter_id

        # Create the job with the vector DB collection ID and splitter ID
        job_id = self.knowledge_job_dao.create_job(
            job_data, config_id, user_id, vectordb_collection.id
        )
        if not job_id:
            raise ValueError("Failed to create knowledge job")

        # Update job count in the configuration
        now = datetime.utcnow()
        self.knowledge_source_service.knowledge_source_dao.update_job_count(
            config_id, user_id, 1, now
        )

        # Create initial timeline entry with "created" status
        timeline_data = JobTimelineCreate(
            job_id=job_id,
            user_id=user_id,
            status=JobStatus.CREATED,
            documents_processed=0,
            chunks_created=0,
            processing_time_seconds=0,
            triggered_by="job_creation",
        )

        timeline_id = self.job_timeline_dao.create_timeline_entry(
            timeline_data, user_id
        )
        if not timeline_id:
            logger.warning(f"Failed to create timeline entry for job {job_id}")

        # Get and return the created job
        job = self.knowledge_job_dao.get_job(job_id, user_id)
        if not job:
            raise ValueError("Failed to retrieve created job")

        return job

    def get_knowledge_job(self, job_id: str, user_id: str) -> Optional[KnowledgeJob]:
        """Get a knowledge processing job by ID."""
        return self.knowledge_job_dao.get_job(job_id, user_id)

    def get_knowledge_job_expanded(
        self, job_id: str, user_id: str, expand: Optional[List[str]] = None
    ) -> Optional[KnowledgeJobExpanded]:
        """Get a knowledge processing job with expanded related data.

        Args:
            job_id: The job ID
            user_id: The user ID
            expand: List of related data to expand (e.g., ['timeline', 'document_splitter', 'vectordb_collection'])
        """
        # Get the base job
        job = self.knowledge_job_dao.get_job(job_id, user_id)
        if not job:
            return None

        # Convert to expanded model
        expanded_job = KnowledgeJobExpanded(**job.model_dump())

        if not expand:
            return expanded_job

        # Expand related data based on query parameters
        if "knowledge_source_config" in expand:
            from datapilotflow.services.knowledge.knowledge_source_service import (
                get_knowledge_source_service,
            )

            source_service = get_knowledge_source_service()
            source_config = source_service.get_knowledge_source_config(
                job.knowledge_source_config_id, user_id
            )
            if source_config:
                expanded_job.knowledge_source_config = source_config.model_dump()

        if "vectordb_collection" in expand:
            collection = self.vectordb_collection_service.get_collection(
                job.vectordb_collection_id, user_id
            )
            if collection:
                expanded_job.vectordb_collection = collection.model_dump()

        if "document_splitter" in expand and job.splitter_id:
            splitter = self.document_splitter_service.get_splitter_by_id(
                job.splitter_id
            )
            if splitter:
                expanded_job.document_splitter = splitter.model_dump()

        if "timeline" in expand:
            from datapilotflow.services.knowledge.job_timeline_service import (
                get_job_timeline_service,
            )

            timeline_service = get_job_timeline_service()
            timeline_entries = timeline_service.get_timeline_entries(job_id, user_id)
            if timeline_entries:
                expanded_job.timeline = [
                    entry.model_dump() for entry in timeline_entries
                ]

        if "execution_stats" in expand:
            # Calculate execution statistics
            from datapilotflow.persistence.dao.job_timeline_dao import JobTimelineDAO

            timeline_dao = JobTimelineDAO()
            latest_timeline = timeline_dao.get_latest_timeline_entry(job_id, user_id)

            stats = {
                "total_documents_processed": 0,
                "total_chunks_created": 0,
                "last_execution": None,
                "average_processing_time": None,
            }

            if latest_timeline:
                stats.update(
                    {
                        "total_documents_processed": latest_timeline.documents_processed
                        or 0,
                        "total_chunks_created": latest_timeline.chunks_created or 0,
                        "last_execution": (
                            latest_timeline.created_at.isoformat()
                            if latest_timeline.created_at
                            else None
                        ),
                        "average_processing_time": latest_timeline.processing_time_seconds,
                    }
                )

            expanded_job.execution_stats = stats

        return expanded_job

    def list_knowledge_jobs(
        self,
        user_id: str,
        config_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[KnowledgeJob]:
        """List knowledge processing jobs for a user."""
        return self.knowledge_job_dao.list_jobs(user_id, config_id, None, skip, limit)

    def update_knowledge_job(
        self, job_id: str, user_id: str, update_data: KnowledgeJobUpdate
    ) -> Optional[KnowledgeJob]:
        """Update a knowledge processing job."""
        # Get the current job to access the vector DB collection ID
        current_job = self.knowledge_job_dao.get_job(job_id, user_id)
        if not current_job:
            return None

        # Get the current collection to check if collection_name is changing
        current_collection = self.vectordb_collection_service.get_collection(
            current_job.vectordb_collection_id, user_id
        )
        if not current_collection:
            logger.error(
                f"Current collection {current_job.vectordb_collection_id} not found for job {job_id}"
            )
            raise ValueError("Current vector DB collection not found")

        # Check if collection_name is changing
        collection_name_changed = (
            hasattr(update_data, "collection_name")
            and update_data.collection_name is not None
            and update_data.collection_name != current_collection.collection_name
        )

        new_collection_id = None

        if collection_name_changed:
            # CRITICAL: If collection_name is changing, CREATE A NEW COLLECTION
            # Do NOT update the existing collection (other jobs might be using it!)
            logger.info(
                f"Collection name changing from '{current_collection.collection_name}' to '{update_data.collection_name}' "
                f"- creating NEW collection instead of updating existing one"
            )

            # Build new collection data
            new_collection_data = VectorDBCollectionCreate(
                collection_name=update_data.collection_name,
                description=update_data.vectordb_collection_description
                or current_collection.description,
                embedding_model_provider_id=update_data.embedding_model_provider_id
                or current_collection.embedding_model_provider_id,
                embedding_model_name=update_data.embedding_model_name
                or current_collection.embedding_model_name,
                vector_dimension=update_data.vector_dimension
                or current_collection.vector_dimension,
            )

            # Create new collection
            new_collection = self.vectordb_collection_service.create_collection(
                new_collection_data, user_id
            )
            if not new_collection:
                raise ValueError("Failed to create new vector DB collection")

            new_collection_id = new_collection.id
            logger.info(
                f"Created new collection {new_collection_id} with name '{update_data.collection_name}'"
            )

        else:
            # Collection name NOT changing - safe to update existing collection
            vectordb_update_fields = [
                "vectordb_collection_description",
                "embedding_model_provider_id",
                "embedding_model_name",
                "vector_dimension",
            ]

            vectordb_update_data = {}
            for field in vectordb_update_fields:
                if (
                    hasattr(update_data, field)
                    and getattr(update_data, field) is not None
                ):
                    vectordb_update_data[field] = getattr(update_data, field)

            if vectordb_update_data:
                logger.info(
                    f"Updating existing collection {current_job.vectordb_collection_id} "
                    f"(collection name unchanged: '{current_collection.collection_name}')"
                )

                # Create VectorDBCollectionUpdate object
                vectordb_collection_update = VectorDBCollectionUpdate(
                    **vectordb_update_data
                )

                # Update the existing vector DB collection
                updated_collection = self.vectordb_collection_service.update_collection(
                    current_job.vectordb_collection_id,
                    user_id,
                    vectordb_collection_update,
                )
                if not updated_collection:
                    raise ValueError(
                        "Failed to update vector DB collection configuration"
                    )

        # If new collection was created, update the job to point to it
        if new_collection_id:
            # Create a modified update_data with new collection ID
            job_update_dict = update_data.dict(exclude_unset=True)
            job_update_dict["vectordb_collection_id"] = new_collection_id
            job_update_data = KnowledgeJobUpdate(**job_update_dict)
            logger.info(
                f"Updating job {job_id} to use new collection {new_collection_id}"
            )
        else:
            job_update_data = update_data

        return self.knowledge_job_dao.update_job(job_id, user_id, job_update_data)

    def delete_knowledge_job(self, job_id: str, user_id: str) -> bool:
        """Delete a knowledge processing job."""
        return self.knowledge_job_dao.delete_job(job_id, user_id)

    def execute_knowledge_job(
        self, job_id: str, user_id: str
    ) -> Optional[KnowledgeJob]:
        """Execute a knowledge processing job with job-specific chunking parameters."""
        try:
            # Get the job
            job = self.get_knowledge_job(job_id, user_id)
            if not job:
                raise ValueError(f"Knowledge job {job_id} not found")

            # Check the latest timeline entry status
            latest_timeline = self.job_timeline_dao.get_latest_timeline_entry(
                job_id, user_id
            )
            if latest_timeline and latest_timeline.status == JobStatus.RUNNING:
                raise ValueError(f"Job {job_id} is already running")

            # Create a new timeline entry for this execution
            timeline_data = JobTimelineCreate(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow().isoformat(),
                documents_processed=0,
                chunks_created=0,
                processing_time_seconds=0,
                triggered_by="job_execution",
            )

            timeline_id = self.job_timeline_dao.create_timeline_entry(
                timeline_data, user_id
            )
            if not timeline_id:
                raise ValueError(f"Failed to create timeline entry for job {job_id}")

            try:
                # Get the splitter configuration for this job
                splitter_config = self.document_splitter_service.get_splitter_for_job(
                    job.splitter_id
                )

                # Apply job overrides to splitter configuration
                if job.custom_chunk_size:
                    splitter_config.chunk_size = job.custom_chunk_size
                if job.custom_chunk_overlap:
                    splitter_config.chunk_overlap = job.custom_chunk_overlap

                # Create splitter using the new modular system
                from datapilotflow.processors.splitters import create_splitter

                splitter = create_splitter(splitter_config)

                custom_note = ""
                if job.custom_chunk_size or job.custom_chunk_overlap:
                    custom_note = " (custom values)"

                logger.info(
                    f"Executing job {job_id} with {splitter_config.splitter_type.value} splitter '{splitter_config.name}'{custom_note}: batch_size={job.batch_size}"
                )

                # TODO: Implement the actual job execution logic here
                # This would involve:
                # 1. Using the knowledge_source_config to crawl/extract content
                # 2. Using the custom splitter to chunk the content
                # 3. Using the embedding_model_provider_id and embedding_model_name for embeddings
                #    Note: Access embedding config via provider.embedding.config
                # 4. Using batch_size for processing documents in batches
                # 5. Storing the results in the vector database

                # Update timeline entry to completed
                self.job_timeline_dao.update_timeline_entry(
                    timeline_id,
                    user_id,
                    {
                        "status": JobStatus.COMPLETED,
                        "completed_at": datetime.utcnow().isoformat(),
                        "documents_processed": 0,  # TODO: Update with actual count
                        "chunks_created": 0,  # TODO: Update with actual count
                        "processing_time_seconds": 0,  # TODO: Calculate actual time
                    },
                )

                return self.get_knowledge_job(job_id, user_id)

            except Exception as e:
                logger.error(f"Error executing job {job_id}: {e}")
                # Update timeline entry to failed
                self.job_timeline_dao.update_timeline_entry(
                    timeline_id,
                    user_id,
                    {
                        "status": JobStatus.FAILED,
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": str(e),
                        "processing_time_seconds": 0,  # TODO: Calculate actual time
                    },
                )
                raise

        except Exception as e:
            logger.error(f"Error in execute_knowledge_job: {e}")
            raise

    def _validate_embedding_model(
        self, provider_id: str, model_name: str, user_id: str
    ) -> None:
        """Validate that the embedding model provider exists and supports the specified model."""
        try:
            from datapilotflow.services.model_provider.model_provider_service import (
                get_model_provider_service,
            )

            model_provider_service = get_model_provider_service()
            provider = model_provider_service.get_model_provider(provider_id, user_id)

            if not provider:
                raise ValueError(f"Model provider with ID {provider_id} not found")

            if not provider.is_active:
                raise ValueError(f"Model provider {provider.name} is not active")

            # Check if provider supports embedding models
            if provider.embedding is None:
                raise ValueError(
                    f"Model provider {provider.name} does not support embedding models"
                )

            # Check if the specific model is supported
            if model_name not in provider.embedding.models:
                raise ValueError(
                    f"Model {model_name} is not supported by provider {provider.name}. Available models: {provider.embedding.models}"
                )

        except ImportError:
            raise ValueError("Model provider service not available")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Error validating embedding model: {str(e)}")

    def _validate_chunking_config(
        self, chunk_size: int, chunk_overlap: int, batch_size: int
    ) -> None:
        """Validate chunking configuration parameters."""
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")

        if chunk_size < 64:
            raise ValueError("Chunk size must be at least 64 tokens")

        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")

        if chunk_overlap > (chunk_size / 2):
            raise ValueError(
                f"Chunk overlap ({chunk_overlap}) cannot exceed 50% of chunk size ({chunk_size})"
            )

        # Note: Upper limit validation for chunk_size should be done against the embedding model's
        # max_input_tokens, which is validated at the frontend and should be checked during job execution

        if batch_size < 1:
            raise ValueError("Batch size must be at least 1")

        if batch_size > 1000:
            raise ValueError("Batch size cannot exceed 1000")


# Global service instance
_knowledge_job_service: Optional[KnowledgeJobService] = None


def get_knowledge_job_service() -> KnowledgeJobService:
    """Get the global knowledge job service instance."""
    global _knowledge_job_service

    if _knowledge_job_service is None:
        _knowledge_job_service = KnowledgeJobService()

    return _knowledge_job_service
