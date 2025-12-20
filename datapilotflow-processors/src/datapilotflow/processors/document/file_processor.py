"""
File processor module that extends the base document processor for file uploads.
This module uses Marker PdfConverter for superior document processing across multiple file types
and integrates with the SkillPilot document processing pipeline.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.documents import Document
from loguru import logger
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

from datapilotflow.domain.knowledge import Knowledge
from datapilotflow.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig

from .base_processor import BaseDocumentProcessor


class FileProcessor(BaseDocumentProcessor):
    """File processor that extends the base document processor for file uploads.

    Uses Marker PdfConverter for superior document processing across multiple file types:
    - PDF, image, PPT, PPTX, DOC, DOCX, XLS, XLSX, HTML, EPUB
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the file processor with Marker PdfConverter.

        Args:
            config: Optional configuration dictionary for Marker
        """
        super().__init__()
        self.processor_type = "file"

        if config is None:
            config = {
                "output_format": "markdown",
                "use_llm": False,
                "force_ocr": False,
                "disable_ocr": True,
                "disable_image_extraction": True,
                "format_lines": True,
                "debug": False,
            }

        try:
            config_parser = ConfigParser(config)
            self._marker_converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
            )
            logger.debug(
                "Marker PdfConverter initialized with OCR disabled by default."
            )
        except ImportError as e:
            logger.error(f"Marker PDF API not available: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ImportError("marker-pdf[full] is required for file processing")

    def _create_fallback_converter(self, config: Dict[str, Any]) -> PdfConverter:
        """Create a fallback converter with OCR disabled to avoid tensor issues."""
        fallback_config = config.copy()
        fallback_config.update(
            {
                "force_ocr": False,
                "disable_ocr": True,  # Disable OCR completely
                "disable_image_extraction": True,
                "use_llm": False,
            }
        )

        try:
            config_parser = ConfigParser(fallback_config)
            return PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
            )
        except Exception as e:
            logger.error(f"Failed to create fallback converter: {e}")
            raise

    def _create_minimal_converter(self) -> PdfConverter:
        """Create a minimal converter with only basic text extraction."""
        minimal_config = {
            "output_format": "markdown",  # Use markdown instead of text
            "use_llm": False,
            "force_ocr": False,
            "disable_ocr": True,
            "disable_image_extraction": True,
            "disable_table_extraction": True,
            "disable_layout_analysis": True,
            "format_lines": False,
            "debug": False,
        }

        try:
            config_parser = ConfigParser(minimal_config)
            return PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
            )
        except Exception as e:
            logger.error(f"Failed to create minimal converter: {e}")
            raise

    def extract_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from a file using appropriate processor based on file type.

        Args:
            file_path: Path to the file to process

        Returns:
            Dict containing extracted text, markdown, tables, layout, and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be processed
        """
        logger.debug(f"Extracting content from file: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = file_path.suffix.lower().lstrip(".")

        # Handle text-based files directly (no need for Marker)
        if file_type in ["txt", "md", "markdown"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                return {
                    "text": content,
                    "markdown": content if file_type in ["md", "markdown"] else content,
                    #'tables': [],
                    #'layout': {},
                    "metadata": {"title": file_path.stem, "file_type": file_type},
                    "processing_info": {
                        "converter_used": "direct_file_read",
                        "file_path": str(file_path),
                        "file_type": file_type,
                    },
                }
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                raise ValueError(f"Failed to read text file {file_path}: {e}")

        # Use Marker for supported file types
        marker_supported_types = [
            "pdf",
            "doc",
            "docx",
            "ppt",
            "pptx",
            "xls",
            "xlsx",
            "html",
            "epub",
            "xml",
        ]
        if file_type in marker_supported_types:
            try:
                result = self._marker_converter(str(file_path))
                # Handle MarkdownOutput object (Pydantic model) - access attributes directly
                return {
                    "text": getattr(result, "text", "") or "",
                    "markdown": getattr(result, "markdown", "") or "",
                    #'tables': getattr(result, 'tables', []) or [],
                    #'layout': getattr(result, 'layout', {}) or {},
                    "metadata": getattr(result, "metadata", {}) or {},
                    "processing_info": {
                        "converter_used": "marker_pdf_universal",
                        "file_path": str(file_path),
                        "file_type": file_type,
                    },
                }
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Primary converter failed for {file_path}: {error_msg}")

                # Check if it's a tensor-related error or segmentation fault
                if (
                    "tensors used as indices" in error_msg
                    or "IndexError" in error_msg
                    or "segmentation fault" in error_msg.lower()
                    or "SIGSEGV" in error_msg
                    or "memory" in error_msg.lower()
                    or "Data format error" in error_msg
                    or "Failed to load document" in error_msg
                ):

                    logger.info(
                        f"Attempting fallback conversion (OCR disabled) for {file_path}"
                    )
                    try:
                        # Create fallback converter with OCR disabled
                        fallback_config = {
                            "output_format": "markdown",
                            "use_llm": False,
                            "force_ocr": False,
                            "disable_ocr": True,  # Disable OCR completely
                            "disable_image_extraction": True,
                            "format_lines": True,
                            "debug": False,
                        }

                        fallback_converter = self._create_fallback_converter(
                            fallback_config
                        )
                        result = fallback_converter(str(file_path))

                        return {
                            "text": getattr(result, "text", "") or "",
                            "markdown": getattr(result, "markdown", "") or "",
                            "metadata": getattr(result, "metadata", {}) or {},
                            "processing_info": {
                                "converter_used": "marker_pdf_fallback_no_ocr",
                                "file_path": str(file_path),
                                "file_type": file_type,
                                "fallback_used": True,
                                "original_error": error_msg,
                            },
                        }
                    except Exception as fallback_error:
                        logger.warning(
                            f"Fallback converter also failed for {file_path}: {fallback_error}"
                        )

                        # For PDF format errors, try a different approach
                        if file_type == "pdf" and (
                            "Data format error" in error_msg
                            or "Failed to load document" in error_msg
                        ):
                            logger.info(
                                f"Attempting PDF format recovery for {file_path}"
                            )
                            try:
                                # Try with different PDF settings
                                recovery_config = {
                                    "output_format": "markdown",
                                    "use_llm": False,
                                    "force_ocr": False,
                                    "disable_ocr": True,
                                    "disable_image_extraction": True,
                                    "format_lines": False,  # Disable line formatting
                                    "debug": False,
                                    "pdf_strategy": "fast",  # Use fast strategy
                                }

                                recovery_converter = self._create_fallback_converter(
                                    recovery_config
                                )
                                result = recovery_converter(str(file_path))

                                return {
                                    "text": getattr(result, "text", "") or "",
                                    "markdown": getattr(result, "markdown", "") or "",
                                    "metadata": getattr(result, "metadata", {}) or {},
                                    "processing_info": {
                                        "converter_used": "marker_pdf_recovery",
                                        "file_path": str(file_path),
                                        "file_type": file_type,
                                        "fallback_used": True,
                                        "recovery_mode": True,
                                        "original_error": error_msg,
                                    },
                                }
                            except Exception as recovery_error:
                                logger.warning(
                                    f"PDF recovery also failed for {file_path}: {recovery_error}"
                                )

                        # Try minimal converter as final fallback
                        logger.info(
                            f"Attempting minimal conversion (text-only) for {file_path}"
                        )
                        try:
                            minimal_converter = self._create_minimal_converter()
                            result = minimal_converter(str(file_path))

                            return {
                                "text": getattr(result, "text", "") or "",
                                "markdown": getattr(result, "text", "")
                                or "",  # Use text as markdown
                                "metadata": getattr(result, "metadata", {}) or {},
                                "processing_info": {
                                    "converter_used": "marker_minimal_text_only",
                                    "file_path": str(file_path),
                                    "file_type": file_type,
                                    "fallback_used": True,
                                    "minimal_mode": True,
                                    "original_error": error_msg,
                                },
                            }
                        except Exception as minimal_error:
                            logger.warning(
                                f"Minimal converter also failed for {file_path}: {minimal_error}"
                            )

                            # Final fallback: try to read file as text
                            logger.info(
                                f"Attempting final text extraction fallback for {file_path}"
                            )
                            try:
                                with open(
                                    file_path, "r", encoding="utf-8", errors="ignore"
                                ) as f:
                                    text_content = f.read()

                                if text_content.strip():
                                    return {
                                        "text": text_content,
                                        "markdown": text_content,
                                        "metadata": {"fallback_extraction": True},
                                        "processing_info": {
                                            "converter_used": "basic_text_fallback",
                                            "file_path": str(file_path),
                                            "file_type": file_type,
                                            "fallback_used": True,
                                            "basic_extraction": True,
                                            "original_error": error_msg,
                                        },
                                    }
                                else:
                                    raise ValueError("No readable text content found")
                            except Exception as basic_error:
                                logger.warning(
                                    f"Basic text extraction also failed for {file_path}: {basic_error}"
                                )

                                # Final fallback: return a structured error response
                                logger.warning(
                                    f"All extraction methods failed for {file_path}. File appears to be corrupted or unsupported."
                                )
                                return {
                                    "text": f"ERROR: Unable to extract content from {Path(file_path).name}. The file appears to be corrupted, password-protected, or in an unsupported format. Please try uploading a different file.",
                                    "markdown": f"# File Processing Error\n\nUnable to extract content from `{Path(file_path).name}`.\n\n**Possible reasons:**\n- File is corrupted\n- File is password-protected\n- File format is not supported\n- File is empty or contains no readable text\n\n**Recommendation:** Please try uploading a different file.",
                                    "metadata": {
                                        "error": True,
                                        "error_type": "extraction_failed",
                                        "original_error": error_msg,
                                        "file_name": Path(file_path).name,
                                    },
                                    "processing_info": {
                                        "converter_used": "error_fallback",
                                        "file_path": str(file_path),
                                        "file_type": file_type,
                                        "fallback_used": True,
                                        "error_mode": True,
                                        "original_error": error_msg,
                                    },
                                }
                else:
                    # Re-raise the original error if it's not tensor-related
                    logger.error(f"Error extracting content from {file_path}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise ValueError(f"Failed to process file {file_path}: {e}")

        # Unsupported file type
        raise ValueError(
            f"Unsupported file type: {file_type}. Supported types: {marker_supported_types + ['txt', 'md', 'markdown']}"
        )

    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from a file.

        Args:
            file_path: Path to the file to process

        Returns:
            Extracted text content
        """
        content = self.extract_content(file_path)
        return content.get("text", "") or content.get("markdown", "")

    def extract_markdown(self, file_path: Path) -> str:
        """Extract markdown from a file.

        Args:
            file_path: Path to the file to process

        Returns:
            Extracted markdown content
        """
        content = self.extract_content(file_path)
        return content.get("markdown", "") or content.get("text", "")

    def create_file_knowledge_source(
        self,
        file_path: Path,
        user_id: str,
        original_filename: str,
        file_type: str = None,
    ) -> Knowledge:
        """Create a Knowledge source for an uploaded file.

        Args:
            file_path: Path to the uploaded file
            user_id: ID of the user who uploaded the file
            original_filename: Original filename from the upload
            file_type: File type (if None, will be detected from extension)

        Returns:
            Knowledge: Knowledge object configured for file processing
        """
        if file_type is None:
            file_type = file_path.suffix.lower().lstrip(".")

        # Use static knowledge ID for user uploaded docs
        knowledge_id = "user_defined_docs"

        file_url = f"file://{file_path.absolute()}"

        return Knowledge(
            id=knowledge_id,
            name=f"Uploaded {file_type.upper()}: {original_filename}",
            description=f"User uploaded {file_type} file: {original_filename}",
            url=file_url,
            enabled=True,
            scraping_mode="single_page",
            allowed_subdomains=[],
            blocked_subdomains=[],
            url_patterns=[],
            crawl_depth=0,
            target_elements=[],
            content_filter_threshold=0.6,
        )

    async def get_file_documents(
        self, knowledge: KnowledgeSourceConfig, batch_size: int = 50
    ) -> AsyncGenerator[List[Document], None]:
        """Extract documents from a file using Marker PdfConverter.

        Args:
            knowledge: Knowledge object for the file
            batch_size: Number of documents to process before yielding

        Yields:
            List[Document]: Batches of documents extracted from the file
        """
        # Extract file path from knowledge URL
        file_url = knowledge.url
        if file_url.startswith("file://"):
            file_path = Path(file_url[7:])  # Remove "file://" prefix
        else:
            file_path = Path(file_url)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return

        try:
            logger.info(
                f"Extracting content from file: {file_path} | knowledge: {knowledge.id} | batch size: {batch_size} | knowledge: {knowledge.name}"
            )
            # Extract content from file using Marker
            content = self.extract_content(file_path)
            text_content = content.get("text", "")
            markdown_content = content.get("markdown", "")
            # tables = content.get('tables', [])
            # layout = content.get('layout', {})
            processing_info = content.get("processing_info", {})

            if not text_content.strip() and not markdown_content.strip():
                logger.warning(f"No content extracted from file: {file_path}")
                return

            # Create Document object with enhanced metadata
            metadata = {
                "source_url": str(file_path),  # Full file path for technical reference
                "knowledge_source": knowledge.id,
                "title": knowledge.name,  # Document name for user-friendly display
                "file_type": processing_info.get("file_type", "unknown"),
                "original_filename": (
                    knowledge.name.split(": ")[-1]
                    if ": " in knowledge.name
                    else file_path.name
                ),
                "extraction_method": processing_info.get("converter_used", "unknown"),
                # "has_tables": len(tables) > 0,
                # "table_count": len(tables),
                # "has_layout_info": bool(layout)
            }

            # Add optional metadata if available
            if hasattr(knowledge, "description"):
                metadata["description"] = knowledge.description

            # Add table information if available
            # if tables:
            #    metadata["tables"] = tables

            # Add layout information if available
            # if layout:
            #    metadata["layout"] = layout

            # Use markdown content if available, otherwise use plain text
            page_content = markdown_content if markdown_content else text_content

            doc = Document(page_content=page_content, metadata=metadata)

            # Yield as a single batch
            yield [doc]

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def extract_documents(
        self,
        knowledge: Knowledge,
        enable_llm_enrichment: bool = True,
        llm_max_workers: int = 8,
        write_to_file: bool = True,
        output_file: Optional[Path] = None,
    ) -> list[Document]:
        """Extract documents from a file using the core processing pipeline.

        Args:
            knowledge: Knowledge object containing file information
            enable_llm_enrichment: Whether to enrich with LLM extraction
            llm_max_workers: Number of LLM workers for enrichment
            write_to_file: Whether to write results to file
            output_file: Output file path

        Returns:
            list[Document]: List of processed documents
        """
        # Get document generator
        documents_generator = self.get_file_documents(knowledge, batch_size=50)

        # Collect all documents
        all_docs = []
        loop = asyncio.get_event_loop()

        try:
            while True:
                batch = loop.run_until_complete(documents_generator.__anext__())
                all_docs.extend(batch)
                logger.info(
                    f"Processed batch of {len(batch)} documents. Total so far: {len(all_docs)}"
                )
        except StopAsyncIteration:
            pass  # All batches processed

        # Process documents using base processor
        self.process_documents_with_batch_callback(
            documents_generator=self.get_file_documents(knowledge, batch_size=50),
            client=None,  # File processing doesn't have client
            batch_callback=None,  # File processing doesn't have batch_callback
            output_file=output_file,
            knowledge_job=None,  # File processing doesn't have knowledge_job
            knowledge_source_config=knowledge,
        )

        return all_docs

    def process_uploaded_file(
        self,
        file_path: Path,
        user_id: str,
        original_filename: str,
        client: Optional[Any] = None,
        batch_callback=None,
        enable_llm_enrichment: bool = True,
        llm_max_workers: int = 5,
        write_to_file: bool = True,
        output_file: Optional[Path] = None,
    ) -> None:
        """Process uploaded file using the document processing pipeline.

        Args:
            file_path: Path to the uploaded file
            user_id: ID of the user who uploaded the file
            original_filename: Original filename from the upload
            client: Optional client object for batch callback
            batch_callback: Optional callback function for batch processing
            enable_llm_enrichment: Whether to enrich with LLM extraction
            llm_max_workers: Number of LLM workers for enrichment
            write_to_file: Whether to write results to file
            output_file: Output file path (if None, uses default)
        """
        logger.info(
            f"Processing uploaded file: {original_filename} for user: {user_id}"
        )

        # Step 1: Create knowledge source for the file
        knowledge = self.create_file_knowledge_source(
            file_path=file_path, user_id=user_id, original_filename=original_filename
        )

        logger.info(f"Created knowledge source: {knowledge.id} for file: {file_path}")

        # Step 2: Use base processing pipeline
        self.process_documents_with_batch_callback(
            documents_generator=self.get_file_documents(knowledge, batch_size=50),
            client=client,
            batch_callback=batch_callback,
            output_file=output_file,
            knowledge_job=None,  # File processing doesn't have knowledge_job
            knowledge_source_config=knowledge,
        )

        logger.info(f"Completed processing file: {original_filename}")

    async def process_uploaded_file_async(
        self,
        file_path: Path,
        user_id: str,
        original_filename: str,
        client: Optional[Any] = None,
        batch_callback=None,
        enable_llm_enrichment: bool = False,
        llm_max_workers: int = 5,
        write_to_file: bool = True,
        output_file: Optional[Path] = None,
        check_duplicates: bool = False,
    ) -> Knowledge:
        """Async version of process_uploaded_file for use in async contexts."""
        logger.info(
            f"Processing uploaded file: {original_filename} for user: {user_id} | enable_llm_enrichment: {enable_llm_enrichment} | llm_max_workers: {llm_max_workers} | write_to_file: {write_to_file} | output_file: {output_file} | check_duplicates: {check_duplicates}"
        )

        # Step 1: Create knowledge source for the file
        knowledge = self.create_file_knowledge_source(
            file_path=file_path, user_id=user_id, original_filename=original_filename
        )

        logger.info(f"Created knowledge source: {knowledge.id} for file: {file_path}")

        # Step 2: Use async processing pipeline - collect documents first
        documents_generator = self.get_file_documents(knowledge, batch_size=50)
        all_docs = []

        try:
            async for batch in documents_generator:
                all_docs.extend(batch)
                logger.info(
                    f"Processed batch of {len(batch)} documents. Total so far: {len(all_docs)}"
                )
        except Exception as e:
            logger.error(f"Error collecting documents: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Step 3: Process documents directly (simplified for files)
        if all_docs:
            logger.info(f"Processing {len(all_docs)} documents from file")

            # Process each document: Split → LLM Enrichment → Cross-reference
            processed_chunks = []

            for doc in all_docs:
                # Step 1: Split document into chunks
                from config import settings
                from datapilotflow.domain.knowledge.document_splitter import SplitterType
                from datapilotflow.processors.splitters import create_splitter_by_type

                # Create a default text splitter
                splitter = create_splitter_by_type(
                    splitter_type=SplitterType.TEXT,
                    chunk_size=1024,
                    chunk_overlap=128,
                    name="File Processor Splitter",
                )
                chunks = splitter.split(doc.page_content)

                # Step 2: Add cross-reference metadata to chunks
                from application.data.utils.chunk_manager import (
                    process_chunks_with_cross_reference,
                )

                chunks_with_cross_ref = process_chunks_with_cross_reference(doc, chunks)

                # Step 3: Enrich chunks with LLM if enabled - RUN IN THREAD POOL TO AVOID BLOCKING
                if enable_llm_enrichment:
                    logger.info(
                        f"Using {len(chunks_with_cross_ref)} chunks without LLM enrichment (simplified pipeline)"
                    )
                    processed_chunks.extend(chunks_with_cross_ref)

            # Write to file if requested
            if write_to_file:
                from application.data.storage.file_writer import (
                    write_enriched_documents_to_file,
                )

                if output_file is None:
                    output_dir = Path("crawl_output")
                    output_dir.mkdir(exist_ok=True)

                    # Add timestamp suffix to filename
                    from datetime import datetime

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = (
                        output_dir
                        / f"enriched_documents_{knowledge.id}_{timestamp}.json"
                    )

                logger.info(
                    f"Writing {len(processed_chunks)} enriched chunks to file: {output_file}"
                )
                write_enriched_documents_to_file(processed_chunks, output_file)

            # Step 4: Store in vector database using Milvus processor
            if processed_chunks:
                logger.info(
                    f"Storing {len(processed_chunks)} chunks in Milvus vector database"
                )
                try:
                    from datapilotflow.processors.storage.milvus_processor import (
                        create_milvus_processor,
                    )
                    from datapilotflow.domain.config import settings
                    from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk

                    milvus_processor = create_milvus_processor(
                        milvus_model=KnowledgeChunk,
                        milvus_collection_name="LongTermMemory",
                    )

                    # Process chunks with Milvus processor
                    stats = milvus_processor.process_documents(processed_chunks)
                    logger.info(f"Milvus processing stats: {stats}")

                    # Extract document_id and chunk_ids from processed chunks
                    document_id = None
                    chunk_ids = []

                    if processed_chunks:
                        # Get document_id from the first chunk (should be the same for all chunks from same document)
                        first_chunk = processed_chunks[0]
                        if hasattr(first_chunk, "metadata"):
                            document_id = first_chunk.metadata.get("document_id")

                        # Collect all chunk_ids
                        for chunk in processed_chunks:
                            if hasattr(chunk, "metadata") and chunk.metadata.get(
                                "chunk_id"
                            ):
                                chunk_ids.append(chunk.metadata["chunk_id"])

                    logger.info(
                        f"File processing completed: {len(processed_chunks)} chunks processed"
                    )
                    logger.info(f"Document ID: {document_id}")
                    logger.info(f"Chunk IDs: {chunk_ids}")

                    # Store the document IDs for later use in MongoDB update
                    # This will be used by the file upload service to update MongoDB
                    knowledge.metadata = {
                        "document_id": document_id,
                        "chunk_ids": chunk_ids,
                        "processing_stats": stats,
                    }

                except Exception as e:
                    logger.error(f"Failed to store chunks in databases: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

            # Call batch callback if provided
            if batch_callback:
                logger.info(
                    f"Calling batch callback with {len(processed_chunks)} chunks"
                )
                batch_callback(client, processed_chunks, 1, len(processed_chunks))
            else:
                logger.info(
                    f"File processing completed: {len(processed_chunks)} chunks processed"
                )

        logger.info(f"Completed processing file: {original_filename}")
        return knowledge


# Convenience functions
def extract_content(
    file_path: Path, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Extract content from a file using Marker PdfConverter.

    Args:
        file_path: Path to the file to process
        config: Optional configuration for Marker

    Returns:
        Dict containing extracted content
    """
    processor = FileProcessor(config)
    return processor.extract_content(file_path)


def extract_text(file_path: Path, config: Optional[Dict[str, Any]] = None) -> str:
    """Extract plain text from a file.

    Args:
        file_path: Path to the file to process
        config: Optional configuration for Marker

    Returns:
        Extracted text content
    """
    processor = FileProcessor(config)
    return processor.extract_text(file_path)


def extract_markdown(file_path: Path, config: Optional[Dict[str, Any]] = None) -> str:
    """Extract markdown from a file.

    Args:
        file_path: Path to the file to process
        config: Optional configuration for Marker

    Returns:
        Extracted markdown content
    """
    processor = FileProcessor(config)
    return processor.extract_markdown(file_path)


def process_uploaded_file(
    file_path: Path,
    user_id: str,
    original_filename: str,
    client: Optional[Any] = None,
    batch_callback=None,
    enable_llm_enrichment: bool = True,
    llm_max_workers: int = 5,
    write_to_file: bool = True,
    output_file: Optional[Path] = None,
    check_duplicates: bool = False,
) -> None:
    """Process uploaded file using the document processing pipeline.

    Args:
        file_path: Path to the uploaded file
        user_id: ID of the user who uploaded the file
        original_filename: Original filename from the upload
        client: Optional client object for batch callback
        batch_callback: Optional callback function for batch processing
        enable_llm_enrichment: Whether to enrich with LLM extraction
        llm_max_workers: Number of LLM workers for enrichment
        write_to_file: Whether to write results to file
        output_file: Output file path (if None, uses default)
        check_duplicates: Whether to check for duplicates (usually False for files)
    """
    processor = FileProcessor()
    processor.process_uploaded_file(
        file_path,
        user_id,
        original_filename,
        client,
        batch_callback,
        enable_llm_enrichment,
        llm_max_workers,
        write_to_file,
        output_file,
        check_duplicates,
    )


def create_file_knowledge_source(
    file_path: Path, user_id: str, original_filename: str, file_type: str = None
):
    """Module-level wrapper for FileProcessor.create_file_knowledge_source for backward compatibility."""
    return FileProcessor().create_file_knowledge_source(
        file_path, user_id, original_filename, file_type
    )


def process_uploaded_files_batch(*args, **kwargs):
    """Module-level wrapper for FileProcessor.process_uploaded_files_batch for backward compatibility."""
    processor = FileProcessor()
    if hasattr(processor, "process_uploaded_files_batch"):
        return processor.process_uploaded_files_batch(*args, **kwargs)
    raise NotImplementedError(
        "process_uploaded_files_batch is not implemented in FileProcessor."
    )
