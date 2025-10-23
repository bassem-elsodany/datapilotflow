#!/usr/bin/env python3
"""
Example script demonstrating how to use different MongoDB schemas.

This script shows how to:
1. Use the generic MongoClientWrapper with different Pydantic models
2. Use the specialized RagFileUploadService
3. Use the specialized RagFailedEventService
4. Query and update records
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.mongo.client import MongoClientWrapper
from services.file_management.dao.rag_file_upload_service import (
    RagFileUploadService, 
    RagFailedEventService
)
from domain.rag_file_upload import (
    RagFileUpload, 
    RagFailedEvent, 
    FileUploadStatus,
    FileMetadata
)
from config import settings


def example_generic_mongo_wrapper():
    """Example of using the generic MongoClientWrapper with different schemas."""
    print("=== Generic MongoClientWrapper Examples ===")
    
    # Example 1: Using with RagFileUpload model
    print("\n1. Using generic wrapper with RagFileUpload model:")
    rag_upload_wrapper = MongoClientWrapper[RagFileUpload](
        model=RagFileUpload,
        collection_name="example_rag_uploads",
        database_name=settings.MONGO_DB_NAME,
        mongodb_uri=settings.MONGO_CONN_STR
    )
    
    # Create a sample record
    sample_upload = RagFileUpload(
        file_id=str(uuid.uuid4()),
        original_filename="example.pdf",
        safe_filename="example_123.pdf",
        file_path="/path/to/example.pdf",
        file_size=1024,
        content_type="application/pdf",
        metadata=FileMetadata(description="Example file")
    )
    
    # Insert the record
    rag_upload_wrapper.collection.insert_one(sample_upload.model_dump())
    print(f"Inserted sample upload record: {sample_upload.file_id}")
    
    # Query the record
    doc = rag_upload_wrapper.collection.find_one({"file_id": sample_upload.file_id})
    if doc:
        retrieved_upload = rag_upload_wrapper._parse_single_document(doc)
        print(f"Retrieved upload: {retrieved_upload.original_filename}")
    
    # Example 2: Using with RagFailedEvent model
    print("\n2. Using generic wrapper with RagFailedEvent model:")
    failed_event_wrapper = MongoClientWrapper[RagFailedEvent](
        model=RagFailedEvent,
        collection_name="example_failed_events",
        database_name=settings.MONGO_DB_NAME,
        mongodb_uri=settings.MONGO_CONN_STR
    )
    
    # Create a sample failed event
    sample_failed_event = RagFailedEvent(
        event_id=str(uuid.uuid4()),
        original_event={"test": "data"},
        error_type="ValueError",
        error_message="Test error",
        traceback="Test traceback",
        failed_step="processing",
        source_queue="main"
    )
    
    # Insert the record
    failed_event_wrapper.collection.insert_one(sample_failed_event.model_dump())
    print(f"Inserted sample failed event: {sample_failed_event.event_id}")


def example_specialized_services():
    """Example of using the specialized services."""
    print("\n=== Specialized Services Examples ===")
    
    # Example 1: RagFileUploadService
    print("\n1. Using RagFileUploadService:")
    rag_service = RagFileUploadService()
    
    # Create a file upload record
    file_id = str(uuid.uuid4())
    upload_record = rag_service.create_file_upload_record(
        file_id=file_id,
        user_id="user123",
        original_filename="test_document.pdf",
        safe_filename=f"{file_id}.pdf",
        file_path=f"/upload/inbound/{file_id}.pdf",
        file_size=2048,
        content_type="application/pdf",
        description="Test document for processing"
    )
    print(f"Created upload record: {upload_record.file_id}")
    
    # Update status
    rag_service.update_status(
        file_id=file_id,
        status=FileUploadStatus.PROCESSING,
        message="File processing started",
        step="extraction"
    )
    print(f"Updated status for file: {file_id}")
    
    # Update processing results
    rag_service.update_processing_results(
        file_id=file_id,
        chunks_created=10,
        enriched_chunks=8,
        processing_time_seconds=15.5,
        output_file="/output/enriched_document.json"
    )
    print(f"Updated processing results for file: {file_id}")
    
    # Query by status
    processing_files = rag_service.get_files_by_status(FileUploadStatus.PROCESSING)
    print(f"Found {len(processing_files)} files with processing status")
    
    # Example 2: RagFailedEventService
    print("\n2. Using RagFailedEventService:")
    failed_event_service = RagFailedEventService()
    
    # Create a failed event record
    event_id = str(uuid.uuid4())
    failed_event = failed_event_service.create_failed_event(
        event_id=event_id,
        original_event={"file_id": file_id, "action": "process"},
        error_type="ProcessingError",
        error_message="Failed to extract text from PDF",
        traceback="Traceback (most recent call last):\n  File...",
        failed_step="text_extraction",
        source_queue="main"
    )
    print(f"Created failed event: {failed_event.event_id}")
    
    # Get unprocessed failed events
    unprocessed_events = failed_event_service.get_unprocessed_failed_events()
    print(f"Found {len(unprocessed_events)} unprocessed failed events")
    
    # Mark as processed
    failed_event_service.mark_as_processed(event_id)
    print(f"Marked event {event_id} as processed")


def example_queries():
    """Example of various queries and operations."""
    print("\n=== Query Examples ===")
    
    rag_service = RagFileUploadService()
    
    # Get all files
    all_files = rag_service.fetch_documents(limit=10, query={})
    print(f"Total files in collection: {len(all_files)}")
    
    # Get files by user
    user_files = rag_service.get_files_by_user("user123")
    print(f"Files for user123: {len(user_files)}")
    
    # Get failed files
    failed_files = rag_service.get_failed_files()
    print(f"Failed files: {len(failed_files)}")
    
    # Get files by status
    for status in FileUploadStatus:
        files = rag_service.get_files_by_status(status)
        print(f"Files with status {status}: {len(files)}")


def example_error_handling():
    """Example of error handling and status updates."""
    print("\n=== Error Handling Examples ===")
    
    rag_service = RagFileUploadService()
    
    # Create a test file record
    file_id = str(uuid.uuid4())
    rag_service.create_file_upload_record(
        file_id=file_id,
        user_id="user456",
        original_filename="error_test.pdf",
        safe_filename=f"{file_id}.pdf",
        file_path=f"/upload/inbound/{file_id}.pdf",
        file_size=1024,
        content_type="application/pdf"
    )
    
    # Simulate processing error
    rag_service.update_status(
        file_id=file_id,
        status=FileUploadStatus.FAILED,
        message="Failed to process PDF - corrupted file",
        step="validation",
        error="PDFCorruptionError",
        traceback="Traceback (most recent call last):\n  File..."
    )
    
    # Update error details
    rag_service.update_error_details(
        file_id=file_id,
        error_type="PDFCorruptionError",
        error_message="PDF file is corrupted and cannot be processed",
        traceback="Full traceback here...",
        failed_step="validation",
        dlq_event={"queue": "main", "retry_count": 3}
    )
    
    # Update file location
    rag_service.update_file_location(file_id, "failed", f"/upload/failed/{file_id}.pdf")
    
    print(f"Created error scenario for file: {file_id}")


def main():
    """Run all examples."""
    print("MongoDB Schema Examples")
    print("=" * 50)
    
    try:
        # Test connection first
        print("Testing MongoDB connection...")
        rag_service = RagFileUploadService()
        print("✓ MongoDB connection successful")
        
        # Run examples
        example_generic_mongo_wrapper()
        example_specialized_services()
        example_queries()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 