"""
Database models for the Firebase Cloud Messaging and notification system.

This module defines SQLAlchemy models for tracking device tokens, notification logs,
templates, and topic subscriptions.
"""

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.models import Base


class NotificationPriority(str, Enum):
    """Notification priority levels for delivery optimization."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status tracking."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELED = "canceled"


class DevicePlatform(str, Enum):
    """Supported device platforms for cross-platform notifications."""

    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class DeviceToken(Base):
    """
    Model for storing Firebase Cloud Messaging device tokens.

    Manages device registration, token validation, and platform-specific configurations.
    """

    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(1024), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Optional user association
    platform = Column(String(20), nullable=False, index=True)  # android, ios, web
    app_version = Column(String(50), nullable=True)
    device_info = Column(JSON, nullable=True)  # Device metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscriptions = relationship(
        "TopicSubscription",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    notification_logs = relationship(
        "NotificationLog",
        back_populates="device",
        cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index('idx_device_tokens_user_platform', 'user_id', 'platform'),
        Index('idx_device_tokens_active_updated', 'is_active', 'updated_at'),
    )

    def __repr__(self) -> str:
        """String representation of device token."""
        return f"<DeviceToken(id={self.id}, platform={self.platform}, user_id={self.user_id})>"


class TopicSubscription(Base):
    """
    Model for managing topic-based messaging subscriptions.

    Enables group messaging and targeted notifications based on topics.
    """

    __tablename__ = "topic_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("device_tokens.id"), nullable=False)
    topic = Column(String(255), nullable=False, index=True)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    device = relationship("DeviceToken", back_populates="subscriptions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_topic_subscriptions_device_topic', 'device_id', 'topic'),
        Index('idx_topic_subscriptions_topic_active', 'topic', 'is_active'),
    )

    def __repr__(self) -> str:
        """String representation of topic subscription."""
        return f"<TopicSubscription(device_id={self.device_id}, topic={self.topic})>"


class NotificationTemplate(Base):
    """
    Model for storing reusable notification templates.

    Supports customizable notification templates with dynamic content.
    """

    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # e.g., alert, reminder, info
    priority = Column(String(20), default=NotificationPriority.NORMAL, nullable=False)

    # Platform-specific configurations
    android_config = Column(JSON, nullable=True)  # Android-specific settings
    ios_config = Column(JSON, nullable=True)      # iOS-specific settings
    web_config = Column(JSON, nullable=True)      # Web-specific settings

    # Rich media support
    image_url = Column(String(1024), nullable=True)
    action_buttons = Column(JSON, nullable=True)  # Action button configurations
    deep_link = Column(String(1024), nullable=True)  # Deep link for app navigation

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    notification_logs = relationship(
        "NotificationLog",
        back_populates="template",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of notification template."""
        return f"<NotificationTemplate(id={self.id}, name={self.name}, category={self.category})>"


class NotificationLog(Base):
    """
    Model for tracking notification delivery and analytics.

    Provides comprehensive logging of all notification attempts and outcomes.
    """

    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Notification details
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("device_tokens.id"), nullable=True)
    topic = Column(String(255), nullable=True, index=True)  # For topic-based notifications

    # Message content
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data_payload = Column(JSON, nullable=True)  # Additional data payload

    # Delivery tracking
    status = Column(String(20), default=NotificationStatus.PENDING, nullable=False, index=True)
    priority = Column(String(20), default=NotificationPriority.NORMAL, nullable=False, index=True)
    fcm_message_id = Column(String(255), nullable=True, index=True)  # FCM message ID for tracking

    # Timing information
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # For scheduled notifications
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Analytics data
    clicked = Column(Boolean, default=False, nullable=False)
    clicked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    template = relationship("NotificationTemplate", back_populates="notification_logs")
    device = relationship("DeviceToken", back_populates="notification_logs")

    # Indexes for performance and analytics
    __table_args__ = (
        Index('idx_notification_logs_status_created', 'status', 'created_at'),
        Index('idx_notification_logs_priority_scheduled', 'priority', 'scheduled_at'),
        Index('idx_notification_logs_topic_sent', 'topic', 'sent_at'),
        Index('idx_notification_logs_device_status', 'device_id', 'status'),
        Index('idx_notification_logs_analytics', 'clicked', 'delivered_at'),
    )

    def __repr__(self) -> str:
        """String representation of notification log."""
        return f"<NotificationLog(id={self.id}, status={self.status}, priority={self.priority})>"


class NotificationSchedule(Base):
    """
    Model for managing scheduled notifications and recurring alerts.

    Supports one-time and recurring notification scheduling.
    """

    __tablename__ = "notification_schedules"

    id = Column(Integer, primary_key=True, index=True)

    # Schedule configuration
    name = Column(String(255), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=False)

    # Targeting
    target_type = Column(String(20), nullable=False)  # "device", "topic", "user"
    target_value = Column(String(255), nullable=False)  # Device ID, topic name, or user ID

    # Scheduling
    trigger_type = Column(String(20), nullable=False)  # "once", "recurring", "condition"
    trigger_config = Column(JSON, nullable=False)  # Configuration for trigger
    next_execution = Column(DateTime(timezone=True), nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    execution_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("NotificationTemplate")

    # Indexes for scheduling efficiency
    __table_args__ = (
        Index('idx_notification_schedules_active_next', 'is_active', 'next_execution'),
        Index('idx_notification_schedules_target', 'target_type', 'target_value'),
    )

    def __repr__(self) -> str:
        """String representation of notification schedule."""
        return f"<NotificationSchedule(id={self.id}, name={self.name}, trigger_type={self.trigger_type})>"
