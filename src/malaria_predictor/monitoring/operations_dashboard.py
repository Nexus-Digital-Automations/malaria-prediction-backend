"""
Production Operations Dashboard Manager.

This module provides a comprehensive production operations dashboard that integrates
all monitoring components for the malaria prediction system including system health,
ML model performance, API metrics, and operational alerting.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from .dashboards import get_dashboard_config
from .health import HealthChecker
from .metrics import get_metrics

logger = logging.getLogger(__name__)


class OperationsDashboardManager:
    """
    Production Operations Dashboard Manager.

    Provides comprehensive operational visibility with real-time monitoring,
    alerting, and integration with operational procedures.
    """

    def __init__(self) -> None:
        self.config_path = Path(__file__).parent / "operations_dashboard_config.json"
        self.dashboard_config = get_dashboard_config()
        self.metrics = get_metrics()
        self.health_manager = HealthChecker()

        # Real-time connections
        self.websocket_connections: set[Any] = set()

        # Dashboard state
        self.dashboard_state: dict[str, Any] = {
            "system_status": "healthy",
            "active_alerts": [],
            "performance_summary": {},
            "last_update": None,
        }

        # Alert state management
        self.active_alerts: dict[str, Any] = {}
        self.alert_history: list[dict[str, Any]] = []

        # Monitoring task
        self.monitoring_task: asyncio.Task[None] | None = None
        self.monitoring_active = False

    def load_operations_config(self) -> dict[str, Any]:
        """Load the enhanced operations dashboard configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(
                "Operations dashboard config not found, using default configuration"
            )
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default operations dashboard configuration."""
        return {
            "version": "1.0.0",
            "title": "Malaria Prediction System - Production Operations Dashboard",
            "dashboards": [],
            "alerts": [],
        }

    async def start_monitoring(self) -> None:
        """Start real-time operations monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Operations dashboard monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop operations monitoring."""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Operations dashboard monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for operations dashboard."""
        while self.monitoring_active:
            try:
                # Update dashboard state
                await self._update_dashboard_state()

                # Check for alerts
                await self._check_operational_alerts()

                # Broadcast updates to connected clients
                await self._broadcast_dashboard_update()

                # Wait before next update
                await asyncio.sleep(30)  # 30-second update interval

            except Exception as e:
                logger.error(f"Operations monitoring loop error: {e}")
                await asyncio.sleep(60)  # Longer wait on error

    async def _update_dashboard_state(self) -> None:
        """Update the current dashboard state with latest metrics."""
        try:
            # Get health status
            health_status = await self.health_manager.get_overall_health()

            # Get performance metrics summary
            performance_metrics = self.metrics.get_health_metrics()

            # Update dashboard state
            self.dashboard_state.update(
                {
                    "system_status": health_status["status"],
                    "performance_summary": {
                        "api_requests_per_second": performance_metrics.get(
                            "api_requests_per_second", 0
                        ),
                        "api_error_rate": performance_metrics.get("api_error_rate", 0),
                        "average_response_time": performance_metrics.get(
                            "average_response_time", 0
                        ),
                        "cpu_usage_percent": performance_metrics.get(
                            "cpu_usage_percent", 0
                        ),
                        "memory_usage_percent": performance_metrics.get(
                            "memory_usage_percent", 0
                        ),
                        "model_prediction_rate": performance_metrics.get(
                            "model_prediction_rate", 0
                        ),
                        "cache_hit_rate": performance_metrics.get("cache_hit_rate", 0)
                        * 100,
                    },
                    "last_update": datetime.utcnow().isoformat(),
                    "health_details": health_status.get("checks", []),
                }
            )

        except Exception as e:
            logger.error(f"Error updating dashboard state: {e}")

    async def _check_operational_alerts(self) -> None:
        """Check and manage operational alerts."""
        config = self.load_operations_config()
        alert_rules = config.get("alerts", [])

        current_time = datetime.utcnow()

        for rule in alert_rules:
            alert_id = rule["name"]

            # For now, we'll simulate alert checking based on dashboard state
            # In a full implementation, this would evaluate Prometheus queries
            alert_triggered = self._evaluate_alert_condition(rule)

            if alert_triggered:
                if alert_id not in self.active_alerts:
                    # New alert
                    alert_data = {
                        "id": alert_id,
                        "rule": rule,
                        "triggered_at": current_time.isoformat(),
                        "status": "firing",
                        "count": 1,
                    }
                    self.active_alerts[alert_id] = alert_data
                    self.alert_history.append(alert_data.copy())

                    await self._fire_operational_alert(alert_data)
                else:
                    # Update existing alert
                    self.active_alerts[alert_id]["count"] += 1
            else:
                # Clear alert if it exists
                if alert_id in self.active_alerts:
                    alert_data = self.active_alerts[alert_id]
                    alert_data["status"] = "resolved"
                    alert_data["resolved_at"] = current_time.isoformat()

                    await self._clear_operational_alert(alert_data)
                    del self.active_alerts[alert_id]

    def _evaluate_alert_condition(self, rule: dict[str, Any]) -> bool:
        """
        Evaluate alert condition based on current system state.

        This is a simplified implementation. In production, this would
        query Prometheus directly with the rule condition.
        """
        condition = rule.get("condition", "")
        performance = self.dashboard_state.get("performance_summary", {})

        # Simple rule evaluation based on common patterns
        if "api_error_rate" in condition and "> 0.05" in condition:
            return performance.get("api_error_rate", 0) > 5.0
        elif "cpu_usage_percent" in condition and "> 85" in condition:
            return performance.get("cpu_usage_percent", 0) > 85
        elif "memory_usage_percent" in condition and "> 85" in condition:
            return performance.get("memory_usage_percent", 0) > 85
        elif "cache_hit_rate" in condition and "< 0.8" in condition:
            return performance.get("cache_hit_rate", 100) < 80

        return False

    async def _fire_operational_alert(self, alert_data: dict[str, Any]) -> None:
        """Fire an operational alert with proper escalation."""
        rule = alert_data["rule"]

        logger.warning(
            f"ALERT FIRED: {rule['name']} - {rule['annotations']['summary']}"
        )

        # Add to dashboard active alerts
        self.dashboard_state["active_alerts"].append(
            {
                "id": alert_data["id"],
                "name": rule["name"],
                "severity": rule["labels"]["severity"],
                "summary": rule["annotations"]["summary"],
                "description": rule["annotations"]["description"],
                "runbook_url": rule["annotations"].get("runbook_url"),
                "triggered_at": alert_data["triggered_at"],
                "team": rule["labels"].get("team", "platform"),
            }
        )

    async def _clear_operational_alert(self, alert_data: dict[str, Any]) -> None:
        """Clear an operational alert."""
        rule = alert_data["rule"]

        logger.info(f"ALERT CLEARED: {rule['name']}")

        # Remove from dashboard active alerts
        self.dashboard_state["active_alerts"] = [
            alert
            for alert in self.dashboard_state["active_alerts"]
            if alert["id"] != alert_data["id"]
        ]

    async def _broadcast_dashboard_update(self) -> None:
        """Broadcast dashboard updates to connected WebSocket clients."""
        if not self.websocket_connections:
            return

        update_data = {
            "type": "dashboard_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": self.dashboard_state,
        }

        # Send to all connected clients
        disconnected_clients = set()

        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(update_data))
            except Exception:
                disconnected_clients.add(websocket)

        # Remove disconnected clients
        self.websocket_connections -= disconnected_clients

    async def add_websocket_connection(self, websocket: WebSocket):
        """Add a WebSocket connection for real-time updates."""
        await websocket.accept()
        self.websocket_connections.add(websocket)

        # Send initial dashboard state
        await websocket.send_text(
            json.dumps(
                {
                    "type": "initial_state",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": self.dashboard_state,
                }
            )
        )

        logger.info(
            f"WebSocket client connected. Total: {len(self.websocket_connections)}"
        )

    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.websocket_connections.discard(websocket)
        logger.info(
            f"WebSocket client disconnected. Total: {len(self.websocket_connections)}"
        )

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get current dashboard summary for API endpoints."""
        return {
            "system_status": self.dashboard_state["system_status"],
            "active_alerts_count": len(self.dashboard_state["active_alerts"]),
            "performance_summary": self.dashboard_state["performance_summary"],
            "last_update": self.dashboard_state["last_update"],
        }

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get current active alerts."""
        return self.dashboard_state["active_alerts"]

    def get_alert_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get alert history for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        return [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert["triggered_at"]) > cutoff_time
        ]

    def get_operations_dashboard_html(self) -> str:
        """Get the enhanced operations dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦟 Malaria Prediction - Production Operations Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }

        .dashboard-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
        }

        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 14px;
        }

        .status-healthy {
            background: #d4edda;
            color: #155724;
        }

        .status-warning {
            background: #fff3cd;
            color: #856404;
        }

        .status-critical {
            background: #f8d7da;
            color: #721c24;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }

        .dot-healthy { background: #28a745; }
        .dot-warning { background: #ffc107; }
        .dot-critical { background: #dc3545; }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .metric-title {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }

        .metric-unit {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 15px;
        }

        .metric-chart {
            height: 120px;
            margin-top: 15px;
        }

        .alerts-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
        }

        .alerts-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 20px;
        }

        .alert-item {
            background: #f8f9fa;
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }

        .alert-critical { border-left-color: #dc3545; }
        .alert-warning { border-left-color: #ffc107; }
        .alert-info { border-left-color: #17a2b8; }

        .alert-title {
            font-weight: 600;
            margin-bottom: 5px;
        }

        .alert-description {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 10px;
        }

        .alert-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #6c757d;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            z-index: 1000;
        }

        .connected {
            background: #d4edda;
            color: #155724;
        }

        .disconnected {
            background: #f8d7da;
            color: #721c24;
        }

        .performance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .performance-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }

        .performance-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
        }

        .performance-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }

        @media (max-width: 768px) {
            .dashboard-container {
                padding: 10px;
            }

            .metrics-grid {
                grid-template-columns: 1fr;
            }

            .header {
                padding: 15px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🦟 Malaria Prediction - Production Operations Dashboard</h1>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                <div id="system-status" class="status-indicator status-healthy">
                    <span class="status-dot dot-healthy"></span>
                    <span>System Healthy</span>
                </div>
                <div style="color: #6c757d; font-size: 14px;">
                    Last Updated: <span id="last-update">--</span>
                </div>
            </div>
        </div>

        <div class="connection-status connected" id="connection-status">
            🔗 Connected
        </div>

        <div id="alerts-section" class="alerts-section" style="display: none;">
            <div class="alerts-header">
                <h3>🚨 Active Alerts</h3>
            </div>
            <div id="alerts-container"></div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">📊 API Request Rate</span>
                </div>
                <div class="metric-value" id="api-requests" style="color: #3498db;">--</div>
                <div class="metric-unit">Requests per second</div>
                <canvas id="api-requests-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">⚠️ Error Rate</span>
                </div>
                <div class="metric-value" id="error-rate" style="color: #e74c3c;">--</div>
                <div class="metric-unit">Percentage</div>
                <canvas id="error-rate-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">⏱️ Response Time</span>
                </div>
                <div class="metric-value" id="response-time" style="color: #f39c12;">--</div>
                <div class="metric-unit">Milliseconds (avg)</div>
                <canvas id="response-time-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">🖥️ CPU Usage</span>
                </div>
                <div class="metric-value" id="cpu-usage" style="color: #9b59b6;">--</div>
                <div class="metric-unit">Percentage</div>
                <canvas id="cpu-usage-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">🧠 Memory Usage</span>
                </div>
                <div class="metric-value" id="memory-usage" style="color: #1abc9c;">--</div>
                <div class="metric-unit">Percentage</div>
                <canvas id="memory-usage-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">🤖 ML Predictions</span>
                </div>
                <div class="metric-value" id="ml-predictions" style="color: #27ae60;">--</div>
                <div class="metric-unit">Predictions per second</div>
                <canvas id="ml-predictions-chart" class="metric-chart"></canvas>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">💾 Cache Hit Rate</span>
                </div>
                <div class="metric-value" id="cache-hit-rate" style="color: #e67e22;">--</div>
                <div class="metric-unit">Percentage</div>
                <canvas id="cache-hit-rate-chart" class="metric-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/operations-dashboard`);

        // Chart instances
        const charts = {};

        // Initialize mini charts
        function initializeCharts() {
            const chartConfigs = {
                'api-requests-chart': { color: '#3498db', label: 'API Requests/sec' },
                'error-rate-chart': { color: '#e74c3c', label: 'Error Rate %' },
                'response-time-chart': { color: '#f39c12', label: 'Response Time (ms)' },
                'cpu-usage-chart': { color: '#9b59b6', label: 'CPU Usage %' },
                'memory-usage-chart': { color: '#1abc9c', label: 'Memory Usage %' },
                'ml-predictions-chart': { color: '#27ae60', label: 'ML Predictions/sec' },
                'cache-hit-rate-chart': { color: '#e67e22', label: 'Cache Hit Rate %' }
            };

            Object.entries(chartConfigs).forEach(([canvasId, config]) => {
                const ctx = document.getElementById(canvasId).getContext('2d');
                charts[canvasId] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            data: [],
                            borderColor: config.color,
                            backgroundColor: config.color + '20',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { display: false },
                            y: { display: false }
                        },
                        plugins: {
                            legend: { display: false }
                        },
                        elements: {
                            point: { radius: 0 }
                        }
                    }
                });
            });
        }

        // Update chart data
        function updateChart(chartId, value) {
            const chart = charts[chartId];
            if (!chart) return;

            const now = new Date().toLocaleTimeString();

            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(value);

            // Keep only last 20 points
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }

            chart.update('none');
        }

        // WebSocket event handlers
        ws.onopen = function() {
            document.getElementById('connection-status').className = 'connection-status connected';
            document.getElementById('connection-status').textContent = '🔗 Connected';
        };

        ws.onclose = function() {
            document.getElementById('connection-status').className = 'connection-status disconnected';
            document.getElementById('connection-status').textContent = '❌ Disconnected';
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'dashboard_update' || data.type === 'initial_state') {
                updateDashboard(data.data);
            }
        };

        function updateDashboard(dashboardData) {
            // Update system status
            const systemStatus = dashboardData.system_status || 'unknown';
            const statusElement = document.getElementById('system-status');

            statusElement.className = `status-indicator status-${systemStatus}`;
            const dot = statusElement.querySelector('.status-dot');
            dot.className = `status-dot dot-${systemStatus}`;
            statusElement.querySelector('span:last-child').textContent =
                systemStatus.charAt(0).toUpperCase() + systemStatus.slice(1);

            // Update last update time
            if (dashboardData.last_update) {
                const updateTime = new Date(dashboardData.last_update).toLocaleString();
                document.getElementById('last-update').textContent = updateTime;
            }

            // Update performance metrics
            const perf = dashboardData.performance_summary || {};

            const metrics = [
                { id: 'api-requests', value: perf.api_requests_per_second || 0, chart: 'api-requests-chart' },
                { id: 'error-rate', value: perf.api_error_rate || 0, chart: 'error-rate-chart' },
                { id: 'response-time', value: perf.average_response_time || 0, chart: 'response-time-chart' },
                { id: 'cpu-usage', value: perf.cpu_usage_percent || 0, chart: 'cpu-usage-chart' },
                { id: 'memory-usage', value: perf.memory_usage_percent || 0, chart: 'memory-usage-chart' },
                { id: 'ml-predictions', value: perf.model_prediction_rate || 0, chart: 'ml-predictions-chart' },
                { id: 'cache-hit-rate', value: perf.cache_hit_rate || 0, chart: 'cache-hit-rate-chart' }
            ];

            metrics.forEach(metric => {
                const element = document.getElementById(metric.id);
                if (element) {
                    let displayValue = metric.value;
                    if (metric.id.includes('rate') || metric.id.includes('usage')) {
                        displayValue = Math.round(displayValue * 100) / 100 + '%';
                    } else {
                        displayValue = Math.round(displayValue * 100) / 100;
                    }
                    element.textContent = displayValue;
                    updateChart(metric.chart, metric.value);
                }
            });

            // Update alerts
            updateAlerts(dashboardData.active_alerts || []);
        }

        function updateAlerts(alerts) {
            const alertsSection = document.getElementById('alerts-section');
            const alertsContainer = document.getElementById('alerts-container');

            if (alerts.length === 0) {
                alertsSection.style.display = 'none';
            } else {
                alertsSection.style.display = 'block';
                alertsContainer.innerHTML = '';

                alerts.forEach(alert => {
                    const alertElement = document.createElement('div');
                    alertElement.className = `alert-item alert-${alert.severity}`;
                    alertElement.innerHTML = `
                        <div class="alert-title">${alert.name}</div>
                        <div class="alert-description">${alert.description}</div>
                        <div class="alert-meta">
                            <span>Severity: ${alert.severity.toUpperCase()}</span>
                            <span>Team: ${alert.team}</span>
                            <span>Triggered: ${new Date(alert.triggered_at).toLocaleString()}</span>
                            ${alert.runbook_url ? `<a href="${alert.runbook_url}" target="_blank">📖 Runbook</a>` : ''}
                        </div>
                    `;
                    alertsContainer.appendChild(alertElement);
                });
            }
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initializeCharts);
    </script>
</body>
</html>
        """

    def export_grafana_dashboards(self) -> dict[str, Any]:
        """Export dashboard configurations for Grafana import."""
        config = self.load_operations_config()

        return {
            "dashboards": config.get("dashboards", []),
            "version": config.get("version", "1.0.0"),
            "title": config.get("title", "Operations Dashboard"),
        }

    def export_prometheus_alerts(self) -> str:
        """Export alert rules in Prometheus format."""
        config = self.load_operations_config()
        alerts = config.get("alerts", [])

        rules = {
            "groups": [{"name": "malaria_prediction_operations_alerts", "rules": []}]
        }

        for alert in alerts:
            rule = {
                "alert": alert["name"],
                "expr": alert["condition"],
                "for": alert.get("for", "5m"),
                "labels": alert.get("labels", {}),
                "annotations": alert.get("annotations", {}),
            }
            rules["groups"][0]["rules"].append(rule)

        return json.dumps(rules, indent=2)


# Global operations dashboard instance
_operations_dashboard: OperationsDashboardManager | None = None


def get_operations_dashboard() -> OperationsDashboardManager:
    """Get the global operations dashboard instance."""
    global _operations_dashboard
    if _operations_dashboard is None:
        _operations_dashboard = OperationsDashboardManager()
    return _operations_dashboard
