"""
Firebase Cloud Messaging (FCM) API Routes.

This module provides comprehensive REST API endpoints for push notification
management including device registration, notification sending, topic management,
emergency alerts, and analytics.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, validator

from ...config import get_settings
from ...notifications import NotificationManager
from ...notifications.emergency_alerts import EmergencyLevel
from ...notifications.models import DevicePlatform
from ..auth import get_current_user, require_permissions

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API requests/responses

class DeviceRegistrationRequest(BaseModel):
    """Request model for device registration."""
    token: str = Field(..., description="FCM device token", min_length=10)
    platform: DevicePlatform = Field(..., description="Device platform")
    user_id: str | None = Field(None, description="Associated user ID")
    device_info: dict[str, Any] | None = Field(default_factory=dict, description="Device metadata")
    auto_subscribe: bool = Field(True, description="Auto-subscribe to relevant topics")
    user_preferences: dict[str, Any] | None = Field(default_factory=dict, description="User preferences")

    @validator('token')
    def validate_token(cls, v: str) -> str:
        """Validate FCM token format."""
        if len(v) < 10:
            raise ValueError("FCM token too short")
        return v


class MalariaAlertRequest(BaseModel):
    """Request model for malaria risk alerts."""
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0.0 to 1.0)")
    location_name: str = Field(..., description="Human-readable location name")
    coordinates: dict[str, float] | None = Field(None, description="Geographic coordinates")
    environmental_data: dict[str, float] | None = Field(None, description="Environmental conditions")
    target_users: list[str] | None = Field(None, description="Specific user IDs to target")
    target_radius_km: float | None = Field(50.0, description="Geographic targeting radius")
    immediate: bool = Field(True, description="Send immediately or schedule")

    @validator('coordinates')
    def validate_coordinates(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        """Validate coordinate format."""
        if v is not None:
            if 'lat' not in v or 'lng' not in v:
                raise ValueError("Coordinates must contain 'lat' and 'lng' keys")
            if not (-90 <= v['lat'] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v['lng'] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v


class OutbreakAlertRequest(BaseModel):
    """Request model for outbreak alerts."""
    location_name: str = Field(..., description="Name of affected location")
    outbreak_probability: float = Field(..., ge=0.0, le=1.0, description="Outbreak probability")
    affected_population: int | None = Field(None, description="Number of people affected")
    coordinates: dict[str, float] | None = Field(None, description="Geographic coordinates")
    radius_km: float = Field(50.0, description="Alert radius in kilometers")
    severity: EmergencyLevel | None = Field(None, description="Emergency severity level")


class MedicationReminderRequest(BaseModel):
    """Request model for medication reminders."""
    user_id: str = Field(..., description="Target user ID")
    medication_name: str = Field(..., description="Name of medication")
    dosage: str | None = Field(None, description="Dosage information")
    schedule_time: datetime | None = Field(None, description="When to send reminder")


class TopicSubscriptionRequest(BaseModel):
    """Request model for topic subscriptions."""
    user_id: str = Field(..., description="User ID")
    topics: list[str] = Field(..., description="List of topic names")

    @validator('topics')
    def validate_topics(cls, v: list[str]) -> list[str]:
        """Validate topic names."""
        if not v:
            raise ValueError("At least one topic must be specified")
        for topic in v:
            if not topic or len(topic.strip()) == 0:
                raise ValueError("Topic names cannot be empty")
        return v


class NotificationAnalyticsQuery(BaseModel):
    """Query parameters for notification analytics."""
    days: int = Field(7, ge=1, le=365, description="Number of days for analysis")
    group_by: str = Field("day", description="Grouping period")

    @validator('group_by')
    def validate_group_by(cls, v: str) -> str:
        """Validate grouping period."""
        valid_periods = ["hour", "day", "week", "month"]
        if v not in valid_periods:
            raise ValueError(f"group_by must be one of: {valid_periods}")
        return v


# Initialize notification manager as dependency
async def get_notification_manager() -> NotificationManager:
    """Get notification manager instance."""
    settings = get_settings()
    return NotificationManager(
        fcm_credentials_path=getattr(settings, 'fcm_credentials_path', None),
        project_id=getattr(settings, 'fcm_project_id', None),
    )


# Device Management Endpoints

@router.post("/devices/register", status_code=status.HTTP_201_CREATED)
async def register_device(
    request: DeviceRegistrationRequest,
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Register a device for push notifications.

    Registers a new device token for receiving push notifications and
    optionally auto-subscribes to relevant topics based on user preferences.
    """
    try:
        success, error = await notification_manager.register_device(
            token=request.token,
            platform=request.platform,
            user_id=request.user_id or current_user.get("user_id"),
            device_info=request.device_info,
            auto_subscribe=request.auto_subscribe,
            user_preferences=request.user_preferences,
        )

        if success:
            return {
                "success": True,
                "message": "Device registered successfully",
                "token": request.token[:10] + "...",
                "platform": request.platform,
                "registered_at": datetime.now(UTC).isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device registration failed: {error}"
            )

    except Exception as e:
        logger.error(f"Device registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during device registration"
        )


@router.delete("/devices/{token}")
async def unregister_device(
    token: str = Path(..., description="FCM device token"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Unregister a device from push notifications.

    Deactivates the device token and removes all topic subscriptions.
    """
    try:
        success, error = await notification_manager.unregister_device(token)

        if success:
            return {
                "success": True,
                "message": "Device unregistered successfully",
                "token": token[:10] + "...",
                "unregistered_at": datetime.now(UTC).isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device unregistration failed: {error}"
            )

    except Exception as e:
        logger.error(f"Device unregistration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during device unregistration"
        )


# Notification Sending Endpoints

@router.post("/send/malaria-alert")
async def send_malaria_alert(
    request: MalariaAlertRequest,
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["send_notifications"])),
) -> dict[str, Any]:
    """
    Send malaria risk alert notification.

    Sends targeted malaria risk alerts to users based on geographic location
    and risk level with appropriate priority and delivery optimization.
    """
    try:
        result = await notification_manager.send_malaria_alert(
            risk_score=request.risk_score,
            location_name=request.location_name,
            coordinates=request.coordinates,
            environmental_data=request.environmental_data,
            target_users=request.target_users,
            target_radius_km=request.target_radius_km,
            immediate=request.immediate,
        )

        if result["success"]:
            return {
                "success": True,
                "message": "Malaria alert sent successfully",
                "alert_details": {
                    "risk_score": request.risk_score,
                    "location": request.location_name,
                    "immediate": request.immediate,
                },
                "delivery_results": result,
                "sent_at": datetime.now(UTC).isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to send malaria alert: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Malaria alert sending error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while sending malaria alert"
        )


@router.post("/send/outbreak-alert")
async def send_outbreak_alert(
    request: OutbreakAlertRequest,
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["send_emergency_alerts"])),
) -> dict[str, Any]:
    """
    Send emergency outbreak alert.

    Issues high-priority emergency alerts for malaria outbreaks with
    immediate delivery and comprehensive tracking.
    """
    try:
        result = await notification_manager.send_outbreak_alert(
            location_name=request.location_name,
            outbreak_probability=request.outbreak_probability,
            affected_population=request.affected_population,
            coordinates=request.coordinates,
            radius_km=request.radius_km,
            severity=request.severity,
        )

        if result["success"]:
            return {
                "success": True,
                "message": "Outbreak alert issued successfully",
                "alert_id": result.get("alert_id"),
                "alert_details": {
                    "location": request.location_name,
                    "probability": request.outbreak_probability,
                    "severity": request.severity,
                },
                "delivery_results": result.get("delivery_results", {}),
                "issued_at": result.get("issued_at"),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to issue outbreak alert: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Outbreak alert error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while issuing outbreak alert"
        )


@router.post("/send/medication-reminder")
async def send_medication_reminder(
    request: MedicationReminderRequest,
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Send medication reminder notification.

    Sends medication reminders to specified users with optional scheduling.
    """
    try:
        # Check if user can send to the specified user_id
        if request.user_id != current_user.get("user_id") and not current_user.get("is_healthcare_provider"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to send reminder to specified user"
            )

        result = await notification_manager.send_medication_reminder(
            user_id=request.user_id,
            medication_name=request.medication_name,
            dosage=request.dosage,
            schedule_time=request.schedule_time,
        )

        if result["success"]:
            return {
                "success": True,
                "message": "Medication reminder sent successfully",
                "reminder_details": {
                    "user_id": request.user_id,
                    "medication": request.medication_name,
                    "dosage": request.dosage,
                    "scheduled": request.schedule_time is not None,
                },
                "delivery_results": result,
                "sent_at": datetime.now(UTC).isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to send medication reminder: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Medication reminder error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while sending medication reminder"
        )


# Topic Management Endpoints

@router.post("/topics/subscribe")
async def subscribe_to_topics(
    request: TopicSubscriptionRequest,
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Subscribe user to notification topics.

    Subscribes all user devices to specified topics for targeted group messaging.
    """
    try:
        # Check if user can manage subscriptions for the specified user_id
        if request.user_id != current_user.get("user_id") and not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage subscriptions for specified user"
            )

        results = await notification_manager.subscribe_user_to_topics(
            user_id=request.user_id,
            topics=request.topics,
        )

        successful_topics = [topic for topic, success in results.items() if success]
        failed_topics = [topic for topic, success in results.items() if not success]

        return {
            "success": len(successful_topics) > 0,
            "message": f"Subscribed to {len(successful_topics)} of {len(request.topics)} topics",
            "subscription_results": {
                "successful_topics": successful_topics,
                "failed_topics": failed_topics,
                "user_id": request.user_id,
            },
            "subscribed_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Topic subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during topic subscription"
        )


@router.get("/topics/statistics")
async def get_topic_statistics(
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_analytics"])),
) -> dict[str, Any]:
    """
    Get topic subscription statistics.

    Returns comprehensive statistics about topic subscriptions and usage.
    """
    try:
        stats = await notification_manager.topic_manager.get_topic_statistics()

        return {
            "success": True,
            "topic_statistics": stats,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Topic statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving topic statistics"
        )


# Analytics Endpoints

@router.get("/analytics/dashboard")
async def get_notification_dashboard(
    days: int = Query(7, ge=1, le=365, description="Number of days for analysis"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_analytics"])),
) -> dict[str, Any]:
    """
    Get comprehensive notification analytics dashboard.

    Returns detailed analytics including delivery rates, engagement metrics,
    error analysis, and performance insights.
    """
    try:
        dashboard_data = await notification_manager.get_notification_dashboard(days=days)

        return {
            "success": True,
            "dashboard_data": dashboard_data,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Dashboard analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving dashboard analytics"
        )


@router.get("/analytics/delivery-summary")
async def get_delivery_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days for analysis"),
    group_by: str = Query("day", description="Grouping period (hour, day, week, month)"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_analytics"])),
) -> dict[str, Any]:
    """
    Get notification delivery summary with trends.

    Returns detailed delivery statistics grouped by specified time period.
    """
    try:
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        summary = await notification_manager.analytics.get_delivery_summary(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

        return {
            "success": True,
            "delivery_summary": summary,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Delivery summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving delivery summary"
        )


@router.get("/analytics/engagement")
async def get_engagement_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days for analysis"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_analytics"])),
) -> dict[str, Any]:
    """
    Get user engagement metrics for notifications.

    Returns click-through rates, template performance, and engagement analysis.
    """
    try:
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        engagement = await notification_manager.analytics.get_engagement_metrics(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "success": True,
            "engagement_metrics": engagement,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Engagement metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving engagement metrics"
        )


@router.get("/analytics/errors")
async def get_error_analysis(
    days: int = Query(7, ge=1, le=365, description="Number of days for analysis"),
    limit: int = Query(50, ge=1, le=200, description="Maximum error details to return"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_analytics"])),
) -> dict[str, Any]:
    """
    Get notification error analysis.

    Returns error patterns, failure analysis, and troubleshooting insights.
    """
    try:
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        error_analysis = await notification_manager.analytics.get_error_analysis(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return {
            "success": True,
            "error_analysis": error_analysis,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving error analysis"
        )


# System Management Endpoints

@router.get("/system/status")
async def get_system_status(
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_system_status"])),
) -> dict[str, Any]:
    """
    Get notification system status and health metrics.

    Returns comprehensive system health information and operational metrics.
    """
    try:
        status_data = await notification_manager.get_system_status()

        return {
            "success": True,
            "system_status": status_data,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking system status"
        )


@router.post("/system/cleanup")
async def cleanup_old_data(
    notification_retention_days: int = Query(90, ge=1, le=365, description="Days to retain notifications"),
    inactive_device_days: int = Query(30, ge=1, le=365, description="Days to consider device inactive"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["system_admin"])),
) -> dict[str, Any]:
    """
    Clean up old notification data and inactive devices.

    Removes old notification logs and deactivates devices that haven't been
    seen within the specified time period.
    """
    try:
        cleanup_stats = await notification_manager.cleanup_old_data(
            notification_retention_days=notification_retention_days,
            inactive_device_days=inactive_device_days,
        )

        return {
            "success": True,
            "message": "Data cleanup completed successfully",
            "cleanup_statistics": cleanup_stats,
            "cleaned_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Data cleanup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during data cleanup"
        )


# Emergency Alert Management

@router.get("/emergency/active-alerts")
async def get_active_emergency_alerts(
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["view_emergency_alerts"])),
) -> dict[str, Any]:
    """
    Get all currently active emergency alerts.

    Returns list of active emergency alerts with their status and details.
    """
    try:
        active_alerts = await notification_manager.emergency_system.get_active_emergency_alerts()

        return {
            "success": True,
            "active_alerts": active_alerts,
            "alert_count": len(active_alerts),
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Active alerts error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving active alerts"
        )


@router.post("/emergency/cancel-alert/{alert_id}")
async def cancel_emergency_alert(
    alert_id: str = Path(..., description="Emergency alert ID to cancel"),
    reason: str = Body(..., description="Reason for cancellation"),
    send_notice: bool = Body(True, description="Send cancellation notice to users"),
    notification_manager: NotificationManager = Depends(get_notification_manager),
    current_user: dict[str, Any] = Depends(require_permissions(["cancel_emergency_alerts"])),
) -> dict[str, Any]:
    """
    Cancel an active emergency alert.

    Cancels pending notifications and optionally sends cancellation notice to users.
    """
    try:
        result = await notification_manager.emergency_system.cancel_emergency_alert(
            alert_id=alert_id,
            reason=reason,
            send_cancellation_notice=send_notice,
        )

        if result["success"]:
            return {
                "success": True,
                "message": f"Emergency alert {alert_id} cancelled successfully",
                "cancellation_details": result,
                "cancelled_by": current_user.get("user_id"),
                "cancelled_at": result.get("cancelled_at"),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel alert: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Alert cancellation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while cancelling emergency alert"
        )
