"""Define a custom Reasoning and Action agent with tool registry.

Works with a chat model with tool calling support.
Based on langchain-ai/react-agent with RAG + task tools integration.
Uses tool registry for ID-based tool management (no semantic search).
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.agents.supervisor_agent.context import Context
from src.agents.supervisor_agent.state import InputState, State
from src.agents.supervisor_agent.tools import ToolRegistry
from src.agents.supervisor_agent.utils import load_chat_model


async def call_model(
    state: State,
    context: Context,
    tool_registry: ToolRegistry,
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state: The current state of the conversation.
        context: Configuration context with model and system prompt.
        tool_registry: Registry of available tools.

    Returns:
        Dictionary containing the model's response message.
    """
    # Get all tools from registry
    all_tools = tool_registry.get_all()

    # Initialize the model with tool binding
    model = load_chat_model(context.model).bind_tools(all_tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = context.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state: The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


def create_graph(tool_registry: ToolRegistry) -> StateGraph:
    """Create a supervisor ReAct agent graph with tool registry.

    Args:
        tool_registry: Registry of available tools (RAG + task tools).

    Returns:
        StateGraph: Compiled LangGraph StateGraph.
    """
    # Define a new graph (without context_schema to avoid serialization issues)
    builder = StateGraph(State, input_schema=InputState)

    # Define the two nodes we will cycle between
    async def call_model_node(state: State) -> Dict[str, List[AIMessage]]:
        # Create context with model_str from state (set by generate_response_supervisor)
        context = Context(model=state.model_str)
        return await call_model(state, context, tool_registry)

    builder.add_node("call_model", call_model_node)

    # ToolNode uses tools from registry
    all_tools = tool_registry.get_all()
    builder.add_node("tools", ToolNode(all_tools))

    # Set the entrypoint as `call_model`
    # This means that this node is the first one called
    builder.add_edge("__start__", "call_model")

    # Add a conditional edge to determine the next step after `call_model`
    builder.add_conditional_edges(
        "call_model",
        route_model_output,
    )

    # Add a normal edge from `tools` to `call_model`
    # This creates a cycle: after using tools, we always return to the model
    builder.add_edge("tools", "call_model")

    # Compile the builder into an executable graph
    graph = builder.compile(name="Supervisor ReAct Agent")

    return graph


# Create graph - will be initialized with actual tools at runtime
graph = None
