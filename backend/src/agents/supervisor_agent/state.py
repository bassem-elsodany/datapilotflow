"""Supervisor Agent specific state management."""

from typing import Any, Dict, List, Optional, TypedDict


class SupervisorAgentState(TypedDict):
    """
    State specific to the Supervisor Agent workflow.
    Handles routing and orchestration between RAG and Task agents.
    """

    # Input
    user_input: str
    conversation_history: Optional[List[Dict[str, str]]]

    # Intent classification
    detected_intent: Optional[str]  # "rag_only" or "rag_then_task"
    intent_confidence: Optional[float]

    # Agent execution tracking
    rag_agent_result: Optional[Dict[str, Any]]
    task_agent_result: Optional[Dict[str, Any]]

    # Final result
    final_response: Optional[str]

    # Metadata
    routing_decision: Optional[str]
    execution_path: List[str]  # Track which agents were executed
    processing_steps: List[str]
    errors: List[str]

    # Configuration
    config: Optional[Dict[str, Any]]
