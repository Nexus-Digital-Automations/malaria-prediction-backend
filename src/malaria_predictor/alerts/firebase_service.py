"""Firebase Cloud Messaging service for push notifications.

Handles Firebase Cloud Messaging (FCM) integration for sending
push notifications to mobile devices and web browsers.
"""

import json
import logging
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, messaging
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database.models import Alert, NotificationDelivery, UserDeviceToken
from ..database.session import get_database

logger = logging.getLogger(__name__)


class PushNotificationPayload(BaseModel):
    """Push notification payload structure."""

    title: str
    body: str
    data: dict[str, str] | None = None
    image_url: str | None = None

    # Platform-specific settings
    android_priority: str = "high"  # normal, high
    android_ttl: int = 3600  # Time to live in seconds
    android_collapse_key: str | None = None

    ios_priority: str = "high"  # normal, high
    ios_sound: str = "default"
    ios_badge: int | None = None
    ios_content_available: bool = False

    # Web-specific settings
    web_icon: str | None = None
    web_badge: str | None = None
    web_actions: list[dict] | None = None


class FirebaseNotificationResult(BaseModel):
    """Result of Firebase notification delivery."""

    success: bool
    message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    token_invalid: bool = False
    retry_after: int | None = None  # Seconds to wait before retry


class FirebaseNotificationService:
    """Firebase Cloud Messaging service for push notifications.

    Provides functionality for:
    - FCM initialization and configuration
    - Single and batch push notification delivery
    - Device token validation and management
    - Delivery tracking and error handling
    - Template-based notification generation
    """

    def __init__(self):
        """Initialize Firebase Cloud Messaging service."""
        self.settings = get_settings()
        self.app = None
        self.initialized = False

        # Statistics tracking
        self.stats = {
            "notifications_sent": 0,
            "notifications_delivered": 0,
            "notifications_failed": 0,
            "tokens_validated": 0,
            "tokens_invalidated": 0,
            "last_reset": datetime.now()
        }

    async def initialize(self) -> bool:
        """Initialize Firebase Admin SDK.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.initialized:
                return True

            # Load Firebase credentials
            firebase_credentials = self._load_firebase_credentials()
            if not firebase_credentials:
                logger.error("Firebase credentials not found")
                return False

            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(firebase_credentials)
            self.app = firebase_admin.initialize_app(cred)
            self.initialized = True

            logger.info("Firebase Cloud Messaging service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Firebase service: {e}")
            return False

    async def send_notification(
        self,
        device_token: str,
        payload: PushNotificationPayload,
        alert_id: int | None = None
    ) -> FirebaseNotificationResult:
        """Send a push notification to a single device.

        Args:
            device_token: FCM device token
            payload: Notification payload
            alert_id: Associated alert ID for tracking

        Returns:
            Notification delivery result
        """
        if not await self.initialize():
            return FirebaseNotificationResult(
                success=False,
                error_code="INITIALIZATION_FAILED",
                error_message="Firebase service not initialized"
            )

        try:
            # Build FCM message
            message = self._build_fcm_message(device_token, payload)

            # Send notification
            response = messaging.send(message)

            self.stats["notifications_sent"] += 1

            # Track delivery if alert_id provided
            if alert_id:
                await self._track_delivery(
                    alert_id=alert_id,
                    device_token=device_token,
                    payload=payload,
                    success=True,
                    message_id=response
                )

            self.stats["notifications_delivered"] += 1

            logger.info(f"Push notification sent successfully: {response}")

            return FirebaseNotificationResult(
                success=True,
                message_id=response
            )

        except messaging.UnregisteredError:
            # Token is invalid
            self.stats["notifications_failed"] += 1
            await self._invalidate_token(device_token)

            if alert_id:
                await self._track_delivery(
                    alert_id=alert_id,
                    device_token=device_token,
                    payload=payload,
                    success=False,
                    error_code="UNREGISTERED",
                    error_message="Device token is invalid"
                )

            return FirebaseNotificationResult(
                success=False,
                error_code="UNREGISTERED",
                error_message="Device token is invalid",
                token_invalid=True
            )

        except messaging.SenderIdMismatchError:
            self.stats["notifications_failed"] += 1

            return FirebaseNotificationResult(
                success=False,
                error_code="SENDER_ID_MISMATCH",
                error_message="Invalid sender ID for token"
            )

        except messaging.QuotaExceededError:
            self.stats["notifications_failed"] += 1

            return FirebaseNotificationResult(
                success=False,
                error_code="QUOTA_EXCEEDED",
                error_message="FCM quota exceeded",
                retry_after=3600  # Retry after 1 hour
            )

        except Exception as e:
            self.stats["notifications_failed"] += 1

            if alert_id:
                await self._track_delivery(
                    alert_id=alert_id,
                    device_token=device_token,
                    payload=payload,
                    success=False,
                    error_code="UNKNOWN_ERROR",
                    error_message=str(e)
                )

            logger.error(f"Failed to send push notification: {e}")

            return FirebaseNotificationResult(
                success=False,
                error_code="UNKNOWN_ERROR",
                error_message=str(e)
            )

    async def send_batch_notifications(
        self,
        tokens_and_payloads: list[tuple[str, PushNotificationPayload]],
        alert_id: int | None = None
    ) -> dict[str, FirebaseNotificationResult]:
        """Send push notifications to multiple devices.

        Args:
            tokens_and_payloads: List of (device_token, payload) tuples
            alert_id: Associated alert ID for tracking

        Returns:
            Dictionary mapping device tokens to delivery results
        """
        if not await self.initialize():
            error_result = FirebaseNotificationResult(
                success=False,
                error_code="INITIALIZATION_FAILED",
                error_message="Firebase service not initialized"
            )
            return {token: error_result for token, _ in tokens_and_payloads}

        results = {}

        # Process in batches of 500 (FCM limit)
        batch_size = 500
        for i in range(0, len(tokens_and_payloads), batch_size):
            batch = tokens_and_payloads[i:i + batch_size]

            try:
                # Build messages for batch
                messages = [
                    self._build_fcm_message(token, payload)
                    for token, payload in batch
                ]

                # Send batch
                response = messaging.send_all(messages)

                # Process results
                for j, (token, payload) in enumerate(batch):
                    individual_response = response.responses[j]

                    if individual_response.success:
                        self.stats["notifications_delivered"] += 1

                        results[token] = FirebaseNotificationResult(
                            success=True,
                            message_id=individual_response.message_id
                        )

                        if alert_id:
                            await self._track_delivery(
                                alert_id=alert_id,
                                device_token=token,
                                payload=payload,
                                success=True,
                                message_id=individual_response.message_id
                            )
                    else:
                        self.stats["notifications_failed"] += 1
                        error = individual_response.exception

                        # Handle different error types
                        if isinstance(error, messaging.UnregisteredError):
                            await self._invalidate_token(token)
                            results[token] = FirebaseNotificationResult(
                                success=False,
                                error_code="UNREGISTERED",
                                error_message="Device token is invalid",
                                token_invalid=True
                            )
                        else:
                            results[token] = FirebaseNotificationResult(
                                success=False,
                                error_code=type(error).__name__,
                                error_message=str(error)
                            )

                        if alert_id:
                            await self._track_delivery(
                                alert_id=alert_id,
                                device_token=token,
                                payload=payload,
                                success=False,
                                error_code=type(error).__name__,
                                error_message=str(error)
                            )

                self.stats["notifications_sent"] += len(batch)

            except Exception as e:
                logger.error(f"Failed to send batch notifications: {e}")

                # Mark all tokens in batch as failed
                for token, payload in batch:
                    self.stats["notifications_failed"] += 1
                    results[token] = FirebaseNotificationResult(
                        success=False,
                        error_code="BATCH_FAILED",
                        error_message=str(e)
                    )

        return results

    async def send_alert_notification(self, alert: Alert) -> dict[str, FirebaseNotificationResult]:
        """Send push notifications for an alert to all relevant devices.

        Args:
            alert: Alert instance to send notifications for

        Returns:
            Dictionary mapping device tokens to delivery results
        """
        # Get alert configuration
        db = next(get_database())

        try:
            # Get target device tokens based on alert configuration
            device_tokens = await self._get_target_device_tokens(db, alert)

            if not device_tokens:
                logger.info(f"No device tokens found for alert {alert.id}")
                return {}

            # Build notification payload from alert
            payload = self._build_alert_payload(alert)

            # Prepare batch data
            tokens_and_payloads = [(token, payload) for token in device_tokens]

            # Send batch notifications
            results = await self.send_batch_notifications(tokens_and_payloads, alert.id)

            logger.info(
                f"Sent push notifications for alert {alert.id} to "
                f"{len(device_tokens)} devices, "
                f"{sum(1 for r in results.values() if r.success)} successful"
            )

            return results

        finally:
            db.close()

    async def validate_token(self, device_token: str) -> bool:
        """Validate a device token with FCM.

        Args:
            device_token: Device token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Send a test message to validate token
            test_message = messaging.Message(
                token=device_token,
                data={"test": "validation"}
            )

            messaging.send(test_message, dry_run=True)
            self.stats["tokens_validated"] += 1
            return True

        except messaging.UnregisteredError:
            await self._invalidate_token(device_token)
            return False

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    async def register_device_token(
        self,
        user_id: str,
        device_token: str,
        device_type: str,
        device_info: dict | None = None
    ) -> bool:
        """Register a new device token for push notifications.

        Args:
            user_id: User ID to associate with token
            device_token: FCM device token
            device_type: Device type (ios, android, web)
            device_info: Additional device information

        Returns:
            True if registration successful, False otherwise
        """
        db = next(get_database())

        try:
            # Validate token first
            if not await self.validate_token(device_token):
                return False

            # Check if token already exists
            existing_token = db.query(UserDeviceToken).filter(
                UserDeviceToken.device_token == device_token
            ).first()

            if existing_token:
                # Update existing token
                existing_token.user_id = user_id
                existing_token.device_type = device_type
                existing_token.is_active = True
                existing_token.is_valid = True
                existing_token.refreshed_at = datetime.now()

                if device_info:
                    existing_token.device_name = device_info.get("device_name")
                    existing_token.platform_version = device_info.get("platform_version")
                    existing_token.app_version = device_info.get("app_version")
            else:
                # Create new token
                new_token = UserDeviceToken(
                    user_id=user_id,
                    device_token=device_token,
                    device_type=device_type,
                    device_id=device_info.get("device_id") if device_info else None,
                    device_name=device_info.get("device_name") if device_info else None,
                    platform_version=device_info.get("platform_version") if device_info else None,
                    app_version=device_info.get("app_version") if device_info else None
                )
                db.add(new_token)

            db.commit()
            logger.info(f"Registered device token for user {user_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to register device token: {e}")
            return False

        finally:
            db.close()

    def get_stats(self) -> dict:
        """Get Firebase service statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            "initialized": self.initialized,
            "success_rate": (
                self.stats["notifications_delivered"] / max(self.stats["notifications_sent"], 1)
            ) * 100
        }

    def _load_firebase_credentials(self) -> dict | None:
        """Load Firebase service account credentials.

        Returns:
            Firebase credentials dictionary or None if not found
        """
        try:
            # Try to load from environment variable (JSON string)
            if hasattr(self.settings, "FIREBASE_CREDENTIALS_JSON"):
                return json.loads(self.settings.FIREBASE_CREDENTIALS_JSON)

            # Try to load from file path
            if hasattr(self.settings, "FIREBASE_CREDENTIALS_PATH"):
                with open(self.settings.FIREBASE_CREDENTIALS_PATH) as f:
                    return json.load(f)

            return None

        except Exception as e:
            logger.error(f"Failed to load Firebase credentials: {e}")
            return None

    def _build_fcm_message(
        self,
        device_token: str,
        payload: PushNotificationPayload
    ) -> messaging.Message:
        """Build FCM message from payload.

        Args:
            device_token: Target device token
            payload: Notification payload

        Returns:
            FCM Message instance
        """
        # Build notification
        notification = messaging.Notification(
            title=payload.title,
            body=payload.body,
            image=payload.image_url
        )

        # Build platform-specific configs
        android_config = messaging.AndroidConfig(
            priority=payload.android_priority,
            ttl=payload.android_ttl,
            collapse_key=payload.android_collapse_key,
            notification=messaging.AndroidNotification(
                sound="default",
                channel_id="malaria_alerts"
            )
        )

        apns_config = messaging.APNSConfig(
            headers={
                "apns-priority": "10" if payload.ios_priority == "high" else "5"
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound=payload.ios_sound,
                    badge=payload.ios_badge,
                    content_available=payload.ios_content_available
                )
            )
        )

        web_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon=payload.web_icon,
                badge=payload.web_badge,
                actions=payload.web_actions
            )
        )

        return messaging.Message(
            token=device_token,
            notification=notification,
            data=payload.data or {},
            android=android_config,
            apns=apns_config,
            webpush=web_config
        )

    def _build_alert_payload(self, alert: Alert) -> PushNotificationPayload:
        """Build push notification payload from alert.

        Args:
            alert: Alert instance

        Returns:
            Push notification payload
        """
        # Determine priority based on alert level
        priority = "high" if alert.alert_level in ["high", "critical", "emergency"] else "normal"

        # Build location string
        location_str = ""
        if alert.location_name:
            location_str = alert.location_name
        elif alert.admin_region:
            location_str = alert.admin_region
        elif alert.country_code:
            location_str = alert.country_code

        # Build data payload
        data = {
            "alert_id": str(alert.id),
            "alert_type": alert.alert_type,
            "alert_level": alert.alert_level,
            "location": location_str,
            "timestamp": alert.created_at.isoformat()
        }

        if alert.risk_score:
            data["risk_score"] = str(alert.risk_score)

        if alert.latitude and alert.longitude:
            data["latitude"] = str(alert.latitude)
            data["longitude"] = str(alert.longitude)

        return PushNotificationPayload(
            title=alert.alert_title,
            body=alert.alert_message,
            data=data,
            android_priority=priority,
            ios_priority=priority,
            ios_sound="alert.wav" if priority == "high" else "default"
        )

    async def _get_target_device_tokens(self, db: Session, alert: Alert) -> list[str]:
        """Get device tokens that should receive the alert.

        Args:
            db: Database session
            alert: Alert instance

        Returns:
            List of device tokens
        """
        # Get alert configuration
        from ..database.models import AlertConfiguration

        config = db.query(AlertConfiguration).filter(
            AlertConfiguration.id == alert.configuration_id
        ).first()

        if not config or not config.enable_push_notifications:
            return []

        # Get user device tokens
        query = db.query(UserDeviceToken).filter(
            UserDeviceToken.user_id == config.user_id,
            UserDeviceToken.is_active,
            UserDeviceToken.is_valid
        )

        device_tokens = query.all()
        return [token.device_token for token in device_tokens]

    async def _track_delivery(
        self,
        alert_id: int,
        device_token: str,
        payload: PushNotificationPayload,
        success: bool,
        message_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None
    ):
        """Track notification delivery in database.

        Args:
            alert_id: Alert ID
            device_token: Target device token
            payload: Notification payload
            success: Whether delivery was successful
            message_id: FCM message ID if successful
            error_code: Error code if failed
            error_message: Error message if failed
        """
        db = next(get_database())

        try:
            delivery = NotificationDelivery(
                alert_id=alert_id,
                channel="push",
                recipient=device_token,
                recipient_type="user",
                subject=payload.title,
                message_body=payload.body,
                message_format="json",
                status="delivered" if success else "failed",
                delivery_provider="firebase",
                provider_message_id=message_id,
                provider_response={
                    "success": success,
                    "error_code": error_code,
                    "error_message": error_message
                } if not success else {"success": True, "message_id": message_id},
                scheduled_at=datetime.now(),
                sent_at=datetime.now(),
                delivered_at=datetime.now() if success else None,
                failed_at=datetime.now() if not success else None,
                error_code=error_code,
                error_message=error_message
            )

            db.add(delivery)
            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to track notification delivery: {e}")

        finally:
            db.close()

    async def _invalidate_token(self, device_token: str):
        """Mark a device token as invalid.

        Args:
            device_token: Device token to invalidate
        """
        db = next(get_database())

        try:
            token = db.query(UserDeviceToken).filter(
                UserDeviceToken.device_token == device_token
            ).first()

            if token:
                token.is_valid = False
                token.is_active = False
                token.deactivated_at = datetime.now()
                token.validation_failures += 1
                db.commit()

                self.stats["tokens_invalidated"] += 1
                logger.info(f"Invalidated device token: {device_token[:20]}...")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to invalidate device token: {e}")

        finally:
            db.close()


# Global Firebase service instance
firebase_service = FirebaseNotificationService()
