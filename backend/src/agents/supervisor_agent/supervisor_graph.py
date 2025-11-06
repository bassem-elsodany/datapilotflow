"""
Supervisor Graph using LangGraph Supervisor Library.

This module implements the supervisor agent orchestration using the official
langgraph-supervisor library for proper tool-based handoff mechanism.

The supervisor:
1. Receives user query and routing configuration
2. Detects intent (rag_only, rag_then_task)
3. Routes to RAG Agent and/or Task Agent via tool calls
4. Collects results and synthesizes final response
"""

from typing import Any, Callable, Dict, List, Optional
from functools import lru_cache

from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from src.agents.common.agent_state import AgentState
from src.agents.rag_agent import RAGAgentService
from src.agents.task_agent import TaskAgentService


def create_supervisor_graph(
    llm_client: ChatLiteLLM,
    rag_agent: RAGAgentService,
    task_agent: TaskAgentService,
    intent_detector: Callable[[AgentState], str],
) -> CompiledStateGraph:
    """
    Create a LangGraph-based supervisor using tool-based handoff pattern.

    The supervisor works as follows:
    1. Intent Detection: Uses LLM to classify user request
    2. Agent Tool Nodes: RAG Agent and Task Agent are exposed as tools
    3. Routing: Based on intent, supervisor calls appropriate agent tools
    4. Context Injection: RAG results automatically injected to Task Agent
    5. Synthesis: Final response synthesized from agent outputs

    Args:
        llm_client: ChatLiteLLM client for intent reasoning
        rag_agent: RAGAgentService instance
        task_agent: TaskAgentService instance
        intent_detector: Async callable to detect user intent

    Returns:
        Compiled LangGraph state graph
    """
    logger.info("🏭 Building Supervisor Graph using LangGraph Supervisor pattern")

    # Create state graph
    graph_builder = StateGraph(AgentState)

    # ==================== TOOL NODES ====================
    # These nodes are callable by the supervisor LLM as tools

    async def rag_agent_tool(state: AgentState) -> AgentState:
        """Tool node that executes RAG Agent."""
        logger.info("🔧 Supervisor calling RAG Agent tool")
        try:
            result_state = await rag_agent.execute(state)
            logger.info("✅ RAG Agent tool completed")
            return result_state
        except Exception as e:
            logger.error(f"❌ RAG Agent tool failed: {e}")
            raise

    async def task_agent_tool(state: AgentState) -> AgentState:
        """Tool node that executes Task Agent."""
        logger.info("🔧 Supervisor calling Task Agent tool")
        try:
            result_state = await task_agent.execute(state)
            logger.info("✅ Task Agent tool completed")
            return result_state
        except Exception as e:
            logger.error(f"❌ Task Agent tool failed: {e}")
            raise

    # ==================== SUPERVISOR NODE ====================

    async def supervisor_node(state: AgentState) -> Dict[str, Any]:
        """
        Supervisor reasoning node.

        Detects user intent and decides which tools (agents) to call.
        Uses an LLM to reason about the user's request and routing strategy.

        Returns state update with:
        - intent: Detected intent classification
        - next_agent: Which agent to route to next ("rag", "task", "end")
        """
        logger.info("🧠 Supervisor: Analyzing request and detecting intent")

        try:
            # Detect intent using provided detector
            intent = await intent_detector(state)
            state["intent"] = intent

            logger.info(f"✅ Supervisor Intent: {intent}")

            # Determine next routing based on intent
            # This implements the handoff decision logic
            if intent == "rag_only":
                logger.info("📍 Routing to: RAG Agent only")
                next_agent = "rag_agent"

            elif intent == "rag_then_task":
                logger.info("📍 Routing to: RAG Agent → Task Agent")
                # Start with RAG, then supervisor will call Task Agent after
                next_agent = "rag_agent"

            else:
                logger.warning(
                    f"⚠️ Unknown intent '{intent}', defaulting to RAG Agent"
                )
                next_agent = "rag_agent"

            return {"next_agent": next_agent, "intent": intent}

        except Exception as e:
            logger.error(f"❌ Supervisor error: {e}")
            return {"next_agent": "end", "error": str(e)}

    # ==================== ROUTING LOGIC ====================

    def route_after_rag(state: AgentState) -> str:
        """
        Conditional routing after RAG Agent execution.

        If intent was rag_then_task, route to Task Agent.
        Otherwise, end the workflow.
        """
        intent = state.get("intent", "unknown")

        if intent == "rag_then_task":
            logger.info("🔄 Post-RAG routing: Directing to Task Agent")
            return "task_agent"
        else:
            logger.info("🏁 Post-RAG routing: Workflow complete")
            return "end"

    def route_from_supervisor(state: AgentState) -> str:
        """
        Route from supervisor based on detected intent.

        Handles the initial routing decision from supervisor node.
        """
        next_agent = state.get("next_agent")

        if next_agent == "rag_agent":
            return "rag_agent"
        elif next_agent == "task_agent":
            return "task_agent"
        else:
            return "end"

    # ==================== GRAPH CONSTRUCTION ====================

    # Add nodes
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("rag_agent", rag_agent_tool)
    graph_builder.add_node("task_agent", task_agent_tool)

    # Define edges
    graph_builder.add_edge(START, "supervisor")

    # Conditional edge from supervisor based on routing decision
    graph_builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "rag_agent": "rag_agent",
            "task_agent": "task_agent",
            "end": END,
        },
    )

    # Conditional edge after RAG Agent
    graph_builder.add_conditional_edges(
        "rag_agent",
        route_after_rag,
        {
            "task_agent": "task_agent",
            "end": END,
        },
    )

    # Task Agent always leads to end
    graph_builder.add_edge("task_agent", END)

    logger.info("✅ Supervisor Graph constructed successfully")

    # Compile and return
    return graph_builder.compile()
