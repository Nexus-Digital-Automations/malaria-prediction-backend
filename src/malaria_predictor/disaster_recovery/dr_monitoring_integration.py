#!/usr/bin/env python3
"""
Disaster Recovery Monitoring Integration for Malaria Prediction System.

This module integrates disaster recovery capabilities with existing monitoring and alerting:
- Prometheus metrics for DR system health
- Grafana dashboard integration
- Alert routing for DR events
- Operations dashboard integration
- Automated DR testing metrics
- Recovery time and performance tracking
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import httpx
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/malaria-prediction/dr-monitoring.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DRMetricsCollector:
    """Collects and exposes disaster recovery metrics for Prometheus."""

    def __init__(self, registry: CollectorRegistry | None = None):
        """Initialize DR metrics collector.

        Args:
            registry: Prometheus registry to use
        """
        self.registry = registry or CollectorRegistry()

        # Backup metrics
        self.backup_operations_total = Counter(
            "dr_backup_operations_total",
            "Total number of backup operations",
            ["component", "type", "status"],
            registry=self.registry,
        )

        self.backup_duration_seconds = Histogram(
            "dr_backup_duration_seconds",
            "Duration of backup operations in seconds",
            ["component", "type"],
            registry=self.registry,
        )

        self.backup_size_bytes = Gauge(
            "dr_backup_size_bytes",
            "Size of backup files in bytes",
            ["component", "type"],
            registry=self.registry,
        )

        self.last_backup_timestamp = Gauge(
            "dr_last_backup_timestamp",
            "Timestamp of last successful backup",
            ["component"],
            registry=self.registry,
        )

        # Recovery metrics
        self.recovery_operations_total = Counter(
            "dr_recovery_operations_total",
            "Total number of recovery operations",
            ["type", "status"],
            registry=self.registry,
        )

        self.recovery_duration_seconds = Histogram(
            "dr_recovery_duration_seconds",
            "Duration of recovery operations in seconds",
            ["type"],
            registry=self.registry,
        )

        self.rto_seconds = Gauge(
            "dr_recovery_time_objective_seconds",
            "Current Recovery Time Objective in seconds",
            ["service"],
            registry=self.registry,
        )

        self.rpo_seconds = Gauge(
            "dr_recovery_point_objective_seconds",
            "Current Recovery Point Objective in seconds",
            ["service"],
            registry=self.registry,
        )

        # Data corruption metrics
        self.data_corruption_alerts_total = Counter(
            "dr_data_corruption_alerts_total",
            "Total number of data corruption alerts",
            ["table", "type", "severity"],
            registry=self.registry,
        )

        self.data_quality_score = Gauge(
            "dr_data_quality_score",
            "Data quality score (0.0 to 1.0)",
            ["table"],
            registry=self.registry,
        )

        self.corruption_recovery_success_total = Counter(
            "dr_corruption_recovery_success_total",
            "Total successful corruption recoveries",
            ["table", "type"],
            registry=self.registry,
        )

        # Failover metrics
        self.failover_operations_total = Counter(
            "dr_failover_operations_total",
            "Total number of failover operations",
            ["type", "status"],
            registry=self.registry,
        )

        self.failover_duration_seconds = Histogram(
            "dr_failover_duration_seconds",
            "Duration of failover operations in seconds",
            ["type"],
            registry=self.registry,
        )

        self.service_health_score = Gauge(
            "dr_service_health_score",
            "Overall service health score (0.0 to 1.0)",
            ["service"],
            registry=self.registry,
        )

        # Testing metrics
        self.dr_tests_total = Counter(
            "dr_tests_total",
            "Total number of DR tests performed",
            ["test_type", "status"],
            registry=self.registry,
        )

        self.dr_test_duration_seconds = Histogram(
            "dr_test_duration_seconds",
            "Duration of DR tests in seconds",
            ["test_type"],
            registry=self.registry,
        )

        self.dr_test_success_rate = Gauge(
            "dr_test_success_rate",
            "DR test success rate (0.0 to 1.0)",
            ["test_type"],
            registry=self.registry,
        )

        # System info
        self.dr_system_info = Info(
            "dr_system_info",
            "Disaster recovery system information",
            registry=self.registry,
        )

        # Initialize system info
        self.dr_system_info.info(
            {
                "version": "1.0.0",
                "backup_retention_days": "30",
                "rto_target_minutes": "120",
                "rpo_target_minutes": "15",
            }
        )

    def record_backup_operation(
        self,
        component: str,
        backup_type: str,
        duration: float,
        size_bytes: int,
        success: bool,
    ) -> None:
        """Record a backup operation.

        Args:
            component: Component being backed up
            backup_type: Type of backup
            duration: Backup duration in seconds
            size_bytes: Backup size in bytes
            success: Whether backup was successful
        """
        status = "success" if success else "failure"

        self.backup_operations_total.labels(
            component=component, type=backup_type, status=status
        ).inc()

        if success:
            self.backup_duration_seconds.labels(
                component=component, type=backup_type
            ).observe(duration)

            self.backup_size_bytes.labels(component=component, type=backup_type).set(
                size_bytes
            )

            self.last_backup_timestamp.labels(component=component).set(time.time())

    def record_recovery_operation(
        self, recovery_type: str, duration: float, success: bool
    ) -> None:
        """Record a recovery operation.

        Args:
            recovery_type: Type of recovery
            duration: Recovery duration in seconds
            success: Whether recovery was successful
        """
        status = "success" if success else "failure"

        self.recovery_operations_total.labels(type=recovery_type, status=status).inc()

        if success:
            self.recovery_duration_seconds.labels(type=recovery_type).observe(duration)

    def record_data_corruption_alert(
        self, table: str, corruption_type: str, severity: str
    ) -> None:
        """Record a data corruption alert.

        Args:
            table: Affected table
            corruption_type: Type of corruption
            severity: Alert severity
        """
        self.data_corruption_alerts_total.labels(
            table=table, type=corruption_type, severity=severity
        ).inc()

    def update_data_quality_score(self, table: str, score: float) -> None:
        """Update data quality score for a table.

        Args:
            table: Table name
            score: Quality score (0.0 to 1.0)
        """
        self.data_quality_score.labels(table=table).set(score)

    def record_failover_operation(
        self, failover_type: str, duration: float, success: bool
    ) -> None:
        """Record a failover operation.

        Args:
            failover_type: Type of failover
            duration: Failover duration in seconds
            success: Whether failover was successful
        """
        status = "success" if success else "failure"

        self.failover_operations_total.labels(type=failover_type, status=status).inc()

        if success:
            self.failover_duration_seconds.labels(type=failover_type).observe(duration)

    def update_service_health_score(self, service: str, score: float) -> None:
        """Update service health score.

        Args:
            service: Service name
            score: Health score (0.0 to 1.0)
        """
        self.service_health_score.labels(service=service).set(score)

    def record_dr_test(self, test_type: str, duration: float, success: bool) -> None:
        """Record a DR test execution.

        Args:
            test_type: Type of DR test
            duration: Test duration in seconds
            success: Whether test was successful
        """
        status = "success" if success else "failure"

        self.dr_tests_total.labels(test_type=test_type, status=status).inc()

        self.dr_test_duration_seconds.labels(test_type=test_type).observe(duration)

    def update_test_success_rate(self, test_type: str, success_rate: float) -> None:
        """Update DR test success rate.

        Args:
            test_type: Type of DR test
            success_rate: Success rate (0.0 to 1.0)
        """
        self.dr_test_success_rate.labels(test_type=test_type).set(success_rate)


class AlertManager:
    """Manages alerts for disaster recovery events."""

    def __init__(
        self,
        webhook_urls: list[str],
        slack_webhook: str | None = None,
        email_config: dict | None = None,
    ):
        """Initialize alert manager.

        Args:
            webhook_urls: List of webhook URLs for alerts
            slack_webhook: Slack webhook URL
            email_config: Email configuration
        """
        self.webhook_urls = webhook_urls
        self.slack_webhook = slack_webhook
        self.email_config = email_config

        # Alert thresholds
        self.thresholds = {
            "backup_failure_count": 3,
            "recovery_time_threshold": 7200,  # 2 hours
            "data_quality_threshold": 0.8,
            "service_health_threshold": 0.9,
        }

    async def send_dr_alert(
        self, alert_type: str, severity: str, message: str, details: dict[str, Any]
    ) -> None:
        """Send disaster recovery alert.

        Args:
            alert_type: Type of alert
            severity: Alert severity (low, medium, high, critical)
            message: Alert message
            details: Additional alert details
        """
        alert_payload = {
            "timestamp": datetime.now().isoformat(),
            "service": "malaria-prediction-dr",
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "details": details,
        }

        # Send to webhook URLs
        for webhook_url in self.webhook_urls:
            try:
                await self._send_webhook_alert(webhook_url, alert_payload)
            except Exception as e:
                logger.error(f"Failed to send alert to {webhook_url}: {e}")

        # Send to Slack if configured
        if self.slack_webhook:
            try:
                await self._send_slack_alert(alert_payload)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

        # Send email if configured
        if self.email_config:
            try:
                await self._send_email_alert(alert_payload)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, webhook_url: str, alert_payload: dict) -> None:
        """Send alert to webhook URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=alert_payload)
            response.raise_for_status()

    async def _send_slack_alert(self, alert_payload: dict) -> None:
        """Send alert to Slack."""
        severity_colors = {
            "low": "#36a64f",
            "medium": "#ff9900",
            "high": "#ff0000",
            "critical": "#800000",
        }

        slack_payload = {
            "attachments": [
                {
                    "color": severity_colors.get(alert_payload["severity"], "#808080"),
                    "title": f"DR Alert: {alert_payload['alert_type']}",
                    "text": alert_payload["message"],
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert_payload["severity"].upper(),
                            "short": True,
                        },
                        {
                            "title": "Service",
                            "value": alert_payload["service"],
                            "short": True,
                        },
                        {
                            "title": "Timestamp",
                            "value": alert_payload["timestamp"],
                            "short": False,
                        },
                    ],
                    "footer": "Malaria Prediction DR System",
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.slack_webhook, json=slack_payload)
            response.raise_for_status()

    async def _send_email_alert(self, alert_payload: dict) -> None:
        """Send alert via email."""
        # This would integrate with your email service (SMTP, SES, etc.)
        # Implementation depends on your email configuration
        logger.info(f"Email alert would be sent: {alert_payload['message']}")


class OperationsDashboardIntegration:
    """Integrates DR monitoring with operations dashboard."""

    def __init__(self, dashboard_api_url: str, api_key: str):
        """Initialize dashboard integration.

        Args:
            dashboard_api_url: Operations dashboard API URL
            api_key: API key for dashboard
        """
        self.dashboard_api_url = dashboard_api_url
        self.api_key = api_key

    async def update_dr_status(self, status_data: dict[str, Any]) -> None:
        """Update DR status in operations dashboard.

        Args:
            status_data: DR status information
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.dashboard_api_url}/api/dr/status",
                    json=status_data,
                    headers=headers,
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Failed to update dashboard DR status: {e}")

    async def create_dr_incident(self, incident_data: dict[str, Any]) -> str | None:
        """Create DR incident in operations dashboard.

        Args:
            incident_data: Incident information

        Returns:
            Incident ID if created successfully
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.dashboard_api_url}/api/incidents",
                    json=incident_data,
                    headers=headers,
                )
                response.raise_for_status()

                result = response.json()
                return result.get("incident_id")

        except Exception as e:
            logger.error(f"Failed to create dashboard incident: {e}")
            return None


class DRMonitoringService:
    """Main service for DR monitoring integration."""

    def __init__(
        self,
        metrics_port: int = 9091,
        webhook_urls: list[str] | None = None,
        slack_webhook: str | None = None,
        dashboard_api_url: str | None = None,
        dashboard_api_key: str | None = None,
    ):
        """Initialize DR monitoring service.

        Args:
            metrics_port: Port to serve Prometheus metrics
            webhook_urls: Webhook URLs for alerts
            slack_webhook: Slack webhook URL
            dashboard_api_url: Operations dashboard API URL
            dashboard_api_key: Dashboard API key
        """
        self.metrics_port = metrics_port

        # Initialize components
        self.metrics_collector = DRMetricsCollector()
        self.alert_manager = AlertManager(webhook_urls or [], slack_webhook)

        self.dashboard_integration = None
        if dashboard_api_url and dashboard_api_key:
            self.dashboard_integration = OperationsDashboardIntegration(
                dashboard_api_url, dashboard_api_key
            )

        # Monitoring state
        self.last_status_update = None
        self.active_incidents: dict[str, dict] = {}

    async def start_metrics_server(self) -> None:
        """Start Prometheus metrics server."""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class MetricsHandler(BaseHTTPRequestHandler):
            def __init__(self, metrics_collector, *args, **kwargs):
                self.metrics_collector = metrics_collector
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == "/metrics":
                    metrics_data = generate_latest(self.metrics_collector.registry)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(metrics_data)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress HTTP server logs

        def handler_wrapper(*args, **kwargs):
            return MetricsHandler(self.metrics_collector, *args, **kwargs)

        def run_server():
            server = HTTPServer(("", self.metrics_port), handler_wrapper)
            server.serve_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        logger.info(f"DR metrics server started on port {self.metrics_port}")

    async def process_backup_event(self, event_data: dict[str, Any]) -> None:
        """Process backup event and update metrics.

        Args:
            event_data: Backup event data
        """
        component = event_data.get("component", "unknown")
        backup_type = event_data.get("type", "unknown")
        duration = event_data.get("duration_seconds", 0)
        size_bytes = event_data.get("size_bytes", 0)
        success = event_data.get("success", False)

        # Update metrics
        self.metrics_collector.record_backup_operation(
            component, backup_type, duration, size_bytes, success
        )

        # Send alert for backup failures
        if not success:
            await self.alert_manager.send_dr_alert(
                "backup_failure",
                "high",
                f"Backup failed for {component} ({backup_type})",
                event_data,
            )

        # Update dashboard
        if self.dashboard_integration:
            status_data = {
                "component": "backup",
                "status": "success" if success else "failure",
                "last_backup": datetime.now().isoformat(),
                "details": event_data,
            }
            await self.dashboard_integration.update_dr_status(status_data)

    async def process_recovery_event(self, event_data: dict[str, Any]) -> None:
        """Process recovery event and update metrics.

        Args:
            event_data: Recovery event data
        """
        recovery_type = event_data.get("type", "unknown")
        duration = event_data.get("duration_seconds", 0)
        success = event_data.get("success", False)

        # Update metrics
        self.metrics_collector.record_recovery_operation(
            recovery_type, duration, success
        )

        # Send alert for recovery operations
        severity = "medium" if success else "critical"
        message = (
            f"Recovery operation {recovery_type}: {'SUCCESS' if success else 'FAILED'}"
        )

        await self.alert_manager.send_dr_alert(
            "recovery_operation", severity, message, event_data
        )

        # Create incident if recovery failed
        if not success and self.dashboard_integration:
            incident_data = {
                "title": f"DR Recovery Failed: {recovery_type}",
                "description": f"Recovery operation failed after {duration} seconds",
                "severity": "critical",
                "component": "disaster_recovery",
                "details": event_data,
            }
            incident_id = await self.dashboard_integration.create_dr_incident(
                incident_data
            )
            if incident_id:
                self.active_incidents[incident_id] = incident_data

    async def process_corruption_event(self, event_data: dict[str, Any]) -> None:
        """Process data corruption event and update metrics.

        Args:
            event_data: Corruption event data
        """
        table = event_data.get("table", "unknown")
        corruption_type = event_data.get("corruption_type", "unknown")
        severity = event_data.get("severity", "medium")
        quality_score = event_data.get("quality_score", 1.0)

        # Update metrics
        self.metrics_collector.record_data_corruption_alert(
            table, corruption_type, severity
        )
        self.metrics_collector.update_data_quality_score(table, quality_score)

        # Send alert for high severity corruption
        if severity in ["high", "critical"]:
            await self.alert_manager.send_dr_alert(
                "data_corruption",
                severity,
                f"Data corruption detected in {table}: {corruption_type}",
                event_data,
            )

    async def process_failover_event(self, event_data: dict[str, Any]) -> None:
        """Process failover event and update metrics.

        Args:
            event_data: Failover event data
        """
        failover_type = event_data.get("type", "unknown")
        duration = event_data.get("duration_seconds", 0)
        success = event_data.get("success", False)

        # Update metrics
        self.metrics_collector.record_failover_operation(
            failover_type, duration, success
        )

        # Send alert for all failover operations
        severity = "high" if success else "critical"
        message = (
            f"Failover operation {failover_type}: {'SUCCESS' if success else 'FAILED'}"
        )

        await self.alert_manager.send_dr_alert(
            "failover_operation", severity, message, event_data
        )

    async def process_test_event(self, event_data: dict[str, Any]) -> None:
        """Process DR test event and update metrics.

        Args:
            event_data: Test event data
        """
        test_type = event_data.get("test_type", "unknown")
        duration = event_data.get("duration_seconds", 0)
        success = event_data.get("success", False)
        success_rate = event_data.get("success_rate", 1.0 if success else 0.0)

        # Update metrics
        self.metrics_collector.record_dr_test(test_type, duration, success)
        self.metrics_collector.update_test_success_rate(test_type, success_rate)

        # Send alert for test failures
        if not success:
            await self.alert_manager.send_dr_alert(
                "dr_test_failure", "medium", f"DR test failed: {test_type}", event_data
            )

    async def update_system_health(self, health_data: dict[str, Any]) -> None:
        """Update overall system health metrics.

        Args:
            health_data: System health data
        """
        for service, health_score in health_data.items():
            self.metrics_collector.update_service_health_score(service, health_score)

        # Update dashboard with overall status
        if self.dashboard_integration:
            status_data = {
                "component": "system_health",
                "timestamp": datetime.now().isoformat(),
                "health_scores": health_data,
            }
            await self.dashboard_integration.update_dr_status(status_data)

    async def start_monitoring(self) -> None:
        """Start DR monitoring service."""
        logger.info("Starting DR monitoring service")

        # Start metrics server
        await self.start_metrics_server()

        # Main monitoring loop would go here
        # This would typically integrate with your event system or message queue
        logger.info("DR monitoring service started successfully")


async def main():
    """Main entry point for DR monitoring service."""
    import argparse

    parser = argparse.ArgumentParser(description="DR Monitoring Integration Service")
    parser.add_argument(
        "--metrics-port", type=int, default=9091, help="Port for Prometheus metrics"
    )
    parser.add_argument(
        "--webhook-url",
        action="append",
        help="Webhook URL for alerts (can specify multiple)",
    )
    parser.add_argument("--slack-webhook", help="Slack webhook URL")
    parser.add_argument("--dashboard-api", help="Operations dashboard API URL")
    parser.add_argument("--dashboard-key", help="Operations dashboard API key")

    args = parser.parse_args()

    # Initialize monitoring service
    monitoring_service = DRMonitoringService(
        metrics_port=args.metrics_port,
        webhook_urls=args.webhook_url or [],
        slack_webhook=args.slack_webhook,
        dashboard_api_url=args.dashboard_api,
        dashboard_api_key=args.dashboard_key,
    )

    try:
        await monitoring_service.start_monitoring()

        # Keep service running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("DR monitoring service stopped by user")
    except Exception as e:
        logger.error(f"DR monitoring service failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
