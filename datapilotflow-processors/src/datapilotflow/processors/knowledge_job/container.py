"""
Dependency Injection Container.

This module provides a centralized container for creating and wiring
all components of the new job processing architecture.
"""

from typing import Optional

from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig
from datapilotflow.processors.knowledge_job.orchestration.cancellation_manager import (
    CancellationManager,
    get_cancellation_manager,
)
from datapilotflow.processors.knowledge_job.orchestration.job_orchestrator import JobOrchestrator
from datapilotflow.processors.knowledge_job.pipeline.pipeline import JobPipeline
from datapilotflow.processors.knowledge_job.pipeline.pipeline_factory import (
    create_pipeline_steps_for_config,
)
from datapilotflow.processors.knowledge_job.pipeline.steps import (
    DocumentChunkingStep,
    DocumentExtractionStep,
    EmbeddingGenerationStep,
    FileExtractionStep,
    TimelineRecordingStep,
    VectorStorageStep,
)


class JobProcessingContainer:
    """
    IoC Container for job processing components.

    This container assembles all the components needed for job processing,
    providing a clean separation between configuration and business logic.
    """

    def __init__(self, cancellation_manager: Optional[CancellationManager] = None):
        """
        Initialize the container.

        Args:
            cancellation_manager: Optional cancellation manager (defaults to global instance)
        """
        self.cancellation_manager = cancellation_manager or get_cancellation_manager()

    def create_job_orchestrator(
        self,
        enable_rollback: bool = False,
        knowledge_source_config: Optional[KnowledgeSourceConfig] = None,
        emit_notification_started: Optional[callable] = None,
        emit_notification_progress: Optional[callable] = None,
        emit_notification_completed: Optional[callable] = None,
        emit_notification_failed: Optional[callable] = None,
        emit_notification_cancelled: Optional[callable] = None,
    ) -> JobOrchestrator:
        """
        Create a fully configured job orchestrator.

        If knowledge_source_config is provided, creates a dynamic pipeline
        based on the content source type. Otherwise, creates a default
        web scraping pipeline.

        Args:
            enable_rollback: Whether to enable automatic rollback on failure
            knowledge_source_config: Optional config for dynamic pipeline creation
            emit_notification_started: Optional callback when job starts
            emit_notification_progress: Optional callback for progress updates
            emit_notification_completed: Optional callback when job completes
            emit_notification_failed: Optional callback when job fails
            emit_notification_cancelled: Optional callback when job is cancelled

        Returns:
            Configured JobOrchestrator ready for job execution
        """
        logger.info("Creating job orchestrator with new architecture")

        # Create pipeline steps based on configuration
        if knowledge_source_config:
            logger.info(
                f"Creating dynamic pipeline for content_source_type="
                f"{knowledge_source_config.content_source_type}, "
                f"scraping_mode={knowledge_source_config.scraping_mode}"
            )
            # Pass None for extraction_batch_size so extraction step uses job's batch_size
            steps = create_pipeline_steps_for_config(
                knowledge_source_config, extraction_batch_size=None
            )
        else:
            logger.info("Creating default web scraping pipeline")
            # Default pipeline (for backward compatibility)
            extraction_step = self._create_extraction_step()
            chunking_step = self._create_chunking_step()
            embedding_step = self._create_embedding_step()
            storage_step = self._create_storage_step()
            timeline_step = self._create_timeline_step()

            steps = [
                extraction_step,
                chunking_step,
                embedding_step,
                storage_step,
                timeline_step,
            ]

        # Assemble pipeline
        pipeline = JobPipeline(
            steps=steps,
            cancellation_manager=self.cancellation_manager,
            enable_rollback=enable_rollback,
        )

        logger.info(
            f"Created pipeline with {len(pipeline.steps)} steps: "
            f"{', '.join(pipeline.get_step_names())}"
        )

        # Create orchestrator with notification callbacks
        orchestrator = JobOrchestrator(
            pipeline=pipeline,
            cancellation_manager=self.cancellation_manager,
            emit_notification_started=emit_notification_started,
            emit_notification_progress=emit_notification_progress,
            emit_notification_completed=emit_notification_completed,
            emit_notification_failed=emit_notification_failed,
            emit_notification_cancelled=emit_notification_cancelled,
        )

        logger.info("Job orchestrator created successfully")

        return orchestrator

    def _create_extraction_step(self) -> DocumentExtractionStep:
        """
        Create the document extraction step.

        Returns:
            Configured DocumentExtractionStep
        """
        return DocumentExtractionStep(batch_size=10)

    def _create_chunking_step(self) -> DocumentChunkingStep:
        """
        Create the document chunking step.

        Returns:
            Configured DocumentChunkingStep
        """
        return DocumentChunkingStep()

    def _create_embedding_step(self) -> EmbeddingGenerationStep:
        """
        Create the embedding generation step.

        Returns:
            Configured EmbeddingGenerationStep
        """
        # Embedding service will be created dynamically based on job config
        return EmbeddingGenerationStep(embedding_service=None)

    def _create_storage_step(self) -> VectorStorageStep:
        """
        Create the vector storage step.

        Returns:
            Configured VectorStorageStep
        """
        # Storage service will be created dynamically based on job config
        return VectorStorageStep(storage_service=None)

    def _create_timeline_step(self) -> TimelineRecordingStep:
        """
        Create the timeline recording step.

        Returns:
            Configured TimelineRecordingStep
        """
        return TimelineRecordingStep(timeline_service=None)

    def create_custom_pipeline(self, step_names: list[str]) -> JobPipeline:
        """
        Create a custom pipeline with only specified steps.

        This is useful for testing or running partial workflows.

        Args:
            step_names: List of step names to include
                       (e.g., ["extraction", "chunking", "embedding"])

        Returns:
            Configured JobPipeline with selected steps

        Raises:
            ValueError: If an unknown step name is provided
        """
        step_factory = {
            "extraction": self._create_extraction_step,
            "chunking": self._create_chunking_step,
            "embedding": self._create_embedding_step,
            "storage": self._create_storage_step,
            "timeline": self._create_timeline_step,
        }

        steps = []
        for step_name in step_names:
            if step_name not in step_factory:
                raise ValueError(
                    f"Unknown step name: {step_name}. "
                    f"Available steps: {list(step_factory.keys())}"
                )

            steps.append(step_factory[step_name]())

        return JobPipeline(
            steps=steps,
            cancellation_manager=self.cancellation_manager,
            enable_rollback=False,
        )


# Global container instance
_global_container: Optional[JobProcessingContainer] = None


def get_job_processing_container() -> JobProcessingContainer:
    """
    Get the global job processing container instance.

    Returns:
        The global JobProcessingContainer
    """
    global _global_container

    if _global_container is None:
        _global_container = JobProcessingContainer()

    return _global_container


def create_job_orchestrator(
    enable_rollback: bool = False,
    knowledge_source_config: Optional[KnowledgeSourceConfig] = None,
    emit_notification_started: Optional[callable] = None,
    emit_notification_progress: Optional[callable] = None,
    emit_notification_completed: Optional[callable] = None,
    emit_notification_failed: Optional[callable] = None,
    emit_notification_cancelled: Optional[callable] = None,
) -> JobOrchestrator:
    """
    Convenience function to create a job orchestrator.

    Args:
        enable_rollback: Whether to enable automatic rollback on failure
        knowledge_source_config: Optional config for dynamic pipeline creation
        emit_notification_started: Optional callback when job starts
        emit_notification_progress: Optional callback for progress updates
        emit_notification_completed: Optional callback when job completes
        emit_notification_failed: Optional callback when job fails
        emit_notification_cancelled: Optional callback when job is cancelled

    Returns:
        Configured JobOrchestrator
    """
    container = get_job_processing_container()
    return container.create_job_orchestrator(
        enable_rollback=enable_rollback,
        knowledge_source_config=knowledge_source_config,
        emit_notification_started=emit_notification_started,
        emit_notification_progress=emit_notification_progress,
        emit_notification_completed=emit_notification_completed,
        emit_notification_failed=emit_notification_failed,
        emit_notification_cancelled=emit_notification_cancelled,
    )
