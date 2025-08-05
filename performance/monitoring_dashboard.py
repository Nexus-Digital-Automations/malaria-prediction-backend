"""
Real-time Performance Monitoring Dashboard.

This module provides a comprehensive performance monitoring dashboard
with real-time metrics, profiling, and alerting capabilities.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime

import psutil
from fastapi import WebSocket
from prometheus_client import Counter, Gauge, Histogram, generate_latest

from .cache_optimization import get_cache_optimizer
from .database_optimization import DatabaseOptimizer

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Real-time performance metric data point."""

    timestamp: float
    metric_type: str
    value: float
    labels: dict[str, str] = None
    metadata: dict = None


@dataclass
class AlertRule:
    """Performance alert rule configuration."""

    name: str
    metric: str
    threshold: float
    operator: str  # >, <, >=, <=, ==
    duration: int  # seconds
    description: str
    severity: str = "warning"  # info, warning, critical
    enabled: bool = True


class PerformanceMonitoringDashboard:
    """Real-time performance monitoring dashboard."""

    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)
        self.alert_rules = self._create_default_alert_rules()
        self.active_alerts = {}
        self.connected_clients = set()

        # Prometheus metrics
        self.setup_prometheus_metrics()

        # Monitoring services
        self.cache_optimizer = None
        self.db_optimizer = DatabaseOptimizer()

        # Performance history
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None

    def setup_prometheus_metrics(self):
        """Initialize Prometheus metrics for monitoring."""
        self.prometheus_metrics = {
            "api_requests_total": Counter(
                "malaria_api_requests_total",
                "Total API requests",
                ["endpoint", "method", "status"],
            ),
            "api_request_duration": Histogram(
                "malaria_api_request_duration_seconds",
                "API request duration",
                ["endpoint", "method"],
            ),
            "database_connections": Gauge(
                "malaria_database_connections",
                "Database connections",
                ["state"],  # active, idle, total
            ),
            "cache_operations": Counter(
                "malaria_cache_operations_total",
                "Cache operations",
                ["operation", "status"],  # get/set, hit/miss
            ),
            "system_cpu_usage": Gauge(
                "malaria_system_cpu_usage_percent", "System CPU usage percentage"
            ),
            "system_memory_usage": Gauge(
                "malaria_system_memory_usage_percent", "System memory usage percentage"
            ),
            "prediction_latency": Histogram(
                "malaria_prediction_latency_seconds",
                "ML prediction latency",
                ["model_type"],
            ),
            "active_users": Gauge("malaria_active_users", "Number of active users"),
        }

    def _create_default_alert_rules(self) -> list[AlertRule]:
        """Create default performance alert rules."""
        return [
            AlertRule(
                name="high_response_time",
                metric="api_request_duration_p95",
                threshold=2000,  # 2 seconds
                operator=">",
                duration=60,  # 1 minute
                description="API P95 response time is above 2 seconds",
                severity="warning",
            ),
            AlertRule(
                name="critical_response_time",
                metric="api_request_duration_p95",
                threshold=5000,  # 5 seconds
                operator=">",
                duration=30,  # 30 seconds
                description="API P95 response time is above 5 seconds",
                severity="critical",
            ),
            AlertRule(
                name="high_error_rate",
                metric="api_error_rate",
                threshold=0.05,  # 5%
                operator=">",
                duration=120,  # 2 minutes
                description="API error rate is above 5%",
                severity="warning",
            ),
            AlertRule(
                name="low_cache_hit_rate",
                metric="cache_hit_rate",
                threshold=0.7,  # 70%
                operator="<",
                duration=300,  # 5 minutes
                description="Cache hit rate is below 70%",
                severity="warning",
            ),
            AlertRule(
                name="high_database_connections",
                metric="database_active_connections",
                threshold=80,  # 80% of pool
                operator=">",
                duration=60,  # 1 minute
                description="Database connection usage is above 80%",
                severity="warning",
            ),
            AlertRule(
                name="high_cpu_usage",
                metric="system_cpu_usage",
                threshold=85,  # 85%
                operator=">",
                duration=180,  # 3 minutes
                description="System CPU usage is above 85%",
                severity="warning",
            ),
            AlertRule(
                name="high_memory_usage",
                metric="system_memory_usage",
                threshold=90,  # 90%
                operator=">",
                duration=120,  # 2 minutes
                description="System memory usage is above 90%",
                severity="critical",
            ),
        ]

    async def start_monitoring(self):
        """Start real-time performance monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Initialize cache optimizer
        self.cache_optimizer = await get_cache_optimizer()

        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Performance monitoring dashboard started")

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring dashboard stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop that collects metrics."""
        while self.monitoring_active:
            try:
                # Collect all metrics
                metrics = await self._collect_all_metrics()

                # Process metrics
                for metric in metrics:
                    self._process_metric(metric)

                # Check alert rules
                await self._check_alert_rules(metrics)

                # Broadcast to connected clients
                await self._broadcast_metrics(metrics)

                # Update Prometheus metrics
                self._update_prometheus_metrics(metrics)

                # Wait before next collection
                await asyncio.sleep(5)  # 5-second intervals

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)  # Longer wait on error

    async def _collect_all_metrics(self) -> list[PerformanceMetric]:
        """Collect all performance metrics from various sources."""
        metrics = []
        timestamp = time.time()

        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()

            metrics.extend(
                [
                    PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="system_cpu_usage",
                        value=cpu_percent,
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="system_memory_usage",
                        value=memory.percent,
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="system_memory_available_mb",
                        value=memory.available / (1024 * 1024),
                    ),
                ]
            )

            # Database metrics
            try:
                # Get database connection pool stats
                from src.malaria_predictor.database.session import (
                    get_connection_pool_status,
                )

                pool_status = await get_connection_pool_status()

                if pool_status.get("pool_size"):
                    metrics.extend(
                        [
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="database_active_connections",
                                value=pool_status["checked_out"] or 0,
                            ),
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="database_idle_connections",
                                value=pool_status["checked_in"] or 0,
                            ),
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="database_pool_utilization",
                                value=(pool_status["checked_out"] or 0)
                                / (pool_status["pool_size"] or 1)
                                * 100,
                            ),
                        ]
                    )
            except Exception as e:
                logger.debug(f"Could not collect database metrics: {e}")

            # Cache metrics
            if self.cache_optimizer:
                try:
                    cache_stats = await self.cache_optimizer.get_cache_statistics()
                    perf_metrics = cache_stats.get("performance_metrics", {})
                    memory_usage = cache_stats.get("memory_usage", {})

                    metrics.extend(
                        [
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="cache_hit_rate",
                                value=perf_metrics.get("hit_rate", 0),
                            ),
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="cache_miss_rate",
                                value=perf_metrics.get("miss_rate", 0),
                            ),
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="cache_memory_usage_mb",
                                value=memory_usage.get("used_memory_mb", 0),
                            ),
                            PerformanceMetric(
                                timestamp=timestamp,
                                metric_type="cache_memory_utilization",
                                value=memory_usage.get("memory_utilization", 0) * 100,
                            ),
                        ]
                    )
                except Exception as e:
                    logger.debug(f"Could not collect cache metrics: {e}")

            # Application-specific metrics
            metrics.extend(
                [
                    PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="connected_websocket_clients",
                        value=len(self.connected_clients),
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="active_alerts",
                        value=len(self.active_alerts),
                    ),
                ]
            )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

        return metrics

    def _process_metric(self, metric: PerformanceMetric):
        """Process and store a metric."""
        # Add to metrics buffer
        self.metrics_buffer.append(metric)

        # Add to performance history
        self.performance_history[metric.metric_type].append(
            {"timestamp": metric.timestamp, "value": metric.value}
        )

        # Update Prometheus gauge if applicable
        prometheus_metric = self.prometheus_metrics.get(metric.metric_type)
        if prometheus_metric and hasattr(prometheus_metric, "set"):
            prometheus_metric.set(metric.value)

    async def _check_alert_rules(self, metrics: list[PerformanceMetric]):
        """Check alert rules against current metrics."""
        current_time = time.time()

        # Create metric lookup
        metric_values = {m.metric_type: m.value for m in metrics}

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            metric_value = metric_values.get(rule.metric)
            if metric_value is None:
                continue

            # Check threshold
            alert_triggered = self._evaluate_threshold(
                metric_value, rule.threshold, rule.operator
            )

            alert_key = f"{rule.name}_{rule.metric}"

            if alert_triggered:
                if alert_key not in self.active_alerts:
                    # New alert
                    self.active_alerts[alert_key] = {
                        "rule": rule,
                        "started_at": current_time,
                        "current_value": metric_value,
                        "count": 1,
                    }
                else:
                    # Update existing alert
                    alert = self.active_alerts[alert_key]
                    alert["current_value"] = metric_value
                    alert["count"] += 1

                    # Check if alert should fire (after duration)
                    if current_time - alert["started_at"] >= rule.duration:
                        await self._fire_alert(rule, metric_value)
            else:
                # Clear alert if it exists
                if alert_key in self.active_alerts:
                    await self._clear_alert(rule)
                    del self.active_alerts[alert_key]

    def _evaluate_threshold(
        self, value: float, threshold: float, operator: str
    ) -> bool:
        """Evaluate metric against threshold with given operator."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        else:
            return False

    async def _fire_alert(self, rule: AlertRule, current_value: float):
        """Fire an alert notification."""
        alert_data = {
            "type": "alert_fired",
            "rule_name": rule.name,
            "severity": rule.severity,
            "description": rule.description,
            "current_value": current_value,
            "threshold": rule.threshold,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.warning(
            f"Alert fired: {rule.name} - {rule.description} (value: {current_value})"
        )

        # Broadcast to connected clients
        await self._broadcast_alert(alert_data)

    async def _clear_alert(self, rule: AlertRule):
        """Clear an alert notification."""
        alert_data = {
            "type": "alert_cleared",
            "rule_name": rule.name,
            "description": f"Alert cleared: {rule.description}",
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Alert cleared: {rule.name}")

        # Broadcast to connected clients
        await self._broadcast_alert(alert_data)

    async def _broadcast_metrics(self, metrics: list[PerformanceMetric]):
        """Broadcast metrics to connected WebSocket clients."""
        if not self.connected_clients:
            return

        # Prepare metrics data
        metrics_data = {
            "type": "metrics_update",
            "timestamp": time.time(),
            "metrics": [
                {
                    "metric_type": m.metric_type,
                    "value": m.value,
                    "timestamp": m.timestamp,
                    "labels": m.labels or {},
                }
                for m in metrics
            ],
        }

        # Send to all connected clients
        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send_text(json.dumps(metrics_data))
            except Exception:
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

    async def _broadcast_alert(self, alert_data: dict):
        """Broadcast alert to connected WebSocket clients."""
        if not self.connected_clients:
            return

        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send_text(json.dumps(alert_data))
            except Exception:
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

    def _update_prometheus_metrics(self, metrics: list[PerformanceMetric]):
        """Update Prometheus metrics."""
        for metric in metrics:
            prometheus_metric = self.prometheus_metrics.get(metric.metric_type)
            if prometheus_metric and hasattr(prometheus_metric, "set"):
                prometheus_metric.set(metric.value)

    async def add_websocket_client(self, websocket: WebSocket):
        """Add a WebSocket client for real-time updates."""
        await websocket.accept()
        self.connected_clients.add(websocket)

        # Send initial data
        await self._send_initial_data(websocket)

        logger.info(
            f"WebSocket client connected. Total clients: {len(self.connected_clients)}"
        )

    async def remove_websocket_client(self, websocket: WebSocket):
        """Remove a WebSocket client."""
        self.connected_clients.discard(websocket)
        logger.info(
            f"WebSocket client disconnected. Total clients: {len(self.connected_clients)}"
        )

    async def _send_initial_data(self, websocket: WebSocket):
        """Send initial dashboard data to new client."""
        try:
            # Send recent metrics history
            history_data = {}
            for metric_type, history in self.performance_history.items():
                history_data[metric_type] = list(history)[-50:]  # Last 50 points

            initial_data = {
                "type": "initial_data",
                "metrics_history": history_data,
                "active_alerts": [
                    {
                        "rule_name": alert["rule"].name,
                        "severity": alert["rule"].severity,
                        "description": alert["rule"].description,
                        "current_value": alert["current_value"],
                        "started_at": alert["started_at"],
                    }
                    for alert in self.active_alerts.values()
                ],
                "alert_rules": [asdict(rule) for rule in self.alert_rules],
            }

            await websocket.send_text(json.dumps(initial_data))

        except Exception as e:
            logger.error(f"Error sending initial data: {e}")

    def get_dashboard_html(self) -> str:
        """Get the HTML dashboard page."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Malaria Prediction API - Performance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .alert.warning { background: #f39c12; color: white; }
        .alert.critical { background: #e74c3c; color: white; }
        .chart-container { height: 300px; margin-top: 20px; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-good { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-critical { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🦟 Malaria Prediction API - Performance Dashboard</h1>
        <p>Real-time performance monitoring and alerting</p>
        <div>
            <span class="status-indicator status-good"></span>
            <span id="connection-status">Connecting...</span>
        </div>
    </div>

    <div id="alerts-container"></div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>API Response Time</h3>
            <div class="metric-value" id="response-time">--</div>
            <div>P95 Response Time (ms)</div>
            <canvas id="response-time-chart" class="chart-container"></canvas>
        </div>

        <div class="metric-card">
            <h3>System CPU Usage</h3>
            <div class="metric-value" id="cpu-usage">--</div>
            <div>CPU Usage (%)</div>
            <canvas id="cpu-chart" class="chart-container"></canvas>
        </div>

        <div class="metric-card">
            <h3>Memory Usage</h3>
            <div class="metric-value" id="memory-usage">--</div>
            <div>Memory Usage (%)</div>
            <canvas id="memory-chart" class="chart-container"></canvas>
        </div>

        <div class="metric-card">
            <h3>Cache Hit Rate</h3>
            <div class="metric-value" id="cache-hit-rate">--</div>
            <div>Cache Hit Rate (%)</div>
            <canvas id="cache-chart" class="chart-container"></canvas>
        </div>

        <div class="metric-card">
            <h3>Database Connections</h3>
            <div class="metric-value" id="db-connections">--</div>
            <div>Active Connections</div>
            <canvas id="db-chart" class="chart-container"></canvas>
        </div>

        <div class="metric-card">
            <h3>Active Users</h3>
            <div class="metric-value" id="active-users">--</div>
            <div>Current Active Users</div>
            <canvas id="users-chart" class="chart-container"></canvas>
        </div>
    </div>

    <script>
        // WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
        const charts = {};

        // Initialize charts
        function initializeCharts() {
            const chartConfigs = {
                'response-time-chart': { label: 'Response Time (ms)', color: '#3498db' },
                'cpu-chart': { label: 'CPU Usage (%)', color: '#e74c3c' },
                'memory-chart': { label: 'Memory Usage (%)', color: '#f39c12' },
                'cache-chart': { label: 'Cache Hit Rate (%)', color: '#27ae60' },
                'db-chart': { label: 'DB Connections', color: '#9b59b6' },
                'users-chart': { label: 'Active Users', color: '#1abc9c' }
            };

            Object.entries(chartConfigs).forEach(([canvasId, config]) => {
                const ctx = document.getElementById(canvasId).getContext('2d');
                charts[canvasId] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: config.label,
                            data: [],
                            borderColor: config.color,
                            backgroundColor: config.color + '20',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { display: false },
                            y: { beginAtZero: true }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            });
        }

        // Update chart data
        function updateChart(chartId, value, timestamp) {
            const chart = charts[chartId];
            if (!chart) return;

            const time = new Date(timestamp * 1000).toLocaleTimeString();

            chart.data.labels.push(time);
            chart.data.datasets[0].data.push(value);

            // Keep only last 50 points
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }

            chart.update('none');
        }

        // WebSocket event handlers
        ws.onopen = function() {
            document.getElementById('connection-status').textContent = 'Connected';
        };

        ws.onclose = function() {
            document.getElementById('connection-status').textContent = 'Disconnected';
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'metrics_update') {
                data.metrics.forEach(metric => {
                    const value = Math.round(metric.value * 100) / 100;

                    switch(metric.metric_type) {
                        case 'system_cpu_usage':
                            document.getElementById('cpu-usage').textContent = value + '%';
                            updateChart('cpu-chart', value, metric.timestamp);
                            break;
                        case 'system_memory_usage':
                            document.getElementById('memory-usage').textContent = value + '%';
                            updateChart('memory-chart', value, metric.timestamp);
                            break;
                        case 'cache_hit_rate':
                            document.getElementById('cache-hit-rate').textContent = (value * 100).toFixed(1) + '%';
                            updateChart('cache-chart', value * 100, metric.timestamp);
                            break;
                        case 'database_active_connections':
                            document.getElementById('db-connections').textContent = value;
                            updateChart('db-chart', value, metric.timestamp);
                            break;
                        case 'connected_websocket_clients':
                            document.getElementById('active-users').textContent = value;
                            updateChart('users-chart', value, metric.timestamp);
                            break;
                    }
                });
            } else if (data.type === 'alert_fired') {
                showAlert(data);
            } else if (data.type === 'alert_cleared') {
                clearAlert(data.rule_name);
            }
        };

        function showAlert(alert) {
            const alertsContainer = document.getElementById('alerts-container');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${alert.severity}`;
            alertDiv.id = `alert-${alert.rule_name}`;
            alertDiv.innerHTML = `
                <strong>${alert.severity.toUpperCase()}</strong>: ${alert.description}
                <br>Current value: ${alert.current_value}, Threshold: ${alert.threshold}
            `;
            alertsContainer.appendChild(alertDiv);
        }

        function clearAlert(ruleName) {
            const alertDiv = document.getElementById(`alert-${ruleName}`);
            if (alertDiv) {
                alertDiv.remove();
            }
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initializeCharts);
    </script>
</body>
</html>
        """

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest()


# Global dashboard instance
_dashboard = None


def get_monitoring_dashboard() -> PerformanceMonitoringDashboard:
    """Get or create global monitoring dashboard instance."""
    global _dashboard

    if _dashboard is None:
        _dashboard = PerformanceMonitoringDashboard()

    return _dashboard
