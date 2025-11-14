"""
Custom ReAct Graph Builder for Supervisor Agent.

Implements the ReAct (Reasoning + Acting) pattern with:
- LLM with bound tools (RAG + task tools)
- Tool execution nodes
- Conditional routing based on tool calls
- Progress event emission for UI streaming

Based on: https://github.com/langchain-ai/react-agent
"""

from typing import Dict, List, Literal, Any, cast
import json

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from loguru import logger

from .state import SupervisorReActState


async def call_model(
    state: SupervisorReActState,
    llm: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: str,
) -> Dict[str, Any]:
    """
    Call the LLM with available tools bound.

    This is the main reasoning step where the model decides:
    1. Which tools to use
    2. What arguments to pass
    3. When to stop and return answer

    Args:
        state: Current graph state (messages + RAG context)
        llm: Language model instance
        tools: All available tools (RAG + task tools)
        system_prompt: Custom system prompt

    Returns:
        Dict with updated messages containing LLM response
    """
    logger.info(f"[ReAct] call_model: Binding {len(tools)} tools to LLM")
    logger.debug(f"[ReAct] Available tools: {[t.name for t in tools]}")

    # Bind all tools to the model
    llm_with_tools = llm.bind_tools(tools)

    # Prepare messages: system prompt + conversation history
    messages = [
        {"role": "system", "content": system_prompt},
        *state.messages
    ]

    logger.debug(f"[ReAct] Invoking LLM with {len(messages)} messages (including system)")

    # Call LLM
    response = cast(
        AIMessage,
        await llm_with_tools.ainvoke(messages)
    )

    logger.info(f"[ReAct] LLM response received")
    if response.tool_calls:
        tool_names = [call["name"] for call in response.tool_calls]
        logger.info(f"[ReAct] Tools requested: {tool_names}")

    return {"messages": [response]}


def route_tools(state: SupervisorReActState) -> Literal["rag_tool", "task_tools", END]:
    """
    Route to appropriate tool execution node based on LLM's tool calls.

    Decision logic:
    - No tool_calls → END (return answer)
    - knowledge_expert → "rag_tool" node
    - Other tools → "task_tools" node (ToolNode handles all of them)

    Args:
        state: Current graph state

    Returns:
        Next node name: "rag_tool", "task_tools", or END
    """
    last_message = state.messages[-1]

    # No tool calls = we're done
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.info("[ReAct] No tool calls in LLM response, routing to END")
        return END

    # Check which tool is being called (first tool_call)
    tool_name = last_message.tool_calls[0]["name"]
    logger.debug(f"[ReAct] Routing to tool: {tool_name}")

    if tool_name == "knowledge_expert":
        logger.info("[ReAct] Routing to rag_tool node")
        return "rag_tool"
    else:
        logger.info(f"[ReAct] Routing to task_tools node ({tool_name})")
        return "task_tools"


async def execute_rag_tool(
    state: SupervisorReActState,
    rag_tool: BaseTool,
) -> Dict[str, Any]:
    """
    Execute the RAG/knowledge_expert tool.

    Extracts documents and stores in state for task tools to access.
    Task tools can read RAG context from state["rag_context"].

    Args:
        state: Current graph state (includes messages)
        rag_tool: The RAG knowledge retrieval tool instance

    Returns:
        Dict with: messages (ToolMessage), rag_documents, rag_context, tools_used
    """
    last_message = state.messages[-1]

    # Find the knowledge_expert tool call in last message
    rag_call = None
    for call in last_message.tool_calls:
        if call["name"] == "knowledge_expert":
            rag_call = call
            break

    if not rag_call:
        logger.warning("[ReAct] RAG tool routed but no knowledge_expert call found")
        return {}

    logger.info("[ReAct] Executing RAG tool (knowledge_expert)")
    logger.debug(f"[ReAct] RAG call args: {rag_call['args']}")

    try:
        # Execute RAG tool
        result = await rag_tool.ainvoke(rag_call["args"])

        # Parse result (could be JSON string or dict)
        if isinstance(result, str):
            result = json.loads(result)

        documents = result.get("documents", [])
        logger.info(f"[ReAct] RAG tool returned {len(documents)} documents")

        # Format documents as context string for task tools
        rag_context = _format_rag_documents(documents)
        logger.debug(f"[ReAct] RAG context size: {len(rag_context)} chars")

        # Track tool usage
        tools_used = state.tools_used.copy() if state.tools_used else []
        tools_used.append("knowledge_expert")

        # Return tool message + state updates
        return {
            "messages": [
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=rag_call["id"],
                    name="knowledge_expert"
                )
            ],
            "rag_documents": {"documents": documents},
            "rag_context": rag_context,
            "rag_context_size": len(rag_context),
            "tools_used": tools_used,
        }

    except Exception as e:
        logger.error(f"[ReAct] RAG tool execution failed: {e}", exc_info=True)
        return {
            "messages": [
                ToolMessage(
                    content=f"Error retrieving knowledge: {str(e)}",
                    tool_call_id=rag_call["id"],
                    name="knowledge_expert",
                    is_error=True
                )
            ]
        }


def _format_rag_documents(documents: List[Dict[str, Any]]) -> str:
    """
    Format RAG documents into a context string.

    Used by task tools to access retrieved knowledge.

    Args:
        documents: List of document dicts from RAG

    Returns:
        Formatted context string with document content
    """
    if not documents:
        return ""

    context_parts = []
    for idx, doc in enumerate(documents, 1):
        # Support multiple content field names
        text = doc.get("content") or doc.get("text") or ""
        if text.strip():
            context_parts.append(f"## Document {idx}\n{text}\n")

    return "".join(context_parts)


def create_supervisor_graph(
    llm: BaseChatModel,
    rag_tool: BaseTool,
    task_tools: List[BaseTool],
    system_prompt: str,
) -> StateGraph:
    """
    Create the supervisor ReAct graph.

    Implements the ReAct pattern with explicit nodes:
    1. call_model: LLM reasoning with bound tools
    2. rag_tool: RAG knowledge retrieval
    3. task_tools: User-configured task execution

    Similar to langchain-ai/react-agent but with RAG + dynamic tools support.

    Args:
        llm: Language model instance (with tool calling support)
        rag_tool: RAG knowledge retrieval tool instance
        task_tools: List of user-configured task tools
        system_prompt: Custom system prompt for the agent

    Returns:
        Compiled LangGraph StateGraph ready for execution
    """
    all_tools = [rag_tool] + task_tools

    logger.info(f"[Graph] Creating supervisor ReAct graph")
    logger.info(f"[Graph] Tools: 1 RAG + {len(task_tools)} task tools = {len(all_tools)} total")
    logger.debug(f"[Graph] Tool names: {[t.name for t in all_tools]}")

    # Create graph
    builder = StateGraph(SupervisorReActState)

    # Node 1: LLM reasoning with bound tools
    async def call_model_node(state: SupervisorReActState) -> Dict[str, Any]:
        return await call_model(state, llm, all_tools, system_prompt)

    builder.add_node("call_model", call_model_node)

    # Node 2: RAG tool execution (custom node, not ToolNode)
    async def rag_node(state: SupervisorReActState) -> Dict[str, Any]:
        return await execute_rag_tool(state, rag_tool)

    builder.add_node("rag_tool", rag_node)

    # Node 3: Task tools execution (LangGraph ToolNode)
    # ToolNode automatically executes tools and returns ToolMessage results
    task_tools_node = ToolNode(task_tools)
    builder.add_node("task_tools", task_tools_node)

    # Set entry point
    builder.set_entry_point("call_model")

    # Conditional edge based on tool calls
    # Routes to: "rag_tool", "task_tools", or END
    builder.add_conditional_edges(
        "call_model",
        route_tools,
    )

    # Loop back to reasoning after tool execution
    builder.add_edge("rag_tool", "call_model")
    builder.add_edge("task_tools", "call_model")

    # Compile graph
    graph = builder.compile(name="Supervisor ReAct Agent")

    logger.info("[Graph] Supervisor ReAct graph created successfully")

    return graph
