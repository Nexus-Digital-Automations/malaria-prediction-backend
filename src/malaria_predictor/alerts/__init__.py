"""Alert and notification system for malaria prediction.

This module provides comprehensive alert and notification capabilities including:
- Real-time WebSocket alerts
- Push notifications via Firebase Cloud Messaging
- Multi-channel notification delivery (email, SMS, webhooks)
- Customizable alert thresholds and rules
- Alert history and performance tracking
- Emergency response protocol integration

Key Components:
- WebSocket manager for real-time alerts
- Notification delivery system
- Alert rule engine
- Template management
- Performance monitoring
"""

from .alert_engine import AlertEngine
from .firebase_service import FirebaseNotificationService
from .notification_service import NotificationService
from .websocket_manager import WebSocketAlertManager

__all__ = [
    "WebSocketAlertManager",
    "NotificationService",
    "AlertEngine",
    "FirebaseNotificationService",
]
