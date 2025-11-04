"""Task Agent specific state management."""

from typing import Any, Dict, List, Optional, TypedDict


class TaskAgentState(TypedDict):
    """
    State specific to the Task Agent workflow.
    Handles any task execution: code generation, planning, analysis, etc.
    """

    # Input
    user_request: str
    conversation_history: Optional[List[Dict[str, str]]]

    # RAG context (optional, injected from supervisor if available)
    rag_knowledge: Optional[str]

    # Task execution
    task_result: Optional[str]
    task_details: Optional[Dict[str, Any]]
    execution_steps: Optional[List[str]]

    # Metadata
    task_type: Optional[str]  # e.g., "code_generation", "planning", "analysis"
    processing_steps: List[str]
    errors: List[str]

    # Configuration
    config: Optional[Dict[str, Any]]


def create_initial_state(
    user_request: str,
    rag_knowledge: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> TaskAgentState:
    """
    Create initial state for Task Agent workflow.

    Args:
        user_request: User's task request
        rag_knowledge: Optional RAG knowledge injection
        config: Optional configuration dictionary

    Returns:
        Initial TaskAgentState
    """
    return TaskAgentState(
        user_request=user_request,
        conversation_history=None,
        rag_knowledge=rag_knowledge,
        task_result=None,
        task_details=None,
        execution_steps=None,
        task_type=None,
        processing_steps=[],
        errors=[],
        config=config or {},
    )
