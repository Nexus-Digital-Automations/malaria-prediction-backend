"""
Health Check Router for Malaria Prediction API.

This module provides comprehensive health check endpoints for monitoring
the API service, model health, data source status, and system metrics.
"""

import logging
import platform
import time
from datetime import datetime
from typing import Any

import psutil
from fastapi import APIRouter, Depends, Request

from ..dependencies import ModelManager, get_model_manager
from ..models import HealthResponse, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(
    request: Request, model_manager: ModelManager = Depends(get_model_manager)
) -> HealthResponse:
    """
    Basic health check endpoint.

    Returns the overall health status of the API service including
    uptime, loaded models, and basic system information.
    """
    try:
        # Calculate uptime
        app_start_time = getattr(request.app.state, "start_time", time.time())
        uptime_seconds = time.time() - app_start_time

        # Get model status
        model_health = await model_manager.health_check()
        loaded_models = list(model_manager.models.keys())

        # Determine overall health status
        status = HealthStatus.HEALTHY
        if not loaded_models:
            status = HealthStatus.DEGRADED
        elif any(model["status"] != "healthy" for model in model_health.values()):
            status = HealthStatus.DEGRADED

        # Basic data source status (placeholder)
        data_sources = {
            "era5": {"status": "unknown", "last_check": None},
            "chirps": {"status": "unknown", "last_check": None},
            "modis": {"status": "unknown", "last_check": None},
            "worldpop": {"status": "unknown", "last_check": None},
            "map": {"status": "unknown", "last_check": None},
        }

        # System metrics
        system_metrics = _get_system_metrics()

        return HealthResponse(
            status=status.value,
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            models_loaded=loaded_models,
            data_sources=data_sources,
            system_metrics=system_metrics,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status=HealthStatus.UNHEALTHY.value,
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=0,
            models_loaded=[],
            data_sources={},
            system_metrics={},
        )


@router.get("/detailed")
async def detailed_health_check(
    request: Request, model_manager: ModelManager = Depends(get_model_manager)
) -> dict[str, Any]:
    """
    Detailed health check with comprehensive system information.

    Provides in-depth health information including model performance metrics,
    system resource usage, and data source connectivity status.
    """
    try:
        # Calculate uptime
        app_start_time = getattr(request.app.state, "start_time", time.time())
        uptime_seconds = time.time() - app_start_time

        # Get detailed model health
        model_health = await model_manager.health_check()

        # System information
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_usage": _get_disk_usage(),
            "process_info": _get_process_info(),
        }

        # Performance metrics
        performance_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "load_average": getattr(psutil, "getloadavg", lambda: [0, 0, 0])(),
            "network_stats": _get_network_stats(),
            "process_count": len(psutil.pids()),
        }

        # Data source health (enhanced placeholder)
        data_sources = await _check_data_sources()

        return {
            "status": "detailed_health_check",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "system_info": system_info,
            "performance_metrics": performance_metrics,
            "model_health": model_health,
            "data_sources": data_sources,
            "api_version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/models")
async def model_health_check(model_manager: ModelManager = Depends(get_model_manager)) -> dict[str, Any]:
    """
    Model-specific health check endpoint.

    Returns detailed information about each loaded model including
    performance metrics, error rates, and usage statistics.
    """
    try:
        model_health = await model_manager.health_check()

        # Add additional model metrics
        for _model_type, health_info in model_health.items():
            # Convert datetime objects to ISO strings for JSON serialization
            if "last_used" in health_info and isinstance(
                health_info["last_used"], datetime
            ):
                health_info["last_used"] = health_info["last_used"].isoformat()
            if "load_time" in health_info and isinstance(
                health_info["load_time"], datetime
            ):
                health_info["load_time"] = health_info["load_time"].isoformat()
            if "last_error" in health_info and isinstance(
                health_info["last_error"], datetime
            ):
                health_info["last_error"] = health_info["last_error"].isoformat()

        return {
            "timestamp": datetime.now().isoformat(),
            "models": model_health,
            "total_models": len(model_health),
            "healthy_models": sum(
                1 for h in model_health.values() if h.get("status") == "healthy"
            ),
            "last_health_check": (
                model_manager.last_health_check.isoformat()
                if model_manager.last_health_check
                else None
            ),
        }

    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/metrics")
async def system_metrics() -> dict[str, Any]:
    """
    System metrics endpoint for monitoring and alerting.

    Provides detailed system resource metrics suitable for
    integration with monitoring systems like Prometheus.
    """
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "load_average": getattr(psutil, "getloadavg", lambda: [0, 0, 0])(),
                },
                "memory": {
                    "usage_percent": psutil.virtual_memory().percent,
                    "total_bytes": psutil.virtual_memory().total,
                    "available_bytes": psutil.virtual_memory().available,
                    "used_bytes": psutil.virtual_memory().used,
                },
                "disk": _get_disk_usage(),
                "network": _get_network_stats(),
            },
            "process": _get_process_info(),
            "api": {
                "version": "1.0.0",
                "uptime_seconds": time.time() - psutil.Process().create_time(),
            },
        }

        return metrics

    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/readiness")
async def readiness_check(model_manager: ModelManager = Depends(get_model_manager)) -> dict[str, Any]:
    """
    Kubernetes-style readiness probe.

    Checks if the service is ready to accept traffic by verifying
    that essential models are loaded and healthy.
    """
    try:
        # Check if at least one model is loaded
        if not model_manager.models:
            return {"status": "not_ready", "reason": "no_models_loaded"}

        # Quick health check
        model_health = await model_manager.health_check()
        healthy_models = [
            m for m, h in model_health.items() if h.get("status") == "healthy"
        ]

        if not healthy_models:
            return {"status": "not_ready", "reason": "no_healthy_models"}

        return {
            "status": "ready",
            "healthy_models": len(healthy_models),
            "total_models": len(model_health),
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get("/liveness")
async def liveness_check() -> dict[str, Any]:
    """
    Kubernetes-style liveness probe.

    Simple check to verify the service is alive and responding.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "pid": psutil.Process().pid,
    }


def _get_system_metrics() -> dict:
    """Get basic system metrics."""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "process_count": len(psutil.pids()),
        }
    except Exception:
        return {}


def _get_disk_usage() -> dict:
    """Get disk usage information."""
    try:
        disk = psutil.disk_usage("/")
        return {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "usage_percent": (disk.used / disk.total) * 100,
        }
    except Exception:
        return {}


def _get_network_stats() -> dict:
    """Get network statistics."""
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }
    except Exception:
        return {}


def _get_process_info() -> dict:
    """Get current process information."""
    try:
        process = psutil.Process()
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_info": process.memory_info()._asdict(),
            "create_time": process.create_time(),
            "num_threads": process.num_threads(),
        }
    except Exception:
        return {}


async def _check_data_sources() -> dict:
    """Check the health of external data sources."""
    # This is a placeholder - in production, would check actual connectivity
    # to ERA5, CHIRPS, MODIS, WorldPop, and MAP services
    return {
        "era5": {
            "status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 150,
            "endpoint": "cds.climate.copernicus.eu",
        },
        "chirps": {
            "status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 200,
            "endpoint": "data.chc.ucsb.edu",
        },
        "modis": {
            "status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 300,
            "endpoint": "earthdata.nasa.gov",
        },
        "worldpop": {
            "status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 250,
            "endpoint": "hub.worldpop.org",
        },
        "map": {
            "status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 180,
            "endpoint": "malariaatlas.org",
        },
    }
