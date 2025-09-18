"""WebSocket manager for real-time alert delivery.

Manages WebSocket connections for real-time alert notifications,
including connection lifecycle, message broadcasting, and user-specific filtering.
"""

import asyncio
import json
import logging
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..database.models import Alert

logger = logging.getLogger(__name__)


class WebSocketConnection(BaseModel):
    """Represents an active WebSocket connection."""

    websocket: WebSocket
    user_id: str
    connection_id: str = Field(default_factory=lambda: str(uuid4()))
    connected_at: datetime = Field(default_factory=datetime.now)
    last_ping: datetime = Field(default_factory=datetime.now)
    subscriptions: set[str] = Field(default_factory=set)
    location_filter: dict[str, float] | None = None
    risk_threshold: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class AlertMessage(BaseModel):
    """Real-time alert message structure."""

    type: str = "alert"
    alert_id: int
    alert_level: str
    alert_type: str
    title: str
    message: str
    location: dict[str, float] | None = None
    risk_score: float | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict | None = None


class WebSocketAlertManager:
    """Manages WebSocket connections and real-time alert broadcasting.

    Provides functionality for:
    - Connection management and authentication
    - Real-time alert broadcasting
    - User-specific filtering and subscriptions
    - Connection health monitoring
    - Performance tracking
    """

    def __init__(self):
        """Initialize the WebSocket alert manager."""
        self.connections: dict[str, WebSocketConnection] = {}
        self.user_connections: dict[str, set[str]] = {}
        self.subscription_groups: dict[str, set[str]] = {}
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0,
            "last_cleanup": datetime.now()
        }

        # Start background tasks
        self._cleanup_task = None
        self._heartbeat_task = None

    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_connections())
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    async def stop_background_tasks(self):
        """Stop background maintenance tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        location_filter: dict[str, float] | None = None,
        risk_threshold: float = 0.0
    ) -> str:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user identifier
            location_filter: Geographic filter for alerts (lat, lng, radius)
            risk_threshold: Minimum risk score for alerts

        Returns:
            Connection ID for the established connection

        Raises:
            Exception: If connection setup fails
        """
        try:
            await websocket.accept()

            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                location_filter=location_filter,
                risk_threshold=risk_threshold
            )

            # Register connection
            self.connections[connection.connection_id] = connection

            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection.connection_id)

            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)

            logger.info(
                f"WebSocket connected: user={user_id}, "
                f"connection={connection.connection_id}, "
                f"active={self.stats['active_connections']}"
            )

            # Send welcome message
            await self._send_to_connection(
                connection.connection_id,
                {
                    "type": "connection_established",
                    "connection_id": connection.connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "WebSocket connection established successfully"
                }
            )

            return connection.connection_id

        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            raise

    async def disconnect(self, connection_id: str) -> None:
        """Disconnect and clean up a WebSocket connection.

        Args:
            connection_id: ID of connection to disconnect
        """
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]

        try:
            # Remove from tracking
            self.connections.pop(connection_id, None)

            # Update user connections
            if connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    self.user_connections.pop(connection.user_id, None)

            # Remove from subscription groups
            for group_name in connection.subscriptions:
                if group_name in self.subscription_groups:
                    self.subscription_groups[group_name].discard(connection_id)
                    if not self.subscription_groups[group_name]:
                        self.subscription_groups.pop(group_name, None)

            # Update statistics
            self.stats["active_connections"] = len(self.connections)

            logger.info(
                f"WebSocket disconnected: user={connection.user_id}, "
                f"connection={connection_id}, "
                f"active={self.stats['active_connections']}"
            )

        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    async def subscribe(self, connection_id: str, group_name: str) -> bool:
        """Subscribe a connection to an alert group.

        Args:
            connection_id: Connection to subscribe
            group_name: Alert group name (e.g., 'high_risk', 'emergency')

        Returns:
            True if subscription successful, False otherwise
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.subscriptions.add(group_name)

        if group_name not in self.subscription_groups:
            self.subscription_groups[group_name] = set()
        self.subscription_groups[group_name].add(connection_id)

        logger.info(f"Subscribed {connection_id} to group '{group_name}'")
        return True

    async def unsubscribe(self, connection_id: str, group_name: str) -> bool:
        """Unsubscribe a connection from an alert group.

        Args:
            connection_id: Connection to unsubscribe
            group_name: Alert group name

        Returns:
            True if unsubscription successful, False otherwise
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.subscriptions.discard(group_name)

        if group_name in self.subscription_groups:
            self.subscription_groups[group_name].discard(connection_id)
            if not self.subscription_groups[group_name]:
                self.subscription_groups.pop(group_name, None)

        logger.info(f"Unsubscribed {connection_id} from group '{group_name}'")
        return True

    async def broadcast_alert(self, alert: Alert) -> int:
        """Broadcast an alert to all relevant WebSocket connections.

        Args:
            alert: Alert instance to broadcast

        Returns:
            Number of connections that received the alert
        """
        if not self.connections:
            return 0

        alert_message = AlertMessage(
            alert_id=alert.id,
            alert_level=alert.alert_level,
            alert_type=alert.alert_type,
            title=alert.alert_title,
            message=alert.alert_message,
            location={
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "name": alert.location_name
            } if alert.latitude and alert.longitude else None,
            risk_score=alert.risk_score,
            metadata={
                "priority": alert.priority,
                "country_code": alert.country_code,
                "admin_region": alert.admin_region,
                "prediction_date": alert.prediction_date.isoformat() if alert.prediction_date else None,
                "confidence_score": alert.confidence_score
            }
        )

        delivered_count = 0

        # Filter connections based on alert criteria
        target_connections = self._filter_connections_for_alert(alert)

        # Send to filtered connections
        for connection_id in target_connections:
            if await self._send_to_connection(connection_id, alert_message.dict()):
                delivered_count += 1

        logger.info(
            f"Broadcasted alert {alert.id} to {delivered_count} WebSocket connections"
        )

        return delivered_count

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """Send a message to all connections for a specific user.

        Args:
            user_id: Target user ID
            message: Message to send

        Returns:
            Number of connections that received the message
        """
        if user_id not in self.user_connections:
            return 0

        delivered_count = 0
        connection_ids = list(self.user_connections[user_id])

        for connection_id in connection_ids:
            if await self._send_to_connection(connection_id, message):
                delivered_count += 1

        return delivered_count

    async def send_to_group(self, group_name: str, message: dict) -> int:
        """Send a message to all connections in a subscription group.

        Args:
            group_name: Target subscription group
            message: Message to send

        Returns:
            Number of connections that received the message
        """
        if group_name not in self.subscription_groups:
            return 0

        delivered_count = 0
        connection_ids = list(self.subscription_groups[group_name])

        for connection_id in connection_ids:
            if await self._send_to_connection(connection_id, message):
                delivered_count += 1

        return delivered_count

    def get_stats(self) -> dict:
        """Get WebSocket manager statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "subscription_groups": len(self.subscription_groups),
            "connections_by_user": {
                user_id: len(connections)
                for user_id, connections in self.user_connections.items()
            }
        }

    def get_user_connections(self, user_id: str) -> list[str]:
        """Get all connection IDs for a user.

        Args:
            user_id: User to get connections for

        Returns:
            List of connection IDs
        """
        return list(self.user_connections.get(user_id, set()))

    async def _send_to_connection(self, connection_id: str, message: dict) -> bool:
        """Send a message to a specific connection.

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        try:
            await connection.websocket.send_text(json.dumps(message, default=str))
            self.stats["messages_sent"] += 1
            return True

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected during send: {connection_id}")
            await self.disconnect(connection_id)
            return False

        except Exception as e:
            logger.error(f"Error sending WebSocket message to {connection_id}: {e}")
            self.stats["errors"] += 1
            await self.disconnect(connection_id)
            return False

    def _filter_connections_for_alert(self, alert: Alert) -> list[str]:
        """Filter connections that should receive an alert.

        Args:
            alert: Alert to filter for

        Returns:
            List of connection IDs that should receive the alert
        """
        target_connections = []

        for connection_id, connection in self.connections.items():
            # Check risk threshold
            if alert.risk_score and alert.risk_score < connection.risk_threshold:
                continue

            # Check location filter
            if (connection.location_filter and
                alert.latitude and alert.longitude):

                # Simple distance check (can be improved with proper geospatial functions)
                lat_diff = abs(alert.latitude - connection.location_filter.get("latitude", 0))
                lng_diff = abs(alert.longitude - connection.location_filter.get("longitude", 0))
                radius = connection.location_filter.get("radius", 1.0)

                if lat_diff > radius or lng_diff > radius:
                    continue

            # Check subscription groups
            alert_group = f"{alert.alert_level}_risk"
            if (connection.subscriptions and
                alert_group not in connection.subscriptions):
                continue

            target_connections.append(connection_id)

        return target_connections

    async def _cleanup_connections(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.now()
                stale_connections = []

                for connection_id, connection in self.connections.items():
                    # Mark connections as stale if no ping in 10 minutes
                    time_since_ping = (current_time - connection.last_ping).total_seconds()
                    if time_since_ping > 600:
                        stale_connections.append(connection_id)

                # Clean up stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)

                self.stats["last_cleanup"] = current_time

                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")

            except asyncio.CancelledError:
                logger.info("WebSocket cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket cleanup task: {e}")

    async def _heartbeat_monitor(self):
        """Background task to monitor connection health."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Send ping to all connections
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }

                failed_connections = []

                for connection_id, connection in self.connections.items():
                    try:
                        await connection.websocket.send_text(json.dumps(ping_message))
                        connection.last_ping = datetime.now()
                    except Exception:
                        failed_connections.append(connection_id)

                # Clean up failed connections
                for connection_id in failed_connections:
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                logger.info("WebSocket heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket heartbeat task: {e}")


# Global WebSocket manager instance
websocket_manager = WebSocketAlertManager()
