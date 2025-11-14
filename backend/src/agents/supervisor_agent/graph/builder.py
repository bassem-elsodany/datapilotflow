"""Define a custom Reasoning and Action agent with RAG + task tools.

Based on: https://github.com/langchain-ai/react-agent
Extended with: RAG tool + dynamic task tools + custom system prompt
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from .state import SupervisorReActState


async def call_model(
    state: SupervisorReActState,
    llm: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: str,
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our agent.

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state: The current state of the conversation.
        llm: The language model to use.
        tools: All available tools (RAG + task tools).
        system_prompt: Custom system prompt.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    # Initialize the model with tool binding
    model = llm.bind_tools(tools)

    # Format the system prompt
    system_message = system_prompt.format(
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


def route_model_output(state: SupervisorReActState) -> Literal["__end__", "tools"]:
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


def create_supervisor_graph(
    llm: BaseChatModel,
    rag_tool: BaseTool,
    task_tools: List[BaseTool],
    system_prompt: str,
) -> StateGraph:
    """Create a supervisor ReAct agent graph.

    Based on react-agent pattern with RAG tool + dynamic task tools.

    Args:
        llm: Language model instance.
        rag_tool: RAG knowledge retrieval tool.
        task_tools: List of user-configured task tools.
        system_prompt: Custom system prompt.

    Returns:
        Compiled LangGraph StateGraph.
    """
    all_tools = [rag_tool] + task_tools

    # Define a new graph
    builder = StateGraph(SupervisorReActState)

    # Define the nodes we will cycle between
    async def call_model_node(state: SupervisorReActState) -> Dict[str, List[AIMessage]]:
        return await call_model(state, llm, all_tools, system_prompt)

    builder.add_node(call_model_node)
    builder.add_node("tools", ToolNode(all_tools))

    # Set the entrypoint as `call_model`
    builder.add_edge("__start__", "call_model")

    # Add a conditional edge to determine the next step after `call_model`
    builder.add_conditional_edges(
        "call_model",
        route_model_output,
    )

    # Add a normal edge from `tools` to `call_model`
    builder.add_edge("tools", "call_model")

    # Compile the builder into an executable graph
    graph = builder.compile(name="Supervisor ReAct Agent")

    return graph
