"""
Structured Logging System with JSON Format and Correlation IDs.

This module provides comprehensive logging capabilities for production monitoring
including JSON structured logging, correlation ID tracking, request context,
and performance metrics integration.
"""

import json
import logging
import logging.handlers
import sys
import time
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path

from ..config import settings

# Context variables for request tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
operation_var: ContextVar[str | None] = ContextVar("operation", default=None)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation IDs and request context to log records.

    This filter extracts context variables and adds them to each log record,
    enabling distributed tracing and request correlation across the application.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation context to log record."""
        # Add correlation IDs
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.session_id = session_id_var.get()
        record.operation = operation_var.get()

        # Add timestamp information
        record.timestamp = datetime.utcnow().isoformat() + "Z"
        record.timestamp_ms = int(time.time() * 1000)

        # Add process/thread information
        record.process_name = record.processName
        record.thread_name = record.threadName

        return True


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON objects with consistent structure including
    correlation IDs, performance metrics, and contextual information.
    """

    def __init__(
        self,
        include_extra: bool = True,
        include_stack_info: bool = True,
        max_message_length: int = 10000,
    ):
        super().__init__()
        self.include_extra = include_extra
        self.include_stack_info = include_stack_info
        self.max_message_length = max_message_length

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_entry = {
            "timestamp": getattr(
                record, "timestamp", datetime.utcnow().isoformat() + "Z"
            ),
            "timestamp_ms": getattr(record, "timestamp_ms", int(time.time() * 1000)),
            "level": record.levelname,
            "logger": record.name,
            "message": self._truncate_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": {
                "pid": record.process,
                "name": getattr(record, "process_name", record.processName),
                "thread": {
                    "id": record.thread,
                    "name": getattr(record, "thread_name", record.threadName),
                },
            },
        }

        # Add correlation context
        correlation = {}
        if hasattr(record, "request_id") and record.request_id:
            correlation["request_id"] = record.request_id
        if hasattr(record, "user_id") and record.user_id:
            correlation["user_id"] = record.user_id
        if hasattr(record, "session_id") and record.session_id:
            correlation["session_id"] = record.session_id
        if hasattr(record, "operation") and record.operation:
            correlation["operation"] = record.operation

        if correlation:
            log_entry["correlation"] = correlation

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
                if self.include_stack_info
                else None,
            }

        # Add stack information for debugging
        if record.stack_info and self.include_stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Add extra fields if enabled
        if self.include_extra:
            extra_fields = {}
            # Get custom fields added to the record
            skip_fields = {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
                "timestamp",
                "timestamp_ms",
                "request_id",
                "user_id",
                "session_id",
                "operation",
                "process_name",
                "thread_name",
            }

            for key, value in record.__dict__.items():
                if key not in skip_fields and not key.startswith("_"):
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)

            if extra_fields:
                log_entry["extra"] = extra_fields

        return json.dumps(log_entry, ensure_ascii=False, separators=(",", ":"))

    def _truncate_message(self, message: str) -> str:
        """Truncate message if it exceeds maximum length."""
        if len(message) <= self.max_message_length:
            return message

        truncated = message[: self.max_message_length - 3] + "..."
        return truncated


class RequestContextLogger:
    """
    Context manager for adding request-specific logging context.

    Automatically sets correlation IDs and request context that will be
    included in all log messages within the context.
    """

    def __init__(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        operation: str | None = None,
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.operation = operation
        self.tokens: list[str] = []

    def __enter__(self):
        """Enter request context."""
        if self.request_id:
            self.tokens.append(request_id_var.set(self.request_id))
        if self.user_id:
            self.tokens.append(user_id_var.set(self.user_id))
        if self.session_id:
            self.tokens.append(session_id_var.set(self.session_id))
        if self.operation:
            self.tokens.append(operation_var.set(self.operation))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit request context."""
        # Reset context variables
        for token in reversed(self.tokens):
            token.var.set(token.old_value)
        self.tokens.clear()


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: str | Path | None = None,
    enable_console: bool = True,
    enable_file_rotation: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_syslog: bool = False,
    syslog_address: tuple = ("localhost", 514),
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json', 'structured', 'text')
        log_file: Path to log file (optional)
        enable_console: Whether to enable console logging
        enable_file_rotation: Whether to enable log file rotation
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        enable_syslog: Whether to enable syslog logging
        syslog_address: Syslog server address tuple
    """
    # Use configuration defaults if not provided
    log_level = log_level or settings.monitoring.log_level
    log_format = log_format or settings.monitoring.log_format

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()

    # Configure formatters based on format type
    if log_format == "json":
        formatter = JSONFormatter(
            include_extra=True, include_stack_info=settings.environment != "production"
        )
    elif log_format == "structured":
        formatter = logging.Formatter(
            fmt=("%(timestamp)s [%(levelname)s] %(name)s [%(request_id)s] %(message)s"),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:  # text format
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        if enable_file_rotation:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:
            file_handler = logging.FileHandler(filename=log_file, encoding="utf-8")

        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)

    # Syslog handler for production environments
    if enable_syslog:
        try:
            syslog_handler = logging.handlers.SysLogHandler(address=syslog_address)
            syslog_handler.setFormatter(formatter)
            syslog_handler.addFilter(correlation_filter)
            root_logger.addHandler(syslog_handler)
        except Exception as e:
            # Fall back to console logging if syslog fails
            logging.warning(f"Failed to setup syslog handler: {e}")

    # Configure third-party loggers to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    # Log setup completion
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "console_enabled": enable_console,
            "file_enabled": bool(log_file),
            "syslog_enabled": enable_syslog,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Performance logging utilities
class PerformanceLogger:
    """Utility class for logging performance metrics."""

    def __init__(self, logger: logging.Logger, operation: str) -> None:
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        """Start performance timing."""
        self.start_time = time.time()
        self.logger.info(
            f"Starting operation: {self.operation}",
            extra={"operation": self.operation, "event": "start"},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log performance results."""
        duration = time.time() - self.start_time

        if exc_type is None:
            self.logger.info(
                f"Completed operation: {self.operation}",
                extra={
                    "operation": self.operation,
                    "event": "complete",
                    "duration_ms": int(duration * 1000),
                    "duration_seconds": round(duration, 3),
                },
            )
        else:
            self.logger.error(
                f"Failed operation: {self.operation}",
                extra={
                    "operation": self.operation,
                    "event": "error",
                    "duration_ms": int(duration * 1000),
                    "duration_seconds": round(duration, 3),
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                },
                exc_info=True,
            )


def log_performance(operation: str):
    """
    Decorator for automatic performance logging.

    Args:
        operation: Name of the operation being timed
    """

    def decorator(func):
        if hasattr(func, "__aenter__"):  # Async function

            async def async_wrapper(*args, **kwargs):
                logger = get_logger(func.__module__)
                with PerformanceLogger(logger, operation):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:  # Sync function

            def sync_wrapper(*args, **kwargs):
                logger = get_logger(func.__module__)
                with PerformanceLogger(logger, operation):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator


# Initialize logging on module import if not already configured
if not logging.getLogger().handlers:
    setup_logging()
