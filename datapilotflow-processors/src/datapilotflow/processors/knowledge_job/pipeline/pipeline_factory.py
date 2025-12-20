"""
Pipeline Factory.

This module provides factory functions for creating pipelines based on
knowledge source configuration, allowing dynamic pipeline composition.
"""

from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import (
    ContentSourceType,
    KnowledgeSourceConfig,
)
from datapilotflow.processors.knowledge_job.pipeline.base import PipelineStep
from datapilotflow.processors.knowledge_job.pipeline.steps import (
    DocumentChunkingStep,
    DocumentExtractionStep,
    EmbeddingGenerationStep,
    FileExtractionStep,
    TimelineRecordingStep,
    VectorStorageStep,
)


class PipelineFactory:
    """
    Factory for creating pipelines based on knowledge source configuration.

    This factory determines which extraction step to use and assembles
    the appropriate pipeline steps based on the content source type.
    """

    @staticmethod
    def create_extraction_step(
        knowledge_source_config: KnowledgeSourceConfig, batch_size: Optional[int] = None
    ) -> PipelineStep:
        """
        Create the appropriate extraction step based on content source type.

        Args:
            knowledge_source_config: The knowledge source configuration
            batch_size: Batch size for document extraction (if None, step will use job's batch_size)

        Returns:
            Appropriate extraction step (FileExtractionStep or DocumentExtractionStep)
        """
        content_source_type = knowledge_source_config.content_source_type

        if content_source_type == ContentSourceType.LOCAL_FILES:
            logger.info(
                f"Creating FileExtractionStep for local files "
                f"(mode: {knowledge_source_config.scraping_mode})"
            )
            return FileExtractionStep(batch_size=batch_size)

        elif content_source_type == ContentSourceType.WEB_SCRAPING:
            logger.info(
                f"Creating DocumentExtractionStep for web scraping "
                f"(mode: {knowledge_source_config.scraping_mode})"
            )
            return DocumentExtractionStep(batch_size=batch_size)

        else:
            logger.warning(
                f"Unknown content source type: {content_source_type}. "
                f"Defaulting to DocumentExtractionStep"
            )
            return DocumentExtractionStep(batch_size=batch_size)

    @staticmethod
    def create_pipeline_steps(
        knowledge_source_config: KnowledgeSourceConfig,
        extraction_batch_size: Optional[int] = None,
    ) -> List[PipelineStep]:
        """
        Create a complete list of pipeline steps based on configuration.

        The pipeline steps are:
        1. Extraction (File or Document based on source type)
        2. Chunking
        3. Embedding
        4. Storage
        5. Timeline

        Args:
            knowledge_source_config: The knowledge source configuration
            extraction_batch_size: Batch size for extraction step (if None, uses job's batch_size)

        Returns:
            List of pipeline steps in execution order
        """
        logger.info(
            f"Creating pipeline for content_source_type={knowledge_source_config.content_source_type}, "
            f"scraping_mode={knowledge_source_config.scraping_mode}"
        )

        steps = [
            # Step 1: Extract documents (file or web)
            PipelineFactory.create_extraction_step(
                knowledge_source_config, batch_size=extraction_batch_size
            ),
            # Step 2: Chunk documents
            DocumentChunkingStep(),
            # Step 3: Generate embeddings
            EmbeddingGenerationStep(embedding_service=None),
            # Step 4: Store in vector database
            VectorStorageStep(storage_service=None),
            # Step 5: Record timeline
            TimelineRecordingStep(timeline_service=None),
        ]

        step_names = [step.name for step in steps]
        logger.info(f"Created pipeline with {len(steps)} steps: {', '.join(step_names)}")

        return steps

    @staticmethod
    def get_pipeline_description(
        knowledge_source_config: KnowledgeSourceConfig,
    ) -> str:
        """
        Get a human-readable description of the pipeline for a given configuration.

        Args:
            knowledge_source_config: The knowledge source configuration

        Returns:
            Description of the pipeline that will be created
        """
        content_type = knowledge_source_config.content_source_type
        scraping_mode = knowledge_source_config.scraping_mode

        if content_type == ContentSourceType.LOCAL_FILES:
            return (
                f"Local File Pipeline ({scraping_mode}): "
                f"File Extraction → Chunking → Embedding → Storage → Timeline"
            )
        elif content_type == ContentSourceType.WEB_SCRAPING:
            return (
                f"Web Scraping Pipeline ({scraping_mode}): "
                f"Web Extraction → Chunking → Embedding → Storage → Timeline"
            )
        else:
            return (
                f"Default Pipeline ({content_type}): "
                f"Extraction → Chunking → Embedding → Storage → Timeline"
            )


def create_pipeline_steps_for_config(
    knowledge_source_config: KnowledgeSourceConfig,
    extraction_batch_size: Optional[int] = None,
) -> List[PipelineStep]:
    """
    Convenience function to create pipeline steps for a configuration.

    Args:
        knowledge_source_config: The knowledge source configuration
        extraction_batch_size: Batch size for extraction step (if None, uses job's batch_size)

    Returns:
        List of pipeline steps
    """
    return PipelineFactory.create_pipeline_steps(
        knowledge_source_config, extraction_batch_size
    )


def get_pipeline_description(
    knowledge_source_config: KnowledgeSourceConfig,
) -> str:
    """
    Convenience function to get pipeline description.

    Args:
        knowledge_source_config: The knowledge source configuration

    Returns:
        Pipeline description
    """
    return PipelineFactory.get_pipeline_description(knowledge_source_config)
