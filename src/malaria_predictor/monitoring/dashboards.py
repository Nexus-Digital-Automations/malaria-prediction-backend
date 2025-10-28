"""
Grafana Dashboard Configuration and Management.

This module provides configuration and utilities for managing Grafana dashboards
and alerting rules for the malaria prediction system monitoring.
"""

import json
from pathlib import Path
from typing import Any


class DashboardConfig:
    """Configuration class for Grafana dashboards and alerts."""

    def __init__(self) -> None:
        self.config_path = Path(__file__).parent / "grafana_dashboards_config.json"

    def load_config(self) -> dict[str, Any]:
        """Load dashboard configuration from JSON file."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"dashboards": [], "alerts": []}

    def get_dashboards(self) -> list[dict[str, Any]]:
        """Get list of dashboard configurations."""
        config = self.load_config()
        return config.get("dashboards", [])

    def get_alerts(self) -> list[dict[str, Any]]:
        """Get list of alert configurations."""
        config = self.load_config()
        return config.get("alerts", [])

    def export_prometheus_rules(self) -> str:
        """Export alert rules in Prometheus format."""
        alerts = self.get_alerts()

        rules = {"groups": [{"name": "malaria_prediction_api_alerts", "rules": []}]}

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


# Global dashboard config instance
_dashboard_config: DashboardConfig | None = None


def get_dashboard_config() -> DashboardConfig:
    """Get the global dashboard config instance."""
    global _dashboard_config
    if _dashboard_config is None:
        _dashboard_config = DashboardConfig()
    return _dashboard_config
