"""
Tracing utilities for Langfuse integration.

This module provides utilities for creating traces and spans in Langfuse
to track LLM calls and workflow execution asynchronously without blocking.
"""

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from src.infrastructure.langfuse_utils import get_langfuse_client


def _sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Sanitize metadata to ensure it's JSON serializable and doesn't contain unhashable types.

    Langfuse serializer fails with "TypeError: unhashable type" when metadata contains
    nested lists or dicts. This function converts complex types to strings.

    Args:
        metadata: Raw metadata dictionary that may contain complex types

    Returns:
        Sanitized metadata with all values converted to JSON-serializable types
    """
    if not metadata:
        return None

    sanitized = {}
    for key, value in metadata.items():
        try:
            # Try to JSON serialize the value to test if it's serializable
            json.dumps({key: value})
            sanitized[key] = value
        except (TypeError, ValueError):
            # If not serializable, convert to string representation
            try:
                sanitized[key] = str(value)
            except Exception as e:
                # If even string conversion fails, use a placeholder
                logger.debug(f"Failed to sanitize metadata key '{key}': {e}")
                sanitized[key] = f"<unserializable: {type(value).__name__}>"

    return sanitized if sanitized else None


@asynccontextmanager
async def trace_workflow(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None,
) -> AsyncGenerator[Any, None]:
    """
    Async context manager for tracing workflow execution.

    Usage:
        async with trace_workflow("my_workflow", metadata={"user_id": "123"}) as trace_id:
            # Do work
            # Trace automatically ends when exiting context

    Args:
        name: Name of the workflow/operation to trace
        metadata: Optional metadata dict to attach to the trace
        tags: Optional list of tags for categorization

    Yields:
        Trace ID for associating events with this trace
    """
    langfuse = get_langfuse_client()

    if not langfuse:
        logger.debug(f"Langfuse not configured, skipping trace for '{name}'")
        yield None
        return

    trace_id = None
    try:
        # Create a trace ID and start a span
        trace_id = langfuse.create_trace_id()
        # Sanitize metadata to prevent serialization errors
        sanitized_metadata = _sanitize_metadata(metadata)
        span = langfuse.start_span(
            name=name, metadata=sanitized_metadata, tags=tags or [], trace_id=trace_id
        )
        logger.debug(f"Started trace: {name} (ID: {trace_id})")
        yield trace_id

    except Exception as e:
        logger.warning(f"Error during trace creation for '{name}': {e}")
        yield None
    finally:
        try:
            # Spans are automatically sent in background, no explicit flush needed
            logger.debug(f"Completed trace: {name}")
        except Exception as e:
            logger.warning(f"Error finalizing trace '{name}': {e}")


@asynccontextmanager
async def trace_span(
    name: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None,
) -> AsyncGenerator[Any, None]:
    """
    Async context manager for tracing a span within a workflow.

    Usage:
        async with trace_workflow("workflow") as trace_id:
            async with trace_span("step_1", trace_id=trace_id) as span_id:
                # Do step 1
                pass

    Args:
        name: Name of the span/step
        trace_id: Optional parent trace ID
        metadata: Optional metadata dict
        tags: Optional list of tags

    Yields:
        Span info dict for additional tracking
    """
    langfuse = get_langfuse_client()

    if not langfuse:
        logger.debug(f"Langfuse not configured, skipping span '{name}'")
        yield None
        return

    try:
        # Create a span within the trace
        # Sanitize metadata to prevent serialization errors
        sanitized_metadata = _sanitize_metadata(metadata)
        span = langfuse.start_span(
            name=name, trace_id=trace_id, metadata=sanitized_metadata, tags=tags or []
        )
        logger.debug(f"Started span: {name}")
        yield {"span_id": getattr(span, "id", None), "name": name}

    except Exception as e:
        logger.warning(f"Error during span creation for '{name}': {e}")
        yield None
    finally:
        try:
            logger.debug(f"Completed span: {name}")
        except Exception as e:
            logger.warning(f"Error finalizing span '{name}': {e}")


def log_llm_call(
    model: str,
    input_text: str,
    output_text: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an LLM call to Langfuse.

    This creates a generation event in Langfuse to track LLM usage.

    Args:
        model: Model name (e.g., "gpt-4", "claude-3")
        input_text: The prompt sent to the LLM
        output_text: The response from the LLM
        trace_id: Optional parent trace ID to associate with this call
        metadata: Optional additional metadata
    """
    langfuse = get_langfuse_client()

    if not langfuse:
        logger.debug("Langfuse not configured, skipping LLM call logging")
        return

    try:
        # Sanitize metadata to prevent serialization errors
        sanitized_metadata = _sanitize_metadata(metadata)
        langfuse.generation(
            name=f"LLM Call - {model}",
            input=input_text,
            output=output_text,
            model=model,
            trace_id=trace_id,
            metadata=sanitized_metadata or {},
        )
        logger.debug(f"Logged LLM call: {model}")
    except Exception as e:
        logger.warning(f"Error logging LLM call to Langfuse: {e}")


async def log_llm_call_async(
    model: str,
    input_text: str,
    output_text: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Async version of log_llm_call.

    Args:
        model: Model name
        input_text: The prompt
        output_text: The response
        trace_id: Optional parent trace ID
        metadata: Optional metadata
    """
    # For now, just call the sync version in a non-blocking way
    # Langfuse client is designed to handle async operations internally
    log_llm_call(model, input_text, output_text, trace_id, metadata)
