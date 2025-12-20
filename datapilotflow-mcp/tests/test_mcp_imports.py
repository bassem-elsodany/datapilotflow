"""
Test MCP package imports and initialization.
"""

import pytest


class TestMCPPackageImports:
    """Test that MCP package can be imported."""

    def test_import_mcp_server(self):
        """Test importing MCP server."""
        from datapilotflow.mcp.server import create_mcp_server

        assert create_mcp_server

    def test_import_rag_tools(self):
        """Test importing RAG tools."""
        from datapilotflow.mcp.tools.rag_tools import (
            RAGQueryInput,
            RAGQueryOutput,
            RAGToolDefinition,
        )

        assert RAGQueryInput
        assert RAGQueryOutput
        assert RAGToolDefinition

    def test_import_rag_adapter(self):
        """Test importing RAG adapter."""
        from datapilotflow.mcp.adapters.rag_adapter import RAGAdapter

        assert RAGAdapter

    def test_import_mcp_config(self):
        """Test importing MCP config."""
        from datapilotflow.mcp.config import settings

        assert settings
        assert settings.MCP_SERVER_HOST
        assert settings.MCP_SERVER_PORT

    def test_import_cli(self):
        """Test importing CLI."""
        from datapilotflow.mcp.cli.run_server import main

        assert main


class TestRAGToolSchemas:
    """Test RAG tool schema validation."""

    def test_rag_query_input_valid(self):
        """Test RAGQueryInput with valid data."""
        from datapilotflow.mcp.tools.rag_tools import RAGQueryInput

        input_data = RAGQueryInput(
            search_query=["q1", "q2", "q3", "q4", "q5"],
            collection_name="test_collection",
            user_id="user1",
            embedding_provider_id="openai",
            embedding_model_name="text-embedding-3-small",
            vector_dimension=1536,
            conversation_id="conv1",
        )

        assert input_data.search_query == ["q1", "q2", "q3", "q4", "q5"]
        assert input_data.collection_name == "test_collection"
        assert input_data.user_id == "user1"
        assert input_data.top_k == 5  # Default
        assert input_data.enable_reranking is False  # Default

    def test_rag_query_input_custom_top_k(self):
        """Test RAGQueryInput with custom top_k."""
        from datapilotflow.mcp.tools.rag_tools import RAGQueryInput

        input_data = RAGQueryInput(
            search_query=["q1", "q2", "q3", "q4", "q5"],
            collection_name="test",
            user_id="user1",
            embedding_provider_id="openai",
            embedding_model_name="model",
            top_k=10,
            conversation_id="conv1",
        )

        assert input_data.top_k == 10

    def test_rag_query_output_valid(self):
        """Test RAGQueryOutput with valid data."""
        from datapilotflow.mcp.tools.rag_tools import RAGQueryOutput

        output = RAGQueryOutput(
            documents=[
                {
                    "id": "1",
                    "content": "test content",
                    "source": "http://example.com",
                    "metadata": {},
                }
            ],
            metadata={
                "total_documents": 1,
                "relevant_documents": 1,
                "source_count": 1,
                "sources": ["http://example.com"],
            },
        )

        assert len(output.documents) == 1
        assert output.documents[0]["id"] == "1"
        assert output.error is None

    def test_rag_query_output_with_error(self):
        """Test RAGQueryOutput with error."""
        from datapilotflow.mcp.tools.rag_tools import RAGQueryOutput

        output = RAGQueryOutput(
            documents=[],
            metadata={},
            error="Test error message",
        )

        assert output.error == "Test error message"
        assert len(output.documents) == 0

    def test_rag_tool_definition(self):
        """Test RAGToolDefinition."""
        from datapilotflow.mcp.tools.rag_tools import RAGToolDefinition

        assert RAGToolDefinition.name == "knowledge_expert"
        assert "retrieve" in RAGToolDefinition.description.lower()

    def test_rag_tool_definition_mcp_format(self):
        """Test RAGToolDefinition MCP format."""
        from datapilotflow.mcp.tools.rag_tools import RAGToolDefinition

        mcp_def = RAGToolDefinition.get_mcp_tool_definition()

        assert mcp_def["name"] == "knowledge_expert"
        assert "inputSchema" in mcp_def
        assert "properties" in mcp_def["inputSchema"]
        assert "search_query" in mcp_def["inputSchema"]["properties"]


class TestMCPServerCreation:
    """Test MCP server creation."""

    def test_create_mcp_server(self):
        """Test creating MCP server."""
        from datapilotflow.mcp.server import create_mcp_server

        server = create_mcp_server()
        assert server is not None
        assert hasattr(server, "run")

    def test_mcp_server_has_knowledge_expert_tool(self):
        """Test that MCP server has knowledge_expert tool."""
        from datapilotflow.mcp.server import mcp

        # Check that the tool is registered
        assert mcp is not None
        # Tools are registered as methods on the FastMCP instance
        assert hasattr(mcp, "tools")


class TestRAGAdapter:
    """Test RAG adapter initialization."""

    def test_rag_adapter_creation(self):
        """Test creating RAG adapter."""
        from datapilotflow.mcp.adapters.rag_adapter import RAGAdapter

        adapter = RAGAdapter()
        assert adapter is not None
        assert hasattr(adapter, "execute_knowledge_expert")

    def test_rag_adapter_has_execute_method(self):
        """Test that RAG adapter has execute method."""
        from datapilotflow.mcp.adapters.rag_adapter import RAGAdapter

        adapter = RAGAdapter()
        assert callable(adapter.execute_knowledge_expert)


class TestMCPConfiguration:
    """Test MCP configuration."""

    def test_default_settings(self):
        """Test default MCP settings."""
        from datapilotflow.mcp.config import settings

        assert settings.MCP_SERVER_HOST == "0.0.0.0"
        assert settings.MCP_SERVER_PORT == 65510
        assert settings.MCP_SERVER_NAME == "datapilotflow"
        assert settings.MCP_LOG_LEVEL == "INFO"
        assert settings.MCP_ENABLED_TOOLS == "knowledge_expert"

    def test_settings_immutable(self):
        """Test that settings is properly configured."""
        from datapilotflow.mcp.config import settings

        # Should be able to access settings properties
        assert hasattr(settings, "MCP_SERVER_HOST")
        assert hasattr(settings, "MCP_SERVER_PORT")
        assert hasattr(settings, "MCP_SERVER_NAME")
