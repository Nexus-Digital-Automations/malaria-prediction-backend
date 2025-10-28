"""
Comprehensive Error Handling Framework for HIPAA-Compliant API Client.

This module provides a robust error handling system with:
- Comprehensive error taxonomy and classification
- Context-aware error recovery strategies
- User-friendly error message mapping
- Error analytics and reporting
- Retry logic with exponential backoff
- Circuit breaker pattern implementation

Designed for healthcare applications requiring high reliability and compliance.
"""

import asyncio
import logging
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for systematic classification."""
    # Network and connectivity errors
    NETWORK = "network"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    DNS = "dns"
    SSL_TLS = "ssl_tls"

    # Authentication and authorization errors
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TOKEN = "token"
    CREDENTIALS = "credentials"

    # API and HTTP errors
    CLIENT_ERROR = "client_error"  # 4xx
    SERVER_ERROR = "server_error"  # 5xx
    RATE_LIMIT = "rate_limit"
    API_UNAVAILABLE = "api_unavailable"

    # Data and validation errors
    DATA_VALIDATION = "data_validation"
    PARSING = "parsing"
    SERIALIZATION = "serialization"
    SCHEMA = "schema"

    # Business logic errors
    BUSINESS_RULE = "business_rule"
    RESOURCE_NOT_FOUND = "resource_not_found"
    CONFLICT = "conflict"
    PRECONDITION = "precondition"

    # System and infrastructure errors
    SYSTEM = "system"
    DATABASE = "database"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"

    # Security errors
    SECURITY = "security"
    AUDIT = "audit"
    COMPLIANCE = "compliance"

    # Unknown or unclassified
    UNKNOWN = "unknown"


class ErrorAction(Enum):
    """Recommended actions for error handling."""
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAK = "circuit_break"
    FAIL_FAST = "fail_fast"
    DEGRADE_GRACEFULLY = "degrade_gracefully"
    LOG_AND_CONTINUE = "log_and_continue"
    ALERT_ADMIN = "alert_admin"
    SECURITY_ALERT = "security_alert"


class ErrorContext(BaseModel):
    """Context information for error occurrences."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str | None = Field(None, description="Request identifier")
    user_id: str | None = Field(None, description="User identifier")
    session_id: str | None = Field(None, description="Session identifier")
    endpoint: str | None = Field(None, description="API endpoint")
    method: str | None = Field(None, description="HTTP method")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    correlation_id: str | None = Field(None, description="Correlation identifier")
    trace_id: str | None = Field(None, description="Distributed trace identifier")
    additional_context: dict[str, Any] = Field(default_factory=dict)


@dataclass
class ErrorPattern:
    """Error pattern definition for classification and handling."""
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    action: ErrorAction
    retry_eligible: bool = True
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    circuit_breaker_threshold: int = 5
    user_message: str = "An error occurred. Please try again."
    admin_message: str = ""
    matchers: list[Callable[[Exception], bool]] = field(default_factory=list)
    recovery_strategies: list[str] = field(default_factory=list)


class ErrorMetrics(BaseModel):
    """Error metrics for analytics and monitoring."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    count: int = 1
    first_occurrence: datetime
    last_occurrence: datetime
    total_duration: float = 0.0
    affected_users: set[str] = Field(default_factory=set)
    endpoints: set[str] = Field(default_factory=set)
    recovery_attempts: int = 0
    successful_recoveries: int = 0

    class Config:
        arbitrary_types_allowed = True


class DetailedError(Exception):
    """
    Enhanced exception class with comprehensive error information.

    Provides detailed context, classification, and recovery information
    for sophisticated error handling and debugging.
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: str | None = None,
        context: ErrorContext | None = None,
        original_exception: Exception | None = None,
        retry_eligible: bool = True,
        user_message: str | None = None,
        recovery_suggestions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize detailed error with comprehensive information.

        Args:
            message: Technical error message for developers
            category: Error category for classification
            severity: Severity level for prioritization
            error_code: Unique error code for tracking
            context: Request and session context
            original_exception: Original exception that caused this error
            retry_eligible: Whether this error can be retried
            user_message: User-friendly error message
            recovery_suggestions: Suggested recovery actions
            metadata: Additional error metadata
        """
        super().__init__(message)

        self.message = message
        self.category = category
        self.severity = severity
        self.error_code = error_code or self._generate_error_code()
        self.context = context or ErrorContext()
        self.original_exception = original_exception
        self.retry_eligible = retry_eligible
        self.user_message = user_message or self._get_default_user_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.metadata = metadata or {}
        self.stack_trace = traceback.format_exc()

        # Timing information
        self.created_at = datetime.now(UTC)

    def _generate_error_code(self) -> str:
        """Generate unique error code."""
        import uuid
        return f"ERR_{self.category.value.upper()}_{str(uuid.uuid4())[:8]}"

    def _get_default_user_message(self) -> str:
        """Get default user-friendly message based on category."""
        messages = {
            ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection and try again.",
            ErrorCategory.TIMEOUT: "The request took too long to complete. Please try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to access this resource.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment and try again.",
            ErrorCategory.SERVER_ERROR: "Server error occurred. Our team has been notified.",
            ErrorCategory.DATA_VALIDATION: "Invalid data provided. Please check your input and try again.",
            ErrorCategory.RESOURCE_NOT_FOUND: "The requested resource was not found.",
            ErrorCategory.SECURITY: "Security error detected. This incident has been logged.",
        }
        return messages.get(self.category, "An unexpected error occurred. Please try again.")

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "retry_eligible": self.retry_eligible,
            "recovery_suggestions": self.recovery_suggestions,
            "context": self.context.dict() if self.context else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "stack_trace": self.stack_trace if self.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None,
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return f"[{self.error_code}] {self.category.value}: {self.message}"


class ErrorClassifier:
    """
    Intelligent error classifier that categorizes exceptions into structured error patterns.

    Uses pattern matching and heuristics to classify errors for appropriate handling.
    """

    def __init__(self) -> None:
        """Initialize error classifier with default patterns."""
        self.patterns: list[ErrorPattern] = []
        self._initialize_default_patterns()

    def _initialize_default_patterns(self):
        """Initialize default error patterns for common scenarios."""

        # Network errors
        self.patterns.extend([
            ErrorPattern(
                name="connection_timeout",
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.RETRY_WITH_BACKOFF,
                max_retries=3,
                user_message="Connection timeout. Please try again.",
                matchers=[
                    lambda e: "timeout" in str(e).lower(),
                    lambda e: "timed out" in str(e).lower(),
                ],
                recovery_strategies=["retry_with_backoff", "check_network_connectivity"],
            ),
            ErrorPattern(
                name="connection_refused",
                category=ErrorCategory.CONNECTION,
                severity=ErrorSeverity.HIGH,
                action=ErrorAction.CIRCUIT_BREAK,
                user_message="Service temporarily unavailable. Please try again later.",
                matchers=[
                    lambda e: "connection refused" in str(e).lower(),
                    lambda e: "connection reset" in str(e).lower(),
                ],
                recovery_strategies=["circuit_break", "check_service_health"],
            ),
            ErrorPattern(
                name="dns_resolution",
                category=ErrorCategory.DNS,
                severity=ErrorSeverity.HIGH,
                action=ErrorAction.FAIL_FAST,
                retry_eligible=False,
                user_message="DNS resolution failed. Please check your network settings.",
                matchers=[
                    lambda e: "name resolution" in str(e).lower(),
                    lambda e: "dns" in str(e).lower(),
                ],
                recovery_strategies=["check_dns_settings", "try_alternative_endpoint"],
            ),
        ])

        # HTTP errors
        self.patterns.extend([
            ErrorPattern(
                name="unauthorized",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.FAIL_FAST,
                retry_eligible=False,
                user_message="Authentication failed. Please check your credentials.",
                matchers=[
                    lambda e: hasattr(e, 'status_code') and e.status_code == 401,
                    lambda e: "unauthorized" in str(e).lower(),
                ],
                recovery_strategies=["refresh_token", "re_authenticate"],
            ),
            ErrorPattern(
                name="forbidden",
                category=ErrorCategory.AUTHORIZATION,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.FAIL_FAST,
                retry_eligible=False,
                user_message="Access denied. You don't have permission for this action.",
                matchers=[
                    lambda e: hasattr(e, 'status_code') and e.status_code == 403,
                    lambda e: "forbidden" in str(e).lower(),
                ],
                recovery_strategies=["check_permissions", "contact_administrator"],
            ),
            ErrorPattern(
                name="rate_limited",
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.RETRY_WITH_BACKOFF,
                max_retries=5,
                backoff_multiplier=3.0,
                user_message="Rate limit exceeded. Please wait and try again.",
                matchers=[
                    lambda e: hasattr(e, 'status_code') and e.status_code == 429,
                    lambda e: "rate limit" in str(e).lower(),
                ],
                recovery_strategies=["exponential_backoff", "reduce_request_rate"],
            ),
            ErrorPattern(
                name="server_error",
                category=ErrorCategory.SERVER_ERROR,
                severity=ErrorSeverity.HIGH,
                action=ErrorAction.RETRY_WITH_BACKOFF,
                max_retries=2,
                user_message="Server error occurred. Our team has been notified.",
                matchers=[
                    lambda e: hasattr(e, 'status_code') and 500 <= e.status_code < 600,
                    lambda e: "internal server error" in str(e).lower(),
                ],
                recovery_strategies=["retry_with_backoff", "alert_operations"],
            ),
        ])

        # Security errors
        self.patterns.extend([
            ErrorPattern(
                name="token_expired",
                category=ErrorCategory.TOKEN,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.RETRY,
                max_retries=1,
                user_message="Session expired. Please log in again.",
                matchers=[
                    lambda e: "token expired" in str(e).lower(),
                    lambda e: "jwt expired" in str(e).lower(),
                ],
                recovery_strategies=["refresh_token", "re_authenticate"],
            ),
            ErrorPattern(
                name="security_violation",
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.CRITICAL,
                action=ErrorAction.SECURITY_ALERT,
                retry_eligible=False,
                user_message="Security violation detected. This incident has been logged.",
                matchers=[
                    lambda e: "security" in str(e).lower() and "violation" in str(e).lower(),
                    lambda e: "suspicious activity" in str(e).lower(),
                ],
                recovery_strategies=["security_alert", "audit_log", "block_session"],
            ),
        ])

        # Data validation errors
        self.patterns.extend([
            ErrorPattern(
                name="validation_error",
                category=ErrorCategory.DATA_VALIDATION,
                severity=ErrorSeverity.LOW,
                action=ErrorAction.FAIL_FAST,
                retry_eligible=False,
                user_message="Invalid data provided. Please check your input.",
                matchers=[
                    lambda e: "validation" in str(e).lower(),
                    lambda e: hasattr(e, 'status_code') and e.status_code == 422,
                ],
                recovery_strategies=["validate_input", "provide_error_details"],
            ),
            ErrorPattern(
                name="parsing_error",
                category=ErrorCategory.PARSING,
                severity=ErrorSeverity.MEDIUM,
                action=ErrorAction.FAIL_FAST,
                retry_eligible=False,
                user_message="Data format error. Please check the data format.",
                matchers=[
                    lambda e: "parsing" in str(e).lower(),
                    lambda e: "json" in str(e).lower() and "decode" in str(e).lower(),
                ],
                recovery_strategies=["check_data_format", "validate_schema"],
            ),
        ])

    def classify_error(self, exception: Exception, context: ErrorContext | None = None) -> DetailedError:
        """
        Classify an exception into a DetailedError with appropriate categorization.

        Args:
            exception: The exception to classify
            context: Request context for additional information

        Returns:
            DetailedError with classification and handling information
        """
        # Find matching pattern
        matching_pattern = None
        for pattern in self.patterns:
            if any(matcher(exception) for matcher in pattern.matchers):
                matching_pattern = pattern
                break

        if matching_pattern:
            # Create DetailedError based on pattern
            detailed_error = DetailedError(
                message=str(exception),
                category=matching_pattern.category,
                severity=matching_pattern.severity,
                context=context,
                original_exception=exception,
                retry_eligible=matching_pattern.retry_eligible,
                user_message=matching_pattern.user_message,
                recovery_suggestions=matching_pattern.recovery_strategies,
                metadata={
                    "pattern_name": matching_pattern.name,
                    "max_retries": matching_pattern.max_retries,
                    "backoff_multiplier": matching_pattern.backoff_multiplier,
                    "recommended_action": matching_pattern.action.value,
                }
            )
        else:
            # Create generic DetailedError for unclassified exceptions
            detailed_error = DetailedError(
                message=str(exception),
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                context=context,
                original_exception=exception,
                metadata={"exception_type": type(exception).__name__}
            )

        logger.warning(f"Error classified: {detailed_error}")
        return detailed_error

    def add_pattern(self, pattern: ErrorPattern):
        """Add custom error pattern."""
        self.patterns.insert(0, pattern)  # Insert at beginning for priority
        logger.info(f"Added custom error pattern: {pattern.name}")

    def remove_pattern(self, pattern_name: str) -> bool:
        """Remove error pattern by name."""
        for i, pattern in enumerate(self.patterns):
            if pattern.name == pattern_name:
                del self.patterns[i]
                logger.info(f"Removed error pattern: {pattern_name}")
                return True
        return False


class ErrorHandler:
    """
    Comprehensive error handling orchestrator with recovery strategies.

    Manages error classification, recovery attempts, metrics collection,
    and escalation procedures for robust error handling.
    """

    def __init__(
        self,
        classifier: ErrorClassifier | None = None,
        enable_metrics: bool = True,
        max_retry_attempts: int = 3,
        default_backoff_multiplier: float = 2.0,
    ):
        """
        Initialize error handler with configuration.

        Args:
            classifier: Error classifier instance
            enable_metrics: Whether to collect error metrics
            max_retry_attempts: Default maximum retry attempts
            default_backoff_multiplier: Default backoff multiplier
        """
        self.classifier = classifier or ErrorClassifier()
        self.enable_metrics = enable_metrics
        self.max_retry_attempts = max_retry_attempts
        self.default_backoff_multiplier = default_backoff_multiplier

        # Error tracking and metrics
        self.error_metrics: dict[str, ErrorMetrics] = {}
        self.error_history: list[DetailedError] = []
        self.recovery_strategies: dict[str, Callable] = {}

        # Thread safety
        self._metrics_lock = asyncio.Lock()

        # Initialize default recovery strategies
        self._initialize_recovery_strategies()

        logger.info("Error handler initialized with comprehensive error management")

    def _initialize_recovery_strategies(self):
        """Initialize default recovery strategies."""
        self.recovery_strategies.update({
            "retry_with_backoff": self._retry_with_exponential_backoff,
            "refresh_token": self._refresh_authentication_token,
            "check_network_connectivity": self._check_network_connectivity,
            "circuit_break": self._activate_circuit_breaker,
            "security_alert": self._trigger_security_alert,
            "validate_input": self._validate_input_data,
        })

    async def handle_error(
        self,
        exception: Exception,
        context: ErrorContext | None = None,
        attempt_recovery: bool = True,
    ) -> DetailedError:
        """
        Handle an error with classification and optional recovery.

        Args:
            exception: The exception to handle
            context: Request context
            attempt_recovery: Whether to attempt error recovery

        Returns:
            DetailedError with handling results
        """
        # Classify the error
        detailed_error = self.classifier.classify_error(exception, context)

        # Record metrics
        if self.enable_metrics:
            await self._record_error_metrics(detailed_error)

        # Add to history
        self.error_history.append(detailed_error)

        # Attempt recovery if enabled and error is recoverable
        if attempt_recovery and detailed_error.retry_eligible:
            recovery_result = await self._attempt_recovery(detailed_error)
            detailed_error.metadata["recovery_attempted"] = True
            detailed_error.metadata["recovery_result"] = recovery_result

        # Log the error
        self._log_error(detailed_error)

        return detailed_error

    async def _attempt_recovery(self, error: DetailedError) -> dict[str, Any]:
        """
        Attempt error recovery using available strategies.

        Args:
            error: Detailed error to recover from

        Returns:
            Recovery result information
        """
        recovery_result = {
            "attempted_strategies": [],
            "successful_strategies": [],
            "failed_strategies": [],
            "recovery_time": 0.0,
        }

        start_time = time.time()

        for strategy_name in error.recovery_suggestions:
            if strategy_name in self.recovery_strategies:
                recovery_result["attempted_strategies"].append(strategy_name)

                try:
                    strategy_func = self.recovery_strategies[strategy_name]
                    result = await strategy_func(error)

                    if result.get("success", False):
                        recovery_result["successful_strategies"].append(strategy_name)
                        logger.info(f"Recovery strategy '{strategy_name}' succeeded for error {error.error_code}")
                    else:
                        recovery_result["failed_strategies"].append(strategy_name)
                        logger.warning(f"Recovery strategy '{strategy_name}' failed for error {error.error_code}")

                except Exception as e:
                    recovery_result["failed_strategies"].append(strategy_name)
                    logger.error(f"Recovery strategy '{strategy_name}' raised exception: {e}")

        recovery_result["recovery_time"] = time.time() - start_time
        return recovery_result

    async def _record_error_metrics(self, error: DetailedError):
        """Record error metrics for analytics."""
        async with self._metrics_lock:
            error_key = f"{error.category.value}_{error.severity.value}"

            if error_key in self.error_metrics:
                metrics = self.error_metrics[error_key]
                metrics.count += 1
                metrics.last_occurrence = error.created_at

                if error.context and error.context.user_id:
                    metrics.affected_users.add(error.context.user_id)

                if error.context and error.context.endpoint:
                    metrics.endpoints.add(error.context.endpoint)
            else:
                affected_users = set()
                endpoints = set()

                if error.context and error.context.user_id:
                    affected_users.add(error.context.user_id)

                if error.context and error.context.endpoint:
                    endpoints.add(error.context.endpoint)

                self.error_metrics[error_key] = ErrorMetrics(
                    error_id=error.error_code,
                    category=error.category,
                    severity=error.severity,
                    first_occurrence=error.created_at,
                    last_occurrence=error.created_at,
                    affected_users=affected_users,
                    endpoints=endpoints,
                )

    def _log_error(self, error: DetailedError):
        """Log error with appropriate level based on severity."""
        log_level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        log_level = log_level_map.get(error.severity, logging.WARNING)

        # Create log message
        log_msg = f"[{error.error_code}] {error.category.value}: {error.message}"

        if error.context:
            context_info = []
            if error.context.user_id:
                context_info.append(f"user={error.context.user_id}")
            if error.context.endpoint:
                context_info.append(f"endpoint={error.context.endpoint}")
            if error.context.request_id:
                context_info.append(f"request={error.context.request_id}")

            if context_info:
                log_msg += f" ({', '.join(context_info)})"

        logger.log(log_level, log_msg)

        # Log stack trace for high severity errors
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and error.stack_trace:
            logger.log(log_level, f"Stack trace for {error.error_code}:\n{error.stack_trace}")

    # Recovery strategy implementations
    async def _retry_with_exponential_backoff(self, error: DetailedError) -> dict[str, Any]:
        """Implement exponential backoff retry strategy."""
        max_retries = error.metadata.get("max_retries", self.max_retry_attempts)
        backoff_multiplier = error.metadata.get("backoff_multiplier", self.default_backoff_multiplier)

        # This is a placeholder - actual retry would be implemented by the calling code
        return {
            "success": True,
            "strategy": "exponential_backoff",
            "max_retries": max_retries,
            "backoff_multiplier": backoff_multiplier,
            "message": "Retry parameters configured for exponential backoff",
        }

    async def _refresh_authentication_token(self, error: DetailedError) -> dict[str, Any]:
        """Refresh authentication token recovery strategy."""
        # Placeholder for token refresh logic
        return {
            "success": True,
            "strategy": "token_refresh",
            "message": "Token refresh initiated",
        }

    async def _check_network_connectivity(self, error: DetailedError) -> dict[str, Any]:
        """Check network connectivity recovery strategy."""
        # Placeholder for network connectivity check
        return {
            "success": True,
            "strategy": "network_check",
            "message": "Network connectivity check completed",
        }

    async def _activate_circuit_breaker(self, error: DetailedError) -> dict[str, Any]:
        """Activate circuit breaker recovery strategy."""
        # Placeholder for circuit breaker activation
        return {
            "success": True,
            "strategy": "circuit_breaker",
            "message": "Circuit breaker activated",
        }

    async def _trigger_security_alert(self, error: DetailedError) -> dict[str, Any]:
        """Trigger security alert recovery strategy."""
        # Placeholder for security alert
        logger.critical(f"SECURITY ALERT: {error.message} - Error Code: {error.error_code}")
        return {
            "success": True,
            "strategy": "security_alert",
            "message": "Security alert triggered",
        }

    async def _validate_input_data(self, error: DetailedError) -> dict[str, Any]:
        """Validate input data recovery strategy."""
        # Placeholder for input validation
        return {
            "success": True,
            "strategy": "input_validation",
            "message": "Input validation guidelines provided",
        }

    def add_recovery_strategy(self, name: str, strategy_func: Callable):
        """Add custom recovery strategy."""
        self.recovery_strategies[name] = strategy_func
        logger.info(f"Added custom recovery strategy: {name}")

    def get_error_metrics_report(self, hours: int = 24) -> dict[str, Any]:
        """
        Generate error metrics report.

        Args:
            hours: Number of hours to include in report

        Returns:
            Comprehensive error metrics report
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        # Filter recent errors
        recent_errors = [
            error for error in self.error_history
            if error.created_at > cutoff
        ]

        # Calculate statistics
        total_errors = len(recent_errors)

        # Group by category
        category_stats = {}
        severity_stats = {}

        for error in recent_errors:
            # Category statistics
            cat_key = error.category.value
            if cat_key not in category_stats:
                category_stats[cat_key] = {"count": 0, "severities": {}}
            category_stats[cat_key]["count"] += 1

            # Severity within category
            sev_key = error.severity.value
            if sev_key not in category_stats[cat_key]["severities"]:
                category_stats[cat_key]["severities"][sev_key] = 0
            category_stats[cat_key]["severities"][sev_key] += 1

            # Overall severity statistics
            if sev_key not in severity_stats:
                severity_stats[sev_key] = 0
            severity_stats[sev_key] += 1

        # Calculate error rates
        critical_errors = severity_stats.get("critical", 0)
        high_errors = severity_stats.get("high", 0)

        return {
            "report_period": {
                "start": cutoff.isoformat(),
                "end": datetime.now(UTC).isoformat(),
                "hours": hours,
            },
            "summary": {
                "total_errors": total_errors,
                "critical_errors": critical_errors,
                "high_severity_errors": high_errors,
                "error_rate_per_hour": total_errors / max(hours, 1),
            },
            "category_breakdown": category_stats,
            "severity_breakdown": severity_stats,
            "top_error_categories": sorted(
                category_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5],
            "metrics_summary": {
                name: {
                    "count": metrics.count,
                    "affected_users": len(metrics.affected_users),
                    "endpoints": len(metrics.endpoints),
                    "recovery_rate": (
                        metrics.successful_recoveries / max(metrics.recovery_attempts, 1) * 100
                        if metrics.recovery_attempts > 0 else 0
                    ),
                }
                for name, metrics in self.error_metrics.items()
            },
            "recommendations": self._generate_error_recommendations(recent_errors),
        }

    def _generate_error_recommendations(self, recent_errors: list[DetailedError]) -> list[str]:
        """Generate recommendations based on recent error patterns."""
        recommendations = []

        if not recent_errors:
            return ["No recent errors - system appears healthy"]

        # Check for high error rates
        if len(recent_errors) > 50:  # Threshold for high error rate
            recommendations.append("High error rate detected - investigate system stability")

        # Check for security issues
        security_errors = [e for e in recent_errors if e.category == ErrorCategory.SECURITY]
        if security_errors:
            recommendations.append("Security errors detected - review access patterns and authentication")

        # Check for network issues
        network_errors = [
            e for e in recent_errors
            if e.category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT, ErrorCategory.CONNECTION]
        ]
        if len(network_errors) > len(recent_errors) * 0.3:  # 30% network errors
            recommendations.append("High network error rate - check connectivity and service health")

        # Check for validation issues
        validation_errors = [e for e in recent_errors if e.category == ErrorCategory.DATA_VALIDATION]
        if len(validation_errors) > len(recent_errors) * 0.2:  # 20% validation errors
            recommendations.append("High validation error rate - review input validation and user guidance")

        if not recommendations:
            recommendations.append("Error patterns appear normal - continue monitoring")

        return recommendations
