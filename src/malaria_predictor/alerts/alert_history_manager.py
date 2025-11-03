"""Alert history management and archiving system.

Provides comprehensive alert history management including:
- Alert archiving and retention policies
- Historical alert analytics and reporting
- Alert performance trend analysis
- Data retention compliance
- Historical data cleanup and optimization
"""

import logging
from datetime import datetime, timedelta
from typing import Any, cast

from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import (
    Alert,
    AlertConfiguration,
    AlertPerformanceMetrics,
    NotificationDelivery,
)
from ..database.session import get_session

logger = logging.getLogger(__name__)


class AlertHistoryQuery(BaseModel):
    """Query parameters for alert history retrieval."""

    user_id: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    alert_levels: list[str] | None = None
    alert_types: list[str] | None = None
    status_filters: list[str] | None = None
    location_filters: list[str] | None = None
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")


class AlertHistorySummary(BaseModel):
    """Summary statistics for alert history."""

    total_alerts: int
    alerts_by_level: dict[str, int]
    alerts_by_type: dict[str, int]
    alerts_by_status: dict[str, int]
    avg_response_time_hours: float | None
    resolution_rate_percentage: float
    false_positive_rate_percentage: float
    delivery_success_rate_percentage: float
    most_active_locations: list[dict[str, Any]]
    trend_analysis: dict[str, Any]


class AlertArchivePolicy(BaseModel):
    """Alert data archiving policy configuration."""

    retention_period_days: int = Field(365, ge=30, le=3650)
    archive_after_days: int = Field(90, ge=7, le=365)
    delete_after_days: int = Field(1095, ge=365, le=7300)  # 3 years
    compress_archived_data: bool = True
    notification_channels_retention_days: int = Field(180, ge=30, le=730)
    performance_metrics_retention_days: int = Field(730, ge=90, le=2190)


class AlertTrendData(BaseModel):
    """Alert trend analysis data."""

    period: str
    date: datetime
    alert_count: int
    avg_risk_score: float | None
    delivery_rate: float
    response_rate: float
    escalation_count: int


class AlertHistoryManager:
    """Manages alert history, archiving, and historical analytics.

    Provides functionality for:
    - Alert history querying with advanced filtering
    - Historical analytics and trend analysis
    - Data retention and archiving policies
    - Performance monitoring and reporting
    - Cleanup and optimization
    """

    def __init__(self) -> None:
        """Initialize the alert history manager."""
        self.settings = settings

        # Default archiving policy
        self.archive_policy = AlertArchivePolicy(
            retention_period_days=365,
            archive_after_days=90,
            delete_after_days=1095,
            compress_archived_data=True,
            notification_channels_retention_days=180,
            performance_metrics_retention_days=730
        )

        # Load custom policy from settings if available
        if hasattr(settings, "ALERT_ARCHIVE_POLICY"):
            self.archive_policy = AlertArchivePolicy(**settings.ALERT_ARCHIVE_POLICY)

        # Statistics tracking
        self.stats: dict[str, int | float | datetime | None] = {
            "queries_processed": 0,
            "archives_created": 0,
            "cleanups_performed": 0,
            "data_purged_count": 0,
            "avg_query_time_ms": 0.0,
            "last_cleanup": None,
            "last_archive": None
        }

    async def get_alert_history(
        self,
        query: AlertHistoryQuery
    ) -> dict[str, Any]:
        """Get filtered alert history for a user.

        Args:
            query: Alert history query parameters

        Returns:
            Dictionary containing alerts and metadata
        """
        start_time = datetime.now()

        try:
            async with get_session() as db:
                # Build base select statement (SQLAlchemy 2.0 async)
                stmt = select(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == query.user_id
                )

                # Apply date filters
                if query.start_date:
                    stmt = stmt.where(Alert.created_at >= query.start_date)

                if query.end_date:
                    stmt = stmt.where(Alert.created_at <= query.end_date)

                # Apply level filters
                if query.alert_levels:
                    stmt = stmt.where(Alert.alert_level.in_(query.alert_levels))

                # Apply type filters
                if query.alert_types:
                    stmt = stmt.where(Alert.alert_type.in_(query.alert_types))

                # Apply status filters
                if query.status_filters:
                    stmt = stmt.where(Alert.status.in_(query.status_filters))

                # Apply location filters
                if query.location_filters:
                    location_conditions = []
                    for location in query.location_filters:
                        location_conditions.extend([
                            Alert.location_name.ilike(f"%{location}%"),
                            Alert.admin_region.ilike(f"%{location}%"),
                            Alert.country_code.ilike(f"%{location}%")
                        ])
                    stmt = stmt.where(or_(*location_conditions))

                # Get total count before pagination
                count_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == query.user_id
                )
                # Apply same filters to count query
                if query.start_date:
                    count_stmt = count_stmt.where(Alert.created_at >= query.start_date)
                if query.end_date:
                    count_stmt = count_stmt.where(Alert.created_at <= query.end_date)
                if query.alert_levels:
                    count_stmt = count_stmt.where(Alert.alert_level.in_(query.alert_levels))
                if query.alert_types:
                    count_stmt = count_stmt.where(Alert.alert_type.in_(query.alert_types))
                if query.status_filters:
                    count_stmt = count_stmt.where(Alert.status.in_(query.status_filters))
                if query.location_filters:
                    location_conditions = []
                    for location in query.location_filters:
                        location_conditions.extend([
                            Alert.location_name.ilike(f"%{location}%"),
                            Alert.admin_region.ilike(f"%{location}%"),
                            Alert.country_code.ilike(f"%{location}%")
                        ])
                    count_stmt = count_stmt.where(or_(*location_conditions))

                total_count = await db.scalar(count_stmt) or 0

                # Apply sorting
                sort_column = getattr(Alert, query.sort_by, Alert.created_at)
                if query.sort_order.lower() == "desc":
                    stmt = stmt.order_by(desc(sort_column))
                else:
                    stmt = stmt.order_by(sort_column)

                # Apply pagination
                stmt = stmt.offset(query.offset).limit(query.limit)
                result = await db.execute(stmt)
                alerts = result.scalars().all()

                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                self._update_query_stats(processing_time)

                return {
                    "alerts": [self._serialize_alert(alert) for alert in alerts],
                    "pagination": {
                        "total": total_count,
                        "limit": query.limit,
                        "offset": query.offset,
                        "has_next": (query.offset + query.limit) < total_count,
                        "has_prev": query.offset > 0
                    },
                    "query_time_ms": int(processing_time),
                    "filters_applied": {
                        "date_range": bool(query.start_date or query.end_date),
                        "levels": query.alert_levels or [],
                        "types": query.alert_types or [],
                        "status": query.status_filters or [],
                        "locations": query.location_filters or []
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            raise

    async def get_alert_history_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> AlertHistorySummary:
        """Get comprehensive alert history summary.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Alert history summary with statistics
        """
        try:
            async with get_session() as db:
                start_date = datetime.now() - timedelta(days=days)

                # Total alerts (SQLAlchemy 2.0 async)
                total_alerts_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date
                )
                total_alerts = await db.scalar(total_alerts_stmt) or 0

                # Alerts by level
                level_stats = {}
                for level in ["low", "medium", "high", "critical", "emergency"]:
                    level_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                        AlertConfiguration.user_id == user_id,
                        Alert.created_at >= start_date,
                        Alert.alert_level == level
                    )
                    count = await db.scalar(level_stmt) or 0
                    level_stats[level] = count

                # Alerts by type
                type_stmt = select(
                    Alert.alert_type,
                    func.count(Alert.id).label("count")
                ).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date
                ).group_by(Alert.alert_type)

                type_result = await db.execute(type_stmt)
                type_results = type_result.all()
                type_stats: dict[str, int] = {str(result.alert_type): int(result.count) for result in type_results}  # type: ignore[call-overload]

                # Alerts by status
                status_stmt = select(
                    Alert.status,
                    func.count(Alert.id).label("count")
                ).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date
                ).group_by(Alert.status)

                status_result = await db.execute(status_stmt)
                status_results = status_result.all()
                status_stats: dict[str, int] = {str(result.status): int(result.count) for result in status_results}  # type: ignore[call-overload]

                # Response time analysis
                response_stmt = select(Alert.response_time_seconds).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date,
                    Alert.response_time_seconds.isnot(None)
                )
                response_result = await db.execute(response_stmt)
                response_times = response_result.all()

                avg_response_time_hours = None
                if response_times:
                    avg_seconds = sum(rt.response_time_seconds for rt in response_times) / len(response_times)
                    avg_response_time_hours = avg_seconds / 3600

                # Resolution and false positive rates
                resolved_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date,
                    Alert.resolved_at.isnot(None)
                )
                resolved_count = await db.scalar(resolved_stmt) or 0

                false_positive_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date,
                    Alert.false_positive
                )
                false_positive_count = await db.scalar(false_positive_stmt) or 0

                resolution_rate = (resolved_count / max(total_alerts, 1)) * 100
                false_positive_rate = (false_positive_count / max(total_alerts, 1)) * 100

                # Delivery success rate
                delivered_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date,
                    or_(
                        Alert.push_notification_delivered,
                        Alert.email_notification_delivered,
                        Alert.sms_notification_delivered,
                        Alert.webhook_notification_delivered
                    )
                )
                delivered_count = await db.scalar(delivered_stmt) or 0

                delivery_success_rate = (delivered_count / max(total_alerts, 1)) * 100

                # Most active locations
                location_stmt = select(
                    Alert.location_name,
                    Alert.country_code,
                    func.count(Alert.id).label("count"),
                    func.avg(Alert.risk_score).label("avg_risk")
                ).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date,
                    Alert.location_name.isnot(None)
                ).group_by(
                    Alert.location_name, Alert.country_code
                ).order_by(desc("count")).limit(10)

                location_result = await db.execute(location_stmt)
                location_results = location_result.all()

                most_active_locations = [
                    {
                        "location": result.location_name,
                        "country": result.country_code,
                        "alert_count": result.count,
                        "avg_risk_score": float(result.avg_risk) if result.avg_risk else None
                    }
                    for result in location_results
                ]

                # Trend analysis
                trend_analysis = await self._calculate_trend_analysis(db, user_id, days)

                return AlertHistorySummary(
                    total_alerts=total_alerts,
                    alerts_by_level=level_stats,
                    alerts_by_type=type_stats,
                    alerts_by_status=status_stats,
                    avg_response_time_hours=avg_response_time_hours,
                    resolution_rate_percentage=resolution_rate,
                    false_positive_rate_percentage=false_positive_rate,
                    delivery_success_rate_percentage=delivery_success_rate,
                    most_active_locations=most_active_locations,
                    trend_analysis=trend_analysis
                )

        except Exception as e:
            logger.error(f"Failed to get alert history summary: {e}")
            raise

    async def get_alert_trends(
        self,
        user_id: str,
        period: str = "daily",
        days: int = 30
    ) -> list[AlertTrendData]:
        """Get alert trend data over time.

        Args:
            user_id: User identifier
            period: Aggregation period (hourly, daily, weekly)
            days: Number of days to analyze

        Returns:
            List of trend data points
        """
        try:
            async with get_session() as db:
                start_date = datetime.now() - timedelta(days=days)

                # Build time truncation based on period
                if period == "hourly":
                    time_trunc = func.date_trunc('hour', Alert.created_at)
                elif period == "weekly":
                    time_trunc = func.date_trunc('week', Alert.created_at)
                else:  # daily
                    time_trunc = func.date_trunc('day', Alert.created_at)

                # Query trend data (SQLAlchemy 2.0 async)
                trends_stmt = select(
                    time_trunc.label("period_date"),
                    func.count(Alert.id).label("alert_count"),
                    func.avg(Alert.risk_score).label("avg_risk_score"),
                    func.sum(
                        func.case(
                            (Alert.push_notification_delivered, 1),
                            (Alert.email_notification_delivered, 1),
                            (Alert.sms_notification_delivered, 1),
                            (Alert.webhook_notification_delivered, 1),
                            else_=0
                        )
                    ).label("delivered_count"),
                    func.sum(
                        func.case(
                            (Alert.acknowledged_at.isnot(None), 1),
                            else_=0
                        )
                    ).label("acknowledged_count"),
                    func.sum(
                        func.case(
                            (Alert.escalated_at.isnot(None), 1),
                            else_=0
                        )
                    ).label("escalation_count")
                ).join(AlertConfiguration).where(
                    AlertConfiguration.user_id == user_id,
                    Alert.created_at >= start_date
                ).group_by(time_trunc).order_by(time_trunc)

                trends_result = await db.execute(trends_stmt)
                trends = trends_result.all()

                # Convert to trend data objects
                trend_data = []
                for trend in trends:
                    delivery_rate = (trend.delivered_count / max(trend.alert_count, 1)) * 100
                    response_rate = (trend.acknowledged_count / max(trend.alert_count, 1)) * 100

                    trend_data.append(AlertTrendData(
                        period=period,
                        date=trend.period_date,
                        alert_count=trend.alert_count,
                        avg_risk_score=float(trend.avg_risk_score) if trend.avg_risk_score else None,
                        delivery_rate=delivery_rate,
                        response_rate=response_rate,
                        escalation_count=trend.escalation_count
                    ))

                return trend_data

        except Exception as e:
            logger.error(f"Failed to get alert trends: {e}")
            raise

    async def archive_old_alerts(
        self,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """Archive old alerts based on retention policy.

        Args:
            dry_run: If True, only simulate archiving without making changes

        Returns:
            Dictionary with archiving results
        """
        try:
            async with get_session() as db:
                archive_cutoff = datetime.now() - timedelta(days=self.archive_policy.archive_after_days)

                # Find alerts to archive (SQLAlchemy 2.0 async)
                archive_stmt = select(Alert).where(
                    Alert.created_at <= archive_cutoff,
                    Alert.status.in_(["resolved", "dismissed"])
                )
                archive_result = await db.execute(archive_stmt)
                alerts_to_archive = archive_result.scalars().all()

                archived_count = 0
                archived_by_level: dict[str, int] = {}
                storage_saved_mb: float = 0.0

                if not dry_run:
                    for alert in alerts_to_archive:
                        # Calculate storage estimation
                        alert_size = len(str(alert.alert_data or "")) + len(str(alert.alert_message) if alert.alert_message else "")
                        storage_saved_mb += alert_size / (1024 * 1024)

                        # Track by level
                        level = str(alert.alert_level)
                        archived_by_level[level] = archived_by_level.get(level, 0) + 1

                        # Mark as archived (you might want to move to separate table)
                        alert.status = "archived"  # type: ignore[assignment]
                        archived_count += 1

                    await db.commit()
                    self.stats["archives_created"] = cast(int, self.stats["archives_created"]) + archived_count
                    self.stats["last_archive"] = datetime.now()

                else:
                    # Dry run - just count
                    archived_count = len(alerts_to_archive)
                    for alert in alerts_to_archive:
                        level = str(alert.alert_level)
                        archived_by_level[level] = archived_by_level.get(level, 0) + 1

                logger.info(
                    f"Archive operation {'simulated' if dry_run else 'completed'}: "
                    f"{archived_count} alerts processed"
                )

                return {
                    "operation": "archive",
                    "dry_run": dry_run,
                    "archived_count": archived_count,
                    "archived_by_level": archived_by_level,
                    "archive_cutoff_date": archive_cutoff.isoformat(),
                    "estimated_storage_saved_mb": storage_saved_mb,
                    "next_archive_recommended": (datetime.now() + timedelta(days=30)).isoformat()
                }

        except Exception as e:
            logger.error(f"Alert archiving failed: {e}")
            raise

    async def cleanup_old_data(
        self,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """Clean up old alert data based on retention policy.

        Args:
            dry_run: If True, only simulate cleanup without making changes

        Returns:
            Dictionary with cleanup results
        """
        try:
            async with get_session() as db:
                # Different retention periods for different data types
                alert_cutoff = datetime.now() - timedelta(days=self.archive_policy.delete_after_days)
                notification_cutoff = datetime.now() - timedelta(
                    days=self.archive_policy.notification_channels_retention_days
                )
                metrics_cutoff = datetime.now() - timedelta(
                    days=self.archive_policy.performance_metrics_retention_days
                )

                cleanup_summary: dict[str, Any] = {
                    "operation": "cleanup",
                    "dry_run": dry_run,
                    "deleted_counts": {},
                    "storage_freed_mb": 0,
                    "cutoff_dates": {
                        "alerts": alert_cutoff.isoformat(),
                        "notifications": notification_cutoff.isoformat(),
                        "metrics": metrics_cutoff.isoformat()
                    }
                }

                # Clean up old alerts (SQLAlchemy 2.0 async)
                alert_count_stmt = select(func.count()).select_from(Alert).where(Alert.created_at <= alert_cutoff)
                alert_count = await db.scalar(alert_count_stmt) or 0

                if not dry_run and alert_count > 0:
                    delete_alerts_stmt = select(Alert).where(Alert.created_at <= alert_cutoff)
                    delete_alerts_result = await db.execute(delete_alerts_stmt)
                    old_alerts = delete_alerts_result.scalars().all()
                    for alert in old_alerts:
                        await db.delete(alert)

                cleanup_summary["deleted_counts"]["alerts"] = alert_count

                # Clean up old notification deliveries
                notification_count_stmt = select(func.count()).select_from(NotificationDelivery).where(
                    NotificationDelivery.sent_at <= notification_cutoff
                )
                notification_count = await db.scalar(notification_count_stmt) or 0

                if not dry_run and notification_count > 0:
                    delete_notif_stmt = select(NotificationDelivery).where(
                        NotificationDelivery.sent_at <= notification_cutoff
                    )
                    delete_notif_result = await db.execute(delete_notif_stmt)
                    old_notifications = delete_notif_result.scalars().all()
                    for notif in old_notifications:
                        await db.delete(notif)

                cleanup_summary["deleted_counts"]["notifications"] = notification_count

                # Clean up old performance metrics
                metrics_count_stmt = select(func.count()).select_from(AlertPerformanceMetrics).where(
                    AlertPerformanceMetrics.metric_date <= metrics_cutoff
                )
                metrics_count = await db.scalar(metrics_count_stmt) or 0

                if not dry_run and metrics_count > 0:
                    delete_metrics_stmt = select(AlertPerformanceMetrics).where(
                        AlertPerformanceMetrics.metric_date <= metrics_cutoff
                    )
                    delete_metrics_result = await db.execute(delete_metrics_stmt)
                    old_metrics = delete_metrics_result.scalars().all()
                    for metric in old_metrics:
                        await db.delete(metric)

                cleanup_summary["deleted_counts"]["metrics"] = metrics_count

                if not dry_run:
                    await db.commit()
                    self.stats["cleanups_performed"] = cast(int, self.stats["cleanups_performed"]) + 1
                    self.stats["data_purged_count"] = cast(int, self.stats["data_purged_count"]) + alert_count + notification_count + metrics_count
                    self.stats["last_cleanup"] = datetime.now()

                total_deleted = alert_count + notification_count + metrics_count
                cleanup_summary["total_deleted"] = total_deleted

                logger.info(
                    f"Data cleanup {'simulated' if dry_run else 'completed'}: "
                    f"{total_deleted} records processed"
                )

                return cleanup_summary

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            raise

    async def export_alert_history(
        self,
        user_id: str,
        export_format: str = "json",
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Export alert history in various formats.

        Args:
            user_id: User identifier
            export_format: Export format (json, csv, excel)
            start_date: Start date for export
            end_date: End date for export

        Returns:
            Dictionary with export data and metadata
        """
        try:
            query = AlertHistoryQuery(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000,  # Large limit for export
                offset=0,
                sort_by="created_at",
                sort_order="desc"
            )

            history_data = await self.get_alert_history(query)

            export_data = {
                "export_format": export_format,
                "export_timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "total_alerts": history_data["pagination"]["total"],
                "alerts": history_data["alerts"]
            }

            if export_format == "csv":
                # Convert to CSV format (simplified structure)
                csv_data = []
                for alert in history_data["alerts"]:
                    csv_data.append({
                        "id": alert["id"],
                        "created_at": alert["created_at"],
                        "alert_level": alert["alert_level"],
                        "alert_type": alert["alert_type"],
                        "location": alert["location_name"],
                        "risk_score": alert["risk_score"],
                        "status": alert["status"],
                        "acknowledged_at": alert["acknowledged_at"],
                        "resolved_at": alert["resolved_at"]
                    })
                export_data["csv_data"] = csv_data

            return export_data

        except Exception as e:
            logger.error(f"Alert history export failed: {e}")
            raise

    def _serialize_alert(self, alert: Alert) -> dict[str, Any]:
        """Serialize alert object to dictionary.

        Args:
            alert: Alert object to serialize

        Returns:
            Dictionary representation of alert
        """
        return {
            "id": alert.id,
            "alert_level": alert.alert_level,
            "alert_type": alert.alert_type,
            "alert_title": alert.alert_title,
            "alert_message": alert.alert_message,
            "location_name": alert.location_name,
            "country_code": alert.country_code,
            "admin_region": alert.admin_region,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "risk_score": alert.risk_score,
            "confidence_score": alert.confidence_score,
            "status": alert.status,
            "priority": alert.priority,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "viewed_at": alert.viewed_at.isoformat() if alert.viewed_at else None,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "response_time_seconds": alert.response_time_seconds,
            "false_positive": alert.false_positive,
            "feedback_rating": alert.feedback_rating,
            "escalated_at": alert.escalated_at.isoformat() if alert.escalated_at else None,
            "escalation_level": alert.escalation_level,
            "delivery_status": {
                "push_sent": alert.push_notification_sent,
                "push_delivered": alert.push_notification_delivered,
                "email_sent": alert.email_notification_sent,
                "email_delivered": alert.email_notification_delivered,
                "sms_sent": alert.sms_notification_sent,
                "sms_delivered": alert.sms_notification_delivered,
                "webhook_sent": alert.webhook_notification_sent,
                "webhook_delivered": alert.webhook_notification_delivered
            }
        }

    async def _calculate_trend_analysis(
        self,
        db: AsyncSession,
        user_id: str,
        days: int
    ) -> dict[str, Any]:
        """Calculate trend analysis for alerts.

        Args:
            db: Database session
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        try:
            # Compare current period vs previous period
            current_start = datetime.now() - timedelta(days=days)
            previous_start = current_start - timedelta(days=days)

            # Current period stats (SQLAlchemy 2.0 async)
            current_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                AlertConfiguration.user_id == user_id,
                Alert.created_at >= current_start
            )
            current_alerts = await db.scalar(current_stmt) or 0

            # Previous period stats (SQLAlchemy 2.0 async)
            previous_stmt = select(func.count()).select_from(Alert).join(AlertConfiguration).where(
                AlertConfiguration.user_id == user_id,
                Alert.created_at >= previous_start,
                Alert.created_at < current_start
            )
            previous_alerts = await db.scalar(previous_stmt) or 0

            # Calculate percentage change
            if previous_alerts > 0:
                alert_change_pct = ((current_alerts - previous_alerts) / previous_alerts) * 100
            else:
                alert_change_pct = 100 if current_alerts > 0 else 0

            return {
                "period_days": days,
                "current_period_alerts": current_alerts,
                "previous_period_alerts": previous_alerts,
                "alert_change_percentage": round(alert_change_pct, 1),
                "trend_direction": "increasing" if alert_change_pct > 5 else "decreasing" if alert_change_pct < -5 else "stable"
            }

        except Exception as e:
            logger.error(f"Trend analysis calculation failed: {e}")
            return {}

    def _update_query_stats(self, processing_time: float) -> None:
        """Update query performance statistics.

        Args:
            processing_time: Query processing time in milliseconds
        """
        self.stats["queries_processed"] = cast(int, self.stats["queries_processed"]) + 1

        # Calculate running average
        current_avg = cast(float, self.stats["avg_query_time_ms"])
        query_count = cast(int, self.stats["queries_processed"])

        if query_count == 1:
            self.stats["avg_query_time_ms"] = processing_time
        else:
            self.stats["avg_query_time_ms"] = (
                (current_avg * (query_count - 1) + processing_time) / query_count
            )

    def get_stats(self) -> dict[str, Any]:
        """Get alert history manager statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            "archive_policy": self.archive_policy.dict(),
            "retention_summary": {
                "archive_after_days": self.archive_policy.archive_after_days,
                "delete_after_days": self.archive_policy.delete_after_days,
                "next_cleanup_recommended": (
                    datetime.now() + timedelta(days=7)
                ).isoformat()
            }
        }


# Global instance
alert_history_manager = AlertHistoryManager()
