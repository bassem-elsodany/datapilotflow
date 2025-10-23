"""
Job Processing Pipeline.

This module implements the pipeline executor that runs pipeline steps sequentially,
handling errors, rollbacks, and cancellation.
"""

import time
import traceback
from typing import List, Optional

from loguru import logger

from src.processors.knowledge_job.orchestration.cancellation_manager import (
    CancellationManager,
    JobCancelledException,
)
from src.processors.knowledge_job.orchestration.job_context import JobContext

from .base import PipelineResult, PipelineStep, StepResult, StepStatus


class JobPipeline:
    """
    Executes a sequence of pipeline steps for job processing.

    The pipeline runs steps in order, passing a shared JobContext through each step.
    It handles errors, cancellation, and can optionally rollback on failure.
    """

    def __init__(
        self,
        steps: List[PipelineStep],
        cancellation_manager: Optional[CancellationManager] = None,
        enable_rollback: bool = False,
    ):
        """
        Initialize the job pipeline.

        Args:
            steps: List of pipeline steps to execute in order
            cancellation_manager: Optional cancellation manager for handling cancellation
            enable_rollback: Whether to rollback steps on failure (default: False)
        """
        self.steps = steps
        self.cancellation_manager = cancellation_manager
        self.enable_rollback = enable_rollback

    async def execute(self, context: JobContext) -> PipelineResult:
        """
        Execute the pipeline with the given context.

        Args:
            context: The job execution context

        Returns:
            PipelineResult containing execution results and metadata
        """
        start_time = time.time()
        step_results: List[StepResult] = []
        completed_steps = 0
        failed_step = None

        logger.info(
            f"Starting pipeline execution for job {context.get_job_id()} "
            f"with {len(self.steps)} steps"
        )

        try:
            for i, step in enumerate(self.steps, 1):
                # Check for cancellation before each step
                if self.cancellation_manager:
                    self.cancellation_manager.check_and_raise(context.get_job_id())

                logger.info(
                    f"Executing step {i}/{len(self.steps)}: {step.name} "
                    f"(job: {context.get_job_id()})"
                )

                step_result = await self._execute_step(step, context)
                step_result.metadata["step_name"] = step.name
                step_result.metadata["step_index"] = i
                step_results.append(step_result)

                if not step_result.success:
                    failed_step = step.name
                    logger.error(
                        f"Step {step.name} failed: {step_result.error} "
                        f"(job: {context.get_job_id()})"
                    )

                    # Attempt rollback if enabled
                    if self.enable_rollback:
                        await self._rollback_steps(step_results[:-1], context)

                    break

                completed_steps += 1
                logger.info(
                    f"Step {step.name} completed successfully in "
                    f"{step_result.execution_time_seconds:.2f}s "
                    f"(job: {context.get_job_id()})"
                )

        except JobCancelledException as e:
            logger.warning(f"Pipeline cancelled: {e}")
            # Add cancellation result
            step_results.append(
                StepResult.cancelled_result(reason=str(e)).model_copy(
                    update={
                        "metadata": {
                            "step_name": "cancellation",
                            "step_index": len(step_results) + 1,
                        }
                    }
                )
            )
            failed_step = "cancelled"

        except Exception as e:
            logger.error(f"Unexpected pipeline error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Add error result
            step_results.append(
                StepResult.failure_result(
                    error=str(e), error_traceback=traceback.format_exc()
                ).model_copy(
                    update={
                        "metadata": {
                            "step_name": "pipeline_error",
                            "step_index": len(step_results) + 1,
                        }
                    }
                )
            )
            failed_step = "pipeline_error"

        total_time = time.time() - start_time
        success = completed_steps == len(self.steps)

        result = PipelineResult(
            success=success,
            step_results=step_results,
            total_execution_time_seconds=total_time,
            completed_steps=completed_steps,
            failed_step=failed_step,
            metadata={
                "job_id": context.get_job_id(),
                "total_steps": len(self.steps),
                "stats": context.stats,
            },
        )

        logger.info(
            f"Pipeline execution {'completed' if success else 'failed'} "
            f"for job {context.get_job_id()}: "
            f"{completed_steps}/{len(self.steps)} steps in {total_time:.2f}s"
        )

        return result

    async def _execute_step(
        self, step: PipelineStep, context: JobContext
    ) -> StepResult:
        """
        Execute a single pipeline step with error handling.

        Args:
            step: The step to execute
            context: The job execution context

        Returns:
            StepResult from the step execution
        """
        step_start_time = time.time()

        try:
            # Validate preconditions
            if not await step.validate(context):
                logger.warning(
                    f"Step {step.name} validation failed, skipping "
                    f"(job: {context.get_job_id()})"
                )
                return StepResult(
                    success=False,
                    status=StepStatus.SKIPPED,
                    error="Step validation failed",
                )

            # Execute the step
            result = await step.execute(context)
            result.execution_time_seconds = time.time() - step_start_time
            return result

        except JobCancelledException:
            # Re-raise cancellation to be handled at pipeline level
            raise

        except Exception as e:
            # Catch and wrap any unhandled exceptions
            logger.error(f"Step {step.name} raised exception: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            execution_time = time.time() - step_start_time
            return StepResult.failure_result(
                error=str(e),
                error_traceback=traceback.format_exc(),
                metadata={"execution_time_seconds": execution_time},
            )

    async def _rollback_steps(
        self, step_results: List[StepResult], context: JobContext
    ) -> None:
        """
        Rollback completed steps in reverse order.

        Args:
            step_results: List of step results to rollback
            context: The job execution context
        """
        logger.warning(
            f"Rolling back {len(step_results)} completed steps "
            f"(job: {context.get_job_id()})"
        )

        # Rollback in reverse order
        for i, step_result in enumerate(reversed(step_results)):
            if not step_result.success:
                continue

            step_index = step_result.metadata.get("step_index", 0)
            if step_index > 0 and step_index <= len(self.steps):
                step = self.steps[step_index - 1]

                try:
                    logger.info(f"Rolling back step: {step.name}")
                    await step.rollback(context)
                    logger.info(f"Step {step.name} rolled back successfully")

                except Exception as e:
                    logger.error(f"Error rolling back step {step.name}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

    def get_step_names(self) -> List[str]:
        """
        Get list of step names in the pipeline.

        Returns:
            List of step names
        """
        return [step.name for step in self.steps]

    def __repr__(self) -> str:
        return f"JobPipeline(steps={len(self.steps)}, rollback={self.enable_rollback})"
