"""Simple tests to verify imports work correctly."""


def test_imports_work():
    """Test that all imports are working correctly."""
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

    assert MongoClientWrapper is not None
    assert User is not None
    assert KnowledgeJob is not None
    assert KnowledgeJobCreate is not None
    assert JobStatus is not None
    assert Notification is not None
    assert KnowledgeJobDAO is not None
    assert NotificationService is not None


def test_mongo_wrapper_initialization():
    """Test MongoClientWrapper can be instantiated."""
    from unittest.mock import patch, MagicMock
    from pydantic import BaseModel
    from datapilotflow.infrastructure.mongo.client import MongoClientWrapper

    class TestModel(BaseModel):
        name: str
        value: int

    with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
        wrapper = MongoClientWrapper(
            model=TestModel,
            collection_name="test_collection",
            database_name="test_db",
            mongodb_uri="mongodb://localhost:27017"
        )
        assert wrapper.model == TestModel
        assert wrapper.collection_name == "test_collection"


def test_knowledge_job_model():
    """Test KnowledgeJob model creation."""
    from datetime import datetime
    from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob

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
    assert job.name == "Test Job"
    assert job.batch_size == 100


def test_knowledge_job_create_model():
    """Test KnowledgeJobCreate model."""
    from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJobCreate

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
    assert job_data.batch_size == 50


def test_notification_model():
    """Test Notification model."""
    from datetime import datetime
    from datapilotflow.domain.notification import Notification

    notification = Notification(
        user_id="user_123",
        title="Test Title",
        message="Test Message",
        notification_type="info",
        created_at=datetime.utcnow()
    )

    assert notification.user_id == "user_123"
    assert notification.title == "Test Title"


def test_knowledge_job_dao_imports():
    """Test KnowledgeJobDAO can be imported."""
    from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO
    from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob

    assert KnowledgeJobDAO is not None
    # Verify DAO uses correct model
    from unittest.mock import patch, MagicMock
    with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
        dao = KnowledgeJobDAO()
        assert dao.model == KnowledgeJob
        assert dao.collection_name == "knowledge_jobs"


def test_auth_dao_imports():
    """Test AuthDAO can be imported."""
    from datapilotflow.infrastructure.dao.auth import AuthDAO
    from datapilotflow.domain.user import User

    assert AuthDAO is not None
    from unittest.mock import patch
    with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
        dao = AuthDAO()
        assert dao.model == User


def test_notification_service_imports():
    """Test NotificationService can be imported."""
    from datapilotflow.infrastructure.dao.notification import NotificationService

    assert NotificationService is not None
    from unittest.mock import patch
    with patch('datapilotflow.infrastructure.mongo.client.get_mongo_client'):
        service = NotificationService()
        assert service.collection_name == "notifications"


def test_tool_dao_imports():
    """Test ToolDAO can be imported."""
    from datapilotflow.infrastructure.dao.tool import ToolDAO

    assert ToolDAO is not None


def test_domain_config_available():
    """Test domain config is accessible."""
    from datapilotflow.domain.config import settings

    assert settings is not None
    assert hasattr(settings, 'MONGO_DB_NAME')
    assert hasattr(settings, 'MONGO_CONN_STR')
