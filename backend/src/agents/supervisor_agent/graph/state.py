"""Define the state structures for the supervisor agent.

Based on react-agent pattern with extensions for RAG integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated


@dataclass
class InputState:
    """Defines the input state for the agent.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    """
    Messages tracking the primary execution state of the agent.

    Typically accumulates a pattern of:
    1. HumanMessage - user input
    2. AIMessage with .tool_calls - agent picking tool(s) to use
    3. ToolMessage(s) - the responses (or errors) from executed tools
    4. AIMessage without .tool_calls - agent responding to user
    5. HumanMessage - user's next conversational turn

    Steps 2-5 may repeat as needed.

    The `add_messages` annotation ensures that new messages are merged with existing ones.
    """


@dataclass
class SupervisorReActState(InputState):
    """Represents the complete state of the supervisor agent.

    Extends InputState with additional attributes for RAG context tracking.
    """

    is_last_step: IsLastStep = field(default=False)
    """
    Indicates whether the current step is the last one before the graph raises an error.

    This is a 'managed' variable, controlled by the state machine rather than user code.
    It is set to 'True' when the step count reaches recursion_limit - 1.
    """
