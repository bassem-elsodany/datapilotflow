"""
LangGraph-compatible agent state management.

Migrates from plain TypedDict to LangGraph patterns for better:
- State management with reducers
- Message handling with MessagesState
- State extension and composition
- Type safety
"""

from typing import Annotated, List, Dict, Any, Optional
from operator import add
from langgraph.graph import MessagesState
from pydantic import BaseModel


class SupervisorAgentState(MessagesState):
    """
    Enhanced agent state using LangGraph MessagesState.

    Extends MessagesState for:
    - Built-in message handling and validation
    - Message list reducers with 'add' operator
    - Proper state composition
    - Type safety via Pydantic integration

    Fields:
    - messages: Inherited from MessagesState (list of messages)
    - rag_documents: Raw documents retrieved from RAG
    - rag_context: Formatted context string (22k+ chars)
    - rag_context_size: Size of RAG context in characters
    - tools_used: List of all tools called during execution
    - task_tools_executed: List of task tools specifically executed
    - error_messages: List of errors encountered
    - execution_metadata: Additional execution tracking data
    """

    # RAG context fields
    rag_documents: Optional[List[Dict[str, Any]]] = None
    rag_context: str = ""
    rag_context_size: int = 0

    # Tool tracking - use Annotated with 'add' operator for list reduction
    tools_used: Annotated[List[str], add] = []
    task_tools_executed: Annotated[List[str], add] = []
    error_messages: Annotated[List[str], add] = []

    # Execution metadata
    execution_metadata: Dict[str, Any] = {}

    def __init__(self, **data):
        """
        Initialize agent state.

        Args:
            **data: State field values
        """
        super().__init__(**data)

    def add_tool_used(self, tool_name: str) -> None:
        """
        Record a tool being used.

        Args:
            tool_name: Name of tool
        """
        if tool_name not in self.tools_used:
            self.tools_used = self.tools_used + [tool_name]

    def add_task_tool_executed(self, tool_name: str) -> None:
        """
        Record a task tool execution.

        Args:
            tool_name: Name of task tool
        """
        if tool_name not in self.task_tools_executed:
            self.task_tools_executed = self.task_tools_executed + [tool_name]

    def add_error(self, error_msg: str) -> None:
        """
        Record an error.

        Args:
            error_msg: Error message
        """
        self.error_messages = self.error_messages + [error_msg]

    def set_rag_context(
        self,
        documents: List[Dict[str, Any]],
        context_str: str
    ) -> None:
        """
        Set RAG documents and formatted context.

        Args:
            documents: List of RAG documents
            context_str: Formatted context string
        """
        self.rag_documents = documents
        self.rag_context = context_str
        self.rag_context_size = len(context_str)

    def get_rag_context(self) -> str:
        """
        Get formatted RAG context.

        Returns:
            Formatted context string
        """
        return self.rag_context

    def has_rag_context(self) -> bool:
        """
        Check if RAG context is available.

        Returns:
            True if context is set
        """
        return len(self.rag_context) > 0

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution state.

        Returns:
            Dictionary with execution summary
        """
        return {
            "messages_count": len(self.messages),
            "tools_used": self.tools_used,
            "task_tools_executed": self.task_tools_executed,
            "error_count": len(self.error_messages),
            "rag_context_size": self.rag_context_size,
            "rag_documents_count": len(self.rag_documents) if self.rag_documents else 0,
            "execution_metadata": self.execution_metadata,
        }


class RAGContextPayload(BaseModel):
    """Payload for RAG context operations"""
    documents: List[Dict[str, Any]]
    context_string: str
    document_count: int
    context_size_chars: int


class ToolExecutionPayload(BaseModel):
    """Payload for tool execution tracking"""
    tool_name: str
    is_task_tool: bool
    execution_time_ms: float
    status: str  # "started", "completed", "failed"
    error_message: Optional[str] = None


class StateReducers:
    """
    Reducer functions for LangGraph state updates.

    Reducers handle how state fields are updated when
    using LangGraph's state update operators.
    """

    @staticmethod
    def add_to_list(current: List[str], new_items: List[str]) -> List[str]:
        """Add items to list without duplicates"""
        result = list(current) if current else []
        for item in new_items:
            if item not in result:
                result.append(item)
        return result

    @staticmethod
    def merge_metadata(
        current: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge metadata dictionaries"""
        result = dict(current) if current else {}
        result.update(updates)
        return result


# Type aliases for convenience
AgentStateDict = Dict[str, Any]


def create_initial_state(query: str) -> SupervisorAgentState:
    """
    Create initial agent state for a new query.

    Args:
        query: User's query string

    Returns:
        Initialized SupervisorAgentState
    """
    from langchain_core.messages import HumanMessage

    return SupervisorAgentState(
        messages=[HumanMessage(content=query)],
        rag_documents=None,
        rag_context="",
        rag_context_size=0,
        tools_used=[],
        task_tools_executed=[],
        error_messages=[],
        execution_metadata={},
    )


def extract_execution_metrics(state: SupervisorAgentState) -> Dict[str, Any]:
    """
    Extract execution metrics from state.

    Args:
        state: SupervisorAgentState instance

    Returns:
        Dictionary of metrics
    """
    return {
        "total_messages": len(state.messages),
        "tools_used_count": len(state.tools_used),
        "tools_used": state.tools_used,
        "task_tools_executed_count": len(state.task_tools_executed),
        "task_tools_executed": state.task_tools_executed,
        "error_count": len(state.error_messages),
        "rag_documents_retrieved": len(state.rag_documents) if state.rag_documents else 0,
        "rag_context_size_bytes": state.rag_context_size,
        "has_rag_context": state.has_rag_context(),
    }
