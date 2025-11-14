"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
Based on langchain-ai/react-agent with RAG + task tools integration.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime

from src.agents.supervisor_agent.context import Context
from src.agents.supervisor_agent.state import InputState, State
from src.agents.supervisor_agent.utils import load_chat_model


async def call_model(
    state: State, runtime: Runtime[Context], tools: List[BaseTool]
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        runtime (Runtime[Context]): Configuration for the model run.
        tools (List[BaseTool]): Available tools (RAG + task tools).

    Returns:
        dict: A dictionary containing the model's response message.
    """
    # Initialize the model with tool binding
    model = load_chat_model(runtime.context.model).bind_tools(tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.system_prompt.format(
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
        state (State): The current state of the conversation.

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


def create_graph(tools: List[BaseTool]) -> StateGraph:
    """Create a supervisor ReAct agent graph.

    Args:
        tools (List[BaseTool]): Available tools (RAG + task tools).

    Returns:
        StateGraph: Compiled LangGraph StateGraph.
    """
    # Define a new graph
    builder = StateGraph(State, input_schema=InputState, context_schema=Context)

    # Define the two nodes we will cycle between
    async def call_model_node(state: State, runtime: Runtime[Context]) -> Dict[str, List[AIMessage]]:
        return await call_model(state, runtime, tools)

    builder.add_node(call_model_node)
    builder.add_node("tools", ToolNode(tools))

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
