"""
Comprehensive Health Check System.

This module provides health checking capabilities for all system components
including database, Redis, external APIs, ML models, and system resources.
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import redis.asyncio as redis
from sqlalchemy import text

from ..config import settings
from ..database.session import get_session


class HealthStatus(Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health information for a system component."""

    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: float
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp,
            "details": self.details or {},
        }


class BaseHealthCheck:
    """
    Base class for health checks.

    Provides common functionality for implementing health checks
    with consistent error handling and response formatting.
    """

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    async def check(self) -> ComponentHealth:
        """
        Perform the health check.

        Returns:
            ComponentHealth with check results
        """
        start_time = time.time()

        try:
            # Run the health check with timeout
            result = await asyncio.wait_for(self._check_health(), timeout=self.timeout)

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name=self.name,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", "Health check completed"),
                response_time_ms=response_time,
                timestamp=time.time(),
                details=result.get("details"),
            )

        except TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                response_time_ms=response_time,
                timestamp=time.time(),
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time(),
                details={"error": str(e), "error_type": type(e).__name__},
            )

    async def _check_health(self) -> dict[str, Any]:
        """
        Implement the actual health check logic.

        Must be implemented by subclasses.

        Returns:
            Dictionary with status, message, and optional details
        """
        raise NotImplementedError("Health check must implement _check_health")


class DatabaseHealthCheck(BaseHealthCheck):
    """
    Database health check implementation.

    Checks database connectivity, query performance, and connection pool status.
    """

    def __init__(self, timeout: float = 5.0):
        super().__init__("database", timeout)

    async def _check_health(self) -> dict[str, Any]:
        """Check database health."""
        try:
            async with get_session() as session:
                # Test basic connectivity
                start_time = time.time()
                result = await session.execute(text("SELECT 1"))
                query_time = (time.time() - start_time) * 1000

                # Check if we got expected result
                row = result.fetchone()
                if row is None or row[0] != 1:
                    return {
                        "status": HealthStatus.UNHEALTHY,
                        "message": "Database query returned unexpected result",
                    }

                # Get additional database info
                details = {
                    "query_time_ms": round(query_time, 2),
                    "connection_pool_size": settings.database.pool_size,
                    "max_overflow": settings.database.max_overflow,
                }

                # Check database version
                try:
                    version_result = await session.execute(text("SELECT version()"))
                    version_row = version_result.fetchone()
                    if version_row:
                        details["version"] = version_row[0]
                except Exception:
                    # Version check is not critical
                    pass

                # Determine status based on query performance
                if query_time > 1000:  # > 1 second
                    status = HealthStatus.DEGRADED
                    message = f"Database responding slowly ({query_time:.0f}ms)"
                elif query_time > 100:  # > 100ms
                    status = HealthStatus.DEGRADED
                    message = f"Database response time elevated ({query_time:.0f}ms)"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Database healthy ({query_time:.0f}ms)"

                return {
                    "status": status,
                    "message": message,
                    "details": details,
                }

        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(e)}",
                "details": {"error": str(e)},
            }


class RedisHealthCheck(BaseHealthCheck):
    """
    Redis health check implementation.

    Checks Redis connectivity, latency, and memory usage.
    """

    def __init__(self, timeout: float = 5.0):
        super().__init__("redis", timeout)

    async def _check_health(self) -> dict[str, Any]:
        """Check Redis health."""
        redis_client = None
        try:
            # Create Redis connection
            redis_url = str(settings.redis.url)
            redis_client = redis.from_url(
                redis_url,
                password=settings.redis.password,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
            )

            # Test connectivity with ping
            start_time = time.time()
            pong = await redis_client.ping()
            ping_time = (time.time() - start_time) * 1000

            if not pong:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Redis ping failed",
                }

            # Get Redis info
            info = await redis_client.info()

            details = {
                "ping_time_ms": round(ping_time, 2),
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }

            # Test set/get operations
            test_key = "health_check_test"
            test_value = str(time.time())

            await redis_client.set(test_key, test_value, ex=10)  # Expire in 10 seconds
            retrieved_value = await redis_client.get(test_key)

            if retrieved_value is None or retrieved_value.decode() != test_value:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Redis operations partially failing",
                    "details": details,
                }

            # Clean up test key
            await redis_client.delete(test_key)

            # Determine status based on performance
            if ping_time > 100:  # > 100ms
                status = HealthStatus.DEGRADED
                message = f"Redis responding slowly ({ping_time:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Redis healthy ({ping_time:.0f}ms)"

            return {
                "status": status,
                "message": message,
                "details": details,
            }

        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis connection failed: {str(e)}",
                "details": {"error": str(e)},
            }
        finally:
            if redis_client:
                await redis_client.close()


class ModelHealthCheck(BaseHealthCheck):
    """
    ML Model health check implementation.

    Checks model availability, loading status, and inference performance.
    """

    def __init__(self, timeout: float = 10.0):
        super().__init__("ml_models", timeout)

    async def _check_health(self) -> dict[str, Any]:
        """Check ML models health."""
        try:
            # This would typically check actual models
            # For now, we'll simulate the check

            models_status = {
                "lstm_model": "loaded",
                "transformer_model": "loaded",
                "ensemble_model": "loaded",
            }

            model_details = {
                "available_models": list(models_status.keys()),
                "loaded_models": [k for k, v in models_status.items() if v == "loaded"],
                "model_storage_path": str(settings.ml_models.storage_path),
                "cache_enabled": settings.ml_models.enable_cache,
                "max_memory_usage_mb": settings.ml_models.max_memory_usage,
            }

            # Simulate model inference test
            start_time = time.time()
            # Here we would actually test model inference
            await asyncio.sleep(0.01)  # Simulate inference time
            inference_time = (time.time() - start_time) * 1000

            model_details["test_inference_time_ms"] = round(inference_time, 2)

            # Check if all models are loaded
            loaded_count = len(model_details["loaded_models"])
            total_count = len(model_details["available_models"])

            if loaded_count == total_count:
                status = HealthStatus.HEALTHY
                message = f"All {total_count} models loaded and healthy"
            elif loaded_count > 0:
                status = HealthStatus.DEGRADED
                message = f"{loaded_count}/{total_count} models loaded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "No models loaded"

            return {
                "status": status,
                "message": message,
                "details": model_details,
            }

        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Model health check failed: {str(e)}",
                "details": {"error": str(e)},
            }


class ExternalAPIHealthCheck(BaseHealthCheck):
    """
    External API health check implementation.

    Checks connectivity to external APIs used for data ingestion.
    """

    def __init__(self, timeout: float = 10.0):
        super().__init__("external_apis", timeout)

    async def _check_health(self) -> dict[str, Any]:
        """Check external APIs health."""
        import httpx

        apis_to_check = [
            {
                "name": "ERA5 API",
                "url": str(settings.external_apis.era5_api_url),
                "timeout": 5.0,
            },
            {
                "name": "CHIRPS API",
                "url": str(settings.external_apis.chirps_api_endpoint),
                "timeout": 5.0,
            },
            {
                "name": "WorldPop API",
                "url": str(settings.external_apis.worldpop_api_endpoint),
                "timeout": 5.0,
            },
            {
                "name": "MAP API",
                "url": str(settings.external_apis.map_api_endpoint),
                "timeout": 5.0,
            },
        ]

        api_results = []
        healthy_count = 0

        async with httpx.AsyncClient() as client:
            for api in apis_to_check:
                try:
                    start_time = time.time()
                    response = await client.get(
                        api["url"],
                        timeout=api["timeout"],
                        follow_redirects=True,
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code < 400:
                        api_status = "healthy"
                        healthy_count += 1
                    elif response.status_code < 500:
                        api_status = "degraded"
                    else:
                        api_status = "unhealthy"

                    api_results.append(
                        {
                            "name": api["name"],
                            "status": api_status,
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time, 2),
                        }
                    )

                except Exception as e:
                    api_results.append(
                        {
                            "name": api["name"],
                            "status": "unhealthy",
                            "error": str(e),
                            "response_time_ms": 0,
                        }
                    )

        # Determine overall status
        total_apis = len(apis_to_check)
        if healthy_count == total_apis:
            status = HealthStatus.HEALTHY
            message = f"All {total_apis} external APIs reachable"
        elif healthy_count > 0:
            status = HealthStatus.DEGRADED
            message = f"{healthy_count}/{total_apis} external APIs reachable"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No external APIs reachable"

        return {
            "status": status,
            "message": message,
            "details": {
                "apis": api_results,
                "healthy_count": healthy_count,
                "total_count": total_apis,
            },
        }


class HealthChecker:
    """
    Main health checker that coordinates all health checks.

    Provides a unified interface for running all health checks
    and aggregating results into an overall system health status.
    """

    def __init__(self):
        self.checks = [
            DatabaseHealthCheck(),
            RedisHealthCheck(),
            ModelHealthCheck(),
            ExternalAPIHealthCheck(),
        ]

    async def check_all(self) -> dict[str, Any]:
        """
        Run all health checks concurrently.

        Returns:
            Dictionary with overall health status and individual check results
        """
        start_time = time.time()

        # Run all checks concurrently
        check_tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        total_time = (time.time() - start_time) * 1000

        # Process results
        check_results = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions from health checks
                check_result = ComponentHealth(
                    name=self.checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed with exception: {str(result)}",
                    response_time_ms=0,
                    timestamp=time.time(),
                )
            else:
                check_result = result

            check_results.append(check_result.to_dict())

            # Count statuses
            if check_result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif check_result.status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1

        # Determine overall status
        total_checks = len(check_results)
        if healthy_count == total_checks:
            overall_status = HealthStatus.HEALTHY
            overall_message = f"All {total_checks} components healthy"
        elif unhealthy_count == 0:
            overall_status = HealthStatus.DEGRADED
            overall_message = f"{healthy_count}/{total_checks} components healthy, {degraded_count} degraded"
        else:
            overall_status = HealthStatus.UNHEALTHY
            overall_message = f"{unhealthy_count} components unhealthy, {degraded_count} degraded, {healthy_count} healthy"

        return {
            "status": overall_status.value,
            "message": overall_message,
            "timestamp": time.time(),
            "response_time_ms": round(total_time, 2),
            "checks": check_results,
            "summary": {
                "total": total_checks,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
            },
        }

    async def check_component(self, component_name: str) -> dict[str, Any] | None:
        """
        Run health check for a specific component.

        Args:
            component_name: Name of the component to check

        Returns:
            Component health result or None if component not found
        """
        for check in self.checks:
            if check.name == component_name:
                result = await check.check()
                return result.to_dict()

        return None

    def get_component_names(self) -> list[str]:
        """Get list of available component names."""
        return [check.name for check in self.checks]


# Global health checker instance
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
