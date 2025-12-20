"""
File upload service for SkillPilot.

This module provides file upload handling, RabbitMQ event publishing,
and file processing queue management for the SkillPilot system.
"""

import os
import traceback
import uuid
import aiofiles
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, status, Request
from fastapi.responses import JSONResponse
from loguru import logger
from datapilotflow.domain.config import settings
import asyncio
import shutil
from pathlib import Path
from datapilotflow.persistence.dao.rag_file_upload_service import RagFileUploadService
from datapilotflow.services.events_publisher import get_file_upload_event_publisher

UPLOAD_INBOUND_DIR = settings.RAG_FILE_UPLOAD_INBOUND_DIR
ARCHIVE_DIR = settings.RAG_FILE_UPLOAD_ARCHIVE_DIR
FAILED_DIR = settings.RAG_FILE_UPLOAD_FAILED_DIR






async def handle_file_upload(file: UploadFile, user_id: Optional[str], description: str, request: Request) -> dict:
    """
    Handles file upload: saves the file, builds the event payload, and publishes to RabbitMQ.
    Returns a response dict for the API to return.
    Raises exceptions on error.
    """
    try:
        # Ensure inbound directory exists
        os.makedirs(UPLOAD_INBOUND_DIR, exist_ok=True)

        # Generate unique file ID and safe filename
        file_id = str(uuid.uuid4())
        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1]
        safe_filename = f"{file_id}{ext}"
        file_location = os.path.join(UPLOAD_INBOUND_DIR, safe_filename)

        # Save file asynchronously
        async with aiofiles.open(file_location, 'wb') as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out_file.write(chunk)

        # Diagnostic: check file existence after write
        if not os.path.exists(file_location):
            logger.error(f"[DIAG] File {file_location} does not exist after write!")
        else:
            logger.info(f"[DIAG] File {file_location} exists after write.")

        # Gather file info
        file_stat = os.stat(file_location)
        content_type = file.content_type or "application/octet-stream"
        file_size = file_stat.st_size
        upload_timestamp = datetime.utcnow().isoformat() + "Z"

        # Build event payload
        event_payload = {
            "event_type": "file_upload",
            "file_id": file_id,
            "user_id": user_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "location": file_location,
            "content_type": content_type,
            "file_size": file_size,
            "upload_timestamp": upload_timestamp,
            "metadata": {
                "source": "web_ui",
                "description": description or ""
            }
        }

        # Create MongoDB record for tracking
        mongo_service = request.app.state.rag_file_upload_service
        upload_record = mongo_service.create_file_upload_record(
            file_id=file_id,
            user_id=user_id,
            original_filename=original_filename,
            safe_filename=safe_filename,
            file_path=file_location,
            file_size=file_size,
            content_type=content_type,
            description=description
        )

        # Publish event to RabbitMQ using the new event publisher
        file_upload_publisher = get_file_upload_event_publisher()
        await file_upload_publisher.publish_file_upload_event(event_payload)

        # Return response dict
        response = {
            "status": "queued",
            "file_id": file_id,
            "filename": safe_filename,
            "location": file_location,
            "message": "File uploaded and queued for processing."
        }
        # mongo_id field removed
        pass
        return response
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise 


def move_file(src_path, dest_dir):
    """Move a file to the destination directory, creating it if needed."""
    os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(src_path):
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.move(src_path, dest_path)
        return dest_path
    return None
