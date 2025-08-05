"""
Production Monitoring and Observability Package.

This package provides comprehensive monitoring, logging, and observability
tools for the malaria prediction system including:

- Structured JSON logging with correlation IDs
- Prometheus metrics collection
- OpenTelemetry distributed tracing
- Performance monitoring for ML models
- Health checks and alerting
- Production monitoring dashboards
"""

from .health import (
    ComponentHealth,
    DatabaseHealthCheck,
    HealthChecker,
    HealthStatus,
    ModelHealthCheck,
    RedisHealthCheck,
)
from .logger import (
    CorrelationIdFilter,
    JSONFormatter,
    RequestContextLogger,
    get_logger,
    setup_logging,
)
from .metrics import (
    APIMetrics,
    MetricsCollector,
    MLModelMetrics,
    PrometheusMetrics,
    SystemMetrics,
)
from .middleware import (
    HealthCheckMiddleware,
    PerformanceMonitoringMiddleware,
    PrometheusMiddleware,
    TracingMiddleware,
)
from .tracing import (
    TracingConfig,
    get_tracer,
    setup_tracing,
    trace_async_function,
    trace_function,
)

__all__ = [
    # Logging
    "get_logger",
    "setup_logging",
    "CorrelationIdFilter",
    "JSONFormatter",
    "RequestContextLogger",
    # Metrics
    "MetricsCollector",
    "PrometheusMetrics",
    "MLModelMetrics",
    "APIMetrics",
    "SystemMetrics",
    # Tracing
    "TracingConfig",
    "get_tracer",
    "setup_tracing",
    "trace_async_function",
    "trace_function",
    # Health Checks
    "HealthChecker",
    "HealthStatus",
    "ComponentHealth",
    "DatabaseHealthCheck",
    "RedisHealthCheck",
    "ModelHealthCheck",
    # Middleware
    "PrometheusMiddleware",
    "TracingMiddleware",
    "HealthCheckMiddleware",
    "PerformanceMonitoringMiddleware",
]
