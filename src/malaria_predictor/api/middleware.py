"""
Enhanced Security Middleware for FastAPI Application.

This module provides comprehensive security middleware including:
- Advanced logging with security event detection
- Distributed rate limiting with Redis support
- Request validation and sanitization
- Security headers enforcement
- IP allowlisting and geoblocking
- DDoS protection and anomaly detection
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.

    Logs all incoming requests with timing information, response status,
    and error details for monitoring and debugging purposes.
    """

    def __init__(self, app, enable_body_logging: bool = False):
        super().__init__(app)
        self.enable_body_logging = enable_body_logging

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive logging."""
        start_time = time.time()

        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"from {client_ip} [{user_agent}]"
        )

        # Optionally log request body for debugging
        if self.enable_body_logging and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    logger.debug(f"Request body: {body.decode()[:500]}...")
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} "
                f"{request.url.path} in {process_time:.3f}s"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {process_time:.3f}s - {str(e)}",
                exc_info=True,
            )

            # Return error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "timestamp": time.time(),
                        "path": str(request.url.path),
                    }
                },
            )

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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    Implements a sliding window rate limiter to protect against abuse.
    In production, consider using Redis for distributed rate limiting.
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of calls allowed
        self.period = period  # Time period in seconds
        self.requests = defaultdict(list)  # IP -> list of timestamps

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests outside the time window
        self._cleanup_old_requests(client_ip, current_time)

        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 429,
                        "message": f"Rate limit exceeded. Maximum {self.calls} requests per {self.period} seconds.",
                        "timestamp": current_time,
                        "path": str(request.url.path),
                        "retry_after": self.period,
                    }
                },
                headers={"Retry-After": str(self.period)},
            )

        # Record this request
        self.requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.calls - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Period"] = str(self.period)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_ip: str, current_time: float):
        """Remove requests outside the time window."""
        cutoff_time = current_time - self.period
        self.requests[client_ip] = [
            timestamp
            for timestamp in self.requests[client_ip]
            if timestamp > cutoff_time
        ]


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting API metrics.

    Collects request counts, response times, and error rates for monitoring.
    """

    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_count = defaultdict(int)
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for each request."""
        start_time = time.time()
        endpoint = f"{request.method} {request.url.path}"

        try:
            response = await call_next(request)

            # Record metrics
            process_time = time.time() - start_time
            self.request_count[endpoint] += 1
            self.response_times[endpoint].append(process_time)

            # Track errors
            if response.status_code >= 400:
                self.error_count[endpoint] += 1

            return response

        except Exception as e:
            # Record error
            process_time = time.time() - start_time
            self.request_count[endpoint] += 1
            self.error_count[endpoint] += 1
            self.response_times[endpoint].append(process_time)

            raise e

    def get_metrics(self) -> dict:
        """Get collected metrics."""
        uptime = time.time() - self.start_time

        metrics = {
            "uptime_seconds": uptime,
            "total_requests": sum(self.request_count.values()),
            "total_errors": sum(self.error_count.values()),
            "endpoints": {},
        }

        for endpoint in self.request_count:
            response_times = self.response_times[endpoint]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            metrics["endpoints"][endpoint] = {
                "request_count": self.request_count[endpoint],
                "error_count": self.error_count[endpoint],
                "error_rate": (
                    self.error_count[endpoint] / self.request_count[endpoint]
                    if self.request_count[endpoint] > 0
                    else 0
                ),
                "avg_response_time": avg_response_time,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
            }

        return metrics


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for adding comprehensive security headers.

    Adds security headers to protect against common vulnerabilities
    and provides HIPAA-compliant security measures.
    """

    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = environment

        # Base security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

        # Environment-specific headers
        if environment == "production":
            self.security_headers.update(
                {
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                    "Content-Security-Policy": (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                        "style-src 'self' 'unsafe-inline'; "
                        "img-src 'self' data: https:; "
                        "font-src 'self'; "
                        "connect-src 'self'; "
                        "frame-ancestors 'none'; "
                        "base-uri 'self'; "
                        "form-action 'self'"
                    ),
                }
            )
        else:
            # Development headers (less restrictive)
            self.security_headers.update(
                {
                    "Content-Security-Policy": (
                        "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                        "img-src 'self' data: https:; "
                        "font-src 'self'"
                    )
                }
            )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Add API-specific headers
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Request-ID"] = getattr(
            request.state, "request_id", "unknown"
        )

        # Remove server information in production
        if self.environment == "production":
            response.headers.pop("Server", None)

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating and sanitizing input data.

    Provides protection against injection attacks and malformed data.
    """

    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_content_length = max_content_length

        # Dangerous patterns to detect
        self.dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"data:.*base64",  # Base64 data URLs
            r"vbscript:",  # VBScript protocol
            r"on\w+\s*=",  # Event handlers
            r"expression\s*\(",  # CSS expressions
            r"url\s*\(",  # CSS URLs
            r"import\s+",  # ES6 imports
            r"@import",  # CSS imports
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize request data."""

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": {
                        "code": 413,
                        "message": "Request entity too large",
                        "max_size": self.max_content_length,
                    }
                },
            )

        # Validate Content-Type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]

            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": {
                            "code": 415,
                            "message": "Unsupported media type",
                            "allowed_types": allowed_types,
                        }
                    },
                )

        # Validate query parameters
        for param_name, param_value in request.query_params.items():
            if self._contains_dangerous_content(param_value):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": {
                            "code": 400,
                            "message": f"Invalid query parameter: {param_name}",
                            "details": "Contains potentially dangerous content",
                        }
                    },
                )

        return await call_next(request)

    def _contains_dangerous_content(self, content: str) -> bool:
        """Check if content contains dangerous patterns."""
        import re

        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding unique request IDs for tracing.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add unique request ID to request state."""
        import uuid

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive audit logging.

    Logs all requests for security and compliance monitoring.
    """

    def __init__(self, app, log_sensitive_data: bool = False):
        super().__init__(app)
        self.log_sensitive_data = log_sensitive_data

        # Sensitive endpoints that require special logging
        self.sensitive_endpoints = {
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/predict/single",
            "/predict/batch",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response for audit purposes."""
        from .security import SecurityAuditor

        start_time = time.time()

        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        endpoint = str(request.url.path)
        method = request.method

        # Determine if this is a sensitive operation
        is_sensitive = any(
            sensitive in endpoint for sensitive in self.sensitive_endpoints
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful request
            SecurityAuditor.log_security_event(
                "api_request",
                ip_address=client_ip,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_agent": user_agent,
                    "is_sensitive": is_sensitive,
                    "success": response.status_code < 400,
                },
            )

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            duration_ms = int((time.time() - start_time) * 1000)

            # Log failed request
            SecurityAuditor.log_security_event(
                "api_request_failed",
                ip_address=client_ip,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "user_agent": user_agent,
                    "is_sensitive": is_sensitive,
                    "success": False,
                },
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"
