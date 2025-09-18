"""API endpoints for alert management and configuration.

Provides REST API endpoints for:
- Alert configuration management
- Alert rule creation and management
- Alert history and querying
- WebSocket connection management
- Device token registration
- Notification preferences
"""

import logging
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from ...database.models import (
    Alert,
    AlertConfiguration,
    AlertPerformanceMetrics,
    AlertRule,
    UserDeviceToken,
)
from ...database.session import get_session as get_database
from ..auth import get_current_user
from ...database.security_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# Pydantic models for API requests/responses
class AlertConfigurationCreate(BaseModel):
    """Request model for creating alert configurations."""

    name: str = Field(..., description="Configuration name")
    low_risk_threshold: float = Field(0.3, ge=0.0, le=1.0)
    medium_risk_threshold: float = Field(0.6, ge=0.0, le=1.0)
    high_risk_threshold: float = Field(0.8, ge=0.0, le=1.0)
    critical_risk_threshold: float = Field(0.9, ge=0.0, le=1.0)

    # Geographic filters
    latitude_min: float | None = None
    latitude_max: float | None = None
    longitude_min: float | None = None
    longitude_max: float | None = None
    country_codes: list[str] | None = None
    admin_regions: list[str] | None = None

    # Time-based settings
    alert_frequency_hours: int = Field(24, ge=1, le=168)
    time_horizon_days: int = Field(7, ge=1, le=30)
    active_hours_start: int | None = Field(None, ge=0, le=23)
    active_hours_end: int | None = Field(None, ge=0, le=23)
    timezone: str = "UTC"

    # Notification channels
    enable_push_notifications: bool = True
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_webhook_notifications: bool = False

    # Contact information
    email_addresses: list[str] | None = None
    phone_numbers: list[str] | None = None
    webhook_urls: list[str] | None = None

    # Emergency settings
    enable_emergency_escalation: bool = False
    emergency_contact_emails: list[str] | None = None
    emergency_contact_phones: list[str] | None = None
    emergency_escalation_threshold: float = Field(0.95, ge=0.0, le=1.0)

    # Configuration status
    is_active: bool = True
    is_default: bool = False


class AlertConfigurationResponse(BaseModel):
    """Response model for alert configurations."""

    id: int
    user_id: str
    configuration_name: str
    low_risk_threshold: float
    medium_risk_threshold: float
    high_risk_threshold: float
    critical_risk_threshold: float
    latitude_min: float | None
    latitude_max: float | None
    longitude_min: float | None
    longitude_max: float | None
    country_codes: list[str] | None
    admin_regions: list[str] | None
    alert_frequency_hours: int
    time_horizon_days: int
    active_hours_start: int | None
    active_hours_end: int | None
    timezone: str
    enable_push_notifications: bool
    enable_email_notifications: bool
    enable_sms_notifications: bool
    enable_webhook_notifications: bool
    email_addresses: list[str] | None
    phone_numbers: list[str] | None
    webhook_urls: list[str] | None
    enable_emergency_escalation: bool
    emergency_contact_emails: list[str] | None
    emergency_contact_phones: list[str] | None
    emergency_escalation_threshold: float
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    last_triggered: datetime | None

    class Config:
        from_attributes = True


class AlertRuleCreate(BaseModel):
    """Request model for creating alert rules."""

    configuration_id: int
    name: str = Field(..., description="Rule name")
    description: str | None = None
    conditions: dict = Field(..., description="Rule conditions as JSON")
    rule_type: str = Field("threshold", description="Rule type")
    evaluation_frequency_minutes: int = Field(60, ge=1, le=1440)
    min_data_points_required: int = Field(1, ge=1)
    lookback_period_hours: int = Field(24, ge=1, le=168)
    cooldown_period_hours: int = Field(24, ge=1, le=168)
    max_alerts_per_day: int = Field(5, ge=1, le=100)
    priority: str = Field("medium", description="Alert priority")
    category: str = Field("outbreak_risk", description="Alert category")
    is_active: bool = True


class AlertRuleResponse(BaseModel):
    """Response model for alert rules."""

    id: int
    configuration_id: int
    rule_name: str
    rule_description: str | None
    conditions: dict
    rule_type: str
    rule_version: str
    evaluation_frequency_minutes: int
    min_data_points_required: int
    lookback_period_hours: int
    cooldown_period_hours: int
    max_alerts_per_day: int
    alert_priority: str
    alert_category: str
    is_active: bool
    last_evaluation: datetime | None
    evaluation_count: int
    triggered_count: int
    false_positive_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Response model for alerts."""

    id: int
    alert_rule_id: int | None
    configuration_id: int
    alert_type: str
    alert_level: str
    alert_title: str
    alert_message: str
    alert_summary: str | None
    latitude: float | None
    longitude: float | None
    location_name: str | None
    country_code: str | None
    admin_region: str | None
    risk_score: float | None
    confidence_score: float | None
    prediction_date: datetime | None
    time_horizon_days: int | None
    alert_data: dict | None
    environmental_data: dict | None
    status: str
    priority: str
    push_notification_sent: bool
    push_notification_delivered: bool
    email_notification_sent: bool
    email_notification_delivered: bool
    sms_notification_sent: bool
    sms_notification_delivered: bool
    webhook_notification_sent: bool
    webhook_notification_delivered: bool
    viewed_at: datetime | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    dismissed_at: datetime | None
    acknowledged_by: str | None
    resolution_notes: str | None
    is_emergency: bool
    escalated_at: datetime | None
    escalation_level: int
    response_time_seconds: int | None
    feedback_rating: int | None
    feedback_comments: str | None
    false_positive: bool | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None

    class Config:
        from_attributes = True


class DeviceTokenRegistration(BaseModel):
    """Request model for device token registration."""

    device_token: str = Field(..., description="FCM device token")
    device_type: str = Field(..., description="Device type (ios, android, web)")
    device_id: str | None = None
    device_name: str | None = None
    platform_version: str | None = None
    app_version: str | None = None


class AlertStatsResponse(BaseModel):
    """Response model for alert statistics."""

    alert_engine_stats: dict
    websocket_stats: dict
    notification_stats: dict
    firebase_stats: dict


# Alert Configuration Endpoints
@router.post("/configurations", response_model=AlertConfigurationResponse)
async def create_alert_configuration(
    config_data: AlertConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Create a new alert configuration."""
    try:
        from ...alerts.alert_engine import alert_engine

        config = await alert_engine.create_alert_configuration(
            user_id=current_user.id,
            config_data=config_data.dict()
        )

        if not config:
            raise HTTPException(status_code=400, detail="Failed to create alert configuration")

        return AlertConfigurationResponse.from_orm(config)

    except Exception as e:
        logger.error(f"Failed to create alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/configurations", response_model=list[AlertConfigurationResponse])
async def get_alert_configurations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    active_only: bool = Query(True, description="Return only active configurations")
):
    """Get user's alert configurations."""
    try:
        query = db.query(AlertConfiguration).filter(
            AlertConfiguration.user_id == current_user.id
        )

        if active_only:
            query = query.filter(AlertConfiguration.is_active)

        configurations = query.order_by(desc(AlertConfiguration.created_at)).all()

        return [AlertConfigurationResponse.from_orm(config) for config in configurations]

    except Exception as e:
        logger.error(f"Failed to get alert configurations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/configurations/{config_id}", response_model=AlertConfigurationResponse)
async def get_alert_configuration(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Get a specific alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(
            AlertConfiguration.id == config_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        return AlertConfigurationResponse.from_orm(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.put("/configurations/{config_id}", response_model=AlertConfigurationResponse)
async def update_alert_configuration(
    config_id: int,
    config_data: AlertConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Update an alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(
            AlertConfiguration.id == config_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        # Update configuration fields
        for field, value in config_data.dict(exclude_unset=True).items():
            setattr(config, field, value)

        config.updated_at = datetime.now()

        db.commit()
        db.refresh(config)

        return AlertConfigurationResponse.from_orm(config)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.delete("/configurations/{config_id}")
async def delete_alert_configuration(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Delete an alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(
            AlertConfiguration.id == config_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        # Deactivate instead of deleting to preserve history
        config.is_active = False
        config.updated_at = datetime.now()

        db.commit()

        return {"message": "Alert configuration deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


# Alert Rule Endpoints
@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Create a new alert rule."""
    try:
        # Verify user owns the configuration
        config = db.query(AlertConfiguration).filter(
            AlertConfiguration.id == rule_data.configuration_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        from ...alerts.alert_engine import alert_engine

        rule_dict = rule_data.dict()
        rule_dict["created_by"] = current_user.id

        rule = await alert_engine.create_alert_rule(
            configuration_id=rule_data.configuration_id,
            rule_data=rule_dict
        )

        if not rule:
            raise HTTPException(status_code=400, detail="Failed to create alert rule")

        return AlertRuleResponse.from_orm(rule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/rules", response_model=list[AlertRuleResponse])
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    configuration_id: int | None = Query(None, description="Filter by configuration ID"),
    active_only: bool = Query(True, description="Return only active rules")
):
    """Get user's alert rules."""
    try:
        query = db.query(AlertRule).join(AlertConfiguration).filter(
            AlertConfiguration.user_id == current_user.id
        )

        if configuration_id:
            query = query.filter(AlertRule.configuration_id == configuration_id)

        if active_only:
            query = query.filter(AlertRule.is_active)

        rules = query.order_by(desc(AlertRule.created_at)).all()

        return [AlertRuleResponse.from_orm(rule) for rule in rules]

    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Alert History Endpoints
@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    alert_level: str | None = Query(None, description="Filter by alert level"),
    alert_type: str | None = Query(None, description="Filter by alert type"),
    status: str | None = Query(None, description="Filter by status"),
    location: str | None = Query(None, description="Filter by location name"),
    start_date: datetime | None = Query(None, description="Filter alerts after this date"),
    end_date: datetime | None = Query(None, description="Filter alerts before this date"),
    unread_only: bool = Query(False, description="Return only unread alerts")
):
    """Get user's alert history."""
    try:
        query = db.query(Alert).join(AlertConfiguration).filter(
            AlertConfiguration.user_id == current_user.id
        )

        # Apply filters
        if alert_level:
            query = query.filter(Alert.alert_level == alert_level)

        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)

        if status:
            query = query.filter(Alert.status == status)

        if location:
            query = query.filter(
                or_(
                    Alert.location_name.ilike(f"%{location}%"),
                    Alert.admin_region.ilike(f"%{location}%")
                )
            )

        if start_date:
            query = query.filter(Alert.created_at >= start_date)

        if end_date:
            query = query.filter(Alert.created_at <= end_date)

        if unread_only:
            query = query.filter(Alert.viewed_at.is_(None))

        # Order by creation time (newest first)
        query = query.order_by(desc(Alert.created_at))

        # Apply pagination
        alerts = query.offset(offset).limit(limit).all()

        return [AlertResponse.from_orm(alert) for alert in alerts]

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Get a specific alert."""
    try:
        alert = db.query(Alert).join(AlertConfiguration).filter(
            Alert.id == alert_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Mark as viewed if not already
        if not alert.viewed_at:
            alert.viewed_at = datetime.now()
            db.commit()

        return AlertResponse.from_orm(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    notes: str | None = None
):
    """Acknowledge an alert."""
    try:
        alert = db.query(Alert).join(AlertConfiguration).filter(
            Alert.id == alert_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert.acknowledged_at:
            raise HTTPException(status_code=400, detail="Alert already acknowledged")

        # Update alert
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = current_user.id
        alert.status = "acknowledged"

        if notes:
            alert.resolution_notes = notes

        # Calculate response time
        if alert.created_at:
            response_time = (datetime.now() - alert.created_at).total_seconds()
            alert.response_time_seconds = int(response_time)

        db.commit()

        return {"message": "Alert acknowledged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    notes: str | None = None
):
    """Resolve an alert."""
    try:
        alert = db.query(Alert).join(AlertConfiguration).filter(
            Alert.id == alert_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert.resolved_at:
            raise HTTPException(status_code=400, detail="Alert already resolved")

        # Update alert
        alert.resolved_at = datetime.now()
        alert.status = "resolved"

        if notes:
            alert.resolution_notes = notes

        # Auto-acknowledge if not already
        if not alert.acknowledged_at:
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = current_user.id

        db.commit()

        return {"message": "Alert resolved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{alert_id}/feedback")
async def submit_alert_feedback(
    alert_id: int,
    rating: int = Query(..., ge=1, le=5, description="Feedback rating (1-5)"),
    comments: str | None = None,
    false_positive: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Submit feedback for an alert."""
    try:
        alert = db.query(Alert).join(AlertConfiguration).filter(
            Alert.id == alert_id,
            AlertConfiguration.user_id == current_user.id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Update feedback
        alert.feedback_rating = rating
        alert.feedback_comments = comments
        alert.false_positive = false_positive

        # Update rule statistics if marked as false positive
        if false_positive and alert.alert_rule_id:
            rule = db.query(AlertRule).filter(AlertRule.id == alert.alert_rule_id).first()
            if rule:
                rule.false_positive_count += 1

        db.commit()

        return {"message": "Feedback submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit alert feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Device Token Management
@router.post("/device-tokens")
async def register_device_token(
    token_data: DeviceTokenRegistration,
    current_user: User = Depends(get_current_user)
):
    """Register a device token for push notifications."""
    try:
        from ...alerts.firebase_service import firebase_service

        device_info = {
            "device_id": token_data.device_id,
            "device_name": token_data.device_name,
            "platform_version": token_data.platform_version,
            "app_version": token_data.app_version
        }

        success = await firebase_service.register_device_token(
            user_id=current_user.id,
            device_token=token_data.device_token,
            device_type=token_data.device_type,
            device_info=device_info
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to register device token")

        return {"message": "Device token registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register device token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/device-tokens")
async def get_device_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Get user's registered device tokens."""
    try:
        tokens = db.query(UserDeviceToken).filter(
            UserDeviceToken.user_id == current_user.id,
            UserDeviceToken.is_active
        ).all()

        return [
            {
                "id": token.id,
                "device_type": token.device_type,
                "device_name": token.device_name,
                "is_valid": token.is_valid,
                "registered_at": token.registered_at,
                "last_notification_sent": token.last_notification_sent
            }
            for token in tokens
        ]

    except Exception as e:
        logger.error(f"Failed to get device tokens: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/device-tokens/{token_id}")
async def deactivate_device_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Deactivate a device token."""
    try:
        token = db.query(UserDeviceToken).filter(
            UserDeviceToken.id == token_id,
            UserDeviceToken.user_id == current_user.id
        ).first()

        if not token:
            raise HTTPException(status_code=404, detail="Device token not found")

        token.is_active = False
        token.deactivated_at = datetime.now()

        db.commit()

        return {"message": "Device token deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate device token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket Connection
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for real-time alerts."""
    try:
        from ...alerts.websocket_manager import websocket_manager

        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=current_user.id
        )

        try:
            while True:
                # Wait for client messages
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client messages
                if message.get("type") == "subscribe":
                    group_name = message.get("group")
                    if group_name:
                        await websocket_manager.subscribe(connection_id, group_name)

                elif message.get("type") == "unsubscribe":
                    group_name = message.get("group")
                    if group_name:
                        await websocket_manager.unsubscribe(connection_id, group_name)

                elif message.get("type") == "pong":
                    # Update last ping time
                    pass

        except WebSocketDisconnect:
            await websocket_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# Statistics and Monitoring
@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    current_user: User = Depends(get_current_user)
):
    """Get alert system statistics."""
    try:
        from ...alerts.alert_engine import alert_engine
        from ...alerts.firebase_service import firebase_service
        from ...alerts.notification_service import notification_service
        from ...alerts.websocket_manager import websocket_manager

        return AlertStatsResponse(
            alert_engine_stats=alert_engine.get_stats(),
            websocket_stats=websocket_manager.get_stats(),
            notification_stats=notification_service.get_stats(),
            firebase_stats=firebase_service.get_stats()
        )

    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/performance/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    period: str = Query("daily", description="Aggregation period (hourly, daily, weekly, monthly)"),
    days: int = Query(7, ge=1, le=90, description="Number of days to include")
):
    """Get alert system performance metrics."""
    try:
        start_date = datetime.now() - timedelta(days=days)

        metrics = db.query(AlertPerformanceMetrics).filter(
            AlertPerformanceMetrics.aggregation_period == period,
            AlertPerformanceMetrics.metric_date >= start_date
        ).order_by(AlertPerformanceMetrics.metric_date).all()

        return [
            {
                "metric_date": metric.metric_date,
                "alerts_generated": metric.alerts_generated,
                "alerts_by_level": metric.alerts_by_level,
                "delivery_rate_percentage": metric.delivery_rate_percentage,
                "engagement_rate_percentage": metric.engagement_rate_percentage,
                "false_positive_rate": metric.false_positive_rate,
                "avg_response_time_seconds": metric.avg_response_time_seconds
            }
            for metric in metrics
        ]

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
