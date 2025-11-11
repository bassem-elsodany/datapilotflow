"""
Error Retry Middleware for agent execution resilience.

Provides:
- Exponential backoff retry logic
- Circuit breaker pattern for repeated failures
- Transient vs permanent error classification
- Error context tracking
"""

import asyncio
import time
from typing import Callable, Any, Optional, List, Tuple
from enum import Enum
from loguru import logger


class ErrorType(Enum):
    """Classification of error types"""
    TRANSIENT = "transient"  # Temporary, retryable
    PERMANENT = "permanent"  # Not retryable
    UNKNOWN = "unknown"  # Unknown, treat as transient


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


def classify_error(error: Exception) -> ErrorType:
    """
    Classify error type for retry logic.

    Args:
        error: Exception to classify

    Returns:
        ErrorType enum value
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Transient errors (should retry)
    transient_patterns = [
        "timeout",
        "connection refused",
        "connection reset",
        "temporary failure",
        "rate limit",
        "too many requests",
        "service unavailable",
        "temporarily unavailable",
        "429",
        "503",
        "504",
        "timed out",
    ]

    for pattern in transient_patterns:
        if pattern in error_str or pattern in error_type:
            return ErrorType.TRANSIENT

    # Permanent errors (don't retry)
    permanent_patterns = [
        "invalid",
        "not found",
        "authentication",
        "permission",
        "forbidden",
        "401",
        "403",
        "404",
        "validation",
        "bad request",
        "malformed",
    ]

    for pattern in permanent_patterns:
        if pattern in error_str or pattern in error_type:
            return ErrorType.PERMANENT

    return ErrorType.UNKNOWN


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Repeated failures, calls rejected immediately
    - HALF_OPEN: Testing recovery, allow one call to try
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout_seconds: Time before attempting recovery
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.name = name

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    def record_success(self) -> None:
        """Record successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"[CIRCUIT BREAKER] {self.name}: Recovery successful, closing circuit")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
        else:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitBreakerState.OPEN:
                logger.warning(
                    f"[CIRCUIT BREAKER] {self.name}: Opening circuit after {self.failure_count} failures"
                )
            self.state = CircuitBreakerState.OPEN

    def can_execute(self) -> bool:
        """
        Check if call can be executed.

        Returns:
            True if call should proceed, False if should be rejected
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time is None:
                return False

            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout_seconds:
                logger.info(f"[CIRCUIT BREAKER] {self.name}: Attempting recovery (half-open state)")
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True

            return False

        if self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_ms: int = 100,
        max_delay_ms: int = 10000,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum retry attempts (including initial)
            initial_delay_ms: Initial delay in milliseconds
            max_delay_ms: Maximum delay in milliseconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay_ms(self, attempt: int) -> int:
        """
        Calculate delay for attempt with exponential backoff.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in milliseconds
        """
        delay = self.initial_delay_ms * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_ms)

        if self.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return int(delay)


async def execute_with_retry(
    func: Callable,
    func_name: str = "function",
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
) -> Any:
    """
    Execute async function with retry logic and circuit breaker.

    Args:
        func: Async function to execute
        func_name: Name for logging
        retry_config: Retry configuration (uses defaults if None)
        circuit_breaker: Circuit breaker instance (optional)

    Returns:
        Function result

    Raises:
        Exception: If all retries fail or circuit is open
    """
    if retry_config is None:
        retry_config = RetryConfig()

    # Check circuit breaker
    if circuit_breaker and not circuit_breaker.can_execute():
        error_msg = (
            f"Circuit breaker open for '{func_name}' - "
            f"too many failures, rejecting call"
        )
        logger.error(f"[RETRY] {error_msg}")
        raise Exception(error_msg)

    last_exception = None

    for attempt in range(retry_config.max_attempts):
        try:
            logger.debug(f"[RETRY] {func_name}: Attempt {attempt + 1}/{retry_config.max_attempts}")

            result = await func()

            # Record success in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success()

            logger.debug(f"[RETRY] {func_name}: Attempt {attempt + 1} successful")
            return result

        except Exception as e:
            last_exception = e
            error_type = classify_error(e)

            # Record failure in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_failure()

            # Don't retry permanent errors
            if error_type == ErrorType.PERMANENT:
                logger.error(
                    f"[RETRY] {func_name}: Permanent error, not retrying: {str(e)}"
                )
                raise

            # Last attempt failed
            if attempt == retry_config.max_attempts - 1:
                error_msg = (
                    f"All {retry_config.max_attempts} retry attempts failed for '{func_name}'. "
                    f"Last error: {str(e)}"
                )
                logger.error(f"[RETRY] {error_msg}")
                raise Exception(error_msg) from e

            # Calculate delay and wait
            delay_ms = retry_config.get_delay_ms(attempt)
            logger.warning(
                f"[RETRY] {func_name}: Attempt {attempt + 1} failed ({error_type.value}). "
                f"Retrying in {delay_ms}ms... Error: {str(e)[:100]}"
            )

            await asyncio.sleep(delay_ms / 1000.0)

    # Should not reach here
    if last_exception:
        raise last_exception
    raise Exception(f"Unexpected error executing {func_name}")


def create_circuit_breakers() -> dict:
    """
    Create circuit breakers for critical services.

    Returns:
        Dictionary of CircuitBreaker instances by service name
    """
    return {
        "rag_tool": CircuitBreaker(
            failure_threshold=3,
            recovery_timeout_seconds=30.0,
            name="rag_tool"
        ),
        "llm_client": CircuitBreaker(
            failure_threshold=5,
            recovery_timeout_seconds=60.0,
            name="llm_client"
        ),
        "task_tools": CircuitBreaker(
            failure_threshold=4,
            recovery_timeout_seconds=45.0,
            name="task_tools"
        ),
    }
