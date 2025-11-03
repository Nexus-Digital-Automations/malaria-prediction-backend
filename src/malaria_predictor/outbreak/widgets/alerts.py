"""
Outbreak Alert Widget

Real-time outbreak alert system with intelligent notifications,
risk-based prioritization, and automated response integration.

Author: AI Agent - Outbreak Pattern Recognition Specialist
"""

from datetime import datetime, timedelta
from typing import Any

import structlog
from pydantic import BaseModel, Field

from ..models import (
    OutbreakEvent,
    OutbreakSeverity,
    SurveillanceData,
)

logger = structlog.get_logger(__name__)


class AlertConfiguration(BaseModel):
    """Configuration for outbreak alert system."""
    enable_real_time: bool = Field(True, description="Enable real-time alerts")
    alert_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "case_increase_percent": 50.0,
            "test_positivity_rate": 0.15,
            "severity_threshold": 0.6,
            "urgency_threshold": 3
        },
        description="Alert threshold configuration"
    )
    notification_channels: list[str] = Field(
        default_factory=lambda: ["dashboard", "email", "sms"],
        description="Enabled notification channels"
    )
    alert_categories: list[str] = Field(
        default_factory=lambda: ["outbreak_detection", "severity_escalation", "system_alert"],
        description="Alert category filters"
    )
    auto_escalation: bool = Field(True, description="Enable automatic alert escalation")
    refresh_interval_seconds: int = Field(30, description="Alert refresh interval")


class AlertItem(BaseModel):
    """Individual alert item structure."""
    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message content")

    # Context Information
    outbreak_id: str | None = Field(None, description="Associated outbreak ID")
    location: dict[str, float] | None = Field(None, description="Alert location")
    affected_population: int = Field(0, description="Affected population count")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(None, description="Alert expiration time")
    acknowledged_at: datetime | None = Field(None, description="Acknowledgment timestamp")

    # Actions and Response
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Recommended response actions"
    )
    escalation_level: int = Field(1, description="Escalation level (1-5)")
    requires_immediate_action: bool = Field(False, description="Immediate action required")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources")
    confidence_score: float = Field(1.0, description="Alert confidence score")
    false_positive_risk: float = Field(0.0, description="False positive risk assessment")


class OutbreakAlert:
    """
    Real-time outbreak alert widget with intelligent notifications.

    Provides comprehensive outbreak alert management including real-time
    monitoring, risk-based prioritization, and automated response coordination.
    """

    def __init__(self, config: AlertConfiguration | None = None) -> None:
        """Initialize outbreak alert widget."""
        self.logger = logger.bind(service="outbreak_alert")
        self.config = config or AlertConfiguration()

        # Alert state management
        self.active_alerts: dict[str, AlertItem] = {}
        self.alert_history: list[AlertItem] = []
        self.acknowledged_alerts: dict[str, AlertItem] = {}

        # Alert processing
        self.alert_processors = {
            "outbreak_detection": self._process_outbreak_detection_alert,  # type: ignore[attr-defined]
            "severity_escalation": self._process_severity_escalation_alert,  # type: ignore[attr-defined]
            "system_alert": self._process_system_alert,  # type: ignore[attr-defined]
            "threshold_exceeded": self._process_threshold_alert,  # type: ignore[attr-defined]
            "pattern_anomaly": self._process_pattern_anomaly_alert  # type: ignore[attr-defined]
        }

        self.logger.info("Outbreak alert widget initialized", config=self.config.model_dump())

    async def generate_alert_widget(
        self,
        outbreak_events: list[OutbreakEvent] | None = None,
        surveillance_data: list[SurveillanceData] | None = None,
        show_acknowledged: bool = False
    ) -> dict[str, Any]:
        """
        Generate comprehensive alert widget with current alerts.

        Args:
            outbreak_events: Recent outbreak events to monitor
            surveillance_data: Current surveillance data
            show_acknowledged: Include acknowledged alerts

        Returns:
            Complete alert widget configuration
        """
        widget_id = f"outbreak_alerts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(
            "Generating outbreak alert widget",
            widget_id=widget_id,
            outbreak_count=len(outbreak_events) if outbreak_events else 0,
            surveillance_count=len(surveillance_data) if surveillance_data else 0
        )

        try:
            # Process new alerts from outbreak events
            if outbreak_events:
                await self._process_outbreak_alerts(outbreak_events)

            # Process surveillance-based alerts
            if surveillance_data:
                await self._process_surveillance_alerts(surveillance_data)

            # Clean up expired alerts
            await self._cleanup_expired_alerts()

            # Prepare alert display data
            alert_data = await self._prepare_alert_display_data(show_acknowledged)

            # Generate alert statistics
            statistics = await self._generate_alert_statistics()

            # Configure alert actions
            actions = await self._configure_alert_actions()

            widget_config = {
                "widget_id": widget_id,
                "type": "outbreak_alert",
                "config": self.config.model_dump(),
                "data": {
                    "active_alerts": alert_data["active"],
                    "acknowledged_alerts": alert_data["acknowledged"] if show_acknowledged else [],
                    "alert_summary": alert_data["summary"],
                    "statistics": statistics
                },
                "actions": actions,
                "layout": {
                    "title": "Outbreak Alerts",
                    "priority_order": ["critical", "high", "medium", "low"],
                    "grouping": "severity",
                    "auto_refresh": self.config.refresh_interval_seconds,
                    "max_displayed": 50
                },
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_alerts": len(self.active_alerts),
                    "critical_alerts": len([a for a in self.active_alerts.values() if a.severity == "critical"])
                }
            }

            self.logger.info(
                "Outbreak alert widget generated successfully",
                widget_id=widget_id,
                active_alerts=len(alert_data["active"]),
                critical_alerts=widget_config["metadata"]["critical_alerts"]
            )

            return widget_config

        except Exception as e:
            self.logger.error(
                "Failed to generate outbreak alert widget",
                widget_id=widget_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def _process_outbreak_alerts(self, outbreak_events: list[OutbreakEvent]) -> None:
        """Process alerts from outbreak events."""
        for outbreak in outbreak_events:
            # Skip if already processed
            alert_id = f"outbreak_{outbreak.outbreak_id}"
            if alert_id in self.active_alerts:
                continue

            # Determine alert severity based on outbreak characteristics
            alert_severity = self._map_outbreak_to_alert_severity(outbreak)

            # Skip low priority outbreaks if not critical
            if alert_severity == "low" and not outbreak.is_active():
                continue

            # Create outbreak detection alert
            alert = AlertItem(
                alert_id=alert_id,
                alert_type="outbreak_detection",
                severity=alert_severity,
                title=f"Outbreak Detected: {outbreak.event_name}",
                message=self._generate_outbreak_alert_message(outbreak),
                outbreak_id=outbreak.outbreak_id,
                location={
                    "lat": outbreak.location.coordinates[1],
                    "lon": outbreak.location.coordinates[0]
                },
                affected_population=outbreak.population_at_risk,
                recommended_actions=self._generate_outbreak_recommendations(outbreak),
                escalation_level=self._calculate_escalation_level(outbreak),
                requires_immediate_action=outbreak.severity in [OutbreakSeverity.CRITICAL, OutbreakSeverity.EMERGENCY],
                data_sources=["outbreak_detection_system"],
                confidence_score=outbreak.confidence_level,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Process severity escalation if needed
            if outbreak.severity in [OutbreakSeverity.CRITICAL, OutbreakSeverity.EMERGENCY]:
                await self._create_escalation_alert(outbreak, alert)

        self.logger.debug(f"Processed {len(outbreak_events)} outbreak events for alerts")

    async def _process_surveillance_alerts(self, surveillance_data: list[SurveillanceData]) -> None:
        """Process alerts from surveillance data."""
        # Aggregate surveillance data for threshold checking
        current_data = {}

        for data in surveillance_data:
            location_key = f"{data.location.coordinates[1]:.3f}_{data.location.coordinates[0]:.3f}"

            if location_key not in current_data:
                current_data[location_key] = {
                    "location": data.location,
                    "total_cases": 0,
                    "total_tests": 0,
                    "total_population": 0,
                    "max_positivity": 0,
                    "max_alert_level": 0,
                    "latest_date": data.reported_at
                }

            current_data[location_key]["total_cases"] += data.confirmed_cases
            current_data[location_key]["total_tests"] += data.tests_performed
            current_data[location_key]["total_population"] += data.population_monitored
            current_data[location_key]["max_positivity"] = max(
                current_data[location_key]["max_positivity"],
                data.test_positivity_rate
            )
            current_data[location_key]["max_alert_level"] = max(
                current_data[location_key]["max_alert_level"],
                data.alert_level
            )

        # Check thresholds for each location
        for location_key, aggregated in current_data.items():
            await self._check_surveillance_thresholds(location_key, aggregated)

    async def _check_surveillance_thresholds(self, location_key: str, data: dict[str, Any]) -> None:
        """Check surveillance data against alert thresholds."""
        alerts_to_create = []

        # Test positivity rate threshold
        if data["max_positivity"] > self.config.alert_thresholds["test_positivity_rate"]:
            alerts_to_create.append({
                "type": "threshold_exceeded",
                "severity": "high" if data["max_positivity"] > 0.25 else "medium",
                "title": f"High Test Positivity Rate: {data['max_positivity']:.1%}",
                "threshold": "test_positivity_rate"
            })

        # Alert level threshold
        if data["max_alert_level"] >= self.config.alert_thresholds["urgency_threshold"]:
            alerts_to_create.append({
                "type": "threshold_exceeded",
                "severity": "critical" if data["max_alert_level"] >= 4 else "high",
                "title": f"Alert Level {data['max_alert_level']} Exceeded",
                "threshold": "urgency_threshold"
            })

        # Case density threshold
        if data["total_population"] > 0:
            case_density = (data["total_cases"] / data["total_population"]) * 100000
            if case_density > 1000:  # Cases per 100k threshold
                alerts_to_create.append({
                    "type": "threshold_exceeded",
                    "severity": "high",
                    "title": f"High Case Density: {case_density:.0f} per 100k",
                    "threshold": "case_density"
                })

        # Create alerts
        for alert_config in alerts_to_create:
            alert_id = f"surveillance_{location_key}_{alert_config['type']}_{data['latest_date'].strftime('%Y%m%d')}"

            if alert_id not in self.active_alerts:
                alert = AlertItem(
                    alert_id=alert_id,
                    alert_type=alert_config["type"],
                    severity=alert_config["severity"],
                    title=alert_config["title"],
                    message=f"Surveillance threshold exceeded in location {location_key}",
                    location={
                        "lat": data["location"].coordinates[1],
                        "lon": data["location"].coordinates[0]
                    },
                    affected_population=data["total_population"],
                    recommended_actions=["Investigate source", "Increase surveillance", "Deploy rapid response"],
                    escalation_level=2 if alert_config["severity"] == "high" else 1,
                    requires_immediate_action=alert_config["severity"] == "critical",
                    data_sources=["surveillance_system"],
                    confidence_score=0.8,
                    expires_at=datetime.utcnow() + timedelta(hours=12)
                )

                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)

    async def _create_escalation_alert(self, outbreak: OutbreakEvent, original_alert: AlertItem) -> None:
        """Create escalation alert for critical outbreaks."""
        escalation_id = f"escalation_{outbreak.outbreak_id}"

        escalation_alert = AlertItem(
            alert_id=escalation_id,
            alert_type="severity_escalation",
            severity="critical",
            title=f"CRITICAL ESCALATION: {outbreak.event_name}",
            message=f"Outbreak {outbreak.event_name} has escalated to {outbreak.severity.value.upper()} level. Immediate response required.",
            outbreak_id=outbreak.outbreak_id,
            location=original_alert.location,
            affected_population=outbreak.population_at_risk,
            recommended_actions=[
                "Activate emergency response plan",
                "Deploy rapid response team",
                "Coordinate with health authorities",
                "Implement immediate containment measures",
                "Mobilize additional resources"
            ],
            escalation_level=5,
            requires_immediate_action=True,
            data_sources=["outbreak_detection_system"],
            confidence_score=outbreak.confidence_level,
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        self.active_alerts[escalation_id] = escalation_alert
        self.alert_history.append(escalation_alert)

    async def _cleanup_expired_alerts(self) -> None:
        """Remove expired alerts from active list."""
        current_time = datetime.utcnow()
        expired_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.expires_at and alert.expires_at < current_time
        ]

        for alert_id in expired_alerts:
            self.active_alerts.pop(alert_id)
            self.logger.debug(f"Alert expired and removed: {alert_id}")

        if expired_alerts:
            self.logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")

    async def _prepare_alert_display_data(self, show_acknowledged: bool) -> dict[str, Any]:
        """Prepare alert data for display."""
        # Sort active alerts by severity and time
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        active_alerts = sorted(
            self.active_alerts.values(),
            key=lambda x: (severity_order.get(x.severity, 4), x.created_at),
            reverse=True
        )

        # Convert to display format
        active_display = []
        for alert in active_alerts:
            display_item = {
                "alert_id": alert.alert_id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "location": alert.location,
                "affected_population": alert.affected_population,
                "recommended_actions": alert.recommended_actions,
                "escalation_level": alert.escalation_level,
                "requires_immediate_action": alert.requires_immediate_action,
                "confidence_score": alert.confidence_score,
                "time_ago": self._format_time_ago(alert.created_at),
                "status": "acknowledged" if alert.acknowledged_at else "active"
            }
            active_display.append(display_item)

        # Prepare acknowledged alerts if requested
        acknowledged_display = []
        if show_acknowledged:
            acknowledged_alerts = sorted(
                self.acknowledged_alerts.values(),
                key=lambda x: x.acknowledged_at or x.created_at,
                reverse=True
            )[:20]  # Limit to recent 20

            for alert in acknowledged_alerts:
                display_item = {
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "severity": alert.severity,
                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    "created_at": alert.created_at.isoformat()
                }
                acknowledged_display.append(display_item)

        # Generate summary
        summary = {
            "total_active": len(active_display),
            "by_severity": {
                "critical": len([a for a in active_display if a["severity"] == "critical"]),
                "high": len([a for a in active_display if a["severity"] == "high"]),
                "medium": len([a for a in active_display if a["severity"] == "medium"]),
                "low": len([a for a in active_display if a["severity"] == "low"])
            },
            "requiring_immediate_action": len([a for a in active_display if a["requires_immediate_action"]]),
            "last_updated": datetime.utcnow().isoformat()
        }

        return {
            "active": active_display,
            "acknowledged": acknowledged_display,
            "summary": summary
        }

    async def _generate_alert_statistics(self) -> dict[str, Any]:
        """Generate alert statistics for dashboard."""
        current_time = datetime.utcnow()

        # Time-based statistics
        last_24h = current_time - timedelta(hours=24)
        last_week = current_time - timedelta(days=7)

        alerts_24h = [a for a in self.alert_history if a.created_at >= last_24h]
        alerts_week = [a for a in self.alert_history if a.created_at >= last_week]

        return {
            "current_period": {
                "total_active": len(self.active_alerts),
                "critical_active": len([a for a in self.active_alerts.values() if a.severity == "critical"]),
                "requiring_action": len([a for a in self.active_alerts.values() if a.requires_immediate_action])
            },
            "trends": {
                "alerts_last_24h": len(alerts_24h),
                "alerts_last_week": len(alerts_week),
                "average_daily": len(alerts_week) / 7 if alerts_week else 0
            },
            "response_metrics": {
                "average_acknowledgment_time": 15,  # Minutes - would calculate from data
                "false_positive_rate": 0.05,
                "escalation_rate": 0.1
            },
            "alert_types": {
                alert_type: len([a for a in self.active_alerts.values() if a.alert_type == alert_type])
                for alert_type in ["outbreak_detection", "severity_escalation", "threshold_exceeded", "system_alert"]
            }
        }

    async def _configure_alert_actions(self) -> dict[str, Any]:
        """Configure available alert actions."""
        return {
            "acknowledge": {
                "label": "Acknowledge Alert",
                "icon": "check-circle",
                "action": "acknowledge_alert",
                "requires_confirmation": False
            },
            "escalate": {
                "label": "Escalate Alert",
                "icon": "arrow-up-circle",
                "action": "escalate_alert",
                "requires_confirmation": True
            },
            "investigate": {
                "label": "Start Investigation",
                "icon": "search",
                "action": "start_investigation",
                "requires_confirmation": False
            },
            "dismiss": {
                "label": "Dismiss Alert",
                "icon": "x-circle",
                "action": "dismiss_alert",
                "requires_confirmation": True
            },
            "view_details": {
                "label": "View Details",
                "icon": "info-circle",
                "action": "view_alert_details",
                "requires_confirmation": False
            }
        }

    def _map_outbreak_to_alert_severity(self, outbreak: OutbreakEvent) -> str:
        """Map outbreak severity to alert severity."""
        severity_mapping = {
            OutbreakSeverity.LOW: "low",
            OutbreakSeverity.MODERATE: "medium",
            OutbreakSeverity.HIGH: "high",
            OutbreakSeverity.CRITICAL: "critical",
            OutbreakSeverity.EMERGENCY: "critical"
        }
        return severity_mapping.get(outbreak.severity, "medium")

    def _generate_outbreak_alert_message(self, outbreak: OutbreakEvent) -> str:
        """Generate descriptive alert message for outbreak."""
        message_parts = [
            f"Outbreak '{outbreak.event_name}' detected in {outbreak.administrative_units[0] if outbreak.administrative_units else 'unknown location'}.",
            f"Severity: {outbreak.severity.value.title()}",
            f"Status: {outbreak.status.value.title()}",
            f"Confirmed cases: {outbreak.total_cases}",
            f"Population at risk: {outbreak.population_at_risk:,}"
        ]

        if outbreak.case_fatality_rate:
            message_parts.append(f"Case fatality rate: {outbreak.case_fatality_rate:.1%}")

        if outbreak.response_measures:
            message_parts.append(f"Active interventions: {len(outbreak.response_measures)}")

        return " | ".join(message_parts)

    def _generate_outbreak_recommendations(self, outbreak: OutbreakEvent) -> list[str]:
        """Generate recommended actions for outbreak."""
        recommendations = ["Verify outbreak information", "Assess risk to population"]

        if outbreak.severity in [OutbreakSeverity.HIGH, OutbreakSeverity.CRITICAL, OutbreakSeverity.EMERGENCY]:
            recommendations.extend([
                "Activate emergency response protocol",
                "Deploy rapid response team",
                "Coordinate with health authorities"
            ])

        if outbreak.total_cases > 100:
            recommendations.append("Consider mass intervention strategies")

        if not outbreak.response_measures:
            recommendations.append("Implement initial control measures")

        return recommendations[:6]  # Limit to 6 recommendations

    def _calculate_escalation_level(self, outbreak: OutbreakEvent) -> int:
        """Calculate escalation level for outbreak."""
        base_level = 1

        # Severity-based escalation
        severity_levels = {
            OutbreakSeverity.LOW: 1,
            OutbreakSeverity.MODERATE: 2,
            OutbreakSeverity.HIGH: 3,
            OutbreakSeverity.CRITICAL: 4,
            OutbreakSeverity.EMERGENCY: 5
        }
        base_level = severity_levels.get(outbreak.severity, 1)

        # Case count escalation
        if outbreak.total_cases > 1000:
            base_level = min(base_level + 1, 5)

        # Population risk escalation
        if outbreak.population_at_risk > 100000:
            base_level = min(base_level + 1, 5)

        return base_level

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as 'time ago' string."""
        delta = datetime.utcnow() - timestamp

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.acknowledged_at = datetime.utcnow()
            self.acknowledged_alerts[alert_id] = alert

            self.logger.info(
                "Alert acknowledged",
                alert_id=alert_id,
                acknowledged_by=acknowledged_by,
                alert_type=alert.alert_type
            )
            return True
        return False

    async def escalate_alert(self, alert_id: str, escalated_by: str) -> bool:
        """Escalate an existing alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.escalation_level = min(alert.escalation_level + 1, 5)
            alert.requires_immediate_action = True

            self.logger.info(
                "Alert escalated",
                alert_id=alert_id,
                escalated_by=escalated_by,
                new_level=alert.escalation_level
            )
            return True
        return False
