"""Integration tests for supervisor agent tool creation pipeline.

Tests:
1. ToolRegistry functionality
2. SupervisorToolFactory tool creation
3. Tool initialization from configuration
4. Service initialization and tool management
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.supervisor_agent.tools import ToolRegistry
from src.agents.supervisor_agent.tool_factory import SupervisorToolFactory
from src.agents.supervisor_agent.tool_initialization import (
    create_knowledge_expert_tool,
    initialize_tools_from_config,
)
from src.agents.supervisor_agent.service import SupervisorAgentService
from src.agents.supervisor_agent.context import Context
from src.domain.conversation.models import AssistantConfig, ConversationSession
from src.domain.tool.models import Tool, ToolType, PromptBasedToolConfig


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_register_single_tool(self):
        """Test registering a single tool."""
        registry = ToolRegistry()
        mock_tool = MagicMock(name="test_tool")

        registry.register("tool_1", mock_tool)

        assert "tool_1" in registry
        assert registry.get("tool_1") == mock_tool

    def test_register_many_tools(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        tools = {
            "tool_1": MagicMock(name="tool_1"),
            "tool_2": MagicMock(name="tool_2"),
            "tool_3": MagicMock(name="tool_3"),
        }

        registry.register_many(tools)

        assert len(registry) == 3
        assert registry.list_ids() == ["tool_1", "tool_2", "tool_3"]

    def test_get_all_tools(self):
        """Test getting all tools."""
        registry = ToolRegistry()
        tools = {
            "tool_1": MagicMock(name="tool_1"),
            "tool_2": MagicMock(name="tool_2"),
        }
        registry.register_many(tools)

        all_tools = registry.get_all()

        assert len(all_tools) == 2
        assert all_tools == [tools["tool_1"], tools["tool_2"]]

    def test_get_by_ids(self):
        """Test getting tools by IDs."""
        registry = ToolRegistry()
        tools = {
            "tool_1": MagicMock(name="tool_1"),
            "tool_2": MagicMock(name="tool_2"),
            "tool_3": MagicMock(name="tool_3"),
        }
        registry.register_many(tools)

        selected = registry.get_by_ids(["tool_1", "tool_3"])

        assert len(selected) == 2
        assert selected == [tools["tool_1"], tools["tool_3"]]

    def test_get_tool_not_found(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()

        tool = registry.get("nonexistent")

        assert tool is None

    def test_bracket_notation_access(self):
        """Test accessing tools with bracket notation."""
        registry = ToolRegistry()
        mock_tool = MagicMock(name="test_tool")
        registry.register("tool_1", mock_tool)

        tool = registry["tool_1"]

        assert tool == mock_tool

    def test_bracket_notation_key_error(self):
        """Test bracket notation raises KeyError for missing tool."""
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            _ = registry["nonexistent"]


class TestToolCreation:
    """Test tool creation via SupervisorToolFactory."""

    def test_create_prompt_based_tool(self):
        """Test creating a prompt-based tool."""
        mock_llm = AsyncMock()

        tool = Tool(
            id="test_tool",
            name="test_tool",
            display_name="Test Tool",
            description="A test tool",
            tool_type=ToolType.PROMPT_BASED,
            user_id="user_1",
            prompt_config=PromptBasedToolConfig(
                system_prompt="You are a test assistant.",
                temperature=0.7,
            ),
        )

        created_tool = SupervisorToolFactory.create_prompt_based_tool(
            tool=tool,
            llm_client=mock_llm,
            rag_context="",
        )

        assert created_tool is not None
        assert created_tool.name == "test_tool"
        assert created_tool.description == "A test tool"

    def test_create_tool_without_prompt_config(self):
        """Test creating tool without prompt_config raises error."""
        mock_llm = AsyncMock()

        tool = Tool(
            id="test_tool",
            name="test_tool",
            display_name="Test Tool",
            description="A test tool",
            tool_type=ToolType.PROMPT_BASED,
            user_id="user_1",
            prompt_config=None,  # Missing config
        )

        with pytest.raises(ValueError, match="prompt_config required"):
            SupervisorToolFactory.create_prompt_based_tool(
                tool=tool,
                llm_client=mock_llm,
            )


class TestToolInitialization:
    """Test tool initialization from configuration."""

    def test_create_knowledge_expert_tool(self):
        """Test creating knowledge expert RAG tool."""
        mock_llm = AsyncMock()

        tool = create_knowledge_expert_tool(mock_llm)

        assert tool is not None
        assert tool.name == "knowledge_expert"
        assert "knowledge base" in tool.description.lower()

    def test_initialize_tools_from_config_empty(self):
        """Test initialization with no tools configured."""
        mock_llm = AsyncMock()
        config = AssistantConfig(enabled=True, tools=None)

        registry = initialize_tools_from_config(
            assistant_config=config,
            llm_client=mock_llm,
            tool_instances={},
        )

        # Should still have knowledge_expert
        assert "knowledge_expert" in registry
        assert len(registry) == 1

    def test_initialize_tools_from_config_with_tools(self):
        """Test initialization with configured tools."""
        mock_llm = AsyncMock()

        tool_1 = Tool(
            id="tool_1",
            name="tool_1",
            display_name="Tool 1",
            description="First tool",
            tool_type=ToolType.PROMPT_BASED,
            user_id="user_1",
            prompt_config=PromptBasedToolConfig(
                system_prompt="Test prompt",
            ),
        )

        config = AssistantConfig(
            enabled=True,
            tools=["tool_1"],
        )

        registry = initialize_tools_from_config(
            assistant_config=config,
            llm_client=mock_llm,
            tool_instances={"tool_1": tool_1},
        )

        assert len(registry) == 2  # knowledge_expert + tool_1
        assert "knowledge_expert" in registry
        assert "tool_1" in registry

    def test_initialize_missing_tool_instance(self):
        """Test initialization when tool instance is missing."""
        mock_llm = AsyncMock()

        config = AssistantConfig(
            enabled=True,
            tools=["missing_tool"],
        )

        registry = initialize_tools_from_config(
            assistant_config=config,
            llm_client=mock_llm,
            tool_instances={},  # Empty - tool not found
        )

        # Should have knowledge_expert but not the missing tool
        assert "knowledge_expert" in registry
        assert "missing_tool" not in registry


class TestSupervisorAgentService:
    """Test SupervisorAgentService."""

    def test_service_initialization(self):
        """Test service initialization."""
        context = Context(
            model="anthropic/claude-sonnet-4-5-20250929",
            max_search_results=10,
        )

        service = SupervisorAgentService(context=context)

        assert service.context == context
        assert service.llm_client is None
        assert service.tool_registry is None
        assert service.graph is None

    def test_service_get_tool_info_uninitialized(self):
        """Test getting tool info before initialization."""
        service = SupervisorAgentService()

        info = service.get_tool_info()

        assert info["count"] == 0
        assert info["tools"] == []
        assert info["has_knowledge_expert"] is False

    @patch("src.agents.supervisor_agent.service.load_chat_model")
    def test_service_initialize_for_conversation_sync(self, mock_load_model):
        """Test synchronous service initialization for conversation."""
        # Setup
        mock_llm = MagicMock()
        mock_load_model.return_value = mock_llm

        conversation = ConversationSession(
            _id="conv_1",
            user_id="user_1",
            created_at=datetime.now(tz=UTC),
            last_updated=datetime.now(tz=UTC),
            messages=[],
            assistant_config=AssistantConfig(enabled=True, tools=[]),
        )

        service = SupervisorAgentService()

        # Execute
        service.initialize_for_conversation_sync(
            conversation=conversation,
            tool_instances={},
        )

        # Verify
        assert service.llm_client is not None
        assert service.tool_registry is not None
        assert service.graph is not None
        assert "knowledge_expert" in service.tool_registry

    def test_service_initialize_non_assistant_conversation(self):
        """Test initializing service with non-assistant conversation."""
        conversation = ConversationSession(
            _id="conv_1",
            user_id="user_1",
            created_at=datetime.now(tz=UTC),
            last_updated=datetime.now(tz=UTC),
            messages=[],
            assistant_config=AssistantConfig(enabled=False),  # RAG mode
        )

        service = SupervisorAgentService()

        with pytest.raises(ValueError, match="not in assistant/supervisor mode"):
            service.initialize_for_conversation_sync(
                conversation=conversation,
                tool_instances={},
            )

    def test_service_without_assistant_config(self):
        """Test initializing service with no assistant config."""
        conversation = ConversationSession(
            _id="conv_1",
            user_id="user_1",
            created_at=datetime.now(tz=UTC),
            last_updated=datetime.now(tz=UTC),
            messages=[],
            assistant_config=None,  # No assistant config
        )

        service = SupervisorAgentService()

        with pytest.raises(ValueError, match="not in assistant/supervisor mode"):
            service.initialize_for_conversation_sync(
                conversation=conversation,
                tool_instances={},
            )


class TestIntegration:
    """Integration tests for complete pipeline."""

    @patch("src.agents.supervisor_agent.service.load_chat_model")
    def test_complete_tool_creation_pipeline(self, mock_load_model):
        """Test complete pipeline from config to service."""
        # Setup
        mock_llm = MagicMock()
        mock_load_model.return_value = mock_llm

        tool_1 = Tool(
            id="tool_1",
            name="calculator",
            display_name="Calculator",
            description="Performs calculations",
            tool_type=ToolType.PROMPT_BASED,
            user_id="user_1",
            prompt_config=PromptBasedToolConfig(
                system_prompt="You are a calculator.",
            ),
        )

        conversation = ConversationSession(
            _id="conv_1",
            user_id="user_1",
            created_at=datetime.now(tz=UTC),
            last_updated=datetime.now(tz=UTC),
            messages=[],
            assistant_config=AssistantConfig(
                enabled=True,
                tools=["tool_1"],
                tool_instructions="Use calculator tool",
            ),
        )

        # Execute
        service = SupervisorAgentService()
        service.initialize_for_conversation_sync(
            conversation=conversation,
            tool_instances={"tool_1": tool_1},
            rag_context="Test RAG context",
        )

        # Verify
        assert service.tool_registry is not None
        assert len(service.tool_registry) == 2  # knowledge_expert + calculator
        assert "knowledge_expert" in service.tool_registry
        assert "calculator" in service.tool_registry

        tool_info = service.get_tool_info()
        assert tool_info["count"] == 2
        assert tool_info["has_knowledge_expert"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
