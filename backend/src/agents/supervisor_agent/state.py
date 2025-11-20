"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, Optional, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep


@dataclass
class InputState:
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    """
    Messages tracking the primary execution state of the agent.

    Typically accumulates a pattern of:
    1. HumanMessage - user input
    2. AIMessage with .tool_calls - agent picking tool(s) to use to collect information
    3. ToolMessage(s) - the responses (or errors) from the executed tools
    4. AIMessage without .tool_calls - agent responding in unstructured format to the user
    5. HumanMessage - user responds with the next conversational turn

    Steps 2-5 may repeat as needed.

    The `add_messages` annotation ensures that new messages are merged with existing ones,
    updating by ID to maintain an "append-only" state unless a message with the same ID is provided.
    """

    model_str: str = field(default="anthropic/claude-sonnet-4-5-20250929")
    """
    The LLM model string in provider/model format (e.g., "anthropic/claude-sonnet-4-5-20250929").
    This is passed through from the service layer to the graph nodes.
    """


@dataclass
class State(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    Includes RAG context, tool tracking, and iterative RAG evaluation fields.
    """

    is_last_step: IsLastStep = field(default=False)
    """
    Indicates whether the current step is the last one before the graph raises an error.

    This is a 'managed' variable, controlled by the state machine rather than user code.
    It is set to 'True' when the step count reaches recursion_limit - 1.
    """

    # RAG context fields
    rag_documents: Optional[List[Dict[str, Any]]] = field(default=None)
    """Raw documents retrieved from RAG."""

    rag_context: str = field(default="")
    """Formatted context string from RAG documents (22k+ chars)."""

    rag_context_size: int = field(default=0)
    """Size of RAG context in characters."""

    # Tool tracking - DON'T use 'add' with dataclass, it concatenates not replaces
    # Instead, manage these lists manually in graph nodes
    tools_used: List[str] = field(default_factory=list)
    """List of all tools called during execution."""

    task_tools_executed: List[str] = field(default_factory=list)
    """List of task tools specifically executed."""

    error_messages: List[str] = field(default_factory=list)
    """List of errors encountered."""

    # Iterative RAG Evaluation Fields
    rag_iteration_count: int = field(default=0)
    """Track current iteration number (1-3)."""

    rag_iterations_history: List[Dict[str, Any]] = field(default_factory=list)
    """History of each iteration with gap analysis."""

    rag_descoped_documents: List[Dict[str, Any]] = field(default_factory=list)
    """Documents filtered out as weak/irrelevant."""

    coverage_verification_results: List[Dict[str, Any]] = field(default_factory=list)
    """Results of each coverage check."""

    # Execution metadata
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional execution tracking data."""
