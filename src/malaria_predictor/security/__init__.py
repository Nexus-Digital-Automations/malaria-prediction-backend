"""
Security Framework for HIPAA-Compliant Malaria Prediction API.

This package provides comprehensive security features including:
- Secure JWT token management with encryption
- Advanced error handling with taxonomy
- Retry strategies with circuit breaker protection
- Security audit logging with anomaly detection
- HIPAA-compliant audit trails and reporting

Main Components:
- TokenManager: Secure token storage and management
- ErrorHandler: Comprehensive error classification and handling
- RetryExecutor: Advanced retry strategies with circuit breakers
- SecurityAuditLogger: HIPAA-compliant audit logging and monitoring

Usage:
    from malaria_predictor.security import (
        TokenManager,
        ErrorHandler,
        RetryExecutor,
        SecurityAuditLogger,
        DetailedError,
        AuditEventType,
        ComplianceFramework,
    )

Example:
    # Initialize security framework
    token_manager = TokenManager(secret_key="your-secret-key")
    error_handler = ErrorHandler()
    retry_executor = RetryExecutor()
    audit_logger = SecurityAuditLogger(storage_path=Path("audit_logs"))

    # Create tokens
    tokens = await token_manager.create_tokens(
        user_id="user123",
        scopes={"read:predictions", "write:predictions"}
    )

    # Handle errors with classification
    try:
        # Some operation that might fail
        pass
    except Exception as e:
        detailed_error = await error_handler.handle_error(e)
        logger.error(f"Classified error: {detailed_error}")

    # Execute with retry and circuit breaker
    result = await retry_executor.execute_with_retry(
        func=some_async_function,
        circuit_breaker_name="external_api"
    )

    # Log security event
    await audit_logger.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        description="User accessed prediction data",
        user_id="user123",
        phi_involved=True
    )
"""

from collections.abc import Callable
from typing import Any

from .audit_logger import (
    AnomalyDetector,
    AuditEvent,
    AuditEventType,
    AuditRiskLevel,
    ComplianceFramework,
    SecurityAuditLogger,
    SecurityMetrics,
)
from .error_handling import (
    DetailedError,
    ErrorAction,
    ErrorCategory,
    ErrorClassifier,
    ErrorContext,
    ErrorHandler,
    ErrorMetrics,
    ErrorPattern,
    ErrorSeverity,
)
from .retry_strategies import (
    BackoffCalculator,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    RetryConfig,
    RetryExecutor,
    RetryResult,
    RetryStrategy,
)
from .token_manager import (
    SecureTokenStorage,
    SecurityAuditEvent,
    TokenData,
    TokenError,
    TokenExpiredError,
    TokenManager,
    TokenValidationError,
)

# Version information
__version__ = "1.0.0"
__author__ = "Malaria Predictor Security Team"

# Security framework components
__all__ = [
    # Token Management
    "TokenManager",
    "TokenData",
    "TokenError",
    "TokenExpiredError",
    "TokenValidationError",
    "SecureTokenStorage",
    "SecurityAuditEvent",

    # Error Handling
    "ErrorHandler",
    "ErrorClassifier",
    "DetailedError",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorAction",
    "ErrorContext",
    "ErrorPattern",
    "ErrorMetrics",

    # Retry Strategies
    "RetryExecutor",
    "RetryStrategy",
    "RetryConfig",
    "RetryResult",
    "BackoffCalculator",
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",

    # Audit Logging
    "SecurityAuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditRiskLevel",
    "ComplianceFramework",
    "SecurityMetrics",
    "AnomalyDetector",
]

# Compliance and security constants
HIPAA_RETENTION_DAYS = 2557  # 7 years for HIPAA compliance
DEFAULT_ENCRYPTION_ALGORITHM = "AES-256"
DEFAULT_HASH_ALGORITHM = "SHA-256"

# Security best practices configuration
SECURITY_DEFAULTS = {
    "token_expiry_minutes": 30,
    "refresh_token_expiry_days": 7,
    "max_retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "audit_log_retention_days": HIPAA_RETENTION_DAYS,
    "encryption_required": True,
    "integrity_verification": True,
}

# Framework initialization helpers
def create_security_framework(
    storage_path: str,
    secret_key: str,
    application_name: str = "malaria_predictor",
    environment: str = "production",
    enable_anomaly_detection: bool = True,
) -> tuple[TokenManager, ErrorHandler, RetryExecutor, SecurityAuditLogger]:
    """
    Create a complete security framework with all components.

    Args:
        storage_path: Path for secure storage
        secret_key: Secret key for encryption and signing
        application_name: Application identifier
        environment: Deployment environment
        enable_anomaly_detection: Enable security anomaly detection

    Returns:
        Tuple of (TokenManager, ErrorHandler, RetryExecutor, SecurityAuditLogger)
    """
    from pathlib import Path

    base_path = Path(storage_path)

    # Initialize components
    token_manager = TokenManager(
        secret_key=secret_key,
        storage_path=base_path / "tokens"
    )

    error_handler = ErrorHandler(enable_metrics=True)
    retry_executor = RetryExecutor()

    audit_logger = SecurityAuditLogger(
        storage_path=base_path / "audit_logs",
        encryption_key=secret_key,
        application_name=application_name,
        environment=environment,
        enable_anomaly_detection=enable_anomaly_detection,
    )

    return token_manager, error_handler, retry_executor, audit_logger


def get_hipaa_compliance_config() -> dict:
    """
    Get HIPAA compliance configuration settings.

    Returns:
        Dictionary with HIPAA compliance requirements
    """
    return {
        "audit_requirements": {
            "user_identification": True,
            "timestamp_required": True,
            "data_integrity": True,
            "encryption_required": True,
            "retention_period_days": HIPAA_RETENTION_DAYS,
        },
        "access_controls": {
            "minimum_authentication": True,
            "role_based_access": True,
            "audit_trail_required": True,
            "phi_protection": True,
        },
        "technical_safeguards": {
            "encryption_in_transit": True,
            "encryption_at_rest": True,
            "access_control_unique_user_identification": True,
            "automatic_logoff": True,
            "audit_logs_and_reporting": True,
        },
        "administrative_safeguards": {
            "security_officer_required": True,
            "workforce_training": True,
            "access_management": True,
            "incident_response": True,
        },
    }


# Security event helpers
async def log_security_event(  # type: ignore[no-untyped-def]
    audit_logger: SecurityAuditLogger,
    event_type: AuditEventType,
    description: str,
    **kwargs
) -> str:
    """
    Helper function to log security events with common patterns.

    Args:
        audit_logger: SecurityAuditLogger instance
        event_type: Type of audit event
        description: Event description
        **kwargs: Additional event parameters

    Returns:
        Event ID for correlation
    """
    return await audit_logger.log_event(
        event_type=event_type,
        description=description,
        **kwargs
    )


# Error handling helpers
async def handle_api_error(
    error_handler: ErrorHandler,
    exception: Exception,
    request_context: dict = None,  # type: ignore[assignment]
) -> DetailedError:
    """
    Helper function to handle API errors with context.

    Args:
        error_handler: ErrorHandler instance
        exception: Exception to handle
        request_context: Request context information

    Returns:
        DetailedError with classification and handling information
    """
    context = None
    if request_context:
        context = ErrorContext(**request_context)

    return await error_handler.handle_error(exception, context)


# Retry execution helpers
async def execute_with_security(
    retry_executor: RetryExecutor,
    audit_logger: SecurityAuditLogger,
    func: Callable,
    operation_name: str,
    user_id: str | None = None,
    **retry_kwargs: Any
) -> Any:
    """
    Execute function with retry logic and audit logging.

    Args:
        retry_executor: RetryExecutor instance
        audit_logger: SecurityAuditLogger instance
        func: Function to execute
        operation_name: Name of operation for auditing
        user_id: User performing operation
        **retry_kwargs: Additional retry configuration

    Returns:
        Execution result
    """
    # Log operation start
    start_event_id = await audit_logger.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        description=f"Starting operation: {operation_name}",
        user_id=user_id,
    )

    try:
        # Execute with retry logic
        result = await retry_executor.execute_with_retry(func, **retry_kwargs)

        # Log success
        await audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            description=f"Operation completed successfully: {operation_name}",
            outcome="success",
            user_id=user_id,
            additional_data={"start_event_id": start_event_id},
        )

        return result.result if result.success else None

    except Exception as e:
        # Log failure
        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description=f"Operation failed: {operation_name} - {str(e)}",
            outcome="failure",
            user_id=user_id,
            risk_level=AuditRiskLevel.MEDIUM,
            additional_data={"start_event_id": start_event_id, "error": str(e)},
        )
        raise
