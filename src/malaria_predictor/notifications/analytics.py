"""
Notification Analytics and Delivery Tracking System.

This module provides comprehensive analytics for push notification performance,
delivery tracking, user engagement metrics, and operational insights for
optimizing notification strategies and system performance.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, desc, extract, func
from sqlalchemy.orm import Session

from ..database.session import get_database_session
from .models import (
    DeviceToken,
    NotificationLog,
    NotificationStatus,
    NotificationTemplate,
    TopicSubscription,
)

logger = logging.getLogger(__name__)


class NotificationAnalytics:
    """
    Comprehensive notification analytics and tracking system.

    Provides detailed insights into notification performance, delivery rates,
    user engagement, and system optimization opportunities.
    """

    def __init__(self, db_session: Session | None = None) -> None:
        """
        Initialize notification analytics.

        Args:
            db_session: Database session (will create if not provided)
        """
        self.db_session = db_session
        self._should_close_session = db_session is None

        logger.info("Notification analytics system initialized")

    async def __aenter__(self) -> "NotificationAnalytics":
        """Async context manager entry."""
        if self._should_close_session:
            self.db_session = await get_database_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_session and self.db_session:
            await self.db_session.close()

    async def get_delivery_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        group_by: str = "day",
    ) -> dict[str, Any]:
        """
        Get comprehensive delivery summary with trends.

        Args:
            start_date: Start date for analysis (defaults to 7 days ago)
            end_date: End date for analysis (defaults to now)
            group_by: Grouping period ("hour", "day", "week", "month")

        Returns:
            Dictionary with delivery summary and trends
        """
        try:
            session = self.db_session or await get_database_session()

            # Default date range
            if not start_date:
                start_date = datetime.now(UTC) - timedelta(days=7)
            if not end_date:
                end_date = datetime.now(UTC)

            # Base query
            base_query = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            )

            # Overall statistics
            total_notifications = base_query.count()
            sent_count = base_query.filter(NotificationLog.status == NotificationStatus.SENT).count()
            failed_count = base_query.filter(NotificationLog.status == NotificationStatus.FAILED).count()
            pending_count = base_query.filter(NotificationLog.status == NotificationStatus.PENDING).count()
            canceled_count = base_query.filter(NotificationLog.status == NotificationStatus.CANCELED).count()

            # Calculate success rate
            success_rate = (sent_count / total_notifications) if total_notifications > 0 else 0

            # Average delivery time
            avg_delivery_time = session.query(
                func.avg(
                    func.extract('epoch', NotificationLog.sent_at - NotificationLog.created_at)
                )
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.SENT,
                    NotificationLog.sent_at.isnot(None),
                )
            ).scalar() or 0

            # Group by time period for trends
            time_trends = await self._get_time_trends(start_date, end_date, group_by)

            # Platform breakdown
            platform_stats = await self._get_platform_breakdown(start_date, end_date)

            # Priority breakdown
            priority_stats = await self._get_priority_breakdown(start_date, end_date)

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": (end_date - start_date).days,
                },
                "summary": {
                    "total_notifications": total_notifications,
                    "sent": sent_count,
                    "failed": failed_count,
                    "pending": pending_count,
                    "canceled": canceled_count,
                    "success_rate": round(success_rate, 4),
                    "average_delivery_time_seconds": round(avg_delivery_time, 2),
                },
                "trends": time_trends,
                "platform_breakdown": platform_stats,
                "priority_breakdown": priority_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get delivery summary: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_engagement_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get user engagement metrics for notifications.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with engagement metrics
        """
        try:
            session = self.db_session or await get_database_session()

            # Default date range
            if not start_date:
                start_date = datetime.now(UTC) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(UTC)

            # Base query
            base_query = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.SENT,
                )
            )

            # Click-through rates
            total_delivered = base_query.count()
            total_clicked = base_query.filter(NotificationLog.clicked).count()
            click_through_rate = (total_clicked / total_delivered) if total_delivered > 0 else 0

            # Template performance
            template_performance = session.query(
                NotificationTemplate.name,
                NotificationTemplate.category,
                func.count(NotificationLog.id).label('sent_count'),
                func.sum(case([(NotificationLog.clicked, 1)], else_=0)).label('clicked_count'),
                func.avg(
                    case([
                        (NotificationLog.clicked_at.isnot(None),
                         func.extract('epoch', NotificationLog.clicked_at - NotificationLog.sent_at))
                    ])
                ).label('avg_time_to_click'),
            ).join(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.SENT,
                )
            ).group_by(NotificationTemplate.id, NotificationTemplate.name, NotificationTemplate.category).all()

            # Format template performance
            template_stats = []
            for row in template_performance:
                sent_count = row.sent_count or 0
                clicked_count = row.clicked_count or 0
                ctr = (clicked_count / sent_count) if sent_count > 0 else 0

                template_stats.append({
                    "template_name": row.name,
                    "category": row.category,
                    "sent_count": sent_count,
                    "clicked_count": clicked_count,
                    "click_through_rate": round(ctr, 4),
                    "avg_time_to_click_seconds": round(row.avg_time_to_click or 0, 2),
                })

            # Priority engagement
            priority_engagement = session.query(
                NotificationLog.priority,
                func.count(NotificationLog.id).label('sent_count'),
                func.sum(case([(NotificationLog.clicked, 1)], else_=0)).label('clicked_count'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.SENT,
                )
            ).group_by(NotificationLog.priority).all()

            priority_stats = []
            for row in priority_engagement:
                sent_count = row.sent_count or 0
                clicked_count = row.clicked_count or 0
                ctr = (clicked_count / sent_count) if sent_count > 0 else 0

                priority_stats.append({
                    "priority": row.priority,
                    "sent_count": sent_count,
                    "clicked_count": clicked_count,
                    "click_through_rate": round(ctr, 4),
                })

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "overall_engagement": {
                    "total_delivered": total_delivered,
                    "total_clicked": total_clicked,
                    "click_through_rate": round(click_through_rate, 4),
                },
                "template_performance": template_stats,
                "priority_engagement": priority_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get engagement metrics: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_error_analysis(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Analyze notification delivery errors and failure patterns.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            limit: Maximum number of error details to return

        Returns:
            Dictionary with error analysis
        """
        try:
            session = self.db_session or await get_database_session()

            # Default date range
            if not start_date:
                start_date = datetime.now(UTC) - timedelta(days=7)
            if not end_date:
                end_date = datetime.now(UTC)

            # Failed notifications
            failed_query = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.FAILED,
                )
            )

            total_failed = failed_query.count()

            # Error message analysis
            error_patterns = session.query(
                NotificationLog.error_message,
                func.count(NotificationLog.id).label('error_count'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.FAILED,
                    NotificationLog.error_message.isnot(None),
                )
            ).group_by(NotificationLog.error_message).order_by(desc('error_count')).limit(20).all()

            # Platform-specific failures
            platform_failures = session.query(
                DeviceToken.platform,
                func.count(NotificationLog.id).label('failure_count'),
            ).join(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.FAILED,
                )
            ).group_by(DeviceToken.platform).all()

            # Retry analysis
            retry_analysis = session.query(
                NotificationLog.retry_count,
                func.count(NotificationLog.id).label('notification_count'),
                func.sum(case([(NotificationLog.status == NotificationStatus.SENT, 1)], else_=0)).label('eventually_sent'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.retry_count > 0,
                )
            ).group_by(NotificationLog.retry_count).order_by(NotificationLog.retry_count).all()

            # Recent error details
            recent_errors = failed_query.order_by(desc(NotificationLog.created_at)).limit(limit).all()

            error_details = []
            for error in recent_errors:
                error_details.append({
                    "id": error.id,
                    "created_at": error.created_at.isoformat(),
                    "title": error.title,
                    "error_message": error.error_message,
                    "retry_count": error.retry_count,
                    "priority": error.priority,
                    "fcm_message_id": error.fcm_message_id,
                })

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_failed": total_failed,
                },
                "error_patterns": [
                    {"error_message": row.error_message, "count": row.error_count}
                    for row in error_patterns
                ],
                "platform_failures": [
                    {"platform": row.platform, "failure_count": row.failure_count}
                    for row in platform_failures
                ],
                "retry_analysis": [
                    {
                        "retry_count": row.retry_count,
                        "notification_count": row.notification_count,
                        "eventually_sent": row.eventually_sent,
                        "recovery_rate": round(row.eventually_sent / row.notification_count, 4)
                        if row.notification_count > 0 else 0,
                    }
                    for row in retry_analysis
                ],
                "recent_errors": error_details,
            }

        except Exception as e:
            logger.error(f"Failed to get error analysis: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_device_analytics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get device and platform analytics.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with device analytics
        """
        try:
            session = self.db_session or await get_database_session()

            # Default date range
            if not start_date:
                start_date = datetime.now(UTC) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(UTC)

            # Active devices
            total_devices = session.query(DeviceToken).filter(DeviceToken.is_active).count()

            # Platform distribution
            platform_distribution = session.query(
                DeviceToken.platform,
                func.count(DeviceToken.id).label('device_count'),
            ).filter(DeviceToken.is_active).group_by(DeviceToken.platform).all()

            # Device engagement (devices that received notifications)
            engaged_devices = session.query(DeviceToken.id).join(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                    NotificationLog.status == NotificationStatus.SENT,
                    DeviceToken.is_active,
                )
            ).distinct().count()

            # Topic subscription stats
            subscription_stats = session.query(
                TopicSubscription.topic,
                func.count(TopicSubscription.id).label('subscriber_count'),
            ).filter(TopicSubscription.is_active).group_by(TopicSubscription.topic).order_by(desc('subscriber_count')).limit(20).all()

            # Device activity (last seen)
            now = datetime.now(UTC)
            device_activity = session.query(
                case([
                    (DeviceToken.last_seen >= now - timedelta(days=1), 'active_24h'),
                    (DeviceToken.last_seen >= now - timedelta(days=7), 'active_7d'),
                    (DeviceToken.last_seen >= now - timedelta(days=30), 'active_30d'),
                ], else_='inactive').label('activity_period'),
                func.count(DeviceToken.id).label('device_count'),
            ).filter(DeviceToken.is_active).group_by('activity_period').all()

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "device_summary": {
                    "total_active_devices": total_devices,
                    "engaged_devices": engaged_devices,
                    "engagement_rate": round(engaged_devices / total_devices, 4) if total_devices > 0 else 0,
                },
                "platform_distribution": [
                    {"platform": row.platform, "device_count": row.device_count}
                    for row in platform_distribution
                ],
                "top_topics": [
                    {"topic": row.topic, "subscriber_count": row.subscriber_count}
                    for row in subscription_stats
                ],
                "device_activity": [
                    {"period": row.activity_period, "device_count": row.device_count}
                    for row in device_activity
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get device analytics: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_performance_insights(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get performance insights and optimization recommendations.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with performance insights and recommendations
        """
        try:
            session = self.db_session or await get_database_session()

            # Default date range
            if not start_date:
                start_date = datetime.now(UTC) - timedelta(days=7)
            if not end_date:
                end_date = datetime.now(UTC)

            insights = []
            recommendations = []

            # Analyze delivery times by hour
            hourly_performance = session.query(
                extract('hour', NotificationLog.created_at).label('hour'),
                func.count(NotificationLog.id).label('total'),
                func.sum(case([(NotificationLog.status == NotificationStatus.SENT, 1)], else_=0)).label('sent'),
                func.avg(
                    case([
                        (NotificationLog.sent_at.isnot(None),
                         func.extract('epoch', NotificationLog.sent_at - NotificationLog.created_at))
                    ])
                ).label('avg_delivery_time'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).group_by('hour').order_by('hour').all()

            # Find best and worst performing hours
            if hourly_performance:
                best_hour = max(hourly_performance, key=lambda x: x.sent / x.total if x.total > 0 else 0)
                worst_hour = min(hourly_performance, key=lambda x: x.sent / x.total if x.total > 0 else 0)

                insights.append({
                    "type": "time_optimization",
                    "title": "Optimal Delivery Hours",
                    "description": f"Hour {best_hour.hour}:00 has the highest success rate ({best_hour.sent/best_hour.total:.2%}), "
                                 f"while hour {worst_hour.hour}:00 has the lowest ({worst_hour.sent/worst_hour.total:.2%})",
                    "data": {
                        "best_hour": best_hour.hour,
                        "best_success_rate": best_hour.sent / best_hour.total if best_hour.total > 0 else 0,
                        "worst_hour": worst_hour.hour,
                        "worst_success_rate": worst_hour.sent / worst_hour.total if worst_hour.total > 0 else 0,
                    }
                })

                recommendations.append({
                    "priority": "medium",
                    "category": "timing",
                    "title": "Optimize Delivery Timing",
                    "description": f"Schedule non-urgent notifications during hour {best_hour.hour}:00 for better delivery rates",
                })

            # Analyze template performance
            template_perf = session.query(
                NotificationTemplate.name,
                func.count(NotificationLog.id).label('total'),
                func.sum(case([(NotificationLog.status == NotificationStatus.FAILED, 1)], else_=0)).label('failed'),
            ).join(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).group_by(NotificationTemplate.name).having(func.count(NotificationLog.id) > 10).all()

            # Find templates with high failure rates
            high_failure_templates = [
                t for t in template_perf
                if t.total > 0 and (t.failed / t.total) > 0.1  # >10% failure rate
            ]

            if high_failure_templates:
                worst_template = max(high_failure_templates, key=lambda x: x.failed / x.total)
                insights.append({
                    "type": "template_performance",
                    "title": "Template Issues Detected",
                    "description": f"Template '{worst_template.name}' has a high failure rate ({worst_template.failed/worst_template.total:.2%})",
                    "data": {
                        "template_name": worst_template.name,
                        "failure_rate": worst_template.failed / worst_template.total,
                        "total_sent": worst_template.total,
                    }
                })

                recommendations.append({
                    "priority": "high",
                    "category": "template",
                    "title": "Review High-Failure Templates",
                    "description": f"Investigate and optimize template '{worst_template.name}' due to high failure rate",
                })

            # Analyze retry effectiveness
            retry_effectiveness = session.query(
                func.sum(case([(NotificationLog.retry_count > 0, 1)], else_=0)).label('retried'),
                func.sum(case([
                    (and_(NotificationLog.retry_count > 0, NotificationLog.status == NotificationStatus.SENT), 1)
                ], else_=0)).label('recovered'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).first()

            if retry_effectiveness and retry_effectiveness.retried > 0:
                recovery_rate = retry_effectiveness.recovered / retry_effectiveness.retried
                insights.append({
                    "type": "retry_effectiveness",
                    "title": "Retry System Performance",
                    "description": f"Retry system recovered {recovery_rate:.2%} of failed notifications",
                    "data": {
                        "total_retried": retry_effectiveness.retried,
                        "recovered": retry_effectiveness.recovered,
                        "recovery_rate": recovery_rate,
                    }
                })

                if recovery_rate < 0.5:  # Less than 50% recovery
                    recommendations.append({
                        "priority": "medium",
                        "category": "reliability",
                        "title": "Improve Retry Strategy",
                        "description": "Consider adjusting retry intervals or limits to improve recovery rate",
                    })

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "insights": insights,
                "recommendations": recommendations,
                "hourly_performance": [
                    {
                        "hour": row.hour,
                        "total": row.total,
                        "sent": row.sent,
                        "success_rate": row.sent / row.total if row.total > 0 else 0,
                        "avg_delivery_time": row.avg_delivery_time or 0,
                    }
                    for row in hourly_performance
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get performance insights: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def _get_time_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
    ) -> list[dict[str, Any]]:
        """Get notification trends grouped by time period."""
        try:
            session = self.db_session or await get_database_session()

            # Determine SQL date grouping based on group_by parameter
            if group_by == "hour":
                date_trunc = func.date_trunc('hour', NotificationLog.created_at)
            elif group_by == "day":
                date_trunc = func.date_trunc('day', NotificationLog.created_at)
            elif group_by == "week":
                date_trunc = func.date_trunc('week', NotificationLog.created_at)
            elif group_by == "month":
                date_trunc = func.date_trunc('month', NotificationLog.created_at)
            else:
                date_trunc = func.date_trunc('day', NotificationLog.created_at)

            # Query trends
            trends = session.query(
                date_trunc.label('period'),
                func.count(NotificationLog.id).label('total'),
                func.sum(case([(NotificationLog.status == NotificationStatus.SENT, 1)], else_=0)).label('sent'),
                func.sum(case([(NotificationLog.status == NotificationStatus.FAILED, 1)], else_=0)).label('failed'),
                func.sum(case([(NotificationLog.status == NotificationStatus.PENDING, 1)], else_=0)).label('pending'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).group_by('period').order_by('period').all()

            return [
                {
                    "period": row.period.isoformat(),
                    "total": row.total,
                    "sent": row.sent,
                    "failed": row.failed,
                    "pending": row.pending,
                    "success_rate": row.sent / row.total if row.total > 0 else 0,
                }
                for row in trends
            ]

        except Exception as e:
            logger.error(f"Failed to get time trends: {str(e)}")
            return []

    async def _get_platform_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get notification statistics by platform."""
        try:
            session = self.db_session or await get_database_session()

            platform_stats = session.query(
                DeviceToken.platform,
                func.count(NotificationLog.id).label('total'),
                func.sum(case([(NotificationLog.status == NotificationStatus.SENT, 1)], else_=0)).label('sent'),
                func.sum(case([(NotificationLog.status == NotificationStatus.FAILED, 1)], else_=0)).label('failed'),
            ).join(NotificationLog).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).group_by(DeviceToken.platform).all()

            return [
                {
                    "platform": row.platform,
                    "total": row.total,
                    "sent": row.sent,
                    "failed": row.failed,
                    "success_rate": row.sent / row.total if row.total > 0 else 0,
                }
                for row in platform_stats
            ]

        except Exception as e:
            logger.error(f"Failed to get platform breakdown: {str(e)}")
            return []

    async def _get_priority_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get notification statistics by priority."""
        try:
            session = self.db_session or await get_database_session()

            priority_stats = session.query(
                NotificationLog.priority,
                func.count(NotificationLog.id).label('total'),
                func.sum(case([(NotificationLog.status == NotificationStatus.SENT, 1)], else_=0)).label('sent'),
                func.sum(case([(NotificationLog.status == NotificationStatus.FAILED, 1)], else_=0)).label('failed'),
                func.avg(
                    case([
                        (NotificationLog.sent_at.isnot(None),
                         func.extract('epoch', NotificationLog.sent_at - NotificationLog.created_at))
                    ])
                ).label('avg_delivery_time'),
            ).filter(
                and_(
                    NotificationLog.created_at >= start_date,
                    NotificationLog.created_at <= end_date,
                )
            ).group_by(NotificationLog.priority).all()

            return [
                {
                    "priority": row.priority,
                    "total": row.total,
                    "sent": row.sent,
                    "failed": row.failed,
                    "success_rate": row.sent / row.total if row.total > 0 else 0,
                    "avg_delivery_time_seconds": row.avg_delivery_time or 0,
                }
                for row in priority_stats
            ]

        except Exception as e:
            logger.error(f"Failed to get priority breakdown: {str(e)}")
            return []
