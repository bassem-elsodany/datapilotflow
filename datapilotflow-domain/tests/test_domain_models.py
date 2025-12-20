"""Real tests for datapilotflow-domain - test actual model functionality."""

import pytest
from datetime import datetime
from datapilotflow.domain.user.user import User
from datapilotflow.domain.user.role_model import Role
from datapilotflow.domain.agent.models import Agent
from datapilotflow.domain.knowledge.knowledge import Knowledge, KnowledgeExtract
from datapilotflow.domain.knowledge.document_splitter import DocumentSplitter
from datapilotflow.domain.conversation.models import ConversationMessage, ConversationSession
from datapilotflow.domain.embedding.embedding_model import EmbeddingModel
from datapilotflow.domain.generative.generative_model import GenerativeModel
from datapilotflow.domain.knowledge.job_timeline import JobTimeline
from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob, JobStatus
from datapilotflow.domain.notification.notification import Notification


class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self):
        """Test creating a user."""
        user = User(
            _id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz",
            name="John Doe"
        )
        assert user.id == "user_123"  # _id is aliased as id
        assert user.email == "john@example.com"
        assert user.username == "john_doe"
        assert user.name == "John Doe"

    def test_user_validation_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            User(
                id="user_123",
                email="not_an_email",
                username="john_doe",
                hashed_password="hash_xyz"
            )

    def test_user_default_values(self):
        """Test user default values."""
        user = User(
            _id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz",
            name="John Doe"
        )
        assert user.is_active is True
        assert len(user.role_ids) == 0


class TestKnowledgeModel:
    """Test Knowledge and KnowledgeExtract models."""

    def test_create_knowledge_extract(self):
        """Test creating a knowledge extract."""
        knowledge = KnowledgeExtract(
            id="know_123",
            name="Test Knowledge",
            description="Test knowledge source",
            url="https://example.com",
            enabled=True,
            scraping_mode="crawl"
        )
        assert knowledge.id == "know_123"
        assert knowledge.name == "Test Knowledge"
        assert knowledge.url == "https://example.com"
        assert knowledge.enabled is True

    def test_create_knowledge(self):
        """Test creating a knowledge model."""
        knowledge = Knowledge(
            id="know_123",
            name="Test Knowledge",
            description="Test knowledge source",
            url="https://example.com",
            enabled=True,
            scraping_mode="crawl"
        )
        assert knowledge.id == "know_123"
        assert knowledge.name == "Test Knowledge"
        assert knowledge.enabled is True

    def test_knowledge_defaults(self):
        """Test knowledge default values."""
        knowledge = Knowledge(
            id="know_123",
            name="Test",
            description="Desc",
            url="https://example.com"
        )
        assert knowledge.enabled is True
        assert knowledge.scraping_mode == "crawl"
        assert knowledge.crawl_depth == 4


class TestDocumentSplitterModel:
    """Test DocumentSplitter model."""

    def test_create_document_splitter(self):
        """Test creating a document splitter configuration."""
        splitter = DocumentSplitter(
            id="split_123",
            user_id="user_123",
            name="Test Splitter",
            chunk_size=1000,
            chunk_overlap=100,
            splitter_type="text",
            created_by="user_123",
            updated_by="user_123"
        )
        assert splitter.id == "split_123"
        assert splitter.user_id == "user_123"
        assert splitter.name == "Test Splitter"
        assert splitter.chunk_size == 1000
        assert splitter.chunk_overlap == 100


class TestConversationModel:
    """Test Conversation and Message models."""

    def test_create_message(self):
        """Test creating a conversation message."""
        message = ConversationMessage(
            _id="msg_123",
            role="user",
            content="Hello, how are you?",
            conversation_id="conv_123",
            user_id="user_123",
            timestamp=datetime.utcnow(),
            message_index=0
        )
        assert message._id == "msg_123"
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.conversation_id == "conv_123"

    def test_create_conversation(self):
        """Test creating a conversation session."""
        conv = ConversationSession(
            _id="conv_123",
            user_id="user_123",
            agent_id="agent_123",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            name="Test Conversation"
        )
        assert conv._id == "conv_123"
        assert conv.user_id == "user_123"
        assert conv.agent_id == "agent_123"
        assert conv.name == "Test Conversation"


class TestEmbeddingModel:
    """Test Embedding model."""

    def test_create_embedding_model(self):
        """Test creating an embedding model configuration."""
        embedding = EmbeddingModel(
            id="embedding_123",
            name="Test Embedding",
            endpoint="https://api.example.com/embed",
            supported_models=["model-1", "model-2"],
            api_key="test-key-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="user_123",
            updated_by="user_123"
        )
        assert embedding.id == "embedding_123"
        assert embedding.name == "Test Embedding"
        assert embedding.endpoint == "https://api.example.com/embed"
        assert len(embedding.supported_models) == 2


class TestGenerativeModel:
    """Test Generative LLM model."""

    def test_create_generative_model(self):
        """Test creating a generative model configuration."""
        model = GenerativeModel(
            id="llm_123",
            name="Test LLM",
            endpoint="https://api.openai.com",
            supported_models=["gpt-4"],
            api_key="sk-xyz",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="user_123",
            updated_by="user_123"
        )
        assert model.id == "llm_123"
        assert model.name == "Test LLM"
        assert model.endpoint == "https://api.openai.com"
        assert len(model.supported_models) == 1


class TestAgentModel:
    """Test Agent model."""

    def test_create_agent(self):
        """Test creating an agent."""
        from datapilotflow.domain.agent.models import AgentType
        from datapilotflow.domain.conversation.models import VectorDatabaseConfig
        agent = Agent(
            _id="agent_123",
            name="Test Agent",
            agent_type=AgentType.RAG,
            user_id="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            vector_database=VectorDatabaseConfig()
        )
        assert agent._id == "agent_123"
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.RAG
        assert agent.user_id == "user_123"


class TestJobTimelineModel:
    """Test JobTimeline model."""

    def test_create_job_timeline(self):
        """Test creating a job timeline entry."""
        timeline = JobTimeline(
            id="timeline_123",
            job_id="job_123",
            user_id="user_123",
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow(),
            documents_processed=10,
            chunks_created=50
        )
        assert timeline.id == "timeline_123"
        assert timeline.job_id == "job_123"
        assert timeline.status == JobStatus.RUNNING
        assert timeline.documents_processed == 10


class TestKnowledgeJobModel:
    """Test KnowledgeJob model."""

    def test_create_knowledge_job(self):
        """Test creating a knowledge job."""
        job = KnowledgeJob(
            id="job_123",
            user_id="user_123",
            name="Test Job",
            knowledge_source_config_id="config_123",
            vectordb_collection_id="collection_123",
            created_by="user_123"
        )
        assert job.id == "job_123"
        assert job.user_id == "user_123"
        assert job.name == "Test Job"
        assert job.batch_size == 100  # default value


class TestNotificationModel:
    """Test Notification model."""

    def test_create_notification(self):
        """Test creating a notification."""
        from datapilotflow.domain.notification.notification import NotificationType
        notification = Notification(
            notification_id="notif_123",
            user_id="user_123",
            type=NotificationType.INFO,
            title="Test Notification",
            message="This is a test notification"
        )
        assert notification.notification_id == "notif_123"
        assert notification.user_id == "user_123"
        assert notification.type == NotificationType.INFO
        assert notification.title == "Test Notification"


class TestModelSerialization:
    """Test that models can be serialized to JSON."""

    def test_user_to_dict(self):
        """Test user model serialization."""
        user = User(
            _id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz",
            name="John Doe"
        )
        user_dict = user.model_dump()
        assert user_dict["id"] == "user_123"  # _id is aliased as id
        assert user_dict["email"] == "john@example.com"

    def test_knowledge_to_json(self):
        """Test knowledge model JSON serialization."""
        knowledge = Knowledge(
            id="know_123",
            name="Test",
            description="Desc",
            url="https://example.com",
            scraping_mode="crawl"
        )
        json_str = knowledge.model_dump_json()
        assert "know_123" in json_str
        assert "Test" in json_str

    def test_agent_creation(self):
        """Test agent can be created and accessed."""
        from datapilotflow.domain.agent.models import AgentType
        from datapilotflow.domain.conversation.models import VectorDatabaseConfig
        agent = Agent(
            _id="agent_123",
            name="Test Agent",
            agent_type=AgentType.RAG,
            user_id="user_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            vector_database=VectorDatabaseConfig()
        )
        assert agent._id == "agent_123"
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.RAG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
