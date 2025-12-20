"""
Base abstractions for the job processing pipeline.

This module defines the core interfaces and data structures for the pipeline pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class StepStatus(str, Enum):
    """Status of a pipeline step execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """Result of a pipeline step execution."""

    success: bool
    status: StepStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0

    @classmethod
    def success_result(
        cls, data: Dict[str, Any] = None, metadata: Dict[str, Any] = None
    ) -> "StepResult":
        """Create a successful result."""
        return cls(
            success=True,
            status=StepStatus.COMPLETED,
            data=data or {},
            metadata=metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        error: str,
        error_traceback: str = None,
        metadata: Dict[str, Any] = None,
    ) -> "StepResult":
        """Create a failed result."""
        return cls(
            success=False,
            status=StepStatus.FAILED,
            error=error,
            error_traceback=error_traceback,
            metadata=metadata or {},
        )

    @classmethod
    def cancelled_result(cls, reason: str = None) -> "StepResult":
        """Create a cancelled result."""
        return cls(
            success=False,
            status=StepStatus.CANCELLED,
            error=reason or "Step cancelled",
        )


@dataclass
class PipelineResult:
    """Result of entire pipeline execution."""

    success: bool
    step_results: List[StepResult] = field(default_factory=list)
    total_execution_time_seconds: float = 0.0
    completed_steps: int = 0
    failed_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """Get result for a specific step by name."""
        for result in self.step_results:
            if result.metadata.get("step_name") == step_name:
                return result
        return None

    def get_aggregated_data(self) -> Dict[str, Any]:
        """Aggregate data from all successful steps."""
        aggregated = {}
        for result in self.step_results:
            if result.success:
                aggregated.update(result.data)
        return aggregated


class PipelineStep(ABC):
    """
    Abstract base class for pipeline steps.

    Each step represents a discrete unit of work in the job processing pipeline.
    Steps are executed sequentially and can share data through the JobContext.
    """

    def __init__(self, name: str = None):
        """
        Initialize the pipeline step.

        Args:
            name: Optional name for the step (defaults to class name)
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def execute(self, context: "JobContext") -> StepResult:
        """
        Execute the pipeline step.

        Args:
            context: The job execution context containing shared state

        Returns:
            StepResult indicating success or failure with relevant data

        Raises:
            Exception: Any unhandled exceptions should be caught by the pipeline executor
        """
        pass

    async def rollback(self, context: "JobContext") -> None:
        """
        Rollback changes made by this step (optional).

        Override this method to implement compensation logic when the pipeline fails.

        Args:
            context: The job execution context
        """
        pass

    async def validate(self, context: "JobContext") -> bool:
        """
        Validate preconditions before executing this step (optional).

        Args:
            context: The job execution context

        Returns:
            True if preconditions are met, False otherwise
        """
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
