"""
Specialized MongoDB service for RAG file upload tracking.

This service extends the generic MongoClientWrapper to provide
specific functionality for tracking file uploads, processing status,
and failed events.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from bson import ObjectId

from datapilotflow.infrastructure.mongo.client import MongoClientWrapper
from datapilotflow.domain.rag.rag_file_upload import (
    RagFileUpload, 
    RagFailedEvent, 
    FileUploadStatus, 
    StatusHistoryEntry,
    ProcessingResults,
    ErrorDetails,
    FileMetadata,
    FileLocations
)
from datapilotflow.domain.config import settings


class RagFileUploadService(MongoClientWrapper[RagFileUpload]):
    """Specialized service for RAG file upload tracking."""
    
    def __init__(self):
        """Initialize the RAG file upload service."""
        super().__init__(
            model=RagFileUpload,
            collection_name="rag_file_uploads",
            database_name=settings.MONGO_DB_NAME,
            mongodb_uri=settings.MONGO_CONN_STR
        )
    
    def create_file_upload_record(
        self,
        file_id: str,
        user_id: Optional[str],
        original_filename: str,
        safe_filename: str,
        file_path: str,
        file_size: int,
        content_type: str,
        description: Optional[str] = None
    ) -> RagFileUpload:
        """Create a new file upload record."""
        # Create file locations with initial inbound location
        file_locations = FileLocations(inbound=file_path)
        
        upload_record = RagFileUpload(
            file_id=file_id,
            user_id=user_id,
            original_filename=original_filename,
            safe_filename=safe_filename,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
            current_step="upload",
            file_locations=file_locations,
            metadata=FileMetadata(description=description)
        )
        
        # Add initial status
        upload_record.status_history.append(
            StatusHistoryEntry(
                status=FileUploadStatus.UPLOADED,
                message="File uploaded successfully",
                step="upload"
            )
        )
        
        # Insert into database and get the inserted document
        result = self.collection.insert_one(upload_record.model_dump())
        logger.info(f"Created file upload record: {file_id} with MongoDB ID: {result.inserted_id}")
        
        # Do NOT update the document with mongo_id
        # Just return the record
        return upload_record
    
    def update_status(
        self,
        file_id: str,
        status: FileUploadStatus,
        message: str,
        step: str,
        error: Optional[str] = None,
        traceback: Optional[str] = None
    ) -> bool:
        """Update file status and add to history."""
        try:
            # Create status history entry
            status_entry = StatusHistoryEntry(
                status=status,
                message=message,
                step=step,
                error=error,
                traceback=traceback
            )
            
            # Update document
            result = self.collection.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        "status": status,
                        "current_step": step,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"status_history": status_entry.model_dump()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated status for file {file_id}: {status} - {message}")
                return True
            else:
                logger.warning(f"File {file_id} not found for status update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating status for file {file_id}: {e}")
            return False
    
    def update_processing_results(
        self,
        file_id: str,
        chunks_created: int = 0,
        enriched_chunks: int = 0,
        processing_time_seconds: Optional[float] = None,
        output_file: Optional[str] = None,
        knowledge_source_id: Optional[str] = None,
        document_id: Optional[str] = None,
        chunk_ids: Optional[List[str]] = None
    ) -> bool:
        """Update processing results."""
        try:
            processing_results = ProcessingResults(
                chunks_created=chunks_created,
                enriched_chunks=enriched_chunks,
                processing_time_seconds=processing_time_seconds,
                output_file=output_file,
                knowledge_source_id=knowledge_source_id,
                document_id=document_id,
                chunk_ids=chunk_ids or []
            )
            result = self.collection.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        "processing_results": processing_results.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            if result.modified_count > 0:
                logger.info(f"Updated processing results for file {file_id}")
                return True
            else:
                logger.warning(f"File {file_id} not found for processing results update")
                return False
        except Exception as e:
            logger.error(f"Error updating processing results for file {file_id}: {e}")
            return False
    
    def update_error_details(
        self,
        file_id: str,
        error_type: str,
        error_message: str,
        traceback: str,
        failed_step: str,
        dlq_event: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update error details."""
        try:
            error_details = ErrorDetails(
                error_type=error_type,
                error_message=error_message,
                traceback=traceback,
                failed_step=failed_step,
                dlq_event=dlq_event
            )
            
            result = self.collection.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        "error_details": error_details.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated error details for file {file_id}")
                return True
            else:
                logger.warning(f"File {file_id} not found for error details update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating error details for file {file_id}: {e}")
            return False
    
    def update_file_location(
        self,
        file_id: str,
        location_type: str,  # "inbound", "failed", "archive"
        file_path: str
    ) -> bool:
        """Update file location."""
        try:
            result = self.collection.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        f"file_locations.{location_type}": file_path,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated {location_type} location for file {file_id}: {file_path}")
                return True
            else:
                logger.warning(f"File {file_id} not found for location update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file location for {file_id}: {e}")
            return False
    
    def get_file_by_id(self, file_id: str) -> Optional[RagFileUpload]:
        """Get file upload record by file ID."""
        try:
            doc = self.collection.find_one({"file_id": file_id})
            if doc:
                return self._parse_single_document(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
    
    def get_files_by_user(self, user_id: str, limit: int = 100) -> List[RagFileUpload]:
        """Get files uploaded by specific user."""
        try:
            query = {"user_id": user_id}
            return self.fetch_documents(limit=limit, query=query)
        except Exception as e:
            logger.error(f"Error getting files for user {user_id}: {e}")
            return []
    
    def get_files_by_status(self, status: FileUploadStatus, limit: int = 100) -> List[RagFileUpload]:
        """Get files by status."""
        try:
            query = {"status": status}
            return self.fetch_documents(limit=limit, query=query)
        except Exception as e:
            logger.error(f"Error getting files with status {status}: {e}")
            return []
    
    def get_failed_files(self, limit: int = 100) -> List[RagFileUpload]:
        """Get all failed files."""
        return self.get_files_by_status(FileUploadStatus.FAILED, limit)
    
    def _parse_single_document(self, doc: Dict[str, Any]) -> RagFileUpload:
        """Parse a single MongoDB document to RagFileUpload model."""
        # Only set mongo_id from _id if it exists, otherwise don't include it
        if "_id" in doc:
            doc["mongo_id"] = str(doc["_id"])
        doc.pop("_id", None)
        return RagFileUpload.model_validate(doc)

    def get_file_uploads_with_processing_results(self) -> List[RagFileUpload]:
        """Get all file uploads that have processing results."""
        try:
            cursor = self.collection.find({
                "processing_results": {"$exists": True}
            })
            results = []
            for doc in cursor:
                result = self._parse_single_document(doc)
                if result:
                    results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error getting file uploads with processing results: {e}")
            return []


class RagFailedEventService(MongoClientWrapper[RagFailedEvent]):
    """Specialized service for RAG failed events tracking."""
    
    def __init__(self):
        """Initialize the RAG failed events service."""
        super().__init__(
            model=RagFailedEvent,
            collection_name="rag_failed_events",
            database_name=settings.MONGO_DB_NAME,
            mongodb_uri=settings.MONGO_CONN_STR
        )
    
    def create_failed_event(
        self,
        event_id: str,
        original_event: Dict[str, Any],
        error_type: str,
        error_message: str,
        traceback: str,
        failed_step: str,
        source_queue: str
    ) -> RagFailedEvent:
        """Create a new failed event record."""
        failed_event = RagFailedEvent(
            event_id=event_id,
            original_event=original_event,
            error_type=error_type,
            error_message=error_message,
            traceback=traceback,
            failed_step=failed_step,
            source_queue=source_queue
        )
        
        # Insert into database
        self.collection.insert_one(failed_event.model_dump())
        logger.info(f"Created failed event record: {event_id}")
        
        return failed_event
    
    def mark_as_processed(self, event_id: str) -> bool:
        """Mark a failed event as processed."""
        try:
            result = self.collection.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "processed_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Marked failed event {event_id} as processed")
                return True
            else:
                logger.warning(f"Failed event {event_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error marking failed event {event_id} as processed: {e}")
            return False
    
    def get_unprocessed_failed_events(self, limit: int = 100) -> List[RagFailedEvent]:
        """Get unprocessed failed events."""
        try:
            query = {"processed_at": None}
            return self.fetch_documents(limit=limit, query=query)
        except Exception as e:
            logger.error(f"Error getting unprocessed failed events: {e}")
            return [] 