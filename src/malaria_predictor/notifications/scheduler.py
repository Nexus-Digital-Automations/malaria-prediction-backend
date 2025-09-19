"""
Notification Scheduling and Delivery Optimization System.

This module provides comprehensive notification scheduling with intelligent delivery
optimization, batch processing, retry logic, and timezone-aware scheduling for
optimal user engagement and system performance.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import Celery
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database.session import get_database_session
from .fcm_service import (
    AndroidConfig,
    APNSConfig,
    FCMMessageData,
    FCMService,
    WebConfig,
)
from .models import (
    DeviceToken,
    NotificationLog,
    NotificationPriority,
    NotificationStatus,
)
from .templates import MessageComposer, NotificationTemplateEngine, TemplateContext

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Advanced notification scheduling system with delivery optimization.

    Provides intelligent scheduling, batch processing, retry logic,
    and timezone-aware delivery for maximum user engagement.
    """

    def __init__(
        self,
        fcm_service: FCMService,
        template_engine: NotificationTemplateEngine,
        celery_app: Celery | None = None,
        db_session: Session | None = None,
    ):
        """
        Initialize notification scheduler.

        Args:
            fcm_service: FCM service for message delivery
            template_engine: Template engine for message composition
            celery_app: Celery app for background task processing
            db_session: Database session (will create if not provided)
        """
        self.fcm_service = fcm_service
        self.template_engine = template_engine
        self.message_composer = MessageComposer(template_engine)
        self.celery_app = celery_app
        self.db_session = db_session
        self._should_close_session = db_session is None

        self.settings = settings

        # Delivery optimization settings
        self.batch_size = 500  # FCM maximum batch size
        self.max_retries = 3
        self.retry_backoff = [60, 300, 900]  # 1 min, 5 min, 15 min
        self.rate_limit_per_minute = 1000

        # Priority delivery windows (UTC hours)
        self.delivery_windows = {
            NotificationPriority.CRITICAL: None,  # Send immediately
            NotificationPriority.HIGH: (6, 22),   # 6 AM - 10 PM local time
            NotificationPriority.NORMAL: (8, 20), # 8 AM - 8 PM local time
            NotificationPriority.LOW: (10, 18),   # 10 AM - 6 PM local time
        }

        logger.info("Notification scheduler initialized with delivery optimization")

    async def __aenter__(self):
        """Async context manager entry."""
        if self._should_close_session:
            self.db_session = await get_database_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_session and self.db_session:
            await self.db_session.close()

    async def schedule_notification(
        self,
        template_name: str,
        context: TemplateContext,
        target_type: str,  # "device", "topic", "user"
        target_value: str,
        scheduled_time: datetime | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        max_retries: int | None = None,
    ) -> int | None:
        """
        Schedule a notification for future delivery.

        Args:
            template_name: Name of notification template
            context: Template context for message rendering
            target_type: Type of target (device, topic, user)
            target_value: Target identifier
            scheduled_time: When to send (None for immediate)
            priority: Notification priority level
            max_retries: Maximum retry attempts

        Returns:
            Notification log ID if successful, None otherwise
        """
        try:
            session = self.db_session or await get_database_session()

            # Get template from database or built-in templates
            template = await self._get_template(template_name)
            if not template:
                logger.error(f"Template '{template_name}' not found")
                return None

            # Render message content
            rendered = self.template_engine.render_template(template, context)

            # Optimize delivery time if not specified
            if scheduled_time is None:
                scheduled_time = self._optimize_delivery_time(priority, target_value)

            # Create notification log entry
            notification_log = NotificationLog(
                template_id=template.id if hasattr(template, 'id') else None,
                title=rendered["title"],
                body=rendered["body"],
                data_payload=context.custom_data,
                status=NotificationStatus.PENDING,
                priority=priority,
                scheduled_at=scheduled_time,
                max_retries=max_retries or self.max_retries,
            )

            # Set target based on type
            if target_type == "device":
                device = session.query(DeviceToken).filter(
                    DeviceToken.token == target_value
                ).first()
                if device:
                    notification_log.device_id = device.id
                else:
                    logger.error(f"Device not found: {target_value}")
                    return None
            elif target_type == "topic":
                notification_log.topic = target_value
            else:
                logger.error(f"Unsupported target type: {target_type}")
                return None

            session.add(notification_log)
            session.commit()

            # Schedule delivery task
            if self.celery_app:
                self._schedule_celery_task(notification_log.id, scheduled_time)
            else:
                # Fall back to immediate delivery for testing
                await self._deliver_notification(notification_log.id)

            logger.info(f"Scheduled notification {notification_log.id} for {scheduled_time}")
            return notification_log.id

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to schedule notification: {str(e)}")
            return None

        finally:
            if self._should_close_session and session:
                session.close()

    async def schedule_bulk_notifications(
        self,
        notifications: list[dict[str, Any]],
        batch_size: int | None = None,
    ) -> list[int | None]:
        """
        Schedule multiple notifications efficiently.

        Args:
            notifications: List of notification configurations
            batch_size: Batch size for processing

        Returns:
            List of notification log IDs
        """
        batch_size = batch_size or 100
        results = []

        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            batch_results = []

            for notif_config in batch:
                try:
                    notification_id = await self.schedule_notification(**notif_config)
                    batch_results.append(notification_id)
                except Exception as e:
                    logger.error(f"Failed to schedule notification in batch: {str(e)}")
                    batch_results.append(None)

            results.extend(batch_results)

            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < len(notifications):
                await asyncio.sleep(0.1)

        logger.info(f"Scheduled {len([r for r in results if r])} of {len(notifications)} notifications")
        return results

    async def send_immediate_notification(
        self,
        template_name: str,
        context: TemplateContext,
        target_type: str,
        target_value: str,
        priority: NotificationPriority = NotificationPriority.HIGH,
    ) -> tuple[bool, int | None, str | None]:
        """
        Send a notification immediately without scheduling.

        Args:
            template_name: Name of notification template
            context: Template context for message rendering
            target_type: Type of target (device, topic, user)
            target_value: Target identifier
            priority: Notification priority level

        Returns:
            Tuple of (success, notification_id, error_message)
        """
        try:
            # Schedule for immediate delivery
            notification_id = await self.schedule_notification(
                template_name=template_name,
                context=context,
                target_type=target_type,
                target_value=target_value,
                scheduled_time=datetime.now(UTC),
                priority=priority,
            )

            if not notification_id:
                return False, None, "Failed to create notification"

            # Deliver immediately
            success, error = await self._deliver_notification(notification_id)
            return success, notification_id, error

        except Exception as e:
            error_msg = f"Failed to send immediate notification: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    async def process_pending_notifications(self) -> int:
        """
        Process all pending scheduled notifications.

        Returns:
            Number of notifications processed
        """
        try:
            session = self.db_session or await get_database_session()

            # Get pending notifications that are due
            now = datetime.now(UTC)
            pending_notifications = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.status == NotificationStatus.PENDING,
                    or_(
                        NotificationLog.scheduled_at.is_(None),
                        NotificationLog.scheduled_at <= now,
                    ),
                )
            ).order_by(
                NotificationLog.priority.desc(),
                NotificationLog.scheduled_at.asc(),
            ).all()

            processed_count = 0

            # Process notifications in batches by priority
            for priority in [NotificationPriority.CRITICAL, NotificationPriority.HIGH,
                           NotificationPriority.NORMAL, NotificationPriority.LOW]:

                priority_notifications = [
                    n for n in pending_notifications if n.priority == priority
                ]

                if not priority_notifications:
                    continue

                # Process in batches
                for i in range(0, len(priority_notifications), self.batch_size):
                    batch = priority_notifications[i:i + self.batch_size]

                    # Process batch concurrently
                    tasks = [
                        self._deliver_notification(notification.id)
                        for notification in batch
                    ]

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if not isinstance(result, Exception) and result[0]:
                            processed_count += 1

                    # Rate limiting between batches
                    if i + self.batch_size < len(priority_notifications):
                        await asyncio.sleep(60 / self.rate_limit_per_minute)

            logger.info(f"Processed {processed_count} pending notifications")
            return processed_count

        except Exception as e:
            logger.error(f"Failed to process pending notifications: {str(e)}")
            return 0

        finally:
            if self._should_close_session and session:
                session.close()

    async def retry_failed_notifications(self) -> int:
        """
        Retry failed notifications that haven't exceeded max retry count.

        Returns:
            Number of notifications retried
        """
        try:
            session = self.db_session or await get_database_session()

            # Get failed notifications eligible for retry
            failed_notifications = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.status == NotificationStatus.FAILED,
                    NotificationLog.retry_count < NotificationLog.max_retries,
                )
            ).order_by(NotificationLog.priority.desc()).all()

            retried_count = 0

            for notification in failed_notifications:
                try:
                    # Calculate next retry time with exponential backoff
                    retry_delay = self.retry_backoff[
                        min(notification.retry_count, len(self.retry_backoff) - 1)
                    ]

                    # Check if enough time has passed for retry
                    if notification.sent_at:
                        next_retry = notification.sent_at + timedelta(seconds=retry_delay)
                        if datetime.now(UTC) < next_retry:
                            continue

                    # Increment retry count
                    notification.retry_count += 1
                    notification.status = NotificationStatus.PENDING

                    # Retry delivery
                    success, error = await self._deliver_notification(notification.id)
                    if success:
                        retried_count += 1

                except Exception as e:
                    logger.error(f"Failed to retry notification {notification.id}: {str(e)}")

            session.commit()

            logger.info(f"Retried {retried_count} failed notifications")
            return retried_count

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to retry notifications: {str(e)}")
            return 0

        finally:
            if self._should_close_session and session:
                session.close()

    async def _deliver_notification(self, notification_id: int) -> tuple[bool, str | None]:
        """
        Deliver a specific notification.

        Args:
            notification_id: ID of notification to deliver

        Returns:
            Tuple of (success, error_message)
        """
        try:
            session = self.db_session or await get_database_session()

            notification = session.query(NotificationLog).filter(
                NotificationLog.id == notification_id
            ).first()

            if not notification:
                return False, "Notification not found"

            # Prepare FCM message data
            message_data = FCMMessageData(
                title=notification.title,
                body=notification.body,
                data=notification.data_payload or {},
                priority=notification.priority,
            )

            # Get platform-specific configurations
            android_config = None
            apns_config = None
            web_config = None

            if notification.template and notification.template.android_config:
                android_config = AndroidConfig(**notification.template.android_config)
            if notification.template and notification.template.ios_config:
                apns_config = APNSConfig(**notification.template.ios_config)
            if notification.template and notification.template.web_config:
                web_config = WebConfig(**notification.template.web_config)

            # Send notification
            success = False
            fcm_message_id = None
            error_message = None

            notification.sent_at = datetime.now(UTC)

            if notification.device_id:
                # Send to specific device
                device = session.query(DeviceToken).filter(
                    DeviceToken.id == notification.device_id
                ).first()

                if device and device.is_active:
                    success, fcm_message_id, error_message = await self.fcm_service.send_to_token(
                        token=device.token,
                        message_data=message_data,
                        android_config=android_config,
                        apns_config=apns_config,
                        web_config=web_config,
                    )
                else:
                    error_message = "Device not found or inactive"

            elif notification.topic:
                # Send to topic
                success, fcm_message_id, error_message = await self.fcm_service.send_to_topic(
                    topic=notification.topic,
                    message_data=message_data,
                    android_config=android_config,
                    apns_config=apns_config,
                    web_config=web_config,
                )

            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.fcm_message_id = fcm_message_id
                logger.debug(f"Successfully delivered notification {notification_id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = error_message
                logger.warning(f"Failed to deliver notification {notification_id}: {error_message}")

            session.commit()
            return success, error_message

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Error delivering notification {notification_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            if self._should_close_session and session:
                session.close()

    def _optimize_delivery_time(
        self,
        priority: NotificationPriority,
        target_value: str,
        timezone_offset: int | None = None,
    ) -> datetime:
        """
        Optimize delivery time based on priority and user timezone.

        Args:
            priority: Notification priority level
            target_value: Target identifier for timezone lookup
            timezone_offset: Manual timezone offset in hours

        Returns:
            Optimized delivery time
        """
        now = datetime.now(UTC)

        # Critical notifications send immediately
        if priority == NotificationPriority.CRITICAL:
            return now

        # Get delivery window for priority
        delivery_window = self.delivery_windows.get(priority)
        if not delivery_window:
            return now

        start_hour, end_hour = delivery_window

        # Estimate user timezone (simplified - in production, store user timezones)
        if timezone_offset is None:
            timezone_offset = 0  # Default to UTC

        # Calculate local time
        local_now = now + timedelta(hours=timezone_offset)
        local_hour = local_now.hour

        # If within delivery window, send now
        if start_hour <= local_hour <= end_hour:
            return now

        # If before window, schedule for start of window
        if local_hour < start_hour:
            next_delivery = local_now.replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
        # If after window, schedule for next day's start
        else:
            next_delivery = local_now.replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)

        # Convert back to UTC
        return next_delivery - timedelta(hours=timezone_offset)

    async def _get_template(self, template_name: str):
        """Get template by name from database or built-in templates."""
        try:
            session = self.db_session or await get_database_session()

            # Try to get from database first
            from .models import NotificationTemplate
            template = session.query(NotificationTemplate).filter(
                NotificationTemplate.name == template_name
            ).first()

            if template:
                return template

            # Fall back to built-in templates
            built_in_templates = {
                "malaria_risk_alert": self.template_engine.create_malaria_alert_template(),
                "outbreak_warning": self.template_engine.create_outbreak_warning_template(),
                "daily_risk_summary": self.template_engine.create_daily_summary_template(),
                "medication_reminder": self.template_engine.create_medication_reminder_template(),
                "travel_alert": self.template_engine.create_travel_alert_template(),
            }

            return built_in_templates.get(template_name)

        except Exception as e:
            logger.error(f"Failed to get template '{template_name}': {str(e)}")
            return None

        finally:
            if self._should_close_session and session:
                session.close()

    def _schedule_celery_task(self, notification_id: int, scheduled_time: datetime):
        """Schedule notification delivery using Celery."""
        if not self.celery_app:
            return

        # Calculate delay in seconds
        delay = (scheduled_time - datetime.now(UTC)).total_seconds()
        delay = max(0, delay)  # Don't schedule in the past

        # Schedule Celery task
        self.celery_app.send_task(
            "notifications.deliver_notification",
            args=[notification_id],
            countdown=delay,
        )

    async def get_delivery_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive delivery statistics.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Dictionary with delivery statistics
        """
        try:
            session = self.db_session or await get_database_session()

            # Default to last 7 days if no dates provided
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
            sent_notifications = base_query.filter(
                NotificationLog.status == NotificationStatus.SENT
            ).count()
            failed_notifications = base_query.filter(
                NotificationLog.status == NotificationStatus.FAILED
            ).count()
            pending_notifications = base_query.filter(
                NotificationLog.status == NotificationStatus.PENDING
            ).count()

            # Statistics by priority
            priority_stats = {}
            for priority in NotificationPriority:
                count = base_query.filter(NotificationLog.priority == priority).count()
                priority_stats[priority] = count

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
                )
            ).scalar()

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "totals": {
                    "total": total_notifications,
                    "sent": sent_notifications,
                    "failed": failed_notifications,
                    "pending": pending_notifications,
                },
                "success_rate": sent_notifications / total_notifications if total_notifications > 0 else 0,
                "priority_breakdown": priority_stats,
                "average_delivery_time_seconds": avg_delivery_time or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get delivery statistics: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()
