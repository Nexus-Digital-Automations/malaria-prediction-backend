"""
OpenTelemetry Distributed Tracing System.

This module provides comprehensive distributed tracing capabilities for the
malaria prediction system using OpenTelemetry, including automatic instrumentation,
custom span creation, and integration with various backends.
"""

import functools
import inspect
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from ..config import settings


class TracingConfig:
    """
    Configuration for OpenTelemetry tracing setup.

    Manages tracing configuration including service information,
    sampling rates, exporters, and instrumentation settings.
    """

    def __init__(
        self,
        service_name: str = "malaria-prediction-api",
        service_version: str = "1.0.0",
        environment: str = None,
        jaeger_endpoint: str = "http://localhost:14268/api/traces",
        sampling_rate: float = 1.0,
        enable_console_export: bool = False,
        enable_jaeger_export: bool = True,
        enable_auto_instrumentation: bool = True,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment or settings.environment
        self.jaeger_endpoint = jaeger_endpoint
        self.sampling_rate = sampling_rate
        self.enable_console_export = enable_console_export
        self.enable_jaeger_export = enable_jaeger_export
        self.enable_auto_instrumentation = enable_auto_instrumentation

    def get_resource(self) -> Resource:
        """Create OpenTelemetry resource with service metadata."""
        resource_attributes = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        }

        return Resource.create(resource_attributes)


def setup_tracing(config: TracingConfig | None = None) -> TracerProvider:
    """
    Initialize OpenTelemetry tracing with comprehensive configuration.

    Args:
        config: Tracing configuration, uses defaults if None

    Returns:
        Configured TracerProvider instance
    """
    if not settings.monitoring.enable_tracing:
        return None

    # Use default config if none provided
    if config is None:
        config = TracingConfig()

    # Create resource
    resource = config.get_resource()

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure span processors and exporters
    span_processors = []

    # Console exporter for development
    if config.enable_console_export:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        span_processors.append(console_processor)

    # Jaeger exporter for production
    if config.enable_jaeger_export:
        try:
            jaeger_exporter = JaegerExporter(
                endpoint=config.jaeger_endpoint,
                collector_endpoint=config.jaeger_endpoint,
            )
            jaeger_processor = BatchSpanProcessor(jaeger_exporter)
            span_processors.append(jaeger_processor)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to setup Jaeger exporter: {e}")

    # Add span processors to tracer provider
    for processor in span_processors:
        tracer_provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Set up propagation
    # Note: Using default propagator instead of B3MultiFormat for compatibility
    # set_global_textmap(B3MultiFormat())

    # Setup metrics provider with Prometheus
    try:
        prometheus_reader = PrometheusMetricReader()
        MeterProvider(
            resource=resource,
            metric_readers=[prometheus_reader],
        )
        # Note: This would need proper metric provider setup
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to setup metrics provider: {e}")

    # Auto-instrumentation
    if config.enable_auto_instrumentation:
        setup_auto_instrumentation()

    return tracer_provider


def setup_auto_instrumentation():
    """
    Setup automatic instrumentation for common libraries.

    Automatically instruments FastAPI, AsyncPG, Redis, and other
    commonly used libraries in the malaria prediction system.
    """
    try:
        # FastAPI instrumentation
        FastAPIInstrumentor().instrument()

        # Database instrumentation
        AsyncPGInstrumentor().instrument()

        # Redis instrumentation
        RedisInstrumentor().instrument()

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Auto-instrumentation setup completed")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to setup auto-instrumentation: {e}")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance for creating spans.

    Args:
        name: Tracer name, typically the module name

    Returns:
        OpenTelemetry Tracer instance
    """
    return trace.get_tracer(name)


@contextmanager
def create_span(
    tracer: trace.Tracer,
    name: str,
    attributes: dict[str, Any] | None = None,
    links: list | None = None,
) -> Generator[trace.Span, None, None]:
    """
    Context manager for creating and managing spans.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name
        attributes: Optional span attributes
        links: Optional span links

    Yields:
        Active span instance
    """
    if not settings.monitoring.enable_tracing:
        yield None
        return

    with tracer.start_as_current_span(
        name=name,
        attributes=attributes or {},
        links=links or [],
    ) as span:
        try:
            yield span
        except Exception as e:
            if span:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


def trace_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Callable:
    """
    Decorator for automatically tracing function calls.

    Args:
        name: Custom span name, defaults to function name
        attributes: Additional span attributes
        record_exception: Whether to record exceptions in spans

    Returns:
        Decorated function with tracing
    """

    def decorator(func: Callable) -> Callable:
        if not settings.monitoring.enable_tracing:
            return func

        tracer = get_tracer(func.__module__)
        span_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            span_attributes = attributes.copy() if attributes else {}
            span_attributes.update(
                {
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                    "function.args_count": len(args),
                    "function.kwargs_count": len(kwargs),
                }
            )

            with create_span(tracer, span_name, span_attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    if span:
                        span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    if span and record_exception:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def trace_async_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Callable:
    """
    Decorator for automatically tracing async function calls.

    Args:
        name: Custom span name, defaults to function name
        attributes: Additional span attributes
        record_exception: Whether to record exceptions in spans

    Returns:
        Decorated async function with tracing
    """

    def decorator(func: Callable) -> Callable:
        if not settings.monitoring.enable_tracing:
            return func

        tracer = get_tracer(func.__module__)
        span_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_attributes = attributes.copy() if attributes else {}
            span_attributes.update(
                {
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                    "function.args_count": len(args),
                    "function.kwargs_count": len(kwargs),
                    "function.is_async": True,
                }
            )

            with create_span(tracer, span_name, span_attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    if span:
                        span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    if span and record_exception:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return async_wrapper

    return decorator


class MLModelTracer:
    """
    Specialized tracer for ML model operations.

    Provides specialized tracing for machine learning operations including
    model loading, prediction, training, and evaluation with ML-specific
    attributes and metrics.
    """

    def __init__(self, tracer: trace.Tracer | None = None):
        self.tracer = tracer or get_tracer(__name__)

    def trace_model_loading(
        self,
        model_name: str,
        model_version: str,
        model_type: str,
    ) -> contextmanager:
        """Trace model loading operations."""
        attributes = {
            "ml.model.name": model_name,
            "ml.model.version": model_version,
            "ml.model.type": model_type,
            "ml.operation": "load",
        }

        return create_span(
            self.tracer,
            f"ml.model.load.{model_name}",
            attributes,
        )

    def trace_prediction(
        self,
        model_name: str,
        model_version: str,
        input_features: int,
        batch_size: int = 1,
    ) -> contextmanager:
        """Trace model prediction operations."""
        attributes = {
            "ml.model.name": model_name,
            "ml.model.version": model_version,
            "ml.operation": "predict",
            "ml.prediction.input_features": input_features,
            "ml.prediction.batch_size": batch_size,
        }

        return create_span(
            self.tracer,
            f"ml.predict.{model_name}",
            attributes,
        )

    def trace_feature_extraction(
        self,
        data_source: str,
        feature_count: int,
        processing_type: str,
    ) -> contextmanager:
        """Trace feature extraction operations."""
        attributes = {
            "ml.feature_extraction.data_source": data_source,
            "ml.feature_extraction.feature_count": feature_count,
            "ml.feature_extraction.processing_type": processing_type,
            "ml.operation": "feature_extraction",
        }

        return create_span(
            self.tracer,
            f"ml.feature_extraction.{data_source}",
            attributes,
        )

    def add_prediction_metrics(
        self,
        span: trace.Span,
        confidence: float,
        prediction_value: float,
        processing_time_ms: float,
    ):
        """Add prediction-specific metrics to a span."""
        if not span:
            return

        span.set_attributes(
            {
                "ml.prediction.confidence": confidence,
                "ml.prediction.value": prediction_value,
                "ml.prediction.processing_time_ms": processing_time_ms,
            }
        )


class DatabaseTracer:
    """
    Specialized tracer for database operations.

    Provides database-specific tracing with query information,
    connection pooling metrics, and performance data.
    """

    def __init__(self, tracer: trace.Tracer | None = None):
        self.tracer = tracer or get_tracer(__name__)

    def trace_query(
        self,
        query_type: str,
        table_name: str = None,
        query_hash: str = None,
    ) -> contextmanager:
        """Trace database query operations."""
        attributes = {
            "db.operation": query_type,
            "db.system": "postgresql",
        }

        if table_name:
            attributes["db.sql.table"] = table_name
        if query_hash:
            attributes["db.statement_hash"] = query_hash

        return create_span(
            self.tracer,
            f"db.{query_type}",
            attributes,
        )

    def add_query_metrics(
        self,
        span: trace.Span,
        rows_affected: int,
        execution_time_ms: float,
        connection_pool_size: int = None,
    ):
        """Add query-specific metrics to a span."""
        if not span:
            return

        attributes = {
            "db.rows_affected": rows_affected,
            "db.execution_time_ms": execution_time_ms,
        }

        if connection_pool_size is not None:
            attributes["db.connection_pool_size"] = connection_pool_size

        span.set_attributes(attributes)


class APITracer:
    """
    Specialized tracer for API operations.

    Provides API-specific tracing with HTTP information,
    user context, and request/response metrics.
    """

    def __init__(self, tracer: trace.Tracer | None = None):
        self.tracer = tracer or get_tracer(__name__)

    def trace_api_request(
        self,
        method: str,
        endpoint: str,
        user_id: str = None,
        request_id: str = None,
    ) -> contextmanager:
        """Trace API request operations."""
        attributes = {
            "http.method": method,
            "http.route": endpoint,
            "http.scheme": "https",
        }

        if user_id:
            attributes["user.id"] = user_id
        if request_id:
            attributes["request.id"] = request_id

        return create_span(
            self.tracer,
            f"http.{method.lower()}.{endpoint}",
            attributes,
        )

    def add_request_metrics(
        self,
        span: trace.Span,
        status_code: int,
        response_size: int,
        processing_time_ms: float,
    ):
        """Add request-specific metrics to a span."""
        if not span:
            return

        span.set_attributes(
            {
                "http.status_code": status_code,
                "http.response.body.size": response_size,
                "http.processing_time_ms": processing_time_ms,
            }
        )


# Global tracer instances
_ml_tracer: MLModelTracer | None = None
_db_tracer: DatabaseTracer | None = None
_api_tracer: APITracer | None = None


def get_ml_tracer() -> MLModelTracer:
    """Get the global ML model tracer instance."""
    global _ml_tracer
    if _ml_tracer is None:
        _ml_tracer = MLModelTracer()
    return _ml_tracer


def get_db_tracer() -> DatabaseTracer:
    """Get the global database tracer instance."""
    global _db_tracer
    if _db_tracer is None:
        _db_tracer = DatabaseTracer()
    return _db_tracer


def get_api_tracer() -> APITracer:
    """Get the global API tracer instance."""
    global _api_tracer
    if _api_tracer is None:
        _api_tracer = APITracer()
    return _api_tracer


# Utility functions for common tracing patterns
def trace_ml_prediction(
    model_name: str,
    model_version: str = "1.0.0",
    record_metrics: bool = True,
):
    """
    Decorator for tracing ML prediction functions.

    Args:
        model_name: Name of the ML model
        model_version: Version of the ML model
        record_metrics: Whether to record prediction metrics
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ml_tracer = get_ml_tracer()

            # Determine input features count from function signature
            sig = inspect.signature(func)
            input_features = len(sig.parameters)

            with ml_tracer.trace_prediction(
                model_name, model_version, input_features
            ) as span:
                start_time = time.time()
                result = await func(*args, **kwargs)
                processing_time = (time.time() - start_time) * 1000

                if record_metrics and span and hasattr(result, "confidence"):
                    ml_tracer.add_prediction_metrics(
                        span,
                        result.confidence,
                        result.prediction,
                        processing_time,
                    )

                return result

        return wrapper

    return decorator


# Initialize tracing on module import if enabled
if settings.monitoring.enable_tracing:
    setup_tracing()
