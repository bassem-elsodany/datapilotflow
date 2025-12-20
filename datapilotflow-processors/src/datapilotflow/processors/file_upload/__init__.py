"""
File Upload Processing Package.

This package contains processors for handling file upload events,
including file processing, extraction, and storage operations.
"""

from .file_upload_processor import FileUploadEventProcessor, get_file_upload_event_processor

__all__ = [
    "FileUploadEventProcessor",
    "get_file_upload_event_processor",
]
