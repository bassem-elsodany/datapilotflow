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
from pydantic import BaseModel, Field


class SupervisorAgentState(BaseModel):
    """
    Enhanced agent state using LangGraph patterns.

    Provides:
    - Message handling and validation
    - List reducers with 'add' operator for Annotated fields
    - Proper state composition
    - Type safety via Pydantic

    Fields:
    - messages: List of message dicts with role and content
    - rag_documents: Raw documents retrieved from RAG
    - rag_context: Formatted context string (22k+ chars)
    - rag_context_size: Size of RAG context in characters
    - tools_used: List of all tools called during execution
    - task_tools_executed: List of task tools specifically executed
    - error_messages: List of errors encountered
    - execution_metadata: Additional execution tracking data

    NEW - Iterative RAG Evaluation:
    - rag_iteration_count: Current iteration number (1-3)
    - rag_iterations_history: History of all iterations with gap analysis
    - rag_descoped_documents: Documents filtered out as weak/irrelevant
    - coverage_verification_results: Results of each coverage check
    """

    # Message handling
    messages: List[Dict[str, Any]] = Field(default_factory=list)

    # RAG context fields
    rag_documents: Optional[List[Dict[str, Any]]] = None
    rag_context: str = ""
    rag_context_size: int = 0

    # Tool tracking - use Annotated with 'add' operator for list reduction
    tools_used: Annotated[List[str], add] = Field(default_factory=list)
    task_tools_executed: Annotated[List[str], add] = Field(default_factory=list)
    error_messages: Annotated[List[str], add] = Field(default_factory=list)

    # NEW - Iterative RAG Evaluation Fields
    rag_iteration_count: int = 0  # Track current iteration (0=not started, 1-3=iterations)
    rag_iterations_history: List[Dict[str, Any]] = Field(default_factory=list)  # History of each iteration
    rag_descoped_documents: List[Dict[str, Any]] = Field(default_factory=list)  # Documents filtered out as weak
    coverage_verification_results: List[Dict[str, Any]] = Field(default_factory=list)  # Coverage check results

    # Execution metadata
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config for compatibility"""
        arbitrary_types_allowed = True

    def __init__(self, **data):
        """
        Initialize agent state.

        Args:
            **data: State field values
        """
        super().__init__(**data)

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access for compatibility"""
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dict-like assignment for compatibility"""
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for dict-like compatibility"""
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get() for compatibility"""
        return getattr(self, key, default)

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
        ACCUMULATE RAG documents and formatted context (for multiple knowledge_expert calls).
        
        This supports the iterative enrichment workflow where the agent:
        1. Calls knowledge_expert (gets initial docs)
        2. Generates with task tool (might be incomplete)
        3. Calls knowledge_expert AGAIN with new variants (gets more docs)
        4. Generates again with ALL accumulated docs
        
        Documents are deduplicated by ID/chunk_id to avoid duplicates.

        Args:
            documents: List of RAG documents to ADD
            context_str: Formatted context string to APPEND
        """
        # Initialize if None
        if self.rag_documents is None:
            self.rag_documents = []
        
        # Deduplicate: only add documents that aren't already in the list
        existing_ids = {
            doc.get("id") or doc.get("chunk_id") or doc.get("source_url")
            for doc in self.rag_documents
        }
        
        new_docs_added = 0
        for doc in documents:
            doc_id = doc.get("id") or doc.get("chunk_id") or doc.get("source_url")
            if doc_id not in existing_ids:
                self.rag_documents.append(doc)
                existing_ids.add(doc_id)
                new_docs_added += 1
        
        # Append context (with separator if not first call)
        if self.rag_context:
            self.rag_context += f"\n\n{'='*80}\n[ADDITIONAL KNOWLEDGE FROM ENRICHMENT]\n{'='*80}\n\n"
        self.rag_context += context_str
        self.rag_context_size = len(self.rag_context)
        
        from loguru import logger
        logger.info(
            f"[RAG ACCUMULATION] Added {new_docs_added} new documents (total: {len(self.rag_documents)}), "
            f"context size: {self.rag_context_size} chars"
        )

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

    def start_rag_iteration(self) -> None:
        """
        Start a new RAG iteration cycle.
        Increments iteration counter (max 3).
        """
        if self.rag_iteration_count < 3:
            self.rag_iteration_count += 1

        from loguru import logger
        logger.info(f"[RAG ITERATION] Starting iteration {self.rag_iteration_count}/3")

    def is_max_iterations_reached(self) -> bool:
        """Check if max iterations (3) has been reached"""
        return self.rag_iteration_count >= 3

    def record_coverage_verification(
        self,
        iteration: int,
        requirements: List[str],
        coverage_status: Dict[str, str],  # {"requirement": "covered|gap|partial"}
        gaps_found: List[str],
        action: str,  # "proceed", "iterate", "max_reached"
    ) -> None:
        """
        Record the result of a coverage verification check.

        Args:
            iteration: Current iteration number
            requirements: List of requirements to verify
            coverage_status: Dict mapping requirement to coverage status
            gaps_found: List of gaps identified
            action: Action to take (proceed, iterate, max_reached)
        """
        verification_result = {
            "iteration": iteration,
            "requirements": requirements,
            "coverage_status": coverage_status,
            "gaps_found": gaps_found,
            "action": action,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        }
        self.coverage_verification_results.append(verification_result)

        from loguru import logger
        logger.info(
            f"[COVERAGE VERIFICATION] Iteration {iteration}: "
            f"Coverage={coverage_status}, Gaps={gaps_found}, Action={action}"
        )

    def record_iteration_knowledge(
        self,
        iteration: int,
        retrieved_docs: List[Dict[str, Any]],
        quality_scores: Dict[str, str],  # {"doc_id": "high|medium|low"}
        targeted_variants: List[str],
    ) -> None:
        """
        Record knowledge retrieved in this iteration with quality assessment.

        Args:
            iteration: Iteration number
            retrieved_docs: Documents retrieved in this iteration
            quality_scores: Quality scores for each document
            targeted_variants: Query variants used in this iteration
        """
        iteration_record = {
            "iteration": iteration,
            "doc_count": len(retrieved_docs),
            "quality_scores": quality_scores,
            "targeted_variants": targeted_variants,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        }
        self.rag_iterations_history.append(iteration_record)

        from loguru import logger
        logger.info(
            f"[RAG ITERATION {iteration}] Retrieved {len(retrieved_docs)} docs, "
            f"Quality distribution: {quality_scores}"
        )

    def descope_weak_documents(self, weak_doc_ids: List[str]) -> int:
        """
        Mark documents as weak/irrelevant and remove from main context.
        Stores them in rag_descoped_documents for reference.

        Args:
            weak_doc_ids: List of document IDs to descope

        Returns:
            Count of documents actually descoped
        """
        if not self.rag_documents:
            return 0

        descoped_count = 0
        remaining_docs = []

        for doc in self.rag_documents:
            doc_id = doc.get("id") or doc.get("chunk_id")
            if doc_id in weak_doc_ids:
                self.rag_descoped_documents.append(doc)
                descoped_count += 1
            else:
                remaining_docs.append(doc)

        self.rag_documents = remaining_docs

        from loguru import logger
        logger.info(
            f"[DESCOPING] Removed {descoped_count} weak documents. "
            f"Active docs: {len(self.rag_documents)}, Descoped: {len(self.rag_descoped_documents)}"
        )

        return descoped_count

    def get_iteration_summary(self) -> Dict[str, Any]:
        """
        Get summary of RAG iterations and coverage.

        Returns:
            Dictionary with iteration summary
        """
        return {
            "current_iteration": self.rag_iteration_count,
            "max_iterations": 3,
            "is_max_reached": self.is_max_iterations_reached(),
            "iterations_history": self.rag_iterations_history,
            "coverage_verifications": self.coverage_verification_results,
            "active_documents": len(self.rag_documents) if self.rag_documents else 0,
            "descoped_documents": len(self.rag_descoped_documents),
        }

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution state.

        Returns:
            Dictionary with execution summary
        """
        summary = {
            "messages_count": len(self.messages),
            "tools_used": self.tools_used,
            "task_tools_executed": self.task_tools_executed,
            "error_count": len(self.error_messages),
            "rag_context_size": self.rag_context_size,
            "rag_documents_count": len(self.rag_documents) if self.rag_documents else 0,
            "execution_metadata": self.execution_metadata,
        }

        # Include iteration summary if iterations were used
        if self.rag_iteration_count > 0:
            summary["rag_iterations"] = self.get_iteration_summary()

        return summary


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
    return SupervisorAgentState(
        messages=[{"role": "user", "content": query}],
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
