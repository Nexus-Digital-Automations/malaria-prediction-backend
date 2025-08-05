"""
Monitoring Middleware for FastAPI Integration.

This module provides comprehensive middleware for integrating all monitoring
components including metrics collection, distributed tracing, health checks,
and performance monitoring with FastAPI applications.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from .health import get_health_checker
from .logger import RequestContextLogger, get_logger
from .metrics import get_metrics
from .tracing import get_api_tracer


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Prometheus metrics collection.

    Automatically collects API metrics including request counts,
    response times, error rates, and payload sizes.
    """

    def __init__(
        self,
        app,
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.metrics = get_metrics()
        self.include_paths = include_paths or []
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.logger = get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Collect metrics for HTTP requests."""
        # Skip excluded paths
        if self._should_skip_path(request.url.path):
            return await call_next(request)

        start_time = time.time()
        method = request.method
        endpoint = self._extract_endpoint(request)

        # Get request size
        request_size = 0
        if hasattr(request, "body"):
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except Exception:
                request_size = 0

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            duration = time.time() - start_time
            status_code = response.status_code

            # Get response size
            response_size = 0
            if hasattr(response, "body"):
                try:
                    if hasattr(response.body, "__len__"):
                        response_size = len(response.body)
                    elif hasattr(response, "content"):
                        response_size = len(response.content)
                except Exception:
                    response_size = 0

            # Record metrics
            self.metrics.api_metrics.record_request(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                request_size=request_size,
                response_size=response_size,
            )

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time

            self.metrics.api_metrics.record_request(
                method=method,
                endpoint=endpoint,
                status_code=500,
                duration=duration,
                request_size=request_size,
                response_size=0,
            )

            self.metrics.api_metrics.record_error(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__,
            )

            self.logger.error(f"Request failed: {method} {endpoint}", exc_info=True)
            raise

    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped for metrics collection."""
        if self.include_paths:
            return not any(included in path for included in self.include_paths)

        return any(excluded in path for excluded in self.exclude_paths)

    def _extract_endpoint(self, request: Request) -> str:
        """Extract normalized endpoint from request."""
        path = request.url.path

        # Normalize path parameters
        if hasattr(request, "path_info"):
            return request.path_info

        # Simple normalization for common patterns
        # In production, you might want more sophisticated path normalization
        return path


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for OpenTelemetry distributed tracing.

    Automatically creates spans for HTTP requests with comprehensive
    attributes and context propagation.
    """

    def __init__(self, app):
        super().__init__(app)
        self.tracer = get_api_tracer()
        self.logger = get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Create tracing spans for HTTP requests."""
        method = request.method
        endpoint = request.url.path

        # Extract request ID if available
        request_id = getattr(request.state, "request_id", None)
        user_id = getattr(request.state, "user_id", None)

        with self.tracer.trace_api_request(
            method, endpoint, user_id, request_id
        ) as span:
            start_time = time.time()

            try:
                response = await call_next(request)
                processing_time = (time.time() - start_time) * 1000

                # Add response metrics to span
                response_size = 0
                if hasattr(response, "body") and response.body:
                    try:
                        response_size = len(response.body)
                    except Exception:
                        pass

                self.tracer.add_request_metrics(
                    span,
                    response.status_code,
                    response_size,
                    processing_time,
                )

                return response

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000

                # Record error in span
                if span:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                self.logger.error(
                    f"Request failed in tracing middleware: {method} {endpoint}",
                    exc_info=True,
                )
                raise


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware for health check endpoints.

    Provides comprehensive health check endpoints with detailed
    component status and metrics.
    """

    def __init__(self, app, health_endpoint: str = "/health"):
        super().__init__(app)
        self.health_endpoint = health_endpoint
        self.health_checker = get_health_checker()
        self.logger = get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle health check requests."""
        path = request.url.path

        # Handle health check endpoints
        if path == self.health_endpoint:
            return await self._handle_health_check(request)
        elif path == f"{self.health_endpoint}/detailed":
            return await self._handle_detailed_health_check(request)
        elif path.startswith(f"{self.health_endpoint}/component/"):
            component_name = path.split("/")[-1]
            return await self._handle_component_health_check(component_name)

        return await call_next(request)

    async def _handle_health_check(self, request: Request) -> JSONResponse:
        """Handle basic health check."""
        try:
            health_status = await self.health_checker.check_all()

            # Return simplified response for basic health check
            status_code = 200 if health_status["status"] == "healthy" else 503

            simple_response = {
                "status": health_status["status"],
                "message": health_status["message"],
                "timestamp": health_status["timestamp"],
            }

            return JSONResponse(
                content=simple_response,
                status_code=status_code,
            )

        except Exception as e:
            self.logger.error("Health check failed", exc_info=True)
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "message": f"Health check error: {str(e)}",
                    "timestamp": time.time(),
                },
                status_code=503,
            )

    async def _handle_detailed_health_check(self, request: Request) -> JSONResponse:
        """Handle detailed health check with all component information."""
        try:
            health_status = await self.health_checker.check_all()
            status_code = 200 if health_status["status"] == "healthy" else 503

            return JSONResponse(
                content=health_status,
                status_code=status_code,
            )

        except Exception as e:
            self.logger.error("Detailed health check failed", exc_info=True)
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "message": f"Health check error: {str(e)}",
                    "timestamp": time.time(),
                    "checks": [],
                    "summary": {
                        "total": 0,
                        "healthy": 0,
                        "degraded": 0,
                        "unhealthy": 0,
                    },
                },
                status_code=503,
            )

    async def _handle_component_health_check(self, component_name: str) -> JSONResponse:
        """Handle health check for specific component."""
        try:
            result = await self.health_checker.check_component(component_name)

            if result is None:
                return JSONResponse(
                    content={
                        "error": f"Component '{component_name}' not found",
                        "available_components": self.health_checker.get_component_names(),
                    },
                    status_code=404,
                )

            status_code = 200 if result["status"] == "healthy" else 503
            return JSONResponse(content=result, status_code=status_code)

        except Exception as e:
            self.logger.error(
                f"Component health check failed for {component_name}", exc_info=True
            )
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "message": f"Health check error: {str(e)}",
                    "timestamp": time.time(),
                },
                status_code=503,
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive performance monitoring.

    Tracks request performance, identifies slow requests,
    and provides detailed performance analytics.
    """

    def __init__(
        self,
        app,
        slow_request_threshold: float = 1.0,  # seconds
        log_slow_requests: bool = True,
        track_request_sizes: bool = True,
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.log_slow_requests = log_slow_requests
        self.track_request_sizes = track_request_sizes
        self.logger = get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Monitor request performance."""
        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        # Track request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Track request size if enabled
        request_size = 0
        if self.track_request_sizes:
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except Exception:
                request_size = 0

        # Use request context logger
        with RequestContextLogger(
            request_id=request_id,
            operation=f"{method} {endpoint}",
        ):
            try:
                # Process request
                response = await call_next(request)

                # Calculate performance metrics
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Track response size
                response_size = 0
                if self.track_request_sizes and hasattr(response, "body"):
                    try:
                        if hasattr(response.body, "__len__"):
                            response_size = len(response.body)
                    except Exception:
                        pass

                # Add performance headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time-ms"] = str(round(duration_ms, 2))

                # Log request completion
                self.logger.info(
                    f"Request completed: {method} {endpoint}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "request_size": request_size,
                        "response_size": response_size,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                    },
                )

                # Log slow requests
                if self.log_slow_requests and duration > self.slow_request_threshold:
                    self.logger.warning(
                        f"Slow request detected: {method} {endpoint} took {duration:.2f}s",
                        extra={
                            "request_id": request_id,
                            "duration_seconds": duration,
                            "threshold_seconds": self.slow_request_threshold,
                            "slow_request": True,
                        },
                    )

                return response

            except Exception as e:
                # Calculate duration for failed requests
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Log error with context
                self.logger.error(
                    f"Request failed: {method} {endpoint}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "endpoint": endpoint,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                    },
                    exc_info=True,
                )

                raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxy headers."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client
        return request.client.host if request.client else "unknown"


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Unified monitoring middleware that combines all monitoring components.

    Provides a single middleware that integrates metrics collection,
    distributed tracing, health checks, and performance monitoring.
    """

    def __init__(
        self,
        app,
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        enable_health_checks: bool = True,
        enable_performance_monitoring: bool = True,
        health_endpoint: str = "/health",
        metrics_endpoint: str = "/metrics",
    ):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        self.enable_tracing = enable_tracing
        self.enable_health_checks = enable_health_checks
        self.enable_performance_monitoring = enable_performance_monitoring
        self.health_endpoint = health_endpoint
        self.metrics_endpoint = metrics_endpoint

        # Initialize components
        if enable_metrics:
            self.metrics = get_metrics()
        if enable_tracing:
            self.tracer = get_api_tracer()
        if enable_health_checks:
            self.health_checker = get_health_checker()

        self.logger = get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Unified monitoring dispatch."""
        path = request.url.path

        # Handle metrics endpoint
        if path == self.metrics_endpoint and self.enable_metrics:
            return await self._handle_metrics(request)

        # Handle health check endpoints
        if self.enable_health_checks and path.startswith(self.health_endpoint):
            return await self._handle_health_endpoints(request, call_next)

        # Apply monitoring to regular requests
        return await self._monitor_request(request, call_next)

    async def _handle_metrics(self, request: Request) -> Response:
        """Handle Prometheus metrics endpoint."""
        try:
            accept_header = request.headers.get("accept", "")
            content, content_type = self.metrics.get_metrics_output(accept_header)

            return Response(
                content=content,
                media_type=content_type,
            )
        except Exception as e:
            self.logger.error("Failed to generate metrics", exc_info=True)
            return Response(
                content=f"Error generating metrics: {str(e)}",
                status_code=500,
                media_type="text/plain",
            )

    async def _handle_health_endpoints(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle health check endpoints."""
        # Delegate to health check middleware logic
        health_middleware = HealthCheckMiddleware(None, self.health_endpoint)
        return await health_middleware.dispatch(request, call_next)

    async def _monitor_request(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Apply comprehensive monitoring to request."""
        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start tracing context if enabled
        tracing_context = None
        if self.enable_tracing:
            tracing_context = self.tracer.trace_api_request(
                method, endpoint, request_id=request_id
            )
            span = tracing_context.__enter__()

        # Start request context logging
        with RequestContextLogger(
            request_id=request_id, operation=f"{method} {endpoint}"
        ):
            try:
                # Process request
                response = await call_next(request)

                # Calculate metrics
                duration = time.time() - start_time

                # Collect metrics if enabled
                if self.enable_metrics:
                    self.metrics.api_metrics.record_request(
                        method=method,
                        endpoint=endpoint,
                        status_code=response.status_code,
                        duration=duration,
                    )

                # Add tracing metrics if enabled
                if self.enable_tracing and span:
                    processing_time = duration * 1000
                    response_size = getattr(response, "content_length", 0) or 0

                    self.tracer.add_request_metrics(
                        span,
                        response.status_code,
                        response_size,
                        processing_time,
                    )

                # Add monitoring headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time-ms"] = str(round(duration * 1000, 2))

                return response

            except Exception as e:
                duration = time.time() - start_time

                # Record error metrics if enabled
                if self.enable_metrics:
                    self.metrics.api_metrics.record_error(
                        method, endpoint, type(e).__name__
                    )

                # Record tracing error if enabled
                if self.enable_tracing and span:
                    span.record_exception(e)

                self.logger.error(f"Request failed: {method} {endpoint}", exc_info=True)
                raise

            finally:
                # Close tracing context if enabled
                if self.enable_tracing and tracing_context:
                    tracing_context.__exit__(None, None, None)
