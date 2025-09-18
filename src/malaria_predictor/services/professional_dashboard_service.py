"""
Professional Dashboard Service for Healthcare Professionals.

This module provides comprehensive dashboard services for healthcare professionals
including metrics aggregation, real-time updates, performance analytics, and
personalized insights for malaria prediction and case management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DashboardMetrics(BaseModel):
    """Dashboard metrics data model."""

    metric_id: str = Field(default_factory=lambda: str(uuid4()))
    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current metric value")
    previous_value: float | None = Field(None, description="Previous period value")
    trend: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    percentage_change: float | None = Field(None, description="Percentage change from previous period")
    target_value: float | None = Field(None, description="Target or goal value")
    unit: str = Field("count", description="Metric unit")
    category: str = Field(..., description="Metric category")
    updated_at: datetime = Field(default_factory=datetime.now)


class AlertSummary(BaseModel):
    """Dashboard alert summary model."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    action_required: str = Field(..., description="Required action")
    location: dict[str, Any] | None = Field(None, description="Alert location")
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = Field(False, description="Alert acknowledgment status")
    resolved: bool = Field(False, description="Alert resolution status")


class PerformanceInsight(BaseModel):
    """Performance insight data model."""

    insight_id: str = Field(default_factory=lambda: str(uuid4()))
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    impact_level: str = Field(..., description="Impact level (high, medium, low)")
    recommendation: str = Field(..., description="Recommended action")
    supporting_data: dict[str, Any] = Field(default_factory=dict, description="Supporting data")
    generated_at: datetime = Field(default_factory=datetime.now)
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")


class ProfessionalDashboardService:
    """
    Professional dashboard service for healthcare workers.

    Provides comprehensive dashboard functionality including metrics aggregation,
    real-time updates, performance analytics, and personalized insights.
    """

    def __init__(self):
        """Initialize professional dashboard service."""
        self.metrics_calculator = MetricsCalculator()
        self.alert_manager = DashboardAlertManager()
        self.insights_generator = InsightsGenerator()
        self.performance_tracker = PerformanceTracker()
        logger.info("Professional dashboard service initialized")

    async def get_dashboard_overview(
        self,
        healthcare_professional_id: str,
        time_period: str = "week",
        include_insights: bool = True
    ) -> dict[str, Any]:
        """
        Get comprehensive dashboard overview for healthcare professional.

        Args:
            healthcare_professional_id: Professional identifier
            time_period: Time period for metrics (day, week, month, quarter)
            include_insights: Whether to include performance insights

        Returns:
            Complete dashboard overview with metrics, alerts, and insights
        """
        logger.info(f"Generating dashboard overview for professional {healthcare_professional_id}")

        # Get professional information
        professional_info = await self._get_professional_info(healthcare_professional_id)

        # Calculate key metrics
        key_metrics = await self.metrics_calculator.calculate_key_metrics(
            healthcare_professional_id, time_period
        )

        # Get active alerts
        active_alerts = await self.alert_manager.get_active_alerts(
            healthcare_professional_id
        )

        # Get recent activities
        recent_activities = await self._get_recent_activities(
            healthcare_professional_id, limit=10
        )

        # Get pending tasks
        pending_tasks = await self._get_pending_tasks(healthcare_professional_id)

        # Generate performance insights if requested
        insights = []
        if include_insights:
            insights = await self.insights_generator.generate_insights(
                healthcare_professional_id, key_metrics, recent_activities
            )

        # Get area risk summary
        risk_summary = await self._get_area_risk_summary(
            professional_info.get("location", {})
        )

        # Performance metrics
        performance_metrics = await self.performance_tracker.get_performance_summary(
            healthcare_professional_id, time_period
        )

        dashboard = {
            "professional_info": professional_info,
            "key_metrics": key_metrics,
            "risk_summary": risk_summary,
            "alerts": active_alerts,
            "recent_activities": recent_activities,
            "pending_tasks": pending_tasks,
            "performance_metrics": performance_metrics,
            "insights": insights,
            "generated_at": datetime.now().isoformat(),
            "time_period": time_period
        }

        logger.info(f"Dashboard overview generated with {len(insights)} insights and {len(active_alerts)} alerts")
        return dashboard

    async def get_case_workload_summary(
        self,
        healthcare_professional_id: str,
        time_period: str = "week"
    ) -> dict[str, Any]:
        """
        Get detailed case workload summary.

        Args:
            healthcare_professional_id: Professional identifier
            time_period: Time period for analysis

        Returns:
            Detailed case workload analysis
        """
        logger.info(f"Generating case workload summary for {healthcare_professional_id}")

        # Calculate case statistics
        case_stats = await self._calculate_case_statistics(
            healthcare_professional_id, time_period
        )

        # Get case breakdown by type and risk
        case_breakdowns = await self._get_case_breakdowns(
            healthcare_professional_id, time_period
        )

        # Get geographic distribution
        geographic_distribution = await self._get_geographic_distribution(
            healthcare_professional_id, time_period
        )

        # Get treatment outcomes
        treatment_outcomes = await self._get_treatment_outcomes(
            healthcare_professional_id, time_period
        )

        # Calculate workload trends
        workload_trends = await self._calculate_workload_trends(
            healthcare_professional_id, time_period
        )

        workload_summary = {
            "time_period": time_period,
            "case_statistics": case_stats,
            "case_breakdown_by_type": case_breakdowns["by_type"],
            "case_breakdown_by_risk": case_breakdowns["by_risk"],
            "geographic_distribution": geographic_distribution,
            "treatment_outcomes": treatment_outcomes,
            "workload_trends": workload_trends,
            "generated_at": datetime.now().isoformat()
        }

        return workload_summary

    async def get_performance_analytics(
        self,
        healthcare_professional_id: str,
        time_period: str = "month"
    ) -> dict[str, Any]:
        """
        Get detailed performance analytics.

        Args:
            healthcare_professional_id: Professional identifier
            time_period: Time period for analysis

        Returns:
            Comprehensive performance analytics
        """
        logger.info(f"Generating performance analytics for {healthcare_professional_id}")

        # Get performance metrics over time
        performance_trends = await self.performance_tracker.get_performance_trends(
            healthcare_professional_id, time_period
        )

        # Calculate efficiency metrics
        efficiency_metrics = await self._calculate_efficiency_metrics(
            healthcare_professional_id, time_period
        )

        # Get quality indicators
        quality_indicators = await self._calculate_quality_indicators(
            healthcare_professional_id, time_period
        )

        # Compare with benchmarks
        benchmark_comparison = await self._compare_with_benchmarks(
            healthcare_professional_id, efficiency_metrics, quality_indicators
        )

        # Generate improvement recommendations
        improvement_recommendations = await self._generate_improvement_recommendations(
            performance_trends, efficiency_metrics, quality_indicators
        )

        analytics = {
            "performance_trends": performance_trends,
            "efficiency_metrics": efficiency_metrics,
            "quality_indicators": quality_indicators,
            "benchmark_comparison": benchmark_comparison,
            "improvement_recommendations": improvement_recommendations,
            "analysis_period": time_period,
            "generated_at": datetime.now().isoformat()
        }

        return analytics

    async def _get_professional_info(self, healthcare_professional_id: str) -> dict[str, Any]:
        """Get professional information."""
        # Mock professional info - in production, fetch from user database
        return {
            "id": healthcare_professional_id,
            "name": "Dr. Sarah Mwangi",
            "role": "doctor",
            "organization": "Nairobi General Hospital",
            "location": {
                "name": "Nairobi",
                "latitude": -1.2921,
                "longitude": 36.8219
            },
            "specialization": ["internal_medicine", "tropical_diseases"],
            "last_login": datetime.now().isoformat()
        }

    async def _get_recent_activities(
        self,
        healthcare_professional_id: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent professional activities."""
        # Mock recent activities - in production, fetch from activity log
        activities = [
            {
                "type": "risk_assessment",
                "description": "Completed risk assessment for patient P12345",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "outcome": "high_risk",
                "case_id": "case_12345"
            },
            {
                "type": "surveillance_report",
                "description": "Submitted weekly surveillance report",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "status": "exported_to_dhis2",
                "report_id": "report_54321"
            },
            {
                "type": "treatment_plan",
                "description": "Updated treatment plan for patient P67890",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "outcome": "protocol_updated",
                "case_id": "case_67890"
            }
        ]

        return activities[:limit]

    async def _get_pending_tasks(self, healthcare_professional_id: str) -> list[dict[str, Any]]:
        """Get pending tasks for professional."""
        # Mock pending tasks - in production, fetch from task management system
        return [
            {
                "type": "case_follow_up",
                "description": "Follow-up required for patient P12340",
                "due_date": (datetime.now() + timedelta(hours=8)).isoformat(),
                "priority": "high",
                "case_id": "case_12340"
            },
            {
                "type": "surveillance_report",
                "description": "Weekly surveillance report due",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "priority": "medium",
                "estimated_duration": "30 minutes"
            },
            {
                "type": "training_completion",
                "description": "Complete malaria case management training module",
                "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                "priority": "low",
                "estimated_duration": "2 hours"
            }
        ]

    async def _get_area_risk_summary(self, location: dict[str, Any]) -> dict[str, Any]:
        """Get area risk summary for professional's coverage area."""
        # Mock risk summary - in production, integrate with prediction API
        return {
            "area_risk_level": "medium",
            "area_risk_score": 0.58,
            "risk_trend": "increasing",
            "environmental_factors": {
                "temperature": "optimal_for_transmission",
                "rainfall": "above_average",
                "vector_activity": "high"
            },
            "recent_cases": {
                "suspected": 12,
                "confirmed": 8,
                "severe": 2
            },
            "forecast": {
                "next_week": "medium_risk",
                "next_month": "high_risk"
            }
        }

    async def _calculate_case_statistics(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, int]:
        """Calculate case statistics for time period."""
        # Mock case statistics - in production, query case database
        return {
            "total_active_cases": 15,
            "new_cases": 8,
            "resolved_cases": 12,
            "transferred_cases": 2,
            "cases_requiring_follow_up": 5
        }

    async def _get_case_breakdowns(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, dict[str, int]]:
        """Get case breakdowns by type and risk level."""
        return {
            "by_type": {
                "suspected": 8,
                "confirmed": 5,
                "severe": 2
            },
            "by_risk": {
                "low": 3,
                "medium": 6,
                "high": 4,
                "very_high": 2
            }
        }

    async def _get_geographic_distribution(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> list[dict[str, Any]]:
        """Get geographic distribution of cases."""
        return [
            {"location": "District A", "cases": 8, "risk_level": "high"},
            {"location": "District B", "cases": 4, "risk_level": "medium"},
            {"location": "District C", "cases": 3, "risk_level": "low"}
        ]

    async def _get_treatment_outcomes(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, int]:
        """Get treatment outcome statistics."""
        return {
            "successful_treatment": 10,
            "treatment_failure": 1,
            "lost_to_follow_up": 1,
            "ongoing_treatment": 3
        }

    async def _calculate_workload_trends(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, Any]:
        """Calculate workload trends over time."""
        return {
            "case_volume_trend": "increasing",
            "average_cases_per_day": 2.1,
            "peak_workload_day": "Wednesday",
            "seasonal_pattern": "wet_season_increase"
        }

    async def _calculate_efficiency_metrics(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, float]:
        """Calculate efficiency metrics."""
        return {
            "average_case_resolution_time_hours": 48.5,
            "assessment_completion_rate": 0.95,
            "follow_up_compliance_rate": 0.88,
            "documentation_completeness": 0.92,
            "response_time_hours": 4.2
        }

    async def _calculate_quality_indicators(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, float]:
        """Calculate quality indicators."""
        return {
            "diagnostic_accuracy": 0.94,
            "treatment_success_rate": 0.91,
            "patient_satisfaction_score": 4.6,
            "protocol_adherence_rate": 0.89,
            "adverse_event_rate": 0.02
        }

    async def _compare_with_benchmarks(
        self,
        healthcare_professional_id: str,
        efficiency_metrics: dict[str, float],
        quality_indicators: dict[str, float]
    ) -> dict[str, Any]:
        """Compare performance with benchmarks."""
        return {
            "efficiency_ranking": "above_average",
            "quality_ranking": "excellent",
            "peer_comparison": {
                "better_than_percent": 78,
                "areas_of_strength": ["diagnostic_accuracy", "patient_satisfaction"],
                "areas_for_improvement": ["response_time", "documentation"]
            },
            "benchmark_data": {
                "regional_average_resolution_time": 52.3,
                "national_average_success_rate": 0.87
            }
        }

    async def _generate_improvement_recommendations(
        self,
        performance_trends: dict[str, Any],
        efficiency_metrics: dict[str, float],
        quality_indicators: dict[str, float]
    ) -> list[dict[str, Any]]:
        """Generate performance improvement recommendations."""
        return [
            {
                "area": "Response Time",
                "current_performance": efficiency_metrics.get("response_time_hours", 0),
                "target_performance": 3.0,
                "recommendation": "Implement mobile alerts for urgent cases",
                "expected_impact": "30% faster response times",
                "priority": "high"
            },
            {
                "area": "Documentation",
                "current_performance": efficiency_metrics.get("documentation_completeness", 0),
                "target_performance": 0.98,
                "recommendation": "Use voice-to-text for faster note-taking",
                "expected_impact": "Improved documentation quality",
                "priority": "medium"
            }
        ]


class MetricsCalculator:
    """Calculator for dashboard metrics and KPIs."""

    async def calculate_key_metrics(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, DashboardMetrics]:
        """Calculate key dashboard metrics."""
        logger.debug(f"Calculating key metrics for {healthcare_professional_id}")

        metrics = {}

        # Active cases metric
        active_cases = DashboardMetrics(
            metric_name="Active Cases",
            current_value=15,
            previous_value=12,
            trend="increasing",
            percentage_change=25.0,
            target_value=20,
            unit="cases",
            category="workload"
        )
        metrics["active_cases"] = active_cases

        # New cases today metric
        new_cases_today = DashboardMetrics(
            metric_name="New Cases Today",
            current_value=3,
            previous_value=2,
            trend="increasing",
            percentage_change=50.0,
            unit="cases",
            category="activity"
        )
        metrics["new_cases_today"] = new_cases_today

        # High risk assessments metric
        high_risk_assessments = DashboardMetrics(
            metric_name="High Risk Assessments",
            current_value=5,
            previous_value=3,
            trend="increasing",
            percentage_change=66.7,
            unit="assessments",
            category="risk"
        )
        metrics["high_risk_assessments"] = high_risk_assessments

        # Treatment success rate metric
        treatment_success_rate = DashboardMetrics(
            metric_name="Treatment Success Rate",
            current_value=91.0,
            previous_value=88.0,
            trend="increasing",
            percentage_change=3.4,
            target_value=95.0,
            unit="percent",
            category="quality"
        )
        metrics["treatment_success_rate"] = treatment_success_rate

        # Average resolution time metric
        avg_resolution_time = DashboardMetrics(
            metric_name="Average Resolution Time",
            current_value=48.5,
            previous_value=52.3,
            trend="decreasing",
            percentage_change=-7.3,
            target_value=36.0,
            unit="hours",
            category="efficiency"
        )
        metrics["avg_resolution_time"] = avg_resolution_time

        return metrics


class DashboardAlertManager:
    """Manager for dashboard alerts and notifications."""

    async def get_active_alerts(
        self,
        healthcare_professional_id: str
    ) -> list[AlertSummary]:
        """Get active alerts for healthcare professional."""
        logger.debug(f"Getting active alerts for {healthcare_professional_id}")

        # Mock alerts - in production, fetch from alert system
        alerts = [
            AlertSummary(
                alert_type="outbreak_risk",
                severity="high",
                title="Outbreak Risk Alert",
                message="Increased case clustering detected in northern district",
                action_required="Conduct outbreak investigation",
                location={"name": "Northern District", "cases": 8}
            ),
            AlertSummary(
                alert_type="resource_shortage",
                severity="medium",
                title="Resource Shortage",
                message="RDT stock running low (3 days remaining)",
                action_required="Submit resupply request"
            ),
            AlertSummary(
                alert_type="follow_up_overdue",
                severity="medium",
                title="Follow-up Overdue",
                message="3 patients have overdue follow-up appointments",
                action_required="Schedule follow-up visits"
            )
        ]

        return alerts


class InsightsGenerator:
    """Generator for performance insights and recommendations."""

    async def generate_insights(
        self,
        healthcare_professional_id: str,
        metrics: dict[str, DashboardMetrics],
        activities: list[dict[str, Any]]
    ) -> list[PerformanceInsight]:
        """Generate performance insights based on metrics and activities."""
        logger.debug(f"Generating insights for {healthcare_professional_id}")

        insights = []

        # Workload insight
        if metrics.get("active_cases") and metrics["active_cases"].current_value > 15:
            insights.append(PerformanceInsight(
                insight_type="workload_management",
                title="High Case Volume Detected",
                description="Your current case load is 25% higher than last period",
                impact_level="medium",
                recommendation="Consider requesting additional support or prioritizing high-risk cases",
                supporting_data={"current_cases": metrics["active_cases"].current_value},
                relevance_score=0.85
            ))

        # Performance improvement insight
        if metrics.get("treatment_success_rate") and metrics["treatment_success_rate"].current_value > 90:
            insights.append(PerformanceInsight(
                insight_type="performance_achievement",
                title="Excellent Treatment Success Rate",
                description="Your treatment success rate of 91% exceeds the regional average",
                impact_level="high",
                recommendation="Share best practices with colleagues to maintain high standards",
                supporting_data={"success_rate": metrics["treatment_success_rate"].current_value},
                relevance_score=0.92
            ))

        # Efficiency insight
        recent_assessments = len([a for a in activities if a["type"] == "risk_assessment"])
        if recent_assessments > 5:
            insights.append(PerformanceInsight(
                insight_type="efficiency_optimization",
                title="High Assessment Activity",
                description="You've completed multiple risk assessments recently",
                impact_level="medium",
                recommendation="Consider batch processing assessments to improve efficiency",
                supporting_data={"recent_assessments": recent_assessments},
                relevance_score=0.78
            ))

        return insights


class PerformanceTracker:
    """Tracker for professional performance metrics and trends."""

    async def get_performance_summary(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, Any]:
        """Get performance summary for time period."""
        return {
            "cases_managed_this_period": 45,
            "average_case_resolution_days": 2.1,
            "surveillance_reporting_compliance": 0.95,
            "patient_satisfaction_score": 4.6,
            "professional_development_hours": 8,
            "quality_score": 0.89
        }

    async def get_performance_trends(
        self,
        healthcare_professional_id: str,
        time_period: str
    ) -> dict[str, Any]:
        """Get performance trends over time."""
        return {
            "case_resolution_trend": "improving",
            "quality_score_trend": "stable",
            "efficiency_trend": "improving",
            "workload_trend": "increasing",
            "satisfaction_trend": "stable"
        }


# Global dashboard service instance
professional_dashboard_service = ProfessionalDashboardService()
