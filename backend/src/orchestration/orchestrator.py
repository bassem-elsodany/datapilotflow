"""Multi-agent orchestrator factory using LangGraph Supervisor pattern.

This module implements the standard langgraph-supervisor pattern from:
https://github.com/langchain-ai/langgraph-supervisor-py

Example usage (standard pattern):
```python
# Create agents (compiled graphs)
rag_agent = rag_agent_service.rag_graph
task_agent = task_agent_service.task_graph

# Create supervisor
supervisor_workflow = create_supervisor(
    [rag_agent, task_agent],
    model=llm_client,
    prompt="You are a supervisor managing multiple agents..."
)

# Execute
result = await supervisor_workflow.ainvoke(initial_state)
```
"""

import logging
from typing import Any, Dict, Optional

from langchain_community.chat_models import ChatLiteLLM
from langgraph_supervisor import create_supervisor

from ..agents.rag_agent import RAGAgentService
from ..agents.task_agent import TaskAgentService
from ..agents.common import AgentState

logger = logging.getLogger(__name__)


def create_multi_agent_orchestrator(
    llm_client: ChatLiteLLM,
    rag_graph: Any,
    conversation_service: Optional[Any] = None,
) -> Any:
    """
    Create a supervisor orchestrator following the official LangGraph Supervisor pattern.

    Wraps the langgraph_supervisor.create_supervisor() function to create a
    compiled StateGraph that orchestrates RAG and Task agents.

    Args:
        llm_client: LangChain LLM client for supervisor LLM reasoning
        rag_graph: Compiled LangGraph for RAG pipeline
        conversation_service: Optional conversation service

    Returns:
        Compiled StateGraph - the supervisor workflow graph
        Usage: result = await supervisor_graph.ainvoke(initial_state)
    """
    logger.info("🏭 Creating supervisor orchestrator...")

    # Create individual agent services
    logger.info("📦 Initializing RAG Agent...")
    rag_agent = RAGAgentService(
        llm_client=llm_client,
        rag_graph=rag_graph,
        conversation_service=conversation_service,
    )

    logger.info("📦 Initializing Task Agent...")
    task_agent = TaskAgentService(llm_client=llm_client)

    # Extract compiled agent graphs (Pregel objects)
    # These are the compiled LangGraphs from each agent
    agents = [rag_agent.rag_graph, task_agent.task_graph]

    logger.info("📦 Creating supervisor with tool-based handoff...")

    # System prompt for supervisor LLM
    supervisor_prompt = """You are an intelligent supervisor orchestrating multiple specialist agents.

Available agents:
1. **RAG Agent** - Document retrieval and ranking from knowledge base
   - Use when user needs information from documents
   - Gather knowledge before task execution

2. **Task Agent** - Task execution, analysis, and code generation
   - Use for tasks requiring action or reasoning
   - Has access to RAG context if documents were retrieved

Your routing strategy:
- For document questions: Use RAG Agent
- For tasks needing knowledge: Use RAG Agent first, then Task Agent
- For pure tasks: Use Task Agent directly
- Always provide agents with full context

Be decisive about routing."""

    # Create supervisor using official langgraph-supervisor pattern
    supervisor_graph = create_supervisor(
        agents=agents,
        model=llm_client,
        prompt=supervisor_prompt,
        output_mode="last_message",
        add_handoff_messages=True,
        handoff_tool_prefix="delegate_to_",
    )

    logger.info("✅ Supervisor orchestrator created successfully")
    logger.info("   - Pattern: LangGraph Supervisor (tool-based handoff)")
    logger.info("   - Agents: RAG Agent, Task Agent")
    logger.info("   - Routing: LLM-driven")

    return supervisor_graph
