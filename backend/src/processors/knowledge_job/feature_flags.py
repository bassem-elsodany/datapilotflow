"""
Feature Flags for Job Processing.

This module provides feature flags for gradually migrating from the old
architecture to the new pipeline-based architecture.
"""

import os
from typing import Optional

from loguru import logger


class JobProcessingFeatureFlags:
    """
    Feature flags for job processing architecture migration.

    These flags allow safe, gradual migration from old to new architecture.
    """

    def __init__(self):
        """Initialize feature flags from environment variables."""
        # Main feature flag: Use new architecture
        self.use_new_architecture = self._get_bool_env(
            "JOB_PROCESSING_USE_NEW_ARCHITECTURE", default=False
        )

        # Percentage-based rollout (0-100)
        self.rollout_percentage = self._get_int_env(
            "JOB_PROCESSING_ROLLOUT_PERCENTAGE", default=0, min_val=0, max_val=100
        )

        # Canary mode: Only specific job IDs use new architecture
        canary_jobs = os.getenv("JOB_PROCESSING_CANARY_JOBS", "")
        self.canary_job_ids = set(
            job_id.strip() for job_id in canary_jobs.split(",") if job_id.strip()
        )

        # Shadow mode: Run both architectures and compare (for testing)
        self.shadow_mode = self._get_bool_env(
            "JOB_PROCESSING_SHADOW_MODE", default=False
        )

        # Log configuration
        self._log_configuration()

    def should_use_new_architecture(self, job_id: Optional[str] = None) -> bool:
        """
        Determine if new architecture should be used for a job.

        Args:
            job_id: Optional job ID for canary testing

        Returns:
            True if new architecture should be used, False otherwise
        """
        # Check main flag
        if self.use_new_architecture:
            return True

        # Check canary list
        if job_id and job_id in self.canary_job_ids:
            logger.info(f"Job {job_id} is in canary list - using new architecture")
            return True

        # Check percentage rollout
        if self.rollout_percentage > 0:
            # Use hash of job_id for consistent routing
            if job_id:
                import hashlib

                hash_value = int(hashlib.md5(job_id.encode()).hexdigest(), 16)
                job_percentage = hash_value % 100

                use_new = job_percentage < self.rollout_percentage
                if use_new:
                    logger.info(
                        f"Job {job_id} selected for new architecture "
                        f"(rollout: {self.rollout_percentage}%)"
                    )
                return use_new

        return False

    def is_shadow_mode_enabled(self) -> bool:
        """
        Check if shadow mode is enabled.

        In shadow mode, both old and new architectures run in parallel
        for comparison and validation.

        Returns:
            True if shadow mode is enabled
        """
        return self.shadow_mode

    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int_env(
        self, key: str, default: int = 0, min_val: int = None, max_val: int = None
    ) -> int:
        """Get integer environment variable with validation."""
        try:
            value = int(os.getenv(key, str(default)))

            if min_val is not None and value < min_val:
                logger.warning(
                    f"{key}={value} is below minimum {min_val}, using {min_val}"
                )
                return min_val

            if max_val is not None and value > max_val:
                logger.warning(
                    f"{key}={value} is above maximum {max_val}, using {max_val}"
                )
                return max_val

            return value

        except ValueError:
            logger.warning(
                f"Invalid integer value for {key}, using default {default}"
            )
            return default

    def _log_configuration(self):
        """Log the current feature flag configuration."""
        logger.info("Job Processing Feature Flags Configuration:")
        logger.info(f"  Use New Architecture: {self.use_new_architecture}")
        logger.info(f"  Rollout Percentage: {self.rollout_percentage}%")
        logger.info(f"  Canary Jobs: {len(self.canary_job_ids)} configured")
        logger.info(f"  Shadow Mode: {self.shadow_mode}")

    def get_config_summary(self) -> dict:
        """
        Get configuration summary as dictionary.

        Returns:
            Dictionary with feature flag configuration
        """
        return {
            "use_new_architecture": self.use_new_architecture,
            "rollout_percentage": self.rollout_percentage,
            "canary_jobs_count": len(self.canary_job_ids),
            "shadow_mode": self.shadow_mode,
        }


# Global instance
_global_feature_flags: Optional[JobProcessingFeatureFlags] = None


def get_feature_flags() -> JobProcessingFeatureFlags:
    """
    Get the global feature flags instance.

    Returns:
        JobProcessingFeatureFlags instance
    """
    global _global_feature_flags

    if _global_feature_flags is None:
        _global_feature_flags = JobProcessingFeatureFlags()

    return _global_feature_flags
