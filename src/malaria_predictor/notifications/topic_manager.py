"""
Topic Subscription Management for Group Messaging.

This module provides comprehensive topic-based messaging capabilities including
topic subscription management, automatic geographic and demographic grouping,
and targeted group notifications for malaria prevention campaigns.
"""

import logging
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..database.session import get_database_session
from .fcm_service import FCMService
from .models import DevicePlatform, DeviceToken, TopicSubscription

logger = logging.getLogger(__name__)


class TopicManager:
    """
    Comprehensive topic subscription management for group messaging.

    Provides intelligent topic management with geographic clustering,
    demographic targeting, and automatic subscription management.
    """

    def __init__(self, fcm_service: FCMService, db_session: Session | None = None) -> None:
        """
        Initialize topic manager.

        Args:
            fcm_service: FCM service instance for topic operations
            db_session: Database session (will create if not provided)
        """
        self.fcm_service = fcm_service
        self.db_session = db_session
        self._should_close_session = db_session is None

        # Predefined topic categories for malaria prevention
        self.topic_categories = {
            "geographic": {
                "description": "Location-based topics for regional alerts",
                "auto_subscribe": True,
                "examples": ["region_africa", "country_kenya", "city_nairobi"],
            },
            "risk_level": {
                "description": "Risk-based grouping for targeted alerts",
                "auto_subscribe": True,
                "examples": ["risk_high", "risk_medium", "risk_low"],
            },
            "user_type": {
                "description": "User role-based topics",
                "auto_subscribe": False,
                "examples": ["healthcare_workers", "travelers", "residents"],
            },
            "alerts": {
                "description": "Alert type subscriptions",
                "auto_subscribe": False,
                "examples": ["outbreak_alerts", "weather_alerts", "medication_reminders"],
            },
            "language": {
                "description": "Language-specific notifications",
                "auto_subscribe": True,
                "examples": ["lang_en", "lang_sw", "lang_fr"],
            },
        }

        logger.info("Topic manager initialized with FCM integration")

    async def __aenter__(self) -> "TopicManager":
        """Async context manager entry."""
        if self._should_close_session:
            self.db_session = await get_database_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_session and self.db_session:
            await self.db_session.close()

    async def subscribe_device_to_topic(
        self,
        device_token: str,
        topic: str,
        auto_create_device: bool = True,
    ) -> tuple[bool, str | None]:
        """
        Subscribe a device to a topic.

        Args:
            device_token: FCM device token
            topic: Topic name to subscribe to
            auto_create_device: Whether to create device record if not exists

        Returns:
            Tuple of (success, error_message)
        """
        try:
            session = self.db_session or await get_database_session()

            # Find or create device record
            device = session.query(DeviceToken).filter(
                DeviceToken.token == device_token
            ).first()

            if not device and auto_create_device:
                # Create device record
                device = DeviceToken(
                    token=device_token,
                    platform=self._detect_platform(device_token),
                    is_active=True,
                )
                session.add(device)
                session.flush()

            if not device:
                return False, "Device not found and auto_create_device is False"

            # Check if already subscribed
            existing_subscription = session.query(TopicSubscription).filter(
                and_(
                    TopicSubscription.device_id == device.id,
                    TopicSubscription.topic == topic,
                    TopicSubscription.is_active,
                )
            ).first()

            if existing_subscription:
                logger.debug(f"Device {device_token[:10]}... already subscribed to topic '{topic}'")
                return True, None

            # Subscribe via FCM
            fcm_result = await self.fcm_service.subscribe_to_topic([device_token], topic)
            if not fcm_result.get(device_token, False):
                return False, "FCM subscription failed"

            # Create subscription record
            subscription = TopicSubscription(
                device_id=device.id,
                topic=topic,
                is_active=True,
            )
            session.add(subscription)
            session.commit()

            logger.info(f"Successfully subscribed device {device_token[:10]}... to topic '{topic}'")
            return True, None

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Failed to subscribe device to topic '{topic}': {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            if self._should_close_session and session:
                session.close()

    async def unsubscribe_device_from_topic(
        self,
        device_token: str,
        topic: str,
    ) -> tuple[bool, str | None]:
        """
        Unsubscribe a device from a topic.

        Args:
            device_token: FCM device token
            topic: Topic name to unsubscribe from

        Returns:
            Tuple of (success, error_message)
        """
        try:
            session = self.db_session or await get_database_session()

            # Find device
            device = session.query(DeviceToken).filter(
                DeviceToken.token == device_token
            ).first()

            if not device:
                return False, "Device not found"

            # Find subscription
            subscription = session.query(TopicSubscription).filter(
                and_(
                    TopicSubscription.device_id == device.id,
                    TopicSubscription.topic == topic,
                    TopicSubscription.is_active,
                )
            ).first()

            if not subscription:
                logger.debug(f"Device {device_token[:10]}... not subscribed to topic '{topic}'")
                return True, None

            # Unsubscribe via FCM
            fcm_result = await self.fcm_service.unsubscribe_from_topic([device_token], topic)
            if not fcm_result.get(device_token, False):
                return False, "FCM unsubscription failed"

            # Deactivate subscription
            subscription.is_active = False
            session.commit()

            logger.info(f"Successfully unsubscribed device {device_token[:10]}... from topic '{topic}'")
            return True, None

        except Exception as e:
            if session:
                session.rollback()
            error_msg = f"Failed to unsubscribe device from topic '{topic}': {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_device_subscriptions(self, device_token: str) -> list[str]:
        """
        Get all active topic subscriptions for a device.

        Args:
            device_token: FCM device token

        Returns:
            List of subscribed topic names
        """
        try:
            session = self.db_session or await get_database_session()

            # Find device and subscriptions
            result = session.query(TopicSubscription.topic).join(DeviceToken).filter(
                and_(
                    DeviceToken.token == device_token,
                    TopicSubscription.is_active,
                )
            ).all()

            return [row.topic for row in result]

        except Exception as e:
            logger.error(f"Failed to get device subscriptions: {str(e)}")
            return []

        finally:
            if self._should_close_session and session:
                session.close()

    async def get_topic_subscribers(self, topic: str) -> list[dict[str, Any]]:
        """
        Get all active subscribers for a topic.

        Args:
            topic: Topic name

        Returns:
            List of subscriber information
        """
        try:
            session = self.db_session or await get_database_session()

            # Get subscribers
            result = session.query(
                DeviceToken.token,
                DeviceToken.platform,
                DeviceToken.user_id,
                TopicSubscription.subscribed_at,
            ).join(TopicSubscription).filter(
                and_(
                    TopicSubscription.topic == topic,
                    TopicSubscription.is_active,
                    DeviceToken.is_active,
                )
            ).all()

            return [
                {
                    "token": row.token,
                    "platform": row.platform,
                    "user_id": row.user_id,
                    "subscribed_at": row.subscribed_at.isoformat(),
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"Failed to get topic subscribers: {str(e)}")
            return []

        finally:
            if self._should_close_session and session:
                session.close()

    async def create_geographic_topic(
        self,
        location_name: str,
        coordinates: dict[str, float] | None = None,
        radius_km: float | None = None,
    ) -> str:
        """
        Create a geographic topic for location-based messaging.

        Args:
            location_name: Human-readable location name
            coordinates: Geographic coordinates (lat, lng)
            radius_km: Radius in kilometers for geographic clustering

        Returns:
            Generated topic name
        """
        # Normalize location name for topic
        normalized_name = location_name.lower().replace(" ", "_").replace("-", "_")
        topic_name = f"geo_{normalized_name}"

        logger.info(f"Created geographic topic: {topic_name} for {location_name}")
        return topic_name

    async def create_risk_level_topic(self, risk_level: str) -> str:
        """
        Create a risk-level topic for targeted alerts.

        Args:
            risk_level: Risk level (low, medium, high, critical)

        Returns:
            Generated topic name
        """
        valid_levels = ["low", "medium", "high", "critical"]
        if risk_level.lower() not in valid_levels:
            raise ValueError(f"Risk level must be one of: {valid_levels}")

        topic_name = f"risk_{risk_level.lower()}"
        logger.info(f"Created risk level topic: {topic_name}")
        return topic_name

    async def auto_subscribe_device(
        self,
        device_token: str,
        user_location: dict[str, Any] | None = None,
        user_preferences: dict[str, Any] | None = None,
        language: str = "en",
    ) -> list[str]:
        """
        Automatically subscribe device to relevant topics based on context.

        Args:
            device_token: FCM device token
            user_location: User location information
            user_preferences: User preferences and demographics
            language: User's preferred language

        Returns:
            List of topics the device was subscribed to
        """
        subscribed_topics = []

        try:
            # Subscribe to language topic
            language_topic = f"lang_{language}"
            success, _ = await self.subscribe_device_to_topic(device_token, language_topic)
            if success:
                subscribed_topics.append(language_topic)

            # Subscribe to geographic topics based on location
            if user_location:
                if "country" in user_location:
                    country_topic = f"geo_{user_location['country'].lower()}"
                    success, _ = await self.subscribe_device_to_topic(device_token, country_topic)
                    if success:
                        subscribed_topics.append(country_topic)

                if "region" in user_location:
                    region_topic = f"geo_{user_location['region'].lower()}"
                    success, _ = await self.subscribe_device_to_topic(device_token, region_topic)
                    if success:
                        subscribed_topics.append(region_topic)

            # Subscribe to user type topics based on preferences
            if user_preferences:
                user_type = user_preferences.get("user_type")
                if user_type:
                    type_topic = f"type_{user_type.lower()}"
                    success, _ = await self.subscribe_device_to_topic(device_token, type_topic)
                    if success:
                        subscribed_topics.append(type_topic)

                # Subscribe to alert preferences
                alert_preferences = user_preferences.get("alerts", [])
                for alert_type in alert_preferences:
                    alert_topic = f"alert_{alert_type.lower()}"
                    success, _ = await self.subscribe_device_to_topic(device_token, alert_topic)
                    if success:
                        subscribed_topics.append(alert_topic)

            # Subscribe to general malaria updates
            general_topic = "malaria_updates"
            success, _ = await self.subscribe_device_to_topic(device_token, general_topic)
            if success:
                subscribed_topics.append(general_topic)

            logger.info(f"Auto-subscribed device {device_token[:10]}... to {len(subscribed_topics)} topics")
            return subscribed_topics

        except Exception as e:
            logger.error(f"Failed to auto-subscribe device: {str(e)}")
            return subscribed_topics

    async def get_topic_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about topic subscriptions.

        Returns:
            Dictionary with topic subscription statistics
        """
        try:
            session = self.db_session or await get_database_session()

            # Get total active subscriptions
            total_subscriptions = session.query(TopicSubscription).filter(
                TopicSubscription.is_active
            ).count()

            # Get subscriptions by topic
            topic_stats = session.query(
                TopicSubscription.topic,
                func.count(TopicSubscription.id).label('subscriber_count')
            ).filter(
                TopicSubscription.is_active
            ).group_by(TopicSubscription.topic).all()

            # Get subscriptions by platform
            platform_stats = session.query(
                DeviceToken.platform,
                func.count(TopicSubscription.id).label('subscription_count')
            ).join(TopicSubscription).filter(
                and_(
                    TopicSubscription.is_active,
                    DeviceToken.is_active,
                )
            ).group_by(DeviceToken.platform).all()

            return {
                "total_subscriptions": total_subscriptions,
                "topics": {row[0]: row[1] for row in topic_stats},
                "platforms": {row[0]: row[1] for row in platform_stats},
                "topic_categories": self.topic_categories,
            }

        except Exception as e:
            logger.error(f"Failed to get topic statistics: {str(e)}")
            return {}

        finally:
            if self._should_close_session and session:
                session.close()

    async def cleanup_inactive_subscriptions(self, days_inactive: int = 30) -> int:
        """
        Clean up subscriptions for inactive devices.

        Args:
            days_inactive: Number of days to consider a device inactive

        Returns:
            Number of subscriptions cleaned up
        """
        try:
            session = self.db_session or await get_database_session()

            # Find subscriptions for inactive devices
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_inactive)

            inactive_subscriptions = session.query(TopicSubscription).join(DeviceToken).filter(
                and_(
                    TopicSubscription.is_active,
                    or_(
                        ~DeviceToken.is_active,
                        DeviceToken.last_seen < cutoff_date,
                    )
                )
            ).all()

            # Deactivate subscriptions
            count = 0
            for subscription in inactive_subscriptions:
                subscription.is_active = False
                count += 1

            session.commit()

            logger.info(f"Cleaned up {count} inactive topic subscriptions")
            return count

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to cleanup inactive subscriptions: {str(e)}")
            return 0

        finally:
            if self._should_close_session and session:
                session.close()

    def _detect_platform(self, device_token: str) -> str:
        """
        Detect device platform from token characteristics.

        Args:
            device_token: FCM device token

        Returns:
            Detected platform (android, ios, web)
        """
        # Basic platform detection based on token length and characteristics
        token_length = len(device_token)

        if token_length >= 140 and token_length <= 180:
            # Typical Android FCM token length
            return DevicePlatform.ANDROID
        elif token_length >= 60 and token_length <= 100:
            # Typical iOS APNS token length
            return DevicePlatform.IOS
        elif ":" in device_token or token_length > 200:
            # Web push tokens often contain colons or are very long
            return DevicePlatform.WEB
        else:
            # Default to Android if unsure
            return DevicePlatform.ANDROID

    async def get_recommended_topics(
        self,
        user_location: dict[str, Any] | None = None,
        user_preferences: dict[str, Any] | None = None,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Get recommended topics for a user based on their profile.

        Args:
            user_location: User location information
            user_preferences: User preferences and demographics
            language: User's preferred language

        Returns:
            List of recommended topics with descriptions
        """
        recommendations = []

        # Language topic
        recommendations.append({
            "topic": f"lang_{language}",
            "category": "language",
            "description": f"Notifications in {language}",
            "priority": "high",
            "auto_subscribe": True,
        })

        # Geographic topics
        if user_location:
            if "country" in user_location:
                recommendations.append({
                    "topic": f"geo_{user_location['country'].lower()}",
                    "category": "geographic",
                    "description": f"Updates for {user_location['country']}",
                    "priority": "high",
                    "auto_subscribe": True,
                })

        # User type topics
        if user_preferences and "user_type" in user_preferences:
            user_type = user_preferences["user_type"]
            recommendations.append({
                "topic": f"type_{user_type.lower()}",
                "category": "user_type",
                "description": f"Content for {user_type}",
                "priority": "medium",
                "auto_subscribe": False,
            })

        # General malaria updates
        recommendations.append({
            "topic": "malaria_updates",
            "category": "general",
            "description": "General malaria prevention updates",
            "priority": "medium",
            "auto_subscribe": True,
        })

        return recommendations
