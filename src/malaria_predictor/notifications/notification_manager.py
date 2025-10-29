"""
Comprehensive Notification Manager.

This module provides a unified interface for all notification operations,
coordinating FCM services, scheduling, templates, analytics, and emergency alerts
to deliver a complete push notification system.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..database.session import get_database_session
from .analytics import NotificationAnalytics
from .emergency_alerts import (
    EmergencyAlertSystem,
    EmergencyLevel,
)
from .fcm_service import FCMService
from .models import (
    DevicePlatform,
    DeviceToken,
    NotificationLog,
    NotificationPriority,
    TopicSubscription,
)
from .scheduler import NotificationScheduler
from .templates import MessageComposer, NotificationTemplateEngine, TemplateContext
from .topic_manager import TopicManager

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Comprehensive notification management system.

    Provides a unified interface for all notification operations including
    device management, template rendering, scheduling, emergency alerts,
    and analytics. Coordinates all notification subsystems.
    """

    def __init__(
        self,
        fcm_credentials_path: str | None = None,
        project_id: str | None = None,
        celery_app: Any | None = None,
        db_session: Session | None = None,
    ):
        """
        Initialize notification manager with all subsystems.

        Args:
            fcm_credentials_path: Path to Firebase service account JSON
            project_id: Firebase project ID
            celery_app: Celery app for background tasks
            db_session: Database session (will create if not provided)
        """
        self.settings = settings
        self.db_session = db_session
        self._should_close_session = db_session is None

        # Initialize core services
        self.fcm_service = FCMService(fcm_credentials_path, project_id)
        self.template_engine = NotificationTemplateEngine()
        self.message_composer = MessageComposer(self.template_engine)

        # Initialize advanced services
        self.scheduler = NotificationScheduler(
            self.fcm_service,
            self.template_engine,
            celery_app,
            db_session,
        )
        self.topic_manager = TopicManager(self.fcm_service, db_session)
        self.emergency_system = EmergencyAlertSystem(
            self.fcm_service,
            self.template_engine,
            self.scheduler,
            db_session,
        )
        self.analytics = NotificationAnalytics(db_session)

        logger.info("Comprehensive notification manager initialized")

    async def __aenter__(self) -> "NotificationManager":
        """Async context manager entry."""
        if self._should_close_session:
            self.db_session = await get_database_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_session and self.db_session:
            await self.db_session.close()

    # Device Management
    async def register_device(
        self,
        token: str,
        platform: DevicePlatform,
        user_id: str | None = None,
        device_info: dict[str, Any] | None = None,
        auto_subscribe: bool = True,
        user_preferences: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Register a new device for push notifications.

        Args:
            token: FCM device token
            platform: Device platform (android, ios, web)
            user_id: Optional user ID association
            device_info: Device metadata
            auto_subscribe: Whether to auto-subscribe to relevant topics
            user_preferences: User preferences for subscription

        Returns:
            Tuple of (success, error_message)
        """
        try:
            session = self.db_session or await get_database_session()

            # Validate token
            is_valid = await self.fcm_service.validate_token(token)
            if not is_valid:
                return False, "Invalid FCM token"

            # Check if device already exists
            existing_device = session.query(DeviceToken).filter(
                DeviceToken.token == token
            ).first()

            if existing_device:
                # Update existing device
                existing_device.is_active = True
                existing_device.last_seen = datetime.now(UTC)
                existing_device.user_id = user_id or existing_device.user_id
                existing_device.device_info = device_info or existing_device.device_info
                device = existing_device
            else:
                # Create new device
                device = DeviceToken(
                    token=token,
                    platform=platform,
                    user_id=user_id,
                    device_info=device_info or {},
                    is_active=True,
                    last_seen=datetime.now(UTC),
                )
                session.add(device)

            session.commit()

            # Auto-subscribe to relevant topics
            if auto_subscribe:
                subscribed_topics = await self.topic_manager.auto_subscribe_device(
                    token,
                    user_location=user_preferences.get("location") if user_preferences else None,
                    user_preferences=user_preferences,
                    language=user_preferences.get("language", "en") if user_preferences else "en",
                )
                logger.info(f"Auto-subscribed device to topics: {subscribed_topics}")

            logger.info(f"Device registered successfully: {token[:10]}... (platform: {platform})")
            return True, None

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Failed to register device: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            if self._should_close_session and session:
                session.close()

    async def unregister_device(self, token: str) -> tuple[bool, str | None]:
        """
        Unregister a device from push notifications.

        Args:
            token: FCM device token

        Returns:
            Tuple of (success, error_message)
        """
        try:
            session = self.db_session or await get_database_session()

            device = session.query(DeviceToken).filter(
                DeviceToken.token == token
            ).first()

            if not device:
                return False, "Device not found"

            # Deactivate device
            device.is_active = False

            # Deactivate all subscriptions
            session.query(TopicSubscription).filter(
                TopicSubscription.device_id == device.id
            ).update({"is_active": False})

            session.commit()

            logger.info(f"Device unregistered: {token[:10]}...")
            return True, None

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Failed to unregister device: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            if self._should_close_session and session:
                session.close()

    # Notification Sending
    async def send_malaria_alert(
        self,
        risk_score: float,
        location_name: str,
        coordinates: dict[str, float] | None = None,
        environmental_data: dict[str, float] | None = None,
        target_users: list[str] | None = None,
        target_radius_km: float | None = None,
        immediate: bool = True,
    ) -> dict[str, Any]:
        """
        Send malaria risk alert to targeted users.

        Args:
            risk_score: Risk score (0.0 to 1.0)
            location_name: Human-readable location name
            coordinates: Geographic coordinates
            environmental_data: Environmental conditions
            target_users: Specific user IDs to target (optional)
            target_radius_km: Geographic targeting radius
            immediate: Whether to send immediately

        Returns:
            Dictionary with sending results
        """
        try:
            # Compose alert message
            alert_data = self.message_composer.compose_malaria_alert(
                risk_score=risk_score,
                location_name=location_name,
                coordinates=coordinates,
                environmental_data=environmental_data,
            )

            # Determine priority based on risk score
            if risk_score >= 0.8:
                priority = NotificationPriority.CRITICAL
            elif risk_score >= 0.6:
                priority = NotificationPriority.HIGH
            else:
                priority = NotificationPriority.NORMAL

            # Create template context
            env_data = environmental_data or {}
            context = TemplateContext(
                risk_score=risk_score,
                risk_level=alert_data.get("risk_level", "medium"),
                location_name=location_name,
                coordinates=coordinates,
                temperature=env_data.get("temperature"),
                humidity=env_data.get("humidity"),
                precipitation=env_data.get("precipitation"),
                vegetation_index=env_data.get("vegetation_index"),
            )

            # Send to geographic topic if no specific users
            if not target_users:
                topic = await self.topic_manager.create_geographic_topic(
                    location_name, coordinates, target_radius_km
                )

                if immediate:
                    success, notification_id, error = await self.scheduler.send_immediate_notification(
                        template_name="malaria_risk_alert",
                        context=context,
                        target_type="topic",
                        target_value=topic,
                        priority=priority,
                    )
                else:
                    notification_id = await self.scheduler.schedule_notification(
                        template_name="malaria_risk_alert",
                        context=context,
                        target_type="topic",
                        target_value=topic,
                        priority=priority,
                    )
                    success = notification_id is not None
                    error = None if success else "Failed to schedule notification"

                return {
                    "success": success,
                    "notification_id": notification_id,
                    "error": error,
                    "target_type": "topic",
                    "target_value": topic,
                    "priority": priority,
                }

            else:
                # Send to specific users
                results = []
                for user_id in target_users:
                    # Find user's devices
                    session = self.db_session or await get_database_session()
                    user_devices = session.query(DeviceToken).filter(
                        DeviceToken.user_id == user_id,
                        DeviceToken.is_active,
                    ).all()

                    for device in user_devices:
                        if immediate:
                            success, notification_id, error = await self.scheduler.send_immediate_notification(
                                template_name="malaria_risk_alert",
                                context=context,
                                target_type="device",
                                target_value=str(device.token),
                                priority=priority,
                            )
                        else:
                            notification_id = await self.scheduler.schedule_notification(
                                template_name="malaria_risk_alert",
                                context=context,
                                target_type="device",
                                target_value=str(device.token),
                                priority=priority,
                            )
                            success = notification_id is not None
                            error = None if success else "Failed to schedule notification"

                        results.append({
                            "user_id": user_id,
                            "device_token": device.token[:10] + "...",
                            "success": success,
                            "notification_id": notification_id,
                            "error": error,
                        })

                return {
                    "success": any(r["success"] for r in results),
                    "results": results,
                    "total_targeted": len(results),
                    "successful": sum(1 for r in results if r["success"]),
                }

        except Exception as e:
            error_msg = f"Failed to send malaria alert: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    async def send_outbreak_alert(
        self,
        location_name: str,
        outbreak_probability: float,
        affected_population: int | None = None,
        coordinates: dict[str, float] | None = None,
        radius_km: float = 50.0,
        severity: EmergencyLevel | None = None,
    ) -> dict[str, Any]:
        """
        Send emergency outbreak alert.

        Args:
            location_name: Name of affected location
            outbreak_probability: Probability of outbreak (0.0 to 1.0)
            affected_population: Number of people affected
            coordinates: Geographic coordinates
            radius_km: Alert radius in kilometers
            severity: Emergency severity level

        Returns:
            Dictionary with alert results
        """
        try:
            # Create emergency alert
            alert = await self.emergency_system.create_outbreak_alert(
                location_name=location_name,
                outbreak_probability=outbreak_probability,
                affected_population=affected_population,
                coordinates=coordinates,
                radius_km=radius_km,
                severity=severity or EmergencyLevel.WARNING,
            )

            # Issue emergency alert
            result = await self.emergency_system.issue_emergency_alert(alert)

            logger.critical(f"Outbreak alert issued for {location_name}: {result}")
            return result

        except Exception as e:
            error_msg = f"Failed to send outbreak alert: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    async def send_medication_reminder(
        self,
        user_id: str,
        medication_name: str,
        dosage: str | None = None,
        schedule_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Send medication reminder notification.

        Args:
            user_id: Target user ID
            medication_name: Name of medication
            dosage: Dosage information
            schedule_time: When to send reminder

        Returns:
            Dictionary with sending results
        """
        try:
            # Compose reminder message
            self.message_composer.compose_medication_reminder(
                user_id=user_id,
                medication_name=medication_name,
                dosage=dosage,
            )

            context = TemplateContext(
                user_id=user_id,
                custom_data={
                    "medication_name": medication_name,
                    "dosage": dosage,
                },
            )

            # Find user's devices
            session = self.db_session or await get_database_session()
            user_devices = session.query(DeviceToken).filter(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active,
            ).all()

            if not user_devices:
                return {
                    "success": False,
                    "error": "No active devices found for user",
                }

            results = []
            for device in user_devices:
                if schedule_time:
                    notification_id = await self.scheduler.schedule_notification(
                        template_name="medication_reminder",
                        context=context,
                        target_type="device",
                        target_value=str(device.token),
                        scheduled_time=schedule_time,
                        priority=NotificationPriority.NORMAL,
                    )
                    success = notification_id is not None
                    error = None if success else "Failed to schedule reminder"
                else:
                    success, notification_id, error = await self.scheduler.send_immediate_notification(
                        template_name="medication_reminder",
                        context=context,
                        target_type="device",
                        target_value=str(device.token),
                        priority=NotificationPriority.NORMAL,
                    )

                results.append({
                    "device_token": device.token[:10] + "...",
                    "success": success,
                    "notification_id": notification_id,
                    "error": error,
                })

            return {
                "success": any(r["success"] for r in results),
                "results": results,
                "user_id": user_id,
                "medication": medication_name,
            }

        except Exception as e:
            error_msg = f"Failed to send medication reminder: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

        finally:
            if self._should_close_session and session:
                session.close()

    # Topic Management
    async def subscribe_user_to_topics(
        self,
        user_id: str,
        topics: list[str],
    ) -> dict[str, bool]:
        """
        Subscribe all user devices to specified topics.

        Args:
            user_id: User ID
            topics: List of topic names

        Returns:
            Dictionary mapping topics to subscription success
        """
        try:
            session = self.db_session or await get_database_session()

            # Get user's active devices
            user_devices = session.query(DeviceToken).filter(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active,
            ).all()

            if not user_devices:
                return dict.fromkeys(topics, False)

            results = {}
            for topic in topics:
                topic_results = []
                for device in user_devices:
                    success, error = await self.topic_manager.subscribe_device_to_topic(
                        str(device.token), topic
                    )
                    topic_results.append(success)

                # Topic subscription successful if at least one device subscribed
                results[topic] = any(topic_results)

            return results

        except Exception as e:
            logger.error(f"Failed to subscribe user to topics: {str(e)}")
            return dict.fromkeys(topics, False)

        finally:
            if self._should_close_session and session:
                session.close()

    # Analytics and Reporting
    async def get_notification_dashboard(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get comprehensive notification dashboard data.

        Args:
            days: Number of days to include in analysis

        Returns:
            Dictionary with dashboard data
        """
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Get all analytics data
            delivery_summary = await self.analytics.get_delivery_summary(start_date, end_date)
            engagement_metrics = await self.analytics.get_engagement_metrics(start_date, end_date)
            error_analysis = await self.analytics.get_error_analysis(start_date, end_date)
            device_analytics = await self.analytics.get_device_analytics(start_date, end_date)
            performance_insights = await self.analytics.get_performance_insights(start_date, end_date)

            # Get topic statistics
            topic_stats = await self.topic_manager.get_topic_statistics()

            # Get active emergency alerts
            active_alerts = await self.emergency_system.get_active_emergency_alerts()

            return {
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "delivery_summary": delivery_summary,
                "engagement_metrics": engagement_metrics,
                "error_analysis": error_analysis,
                "device_analytics": device_analytics,
                "performance_insights": performance_insights,
                "topic_statistics": topic_stats,
                "active_emergency_alerts": active_alerts,
                "system_health": {
                    "fcm_service": "operational",  # In production, check actual service health
                    "scheduler": "operational",
                    "database": "operational",
                },
            }

        except Exception as e:
            logger.error(f"Failed to get notification dashboard: {str(e)}")
            return {}

    # System Maintenance
    async def cleanup_old_data(
        self,
        notification_retention_days: int = 90,
        inactive_device_days: int = 30,
    ) -> dict[str, int]:
        """
        Clean up old notification data and inactive devices.

        Args:
            notification_retention_days: Days to retain notification logs
            inactive_device_days: Days to consider a device inactive

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            session = self.db_session or await get_database_session()

            cleanup_stats = {
                "deleted_notifications": 0,
                "deactivated_devices": 0,
                "cleaned_subscriptions": 0,
            }

            # Clean up old notification logs
            cutoff_date = datetime.now(UTC) - timedelta(days=notification_retention_days)
            old_notifications = session.query(NotificationLog).filter(
                NotificationLog.created_at < cutoff_date
            )
            cleanup_stats["deleted_notifications"] = old_notifications.count()
            old_notifications.delete()

            # Deactivate inactive devices
            inactive_cutoff = datetime.now(UTC) - timedelta(days=inactive_device_days)
            inactive_devices = session.query(DeviceToken).filter(
                DeviceToken.last_seen < inactive_cutoff,
                DeviceToken.is_active,
            )
            cleanup_stats["deactivated_devices"] = inactive_devices.count()
            inactive_devices.update({"is_active": False})

            # Clean up topic subscriptions for inactive devices
            cleaned_subscriptions = await self.topic_manager.cleanup_inactive_subscriptions(
                inactive_device_days
            )
            cleanup_stats["cleaned_subscriptions"] = cleaned_subscriptions

            session.commit()

            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_system_status(self) -> dict[str, Any]:
        """
        Get comprehensive system status and health metrics.

        Returns:
            Dictionary with system status
        """
        try:
            session = self.db_session or await get_database_session()

            # Get basic counts
            total_devices = session.query(DeviceToken).filter(DeviceToken.is_active).count()
            total_subscriptions = session.query(TopicSubscription).filter(
                TopicSubscription.is_active
            ).count()

            # Get recent activity
            last_hour = datetime.now(UTC) - timedelta(hours=1)
            recent_notifications = session.query(NotificationLog).filter(
                NotificationLog.created_at >= last_hour
            ).count()

            # Get pending notifications
            pending_notifications = session.query(NotificationLog).filter(
                NotificationLog.status == "pending"
            ).count()

            return {
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "metrics": {
                    "active_devices": total_devices,
                    "active_subscriptions": total_subscriptions,
                    "notifications_last_hour": recent_notifications,
                    "pending_notifications": pending_notifications,
                },
                "services": {
                    "fcm_service": "operational",
                    "scheduler": "operational",
                    "topic_manager": "operational",
                    "emergency_system": "operational",
                    "analytics": "operational",
                },
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        finally:
            if self._should_close_session and session:
                session.close()
