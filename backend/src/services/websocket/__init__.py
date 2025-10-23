"""
WebSocket Services Package.

This package contains services for real-time communication,
including job progress updates and notifications.
"""

from .job_progress_service import JobProgressService, get_job_progress_service

__all__ = [
    "JobProgressService",
    "get_job_progress_service",
]
