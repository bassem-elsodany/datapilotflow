"""
Document Splitter Service.

This module provides business logic for managing document splitter configurations,
including CRUD operations and default splitter initialization.
"""

from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.document_splitter import (
    DocumentSplitter,
    DocumentSplitterCreate,
    DocumentSplitterUpdate,
    SplitterType,
)
from datapilotflow.persistence.dao.document_splitter_dao import DocumentSplitterDAO


class DocumentSplitterService:
    """Service for managing document splitter configurations."""

    def __init__(self):
        """Initialize the DocumentSplitterService."""
        self.dao = DocumentSplitterDAO()

    def create_splitter(self, splitter_data: DocumentSplitterCreate, user_id: str) -> DocumentSplitter:
        """Create a new document splitter configuration.

        Args:
            splitter_data: The splitter configuration data
            user_id: ID of the user creating the splitter

        Returns:
            DocumentSplitter: The created splitter configuration

        Raises:
            ValueError: If validation fails or splitter name already exists
        """
        try:
            # Validate splitter configuration
            self._validate_splitter_config(splitter_data)
            
            # Create the splitter
            splitter_id = self.dao.create_splitter(splitter_data, user_id)
            if not splitter_id:
                raise ValueError("Failed to create document splitter")
            
            # Get and return the created splitter
            splitter = self.dao.get_splitter(splitter_id)
            if not splitter:
                raise ValueError("Failed to retrieve created splitter")
                
            logger.info(f"Created document splitter '{splitter.name}' for user {user_id}")
            return splitter
            
        except Exception as e:
            logger.error(f"Error creating document splitter: {e}")
            raise

    def get_splitter_by_id(self, splitter_id: str) -> Optional[DocumentSplitter]:
        """Get a document splitter by ID.

        Args:
            splitter_id: The splitter ID

        Returns:
            DocumentSplitter: The splitter if found, None otherwise
        """
        return self.dao.get_splitter(splitter_id)

    def get_user_splitters(self, user_id: str, include_defaults: bool = True) -> List[DocumentSplitter]:
        """Get all document splitters available to a user.

        Args:
            user_id: The user ID
            include_defaults: Whether to include default/system splitters

        Returns:
            List[DocumentSplitter]: List of available splitter configurations
        """
        return self.dao.list_splitters(user_id, include_defaults)

    def get_default_splitters(self) -> List[DocumentSplitter]:
        """Get all default/system document splitters.

        Returns:
            List[DocumentSplitter]: List of default splitter configurations
        """
        return self.dao.list_defaults()

    def get_splitters_by_type(self, splitter_type: SplitterType, user_id: Optional[str] = None) -> List[DocumentSplitter]:
        """Get splitters by type, optionally filtered by user.

        Args:
            splitter_type: The type of splitter to filter by
            user_id: Optional user ID to filter by

        Returns:
            List[DocumentSplitter]: List of matching splitter configurations
        """
        return self.dao.list_by_type(splitter_type, user_id)

    def update_splitter(self, splitter_id: str, splitter_update: DocumentSplitterUpdate, user_id: str) -> Optional[DocumentSplitter]:
        """Update a document splitter configuration.

        Args:
            splitter_id: The splitter ID
            splitter_update: The update data
            user_id: ID of the user updating the splitter

        Returns:
            DocumentSplitter: The updated splitter if found, None otherwise

        Raises:
            ValueError: If validation fails or splitter not found
            PermissionError: If user doesn't have permission to update the splitter
        """
        # Get existing splitter to check permissions
        existing_splitter = self.dao.get_splitter(splitter_id, user_id)
        if not existing_splitter:
            raise ValueError(f"Document splitter not found: {splitter_id}")

        # Check if user has permission to update (owner only, not defaults)
        if existing_splitter.user_id != user_id:
            raise PermissionError(f"User {user_id} does not have permission to update splitter {splitter_id}")

        # Validate update data
        if splitter_update.splitter_type is not None:
            temp_create = DocumentSplitterCreate(
                name="temp",
                splitter_type=splitter_update.splitter_type,
                chunk_size=splitter_update.chunk_size or existing_splitter.chunk_size,
                chunk_overlap=splitter_update.chunk_overlap or existing_splitter.chunk_overlap,
                headers_to_split_on=splitter_update.headers_to_split_on or existing_splitter.headers_to_split_on,
            )
            self._validate_splitter_config(temp_create)

        try:
            success = self.dao.update_splitter(splitter_id, splitter_update, user_id)
            if success:
                updated_splitter = self.dao.get_splitter(splitter_id)
                if updated_splitter:
                    logger.info(f"Updated document splitter '{updated_splitter.name}' by user {user_id}")
                return updated_splitter
            return None
        except Exception as e:
            logger.error(f"Error updating document splitter: {e}")
            raise

    def delete_splitter(self, splitter_id: str, user_id: str) -> bool:
        """Delete a document splitter configuration.

        Args:
            splitter_id: The splitter ID
            user_id: ID of the user requesting deletion

        Returns:
            bool: True if deleted, False if not found

        Raises:
            ValueError: If splitter is in use or is a default splitter
            PermissionError: If user doesn't have permission to delete the splitter
        """
        # Get existing splitter to check permissions
        existing_splitter = self.dao.get_splitter(splitter_id, user_id)
        if not existing_splitter:
            return False

        # Check if it's a default splitter
        if existing_splitter.is_default:
            raise ValueError("Cannot delete default splitter configurations")

        # Check if user has permission to delete (owner only)
        if existing_splitter.user_id != user_id:
            raise PermissionError(f"User {user_id} does not have permission to delete splitter {splitter_id}")

        try:
            deleted = self.dao.delete_splitter(splitter_id, user_id)
            if deleted:
                logger.info(f"Deleted document splitter '{existing_splitter.name}' by user {user_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting document splitter: {e}")
            raise

    def get_splitter_for_job(self, splitter_id: str) -> DocumentSplitter:
        """Get a splitter configuration for use in a knowledge job.

        This method also increments the usage count for tracking purposes.

        Args:
            splitter_id: The splitter ID

        Returns:
            DocumentSplitter: The splitter configuration

        Raises:
            ValueError: If splitter not found
        """
        splitter = self.dao.get_splitter(splitter_id)
        if not splitter:
            raise ValueError(f"Document splitter not found: {splitter_id}")

        # Increment usage count
        self.dao.increment_usage_count(splitter_id)
        logger.debug(f"Retrieved splitter '{splitter.name}' for job use")
        
        return splitter

    def get_most_used_splitters(self, limit: int = 10) -> List[DocumentSplitter]:
        """Get the most frequently used splitter configurations.

        Args:
            limit: Maximum number of splitters to return

        Returns:
            List[DocumentSplitter]: List of most used splitters
        """
        return self.dao.list_most_used(limit)


    def _validate_splitter_config(self, splitter_data: DocumentSplitterCreate) -> None:
        """Validate splitter configuration data.

        Args:
            splitter_data: The splitter configuration to validate

        Raises:
            ValueError: If validation fails
        """
        if splitter_data.splitter_type == SplitterType.TEXT:
            # Validate text splitter configuration
            if splitter_data.chunk_size is None:
                raise ValueError("chunk_size is required for TEXT splitter type")
            
            if splitter_data.chunk_overlap is not None:
                if splitter_data.chunk_overlap >= splitter_data.chunk_size:
                    raise ValueError("chunk_overlap must be less than chunk_size")

        elif splitter_data.splitter_type == SplitterType.DOCUMENT:
            # Document splitter can work with defaults, but validate if headers are provided
            if splitter_data.headers_to_split_on is not None:
                if not splitter_data.headers_to_split_on:
                    raise ValueError("headers_to_split_on cannot be empty for DOCUMENT splitter type")
                
                # Validate header patterns
                for pattern, name in splitter_data.headers_to_split_on:
                    if not pattern.strip() or not name.strip():
                        raise ValueError("Header patterns and names cannot be empty")

    def get_default_splitter_for_type(self, splitter_type: SplitterType) -> Optional[DocumentSplitter]:
        """Get a default splitter configuration for a specific type.

        Args:
            splitter_type: The splitter type to get default for

        Returns:
            DocumentSplitter: A default splitter of the specified type, or None if not found
        """
        defaults = self.dao.list_by_type(splitter_type)
        
        # Return the first default splitter of the requested type
        for splitter in defaults:
            if splitter.is_default:
                return splitter
        
        return None


# Singleton instance for easy access
_document_splitter_service = None


def get_document_splitter_service() -> DocumentSplitterService:
    """Get the singleton DocumentSplitterService instance.

    Returns:
        DocumentSplitterService: The service instance
    """
    global _document_splitter_service
    if _document_splitter_service is None:
        _document_splitter_service = DocumentSplitterService()
    return _document_splitter_service