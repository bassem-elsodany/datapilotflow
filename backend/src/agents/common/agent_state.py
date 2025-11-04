"""Unified state structure for the multi-agent system."""

from typing import Any, List, Optional, Dict
from dataclasses import dataclass, field
from langgraph.graph import MessagesState


@dataclass
class RAGContext:
    """Context containing RAG results that can be shared with other agents."""

    query: str
    original_documents: List[Dict[str, Any]]
    judged_documents: List[Dict[str, Any]]
    retrieved_count: int
    relevant_count: int
    relevance_threshold: float
    relevance_scores: List[float]
    execution_time_ms: float


@dataclass
class AgentState(MessagesState):
    """
    Unified state passed between supervisor and agents.

    Contains:
    - messages: Conversation history (MessagesState requirement)
    - rag_context: Results from RAG Agent (populated if RAG was executed)
    - task_result: Results from Task Agent (populated if Task was executed)
    - current_agent: Which agent is currently processing
    - user_id: User identifier
    - conversation_id: Conversation identifier
    - intent: Detected user intent for routing
    """

    messages: List[Dict[str, Any]] = field(default_factory=list)

    # Context from RAG Agent execution
    rag_context: Optional[RAGContext] = None

    # Context from Task Agent execution
    task_result: Optional[str] = None
    task_details: Optional[Dict[str, Any]] = None

    # Metadata
    current_agent: Optional[str] = None
    user_id: str = ""
    conversation_id: str = ""
    intent: str = "unknown"

    # Tracking
    execution_log: List[str] = field(default_factory=list)
