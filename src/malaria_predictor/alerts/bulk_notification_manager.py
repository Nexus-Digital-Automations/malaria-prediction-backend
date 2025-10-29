"""Bulk notification management and scheduling system.

Provides comprehensive bulk notification capabilities including:
- Mass notification campaigns
- Scheduled notification delivery
- Rate limiting and queue management
- Batch processing optimization
- Geographic and demographic targeting
- Performance monitoring and analytics
- Retry logic and failure handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from ..config import settings
from ..database.models import UserDeviceToken
from ..database.session import get_session
from .alert_template_manager import alert_template_manager

logger = logging.getLogger(__name__)


class TargetingCriteria(BaseModel):
    """Criteria for targeting users in bulk notifications."""

    # User-based targeting
    user_ids: list[str] = []
    user_segments: list[str] = []
    exclude_user_ids: list[str] = []

    # Geographic targeting
    countries: list[str] = []
    regions: list[str] = []
    coordinates: list[dict[str, float]] = []  # [{"lat": 40.7, "lng": -74.0, "radius_km": 50}]
    exclude_countries: list[str] = []

    # Device and platform targeting
    device_types: list[str] = []  # android, ios, web
    app_versions: list[str] = []
    platform_versions: list[str] = []

    # Behavioral targeting
    last_active_days: int | None = None  # Users active within N days
    alert_engagement_level: str | None = None  # high, medium, low
    subscription_status: str | None = None  # active, inactive, trial

    # Risk-based targeting
    risk_score_min: float | None = None
    risk_score_max: float | None = None
    alert_history_count_min: int | None = None


class NotificationSchedule(BaseModel):
    """Schedule configuration for bulk notifications."""

    # Immediate or scheduled
    send_immediately: bool = False
    scheduled_time: datetime | None = None
    timezone: str = "UTC"

    # Recurring schedules
    is_recurring: bool = False
    recurrence_pattern: str | None = None  # daily, weekly, monthly, custom
    recurrence_interval: int = 1  # Every N intervals
    recurrence_days: list[int] = []  # Days of week (0=Monday) or month
    recurrence_end_date: datetime | None = None
    max_occurrences: int | None = None

    # Send time optimization
    optimize_send_times: bool = False  # Use user-specific optimal times
    send_window_start: int = 9  # Hour of day (24-hour format)
    send_window_end: int = 21  # Hour of day
    respect_quiet_hours: bool = True

    # Rate limiting
    max_sends_per_minute: int = 100
    batch_size: int = 500
    delay_between_batches_seconds: int = 60


class BulkNotificationCampaign(BaseModel):
    """Bulk notification campaign definition."""

    campaign_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    campaign_type: str  # emergency, promotional, informational, alert

    # Content
    template_id: str | None = None
    template_variables: dict[str, str] = {}
    custom_content: dict[str, str] = {}  # title, body, etc.

    # Targeting
    targeting: TargetingCriteria
    channels: list[str] = ["push"]  # push, email, sms, webhook

    # Scheduling
    schedule: NotificationSchedule

    # Campaign settings
    priority: str = "normal"  # low, normal, high, urgent
    expiry_hours: int = 24  # Campaign expiration
    allow_duplicates: bool = False  # Send to users who already received similar
    require_confirmation: bool = False  # Require admin confirmation before send

    # A/B Testing
    ab_test_enabled: bool = False
    ab_test_variants: list[dict[str, Any]] = []
    ab_test_traffic_split: dict[str, float] = {}

    # Status and tracking
    status: str = "draft"  # draft, scheduled, running, paused, completed, cancelled, failed
    created_by: str | None = None
    approved_by: str | None = None

    # Metrics
    target_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @validator('campaign_type')
    def validate_campaign_type(cls, v):
        valid_types = ['emergency', 'promotional', 'informational', 'alert']
        if v not in valid_types:
            raise ValueError(f'Campaign type must be one of {valid_types}')
        return v


class BulkNotificationJob(BaseModel):
    """Individual bulk notification job."""

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    batch_number: int

    # Recipients
    target_users: list[str]
    target_tokens: list[str]

    # Content
    rendered_content: dict[str, str]  # channel -> content

    # Execution
    status: str = "pending"  # pending, running, completed, failed, cancelled
    retry_count: int = 0
    max_retries: int = 3

    # Results
    success_count: int = 0
    failure_count: int = 0
    error_details: list[dict[str, str]] = []

    # Timing
    scheduled_time: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    processing_time_seconds: float | None = None


class BulkNotificationManager:
    """Manages bulk notification campaigns and scheduling.

    Provides functionality for:
    - Campaign creation and management
    - User targeting and segmentation
    - Batch processing and rate limiting
    - Scheduled delivery with timezone support
    - Performance monitoring and analytics
    - Retry logic and failure handling
    """

    def __init__(self) -> None:
        """Initialize the bulk notification manager."""
        self.settings = settings

        # Campaign and job storage
        self.campaigns: dict[str, BulkNotificationCampaign] = {}
        self.jobs: dict[str, BulkNotificationJob] = {}

        # Processing queues
        self.job_queue: list[Any] = asyncio.Queue()
        self.retry_queue: list[Any] = asyncio.Queue()

        # Background tasks
        self._scheduler_task: asyncio.Task | None = None
        self._processor_task: asyncio.Task | None = None
        self._retry_task: asyncio.Task | None = None

        # Rate limiting
        self.rate_limiter = asyncio.Semaphore(100)  # Max concurrent sends

        # Statistics
        self.stats = {
            "campaigns_created": 0,
            "campaigns_executed": 0,
            "total_notifications_sent": 0,
            "total_notifications_delivered": 0,
            "total_notifications_failed": 0,
            "avg_campaign_completion_time_minutes": 0.0,
            "avg_delivery_rate_percentage": 0.0,
            "batch_processing_efficiency": 0.0,
            "active_campaigns": 0,
            "queued_jobs": 0
        }

    async def start_background_tasks(self) -> None:
        """Start background processing tasks."""
        if not self._scheduler_task:
            self._scheduler_task = asyncio.create_task(self._campaign_scheduler())
        if not self._processor_task:
            self._processor_task = asyncio.create_task(self._job_processor())
        if not self._retry_task:
            self._retry_task = asyncio.create_task(self._retry_processor())

    async def stop_background_tasks(self) -> None:
        """Stop background processing tasks."""
        for task in [self._scheduler_task, self._processor_task, self._retry_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def create_campaign(
        self,
        campaign: BulkNotificationCampaign,
        user_id: str
    ) -> str | None:
        """Create a new bulk notification campaign.

        Args:
            campaign: Campaign configuration
            user_id: User creating the campaign

        Returns:
            Campaign ID if created successfully, None otherwise
        """
        try:
            # Validate campaign
            validation_result = await self._validate_campaign(campaign)
            if not validation_result["valid"]:
                logger.error(f"Campaign validation failed: {validation_result['errors']}")
                return None

            # Set metadata
            campaign.created_by = user_id
            campaign.created_at = datetime.now()

            # Resolve targeting to get target count
            target_users = await self._resolve_targeting(campaign.targeting)
            campaign.target_count = len(target_users)

            if campaign.target_count == 0:
                logger.warning("Campaign has no target users")

            # Store campaign
            self.campaigns[campaign.campaign_id] = campaign

            # Schedule campaign if needed
            if campaign.schedule.send_immediately:
                await self._execute_campaign(campaign.campaign_id)
            elif campaign.schedule.scheduled_time:
                campaign.status = "scheduled"
                campaign.scheduled_at = campaign.schedule.scheduled_time

            self.stats["campaigns_created"] += 1
            logger.info(f"Created campaign {campaign.campaign_id} targeting {campaign.target_count} users")

            return campaign.campaign_id

        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return None

    async def update_campaign(
        self,
        campaign_id: str,
        updates: dict[str, Any],
        user_id: str
    ) -> bool:
        """Update an existing campaign.

        Args:
            campaign_id: Campaign identifier
            updates: Fields to update
            user_id: User making the update

        Returns:
            True if updated successfully
        """
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False

            # Check permissions
            if campaign.created_by != user_id:
                logger.error("User not authorized to update campaign")
                return False

            # Check if campaign can be updated
            if campaign.status in ["running", "completed", "cancelled"]:
                logger.error(f"Cannot update campaign in status: {campaign.status}")
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)

            # Re-validate if content changed
            if any(key in updates for key in ["targeting", "template_id", "custom_content"]):
                validation_result = await self._validate_campaign(campaign)
                if not validation_result["valid"]:
                    logger.error(f"Updated campaign validation failed: {validation_result['errors']}")
                    return False

            logger.info(f"Updated campaign {campaign_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update campaign: {e}")
            return False

    async def execute_campaign(self, campaign_id: str, user_id: str) -> bool:
        """Manually execute a campaign.

        Args:
            campaign_id: Campaign identifier
            user_id: User executing the campaign

        Returns:
            True if execution started successfully
        """
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False

            # Check permissions
            if campaign.created_by != user_id:
                logger.error("User not authorized to execute campaign")
                return False

            # Check if campaign can be executed
            if campaign.status not in ["draft", "scheduled"]:
                logger.error(f"Cannot execute campaign in status: {campaign.status}")
                return False

            # Check if confirmation is required
            if campaign.require_confirmation and not campaign.approved_by:
                logger.error("Campaign requires approval before execution")
                return False

            await self._execute_campaign(campaign_id)
            return True

        except Exception as e:
            logger.error(f"Failed to execute campaign: {e}")
            return False

    async def cancel_campaign(self, campaign_id: str, user_id: str) -> bool:
        """Cancel a campaign.

        Args:
            campaign_id: Campaign identifier
            user_id: User cancelling the campaign

        Returns:
            True if cancelled successfully
        """
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False

            # Check permissions
            if campaign.created_by != user_id:
                logger.error("User not authorized to cancel campaign")
                return False

            # Cancel campaign
            if campaign.status in ["draft", "scheduled", "running"]:
                campaign.status = "cancelled"

                # Cancel pending jobs
                for job in self.jobs.values():
                    if job.campaign_id == campaign_id and job.status == "pending":
                        job.status = "cancelled"

                logger.info(f"Cancelled campaign {campaign_id}")
                return True
            else:
                logger.error(f"Cannot cancel campaign in status: {campaign.status}")
                return False

        except Exception as e:
            logger.error(f"Failed to cancel campaign: {e}")
            return False

    async def get_campaign_status(self, campaign_id: str) -> dict[str, Any] | None:
        """Get detailed status of a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign status details or None if not found
        """
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return None

            # Get job statistics
            campaign_jobs = [job for job in self.jobs.values() if job.campaign_id == campaign_id]

            pending_jobs = len([job for job in campaign_jobs if job.status == "pending"])
            running_jobs = len([job for job in campaign_jobs if job.status == "running"])
            completed_jobs = len([job for job in campaign_jobs if job.status == "completed"])
            failed_jobs = len([job for job in campaign_jobs if job.status == "failed"])

            # Calculate progress
            total_jobs = len(campaign_jobs)
            if total_jobs > 0:
                progress_percentage = (completed_jobs / total_jobs) * 100
            else:
                progress_percentage = 0

            # Calculate rates
            delivery_rate = 0.0
            if campaign.sent_count > 0:
                delivery_rate = (campaign.delivered_count / campaign.sent_count) * 100

            return {
                "campaign_id": campaign_id,
                "name": campaign.name,
                "status": campaign.status,
                "progress_percentage": progress_percentage,
                "target_count": campaign.target_count,
                "sent_count": campaign.sent_count,
                "delivered_count": campaign.delivered_count,
                "failed_count": campaign.failed_count,
                "opened_count": campaign.opened_count,
                "clicked_count": campaign.clicked_count,
                "delivery_rate_percentage": delivery_rate,
                "jobs": {
                    "total": total_jobs,
                    "pending": pending_jobs,
                    "running": running_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs
                },
                "created_at": campaign.created_at.isoformat(),
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
                "estimated_completion": self._estimate_completion_time(campaign_id)
            }

        except Exception as e:
            logger.error(f"Failed to get campaign status: {e}")
            return None

    async def get_user_campaigns(
        self,
        user_id: str,
        status_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Get campaigns created by a user.

        Args:
            user_id: User identifier
            status_filter: Filter by campaign status

        Returns:
            List of user's campaigns
        """
        try:
            user_campaigns = []

            for campaign in self.campaigns.values():
                if campaign.created_by == user_id:
                    if status_filter and campaign.status != status_filter:
                        continue

                    user_campaigns.append({
                        "campaign_id": campaign.campaign_id,
                        "name": campaign.name,
                        "description": campaign.description,
                        "campaign_type": campaign.campaign_type,
                        "status": campaign.status,
                        "target_count": campaign.target_count,
                        "sent_count": campaign.sent_count,
                        "delivered_count": campaign.delivered_count,
                        "created_at": campaign.created_at.isoformat(),
                        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
                    })

            # Sort by creation date (newest first)
            user_campaigns.sort(key=lambda c: c["created_at"], reverse=True)

            return user_campaigns

        except Exception as e:
            logger.error(f"Failed to get user campaigns: {e}")
            return []

    async def _validate_campaign(self, campaign: BulkNotificationCampaign) -> dict[str, Any]:
        """Validate campaign configuration."""
        errors = []
        warnings = []

        try:
            # Validate content
            if not campaign.template_id and not campaign.custom_content:
                errors.append("Campaign must have either template_id or custom_content")

            if campaign.template_id:
                # Validate template exists
                templates = await alert_template_manager.list_templates()
                template_ids = [t["template_id"] for t in templates]
                if campaign.template_id not in template_ids:
                    errors.append(f"Template not found: {campaign.template_id}")

            # Validate targeting
            if not any([
                campaign.targeting.user_ids,
                campaign.targeting.user_segments,
                campaign.targeting.countries,
                campaign.targeting.regions,
                campaign.targeting.coordinates
            ]):
                errors.append("Campaign must have at least one targeting criteria")

            # Validate channels
            valid_channels = ["push", "email", "sms", "webhook"]
            invalid_channels = [ch for ch in campaign.channels if ch not in valid_channels]
            if invalid_channels:
                errors.append(f"Invalid channels: {invalid_channels}")

            # Validate schedule
            if not campaign.schedule.send_immediately and not campaign.schedule.scheduled_time:
                errors.append("Campaign must be set to send immediately or have a scheduled time")

            if campaign.schedule.scheduled_time and campaign.schedule.scheduled_time <= datetime.now():
                warnings.append("Scheduled time is in the past")

            # Validate A/B testing
            if campaign.ab_test_enabled:
                if not campaign.ab_test_variants:
                    errors.append("A/B test requires variants")

                total_split = sum(campaign.ab_test_traffic_split.values())
                if abs(total_split - 1.0) > 0.01:
                    errors.append("A/B test traffic split must sum to 1.0")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"Campaign validation failed: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }

    async def _resolve_targeting(self, targeting: TargetingCriteria) -> list[str]:
        """Resolve targeting criteria to list of user IDs."""
        try:
            target_users = set()

            # Direct user IDs
            if targeting.user_ids:
                target_users.update(targeting.user_ids)

            # User segments (would implement segment resolution)
            if targeting.user_segments:
                for segment_id in targeting.user_segments:
                    segment_users = await self._get_segment_users(segment_id)
                    target_users.update(segment_users)

            # Geographic targeting
            if targeting.countries or targeting.regions or targeting.coordinates:
                geo_users = await self._get_users_by_geography(targeting)
                target_users.update(geo_users)

            # Device targeting
            if targeting.device_types or targeting.app_versions or targeting.platform_versions:
                device_users = await self._get_users_by_device(targeting)
                target_users.update(device_users)

            # Behavioral targeting
            if targeting.last_active_days or targeting.alert_engagement_level:
                behavior_users = await self._get_users_by_behavior(targeting)
                target_users.update(behavior_users)

            # Risk-based targeting
            if targeting.risk_score_min or targeting.risk_score_max or targeting.alert_history_count_min:
                risk_users = await self._get_users_by_risk(targeting)
                target_users.update(risk_users)

            # Apply exclusions
            if targeting.exclude_user_ids:
                target_users -= set(targeting.exclude_user_ids)

            if targeting.exclude_countries:
                excluded_users = await self._get_users_by_countries(targeting.exclude_countries)
                target_users -= set(excluded_users)

            return list(target_users)

        except Exception as e:
            logger.error(f"Failed to resolve targeting: {e}")
            return []

    async def _execute_campaign(self, campaign_id: str):
        """Execute a campaign by creating and queuing jobs."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return

            campaign.status = "running"
            campaign.started_at = datetime.now()

            # Resolve target users
            target_users = await self._resolve_targeting(campaign.targeting)

            if not target_users:
                campaign.status = "completed"
                campaign.completed_at = datetime.now()
                logger.warning(f"Campaign {campaign_id} completed with no target users")
                return

            # Create jobs in batches
            batch_size = campaign.schedule.batch_size
            for i in range(0, len(target_users), batch_size):
                batch_users = target_users[i:i + batch_size]
                batch_number = i // batch_size + 1

                # Get device tokens for batch users
                batch_tokens = await self._get_user_device_tokens(batch_users, campaign.channels)

                # Render content for the job
                rendered_content = await self._render_campaign_content(campaign, batch_users[0])

                # Create job
                job = BulkNotificationJob(
                    campaign_id=campaign_id,
                    batch_number=batch_number,
                    target_users=batch_users,
                    target_tokens=batch_tokens,
                    rendered_content=rendered_content,
                    scheduled_time=datetime.now()
                )

                self.jobs[job.job_id] = job
                await self.job_queue.put(job.job_id)

            self.stats["campaigns_executed"] += 1
            self.stats["active_campaigns"] = len([c for c in self.campaigns.values() if c.status == "running"])

            logger.info(f"Campaign {campaign_id} execution started with {len(target_users)} targets")

        except Exception as e:
            logger.error(f"Failed to execute campaign: {e}")
            if campaign_id in self.campaigns:
                self.campaigns[campaign_id].status = "failed"

    async def _render_campaign_content(
        self,
        campaign: BulkNotificationCampaign,
        sample_user_id: str
    ) -> dict[str, str]:
        """Render campaign content for notification delivery."""
        try:
            rendered_content = {}

            if campaign.template_id:
                # Use template
                for channel in campaign.channels:
                    preview = await alert_template_manager.render_template(
                        template_id=campaign.template_id,
                        variables=campaign.template_variables,
                        channel=channel
                    )
                    if preview:
                        if channel == "push":
                            rendered_content[channel] = {
                                "title": preview.rendered_title,
                                "body": preview.rendered_body
                            }
                        elif channel == "email":
                            rendered_content[channel] = {
                                "subject": preview.rendered_title,
                                "body": preview.rendered_body
                            }
                        elif channel == "sms":
                            rendered_content[channel] = {
                                "message": f"{preview.rendered_title}: {preview.rendered_body}"
                            }
            else:
                # Use custom content
                for channel in campaign.channels:
                    rendered_content[channel] = campaign.custom_content

            return rendered_content

        except Exception as e:
            logger.error(f"Failed to render campaign content: {e}")
            return {}

    async def _get_user_device_tokens(
        self,
        user_ids: list[str],
        channels: list[str]
    ) -> list[str]:
        """Get device tokens for users and channels."""
        try:
            tokens = []

            if "push" in channels:
                async with get_session() as db:
                    device_tokens = db.query(UserDeviceToken).filter(
                        UserDeviceToken.user_id.in_(user_ids),
                        UserDeviceToken.is_active,
                        UserDeviceToken.is_valid
                    ).all()

                    tokens.extend([token.device_token for token in device_tokens])

            return tokens

        except Exception as e:
            logger.error(f"Failed to get user device tokens: {e}")
            return []

    async def _get_segment_users(self, segment_id: str) -> list[str]:
        """Get users belonging to a segment."""
        # This would implement segment user resolution
        # For now, return empty list
        return []

    async def _get_users_by_geography(self, targeting: TargetingCriteria) -> list[str]:
        """Get users based on geographic targeting."""
        # This would implement geographic user resolution
        # For now, return empty list
        return []

    async def _get_users_by_device(self, targeting: TargetingCriteria) -> list[str]:
        """Get users based on device targeting."""
        # This would implement device-based user resolution
        # For now, return empty list
        return []

    async def _get_users_by_behavior(self, targeting: TargetingCriteria) -> list[str]:
        """Get users based on behavioral targeting."""
        # This would implement behavioral user resolution
        # For now, return empty list
        return []

    async def _get_users_by_risk(self, targeting: TargetingCriteria) -> list[str]:
        """Get users based on risk targeting."""
        # This would implement risk-based user resolution
        # For now, return empty list
        return []

    async def _get_users_by_countries(self, countries: list[str]) -> list[str]:
        """Get users from specific countries."""
        # This would implement country-based user resolution
        # For now, return empty list
        return []

    def _estimate_completion_time(self, campaign_id: str) -> str | None:
        """Estimate campaign completion time."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign or campaign.status != "running":
                return None

            # Simple estimation based on remaining jobs and processing rate
            remaining_jobs = len([job for job in self.jobs.values()
                                if job.campaign_id == campaign_id and job.status in ["pending", "running"]])

            if remaining_jobs == 0:
                return "Soon"

            # Estimate based on average job processing time
            avg_job_time_minutes = 2  # Rough estimate
            estimated_minutes = remaining_jobs * avg_job_time_minutes

            completion_time = datetime.now() + timedelta(minutes=estimated_minutes)
            return completion_time.isoformat()

        except Exception as e:
            logger.error(f"Failed to estimate completion time: {e}")
            return None

    async def _campaign_scheduler(self):
        """Background task to check for scheduled campaigns."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                for campaign in self.campaigns.values():
                    if (campaign.status == "scheduled" and
                        campaign.scheduled_at and
                        campaign.scheduled_at <= now):

                        await self._execute_campaign(campaign.campaign_id)

            except asyncio.CancelledError:
                logger.info("Campaign scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in campaign scheduler: {e}")

    async def _job_processor(self):
        """Background task to process notification jobs."""
        while True:
            try:
                # Get job from queue
                job_id = await self.job_queue.get()
                job = self.jobs.get(job_id)

                if not job or job.status != "pending":
                    continue

                await self._process_job(job)

            except asyncio.CancelledError:
                logger.info("Job processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in job processor: {e}")

    async def _process_job(self, job: BulkNotificationJob):
        """Process a single notification job."""
        try:
            job.status = "running"
            job.started_at = datetime.now()

            async with self.rate_limiter:
                # Send notifications for the job
                for token in job.target_tokens:
                    try:
                        # Send push notification (example)
                        if "push" in job.rendered_content:
                            job.rendered_content["push"]
                            # Here you would call the actual notification service
                            # result = await notification_service.send_notification(...)

                            job.success_count += 1

                    except Exception as e:
                        job.failure_count += 1
                        job.error_details.append({
                            "token": token,
                            "error": str(e)
                        })

            # Update job status
            job.status = "completed"
            job.completed_at = datetime.now()
            job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()

            # Update campaign stats
            campaign = self.campaigns.get(job.campaign_id)
            if campaign:
                campaign.sent_count += job.success_count + job.failure_count
                campaign.delivered_count += job.success_count
                campaign.failed_count += job.failure_count

                # Check if campaign is complete
                campaign_jobs = [j for j in self.jobs.values() if j.campaign_id == job.campaign_id]
                completed_jobs = [j for j in campaign_jobs if j.status in ["completed", "failed", "cancelled"]]

                if len(completed_jobs) == len(campaign_jobs):
                    campaign.status = "completed"
                    campaign.completed_at = datetime.now()

            logger.info(f"Processed job {job.job_id}: {job.success_count} success, {job.failure_count} failed")

        except Exception as e:
            logger.error(f"Failed to process job {job.job_id}: {e}")
            job.status = "failed"
            job.completed_at = datetime.now()

            # Schedule retry if attempts remaining
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = "pending"
                await self.retry_queue.put(job.job_id)

    async def _retry_processor(self):
        """Background task to process failed job retries."""
        while True:
            try:
                job_id = await self.retry_queue.get()

                # Wait before retry
                await asyncio.sleep(300)  # 5 minute delay

                job = self.jobs.get(job_id)
                if job and job.status == "pending":
                    await self.job_queue.put(job_id)

            except asyncio.CancelledError:
                logger.info("Retry processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in retry processor: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get bulk notification manager statistics."""
        self.stats["queued_jobs"] = self.job_queue.qsize()
        self.stats["active_campaigns"] = len([c for c in self.campaigns.values() if c.status == "running"])

        return {
            **self.stats,
            "total_campaigns": len(self.campaigns),
            "total_jobs": len(self.jobs),
            "campaigns_by_status": self._get_campaigns_by_status(),
            "jobs_by_status": self._get_jobs_by_status()
        }

    def _get_campaigns_by_status(self) -> dict[str, int]:
        """Get campaign count by status."""
        status_counts: dict[str, int] = {}
        for campaign in self.campaigns.values():
            status_counts[campaign.status] = status_counts.get(campaign.status, 0) + 1
        return status_counts

    def _get_jobs_by_status(self) -> dict[str, int]:
        """Get job count by status."""
        status_counts: dict[str, int] = {}
        for job in self.jobs.values():
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        return status_counts


# Global instance
bulk_notification_manager = BulkNotificationManager()
