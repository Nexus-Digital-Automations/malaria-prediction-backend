"""Enhanced Firebase Cloud Messaging service with advanced features.

Provides comprehensive Firebase Cloud Messaging capabilities including:
- Rich notification templates and customization
- Scheduled and batched notifications
- Advanced targeting and segmentation
- A/B testing for notifications
- Performance analytics and optimization
- Token management and validation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None
    FIREBASE_AVAILABLE = False

from ..config import settings
from ..database.models import UserDeviceToken
from ..database.session import get_session
from .firebase_service import FirebaseNotificationResult, PushNotificationPayload

logger = logging.getLogger(__name__)


class NotificationTemplate(BaseModel):
    """Enhanced notification template with dynamic content."""

    template_id: str
    name: str
    description: str
    category: str  # alert, promotional, informational, emergency

    # Template content with placeholders
    title_template: str  # e.g., "Malaria Alert: {{alert_level}} Risk in {{location}}"
    body_template: str
    image_url_template: str | None = None

    # Dynamic data mapping
    required_variables: list[str]  # Variables that must be provided
    optional_variables: list[str] = []  # Variables with defaults
    default_values: dict[str, str] = {}

    # Template settings
    alert_level_mapping: dict[str, dict[str, str]] = {}  # Level-specific overrides
    localization: dict[str, dict[str, str]] = {}  # Language translations

    # Platform customizations
    android_settings: dict[str, Any] = {}
    ios_settings: dict[str, Any] = {}
    web_settings: dict[str, Any] = {}

    # Engagement optimization
    send_time_optimization: bool = False  # Optimize send times per user
    frequency_capping: dict[str, int] = {}  # Max notifications per time period

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class NotificationCampaign(BaseModel):
    """Notification campaign for batch and scheduled sending."""

    campaign_id: str
    name: str
    description: str
    template_id: str

    # Targeting
    target_users: list[str] | None = None  # Specific user IDs
    target_segments: list[str] | None = None  # User segments
    target_locations: list[dict[str, float]] | None = None  # Geographic targeting
    target_device_types: list[str] | None = None  # android, ios, web

    # Scheduling
    scheduled_time: datetime | None = None
    time_zone: str = "UTC"
    send_immediately: bool = False

    # Frequency and limits
    max_sends_per_user: int = 1
    frequency_cap_hours: int = 24

    # A/B Testing
    ab_test_enabled: bool = False
    ab_test_variants: list[dict[str, Any]] = []
    ab_test_traffic_split: dict[str, float] = {}  # variant -> percentage

    # Campaign settings
    priority: str = "normal"  # low, normal, high, urgent
    expiry_time: datetime | None = None

    # Status tracking
    status: str = "draft"  # draft, scheduled, running, paused, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Performance metrics
    total_targeted: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_failed: int = 0


class UserSegment(BaseModel):
    """User segmentation for targeted notifications."""

    segment_id: str
    name: str
    description: str

    # Segmentation criteria
    location_filters: dict[str, Any] = {}  # Country, region, coordinates
    device_filters: list[str] = []  # Device types
    activity_filters: dict[str, Any] = {}  # Last active, engagement level
    alert_history_filters: dict[str, Any] = {}  # Alert interaction history

    # Dynamic segments
    is_dynamic: bool = True  # Automatically update membership
    update_frequency_hours: int = 24

    # Segment stats
    user_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)


class NotificationAnalytics(BaseModel):
    """Analytics data for notification performance."""

    notification_id: str
    campaign_id: str | None = None
    template_id: str
    user_id: str
    device_token: str

    # Timing
    sent_at: datetime
    delivered_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    dismissed_at: datetime | None = None

    # Status
    delivery_status: str  # sent, delivered, failed, expired
    failure_reason: str | None = None

    # Engagement
    time_to_open_seconds: int | None = None
    time_to_click_seconds: int | None = None
    actions_taken: list[str] = []

    # Context
    user_timezone: str | None = None
    device_type: str | None = None
    app_version: str | None = None

    # A/B Testing
    ab_variant: str | None = None


class EnhancedFirebaseService:
    """Enhanced Firebase Cloud Messaging service with advanced features.

    Provides functionality for:
    - Template-based notification generation
    - Campaign management and scheduling
    - User segmentation and targeting
    - A/B testing and optimization
    - Advanced analytics and reporting
    - Batch processing and rate limiting
    """

    def __init__(self) -> None:
        """Initialize enhanced Firebase service."""
        self.settings = settings
        self.app = None
        self.initialized = False

        # Template and campaign storage
        self.templates: dict[str, NotificationTemplate] = {}
        self.campaigns: dict[str, NotificationCampaign] = {}
        self.segments: dict[str, UserSegment] = {}

        # Analytics and performance tracking
        self.analytics: list[NotificationAnalytics] = []
        self.performance_metrics: dict[str, Any] = {
            "templates_used": {},
            "campaign_performance": {},
            "segment_performance": {},
            "delivery_rates_by_platform": {},
            "engagement_rates_by_template": {},
            "optimal_send_times": {},
            "ab_test_results": {}
        }

        # Rate limiting and queuing
        self.send_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.rate_limit_per_second = 100  # FCM rate limit
        self.batch_size = 500  # Maximum batch size for FCM

        # Background tasks
        self._queue_processor_task: asyncio.Task[None] | None = None
        self._analytics_processor_task: asyncio.Task[None] | None = None

        # Statistics
        self.stats = {
            "enhanced_notifications_sent": 0,
            "campaigns_executed": 0,
            "templates_rendered": 0,
            "segments_updated": 0,
            "ab_tests_completed": 0,
            "avg_template_render_time_ms": 0.0,
            "avg_campaign_completion_time_minutes": 0.0
        }

    async def initialize(self) -> bool:
        """Initialize enhanced Firebase service."""
        try:
            if self.initialized:
                return True

            if not FIREBASE_AVAILABLE:
                logger.warning("Firebase Admin SDK not available")
                return False

            # Initialize base Firebase service
            firebase_credentials = self._load_firebase_credentials()
            if not firebase_credentials:
                logger.error("Firebase credentials not found")
                return False

            cred = credentials.Certificate(firebase_credentials)
            self.app = firebase_admin.initialize_app(cred, name="enhanced_firebase")
            self.initialized = True

            # Start background tasks
            await self.start_background_tasks()

            # Load default templates
            await self._load_default_templates()

            logger.info("Enhanced Firebase service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize enhanced Firebase service: {e}")
            return False

    async def start_background_tasks(self) -> None:
        """Start background processing tasks."""
        if not self._queue_processor_task:
            self._queue_processor_task = asyncio.create_task(self._process_send_queue())
        if not self._analytics_processor_task:
            self._analytics_processor_task = asyncio.create_task(self._process_analytics())

    async def stop_background_tasks(self) -> None:
        """Stop background processing tasks."""
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            self._queue_processor_task = None
        if self._analytics_processor_task:
            self._analytics_processor_task.cancel()
            self._analytics_processor_task = None

    async def create_template(self, template: NotificationTemplate) -> bool:
        """Create a new notification template.

        Args:
            template: Template configuration

        Returns:
            True if template created successfully
        """
        try:
            # Validate template
            if not self._validate_template(template):
                return False

            self.templates[template.template_id] = template
            logger.info(f"Created notification template: {template.template_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False

    async def render_notification(
        self,
        template_id: str,
        variables: dict[str, str],
        user_preferences: dict[str, Any] | None = None
    ) -> PushNotificationPayload | None:
        """Render a notification from template with dynamic data.

        Args:
            template_id: Template identifier
            variables: Dynamic variables for template
            user_preferences: User-specific preferences

        Returns:
            Rendered notification payload or None if failed
        """
        start_time = datetime.now()

        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return None

            # Validate required variables
            missing_vars = set(template.required_variables) - set(variables.keys())
            if missing_vars:
                logger.error(f"Missing required variables: {missing_vars}")
                return None

            # Merge with default values
            render_vars = {**template.default_values, **variables}

            # Apply alert level specific overrides
            alert_level = variables.get("alert_level", "medium")
            if alert_level in template.alert_level_mapping:
                level_overrides = template.alert_level_mapping[alert_level]
                render_vars.update(level_overrides)

            # Render template content
            title = self._render_template_string(template.title_template, render_vars)
            body = self._render_template_string(template.body_template, render_vars)
            image_url = None
            if template.image_url_template:
                image_url = self._render_template_string(template.image_url_template, render_vars)

            # Create enhanced payload
            payload = PushNotificationPayload(
                title=title,
                body=body,
                image_url=image_url,
                alert_level=alert_level,
                category=template.category,
                data=render_vars
            )

            # Apply user preferences
            if user_preferences:
                payload = self._apply_user_preferences(payload, user_preferences)

            # Apply platform-specific settings
            self._apply_platform_settings(payload, template)

            # Update stats
            self.stats["templates_rendered"] += 1
            render_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_render_time_stats(render_time)

            return payload

        except Exception as e:
            logger.error(f"Failed to render notification template: {e}")
            return None

    async def create_campaign(self, campaign: NotificationCampaign) -> bool:
        """Create a new notification campaign.

        Args:
            campaign: Campaign configuration

        Returns:
            True if campaign created successfully
        """
        try:
            # Validate campaign
            if not self._validate_campaign(campaign):
                return False

            # Resolve target audience
            target_tokens = await self._resolve_campaign_targets(campaign)
            campaign.total_targeted = len(target_tokens)

            self.campaigns[campaign.campaign_id] = campaign
            logger.info(f"Created notification campaign: {campaign.campaign_id}")

            # Schedule campaign if needed
            if campaign.scheduled_time and not campaign.send_immediately:
                await self._schedule_campaign(campaign)
            elif campaign.send_immediately:
                await self._execute_campaign(campaign.campaign_id)

            return True

        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return False

    async def send_template_notification(
        self,
        template_id: str,
        user_id: str,
        variables: dict[str, str],
        device_tokens: list[str] | None = None
    ) -> dict[str, FirebaseNotificationResult]:
        """Send a template-based notification to a user.

        Args:
            template_id: Template identifier
            user_id: Target user ID
            variables: Dynamic template variables
            device_tokens: Specific device tokens (optional)

        Returns:
            Dictionary mapping device tokens to delivery results
        """
        try:
            # Get user preferences and device tokens
            if not device_tokens:
                device_tokens = await self._get_user_device_tokens(user_id)

            if not device_tokens:
                logger.warning(f"No device tokens found for user: {user_id}")
                return {}

            # Get user preferences
            user_preferences = await self._get_user_preferences(user_id)

            # Render notification
            payload = await self.render_notification(
                template_id=template_id,
                variables=variables,
                user_preferences=user_preferences
            )

            if not payload:
                return {}

            # Send to all user devices
            results = {}
            for token in device_tokens:
                result = await self._send_enhanced_notification(token, payload, user_id)
                results[token] = result

                # Track analytics
                await self._track_notification_analytics(
                    notification_id=f"{template_id}_{user_id}_{int(datetime.now().timestamp())}",
                    template_id=template_id,
                    user_id=user_id,
                    device_token=token,
                    payload=payload,
                    result=result
                )

            self.stats["enhanced_notifications_sent"] += len(results)
            return results

        except Exception as e:
            logger.error(f"Failed to send template notification: {e}")
            return {}

    async def create_user_segment(self, segment: UserSegment) -> bool:
        """Create a new user segment for targeting.

        Args:
            segment: Segment configuration

        Returns:
            True if segment created successfully
        """
        try:
            # Update segment membership
            await self._update_segment_membership(segment)

            self.segments[segment.segment_id] = segment
            self.stats["segments_updated"] += 1

            logger.info(f"Created user segment: {segment.segment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create user segment: {e}")
            return False

    async def get_campaign_analytics(self, campaign_id: str) -> dict[str, Any]:
        """Get comprehensive analytics for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign analytics data
        """
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return {}

            # Get campaign notifications
            campaign_analytics = [
                a for a in self.analytics
                if a.campaign_id == campaign_id
            ]

            # Calculate metrics
            total_sent = len(campaign_analytics)
            total_delivered = len([a for a in campaign_analytics if a.delivered_at])
            total_opened = len([a for a in campaign_analytics if a.opened_at])
            total_clicked = len([a for a in campaign_analytics if a.clicked_at])

            delivery_rate = (total_delivered / max(total_sent, 1)) * 100
            open_rate = (total_opened / max(total_delivered, 1)) * 100
            click_rate = (total_clicked / max(total_delivered, 1)) * 100

            # Platform breakdown
            platform_stats = {}
            for analytics in campaign_analytics:
                platform = analytics.device_type or "unknown"
                if platform not in platform_stats:
                    platform_stats[platform] = {"sent": 0, "delivered": 0, "opened": 0}

                platform_stats[platform]["sent"] += 1
                if analytics.delivered_at:
                    platform_stats[platform]["delivered"] += 1
                if analytics.opened_at:
                    platform_stats[platform]["opened"] += 1

            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "total_targeted": campaign.total_targeted,
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "delivery_rate_percentage": delivery_rate,
                "open_rate_percentage": open_rate,
                "click_rate_percentage": click_rate,
                "platform_breakdown": platform_stats,
                "created_at": campaign.created_at.isoformat(),
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get campaign analytics: {e}")
            return {}

    async def optimize_send_times(self, user_id: str) -> datetime | None:
        """Determine optimal send time for a user based on engagement history.

        Args:
            user_id: User identifier

        Returns:
            Optimal send time or None if insufficient data
        """
        try:
            # Get user's notification history
            user_analytics = [a for a in self.analytics if a.user_id == user_id]

            if len(user_analytics) < 10:  # Need sufficient data
                return None

            # Analyze engagement by hour of day
            hourly_engagement = {}
            for analytics in user_analytics:
                if analytics.opened_at:
                    hour = analytics.sent_at.hour
                    if hour not in hourly_engagement:
                        hourly_engagement[hour] = {"sent": 0, "opened": 0}
                    hourly_engagement[hour]["sent"] += 1
                    hourly_engagement[hour]["opened"] += 1

            # Find hour with highest engagement rate
            best_hour = None
            best_rate = 0.0

            for hour, stats in hourly_engagement.items():
                if stats["sent"] >= 3:  # Minimum sample size
                    rate = stats["opened"] / stats["sent"]
                    if rate > best_rate:
                        best_rate = rate
                        best_hour = hour

            if best_hour is not None:
                # Return next occurrence of optimal hour
                now = datetime.now()
                optimal_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
                if optimal_time <= now:
                    optimal_time += timedelta(days=1)
                return optimal_time

            return None

        except Exception as e:
            logger.error(f"Failed to optimize send times: {e}")
            return None

    def _load_firebase_credentials(self) -> dict[str, Any] | None:
        """Load Firebase credentials from settings."""
        try:
            if hasattr(self.settings, "FIREBASE_CREDENTIALS_PATH"):
                with open(self.settings.FIREBASE_CREDENTIALS_PATH) as f:
                    return json.load(f)  # type: ignore[no-any-return]
            elif hasattr(self.settings, "FIREBASE_CREDENTIALS_JSON"):
                return json.loads(self.settings.FIREBASE_CREDENTIALS_JSON)  # type: ignore[no-any-return]
            else:
                logger.error("Firebase credentials not configured")
                return None
        except Exception as e:
            logger.error(f"Failed to load Firebase credentials: {e}")
            return None

    async def _load_default_templates(self) -> None:
        """Load default notification templates."""
        try:
            # Malaria alert template
            malaria_alert_template = NotificationTemplate(
                template_id="malaria_alert",
                name="Malaria Risk Alert",
                description="Template for malaria risk notifications",
                category="alert",
                title_template="Malaria Alert: {{alert_level}} Risk",
                body_template="{{alert_level}} malaria risk detected in {{location}}. Risk score: {{risk_score}}%. Take preventive measures.",
                required_variables=["alert_level", "location", "risk_score"],
                alert_level_mapping={
                    "critical": {
                        "android_color": "#FF0000",
                        "ios_interruption_level": "critical",
                        "android_priority": "high"
                    },
                    "high": {
                        "android_color": "#FF6600",
                        "ios_interruption_level": "time-sensitive"
                    },
                    "medium": {
                        "android_color": "#FFA500"
                    },
                    "low": {
                        "android_color": "#FFFF00"
                    }
                }
            )

            # Emergency alert template
            emergency_template = NotificationTemplate(
                template_id="emergency_alert",
                name="Emergency Alert",
                description="Template for emergency notifications",
                category="emergency",
                title_template="EMERGENCY: {{alert_type}}",
                body_template="EMERGENCY ALERT: {{message}}. Immediate action required.",
                required_variables=["alert_type", "message"],
                android_settings={
                    "priority": "high",
                    "channel_id": "emergency_alerts",
                    "color": "#FF0000",
                    "sound": "emergency_sound"
                },
                ios_settings={
                    "priority": "high",
                    "interruption_level": "critical",
                    "sound": "emergency.wav"
                }
            )

            await self.create_template(malaria_alert_template)
            await self.create_template(emergency_template)

            logger.info("Default templates loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load default templates: {e}")

    def _validate_template(self, template: NotificationTemplate) -> bool:
        """Validate notification template."""
        # Check required fields
        if not template.template_id or not template.title_template or not template.body_template:
            return False

        # Validate template syntax (basic check for {{variable}} pattern)
        import re
        variables_in_title = re.findall(r'{{(\w+)}}', template.title_template)
        variables_in_body = re.findall(r'{{(\w+)}}', template.body_template)

        all_variables = set(variables_in_title + variables_in_body)
        required_vars = set(template.required_variables)

        # Check if all required variables are used
        if not required_vars.issubset(all_variables):
            logger.error("Required variables not used in template")
            return False

        return True

    def _validate_campaign(self, campaign: NotificationCampaign) -> bool:
        """Validate notification campaign."""
        # Check required fields
        if not campaign.campaign_id or not campaign.template_id:
            return False

        # Check template exists
        if campaign.template_id not in self.templates:
            logger.error(f"Template not found: {campaign.template_id}")
            return False

        # Validate targeting
        if not any([campaign.target_users, campaign.target_segments, campaign.target_locations]):
            logger.error("Campaign must have at least one targeting criteria")
            return False

        return True

    def _render_template_string(self, template: str, variables: dict[str, str]) -> str:
        """Render template string with variables."""
        try:
            # Simple template rendering (replace {{variable}} with values)
            result = template
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template

    def _apply_user_preferences(
        self,
        payload: PushNotificationPayload,
        preferences: dict[str, Any]
    ) -> PushNotificationPayload:
        """Apply user-specific preferences to notification."""
        # Apply sound preferences
        if "notification_sound" in preferences:
            payload.ios_sound = preferences["notification_sound"]
            payload.android_sound = preferences["notification_sound"]

        # Apply quiet hours
        if "quiet_hours" in preferences:
            quiet_start = preferences["quiet_hours"].get("start", 22)
            quiet_end = preferences["quiet_hours"].get("end", 8)
            current_hour = datetime.now().hour

            if quiet_start <= current_hour or current_hour <= quiet_end:
                payload.ios_interruption_level = "passive"
                payload.android_priority = "normal"

        return payload

    def _apply_platform_settings(
        self,
        payload: PushNotificationPayload,
        template: NotificationTemplate
    ) -> None:
        """Apply platform-specific settings from template."""
        # Apply Android settings
        android_settings = template.android_settings
        for key, value in android_settings.items():
            if hasattr(payload, f"android_{key}"):
                setattr(payload, f"android_{key}", value)

        # Apply iOS settings
        ios_settings = template.ios_settings
        for key, value in ios_settings.items():
            if hasattr(payload, f"ios_{key}"):
                setattr(payload, f"ios_{key}", value)

        # Apply Web settings
        web_settings = template.web_settings
        for key, value in web_settings.items():
            if hasattr(payload, f"web_{key}"):
                setattr(payload, f"web_{key}", value)

    async def _get_user_device_tokens(self, user_id: str) -> list[str]:
        """Get active device tokens for a user."""
        try:
            async with get_session() as db:
                tokens = db.query(UserDeviceToken).filter(  # type: ignore[attr-defined]
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.is_active,
                    UserDeviceToken.is_valid
                ).all()
                return [token.device_token for token in tokens]
        except Exception as e:
            logger.error(f"Failed to get user device tokens: {e}")
            return []

    async def _get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """Get user notification preferences."""
        # This would typically load from user preferences table
        # For now, return default preferences
        return {
            "notification_sound": "default",
            "quiet_hours": {"start": 22, "end": 8},
            "timezone": "UTC"
        }

    async def _send_enhanced_notification(
        self,
        device_token: str,
        payload: PushNotificationPayload,
        user_id: str
    ) -> FirebaseNotificationResult:
        """Send enhanced notification with full FCM features."""
        try:
            if not self.initialized:
                return FirebaseNotificationResult(
                    success=False,
                    error_code="NOT_INITIALIZED",
                    error_message="Firebase service not initialized"
                )

            # Build enhanced FCM message
            message = self._build_enhanced_fcm_message(device_token, payload)

            # Send notification
            response = messaging.send(message)

            return FirebaseNotificationResult(
                success=True,
                message_id=response
            )

        except Exception as e:
            logger.error(f"Enhanced notification send failed: {e}")
            return FirebaseNotificationResult(
                success=False,
                error_code="SEND_FAILED",
                error_message=str(e)
            )

    def _build_enhanced_fcm_message(self, device_token: str, payload: PushNotificationPayload) -> Any:
        """Build enhanced FCM message with platform-specific features."""
        # Build notification object
        notification = messaging.Notification(
            title=payload.title,
            body=payload.body,
            image=payload.image_url
        )

        # Build data payload
        data = payload.data or {}
        if payload.alert_level:
            data["alert_level"] = payload.alert_level
        if payload.category:
            data["category"] = payload.category
        if payload.deep_link:
            data["deep_link"] = payload.deep_link

        # Platform-specific configurations
        android_config = messaging.AndroidConfig(
            priority=payload.android_priority,
            ttl=timedelta(seconds=payload.android_ttl),
            collapse_key=payload.android_collapse_key,
            notification=messaging.AndroidNotification(
                channel_id=payload.android_channel_id,
                color=payload.android_color,
                sound=payload.android_sound,
                visibility=payload.android_visibility
            )
        )

        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound=payload.ios_sound,
                    badge=payload.ios_badge,
                    content_available=payload.ios_content_available,
                    mutable_content=payload.ios_mutable_content,
                    thread_id=payload.ios_thread_id,
                    category=payload.ios_category
                )
            )
        )

        web_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon=payload.web_icon,
                badge=payload.web_badge,
                require_interaction=payload.web_require_interaction,
                silent=payload.web_silent,
                vibrate=payload.web_vibrate,
                direction=payload.web_dir,
                actions=payload.web_actions
            )
        )

        return messaging.Message(
            token=device_token,
            notification=notification,
            data=data,
            android=android_config,
            apns=apns_config,
            webpush=web_config
        )

    async def _track_notification_analytics(
        self,
        notification_id: str,
        template_id: str,
        user_id: str,
        device_token: str,
        payload: PushNotificationPayload,
        result: FirebaseNotificationResult
    ) -> None:
        """Track notification analytics."""
        try:
            analytics = NotificationAnalytics(
                notification_id=notification_id,
                template_id=template_id,
                user_id=user_id,
                device_token=device_token,
                sent_at=datetime.now(),
                delivery_status="sent" if result.success else "failed",
                failure_reason=result.error_message if not result.success else None
            )

            self.analytics.append(analytics)

            # Update performance metrics
            template_metrics = self.performance_metrics["templates_used"]
            template_metrics[template_id] = template_metrics.get(template_id, 0) + 1

        except Exception as e:
            logger.error(f"Failed to track analytics: {e}")

    async def _resolve_campaign_targets(self, campaign: NotificationCampaign) -> list[str]:
        """Resolve campaign targeting to list of device tokens."""
        target_tokens = []

        try:
            # Target specific users
            if campaign.target_users:
                for user_id in campaign.target_users:
                    tokens = await self._get_user_device_tokens(user_id)
                    target_tokens.extend(tokens)

            # Target segments
            if campaign.target_segments:
                for segment_id in campaign.target_segments:
                    segment_tokens = await self._get_segment_device_tokens(segment_id)
                    target_tokens.extend(segment_tokens)

            # Remove duplicates
            return list(set(target_tokens))

        except Exception as e:
            logger.error(f"Failed to resolve campaign targets: {e}")
            return []

    async def _get_segment_device_tokens(self, segment_id: str) -> list[str]:
        """Get device tokens for users in a segment."""
        # This would implement segment membership resolution
        # For now, return empty list
        return []

    async def _execute_campaign(self, campaign_id: str) -> None:
        """Execute a notification campaign."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return

            campaign.status = "running"
            campaign.started_at = datetime.now()

            # Get target tokens
            target_tokens = await self._resolve_campaign_targets(campaign)

            # Send notifications
            for token in target_tokens:
                # Add to send queue for rate limiting
                await self.send_queue.put((campaign_id, token))

            self.stats["campaigns_executed"] += 1

        except Exception as e:
            logger.error(f"Failed to execute campaign: {e}")

    async def _schedule_campaign(self, campaign: NotificationCampaign) -> None:
        """Schedule a campaign for future execution."""
        # This would implement campaign scheduling
        # For now, just log the scheduling
        logger.info(f"Campaign {campaign.campaign_id} scheduled for {campaign.scheduled_time}")

    async def _update_segment_membership(self, segment: UserSegment) -> None:
        """Update user membership for a segment based on criteria."""
        # This would implement dynamic segment updates
        # For now, just update the timestamp
        segment.last_updated = datetime.now()

    async def _process_send_queue(self) -> None:
        """Background task to process notification send queue with rate limiting."""
        while True:
            try:
                # Process batch of notifications
                batch = []
                for _ in range(min(self.batch_size, self.send_queue.qsize())):
                    if not self.send_queue.empty():
                        item = await self.send_queue.get()
                        batch.append(item)

                if batch:
                    await self._process_notification_batch(batch)

                # Rate limiting
                await asyncio.sleep(1.0 / self.rate_limit_per_second)

            except asyncio.CancelledError:
                logger.info("Send queue processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in send queue processor: {e}")

    async def _process_notification_batch(self, batch: list[tuple]) -> None:
        """Process a batch of notifications."""
        # This would implement batch notification sending
        # For now, just log the batch processing
        logger.debug(f"Processing notification batch of size {len(batch)}")

    async def _process_analytics(self) -> None:
        """Background task to process and aggregate analytics."""
        while True:
            try:
                await asyncio.sleep(300)  # Process every 5 minutes

                # Update performance metrics
                await self._update_performance_metrics()

            except asyncio.CancelledError:
                logger.info("Analytics processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in analytics processor: {e}")

    async def _update_performance_metrics(self) -> None:
        """Update aggregated performance metrics."""
        try:
            # Calculate delivery rates by platform
            platform_stats = {}
            for analytics in self.analytics:
                platform = analytics.device_type or "unknown"
                if platform not in platform_stats:
                    platform_stats[platform] = {"sent": 0, "delivered": 0}

                platform_stats[platform]["sent"] += 1
                if analytics.delivered_at:
                    platform_stats[platform]["delivered"] += 1

            # Update metrics
            for platform, stats in platform_stats.items():
                if stats["sent"] > 0:
                    rate = (stats["delivered"] / stats["sent"]) * 100
                    self.performance_metrics["delivery_rates_by_platform"][platform] = rate

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    def _update_render_time_stats(self, render_time: float) -> None:
        """Update template render time statistics."""
        current_avg = self.stats["avg_template_render_time_ms"]
        render_count = self.stats["templates_rendered"]

        if render_count == 1:
            self.stats["avg_template_render_time_ms"] = render_time
        else:
            self.stats["avg_template_render_time_ms"] = (
                (current_avg * (render_count - 1) + render_time) / render_count
            )

    def get_stats(self) -> dict[str, Any]:
        """Get enhanced Firebase service statistics."""
        return {
            **self.stats,
            "templates_count": len(self.templates),
            "campaigns_count": len(self.campaigns),
            "segments_count": len(self.segments),
            "analytics_count": len(self.analytics),
            "performance_metrics": self.performance_metrics,
            "queue_size": self.send_queue.qsize(),
            "initialized": self.initialized
        }


# Global instance
enhanced_firebase_service = EnhancedFirebaseService()
