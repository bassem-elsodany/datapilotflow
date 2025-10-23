"""
Cancellation Manager.

This module provides centralized management of job cancellation signals,
replacing the scattered signal handlers and global state in the old architecture.
"""

import signal
from threading import Lock
from typing import Optional, Set

from loguru import logger


class CancellationManager:
    """
    Manages job cancellation requests and signals.

    This class provides a thread-safe way to handle job cancellation,
    supporting both explicit cancellation requests and system signals (SIGINT/SIGTERM).
    """

    def __init__(self, handle_signals: bool = True):
        """
        Initialize the cancellation manager.

        Args:
            handle_signals: Whether to set up signal handlers for SIGINT/SIGTERM
        """
        self._cancelled_jobs: Set[str] = set()
        self._lock = Lock()
        self._signal_received = False

        if handle_signals:
            self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.warning(
                f"Received signal {signal_name} ({signum}), requesting cancellation of all jobs"
            )
            self._signal_received = True

        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            logger.debug("Signal handlers registered for graceful cancellation")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    def request_cancellation(self, job_id: str, reason: str = None) -> None:
        """
        Request cancellation of a specific job.

        Args:
            job_id: The job ID to cancel
            reason: Optional reason for cancellation
        """
        with self._lock:
            self._cancelled_jobs.add(job_id)
            logger.info(
                f"Cancellation requested for job {job_id}"
                + (f": {reason}" if reason else "")
            )

    def clear_cancellation(self, job_id: str) -> None:
        """
        Clear cancellation request for a job.

        Args:
            job_id: The job ID to clear
        """
        with self._lock:
            self._cancelled_jobs.discard(job_id)
            logger.debug(f"Cancellation cleared for job {job_id}")

    def is_cancelled(self, job_id: str) -> bool:
        """
        Check if a job has been cancelled.

        Args:
            job_id: The job ID to check

        Returns:
            True if the job is cancelled, False otherwise
        """
        with self._lock:
            # Job is cancelled if explicitly requested OR if global signal received
            return job_id in self._cancelled_jobs or self._signal_received

    def check_and_raise(self, job_id: str) -> None:
        """
        Check if job is cancelled and raise exception if so.

        Args:
            job_id: The job ID to check

        Raises:
            JobCancelledException: If the job has been cancelled
        """
        if self.is_cancelled(job_id):
            raise JobCancelledException(job_id)

    def get_cancelled_jobs(self) -> Set[str]:
        """
        Get set of all cancelled job IDs.

        Returns:
            Set of cancelled job IDs
        """
        with self._lock:
            return self._cancelled_jobs.copy()

    def cancel_all(self, reason: str = None) -> None:
        """
        Cancel all jobs (typically used during shutdown).

        Args:
            reason: Optional reason for cancellation
        """
        with self._lock:
            self._signal_received = True
            logger.warning(
                f"Cancelling ALL jobs" + (f": {reason}" if reason else "")
            )

    def reset(self) -> None:
        """Reset the cancellation manager (primarily for testing)."""
        with self._lock:
            self._cancelled_jobs.clear()
            self._signal_received = False
            logger.debug("Cancellation manager reset")


class JobCancelledException(Exception):
    """Exception raised when a job is cancelled."""

    def __init__(self, job_id: str, message: str = None):
        """
        Initialize the exception.

        Args:
            job_id: The ID of the cancelled job
            message: Optional custom message
        """
        self.job_id = job_id
        self.message = message or f"Job {job_id} was cancelled"
        super().__init__(self.message)


# Global instance for backward compatibility (can be replaced with DI)
_global_cancellation_manager: Optional[CancellationManager] = None


def get_cancellation_manager() -> CancellationManager:
    """
    Get the global cancellation manager instance.

    Returns:
        The global CancellationManager instance
    """
    global _global_cancellation_manager

    if _global_cancellation_manager is None:
        _global_cancellation_manager = CancellationManager(handle_signals=True)

    return _global_cancellation_manager
