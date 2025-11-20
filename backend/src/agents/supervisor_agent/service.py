"""Supervisor agent service layer.

Orchestrates tool initialization, graph creation, and conversation execution.
Handles LLM client creation, tool registry setup, and message streaming.
"""

from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime, UTC
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph
from loguru import logger

from src.agents.supervisor_agent.graph import create_graph
from src.agents.supervisor_agent.tool_initialization import (
    initialize_tools_from_config,
    initialize_tools_from_config_async,
)
from src.agents.supervisor_agent.tool_registry import ToolRegistry
from src.agents.supervisor_agent.utils import load_chat_model
from src.agents.supervisor_agent.state import State
from src.agents.supervisor_agent.context import Context
from src.domain.conversation.models import AssistantConfig, ConversationSession
from src.domain.tool.models import Tool


class SupervisorAgentService:
    """Service for running supervisor agent conversations."""

    def __init__(self, context: Optional[Context] = None):
        """Initialize supervisor agent service.

        Args:
            context: Optional Context with model and system prompt configuration.
                    If not provided, uses defaults from Context class.
        """
        self.context = context or Context()
        self.llm_client: Optional[BaseChatModel] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.graph: Optional[StateGraph] = None
        logger.info(f"SupervisorAgentService initialized with model: {self.context.model}")

    async def initialize_for_conversation(
        self,
        conversation: ConversationSession,
        tool_instances: Optional[Dict[str, Tool]] = None,
        rag_context: str = "",
        llm_client: Optional[BaseChatModel] = None,
    ) -> None:
        """Initialize agent for a specific conversation.

        Creates tools from conversation config and builds the graph.
        LLM client can be provided or will be created from context.

        Args:
            conversation: The conversation session with assistant config
            tool_instances: Dict mapping tool IDs to Tool domain objects
                           (typically fetched from database)
            rag_context: RAG context to inject into tool execution
            llm_client: Optional pre-created LLM client. If not provided, creates one from context.model

        Raises:
            ValueError: If conversation is not in assistant mode
        """
        if not conversation.assistant_config or not conversation.assistant_config.enabled:
            raise ValueError(
                f"Conversation {conversation._id} is not in assistant/supervisor mode"
            )

        logger.info(
            f"Initializing supervisor agent for conversation {conversation._id} "
            f"with tools: {conversation.assistant_config.tools}"
        )

        # Step 1: Set LLM client (provided or create new)
        if llm_client:
            self.llm_client = llm_client
            logger.info("Using provided LLM client")
        else:
            self.llm_client = load_chat_model(self.context.model)
            logger.info(f"Created LLM client: {self.context.model}")

        # Step 2: Initialize tools from conversation config
        self.tool_registry = await initialize_tools_from_config_async(
            assistant_config=conversation.assistant_config,
            llm_client=self.llm_client,
            rag_context=rag_context,
            tool_instances=tool_instances,
        )
        logger.info(f"Tool registry initialized with {len(self.tool_registry)} tools")

        # Step 3: Create graph with tool registry
        self.graph = create_graph(self.tool_registry)
        logger.info("Supervisor ReAct agent graph created")

    def initialize_for_conversation_sync(
        self,
        conversation: ConversationSession,
        tool_instances: Optional[Dict[str, Tool]] = None,
        rag_context: str = "",
        llm_client: Optional[BaseChatModel] = None,
    ) -> None:
        """Synchronous version of initialize_for_conversation.

        Use this if you're in a non-async context.

        Args:
            conversation: The conversation session with assistant config
            tool_instances: Dict mapping tool IDs to Tool domain objects
            rag_context: RAG context to inject into tool execution
            llm_client: Optional pre-created LLM client. If not provided, creates one from context.model

        Raises:
            ValueError: If conversation is not in assistant mode
        """
        if not conversation.assistant_config or not conversation.assistant_config.enabled:
            raise ValueError(
                f"Conversation {conversation._id} is not in assistant/supervisor mode"
            )

        logger.info(
            f"Initializing supervisor agent for conversation {conversation._id} "
            f"with tools: {conversation.assistant_config.tools}"
        )

        # Step 1: Set LLM client (provided or create new)
        if llm_client:
            self.llm_client = llm_client
            logger.info("Using provided LLM client")
        else:
            self.llm_client = load_chat_model(self.context.model)
            logger.info(f"Created LLM client: {self.context.model}")

        # Step 2: Initialize tools from conversation config
        self.tool_registry = initialize_tools_from_config(
            assistant_config=conversation.assistant_config,
            llm_client=self.llm_client,
            rag_context=rag_context,
            tool_instances=tool_instances,
        )
        logger.info(f"Tool registry initialized with {len(self.tool_registry)} tools")

        # Step 3: Create graph with tool registry
        self.graph = create_graph(self.tool_registry)
        logger.info("Supervisor ReAct agent graph created")

    async def run_conversation(
        self,
        user_message: str,
        conversation_messages: list[BaseMessage],
        max_iterations: int = 10,
    ) -> tuple[str, Dict[str, Any]]:
        """Run a single conversation turn through the supervisor agent.

        Args:
            user_message: The user's input message
            conversation_messages: Previous conversation messages (LangChain BaseMessage objects)
            max_iterations: Max iterations before timeout (default 10)

        Returns:
            Tuple of (final_response_text, execution_state_dict)

        Raises:
            RuntimeError: If graph or LLM client not initialized
            ValueError: If execution fails
        """
        if not self.graph or not self.llm_client:
            raise RuntimeError(
                "Agent not initialized - call initialize_for_conversation() first"
            )

        logger.info(f"Running conversation turn - user message: {user_message[:100]}...")

        # Prepare initial state with user message
        messages = [*conversation_messages, HumanMessage(content=user_message)]

        # Run the graph
        try:
            result = await self.graph.ainvoke(
                {"messages": messages},
                config={
                    "configurable": self.context,
                    "recursion_limit": max_iterations,
                },
            )

            # Extract final response
            final_message = result["messages"][-1]
            final_response = (
                final_message.content
                if hasattr(final_message, "content")
                else str(final_message)
            )

            logger.info(f"Conversation turn completed - response length: {len(final_response)}")

            return final_response, result

        except Exception as e:
            logger.error(f"Error during conversation execution: {e}")
            raise ValueError(f"Conversation execution failed: {e}") from e

    async def stream_conversation(
        self,
        user_message: str,
        conversation_messages: list[BaseMessage],
        max_iterations: int = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream conversation execution with event streaming.

        Yields events for:
        - supervisor_started: Supervisor agent started
        - agent_execution_step: Agent made a decision (tool selection or response)
        - tool_execution: Tool was executed
        - response_generated: Final response ready
        - workflow_complete: Entire workflow finished

        Args:
            user_message: The user's input message
            conversation_messages: Previous conversation messages
            max_iterations: Max iterations before timeout

        Yields:
            Event dicts with type, timestamp, and event-specific data
        """
        if not self.graph or not self.llm_client:
            raise RuntimeError(
                "Agent not initialized - call initialize_for_conversation() first"
            )

        logger.info(f"Streaming conversation - user message: {user_message[:100]}...")

        # Emit start event
        yield {
            "type": "supervisor_started",
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "user_message": user_message,
            "tools_available": self.tool_registry.list_ids() if self.tool_registry else [],
        }

        # Prepare initial state
        messages = [*conversation_messages, HumanMessage(content=user_message)]

        # Run graph with streaming
        try:
            async for event in self.graph.astream(
                {"messages": messages},
                config={
                    "configurable": self.context,
                    "recursion_limit": max_iterations,
                },
            ):
                # Event structure from langgraph: {node_name: state_update}
                for node_name, node_state in event.items():
                    logger.debug(f"Graph event from node '{node_name}'")

                    # Emit step event
                    yield {
                        "type": "agent_execution_step",
                        "timestamp": datetime.now(tz=UTC).isoformat(),
                        "node": node_name,
                        "state_keys": list(node_state.keys()) if isinstance(node_state, dict) else [],
                    }

                    # Check for tool calls in messages
                    if isinstance(node_state, dict) and "messages" in node_state:
                        messages_list = node_state["messages"]
                        if isinstance(messages_list, list) and len(messages_list) > 0:
                            last_msg = messages_list[-1]
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                for tool_call in last_msg.tool_calls:
                                    yield {
                                        "type": "tool_execution",
                                        "timestamp": datetime.now(tz=UTC).isoformat(),
                                        "tool_name": tool_call.get("name", "unknown"),
                                        "tool_input": tool_call.get("args", {}),
                                    }

            # Emit complete event with final response
            yield {
                "type": "workflow_complete",
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error during conversation streaming: {e}")
            yield {
                "type": "workflow_complete",
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "status": "error",
                "error": str(e),
            }

    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about registered tools.

        Returns:
            Dict with tools list and metadata
        """
        if not self.tool_registry:
            return {"tools": [], "count": 0}

        tool_ids = self.tool_registry.list_ids()
        return {
            "tools": tool_ids,
            "count": len(tool_ids),
            "has_knowledge_expert": "knowledge_expert" in tool_ids,
        }
