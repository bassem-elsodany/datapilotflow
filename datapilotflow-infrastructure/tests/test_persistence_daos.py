"""
Comprehensive test suite for DataPilotFlow persistence layer DAOs.

Tests cover:
- MongoClientWrapper initialization and methods
- Basic DAO operations (create, read, update, delete)
- Model serialization/deserialization
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId
from pydantic import BaseModel, Field

from datapilotflow.infrastructure.mongo.client import MongoClientWrapper
from datapilotflow.domain.user import User
from datapilotflow.domain.knowledge.knowledge_job import (
    KnowledgeJob,
    KnowledgeJobCreate,
    JobStatus,
)
from datapilotflow.domain.notification import Notification
from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO
from datapilotflow.infrastructure.dao.notification import NotificationService


class TestMongoClientWrapper:
    """Test MongoClientWrapper initialization and basic operations."""

    def test_wrapper_initialization(self):
        """Test that MongoClientWrapper can be initialized with a valid model."""
        # Create a simple test model
        class TestModel(BaseModel):
            name: str
            value: int

        # Initialize wrapper - this should not raise an exception
        with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
            wrapper = MongoClientWrapper(
                model=TestModel,
                collection_name="test_collection",
                database_name="test_db",
                mongodb_uri="mongodb://localhost:27017"
            )
            assert wrapper.model == TestModel
            assert wrapper.collection_name == "test_collection"
            assert wrapper.database_name == "test_db"

    def test_parse_single_document_with_objectid(self):
        """Test parsing MongoDB documents with ObjectId conversion."""
        class TestModel(BaseModel):
            id: str = Field(alias="_id")
            name: str

        with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
            wrapper = MongoClientWrapper(
                model=TestModel,
                collection_name="test",
                database_name="test_db"
            )

            # Create a mock document with ObjectId
            test_id = ObjectId()
            doc = {
                "_id": test_id,
                "name": "Test"
            }

            parsed = wrapper._parse_single_document(doc)
            assert parsed.id == str(test_id)
            assert parsed.name == "Test"

    def test_parse_single_document_with_datetime(self):
        """Test parsing MongoDB documents with datetime conversion."""
        class TestModel(BaseModel):
            id: str = Field(alias="_id")
            created_at: str  # Should be ISO string

        with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
            wrapper = MongoClientWrapper(
                model=TestModel,
                collection_name="test",
                database_name="test_db"
            )

            now = datetime.now(timezone.utc)
            doc = {
                "_id": ObjectId(),
                "created_at": now
            }

            parsed = wrapper._parse_single_document(doc)
            assert isinstance(parsed.created_at, str)
            assert now.isoformat() == parsed.created_at


class TestKnowledgeJobDAO:
    """Test KnowledgeJobDAO operations."""

    def test_knowledge_job_creation_fields(self):
        """Test that KnowledgeJobCreate model has required fields."""
        job_data = KnowledgeJobCreate(
            name="Test Job",
            description="Test Description",
            batch_size=50,
            save_to_file=True,
            write_consolidated_file=False,
            clear_collection_before_start=False,
            check_duplicates_before_insert=True
        )

        assert job_data.name == "Test Job"
        assert job_data.description == "Test Description"
        assert job_data.batch_size == 50
        assert job_data.save_to_file is True

    def test_knowledge_job_model_defaults(self):
        """Test that KnowledgeJob model has proper defaults."""
        now = datetime.utcnow()
        job = KnowledgeJob(
            knowledge_source_config_id="config_123",
            user_id="user_123",
            created_by="user_123",
            created_at=now,
            status="created",
            name="Test Job",
            description="Description",
            batch_size=100,
            save_to_file=True,
            write_consolidated_file=False,
            clear_collection_before_start=False,
            check_duplicates_before_insert=False
        )

        assert job.knowledge_source_config_id == "config_123"
        assert job.user_id == "user_123"
        assert job.status == "created"
        assert job.batch_size == 100

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_initialization(self, mock_client):
        """Test that KnowledgeJobDAO initializes without errors."""
        # Mock the MongoDB client and collection
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value = mock_mongo_client

        # This should not raise an exception
        dao = KnowledgeJobDAO()
        assert dao.collection_name == "knowledge_jobs"
        assert dao.model == KnowledgeJob

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_create_job(self, mock_client):
        """Test creating a knowledge job through DAO."""
        # Mock the MongoDB client and collection
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Mock the insert_one result
        mock_result = MagicMock()
        inserted_id = ObjectId()
        mock_result.inserted_id = inserted_id
        mock_collection.insert_one.return_value = mock_result

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()

        job_data = KnowledgeJobCreate(
            name="Test Job",
            description="Test",
            batch_size=50,
            save_to_file=True,
            write_consolidated_file=False,
            clear_collection_before_start=False,
            check_duplicates_before_insert=True
        )

        job_id = dao.create_job(
            job_data=job_data,
            config_id="config_123",
            user_id="user_123"
        )

        assert job_id == str(inserted_id)
        mock_collection.insert_one.assert_called_once()

        # Verify the inserted document structure
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["name"] == "Test Job"
        assert call_args["knowledge_source_config_id"] == "config_123"
        assert call_args["user_id"] == "user_123"

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_get_job(self, mock_client):
        """Test retrieving a knowledge job by ID."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        job_id = ObjectId()
        mock_collection.find_one.return_value = {
            "_id": job_id,
            "knowledge_source_config_id": "config_123",
            "user_id": "user_123",
            "created_by": "user_123",
            "created_at": datetime.utcnow(),
            "status": "created",
            "name": "Test Job",
            "description": "Description",
            "batch_size": 100,
            "save_to_file": True,
            "write_consolidated_file": False,
            "clear_collection_before_start": False,
            "check_duplicates_before_insert": False
        }

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()
        job = dao.get_job(str(job_id), "user_123")

        assert job is not None
        assert job.knowledge_source_config_id == "config_123"
        assert job.name == "Test Job"

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_list_jobs(self, mock_client):
        """Test listing knowledge jobs for a user."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        job_id_1 = ObjectId()
        job_id_2 = ObjectId()

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": job_id_1,
                "knowledge_source_config_id": "config_1",
                "user_id": "user_123",
                "created_by": "user_123",
                "created_at": datetime.utcnow(),
                "status": "created",
                "name": "Job 1",
                "description": "Desc 1",
                "batch_size": 100,
                "save_to_file": True,
                "write_consolidated_file": False,
                "clear_collection_before_start": False,
                "check_duplicates_before_insert": False
            },
            {
                "_id": job_id_2,
                "knowledge_source_config_id": "config_2",
                "user_id": "user_123",
                "created_by": "user_123",
                "created_at": datetime.utcnow(),
                "status": "created",
                "name": "Job 2",
                "description": "Desc 2",
                "batch_size": 50,
                "save_to_file": False,
                "write_consolidated_file": True,
                "clear_collection_before_start": False,
                "check_duplicates_before_insert": True
            }
        ]
        mock_collection.find.return_value = mock_cursor

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()
        jobs = dao.list_jobs(user_id="user_123", skip=0, limit=10)

        assert len(jobs) == 2
        assert jobs[0].name == "Job 1"
        assert jobs[1].name == "Job 2"

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_update_status(self, mock_client):
        """Test updating knowledge job status."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        job_id = ObjectId()
        updated_doc = {
            "_id": job_id,
            "knowledge_source_config_id": "config_123",
            "user_id": "user_123",
            "created_by": "user_123",
            "created_at": datetime.utcnow(),
            "status": "running",
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "name": "Test Job",
            "description": "Description",
            "batch_size": 100,
            "save_to_file": True,
            "write_consolidated_file": False,
            "clear_collection_before_start": False,
            "check_duplicates_before_insert": False
        }

        mock_collection.find_one_and_update.return_value = updated_doc

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()
        job = dao.update_job_status(
            job_id=str(job_id),
            user_id="user_123",
            status=JobStatus.RUNNING
        )

        assert job is not None
        assert job.status == "running"


class TestNotificationModel:
    """Test Notification model operations."""

    def test_notification_creation(self):
        """Test creating a Notification."""
        notification = Notification(
            user_id="user_123",
            title="Test Title",
            message="Test Message",
            notification_type="info",
            created_at=datetime.utcnow()
        )

        assert notification.user_id == "user_123"
        assert notification.title == "Test Title"
        assert notification.message == "Test Message"
        assert notification.notification_type == "info"

    def test_notification_with_metadata(self):
        """Test Notification with additional metadata."""
        metadata = {
            "action": "job_completed",
            "job_id": "job_123"
        }
        notification = Notification(
            user_id="user_123",
            title="Job Completed",
            message="Your job has completed successfully",
            notification_type="success",
            metadata=metadata,
            created_at=datetime.utcnow()
        )

        assert notification.metadata == metadata

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_notification_service_initialization(self, mock_client):
        """Test NotificationService initialization."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_client.return_value = mock_mongo_client

        service = NotificationService()
        assert service.collection_name == "notifications"


class TestPersistenceImports:
    """Test that all persistence imports work correctly."""

    def test_knowledge_job_dao_imports(self):
        """Test that KnowledgeJobDAO imports are correct."""
        from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO
        assert KnowledgeJobDAO is not None

    def test_auth_dao_imports(self):
        """Test that AuthDAO imports are correct."""
        from datapilotflow.infrastructure.dao.auth import AuthDAO
        assert AuthDAO is not None

    def test_notification_service_imports(self):
        """Test that NotificationService imports are correct."""
        from datapilotflow.infrastructure.dao.notification import NotificationService
        assert NotificationService is not None

    def test_tool_dao_imports(self):
        """Test that ToolDAO imports are correct."""
        from datapilotflow.infrastructure.dao.tool import ToolDAO
        assert ToolDAO is not None

    def test_mongo_client_wrapper_imports(self):
        """Test that MongoClientWrapper imports are correct."""
        from datapilotflow.infrastructure.mongo.client import MongoClientWrapper
        assert MongoClientWrapper is not None

    def test_domain_config_available_to_persistence(self):
        """Test that domain config is accessible from persistence."""
        from datapilotflow.domain.config import settings
        assert settings is not None
        assert hasattr(settings, 'MONGO_DB_NAME')
        assert hasattr(settings, 'MONGO_CONN_STR')


class TestDAOErrorHandling:
    """Test error handling in DAO operations."""

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_get_nonexistent_job(self, mock_client):
        """Test getting a nonexistent job returns None."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find_one.return_value = None

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()
        job = dao.get_job("nonexistent_id", "user_123")

        assert job is None

    @patch('datapilotflow.infrastructure.mongo.client.get_mongo_client')
    def test_knowledge_job_dao_create_job_failure(self, mock_client):
        """Test handling of creation failure."""
        mock_mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Mock insert_one to raise exception
        mock_collection.insert_one.side_effect = Exception("Database error")

        mock_client.return_value = mock_mongo_client

        dao = KnowledgeJobDAO()

        job_data = KnowledgeJobCreate(
            name="Test Job",
            description="Test",
            batch_size=50,
            save_to_file=True,
            write_consolidated_file=False,
            clear_collection_before_start=False,
            check_duplicates_before_insert=True
        )

        # Should return None on error
        job_id = dao.create_job(
            job_data=job_data,
            config_id="config_123",
            user_id="user_123"
        )

        assert job_id is None
