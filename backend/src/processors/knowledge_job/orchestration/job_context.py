"""
Job execution context.

This module defines the shared context that flows through the pipeline,
containing all state and data needed by pipeline steps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from langchain_core.documents import Document

from src.domain.knowledge.knowledge_job import KnowledgeJob
from src.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig
from src.domain.rag.knowledge_chunk import KnowledgeChunk


@dataclass
class JobContext:
    """
    Shared context for job execution through the pipeline.

    This context is passed to each pipeline step and accumulates data
    as the pipeline progresses. Steps can read from and write to this context.
    """

    # Job configuration (immutable)
    job: KnowledgeJob
    knowledge_source_config: KnowledgeSourceConfig
    user_id: str
    execution_context: Dict[str, Any] = field(default_factory=dict)

    # Pipeline execution data (mutable - populated by steps)
    documents: List[Document] = field(default_factory=list)
    chunks: List[KnowledgeChunk] = field(default_factory=list)
    vectors: List[List[float]] = field(default_factory=list)

    # Processing statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    # Timeline tracking
    timeline_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Callbacks and hooks
    status_callback: Optional[Callable[[str, Optional[Dict[str, Any]]], None]] = None
    progress_callback: Optional[Callable[[int, int], None]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default stats if not provided."""
        if not self.stats:
            self.stats = {
                "total_documents": 0,
                "total_chunks": 0,
                "total_vectors": 0,
                "processing_time_seconds": 0.0,
                "batches_processed": 0,
            }

    def update_stats(self, **kwargs) -> None:
        """
        Update processing statistics.

        Args:
            **kwargs: Key-value pairs to update in stats
        """
        self.stats.update(kwargs)

    def increment_stat(self, key: str, value: int = 1) -> None:
        """
        Increment a stat counter.

        Args:
            key: The stat key to increment
            value: Amount to increment by (default: 1)
        """
        current = self.stats.get(key, 0)
        self.stats[key] = current + value

    def add_error(self, error: str) -> None:
        """
        Add an error message to the context.

        Args:
            error: Error message to record
        """
        self.errors.append(error)

    def emit_status(self, message: str, batch_info: Dict[str, Any] = None) -> None:
        """
        Emit a status update via the callback if configured.

        Args:
            message: Status message
            batch_info: Optional batch processing information
        """
        if self.status_callback:
            self.status_callback(message, batch_info)

    def emit_progress(self, current: int, total: int) -> None:
        """
        Emit progress update via callback if configured.

        Args:
            current: Current progress count
            total: Total count
        """
        if self.progress_callback:
            self.progress_callback(current, total)

    def get_job_id(self) -> str:
        """Get the job ID."""
        return self.job.id

    def get_user_id(self) -> str:
        """Get the user ID."""
        return self.user_id

    def is_collection_clear_requested(self) -> bool:
        """Check if collection should be cleared before processing."""
        return getattr(self.job, "clear_collection_before_start", False)

    def should_check_duplicates(self) -> bool:
        """Check if duplicate checking is enabled."""
        return getattr(self.job, "check_duplicates_before_insert", False)

    def get_vectordb_collection_id(self) -> str:
        """Get the VectorDB collection ID."""
        return self.job.vectordb_collection_id

    def get_splitter_id(self) -> str:
        """Get the document splitter ID."""
        return self.job.splitter_id

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization.

        Returns:
            Dictionary representation of the context
        """
        return {
            "job_id": self.job.id,
            "user_id": self.user_id,
            "stats": self.stats,
            "errors": self.errors,
            "timeline_id": self.timeline_id,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"JobContext(job_id='{self.job.id}', "
            f"docs={len(self.documents)}, "
            f"chunks={len(self.chunks)}, "
            f"vectors={len(self.vectors)})"
        )
