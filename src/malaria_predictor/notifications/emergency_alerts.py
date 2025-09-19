"""
Emergency Alert Prioritization and Delivery System.

This module provides critical emergency alert capabilities for malaria outbreaks,
health emergencies, and other urgent public health situations with prioritized
delivery, bypass mechanisms, and multi-channel communication.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

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
    TopicSubscription,
)
from .scheduler import NotificationScheduler
from .templates import NotificationTemplateEngine, TemplateContext

logger = logging.getLogger(__name__)


class EmergencyLevel(str, Enum):
    """Emergency alert severity levels."""
    WATCH = "watch"          # Potential risk, increased monitoring
    ADVISORY = "advisory"    # Moderate risk, take precautions
    WARNING = "warning"      # High risk, immediate action recommended
    EMERGENCY = "emergency"  # Critical risk, urgent action required


class EmergencyType(str, Enum):
    """Types of emergency alerts."""
    OUTBREAK = "outbreak"           # Disease outbreak detected
    EPIDEMIC = "epidemic"           # Large-scale disease spread
    WEATHER_EXTREME = "weather"     # Extreme weather conditions
    VECTOR_SURGE = "vector_surge"   # Mosquito population surge
    HEALTH_SYSTEM = "health_system" # Health system overload
    MEDICATION = "medication"       # Critical medication shortage
    TRAVEL = "travel"              # Travel-related health emergency


class EmergencyAlert(BaseModel):
    """Emergency alert data model."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: EmergencyType = Field(..., description="Type of emergency")
    severity: EmergencyLevel = Field(..., description="Severity level")

    title: str = Field(..., max_length=255, description="Alert title")
    message: str = Field(..., max_length=4000, description="Alert message")

    # Geographic targeting
    affected_regions: list[str] = Field(default_factory=list, description="Affected regions")
    coordinates: dict[str, float] | None = Field(None, description="Geographic coordinates")
    radius_km: float | None = Field(None, description="Alert radius in kilometers")

    # Timing
    alert_start: datetime = Field(default_factory=lambda: datetime.now(UTC))
    alert_end: datetime | None = Field(None, description="Alert expiration time")

    # Targeting
    target_demographics: list[str] = Field(default_factory=list, description="Target demographics")
    exclude_groups: list[str] = Field(default_factory=list, description="Groups to exclude")

    # Actions and information
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions")
    information_url: str | None = Field(None, description="Additional information URL")
    contact_info: str | None = Field(None, description="Emergency contact information")

    # System metadata
    issued_by: str = Field(..., description="Authority issuing the alert")
    source_data: dict[str, Any] | None = Field(None, description="Source data for alert")

    @field_validator('alert_end')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate alert end time is after start time."""
        if v and 'alert_start' in info.data and v <= info.data['alert_start']:
            raise ValueError("Alert end time must be after start time")
        return v


class EmergencyAlertSystem:
    """
    Advanced emergency alert system for critical health notifications.

    Provides prioritized delivery, bypass mechanisms, multi-channel communication,
    and comprehensive tracking for emergency situations.
    """

    def __init__(
        self,
        fcm_service: FCMService,
        template_engine: NotificationTemplateEngine,
        scheduler: NotificationScheduler,
        db_session: Session | None = None,
    ):
        """
        Initialize emergency alert system.

        Args:
            fcm_service: FCM service for notification delivery
            template_engine: Template engine for message composition
            scheduler: Notification scheduler for delivery management
            db_session: Database session (will create if not provided)
        """
        self.fcm_service = fcm_service
        self.template_engine = template_engine
        self.scheduler = scheduler
        self.db_session = db_session
        self._should_close_session = db_session is None

        # Emergency delivery settings
        self.emergency_batch_size = 100  # Smaller batches for faster delivery
        self.emergency_rate_limit = 2000  # Higher rate limit for emergencies
        self.bypass_quiet_hours = True   # Bypass user quiet hour preferences

        # Delivery retry settings for emergencies
        self.emergency_retries = 5
        self.emergency_retry_intervals = [10, 30, 60, 180, 300]  # Faster retry schedule

        logger.info("Emergency alert system initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        if self._should_close_session:
            self.db_session = await get_database_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_session and self.db_session:
            await self.db_session.close()

    async def issue_emergency_alert(
        self,
        alert: EmergencyAlert,
        immediate_delivery: bool = True,
    ) -> dict[str, Any]:
        """
        Issue an emergency alert with prioritized delivery.

        Args:
            alert: Emergency alert configuration
            immediate_delivery: Whether to deliver immediately or schedule

        Returns:
            Dictionary with issuance results and delivery statistics
        """
        try:
            session = self.db_session or await get_database_session()

            logger.critical(f"Issuing emergency alert: {alert.alert_id} - {alert.severity}")

            # Determine notification priority based on emergency level
            notification_priority = self._get_notification_priority(alert.severity)

            # Get target devices based on alert criteria
            target_devices = await self._get_target_devices(alert)

            if not target_devices:
                logger.warning(f"No target devices found for emergency alert {alert.alert_id}")
                return {
                    "success": False,
                    "error": "No target devices found",
                    "alert_id": alert.alert_id,
                }

            # Create template context
            context = self._create_emergency_context(alert)

            # Prepare notification data
            message_data = FCMMessageData(
                title=alert.title,
                body=alert.message,
                data={
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "information_url": alert.information_url or "",
                    "contact_info": alert.contact_info or "",
                },
                priority="high",  # Always high priority for emergencies
                ttl=3600,  # 1 hour TTL for emergency alerts
            )

            # Configure platform-specific emergency settings
            android_config = AndroidConfig(
                priority="high",
                ttl=3600,
                notification_sound="emergency_alert",
                notification_color="#FF0000",  # Red for emergency
                notification_channel_id="emergency_alerts",
            )

            apns_config = APNSConfig(
                sound="emergency.wav",
                badge=1,
                content_available=True,
                mutable_content=True,
            )

            web_config = WebConfig(
                icon="/icons/emergency-192x192.png",
                badge="/icons/emergency-badge-72x72.png",
                require_interaction=True,
                tag=f"emergency_{alert.alert_id}",
            )

            # Track delivery results
            delivery_results = {
                "total_targeted": len(target_devices),
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "delivery_errors": [],
            }

            if immediate_delivery:
                # Immediate delivery for emergencies
                delivery_results = await self._deliver_emergency_immediate(
                    target_devices,
                    message_data,
                    android_config,
                    apns_config,
                    web_config,
                    alert,
                    notification_priority,
                )
            else:
                # Scheduled delivery (for testing or specific timing)
                delivery_results = await self._schedule_emergency_delivery(
                    target_devices,
                    alert,
                    context,
                    notification_priority,
                )

            # Log emergency alert issuance
            await self._log_emergency_alert(alert, delivery_results)

            logger.critical(
                f"Emergency alert {alert.alert_id} issued: "
                f"{delivery_results['successful_deliveries']}/{delivery_results['total_targeted']} delivered"
            )

            return {
                "success": True,
                "alert_id": alert.alert_id,
                "delivery_results": delivery_results,
                "issued_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            error_msg = f"Failed to issue emergency alert {alert.alert_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "alert_id": alert.alert_id,
            }

        finally:
            if self._should_close_session and session:
                session.close()

    async def create_outbreak_alert(
        self,
        location_name: str,
        outbreak_probability: float,
        affected_population: int | None = None,
        coordinates: dict[str, float] | None = None,
        radius_km: float = 50.0,
        severity: EmergencyLevel = EmergencyLevel.WARNING,
    ) -> EmergencyAlert:
        """
        Create a malaria outbreak emergency alert.

        Args:
            location_name: Name of affected location
            outbreak_probability: Probability of outbreak (0.0 to 1.0)
            affected_population: Number of people affected
            coordinates: Geographic coordinates
            radius_km: Alert radius in kilometers
            severity: Emergency severity level

        Returns:
            EmergencyAlert configuration
        """
        alert_id = f"outbreak_{location_name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"

        # Determine severity based on probability
        if outbreak_probability >= 0.8:
            severity = EmergencyLevel.EMERGENCY
        elif outbreak_probability >= 0.6:
            severity = EmergencyLevel.WARNING
        else:
            severity = EmergencyLevel.ADVISORY

        message = f"MALARIA OUTBREAK ALERT: Potential outbreak detected in {location_name}. "
        message += f"Outbreak probability: {outbreak_probability * 100:.1f}%. "

        if affected_population:
            message += f"Estimated {affected_population:,} people at risk. "

        message += "Seek immediate medical attention for fever, chills, or flu-like symptoms. "
        message += "Use mosquito protection and avoid high-risk areas."

        recommended_actions = [
            "Seek medical attention for fever or flu-like symptoms",
            "Use insect repellent and protective clothing",
            "Eliminate standing water around homes",
            "Use bed nets treated with insecticide",
            "Avoid outdoor activities during peak mosquito hours",
        ]

        return EmergencyAlert(
            alert_id=alert_id,
            alert_type=EmergencyType.OUTBREAK,
            severity=severity,
            title=f"🚨 Malaria Outbreak Alert - {location_name}",
            message=message,
            affected_regions=[location_name],
            coordinates=coordinates,
            radius_km=radius_km,
            recommended_actions=recommended_actions,
            issued_by="Malaria Prediction System",
            source_data={
                "outbreak_probability": outbreak_probability,
                "affected_population": affected_population,
                "detection_timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def create_vector_surge_alert(
        self,
        location_name: str,
        mosquito_density_increase: float,
        weather_conditions: dict[str, Any],
        coordinates: dict[str, float] | None = None,
        radius_km: float = 25.0,
    ) -> EmergencyAlert:
        """
        Create a mosquito vector surge alert.

        Args:
            location_name: Name of affected location
            mosquito_density_increase: Percentage increase in mosquito density
            weather_conditions: Current weather conditions
            coordinates: Geographic coordinates
            radius_km: Alert radius in kilometers

        Returns:
            EmergencyAlert configuration
        """
        alert_id = f"vector_surge_{location_name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"

        # Determine severity based on density increase
        if mosquito_density_increase >= 300:
            severity = EmergencyLevel.WARNING
        elif mosquito_density_increase >= 150:
            severity = EmergencyLevel.ADVISORY
        else:
            severity = EmergencyLevel.WATCH

        message = f"MOSQUITO SURGE ALERT: Significant increase in mosquito activity detected in {location_name}. "
        message += f"Mosquito density increased by {mosquito_density_increase:.0f}%. "

        if weather_conditions:
            temp = weather_conditions.get('temperature')
            humidity = weather_conditions.get('humidity')
            if temp and humidity:
                message += f"Current conditions: {temp}°C, {humidity}% humidity - ideal for mosquito breeding. "

        message += "Take enhanced protective measures against mosquito bites."

        return EmergencyAlert(
            alert_id=alert_id,
            alert_type=EmergencyType.VECTOR_SURGE,
            severity=severity,
            title=f"🦟 Mosquito Surge Alert - {location_name}",
            message=message,
            affected_regions=[location_name],
            coordinates=coordinates,
            radius_km=radius_km,
            recommended_actions=[
                "Use strong insect repellent (DEET 20%+)",
                "Wear long sleeves and pants during peak hours",
                "Eliminate all standing water sources",
                "Use fans to disrupt mosquito flight",
                "Consider staying indoors during dawn and dusk",
            ],
            issued_by="Vector Surveillance System",
            source_data={
                "density_increase": mosquito_density_increase,
                "weather_conditions": weather_conditions,
                "surge_detection_timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def cancel_emergency_alert(
        self,
        alert_id: str,
        reason: str,
        send_cancellation_notice: bool = True,
    ) -> dict[str, Any]:
        """
        Cancel an active emergency alert.

        Args:
            alert_id: Alert ID to cancel
            reason: Reason for cancellation
            send_cancellation_notice: Whether to send cancellation notification

        Returns:
            Dictionary with cancellation results
        """
        try:
            session = self.db_session or await get_database_session()

            # Find related notification logs
            related_notifications = session.query(NotificationLog).filter(
                NotificationLog.data_payload.contains({"alert_id": alert_id})
            ).all()

            # Cancel pending notifications
            cancelled_count = 0
            for notification in related_notifications:
                if notification.status == NotificationStatus.PENDING:
                    notification.status = NotificationStatus.CANCELED
                    cancelled_count += 1

            session.commit()

            # Send cancellation notice if requested
            if send_cancellation_notice and related_notifications:
                await self._send_cancellation_notice(alert_id, reason, related_notifications)

            logger.info(f"Cancelled emergency alert {alert_id}: {cancelled_count} pending notifications cancelled")

            return {
                "success": True,
                "alert_id": alert_id,
                "cancelled_notifications": cancelled_count,
                "reason": reason,
                "cancelled_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Failed to cancel emergency alert {alert_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "alert_id": alert_id,
            }

        finally:
            if self._should_close_session and session:
                session.close()

    async def _get_target_devices(self, alert: EmergencyAlert) -> list[DeviceToken]:
        """Get target devices based on alert criteria."""
        try:
            session = self.db_session or await get_database_session()

            # Base query for active devices
            query = session.query(DeviceToken).filter(DeviceToken.is_active)

            # Geographic targeting
            if alert.affected_regions:
                # In a real implementation, you would filter by device location
                # For now, we'll use topic subscriptions for geographic targeting
                topic_filters = []
                for region in alert.affected_regions:
                    region_topic = f"geo_{region.lower().replace(' ', '_')}"
                    topic_filters.append(region_topic)

                if topic_filters:
                    # Get devices subscribed to affected region topics
                    query = query.join(TopicSubscription).filter(
                        and_(
                            TopicSubscription.topic.in_(topic_filters),
                            TopicSubscription.is_active,
                        )
                    )

            # Demographic targeting
            if alert.target_demographics:
                # Filter by user type subscriptions
                demo_topics = [f"type_{demo.lower()}" for demo in alert.target_demographics]
                query = query.join(TopicSubscription).filter(
                    and_(
                        TopicSubscription.topic.in_(demo_topics),
                        TopicSubscription.is_active,
                    )
                )

            # Exclude groups if specified
            if alert.exclude_groups:
                exclude_topics = [f"type_{group.lower()}" for group in alert.exclude_groups]
                excluded_devices = session.query(DeviceToken.id).join(TopicSubscription).filter(
                    and_(
                        TopicSubscription.topic.in_(exclude_topics),
                        TopicSubscription.is_active,
                    )
                )
                query = query.filter(~DeviceToken.id.in_(excluded_devices))

            return query.distinct().all()

        except Exception as e:
            logger.error(f"Failed to get target devices: {str(e)}")
            return []

        finally:
            if self._should_close_session and session:
                session.close()

    async def _deliver_emergency_immediate(
        self,
        target_devices: list[DeviceToken],
        message_data: FCMMessageData,
        android_config: AndroidConfig,
        apns_config: APNSConfig,
        web_config: WebConfig,
        alert: EmergencyAlert,
        priority: NotificationPriority,
    ) -> dict[str, Any]:
        """Deliver emergency notifications immediately."""
        delivery_results = {
            "total_targeted": len(target_devices),
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "delivery_errors": [],
        }

        # Process in smaller batches for faster emergency delivery
        batch_size = self.emergency_batch_size

        for i in range(0, len(target_devices), batch_size):
            batch_devices = target_devices[i:i + batch_size]
            batch_tokens = [device.token for device in batch_devices]

            try:
                # Send batch via FCM
                batch_results = await self.fcm_service.send_to_tokens(
                    tokens=batch_tokens,
                    message_data=message_data,
                    android_config=android_config,
                    apns_config=apns_config,
                    web_config=web_config,
                )

                # Process results and log
                for device, token in zip(batch_devices, batch_tokens, strict=False):
                    success, message_id, error = batch_results.get(token, (False, None, "Unknown error"))

                    # Create notification log entry
                    notification_log = NotificationLog(
                        device_id=device.id,
                        title=message_data.title,
                        body=message_data.body,
                        data_payload=message_data.data,
                        status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
                        priority=priority,
                        fcm_message_id=message_id,
                        error_message=error,
                        sent_at=datetime.now(UTC),
                        max_retries=self.emergency_retries,
                    )

                    session = self.db_session or await get_database_session()
                    session.add(notification_log)

                    if success:
                        delivery_results["successful_deliveries"] += 1
                    else:
                        delivery_results["failed_deliveries"] += 1
                        delivery_results["delivery_errors"].append({
                            "token": token[:10] + "...",
                            "error": error,
                        })

                session.commit()

                # Brief delay between emergency batches to avoid overwhelming FCM
                if i + batch_size < len(target_devices):
                    await asyncio.sleep(0.5)

            except Exception as e:
                error_msg = f"Emergency batch delivery failed: {str(e)}"
                logger.error(error_msg)
                delivery_results["failed_deliveries"] += len(batch_devices)
                delivery_results["delivery_errors"].append({
                    "batch": f"Batch {i // batch_size + 1}",
                    "error": error_msg,
                })

        return delivery_results

    def _get_notification_priority(self, emergency_level: EmergencyLevel) -> NotificationPriority:
        """Map emergency level to notification priority."""
        priority_mapping = {
            EmergencyLevel.WATCH: NotificationPriority.NORMAL,
            EmergencyLevel.ADVISORY: NotificationPriority.HIGH,
            EmergencyLevel.WARNING: NotificationPriority.HIGH,
            EmergencyLevel.EMERGENCY: NotificationPriority.CRITICAL,
        }
        return priority_mapping.get(emergency_level, NotificationPriority.HIGH)

    def _create_emergency_context(self, alert: EmergencyAlert) -> TemplateContext:
        """Create template context from emergency alert."""
        return TemplateContext(
            alert_type=alert.alert_type,
            severity=alert.severity,
            location_name=alert.affected_regions[0] if alert.affected_regions else None,
            coordinates=alert.coordinates,
            custom_data={
                "alert_id": alert.alert_id,
                "recommended_actions": alert.recommended_actions,
                "information_url": alert.information_url,
                "contact_info": alert.contact_info,
                "issued_by": alert.issued_by,
            },
        )

    async def _log_emergency_alert(self, alert: EmergencyAlert, delivery_results: dict[str, Any]):
        """Log emergency alert issuance for audit and analysis."""
        try:
            # In a production system, you would log to a dedicated emergency alerts table
            logger.critical(
                "EMERGENCY ALERT ISSUED",
                extra={
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "affected_regions": alert.affected_regions,
                    "delivery_results": delivery_results,
                    "issued_at": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log emergency alert: {str(e)}")

    async def _send_cancellation_notice(
        self,
        alert_id: str,
        reason: str,
        related_notifications: list[NotificationLog],
    ):
        """Send cancellation notice to users who received the original alert."""
        try:
            # Get unique devices that received the original alert
            device_ids = {
                notif.device_id for notif in related_notifications
                if notif.device_id and notif.status == NotificationStatus.SENT
            }

            if not device_ids:
                return

            session = self.db_session or await get_database_session()
            devices = session.query(DeviceToken).filter(
                DeviceToken.id.in_(device_ids)
            ).all()

            # Send cancellation message
            cancellation_message = FCMMessageData(
                title="🔔 Alert Cancelled",
                body=f"Previous emergency alert has been cancelled. Reason: {reason}",
                data={
                    "alert_id": alert_id,
                    "action": "cancellation",
                    "reason": reason,
                },
                priority="normal",
            )

            tokens = [device.token for device in devices if device.is_active]
            if tokens:
                await self.fcm_service.send_to_tokens(tokens, cancellation_message)
                logger.info(f"Sent cancellation notice for alert {alert_id} to {len(tokens)} devices")

        except Exception as e:
            logger.error(f"Failed to send cancellation notice: {str(e)}")

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_active_emergency_alerts(self) -> list[dict[str, Any]]:
        """Get all currently active emergency alerts."""
        try:
            session = self.db_session or await get_database_session()

            # In a production system, you would have a dedicated emergency_alerts table
            # For now, we'll extract from recent notification logs
            now = datetime.now(UTC)
            recent_cutoff = now - timedelta(hours=24)

            emergency_notifications = session.query(NotificationLog).filter(
                and_(
                    NotificationLog.priority == NotificationPriority.CRITICAL,
                    NotificationLog.created_at >= recent_cutoff,
                    NotificationLog.status != NotificationStatus.CANCELED,
                )
            ).order_by(desc(NotificationLog.created_at)).all()

            # Group by alert_id from data payload
            active_alerts = {}
            for notification in emergency_notifications:
                if notification.data_payload and "alert_id" in notification.data_payload:
                    alert_id = notification.data_payload["alert_id"]
                    if alert_id not in active_alerts:
                        active_alerts[alert_id] = {
                            "alert_id": alert_id,
                            "title": notification.title,
                            "message": notification.body,
                            "issued_at": notification.created_at.isoformat(),
                            "notification_count": 0,
                        }
                    active_alerts[alert_id]["notification_count"] += 1

            return list(active_alerts.values())

        except Exception as e:
            logger.error(f"Failed to get active emergency alerts: {str(e)}")
            return []

        finally:
            if self._should_close_session and session:
                session.close()
