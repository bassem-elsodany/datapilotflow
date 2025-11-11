"""
Tool Middleware for advanced tool execution management.

Provides:
- Tool execution timeouts
- Input/output validation
- Error handling and logging
- Tool result verification
"""

import asyncio
import functools
import traceback
from typing import Any, Callable, Optional, List, Dict
from langchain_core.tools import BaseTool, ToolException
from loguru import logger

# Module-level storage for current agent state (set by supervisor)
_current_agent_state: Optional[Any] = None


def set_current_agent_state(agent_state: Any) -> None:
    """Set the current agent state for RAG context injection."""
    global _current_agent_state
    _current_agent_state = agent_state


def get_current_agent_state() -> Optional[Any]:
    """Get the current agent state."""
    return _current_agent_state


class ToolTimeoutError(ToolException):
    """Raised when tool execution exceeds timeout"""
    pass


class ToolValidationError(ToolException):
    """Raised when tool input/output validation fails"""
    pass


def validate_tool_input(tool_name: str, args: Dict[str, Any], max_input_length: int = 50000) -> None:
    """
    Validate tool input arguments.

    Args:
        tool_name: Name of the tool
        args: Input arguments
        max_input_length: Maximum allowed total input length

    Raises:
        ToolValidationError: If validation fails
    """
    # Check for None/empty critical arguments
    for key, value in args.items():
        if value is None and key != "rag_documents":
            logger.warning(f"[TOOL VALIDATION] {tool_name}: Argument '{key}' is None")

    # Check total input size
    total_size = sum(len(str(v)) for v in args.values())
    if total_size > max_input_length:
        raise ToolValidationError(
            f"Tool input too large: {total_size} chars (max {max_input_length}). "
            f"Tool: {tool_name}"
        )

    logger.debug(f"[TOOL VALIDATION] {tool_name}: Input valid ({total_size} chars)")


def validate_tool_output(tool_name: str, output: Any, max_output_length: int = 100000) -> None:
    """
    Validate tool output.

    Args:
        tool_name: Name of the tool
        output: Tool output
        max_output_length: Maximum allowed output length

    Raises:
        ToolValidationError: If validation fails
    """
    if output is None:
        logger.warning(f"[TOOL VALIDATION] {tool_name}: Output is None")
        return

    # Check output size
    output_str = str(output)
    if len(output_str) > max_output_length:
        raise ToolValidationError(
            f"Tool output too large: {len(output_str)} chars (max {max_output_length}). "
            f"Tool: {tool_name}. Output preview: {output_str[:100]}..."
        )

    logger.debug(f"[TOOL VALIDATION] {tool_name}: Output valid ({len(output_str)} chars)")


async def wrap_tool_with_timeout(
    func: Callable,
    tool_name: str,
    timeout_seconds: float = 60.0
) -> Any:
    """
    Wrap async function with timeout protection.

    Args:
        func: Async function to wrap
        tool_name: Name of the tool (for logging)
        timeout_seconds: Timeout in seconds

    Returns:
        Wrapped function result

    Raises:
        ToolTimeoutError: If execution exceeds timeout
    """
    try:
        logger.debug(f"[TOOL TIMEOUT] {tool_name}: Starting with {timeout_seconds}s timeout")
        result = await asyncio.wait_for(func(), timeout=timeout_seconds)
        logger.debug(f"[TOOL TIMEOUT] {tool_name}: Completed within timeout")
        return result
    except asyncio.TimeoutError:
        error_msg = f"Tool '{tool_name}' execution timed out after {timeout_seconds}s"
        logger.error(f"[TOOL TIMEOUT] {error_msg}")
        raise ToolTimeoutError(error_msg)
    except Exception as e:
        logger.error(f"[TOOL TIMEOUT] {tool_name}: Error during timeout-wrapped execution: {e}")
        raise


def create_tool_middleware(
    tool: BaseTool,
    timeout_seconds: float = 60.0,
    validate_input: bool = True,
    validate_output: bool = True,
) -> BaseTool:
    """
    Wrap a LangChain tool with middleware for timeout and validation.

    Args:
        tool: LangChain BaseTool to wrap
        timeout_seconds: Tool execution timeout in seconds
        validate_input: Whether to validate input
        validate_output: Whether to validate output

    Returns:
        Wrapped tool with middleware applied
    """
    original_func = tool.func
    tool_name = tool.name

    @functools.wraps(original_func)
    async def wrapped_async_func(**kwargs) -> Any:
        """Wrapped async tool function with timeout and validation"""
        try:
            # Validate input if enabled
            if validate_input:
                try:
                    validate_tool_input(tool_name, kwargs)
                except ToolValidationError as e:
                    logger.error(f"[TOOL MIDDLEWARE] {tool_name}: Input validation failed: {e}")
                    raise

            # Execute with timeout
            async def tool_execution():
                """Tool execution function"""
                return await original_func(**kwargs)

            result = await wrap_tool_with_timeout(
                tool_execution,
                tool_name,
                timeout_seconds
            )

            # Validate output if enabled
            if validate_output:
                try:
                    validate_tool_output(tool_name, result)
                except ToolValidationError as e:
                    logger.error(f"[TOOL MIDDLEWARE] {tool_name}: Output validation failed: {e}")
                    # Don't raise - output validation is warning-only

            logger.info(f"[TOOL MIDDLEWARE] {tool_name}: Execution successful")
            return result

        except (ToolTimeoutError, ToolValidationError) as e:
            # Expected tool errors
            logger.error(f"[TOOL MIDDLEWARE] {tool_name}: {str(e)}")
            raise
        except Exception as e:
            # Unexpected errors
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(f"[TOOL MIDDLEWARE] {error_msg}")
            logger.error(f"[TOOL MIDDLEWARE] Traceback: {traceback.format_exc()}")
            raise ToolException(error_msg)

    @functools.wraps(original_func)
    def wrapped_sync_func(**kwargs) -> Any:
        """Wrapped sync tool function with validation (timeout not available for sync)"""
        try:
            # Validate input if enabled
            if validate_input:
                try:
                    validate_tool_input(tool_name, kwargs)
                except ToolValidationError as e:
                    logger.error(f"[TOOL MIDDLEWARE] {tool_name}: Input validation failed: {e}")
                    raise

            # Execute (no timeout for sync functions)
            result = original_func(**kwargs)

            # Validate output if enabled
            if validate_output:
                try:
                    validate_tool_output(tool_name, result)
                except ToolValidationError as e:
                    logger.error(f"[TOOL MIDDLEWARE] {tool_name}: Output validation failed: {e}")
                    # Don't raise - output validation is warning-only

            logger.info(f"[TOOL MIDDLEWARE] {tool_name}: Execution successful")
            return result

        except (ToolValidationError, ToolException) as e:
            logger.error(f"[TOOL MIDDLEWARE] {tool_name}: {str(e)}")
            raise
        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(f"[TOOL MIDDLEWARE] {error_msg}")
            logger.error(f"[TOOL MIDDLEWARE] Traceback: {traceback.format_exc()}")
            raise ToolException(error_msg)

    # Replace tool function based on whether it's async or sync
    if asyncio.iscoroutinefunction(original_func):
        tool.func = wrapped_async_func
        logger.debug(f"[TOOL MIDDLEWARE] {tool_name}: Applied async middleware (timeout: {timeout_seconds}s)")
    else:
        tool.func = wrapped_sync_func
        logger.debug(f"[TOOL MIDDLEWARE] {tool_name}: Applied sync middleware (no timeout)")

    return tool


def inject_rag_context_to_task_tool(tool: BaseTool) -> BaseTool:
    """
    Wrap a task tool to automatically inject RAG context as a parameter.
    RAG context is retrieved from the current agent state at runtime.

    Args:
        tool: The task tool to wrap

    Returns:
        Wrapped tool with RAG context injection
    """
    tool_name = tool.name
    original_func = tool.func

    def wrapped_with_rag_context(*args, **kwargs) -> str:
        """Wrapper that injects RAG context from current agent_state."""
        # Get RAG context from current agent state at call time
        current_state = get_current_agent_state()
        rag_context = current_state.get("rag_context", "") if current_state else ""

        # Inject as rag_documents parameter
        kwargs["rag_documents"] = rag_context

        logger.debug(
            f"[RAG INJECTION] {tool_name}: Injected {len(rag_context)} chars of RAG context"
        )

        # Call original function with RAG context
        return original_func(*args, **kwargs)

    async def wrapped_with_rag_context_async(*args, **kwargs) -> str:
        """Async wrapper that injects RAG context from current agent_state."""
        # Get RAG context from current agent state at call time
        current_state = get_current_agent_state()
        rag_context = current_state.get("rag_context", "") if current_state else ""

        # Inject as rag_documents parameter
        kwargs["rag_documents"] = rag_context

        logger.debug(
            f"[RAG INJECTION] {tool_name}: Injected {len(rag_context)} chars of RAG context"
        )

        # Call original function with RAG context
        if asyncio.iscoroutinefunction(original_func):
            return await original_func(*args, **kwargs)
        else:
            return original_func(*args, **kwargs)

    # Replace function based on whether it's async or sync
    if asyncio.iscoroutinefunction(original_func):
        tool.func = wrapped_with_rag_context_async
        logger.debug(f"[RAG INJECTION] {tool_name}: Applied async RAG context injection")
    else:
        tool.func = wrapped_with_rag_context
        logger.debug(f"[RAG INJECTION] {tool_name}: Applied sync RAG context injection")

    return tool


def apply_middleware_to_tools(
    tools: List[BaseTool],
    timeout_seconds: float = 60.0,
    validate_input: bool = True,
    validate_output: bool = True,
) -> List[BaseTool]:
    """
    Apply middleware to a list of tools.

    Args:
        tools: List of LangChain tools
        timeout_seconds: Tool execution timeout
        validate_input: Whether to validate inputs
        validate_output: Whether to validate outputs

    Returns:
        List of tools with middleware applied
    """
    wrapped_tools = []

    for tool in tools:
        try:
            wrapped_tool = create_tool_middleware(
                tool,
                timeout_seconds=timeout_seconds,
                validate_input=validate_input,
                validate_output=validate_output,
            )
            wrapped_tools.append(wrapped_tool)
        except Exception as e:
            logger.warning(
                f"Failed to apply middleware to tool '{tool.name}': {e}. "
                f"Using original tool without middleware."
            )
            wrapped_tools.append(tool)

    logger.info(f"[TOOL MIDDLEWARE] Applied middleware to {len(wrapped_tools)} tools")
    return wrapped_tools
