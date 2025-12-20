"""Real tests for datapilotflow-domain - test actual model functionality."""

import pytest
from datetime import datetime
from datapilotflow.domain.user.user import User
from datapilotflow.domain.user.role_model import Role
from datapilotflow.domain.agent.models import Agent
from datapilotflow.domain.knowledge.knowledge import Document, Chunk
from datapilotflow.domain.conversation.models import Message, Conversation
from datapilotflow.domain.embedding.embedding_model import EmbeddingModel
from datapilotflow.domain.generative.generative_model import GenerativeModel


class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self):
        """Test creating a user."""
        user = User(
            id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz",
            full_name="John Doe"
        )
        assert user.id == "user_123"
        assert user.email == "john@example.com"
        assert user.username == "john_doe"
        assert user.full_name == "John Doe"

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
            id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz"
        )
        assert user.is_active is True


class TestDocumentAndChunkModel:
    """Test Document and Chunk models."""

    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            id="doc_123",
            title="Test Document",
            content="This is test content",
            source_url="https://example.com",
            source_type="webpage"
        )
        assert doc.id == "doc_123"
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.source_url == "https://example.com"

    def test_create_chunk(self):
        """Test creating a chunk."""
        chunk = Chunk(
            id="chunk_123",
            text="This is chunk text",
            document_id="doc_123",
            chunk_index=0,
            tokens_count=5
        )
        assert chunk.id == "chunk_123"
        assert chunk.text == "This is chunk text"
        assert chunk.document_id == "doc_123"
        assert chunk.chunk_index == 0
        assert chunk.tokens_count == 5


class TestConversationModel:
    """Test Conversation and Message models."""

    def test_create_message(self):
        """Test creating a message."""
        message = Message(
            id="msg_123",
            role="user",
            content="Hello, how are you?",
            conversation_id="conv_123"
        )
        assert message.id == "msg_123"
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.conversation_id == "conv_123"

    def test_create_conversation(self):
        """Test creating a conversation."""
        conv = Conversation(
            id="conv_123",
            user_id="user_123",
            title="Test Conversation",
            messages=[]
        )
        assert conv.id == "conv_123"
        assert conv.user_id == "user_123"
        assert conv.title == "Test Conversation"
        assert len(conv.messages) == 0


class TestEmbeddingModel:
    """Test Embedding model."""

    def test_create_embedding_model(self):
        """Test creating an embedding model configuration."""
        embedding = EmbeddingModel(
            id="embedding_123",
            model_name="sentence-transformers/all-mpnet-base-v2",
            provider="huggingface",
            embedding_dimension=768,
            is_default=True
        )
        assert embedding.id == "embedding_123"
        assert embedding.model_name == "sentence-transformers/all-mpnet-base-v2"
        assert embedding.provider == "huggingface"
        assert embedding.embedding_dimension == 768
        assert embedding.is_default is True


class TestGenerativeModel:
    """Test Generative LLM model."""

    def test_create_generative_model(self):
        """Test creating a generative model configuration."""
        model = GenerativeModel(
            id="llm_123",
            model_name="gpt-4",
            provider="openai",
            model_type="chat",
            api_key="sk-xyz",
            temperature=0.7,
            max_tokens=2000
        )
        assert model.id == "llm_123"
        assert model.model_name == "gpt-4"
        assert model.provider == "openai"
        assert model.model_type == "chat"
        assert model.temperature == 0.7
        assert model.max_tokens == 2000


class TestAgentModel:
    """Test Agent model."""

    def test_create_agent(self):
        """Test creating an agent."""
        agent = Agent(
            id="agent_123",
            name="Test Agent",
            agent_type="rag",
            description="A test RAG agent",
            user_id="user_123"
        )
        assert agent.id == "agent_123"
        assert agent.name == "Test Agent"
        assert agent.agent_type == "rag"
        assert agent.user_id == "user_123"


class TestModelSerialization:
    """Test that models can be serialized to JSON."""

    def test_user_to_dict(self):
        """Test user model serialization."""
        user = User(
            id="user_123",
            email="john@example.com",
            username="john_doe",
            hashed_password="hash_xyz"
        )
        user_dict = user.model_dump()
        assert user_dict["id"] == "user_123"
        assert user_dict["email"] == "john@example.com"

    def test_document_to_json(self):
        """Test document model JSON serialization."""
        doc = Document(
            id="doc_123",
            title="Test",
            content="Content",
            source_url="https://example.com",
            source_type="webpage"
        )
        json_str = doc.model_dump_json()
        assert "doc_123" in json_str
        assert "Test" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
