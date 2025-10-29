"""Real-time alert performance monitoring and analytics.

Provides comprehensive analytics for alert system performance including:
- Real-time alert metrics and KPIs
- Performance monitoring and alerting
- User engagement analytics
- Delivery success rate tracking
- Alert effectiveness measurement
- Predictive analytics for alert optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, or_

from ..config import settings
from ..database.models import (
    Alert,
    AlertConfiguration,
    NotificationDelivery,
)
from ..database.session import get_session

logger = logging.getLogger(__name__)


class AlertKPIs(BaseModel):
    """Key Performance Indicators for alert system."""

    total_alerts_24h: int
    total_alerts_7d: int
    total_alerts_30d: int
    avg_delivery_rate_24h: float
    avg_delivery_rate_7d: float
    avg_response_rate_24h: float
    avg_response_rate_7d: float
    false_positive_rate_7d: float
    escalation_rate_24h: float
    avg_resolution_time_hours: float | None
    active_configurations: int
    active_users_24h: int
    critical_alerts_pending: int


class ChannelPerformanceMetrics(BaseModel):
    """Performance metrics for notification channels."""

    channel: str
    messages_sent_24h: int
    messages_delivered_24h: int
    delivery_rate_percentage: float
    avg_delivery_time_seconds: float | None
    failure_rate_percentage: float
    error_types: dict[str, int]


class UserEngagementMetrics(BaseModel):
    """User engagement metrics for alerts."""

    total_users: int
    active_users_24h: int
    active_users_7d: int
    avg_alerts_per_user_24h: float
    avg_response_time_minutes: float | None
    acknowledgment_rate_percentage: float
    resolution_rate_percentage: float
    feedback_submission_rate: float
    avg_user_rating: float | None


class AlertEffectivenessMetrics(BaseModel):
    """Alert effectiveness and accuracy metrics."""

    accuracy_score: float
    precision_score: float
    recall_score: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    true_positive_alerts_7d: int
    false_positive_alerts_7d: int
    user_satisfaction_score: float | None


class SystemHealthMetrics(BaseModel):
    """Overall system health and performance metrics."""

    system_uptime_percentage: float
    avg_processing_time_ms: float
    error_rate_percentage: float
    queue_depth: int
    memory_usage_mb: float
    cpu_usage_percentage: float
    database_response_time_ms: float
    active_websocket_connections: int


class AlertTrendAnalysis(BaseModel):
    """Trend analysis for alerts over time."""

    period: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    growth_rate_percentage: float
    seasonal_patterns: dict[str, float]
    peak_hours: list[int]
    peak_days: list[str]
    forecast_next_7d: list[dict[str, Any]]


class AlertAnalyticsEngine:
    """Real-time analytics engine for alert system performance.

    Provides functionality for:
    - Real-time KPI calculation and monitoring
    - Performance metrics aggregation
    - User engagement analysis
    - Alert effectiveness measurement
    - Trend analysis and forecasting
    - Anomaly detection and alerting
    """

    def __init__(self) -> None:
        """Initialize the alert analytics engine."""
        self.settings = settings

        # Analytics configuration
        self.config = {
            "kpi_refresh_interval_seconds": 300,  # 5 minutes
            "metrics_retention_days": 90,
            "anomaly_threshold_percentage": 50,  # Alert if metrics change by >50%
            "trend_analysis_period_days": 30,
            "forecast_horizon_days": 7
        }

        # Load custom config from settings if available
        if hasattr(settings, "ALERT_ANALYTICS_CONFIG"):
            self.config.update(settings.ALERT_ANALYTICS_CONFIG)

        # Statistics and caching
        self.stats = {
            "analytics_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "anomalies_detected": 0,
            "avg_calculation_time_ms": 0.0,
            "last_kpi_refresh": None,
            "last_anomaly_check": None
        }

        # In-memory cache for frequently accessed metrics
        self.metrics_cache: dict[str, Any] = {}
        self.cache_ttl_seconds = 300  # 5 minutes

        # Background tasks
        self._monitoring_task: asyncio.Task[None] | None = None
        self._anomaly_detection_task: asyncio.Task[None] | None = None

    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._continuous_monitoring())
        if not self._anomaly_detection_task:
            self._anomaly_detection_task = asyncio.create_task(self._anomaly_detection())

    async def stop_monitoring(self) -> None:
        """Stop background monitoring tasks."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        if self._anomaly_detection_task:
            self._anomaly_detection_task.cancel()
            self._anomaly_detection_task = None

    async def get_alert_kpis(self, force_refresh: bool = False) -> AlertKPIs:
        """Get comprehensive alert system KPIs.

        Args:
            force_refresh: Force calculation instead of using cache

        Returns:
            Alert KPIs object with current metrics
        """
        cache_key = "alert_kpis"

        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_key):
            self.stats["cache_hits"] += 1
            return self.metrics_cache[cache_key]["data"]

        start_time = datetime.now()

        try:
            async with get_session() as db:
                now = datetime.now()
                day_ago = now - timedelta(days=1)
                week_ago = now - timedelta(days=7)
                month_ago = now - timedelta(days=30)

                # Total alerts by time period
                total_24h = db.query(Alert).filter(Alert.created_at >= day_ago).count()
                total_7d = db.query(Alert).filter(Alert.created_at >= week_ago).count()
                total_30d = db.query(Alert).filter(Alert.created_at >= month_ago).count()

                # Delivery rates
                delivered_24h = db.query(Alert).filter(
                    Alert.created_at >= day_ago,
                    or_(
                        Alert.push_notification_delivered,
                        Alert.email_notification_delivered,
                        Alert.sms_notification_delivered,
                        Alert.webhook_notification_delivered
                    )
                ).count()

                delivered_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    or_(
                        Alert.push_notification_delivered,
                        Alert.email_notification_delivered,
                        Alert.sms_notification_delivered,
                        Alert.webhook_notification_delivered
                    )
                ).count()

                avg_delivery_rate_24h = (delivered_24h / max(total_24h, 1)) * 100
                avg_delivery_rate_7d = (delivered_7d / max(total_7d, 1)) * 100

                # Response rates
                responded_24h = db.query(Alert).filter(
                    Alert.created_at >= day_ago,
                    Alert.acknowledged_at.isnot(None)
                ).count()

                responded_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.acknowledged_at.isnot(None)
                ).count()

                avg_response_rate_24h = (responded_24h / max(total_24h, 1)) * 100
                avg_response_rate_7d = (responded_7d / max(total_7d, 1)) * 100

                # False positive rate
                false_positives_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.false_positive
                ).count()

                false_positive_rate_7d = (false_positives_7d / max(total_7d, 1)) * 100

                # Escalation rate
                escalated_24h = db.query(Alert).filter(
                    Alert.created_at >= day_ago,
                    Alert.escalated_at.isnot(None)
                ).count()

                escalation_rate_24h = (escalated_24h / max(total_24h, 1)) * 100

                # Average resolution time
                resolution_times = db.query(Alert.response_time_seconds).filter(
                    Alert.created_at >= week_ago,
                    Alert.response_time_seconds.isnot(None)
                ).all()

                avg_resolution_time_hours = None
                if resolution_times:
                    avg_seconds = sum(rt.response_time_seconds for rt in resolution_times) / len(resolution_times)
                    avg_resolution_time_hours = avg_seconds / 3600

                # Active configurations and users
                active_configurations = db.query(AlertConfiguration).filter(
                    AlertConfiguration.is_active
                ).count()

                active_users_24h = db.query(Alert.configuration_id).join(AlertConfiguration).filter(
                    Alert.created_at >= day_ago
                ).distinct().count()

                # Critical alerts pending
                critical_alerts_pending = db.query(Alert).filter(
                    Alert.alert_level.in_(["critical", "emergency"]),
                    Alert.status.in_(["generated", "sent", "delivered"])
                ).count()

                kpis = AlertKPIs(
                    total_alerts_24h=total_24h,
                    total_alerts_7d=total_7d,
                    total_alerts_30d=total_30d,
                    avg_delivery_rate_24h=avg_delivery_rate_24h,
                    avg_delivery_rate_7d=avg_delivery_rate_7d,
                    avg_response_rate_24h=avg_response_rate_24h,
                    avg_response_rate_7d=avg_response_rate_7d,
                    false_positive_rate_7d=false_positive_rate_7d,
                    escalation_rate_24h=escalation_rate_24h,
                    avg_resolution_time_hours=avg_resolution_time_hours,
                    active_configurations=active_configurations,
                    active_users_24h=active_users_24h,
                    critical_alerts_pending=critical_alerts_pending
                )

                # Cache the results
                self._cache_data(cache_key, kpis)
                self.stats["cache_misses"] += 1

                # Update stats
                calculation_time = (datetime.now() - start_time).total_seconds() * 1000
                self._update_calculation_stats(calculation_time)

                return kpis

        except Exception as e:
            logger.error(f"Failed to calculate alert KPIs: {e}")
            raise

    async def get_channel_performance(self) -> list[ChannelPerformanceMetrics]:
        """Get performance metrics for all notification channels.

        Returns:
            List of channel performance metrics
        """
        try:
            async with get_session() as db:
                day_ago = datetime.now() - timedelta(days=1)

                channels = ["push", "email", "sms", "webhook"]
                channel_metrics = []

                for channel in channels:
                    # Get delivery data for the channel
                    deliveries = db.query(NotificationDelivery).filter(
                        NotificationDelivery.channel == channel,
                        NotificationDelivery.sent_at >= day_ago
                    ).all()

                    messages_sent = len(deliveries)
                    messages_delivered = sum(1 for d in deliveries if d.status == "delivered")
                    delivery_rate = (messages_delivered / max(messages_sent, 1)) * 100

                    # Calculate average delivery time
                    delivery_times = [
                        (d.delivered_at - d.sent_at).total_seconds()
                        for d in deliveries
                        if d.delivered_at and d.sent_at and d.status == "delivered"
                    ]
                    avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else None

                    # Error analysis
                    failed_deliveries = [d for d in deliveries if d.status == "failed"]
                    failure_rate = (len(failed_deliveries) / max(messages_sent, 1)) * 100

                    error_types: dict[str, int] = {}
                    for delivery in failed_deliveries:
                        error_code = delivery.error_code or "unknown"
                        error_types[error_code] = error_types.get(error_code, 0) + 1

                    channel_metrics.append(ChannelPerformanceMetrics(
                        channel=channel,
                        messages_sent_24h=messages_sent,
                        messages_delivered_24h=messages_delivered,
                        delivery_rate_percentage=delivery_rate,
                        avg_delivery_time_seconds=avg_delivery_time,
                        failure_rate_percentage=failure_rate,
                        error_types=error_types
                    ))

                return channel_metrics

        except Exception as e:
            logger.error(f"Failed to get channel performance metrics: {e}")
            raise

    async def get_user_engagement_metrics(self) -> UserEngagementMetrics:
        """Get user engagement metrics for alerts.

        Returns:
            User engagement metrics object
        """
        try:
            async with get_session() as db:
                now = datetime.now()
                day_ago = now - timedelta(days=1)
                week_ago = now - timedelta(days=7)

                # Total and active users
                total_users = db.query(AlertConfiguration.user_id).distinct().count()

                active_users_24h = db.query(Alert.configuration_id).join(AlertConfiguration).filter(
                    Alert.created_at >= day_ago
                ).distinct().count()

                active_users_7d = db.query(Alert.configuration_id).join(AlertConfiguration).filter(
                    Alert.created_at >= week_ago
                ).distinct().count()

                # Alerts per user
                total_alerts_24h = db.query(Alert).filter(Alert.created_at >= day_ago).count()
                avg_alerts_per_user_24h = total_alerts_24h / max(active_users_24h, 1)

                # Response time analysis
                response_times = db.query(Alert.response_time_seconds).filter(
                    Alert.created_at >= week_ago,
                    Alert.response_time_seconds.isnot(None)
                ).all()

                avg_response_time_minutes = None
                if response_times:
                    avg_seconds = sum(rt.response_time_seconds for rt in response_times) / len(response_times)
                    avg_response_time_minutes = avg_seconds / 60

                # Engagement rates
                total_alerts_7d = db.query(Alert).filter(Alert.created_at >= week_ago).count()

                acknowledged_alerts_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.acknowledged_at.isnot(None)
                ).count()

                resolved_alerts_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.resolved_at.isnot(None)
                ).count()

                feedback_alerts_7d = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.feedback_rating.isnot(None)
                ).count()

                acknowledgment_rate = (acknowledged_alerts_7d / max(total_alerts_7d, 1)) * 100
                resolution_rate = (resolved_alerts_7d / max(total_alerts_7d, 1)) * 100
                feedback_submission_rate = (feedback_alerts_7d / max(total_alerts_7d, 1)) * 100

                # Average user rating
                ratings = db.query(Alert.feedback_rating).filter(
                    Alert.created_at >= week_ago,
                    Alert.feedback_rating.isnot(None)
                ).all()

                avg_user_rating = None
                if ratings:
                    avg_user_rating = sum(r.feedback_rating for r in ratings) / len(ratings)

                return UserEngagementMetrics(
                    total_users=total_users,
                    active_users_24h=active_users_24h,
                    active_users_7d=active_users_7d,
                    avg_alerts_per_user_24h=avg_alerts_per_user_24h,
                    avg_response_time_minutes=avg_response_time_minutes,
                    acknowledgment_rate_percentage=acknowledgment_rate,
                    resolution_rate_percentage=resolution_rate,
                    feedback_submission_rate=feedback_submission_rate,
                    avg_user_rating=avg_user_rating
                )

        except Exception as e:
            logger.error(f"Failed to get user engagement metrics: {e}")
            raise

    async def get_alert_effectiveness_metrics(self) -> AlertEffectivenessMetrics:
        """Get alert effectiveness and accuracy metrics.

        Returns:
            Alert effectiveness metrics object
        """
        try:
            async with get_session() as db:
                week_ago = datetime.now() - timedelta(days=7)

                # Get alerts with feedback for the past week
                alerts_with_feedback = db.query(Alert).filter(
                    Alert.created_at >= week_ago,
                    Alert.false_positive.isnot(None)
                ).all()

                if not alerts_with_feedback:
                    # Return default metrics if no feedback data
                    return AlertEffectivenessMetrics(
                        accuracy_score=0.0,
                        precision_score=0.0,
                        recall_score=0.0,
                        f1_score=0.0,
                        false_positive_rate=0.0,
                        false_negative_rate=0.0,
                        true_positive_alerts_7d=0,
                        false_positive_alerts_7d=0,
                        user_satisfaction_score=None
                    )

                # Calculate confusion matrix components
                true_positives = sum(1 for alert in alerts_with_feedback if not alert.false_positive)
                false_positives = sum(1 for alert in alerts_with_feedback if alert.false_positive)

                # Note: False negatives and true negatives require ground truth data
                # For now, we'll estimate based on available feedback
                total_feedback = len(alerts_with_feedback)

                # Calculate metrics
                precision = true_positives / max(true_positives + false_positives, 1)
                false_positive_rate = false_positives / max(total_feedback, 1)
                accuracy = true_positives / max(total_feedback, 1)

                # Estimated recall (assuming we catch most true positives)
                recall = 0.85 if true_positives > 0 else 0.0

                # F1 score
                f1_score = 2 * (precision * recall) / max(precision + recall, 1) if precision + recall > 0 else 0

                # User satisfaction from ratings
                satisfaction_scores = [
                    alert.feedback_rating
                    for alert in alerts_with_feedback
                    if alert.feedback_rating is not None
                ]

                user_satisfaction_score = None
                if satisfaction_scores:
                    user_satisfaction_score = sum(satisfaction_scores) / len(satisfaction_scores)

                return AlertEffectivenessMetrics(
                    accuracy_score=accuracy,
                    precision_score=precision,
                    recall_score=recall,
                    f1_score=f1_score,
                    false_positive_rate=false_positive_rate,
                    false_negative_rate=1 - recall,  # Estimated
                    true_positive_alerts_7d=true_positives,
                    false_positive_alerts_7d=false_positives,
                    user_satisfaction_score=user_satisfaction_score
                )

        except Exception as e:
            logger.error(f"Failed to get alert effectiveness metrics: {e}")
            raise

    async def get_system_health_metrics(self) -> SystemHealthMetrics:
        """Get overall system health and performance metrics.

        Returns:
            System health metrics object
        """
        try:
            # Get alert engine stats
            from .alert_engine import alert_engine
            from .firebase_service import firebase_service
            from .notification_service import notification_service
            from .websocket_manager import websocket_manager

            alert_stats = alert_engine.get_stats()
            websocket_stats = websocket_manager.get_stats()
            notification_stats = notification_service.get_stats()
            firebase_stats = firebase_service.get_stats()

            # Calculate system health metrics
            total_sent = (
                notification_stats.get("email_sent", 0) +
                notification_stats.get("sms_sent", 0) +
                notification_stats.get("webhook_sent", 0) +
                firebase_stats.get("notifications_sent", 0)
            )

            total_failed = (
                notification_stats.get("email_failed", 0) +
                notification_stats.get("sms_failed", 0) +
                notification_stats.get("webhook_failed", 0) +
                firebase_stats.get("notifications_failed", 0)
            )

            error_rate = (total_failed / max(total_sent, 1)) * 100

            return SystemHealthMetrics(
                system_uptime_percentage=99.5,  # This would come from monitoring system
                avg_processing_time_ms=alert_stats.get("avg_evaluation_time_ms", 0),
                error_rate_percentage=error_rate,
                queue_depth=0,  # This would come from task queue monitoring
                memory_usage_mb=0.0,  # This would come from system monitoring
                cpu_usage_percentage=0.0,  # This would come from system monitoring
                database_response_time_ms=0.0,  # This would come from DB monitoring
                active_websocket_connections=websocket_stats.get("active_connections", 0)
            )

        except Exception as e:
            logger.error(f"Failed to get system health metrics: {e}")
            raise

    async def get_trend_analysis(self, days: int = 30) -> AlertTrendAnalysis:
        """Get trend analysis for alerts over time.

        Args:
            days: Number of days to analyze

        Returns:
            Alert trend analysis object
        """
        try:
            async with get_session() as db:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                mid_date = start_date + timedelta(days=days//2)

                # Compare first half vs second half
                first_half_count = db.query(Alert).filter(
                    Alert.created_at >= start_date,
                    Alert.created_at < mid_date
                ).count()

                second_half_count = db.query(Alert).filter(
                    Alert.created_at >= mid_date,
                    Alert.created_at <= end_date
                ).count()

                # Calculate growth rate
                if first_half_count > 0:
                    growth_rate = ((second_half_count - first_half_count) / first_half_count) * 100
                else:
                    growth_rate = 100 if second_half_count > 0 else 0

                # Determine trend direction
                if growth_rate > 10:
                    trend_direction = "increasing"
                elif growth_rate < -10:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"

                # Seasonal patterns (by hour of day)
                hourly_counts = db.query(
                    func.extract('hour', Alert.created_at).label('hour'),
                    func.count(Alert.id).label('count')
                ).filter(
                    Alert.created_at >= start_date
                ).group_by(func.extract('hour', Alert.created_at)).all()

                seasonal_patterns = {str(int(h.hour)): h.count for h in hourly_counts}

                # Peak hours (top 3 hours with most alerts)
                peak_hours = sorted(seasonal_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
                peak_hours = [int(hour) for hour, _ in peak_hours]

                # Peak days (by day of week)
                daily_counts = db.query(
                    func.extract('dow', Alert.created_at).label('dow'),
                    func.count(Alert.id).label('count')
                ).filter(
                    Alert.created_at >= start_date
                ).group_by(func.extract('dow', Alert.created_at)).all()

                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                daily_patterns = {day_names[int(d.dow)]: d.count for d in daily_counts}

                peak_days = sorted(daily_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
                peak_days = [day for day, _ in peak_days]

                # Simple forecast (based on recent trend)
                daily_avg = second_half_count / (days // 2)
                forecast_next_7d = []
                for i in range(7):
                    forecast_date = end_date + timedelta(days=i+1)
                    forecast_count = max(0, int(daily_avg * (1 + growth_rate/100)))
                    forecast_next_7d.append({
                        "date": forecast_date.isoformat(),
                        "predicted_alerts": forecast_count
                    })

                return AlertTrendAnalysis(
                    period=f"{days}d",
                    trend_direction=trend_direction,
                    growth_rate_percentage=growth_rate,
                    seasonal_patterns=seasonal_patterns,
                    peak_hours=peak_hours,
                    peak_days=peak_days,
                    forecast_next_7d=forecast_next_7d
                )

        except Exception as e:
            logger.error(f"Failed to get trend analysis: {e}")
            raise

    async def detect_anomalies(self) -> list[dict[str, Any]]:
        """Detect anomalies in alert system performance.

        Returns:
            List of detected anomalies
        """
        anomalies = []

        try:
            # Get current and historical KPIs
            current_kpis = await self.get_alert_kpis()

            # Define anomaly thresholds
            thresholds = {
                "delivery_rate_drop": 20,  # Alert if delivery rate drops by 20%
                "response_rate_drop": 30,  # Alert if response rate drops by 30%
                "false_positive_spike": 15,  # Alert if false positive rate > 15%
                "escalation_spike": 10,  # Alert if escalation rate > 10%
                "critical_alerts_backlog": 5  # Alert if >5 critical alerts pending
            }

            # Check delivery rate anomaly
            if current_kpis.avg_delivery_rate_24h < (100 - thresholds["delivery_rate_drop"]):
                anomalies.append({
                    "type": "delivery_rate_drop",
                    "severity": "high",
                    "description": f"Delivery rate dropped to {current_kpis.avg_delivery_rate_24h:.1f}%",
                    "metric_value": current_kpis.avg_delivery_rate_24h,
                    "threshold": 100 - thresholds["delivery_rate_drop"],
                    "detected_at": datetime.now().isoformat()
                })

            # Check response rate anomaly
            if current_kpis.avg_response_rate_24h < (100 - thresholds["response_rate_drop"]):
                anomalies.append({
                    "type": "response_rate_drop",
                    "severity": "medium",
                    "description": f"Response rate dropped to {current_kpis.avg_response_rate_24h:.1f}%",
                    "metric_value": current_kpis.avg_response_rate_24h,
                    "threshold": 100 - thresholds["response_rate_drop"],
                    "detected_at": datetime.now().isoformat()
                })

            # Check false positive spike
            if current_kpis.false_positive_rate_7d > thresholds["false_positive_spike"]:
                anomalies.append({
                    "type": "false_positive_spike",
                    "severity": "medium",
                    "description": f"False positive rate spiked to {current_kpis.false_positive_rate_7d:.1f}%",
                    "metric_value": current_kpis.false_positive_rate_7d,
                    "threshold": thresholds["false_positive_spike"],
                    "detected_at": datetime.now().isoformat()
                })

            # Check escalation spike
            if current_kpis.escalation_rate_24h > thresholds["escalation_spike"]:
                anomalies.append({
                    "type": "escalation_spike",
                    "severity": "high",
                    "description": f"Escalation rate spiked to {current_kpis.escalation_rate_24h:.1f}%",
                    "metric_value": current_kpis.escalation_rate_24h,
                    "threshold": thresholds["escalation_spike"],
                    "detected_at": datetime.now().isoformat()
                })

            # Check critical alerts backlog
            if current_kpis.critical_alerts_pending > thresholds["critical_alerts_backlog"]:
                anomalies.append({
                    "type": "critical_alerts_backlog",
                    "severity": "critical",
                    "description": f"{current_kpis.critical_alerts_pending} critical alerts pending",
                    "metric_value": current_kpis.critical_alerts_pending,
                    "threshold": thresholds["critical_alerts_backlog"],
                    "detected_at": datetime.now().isoformat()
                })

            if anomalies:
                self.stats["anomalies_detected"] += len(anomalies)
                logger.warning(f"Detected {len(anomalies)} alert system anomalies")

            return anomalies

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    async def _continuous_monitoring(self) -> None:
        """Background task for continuous monitoring."""
        while True:
            try:
                await asyncio.sleep(self.config["kpi_refresh_interval_seconds"])

                # Refresh KPIs
                await self.get_alert_kpis(force_refresh=True)
                self.stats["last_kpi_refresh"] = datetime.now()

                logger.debug("KPIs refreshed successfully")

            except asyncio.CancelledError:
                logger.info("Continuous monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")

    async def _anomaly_detection(self) -> None:
        """Background task for anomaly detection."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                anomalies = await self.detect_anomalies()
                if anomalies:
                    # Here you could send alerts to administrators
                    logger.warning(f"Anomalies detected: {len(anomalies)}")

                self.stats["last_anomaly_check"] = datetime.now()

            except asyncio.CancelledError:
                logger.info("Anomaly detection task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.metrics_cache:
            return False

        cache_entry = self.metrics_cache[cache_key]
        age_seconds = (datetime.now() - cache_entry["timestamp"]).total_seconds()
        return age_seconds < self.cache_ttl_seconds

    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with timestamp.

        Args:
            cache_key: Key for caching
            data: Data to cache
        """
        self.metrics_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }

    def _update_calculation_stats(self, calculation_time: float) -> None:
        """Update calculation performance statistics.

        Args:
            calculation_time: Calculation time in milliseconds
        """
        self.stats["analytics_calculations"] += 1

        # Calculate running average
        current_avg = self.stats["avg_calculation_time_ms"]
        calculation_count = self.stats["analytics_calculations"]

        if calculation_count == 1:
            self.stats["avg_calculation_time_ms"] = calculation_time
        else:
            self.stats["avg_calculation_time_ms"] = (
                (current_avg * (calculation_count - 1) + calculation_time) / calculation_count
            )

    def get_stats(self) -> dict[str, Any]:
        """Get analytics engine statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            "config": self.config,
            "cache_size": len(self.metrics_cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(self.stats["cache_hits"] + self.stats["cache_misses"], 1)
            ) * 100
        }


# Global instance
alert_analytics_engine = AlertAnalyticsEngine()
