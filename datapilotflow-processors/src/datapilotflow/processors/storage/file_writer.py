"""
File Writer module for handling document and markdown file writing operations.
"""

import hashlib
import json
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document
from loguru import logger


def _prepare_document_data(documents: List[Document]) -> List[Dict[str, Any]]:
    """Prepare document data matching Milvus schema (without vector field).

    Generates the same fields that Milvus generates at insert time.

    Args:
        documents: List of Document objects to prepare

    Returns:
        List of dictionaries with document data matching Milvus schema
    """
    enriched_data = []
    for doc in documents:
        # Generate correlation_id the same way Milvus does
        source_url = doc.metadata.get("source_url", "")
        chunk_index = doc.metadata.get("chunk_index", 0)
        page_content = doc.page_content
        content_hash = hashlib.md5(page_content.encode()).hexdigest()
        correlation_id = f"{source_url}_{chunk_index}_{content_hash}"

        # Core fields matching Milvus schema exactly
        doc_data = {
            "id": str(uuid.uuid4()),  # Generate UUID like Milvus does
            "page_content": page_content,
            "source_url": source_url,
            "job_id": doc.metadata.get("job_id", ""),
            "title": doc.metadata.get("title", ""),
            "chunk_id": doc.metadata.get("chunk_id", ""),
            "chunk_index": chunk_index,
            "total_chunks": doc.metadata.get("total_chunks", 1),
            "correlation_id": correlation_id,  # Generated, not from metadata
            "created_at": datetime.utcnow().isoformat(),  # Generated, not from metadata
        }

        enriched_data.append(doc_data)

    return enriched_data


async def write_markdown_to_file(
    markdown_file: Path, metadata: Dict[str, Any], content: str
):
    """Helper function to write markdown content to file asynchronously."""
    try:
        logger.info(f"Writing markdown to file: {markdown_file}")

        # Ensure the directory exists
        markdown_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare the data to write
        data_entry = {**metadata, "page_content": content}

        # Read existing data or create new array
        existing_data = []
        if markdown_file.exists():
            try:
                with open(markdown_file, "r", encoding="utf-8") as f:
                    file_content = f.read().strip()
                    if file_content:
                        existing_data = json.loads(file_content)
                        if not isinstance(existing_data, list):
                            logger.warning(
                                f"File {markdown_file} does not contain a JSON array, creating new array"
                            )
                            existing_data = []
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(
                    f"Error reading existing file {markdown_file}: {e}, creating new file"
                )
                existing_data = []

        # Add new entry
        existing_data.append(data_entry)

        # Write back to file
        with open(markdown_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)

        logger.info(
            f"Successfully wrote markdown for {metadata.get('source_url', 'unknown')} to {markdown_file}"
        )

    except Exception as e:
        logger.error(f"Error writing markdown to file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


def write_enriched_markdown_to_file(documents: List[Document], output_file: Path):
    """Write markdown content to a JSON file.

    Args:
        documents: List of Document objects with markdown content
        output_file: Path to the output JSON file
    """
    try:
        logger.info(
            f"Writing {len(documents)} enriched markdown documents to file: {output_file}"
        )

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare the data to write using shared helper
        enriched_data = _prepare_document_data(documents)

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, indent=4, ensure_ascii=False)

        logger.info(
            f"Successfully wrote {len(documents)} enriched markdown documents to {output_file}"
        )

    except Exception as e:
        logger.error(f"Error writing enriched markdown documents to file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


def write_enriched_documents_to_file(
    documents: List[Document], output_file: Path, append: bool = False
):
    """Write processed documents to a JSON file.

    Args:
        documents: List of Document objects with processed content and metadata
        output_file: Path to the output JSON file
        append: If True, append to existing file; if False, overwrite existing file
    """
    try:
        logger.info(
            f"Writing {len(documents)} enriched documents to file: {output_file} (append={append})"
        )

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare the data to write using shared helper
        enriched_data = _prepare_document_data(documents)

        # Handle append vs overwrite
        if append and output_file.exists():
            # Read existing data
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    file_content = f.read().strip()
                    if file_content:
                        existing_data = json.loads(file_content)
                        if isinstance(existing_data, list):
                            enriched_data = existing_data + enriched_data
                        else:
                            logger.warning(
                                f"File {output_file} does not contain a JSON array, overwriting"
                            )
                    else:
                        logger.info(f"File {output_file} is empty, starting fresh")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(
                    f"Error reading existing file {output_file}: {e}, overwriting"
                )

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, indent=4, ensure_ascii=False)

        logger.info(
            f"Successfully wrote {len(documents)} enriched documents to {output_file}"
        )

    except Exception as e:
        logger.error(f"Error writing enriched documents to file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
