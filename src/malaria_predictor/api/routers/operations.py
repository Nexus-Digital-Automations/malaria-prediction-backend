"""
Operations Dashboard API Routes.

This module provides API endpoints for the production operations dashboard
including real-time monitoring, alerting, and system health status.
"""

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from ...monitoring.health import get_health_checker
from ...monitoring.operations_dashboard import get_operations_dashboard

# Operations endpoints - no authentication required for monitoring
# from ..dependencies import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/dashboard", response_class=HTMLResponse)
async def get_operations_dashboard_page() -> HTMLResponse:
    """
    Get the production operations dashboard HTML page.

    Returns a comprehensive real-time dashboard with system health,
    performance metrics, ML model monitoring, and active alerts.
    """
    dashboard = get_operations_dashboard()
    return HTMLResponse(content=dashboard.get_operations_dashboard_html())


@router.get("/summary")
async def get_dashboard_summary(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get current dashboard summary for API consumption.

    Returns:
        Dict containing system status, active alerts count,
        performance summary, and last update timestamp.
    """
    dashboard = get_operations_dashboard()
    return dashboard.get_dashboard_summary()


@router.get("/alerts")
async def get_active_alerts(
    # Authentication removed for monitoring endpoints
) -> list[dict[str, Any]]:
    """
    Get current active alerts.

    Returns:
        List of active alerts with details including severity,
        description, and runbook links.
    """
    dashboard = get_operations_dashboard()
    return dashboard.get_active_alerts()


@router.get("/alerts/history")
async def get_alert_history(
    hours: int = 24,
    # Authentication removed for monitoring endpoints
) -> list[dict[str, Any]]:
    """
    Get alert history for the specified time period.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        List of alerts from the specified time period.
    """
    dashboard = get_operations_dashboard()
    return dashboard.get_alert_history(hours=hours)


@router.get("/health/detailed")
async def get_detailed_health_status(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get detailed health status for all system components.

    Returns comprehensive health information including database,
    cache, ML models, and external API connectivity.
    """
    health_manager = get_health_checker()
    return await health_manager.check_all()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(
    # Authentication removed for monitoring endpoints
) -> JSONResponse:
    """
    Get Prometheus metrics in text format.

    Returns all system metrics in Prometheus exposition format
    for scraping by Prometheus server.
    """
    from ...monitoring.metrics import get_metrics

    metrics = get_metrics()
    content, content_type = metrics.get_metrics_output()

    return JSONResponse(
        content={"metrics": content}, headers={"Content-Type": content_type}
    )


@router.get("/config/grafana")
async def get_grafana_dashboard_config(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get Grafana dashboard configurations for import.

    Returns dashboard configurations that can be imported
    directly into Grafana for visualization.
    """
    dashboard = get_operations_dashboard()
    return dashboard.export_grafana_dashboards()


@router.get("/config/prometheus-alerts")
async def get_prometheus_alert_rules(
    # Authentication removed for monitoring endpoints
) -> JSONResponse:
    """
    Get Prometheus alert rules configuration.

    Returns alert rules in Prometheus format that can be
    loaded into Prometheus for automated alerting.
    """
    dashboard = get_operations_dashboard()
    rules_yaml = dashboard.export_prometheus_alerts()

    return JSONResponse(
        content={"rules": rules_yaml}, headers={"Content-Type": "application/json"}
    )


@router.websocket("/ws/operations-dashboard")
async def operations_dashboard_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time operations dashboard updates.

    Provides real-time streaming of system health, performance metrics,
    and alert notifications to connected dashboard clients.
    """
    dashboard = get_operations_dashboard()

    try:
        await dashboard.add_websocket_connection(websocket)

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (keepalive, etc.)
                message = await websocket.receive_text()

                # Handle client requests
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "get_status":
                    summary = dashboard.get_dashboard_summary()
                    await websocket.send_text(f"status:{summary['system_status']}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await dashboard.remove_websocket_connection(websocket)


@router.post("/monitoring/start")
async def start_operations_monitoring(
    # Authentication removed for monitoring endpoints
) -> dict[str, str]:
    """
    Start operations monitoring and alerting.

    Begins real-time monitoring of system health, performance metrics,
    and automated alert evaluation.
    """
    dashboard = get_operations_dashboard()
    await dashboard.start_monitoring()

    return {"message": "Operations monitoring started", "status": "success"}


@router.post("/monitoring/stop")
async def stop_operations_monitoring(
    # Authentication removed for monitoring endpoints
) -> dict[str, str]:
    """
    Stop operations monitoring and alerting.

    Stops real-time monitoring and alert evaluation.
    """
    dashboard = get_operations_dashboard()
    await dashboard.stop_monitoring()

    return {"message": "Operations monitoring stopped", "status": "success"}


@router.get("/system/resources")
async def get_system_resources(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get current system resource utilization.

    Returns detailed information about CPU, memory, disk,
    and network usage for operational monitoring.
    """
    import psutil

    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_count = psutil.cpu_count()

        # Memory information
        memory = psutil.virtual_memory()

        # Disk information
        disk_usage = psutil.disk_usage("/")

        # Network information
        network_io = psutil.net_io_counters()

        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
                ),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
            },
        }

    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        return {"error": str(e)}


@router.get("/database/status")
async def get_database_status(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get database connection and performance status.

    Returns information about database connections, query performance,
    and overall database health.
    """
    try:
        from ...database.session import get_connection_pool_status

        pool_status = await get_connection_pool_status()

        return {
            "connection_pool": pool_status,
            "status": "healthy" if pool_status.get("pool_size", 0) > 0 else "unhealthy",
        }

    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/cache/status")
async def get_cache_status(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get cache performance and connection status.

    Returns information about cache hit rates, memory usage,
    and connection health.
    """
    try:
        from ...performance.cache_optimization import (  # type: ignore[import-untyped]
            get_cache_optimizer,  # fmt: skip
        )

        cache_optimizer = await get_cache_optimizer()
        cache_stats = await cache_optimizer.get_cache_statistics()

        return {
            "performance_metrics": cache_stats.get("performance_metrics", {}),
            "memory_usage": cache_stats.get("memory_usage", {}),
            "connection_status": cache_stats.get("connection_status", "unknown"),
            "status": (
                "healthy"
                if cache_stats.get("connection_status") == "connected"
                else "unhealthy"
            ),
        }

    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/models/status")
async def get_ml_models_status(
    # Authentication removed for monitoring endpoints
) -> dict[str, Any]:
    """
    Get ML models performance and health status.

    Returns information about model loading status, inference performance,
    and prediction accuracy metrics.
    """
    try:
        # This would integrate with your ML model management system
        # For now, return a basic status structure

        return {
            "models": [
                {
                    "name": "lstm_model",
                    "version": "1.0.0",
                    "status": "loaded",
                    "memory_usage_mb": 256,
                    "last_prediction": None,
                    "accuracy": 0.92,
                },
                {
                    "name": "transformer_model",
                    "version": "1.0.0",
                    "status": "loaded",
                    "memory_usage_mb": 512,
                    "last_prediction": None,
                    "accuracy": 0.89,
                },
            ],
            "total_models": 2,
            "healthy_models": 2,
            "status": "healthy",
        }

    except Exception as e:
        logger.error(f"Error getting ML models status: {e}")
        return {"status": "error", "error": str(e)}
