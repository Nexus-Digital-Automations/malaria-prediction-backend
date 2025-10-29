"""
Advanced Retry Strategies with Circuit Breaker Pattern for HIPAA-Compliant API Client.

This module provides sophisticated retry mechanisms with:
- Exponential backoff with jitter
- Circuit breaker pattern for endpoint protection
- Adaptive retry strategies based on error types
- Request de-duplication and idempotency
- Health monitoring and automatic recovery
- Comprehensive metrics and monitoring

Designed for high-reliability healthcare applications with fault tolerance requirements.
"""

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from .error_handling import DetailedError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(Enum):
    """Available retry strategies."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    ADAPTIVE = "adaptive"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    timeout_per_attempt: float = 30.0
    retryable_exceptions: set[type] = field(default_factory=set)
    retryable_status_codes: set[int] = field(default_factory=lambda: {408, 429, 500, 502, 503, 504})
    idempotency_key: str | None = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0
    monitor_window: float = 300.0  # 5 minutes
    half_open_max_calls: int = 3
    expected_exception: type = Exception


class RetryMetrics(BaseModel):
    """Metrics for retry operations."""
    total_attempts: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    total_retry_time: float = 0.0
    average_retry_time: float = 0.0
    max_retry_time: float = 0.0
    strategy_usage: dict[str, int] = Field(default_factory=dict)
    error_types: dict[str, int] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CircuitBreakerMetrics(BaseModel):
    """Metrics for circuit breaker operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opens: int = 0
    circuit_closes: int = 0
    half_open_attempts: int = 0
    current_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    last_failure: datetime | None = None
    last_success: datetime | None = None
    failure_rate: float = 0.0
    average_response_time: float = 0.0


class RetryResult(BaseModel):
    """Result of a retry operation."""
    success: bool
    attempts: int
    total_time: float
    last_error: str | None = None
    strategy_used: str
    circuit_breaker_triggered: bool = False
    result: Any = None


class BackoffCalculator:
    """
    Advanced backoff calculation with multiple strategies and jitter.

    Provides sophisticated delay calculation for retry operations with
    support for different backoff strategies and jitter to prevent thundering herd.
    """

    @staticmethod
    def calculate_delay(
        attempt: int,
        config: RetryConfig,
        last_delay: float = 0.0,
        error_context: DetailedError | None = None,
    ) -> float:
        """
        Calculate delay for retry attempt based on strategy and context.

        Args:
            attempt: Current attempt number (1-based)
            config: Retry configuration
            last_delay: Previous delay for adaptive strategies
            error_context: Error context for adaptive calculation

        Returns:
            Calculated delay in seconds
        """
        base_delay = config.base_delay

        # Adjust base delay based on error type for adaptive strategy
        if config.strategy == RetryStrategy.ADAPTIVE and error_context:
            base_delay = BackoffCalculator._adaptive_base_delay(base_delay, error_context)

        # Calculate delay based on strategy
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
        elif config.strategy == RetryStrategy.ADAPTIVE:
            # Adaptive strategy combines exponential with error-type adjustments
            delay = base_delay * (config.backoff_multiplier ** (attempt - 1))
            delay = BackoffCalculator._apply_adaptive_adjustments(delay, error_context, last_delay)

        # Apply jitter if enabled
        if config.jitter and delay > 0:
            jitter_amount = delay * config.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        # Ensure delay is within bounds
        delay = max(0.0, min(delay, config.max_delay))

        return delay

    @staticmethod
    def _adaptive_base_delay(base_delay: float, error_context: DetailedError) -> float:
        """Adjust base delay based on error characteristics."""
        # Increase delay for server errors (likely need more time)
        if error_context.category in [ErrorCategory.SERVER_ERROR, ErrorCategory.TIMEOUT]:
            return base_delay * 2.0

        # Increase significantly for rate limiting
        if error_context.category == ErrorCategory.RATE_LIMIT:
            return base_delay * 5.0

        # Reduce delay for client errors (unlikely to be transient)
        if error_context.category in [ErrorCategory.CLIENT_ERROR, ErrorCategory.DATA_VALIDATION]:
            return base_delay * 0.5

        # Default for network and other transient errors
        return base_delay

    @staticmethod
    def _apply_adaptive_adjustments(delay: float, error_context: DetailedError | None, last_delay: float) -> float:
        """Apply adaptive adjustments to calculated delay."""
        if not error_context:
            return delay

        # For repeated same-type errors, increase delay more aggressively
        if error_context.category in [ErrorCategory.RATE_LIMIT, ErrorCategory.SERVER_ERROR]:
            delay *= 1.5

        # For authentication errors, use shorter delays as they're often quick to resolve
        if error_context.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.TOKEN]:
            delay *= 0.7

        # For critical errors, use longer delays
        if error_context.severity == ErrorSeverity.CRITICAL:
            delay *= 2.0

        return delay


class CircuitBreaker:
    """
    Advanced circuit breaker implementation with health monitoring.

    Implements the circuit breaker pattern to prevent cascading failures
    and provide automatic recovery when services become healthy again.
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig,
        health_check: Callable[[], Awaitable[bool]] | None = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique identifier for this circuit breaker
            config: Circuit breaker configuration
            health_check: Optional health check function
        """
        self.name = name
        self.config = config
        self.health_check = health_check

        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.next_attempt_time: datetime | None = None

        # Request tracking for monitoring window
        self.request_history: list[tuple[datetime, bool, float]] = []  # (timestamp, success, response_time)

        # Metrics
        self.metrics = CircuitBreakerMetrics()

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(f"Circuit breaker '{name}' initialized with {config.failure_threshold} failure threshold")

    async def call(self, func: Callable[[], Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if circuit allows request
            if not await self._can_execute():
                self.metrics.total_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Will retry after {self.next_attempt_time}"
                )

            # Track request attempt
            self.metrics.total_requests += 1
            start_time = time.time()

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Record success
                response_time = time.time() - start_time
                await self._record_success(response_time)

                return result

            except Exception as e:
                # Record failure
                response_time = time.time() - start_time
                await self._record_failure(e, response_time)
                raise

    async def _can_execute(self) -> bool:
        """Check if circuit breaker allows execution."""
        now = datetime.now(UTC)

        if self.state == CircuitBreakerState.CLOSED:
            return True

        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.next_attempt_time and now >= self.next_attempt_time:
                # Transition to half-open
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                return True
            return False

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited number of calls in half-open state
            return self.success_count < self.config.half_open_max_calls

    async def _record_success(self, response_time: float) -> None:
        """Record successful request."""
        now = datetime.now(UTC)
        self.request_history.append((now, True, response_time))
        self.metrics.successful_requests += 1
        self.metrics.last_success = now

        # Update average response time
        self._update_average_response_time(response_time)

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                # Transition to closed
                await self._close_circuit()

        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

        # Clean old history
        await self._cleanup_history()

    async def _record_failure(self, exception: Exception, response_time: float) -> None:
        """Record failed request."""
        now = datetime.now(UTC)
        self.request_history.append((now, False, response_time))
        self.metrics.failed_requests += 1
        self.metrics.last_failure = now
        self.last_failure_time = now

        # Update average response time
        self._update_average_response_time(response_time)

        # Check if this is the expected exception type
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1

            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._open_circuit()

            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Immediately open on failure in half-open state
                await self._open_circuit()

        # Clean old history
        await self._cleanup_history()

    async def _open_circuit(self) -> None:
        """Transition circuit to open state."""
        self.state = CircuitBreakerState.OPEN
        self.next_attempt_time = datetime.now(UTC) + timedelta(seconds=self.config.timeout)
        self.metrics.circuit_opens += 1
        self.metrics.current_state = CircuitBreakerState.OPEN

        logger.warning(
            f"Circuit breaker '{self.name}' OPENED due to {self.failure_count} failures. "
            f"Will retry after {self.next_attempt_time}"
        )

        # Optionally run health check
        if self.health_check:
            asyncio.create_task(self._monitor_health())

    async def _close_circuit(self) -> None:
        """Transition circuit to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.next_attempt_time = None
        self.metrics.circuit_closes += 1
        self.metrics.current_state = CircuitBreakerState.CLOSED

        logger.info(f"Circuit breaker '{self.name}' CLOSED - service appears healthy")

    async def _monitor_health(self) -> None:
        """Monitor service health when circuit is open."""
        if not self.health_check:
            return

        while self.state == CircuitBreakerState.OPEN:
            try:
                if await self.health_check():
                    # Service is healthy, allow transition to half-open earlier
                    self.next_attempt_time = datetime.now(UTC)
                    logger.info(f"Health check passed for '{self.name}' - allowing early retry")
                    break
            except Exception as e:
                logger.debug(f"Health check failed for '{self.name}': {e}")

            # Wait before next health check
            await asyncio.sleep(self.config.timeout / 4)

    async def _cleanup_history(self) -> None:
        """Clean old request history outside monitoring window."""
        cutoff = datetime.now(UTC) - timedelta(seconds=self.config.monitor_window)
        self.request_history = [
            (timestamp, success, response_time)
            for timestamp, success, response_time in self.request_history
            if timestamp > cutoff
        ]

        # Update failure rate
        if self.request_history:
            failures = sum(1 for _, success, _ in self.request_history if not success)
            self.metrics.failure_rate = failures / len(self.request_history) * 100
        else:
            self.metrics.failure_rate = 0.0

    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time metric."""
        total_requests = self.metrics.total_requests
        if total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Running average
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (total_requests - 1) + response_time) / total_requests
            )

    async def get_status(self) -> dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "next_attempt_time": self.next_attempt_time.isoformat() if self.next_attempt_time else None,
            "metrics": self.metrics.dict(),
            "request_history_count": len(self.request_history),
        }

    async def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.next_attempt_time = None
            self.request_history.clear()

            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class RetryExecutor:
    """
    Advanced retry executor with comprehensive strategies and monitoring.

    Provides sophisticated retry logic with circuit breaker integration,
    request de-duplication, and comprehensive metrics collection.
    """

    def __init__(self, default_config: RetryConfig | None = None) -> None:
        """
        Initialize retry executor.

        Args:
            default_config: Default retry configuration
        """
        self.default_config = default_config or RetryConfig()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.metrics = RetryMetrics()
        self.active_requests: dict[str, asyncio.Future] = {}  # For de-duplication

        # Thread safety
        self._metrics_lock = asyncio.Lock()

        logger.info("Retry executor initialized with advanced strategies")

    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[T]],
        config: RetryConfig | None = None,
        circuit_breaker_name: str | None = None,
        error_handler: Callable[[DetailedError], Awaitable[bool]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RetryResult:
        """
        Execute function with comprehensive retry logic.

        Args:
            func: Async function to execute
            config: Retry configuration (uses default if None)
            circuit_breaker_name: Name of circuit breaker to use
            error_handler: Optional error handler for custom logic
            context: Additional context for retry decisions

        Returns:
            RetryResult with execution details
        """
        retry_config = config or self.default_config
        start_time = time.time()
        last_error = None
        last_delay = 0.0

        # Check for request de-duplication
        if retry_config.idempotency_key:
            dedup_result = await self._handle_request_deduplication(
                retry_config.idempotency_key, func
            )
            if dedup_result is not None:
                return dedup_result

        # Get circuit breaker if specified
        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = await self._get_circuit_breaker(circuit_breaker_name)

        for attempt in range(1, retry_config.max_attempts + 1):
            try:
                # Execute through circuit breaker if available
                if circuit_breaker:
                    result = await circuit_breaker.call(func)
                else:
                    result = await asyncio.wait_for(func(), timeout=retry_config.timeout_per_attempt)

                # Success - update metrics and return
                total_time = time.time() - start_time
                await self._update_success_metrics(attempt, total_time, retry_config.strategy)

                return RetryResult(
                    success=True,
                    attempts=attempt,
                    total_time=total_time,
                    strategy_used=retry_config.strategy.value,
                    result=result,
                )

            except Exception as e:
                last_error = e
                total_time = time.time() - start_time

                # Classify error for retry decision
                detailed_error = DetailedError(
                    message=str(e),
                    original_exception=e,
                    metadata={"attempt": attempt, "total_time": total_time}
                )

                # Check if error is retryable
                if not await self._is_retryable(e, retry_config, detailed_error):
                    await self._update_failure_metrics(attempt, total_time, retry_config.strategy, str(e))
                    break

                # Call custom error handler if provided
                if error_handler:
                    try:
                        should_continue = await error_handler(detailed_error)
                        if not should_continue:
                            break
                    except Exception as handler_error:
                        logger.warning(f"Error handler failed: {handler_error}")

                # Don't delay after last attempt
                if attempt < retry_config.max_attempts:
                    delay = BackoffCalculator.calculate_delay(
                        attempt, retry_config, last_delay, detailed_error
                    )

                    logger.info(
                        f"Retry attempt {attempt} failed, retrying in {delay:.2f}s: {str(e)[:100]}"
                    )

                    await asyncio.sleep(delay)
                    last_delay = delay

        # All attempts failed
        total_time = time.time() - start_time
        await self._update_failure_metrics(
            retry_config.max_attempts, total_time, retry_config.strategy, str(last_error)
        )

        return RetryResult(
            success=False,
            attempts=retry_config.max_attempts,
            total_time=total_time,
            last_error=str(last_error),
            strategy_used=retry_config.strategy.value,
            circuit_breaker_triggered=isinstance(last_error, CircuitBreakerOpenError),
        )

    async def _is_retryable(
        self,
        exception: Exception,
        config: RetryConfig,
        detailed_error: DetailedError
    ) -> bool:
        """Determine if exception is retryable based on configuration and context."""

        # Check if exception type is retryable
        if config.retryable_exceptions and type(exception) not in config.retryable_exceptions:
            return False

        # Check HTTP status codes if available
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
            if status_code not in config.retryable_status_codes:
                return False

        # Check error category for retry eligibility
        non_retryable_categories = {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.DATA_VALIDATION,
            ErrorCategory.SECURITY,
        }

        if detailed_error.category in non_retryable_categories:
            return False

        # Circuit breaker open errors are not retryable at this level
        if isinstance(exception, CircuitBreakerOpenError):
            return False

        return True

    async def _handle_request_deduplication(
        self, idempotency_key: str, func: Callable[[], Awaitable[T]]
    ) -> RetryResult | None:
        """Handle request de-duplication for idempotent operations."""
        if idempotency_key in self.active_requests:
            # Wait for existing request to complete
            try:
                result = await self.active_requests[idempotency_key]
                return RetryResult(
                    success=True,
                    attempts=0,  # Deduplicated request
                    total_time=0.0,
                    strategy_used="deduplicated",
                    result=result,
                )
            except Exception:
                # Existing request failed, allow new attempt
                return None

        # Create new request future
        future: asyncio.Future[Any] = asyncio.Future()
        self.active_requests[idempotency_key] = future

        try:
            result = await func()
            future.set_result(result)
            return None  # Let normal retry logic handle it
        except Exception as e:
            future.set_exception(e)
            return None
        finally:
            # Clean up
            if idempotency_key in self.active_requests:
                del self.active_requests[idempotency_key]

    async def _get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker by name."""
        if name not in self.circuit_breakers:
            config = CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)

        return self.circuit_breakers[name]

    async def _update_success_metrics(self, attempts: int, total_time: float, strategy: RetryStrategy):
        """Update metrics for successful retry operation."""
        async with self._metrics_lock:
            self.metrics.total_attempts += attempts
            if attempts > 1:
                self.metrics.successful_retries += 1
                self.metrics.total_retry_time += total_time
                self.metrics.max_retry_time = max(self.metrics.max_retry_time, total_time)

            # Update strategy usage
            strategy_name = strategy.value
            self.metrics.strategy_usage[strategy_name] = (
                self.metrics.strategy_usage.get(strategy_name, 0) + 1
            )

            # Update average retry time
            if self.metrics.successful_retries > 0:
                self.metrics.average_retry_time = (
                    self.metrics.total_retry_time / self.metrics.successful_retries
                )

            self.metrics.last_updated = datetime.now(UTC)

    async def _update_failure_metrics(
        self, attempts: int, total_time: float, strategy: RetryStrategy, error_type: str
    ):
        """Update metrics for failed retry operation."""
        async with self._metrics_lock:
            self.metrics.total_attempts += attempts
            self.metrics.failed_retries += 1

            # Update strategy usage
            strategy_name = strategy.value
            self.metrics.strategy_usage[strategy_name] = (
                self.metrics.strategy_usage.get(strategy_name, 0) + 1
            )

            # Update error types
            self.metrics.error_types[error_type] = (
                self.metrics.error_types.get(error_type, 0) + 1
            )

            self.metrics.last_updated = datetime.now(UTC)

    def add_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig,
        health_check: Callable[[], Awaitable[bool]] | None = None
    ):
        """Add custom circuit breaker."""
        self.circuit_breakers[name] = CircuitBreaker(name, config, health_check)
        logger.info(f"Added circuit breaker: {name}")

    async def get_circuit_breaker_status(self, name: str) -> dict[str, Any] | None:
        """Get status of specific circuit breaker."""
        if name in self.circuit_breakers:
            return await self.circuit_breakers[name].get_status()
        return None

    async def get_all_circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all circuit breakers."""
        status = {}
        for name, breaker in self.circuit_breakers.items():
            status[name] = await breaker.get_status()
        return status

    def get_retry_metrics(self) -> RetryMetrics:
        """Get current retry metrics."""
        return self.metrics

    async def reset_circuit_breaker(self, name: str) -> bool:
        """Reset specific circuit breaker."""
        if name in self.circuit_breakers:
            await self.circuit_breakers[name].reset()
            return True
        return False

    async def reset_all_circuit_breakers(self):
        """Reset all circuit breakers."""
        for breaker in self.circuit_breakers.values():
            await breaker.reset()
        logger.info("All circuit breakers reset")

    def get_comprehensive_status(self) -> dict[str, Any]:
        """Get comprehensive status of retry executor."""
        return {
            "retry_metrics": self.metrics.dict(),
            "circuit_breaker_count": len(self.circuit_breakers),
            "active_requests": len(self.active_requests),
            "default_config": {
                "strategy": self.default_config.strategy.value,
                "max_attempts": self.default_config.max_attempts,
                "base_delay": self.default_config.base_delay,
                "max_delay": self.default_config.max_delay,
            },
        }
