"""Multi-channel notification delivery service.

Handles delivery of notifications across multiple channels including
email, SMS, webhooks, and push notifications with retry logic and tracking.
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiohttp
from pydantic import BaseModel

from ..config import settings
from ..database.models import (
    Alert,
    AlertConfiguration,
    NotificationDelivery,
)
from ..database.session import get_session as get_database
from .firebase_service import PushNotificationPayload, firebase_service

logger = logging.getLogger(__name__)


class NotificationRequest(BaseModel):
    """Notification delivery request."""

    alert_id: int
    channel: str  # email, sms, webhook, push
    recipient: str
    recipient_type: str = "user"
    subject: str | None = None
    message: str
    message_format: str = "text"  # text, html, json
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_at: datetime | None = None
    metadata: dict | None = None


class DeliveryResult(BaseModel):
    """Notification delivery result."""

    success: bool
    delivery_id: int | None = None
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_after: int | None = None
    processing_time_ms: int = 0


class EmailConfig(BaseModel):
    """Email service configuration."""

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    from_email: str
    from_name: str = "Malaria Alert System"


class SMSConfig(BaseModel):
    """SMS service configuration."""

    provider: str  # twilio, aws_sns, etc.
    api_key: str
    api_secret: str
    from_number: str
    api_endpoint: str | None = None


class WebhookConfig(BaseModel):
    """Webhook service configuration."""

    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 60
    verify_ssl: bool = True


class NotificationService:
    """Multi-channel notification delivery service.

    Provides functionality for:
    - Email notification delivery via SMTP
    - SMS notification delivery via third-party APIs
    - Webhook notification delivery with retry logic
    - Delivery tracking and performance monitoring
    - Template-based message generation
    - Batch delivery optimization
    """

    def __init__(self) -> None:
        """Initialize the notification service."""
        self.settings = settings

        # Load configurations
        self.email_config = self._load_email_config()
        self.sms_config = self._load_sms_config()
        self.webhook_config = self._load_webhook_config()

        # Statistics tracking
        self.stats = {
            "email_sent": 0,
            "email_delivered": 0,
            "email_failed": 0,
            "sms_sent": 0,
            "sms_delivered": 0,
            "sms_failed": 0,
            "webhook_sent": 0,
            "webhook_delivered": 0,
            "webhook_failed": 0,
            "total_delivery_time_ms": 0,
            "avg_delivery_time_ms": 0.0
        }

        # Retry queue
        self.retry_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.retry_task: asyncio.Task[None] | None = None

    async def start_retry_processor(self) -> None:
        """Start the retry processor task."""
        if not self.retry_task:
            self.retry_task = asyncio.create_task(self._process_retries())

    async def stop_retry_processor(self) -> None:
        """Stop the retry processor task."""
        if self.retry_task:
            self.retry_task.cancel()
            self.retry_task = None

    async def deliver_alert_notifications(self, alert: Alert) -> dict[str, list[DeliveryResult]]:
        """Deliver notifications for an alert across all configured channels.

        Args:
            alert: Alert to send notifications for

        Returns:
            Dictionary mapping channels to delivery results
        """
        db = next(get_database())  # type: ignore[call-overload]

        try:
            # Get alert configuration
            config = db.query(AlertConfiguration).filter(
                AlertConfiguration.id == alert.configuration_id
            ).first()

            if not config:
                logger.error(f"No configuration found for alert {alert.id}")
                return {}

            results = {}

            # Send push notifications
            if config.enable_push_notifications:
                results["push"] = await self._deliver_push_notifications(alert, config)

            # Send email notifications
            if config.enable_email_notifications and config.email_addresses:
                results["email"] = await self._deliver_email_notifications(alert, config)

            # Send SMS notifications
            if config.enable_sms_notifications and config.phone_numbers:
                results["sms"] = await self._deliver_sms_notifications(alert, config)

            # Send webhook notifications
            if config.enable_webhook_notifications and config.webhook_urls:
                results["webhook"] = await self._deliver_webhook_notifications(alert, config)

            # Check for emergency escalation
            if (config.enable_emergency_escalation and
                alert.risk_score and alert.risk_score >= config.emergency_escalation_threshold):

                await self._escalate_emergency_alert(alert, config)

            logger.info(f"Delivered notifications for alert {alert.id} across {len(results)} channels")
            return results

        except Exception as e:
            logger.error(f"Failed to deliver alert notifications: {e}")
            return {}

        finally:
            db.close()

    async def send_notification(self, request: NotificationRequest) -> DeliveryResult:
        """Send a single notification.

        Args:
            request: Notification request

        Returns:
            Delivery result
        """
        start_time = datetime.now()

        try:
            # Route to appropriate delivery method
            if request.channel == "email":
                result = await self._send_email(request)
            elif request.channel == "sms":
                result = await self._send_sms(request)
            elif request.channel == "webhook":
                result = await self._send_webhook(request)
            elif request.channel == "push":
                result = await self._send_push(request)
            else:
                result = DeliveryResult(
                    success=False,
                    error_code="UNSUPPORTED_CHANNEL",
                    error_message=f"Unsupported notification channel: {request.channel}"
                )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)

            # Track delivery in database
            await self._track_delivery(request, result)

            # Update statistics
            self._update_stats(request.channel, result)

            # Schedule retry if needed
            if not result.success and result.retry_after:
                await self._schedule_retry(request, result.retry_after)

            return result

        except Exception as e:
            logger.error(f"Notification delivery failed: {e}")

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return DeliveryResult(
                success=False,
                error_code="DELIVERY_ERROR",
                error_message=str(e),
                processing_time_ms=int(processing_time)
            )

    async def _deliver_push_notifications(
        self,
        alert: Alert,
        config: AlertConfiguration
    ) -> list[DeliveryResult]:
        """Deliver push notifications for an alert.

        Args:
            alert: Alert to send
            config: Alert configuration

        Returns:
            List of delivery results
        """
        try:
            results = await firebase_service.send_alert_notification(alert)

            delivery_results = []
            for _token, firebase_result in results.items():
                delivery_results.append(DeliveryResult(
                    success=firebase_result.success,
                    provider_message_id=firebase_result.message_id,
                    error_code=firebase_result.error_code,
                    error_message=firebase_result.error_message,
                    retry_after=firebase_result.retry_after
                ))

            return delivery_results

        except Exception as e:
            logger.error(f"Push notification delivery failed: {e}")
            return [DeliveryResult(
                success=False,
                error_code="PUSH_ERROR",
                error_message=str(e)
            )]

    async def _deliver_email_notifications(
        self,
        alert: Alert,
        config: AlertConfiguration
    ) -> list[DeliveryResult]:
        """Deliver email notifications for an alert.

        Args:
            alert: Alert to send
            config: Alert configuration

        Returns:
            List of delivery results
        """
        if not self.email_config or not config.email_addresses:
            return []

        # Generate email content
        subject, html_body, text_body = await self._generate_email_content(alert)

        results = []

        for email in config.email_addresses:  # type: ignore[attr-defined]
            request = NotificationRequest(
                alert_id=int(alert.id),
                channel="email",
                recipient=email,
                subject=subject,
                message=html_body,
                message_format="html"
            )

            result = await self.send_notification(request)
            results.append(result)

        return results

    async def _deliver_sms_notifications(
        self,
        alert: Alert,
        config: AlertConfiguration
    ) -> list[DeliveryResult]:
        """Deliver SMS notifications for an alert.

        Args:
            alert: Alert to send
            config: Alert configuration

        Returns:
            List of delivery results
        """
        if not self.sms_config or not config.phone_numbers:
            return []

        # Generate SMS content
        message = await self._generate_sms_content(alert)

        results = []

        for phone in config.phone_numbers:  # type: ignore[attr-defined]
            request = NotificationRequest(
                alert_id=int(alert.id),
                channel="sms",
                recipient=phone,
                message=message
            )

            result = await self.send_notification(request)
            results.append(result)

        return results

    async def _deliver_webhook_notifications(
        self,
        alert: Alert,
        config: AlertConfiguration
    ) -> list[DeliveryResult]:
        """Deliver webhook notifications for an alert.

        Args:
            alert: Alert to send
            config: Alert configuration

        Returns:
            List of delivery results
        """
        if not config.webhook_urls:
            return []

        # Generate webhook payload
        payload = await self._generate_webhook_payload(alert)

        results = []

        for webhook_url in config.webhook_urls:  # type: ignore[attr-defined]
            request = NotificationRequest(
                alert_id=int(alert.id),
                channel="webhook",
                recipient=webhook_url,
                message=json.dumps(payload),
                message_format="json"
            )

            result = await self.send_notification(request)
            results.append(result)

        return results

    async def _send_email(self, request: NotificationRequest) -> DeliveryResult:
        """Send email notification.

        Args:
            request: Email notification request

        Returns:
            Delivery result
        """
        if not self.email_config:
            return DeliveryResult(
                success=False,
                error_code="EMAIL_NOT_CONFIGURED",
                error_message="Email service not configured"
            )

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = request.subject or "Malaria Alert"
            msg['From'] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
            msg['To'] = request.recipient

            # Add message body
            if request.message_format == "html":
                html_part = MIMEText(request.message, 'html')
                msg.attach(html_part)
            else:
                text_part = MIMEText(request.message, 'plain')
                msg.attach(text_part)

            # Send email
            with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port) as server:
                if self.email_config.smtp_use_tls:
                    server.starttls()

                server.login(self.email_config.smtp_username, self.email_config.smtp_password)
                server.send_message(msg)

            return DeliveryResult(
                success=True,
                provider_message_id=f"smtp_{datetime.now().timestamp()}"
            )

        except Exception as e:
            logger.error(f"Email sending failed: {e}")

            return DeliveryResult(
                success=False,
                error_code="SMTP_ERROR",
                error_message=str(e)
            )

    async def _send_sms(self, request: NotificationRequest) -> DeliveryResult:
        """Send SMS notification.

        Args:
            request: SMS notification request

        Returns:
            Delivery result
        """
        if not self.sms_config:
            return DeliveryResult(
                success=False,
                error_code="SMS_NOT_CONFIGURED",
                error_message="SMS service not configured"
            )

        try:
            # Route to appropriate SMS provider
            if self.sms_config.provider == "twilio":
                return await self._send_twilio_sms(request)
            elif self.sms_config.provider == "aws_sns":
                return await self._send_aws_sns_sms(request)
            else:
                return DeliveryResult(
                    success=False,
                    error_code="UNSUPPORTED_SMS_PROVIDER",
                    error_message=f"Unsupported SMS provider: {self.sms_config.provider}"
                )

        except Exception as e:
            logger.error(f"SMS sending failed: {e}")

            return DeliveryResult(
                success=False,
                error_code="SMS_ERROR",
                error_message=str(e)
            )

    async def _send_webhook(self, request: NotificationRequest) -> DeliveryResult:
        """Send webhook notification.

        Args:
            request: Webhook notification request

        Returns:
            Delivery result
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'MalariaAlertSystem/1.0'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    request.recipient,
                    data=request.message,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.webhook_config.timeout_seconds),
                    ssl=self.webhook_config.verify_ssl
                ) as response:

                    if response.status == 200:
                        return DeliveryResult(
                            success=True,
                            provider_message_id=response.headers.get('X-Message-ID')
                        )
                    else:
                        return DeliveryResult(
                            success=False,
                            error_code=f"HTTP_{response.status}",
                            error_message=f"Webhook returned status {response.status}",
                            retry_after=300 if response.status >= 500 else None
                        )

        except TimeoutError:
            return DeliveryResult(
                success=False,
                error_code="WEBHOOK_TIMEOUT",
                error_message="Webhook request timed out",
                retry_after=600
            )

        except Exception as e:
            logger.error(f"Webhook sending failed: {e}")

            return DeliveryResult(
                success=False,
                error_code="WEBHOOK_ERROR",
                error_message=str(e),
                retry_after=300
            )

    async def _send_push(self, request: NotificationRequest) -> DeliveryResult:
        """Send push notification.

        Args:
            request: Push notification request

        Returns:
            Delivery result
        """
        try:
            payload = PushNotificationPayload(
                title=request.subject or "Malaria Alert",
                body=request.message
            )

            result = await firebase_service.send_notification(
                request.recipient,
                payload,
                request.alert_id
            )

            return DeliveryResult(
                success=result.success,
                provider_message_id=result.message_id,
                error_code=result.error_code,
                error_message=result.error_message,
                retry_after=result.retry_after
            )

        except Exception as e:
            logger.error(f"Push notification sending failed: {e}")

            return DeliveryResult(
                success=False,
                error_code="PUSH_ERROR",
                error_message=str(e)
            )

    async def _send_twilio_sms(self, request: NotificationRequest) -> DeliveryResult:
        """Send SMS via Twilio.

        Args:
            request: SMS notification request

        Returns:
            Delivery result
        """
        # This would integrate with Twilio SDK
        # For now, return a mock implementation
        return DeliveryResult(
            success=False,
            error_code="NOT_IMPLEMENTED",
            error_message="Twilio SMS integration not yet implemented"
        )

    async def _send_aws_sns_sms(self, request: NotificationRequest) -> DeliveryResult:
        """Send SMS via AWS SNS.

        Args:
            request: SMS notification request

        Returns:
            Delivery result
        """
        # This would integrate with AWS SNS
        # For now, return a mock implementation
        return DeliveryResult(
            success=False,
            error_code="NOT_IMPLEMENTED",
            error_message="AWS SNS SMS integration not yet implemented"
        )

    async def _generate_email_content(self, alert: Alert) -> tuple[str, str, str]:
        """Generate email content for alert.

        Args:
            alert: Alert to generate content for

        Returns:
            Tuple of (subject, html_body, text_body)
        """
        subject = str(alert.alert_title)

        # Generate HTML email
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2 style="color: {'red' if alert.alert_level in ['high', 'critical'] else 'orange'};">
                {alert.alert_title}
            </h2>
            <p><strong>Alert Level:</strong> {alert.alert_level.title()}</p>
            <p><strong>Location:</strong> {alert.location_name or 'Unknown'}</p>
            <p><strong>Risk Score:</strong> {f'{alert.risk_score:.1%}' if alert.risk_score else 'Unknown'}</p>
            <p><strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}</p>

            <h3>Alert Details</h3>
            <p>{alert.alert_message}</p>

            <hr>
            <p><small>
                This alert was generated by the Malaria Prediction System.
                For more information, visit your dashboard.
            </small></p>
        </body>
        </html>
        """

        # Generate text email
        text_body = f"""
        {alert.alert_title}

        Alert Level: {alert.alert_level.title()}
        Location: {alert.location_name or 'Unknown'}
        Risk Score: {f'{alert.risk_score:.1%}' if alert.risk_score else 'Unknown'}
        Time: {alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}

        Alert Details:
        {alert.alert_message}

        ---
        This alert was generated by the Malaria Prediction System.
        """

        return subject, html_body, text_body

    async def _generate_sms_content(self, alert: Alert) -> str:
        """Generate SMS content for alert.

        Args:
            alert: Alert to generate content for

        Returns:
            SMS message text
        """
        location = alert.location_name or alert.admin_region or "your area"
        risk_info = f" ({alert.risk_score:.0%})" if alert.risk_score else ""

        message = (
            f"MALARIA ALERT: {alert.alert_level.upper()} risk detected in {location}{risk_info}. "
            f"Take preventive measures. Time: {alert.created_at.strftime('%m/%d %H:%M')}"
        )

        # SMS length limit
        if len(message) > 160:
            message = message[:157] + "..."

        return message

    async def _generate_webhook_payload(self, alert: Alert) -> dict:
        """Generate webhook payload for alert.

        Args:
            alert: Alert to generate payload for

        Returns:
            Webhook payload dictionary
        """
        return {
            "event": "malaria_alert",
            "alert_id": alert.id,
            "alert_level": alert.alert_level,
            "alert_type": alert.alert_type,
            "title": alert.alert_title,
            "message": alert.alert_message,
            "location": {
                "name": alert.location_name,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "country_code": alert.country_code,
                "admin_region": alert.admin_region
            },
            "risk_data": {
                "risk_score": alert.risk_score,
                "confidence_score": alert.confidence_score,
                "prediction_date": alert.prediction_date.isoformat() if alert.prediction_date else None
            },
            "metadata": {
                "priority": alert.priority,
                "is_emergency": alert.is_emergency,
                "created_at": alert.created_at.isoformat(),
                "system": "malaria_prediction_system"
            }
        }

    async def _escalate_emergency_alert(
        self,
        alert: Alert,
        config: AlertConfiguration
    ) -> None:
        """Escalate alert to emergency contacts.

        Args:
            alert: Emergency alert
            config: Alert configuration
        """
        try:
            alert.escalated_at = datetime.now()  # type: ignore[assignment]
            alert.escalation_level = 1  # type: ignore[assignment]

            # Send to emergency email contacts
            if config.emergency_contact_emails:
                for email in config.emergency_contact_emails:  # type: ignore[attr-defined]
                    request = NotificationRequest(
                        alert_id=int(alert.id),
                        channel="email",
                        recipient=email,
                        recipient_type="emergency_contact",
                        subject=f"EMERGENCY: {alert.alert_title}",
                        message=f"EMERGENCY ESCALATION\n\n{alert.alert_message}",
                        priority="urgent"
                    )
                    await self.send_notification(request)

            # Send to emergency phone contacts
            if config.emergency_contact_phones:
                for phone in config.emergency_contact_phones:  # type: ignore[attr-defined]
                    request = NotificationRequest(
                        alert_id=int(alert.id),
                        channel="sms",
                        recipient=phone,
                        recipient_type="emergency_contact",
                        message=f"EMERGENCY: {await self._generate_sms_content(alert)}",
                        priority="urgent"
                    )
                    await self.send_notification(request)

            logger.info(f"Escalated emergency alert {alert.id}")

        except Exception as e:
            logger.error(f"Emergency escalation failed for alert {alert.id}: {e}")

    async def _track_delivery(
        self,
        request: NotificationRequest,
        result: DeliveryResult
    ) -> None:
        """Track notification delivery in database.

        Args:
            request: Original notification request
            result: Delivery result
        """
        db = next(get_database())  # type: ignore[call-overload]

        try:
            delivery = NotificationDelivery(
                alert_id=request.alert_id,
                channel=request.channel,
                recipient=request.recipient,
                recipient_type=request.recipient_type,
                subject=request.subject,
                message_body=request.message,
                message_format=request.message_format,
                status="delivered" if result.success else "failed",
                provider_message_id=result.provider_message_id,
                scheduled_at=request.scheduled_at or datetime.now(),
                sent_at=datetime.now(),
                delivered_at=datetime.now() if result.success else None,
                failed_at=datetime.now() if not result.success else None,
                error_code=result.error_code,
                error_message=result.error_message,
                processing_time_ms=result.processing_time_ms
            )

            db.add(delivery)
            db.commit()

            result.delivery_id = delivery.id  # type: ignore[assignment]

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to track delivery: {e}")

        finally:
            db.close()

    def _update_stats(self, channel: str, result: DeliveryResult) -> None:
        """Update delivery statistics.

        Args:
            channel: Notification channel
            result: Delivery result
        """
        sent_key = f"{channel}_sent"
        delivered_key = f"{channel}_delivered"
        failed_key = f"{channel}_failed"

        self.stats[sent_key] = self.stats.get(sent_key, 0) + 1

        if result.success:
            self.stats[delivered_key] = self.stats.get(delivered_key, 0) + 1
        else:
            self.stats[failed_key] = self.stats.get(failed_key, 0) + 1

        # Update average delivery time
        total_time = self.stats["total_delivery_time_ms"] + result.processing_time_ms
        total_deliveries = sum(
            self.stats.get(f"{ch}_sent", 0)
            for ch in ["email", "sms", "webhook", "push"]
        )

        self.stats["total_delivery_time_ms"] = total_time
        self.stats["avg_delivery_time_ms"] = total_time / max(total_deliveries, 1)

    async def _schedule_retry(self, request: NotificationRequest, retry_after: int) -> None:
        """Schedule notification for retry.

        Args:
            request: Failed notification request
            retry_after: Seconds to wait before retry
        """
        retry_request = request.copy()
        retry_request.scheduled_at = datetime.now() + timedelta(seconds=retry_after)

        await self.retry_queue.put(retry_request)

    async def _process_retries(self) -> None:
        """Background task to process retry queue."""
        while True:
            try:
                # Get retry request
                request = await self.retry_queue.get()

                # Wait until scheduled time
                if request.scheduled_at and request.scheduled_at > datetime.now():
                    wait_seconds = (request.scheduled_at - datetime.now()).total_seconds()
                    await asyncio.sleep(wait_seconds)

                # Retry delivery
                await self.send_notification(request)

            except asyncio.CancelledError:
                logger.info("Notification retry processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in retry processor: {e}")

    def _load_email_config(self) -> EmailConfig | None:
        """Load email configuration from settings.

        Returns:
            Email configuration or None if not configured
        """
        try:
            if not all(hasattr(self.settings, attr) for attr in [
                "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "FROM_EMAIL"
            ]):
                return None

            return EmailConfig(
                smtp_host=self.settings.SMTP_HOST,  # type: ignore[attr-defined]
                smtp_port=getattr(self.settings, "SMTP_PORT", 587),
                smtp_username=self.settings.SMTP_USERNAME,  # type: ignore[attr-defined]
                smtp_password=self.settings.SMTP_PASSWORD,  # type: ignore[attr-defined]
                smtp_use_tls=getattr(self.settings, "SMTP_USE_TLS", True),
                from_email=self.settings.FROM_EMAIL,  # type: ignore[attr-defined]
                from_name=getattr(self.settings, "FROM_NAME", "Malaria Alert System")
            )

        except Exception as e:
            logger.error(f"Failed to load email configuration: {e}")
            return None

    def _load_sms_config(self) -> SMSConfig | None:
        """Load SMS configuration from settings.

        Returns:
            SMS configuration or None if not configured
        """
        try:
            if not all(hasattr(self.settings, attr) for attr in [
                "SMS_PROVIDER", "SMS_API_KEY", "SMS_API_SECRET", "SMS_FROM_NUMBER"
            ]):
                return None

            return SMSConfig(
                provider=self.settings.SMS_PROVIDER,  # type: ignore[attr-defined]
                api_key=self.settings.SMS_API_KEY,  # type: ignore[attr-defined]
                api_secret=self.settings.SMS_API_SECRET,  # type: ignore[attr-defined]
                from_number=self.settings.SMS_FROM_NUMBER,  # type: ignore[attr-defined]
                api_endpoint=getattr(self.settings, "SMS_API_ENDPOINT", None)
            )

        except Exception as e:
            logger.error(f"Failed to load SMS configuration: {e}")
            return None

    def _load_webhook_config(self) -> WebhookConfig:
        """Load webhook configuration from settings.

        Returns:
            Webhook configuration with defaults
        """
        return WebhookConfig(
            timeout_seconds=getattr(self.settings, "WEBHOOK_TIMEOUT_SECONDS", 30),
            max_retries=getattr(self.settings, "WEBHOOK_MAX_RETRIES", 3),
            retry_delay_seconds=getattr(self.settings, "WEBHOOK_RETRY_DELAY_SECONDS", 60),
            verify_ssl=getattr(self.settings, "WEBHOOK_VERIFY_SSL", True)
        )

    def get_stats(self) -> dict:
        """Get notification service statistics.

        Returns:
            Dictionary with current statistics
        """
        return self.stats.copy()


# Global notification service instance
notification_service = NotificationService()
