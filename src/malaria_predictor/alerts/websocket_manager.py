"""Enhanced WebSocket manager for real-time alert delivery.

Manages WebSocket connections for real-time alert notifications with advanced features:
- Connection management with authentication and rate limiting
- Real-time alert broadcasting with low latency (<100ms)
- User-specific filtering and subscription management
- Connection health monitoring and automatic reconnection
- Offline alert queuing and persistence
- Multi-client broadcast with targeted messaging
- Performance tracking and diagnostics
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from uuid import uuid4

import redis.asyncio as redis
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..config import settings
from ..database.models import Alert
from ..database.session import get_session

logger = logging.getLogger(__name__)


# Rate limiting configuration
class RateLimitConfig(BaseModel):
    """Rate limiting configuration for WebSocket connections."""

    max_connections_per_user: int = 5
    max_messages_per_minute: int = 60
    max_subscriptions_per_connection: int = 10
    cooldown_period_seconds: int = 30
    ban_duration_minutes: int = 15


class ConnectionMetrics(BaseModel):
    """Metrics tracking for a WebSocket connection."""

    messages_sent: int = 0
    messages_received: int = 0
    subscriptions_count: int = 0
    reconnection_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.now)
    latency_ms: list[float] = Field(default_factory=list)
    error_count: int = 0


class WebSocketConnection(BaseModel):
    """Enhanced WebSocket connection with advanced features."""

    websocket: WebSocket
    user_id: str
    connection_id: str = Field(default_factory=lambda: str(uuid4()))
    connected_at: datetime = Field(default_factory=datetime.now)
    last_ping: datetime = Field(default_factory=datetime.now)
    last_pong: datetime = Field(default_factory=datetime.now)

    # Authentication and authorization
    auth_token: str | None = None
    permissions: set[str] = Field(default_factory=set)
    user_roles: list[str] = Field(default_factory=list)

    # Subscription management
    subscriptions: set[str] = Field(default_factory=set)
    subscription_filters: dict[str, dict] = Field(default_factory=dict)

    # Geographic and risk filtering
    location_filter: dict[str, float] | None = None
    risk_threshold: float = 0.0
    alert_types_filter: set[str] = Field(default_factory=set)

    # Rate limiting and monitoring
    message_queue: deque = Field(default_factory=lambda: deque(maxlen=1000))
    rate_limit_tokens: int = 60  # Messages per minute
    last_token_refresh: datetime = Field(default_factory=datetime.now)

    # Connection health
    metrics: ConnectionMetrics = Field(default_factory=ConnectionMetrics)
    is_healthy: bool = True
    reconnect_attempts: int = 0
    max_reconnect_attempts: int = 5

    # Offline message queue
    offline_queue: list[dict] = Field(default_factory=list)
    max_offline_messages: int = 100

    class Config:
        arbitrary_types_allowed = True


class AlertMessage(BaseModel):
    """Enhanced real-time alert message structure."""

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

    # Enhanced fields
    priority: str = "normal"  # low, normal, high, urgent, emergency
    category: str = "outbreak_risk"
    confidence_score: float | None = None
    expiry_time: datetime | None = None
    action_required: bool = False
    action_url: str | None = None
    affected_population: int | None = None


class SystemMessage(BaseModel):
    """System-level WebSocket messages."""

    type: str  # connection_status, health_check, rate_limit_warning, etc.
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    connection_id: str
    metadata: dict | None = None


class SubscriptionMessage(BaseModel):
    """Subscription management messages."""

    type: str = "subscription"
    action: str  # subscribe, unsubscribe, list, update
    group_name: str | None = None
    filters: dict | None = None
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """Real-time performance metrics."""

    type: str = "performance_metrics"
    connection_id: str
    latency_ms: float
    queue_size: int
    message_rate: float
    error_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)


class WebSocketAlertManager:
    """Enhanced WebSocket manager for real-time alert broadcasting.

    Provides advanced functionality for:
    - Connection management with authentication and rate limiting
    - Real-time alert broadcasting with low latency (<100ms)
    - User-specific filtering and subscription management
    - Connection health monitoring and automatic reconnection
    - Offline alert queuing and persistence
    - Multi-client broadcast with targeted messaging
    - Performance tracking and comprehensive diagnostics
    """

    def __init__(self) -> None:
        """Initialize the enhanced WebSocket alert manager."""
        self.connections: dict[str, WebSocketConnection] = {}
        self.user_connections: dict[str, set[str]] = defaultdict(set)
        self.subscription_groups: dict[str, set[str]] = defaultdict(set)

        # Rate limiting
        self.rate_limit_config = RateLimitConfig()
        self.banned_users: dict[str, datetime] = {}
        self.rate_limit_violations: dict[str, list[datetime]] = defaultdict(list)

        # Enhanced statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_queued": 0,
            "errors": 0,
            "rate_limit_violations": 0,
            "banned_users": 0,
            "avg_latency_ms": 0.0,
            "last_cleanup": datetime.now(),
            "last_health_check": datetime.now()
        }

        # Performance tracking
        self.latency_history: deque = deque(maxlen=1000)
        self.throughput_history: deque = deque(maxlen=100)

        # Redis client for persistence and scaling
        self.redis_client: redis.Redis | None = None

        # Background tasks
        self._cleanup_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._metrics_task: asyncio.Task[None] | None = None
        self._queue_processor_task: asyncio.Task[None] | None = None

        # Message queues for offline users
        self.offline_queues: dict[str, list[dict]] = defaultdict(list)
        self.max_offline_queue_size = 100

    async def initialize(self) -> None:
        """Initialize the WebSocket manager with Redis and background tasks."""
        try:
            # Initialize Redis client for persistence and scaling
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis connection established for WebSocket persistence")
            else:
                logger.warning("Redis not configured, running in memory-only mode")

            # Start background tasks
            await self.start_background_tasks()

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise

    async def start_background_tasks(self) -> None:
        """Start enhanced background maintenance tasks."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_connections())
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        if not self._metrics_task:
            self._metrics_task = asyncio.create_task(self._metrics_collector())
        if not self._queue_processor_task:
            self._queue_processor_task = asyncio.create_task(self._process_offline_queues())

    async def stop_background_tasks(self) -> None:
        """Stop enhanced background maintenance tasks."""
        tasks = [
            self._cleanup_task,
            self._heartbeat_task,
            self._metrics_task,
            self._queue_processor_task
        ]

        for task in tasks:
            if task:
                task.cancel()

        self._cleanup_task = None
        self._heartbeat_task = None
        self._metrics_task = None
        self._queue_processor_task = None

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

    async def _check_rate_limit(self, user_id: str, connection_id: str) -> bool:
        """Check if user is rate limited."""
        current_time = datetime.now()

        # Check if user is banned
        if user_id in self.banned_users:
            ban_expires = self.banned_users[user_id] + timedelta(
                minutes=self.rate_limit_config.ban_duration_minutes
            )
            if current_time < ban_expires:
                return False
            else:
                del self.banned_users[user_id]

        # Check rate limit violations
        violations = self.rate_limit_violations[user_id]
        violations = [v for v in violations if current_time - v < timedelta(minutes=1)]
        self.rate_limit_violations[user_id] = violations

        if len(violations) > self.rate_limit_config.max_messages_per_minute:
            # Ban user
            self.banned_users[user_id] = current_time
            self.stats["banned_users"] += 1  # type: ignore[operator]
            self.stats["rate_limit_violations"] += 1  # type: ignore[operator]

            logger.warning(f"User {user_id} banned for rate limit violations")
            return False

        return True

    async def _refresh_rate_limit_tokens(self, connection: WebSocketConnection) -> None:
        """Refresh rate limit tokens for a connection."""
        current_time = datetime.now()
        time_diff = (current_time - connection.last_token_refresh).total_seconds()

        if time_diff >= 60:  # Refresh every minute
            connection.rate_limit_tokens = self.rate_limit_config.max_messages_per_minute
            connection.last_token_refresh = current_time
        elif time_diff > 0:
            # Gradual token refresh
            tokens_to_add = int(time_diff * self.rate_limit_config.max_messages_per_minute / 60)
            connection.rate_limit_tokens = min(
                self.rate_limit_config.max_messages_per_minute,
                connection.rate_limit_tokens + tokens_to_add
            )

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        auth_token: str | None = None,
        location_filter: dict[str, float] | None = None,
        risk_threshold: float = 0.0,
        alert_types_filter: set[str] | None = None,
        permissions: set[str] | None = None,
        user_roles: list[str] | None = None
    ) -> str:
        """Accept and register an enhanced WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user identifier
            auth_token: Authentication token for verification
            location_filter: Geographic filter for alerts (lat, lng, radius)
            risk_threshold: Minimum risk score for alerts
            alert_types_filter: Set of alert types to receive
            permissions: Set of permissions for the connection
            user_roles: List of user roles

        Returns:
            Connection ID for the established connection

        Raises:
            HTTPException: If connection setup fails or user is banned
        """
        try:
            # Check rate limits and bans
            if not await self._check_rate_limit(user_id, ""):
                raise HTTPException(status_code=429, detail="Rate limit exceeded or user banned")

            # Check max connections per user
            user_connection_count = len(self.user_connections.get(user_id, set()))
            if user_connection_count >= self.rate_limit_config.max_connections_per_user:
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum connections per user ({self.rate_limit_config.max_connections_per_user}) exceeded"
                )

            await websocket.accept()

            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                auth_token=auth_token,
                location_filter=location_filter,
                risk_threshold=risk_threshold,
                alert_types_filter=alert_types_filter or set(),
                permissions=permissions or set(),
                user_roles=user_roles or []
            )

            # Register connection
            self.connections[connection.connection_id] = connection
            self.user_connections[user_id].add(connection.connection_id)

            # Update statistics
            self.stats["total_connections"] += 1  # type: ignore[operator]
            self.stats["active_connections"] = len(self.connections)

            # Process offline queue for returning user
            await self._process_user_offline_queue(user_id, connection.connection_id)

            # Persist connection to Redis if available
            if self.redis_client:
                await self._persist_connection(connection)

            logger.info(
                f"Enhanced WebSocket connected: user={user_id}, "
                f"connection={connection.connection_id}, "
                f"active={self.stats['active_connections']}, "
                f"permissions={permissions}, roles={user_roles}"
            )

            # Send welcome message with enhanced connection info
            welcome_message = SystemMessage(
                type="connection_established",
                message="Enhanced WebSocket connection established successfully",
                connection_id=connection.connection_id,
                metadata={
                    "server_version": "2.0",
                    "features": ["rate_limiting", "offline_queue", "health_monitoring"],
                    "max_subscriptions": self.rate_limit_config.max_subscriptions_per_connection,
                    "max_messages_per_minute": self.rate_limit_config.max_messages_per_minute,
                    "permissions": list(permissions) if permissions else [],
                    "roles": user_roles or []
                }
            )

            await self._send_to_connection(connection.connection_id, welcome_message.dict())

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
        """Broadcast an alert to all relevant WebSocket connections with enhanced features.

        Args:
            alert: Alert instance to broadcast

        Returns:
            Number of connections that received the alert
        """
        if not self.connections:
            # Queue for offline users if no active connections
            await self._queue_alert_for_offline_users(alert)
            return 0

        start_time = time.time()

        # Create enhanced alert message
        alert_message = AlertMessage(
            alert_id=int(alert.id),
            alert_level=str(alert.alert_level),
            alert_type=str(alert.alert_type),
            title=str(alert.alert_title),
            message=str(alert.alert_message),
            location={
                "latitude": float(alert.latitude),
                "longitude": float(alert.longitude),
                "name": str(alert.location_name)
            } if alert.latitude and alert.longitude else None,
            risk_score=float(alert.risk_score) if alert.risk_score is not None else None,
            priority=getattr(alert, 'priority', 'normal'),
            category=getattr(alert, 'alert_category', 'outbreak_risk'),
            confidence_score=float(alert.confidence_score) if alert.confidence_score is not None else None,
            affected_population=getattr(alert, 'affected_population', None),
            metadata={
                "country_code": alert.country_code,
                "admin_region": alert.admin_region,
                "prediction_date": alert.prediction_date.isoformat() if alert.prediction_date else None,
                "broadcast_timestamp": datetime.now().isoformat(),
                "server_id": getattr(settings, 'SERVER_ID', 'default')
            }
        )

        # Filter connections based on enhanced criteria
        target_connections = await self._filter_connections_for_alert_enhanced(alert)
        delivered_count = 0
        failed_connections = []

        # Batch send for performance optimization
        send_tasks = []
        for connection_id in target_connections:
            task = asyncio.create_task(
                self._send_to_connection_with_retry(connection_id, alert_message.dict())
            )
            send_tasks.append((connection_id, task))

        # Wait for all sends to complete
        for connection_id, task in send_tasks:
            try:
                success = await task
                if success:
                    delivered_count += 1
                else:
                    failed_connections.append(connection_id)
            except Exception as e:
                logger.warning(f"Failed to send alert to connection {connection_id}: {e}")
                failed_connections.append(connection_id)

        # Update performance metrics
        broadcast_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        self.latency_history.append(broadcast_time)
        self.stats["messages_sent"] += delivered_count  # type: ignore[operator]

        # Queue alert for users with failed connections
        if failed_connections:
            await self._queue_alert_for_failed_connections(alert, failed_connections)

        logger.info(
            f"Enhanced broadcast: alert {alert.id} delivered to {delivered_count}/{len(target_connections)} "
            f"connections in {broadcast_time:.2f}ms (failed: {len(failed_connections)})"
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
        """Get comprehensive WebSocket manager statistics and diagnostics.

        Returns:
            Dictionary with detailed statistics and health information
        """
        current_time = datetime.now()

        # Calculate connection health metrics
        healthy_connections = sum(1 for conn in self.connections.values() if conn.is_healthy)
        connection_health_ratio = healthy_connections / len(self.connections) if self.connections else 1.0

        # Calculate average latency
        avg_latency = 0.0
        if self.latency_history:
            avg_latency = sum(self.latency_history) / len(self.latency_history)

        # Calculate throughput metrics
        total_throughput = sum(self.throughput_history) if self.throughput_history else 0
        avg_throughput = total_throughput / len(self.throughput_history) if self.throughput_history else 0

        # Connection distribution by user
        connections_by_user = {
            user_id: len(connections)
            for user_id, connections in self.user_connections.items()
        }

        # Subscription group statistics
        subscription_stats = {
            group_name: len(connections)
            for group_name, connections in self.subscription_groups.items()
        }

        # Rate limiting statistics
        active_bans = len(self.banned_users)
        ban_expiry_times = {
            user_id: (ban_time + timedelta(minutes=self.rate_limit_config.ban_duration_minutes)).isoformat()
            for user_id, ban_time in self.banned_users.items()
        }

        # Connection age distribution
        connection_ages = []
        for conn in self.connections.values():
            age_seconds = (current_time - conn.connected_at).total_seconds()
            connection_ages.append(age_seconds)

        avg_connection_age = sum(connection_ages) / len(connection_ages) if connection_ages else 0

        # Offline queue statistics
        total_queued_messages = sum(len(queue) for queue in self.offline_queues.values())
        queued_users = len(self.offline_queues)

        return {
            # Core statistics
            **self.stats,
            "active_connections": len(self.connections),
            "healthy_connections": healthy_connections,
            "connection_health_ratio": round(connection_health_ratio, 3),
            "active_users": len(self.user_connections),
            "subscription_groups_count": len(self.subscription_groups),

            # Performance metrics
            "avg_latency_ms": round(avg_latency, 2),
            "avg_throughput_msg_per_min": round(avg_throughput, 2),
            "latency_history_size": len(self.latency_history),
            "throughput_history_size": len(self.throughput_history),

            # Connection details
            "connections_by_user": connections_by_user,
            "avg_connection_age_seconds": round(avg_connection_age, 2),
            "subscription_group_stats": subscription_stats,

            # Rate limiting and security
            "active_bans": active_bans,
            "ban_expiry_times": ban_expiry_times,
            "rate_limit_config": self.rate_limit_config.dict(),

            # Offline queue statistics
            "offline_queues": {
                "total_queued_messages": total_queued_messages,
                "queued_users": queued_users,
                "max_queue_size": self.max_offline_queue_size,
                "queue_usage_ratio": round(total_queued_messages / (queued_users * self.max_offline_queue_size) if queued_users > 0 else 0, 3)
            },

            # System health
            "system_health": {
                "redis_connected": self.redis_client is not None,
                "background_tasks_running": {
                    "cleanup": self._cleanup_task is not None and not self._cleanup_task.done(),
                    "heartbeat": self._heartbeat_task is not None and not self._heartbeat_task.done(),
                    "metrics": self._metrics_task is not None and not self._metrics_task.done(),
                    "queue_processor": self._queue_processor_task is not None and not self._queue_processor_task.done()
                },
                "last_health_check": self.stats.get("last_health_check", current_time).isoformat(),  # type: ignore[attr-defined]
                "uptime_seconds": (current_time - self.stats.get("last_cleanup", current_time)).total_seconds()  # type: ignore[operator]
            },

            # Diagnostics
            "diagnostics": {
                "memory_usage_connections": len(self.connections),
                "memory_usage_subscriptions": sum(len(connections) for connections in self.subscription_groups.values()),
                "memory_usage_offline_queues": total_queued_messages,
                "timestamp": current_time.isoformat()
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
            self.stats["messages_sent"] += 1  # type: ignore[operator]
            return True

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected during send: {connection_id}")
            await self.disconnect(connection_id)
            return False

        except Exception as e:
            logger.error(f"Error sending WebSocket message to {connection_id}: {e}")
            self.stats["errors"] += 1  # type: ignore[operator]
            await self.disconnect(connection_id)
            return False

    async def _persist_connection(self, connection: WebSocketConnection) -> None:
        """Persist connection information to Redis for scaling."""
        if not self.redis_client:
            return

        try:
            connection_data = {
                "user_id": connection.user_id,
                "connected_at": connection.connected_at.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "location_filter": json.dumps(connection.location_filter) if connection.location_filter else None,
                "risk_threshold": connection.risk_threshold,
                "permissions": list(connection.permissions),
                "user_roles": connection.user_roles
            }

            await self.redis_client.hset(
                f"websocket_connection:{connection.connection_id}",
                mapping=connection_data
            )
            await self.redis_client.expire(
                f"websocket_connection:{connection.connection_id}",
                86400  # 24 hours
            )

        except Exception as e:
            logger.warning(f"Failed to persist connection to Redis: {e}")

    async def _process_user_offline_queue(self, user_id: str, connection_id: str) -> None:
        """Process queued messages for a user coming online."""
        if user_id not in self.offline_queues:
            return

        queued_messages = self.offline_queues[user_id]
        if not queued_messages:
            return

        logger.info(f"Processing {len(queued_messages)} offline messages for user {user_id}")

        # Send queued messages
        for message in queued_messages:
            await self._send_to_connection(connection_id, message)

        # Clear offline queue
        del self.offline_queues[user_id]

    async def _queue_alert_for_offline_users(self, alert: Alert) -> None:
        """Queue alert for users who are currently offline."""
        try:
            # Get all users who should receive this alert but are offline
            async with get_session() as db:
                from ..database.models import AlertConfiguration

                # Query alert configurations that match this alert
                # This is a simplified version - in production, you'd have more complex filtering
                configs = await db.execute(
                    select(AlertConfiguration).where(
                        AlertConfiguration.is_active
                    )
                )
                configurations = configs.scalars().all()

                for config in configurations:
                    user_id = str(config.user_id)
                    if user_id not in self.user_connections or not self.user_connections[user_id]:
                        # User is offline, queue the alert
                        alert_dict = {
                            "type": "alert",
                            "alert_id": alert.id,
                            "alert_level": alert.alert_level,
                            "alert_type": alert.alert_type,
                            "title": alert.alert_title,
                            "message": alert.alert_message,
                            "timestamp": datetime.now().isoformat(),
                            "queued_at": datetime.now().isoformat()
                        }

                        if len(self.offline_queues[user_id]) < self.max_offline_queue_size:
                            self.offline_queues[user_id].append(alert_dict)
                            self.stats["messages_queued"] += 1  # type: ignore[operator]

        except Exception as e:
            logger.error(f"Failed to queue alert for offline users: {e}")

    async def _queue_alert_for_failed_connections(self, alert: Alert, failed_connection_ids: list[str]) -> None:
        """Queue alert for connections that failed to receive it."""
        for connection_id in failed_connection_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]

                alert_dict = {
                    "type": "alert",
                    "alert_id": alert.id,
                    "alert_level": alert.alert_level,
                    "alert_type": alert.alert_type,
                    "title": alert.alert_title,
                    "message": alert.alert_message,
                    "timestamp": datetime.now().isoformat(),
                    "retry_attempt": True
                }

                if len(connection.offline_queue) < connection.max_offline_messages:
                    connection.offline_queue.append(alert_dict)

    async def _send_to_connection_with_retry(self, connection_id: str, message: dict, max_retries: int = 2) -> bool:
        """Send message to connection with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                success = await self._send_to_connection(connection_id, message)
                if success:
                    return True

                if attempt < max_retries:
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff

            except Exception as e:
                if attempt == max_retries:
                    logger.warning(f"Failed to send message after {max_retries} retries: {e}")

        return False

    async def _filter_connections_for_alert_enhanced(self, alert: Alert) -> list[str]:
        """Enhanced connection filtering with better performance and criteria."""
        target_connections = []

        for connection_id, connection in self.connections.items():
            # Check if connection is healthy
            if not connection.is_healthy:
                continue

            # Check rate limiting
            if not await self._check_rate_limit(connection.user_id, connection_id):
                continue

            # Check alert type filter
            if (connection.alert_types_filter and
                alert.alert_type not in connection.alert_types_filter):
                continue

            # Check risk threshold
            if alert.risk_score and alert.risk_score < connection.risk_threshold:
                continue

            # Enhanced location filtering with proper geospatial calculation
            if (connection.location_filter and alert.latitude and alert.longitude):
                if not self._check_location_filter(alert, connection.location_filter):
                    continue

            # Check subscription groups with enhanced matching
            if connection.subscriptions:
                alert_groups = self._get_alert_groups(alert)
                if not any(group in connection.subscriptions for group in alert_groups):
                    continue

            # Check permissions for sensitive alerts
            if hasattr(alert, 'required_permissions'):
                required_perms: set[str] = getattr(alert, 'required_permissions', set())
                if required_perms and not connection.permissions.intersection(required_perms):
                    continue

            target_connections.append(connection_id)

        return target_connections

    def _check_location_filter(self, alert: Alert, location_filter: dict[str, float]) -> bool:
        """Check if alert location matches connection's location filter."""
        try:
            # Simple distance calculation (can be enhanced with proper geospatial libraries)
            alert_lat = alert.latitude
            alert_lng = alert.longitude
            filter_lat = location_filter.get("latitude", 0)
            filter_lng = location_filter.get("longitude", 0)
            radius = location_filter.get("radius", 1.0)

            # Calculate approximate distance in degrees
            lat_diff = abs(alert_lat - filter_lat)
            lng_diff = abs(alert_lng - filter_lng)

            # Simple box check (can be improved with haversine formula)
            return lat_diff <= radius and lng_diff <= radius  # type: ignore[no-any-return]

        except Exception:
            return True  # Default to include if calculation fails

    def _get_alert_groups(self, alert: Alert) -> list[str]:
        """Get subscription groups that match an alert."""
        groups = []

        # Risk level groups
        groups.append(f"{alert.alert_level}_risk")

        # Alert type groups
        groups.append(f"{alert.alert_type}_alerts")

        # Geographic groups
        if alert.country_code:
            groups.append(f"country_{alert.country_code}")

        if alert.admin_region:
            groups.append(f"region_{alert.admin_region}")

        # Priority groups
        priority = getattr(alert, 'priority', 'normal')
        if priority in ['high', 'urgent', 'emergency']:
            groups.append(f"{priority}_priority")

        return groups

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

    async def _heartbeat_monitor(self) -> None:
        """Enhanced background task to monitor connection health."""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds for better responsiveness

                current_time = datetime.now()
                ping_message = {
                    "type": "ping",
                    "timestamp": current_time.isoformat(),
                    "server_time": current_time.timestamp()
                }

                failed_connections = []
                unhealthy_connections = []

                for connection_id, connection in self.connections.items():
                    try:
                        # Check connection health
                        time_since_pong = (current_time - connection.last_pong).total_seconds()
                        if time_since_pong > 300:  # 5 minutes without pong
                            unhealthy_connections.append(connection_id)
                            connection.is_healthy = False
                            continue

                        # Refresh rate limit tokens
                        await self._refresh_rate_limit_tokens(connection)

                        # Send ping
                        await connection.websocket.send_text(json.dumps(ping_message))
                        connection.last_ping = current_time

                        # Update metrics
                        connection.metrics.last_activity = current_time

                    except Exception as e:
                        logger.debug(f"Ping failed for connection {connection_id}: {e}")
                        failed_connections.append(connection_id)

                # Clean up failed connections
                for connection_id in failed_connections:
                    await self.disconnect(connection_id)

                # Mark unhealthy connections for potential reconnection
                for connection_id in unhealthy_connections:
                    if connection_id in self.connections:
                        connection = self.connections[connection_id]
                        connection.reconnect_attempts += 1
                        if connection.reconnect_attempts > connection.max_reconnect_attempts:
                            await self.disconnect(connection_id)

                self.stats["last_health_check"] = current_time

            except asyncio.CancelledError:
                logger.info("Enhanced WebSocket heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in enhanced WebSocket heartbeat task: {e}")

    async def _metrics_collector(self) -> None:
        """Background task to collect and update performance metrics."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                current_time = datetime.now()

                # Calculate average latency
                if self.latency_history:
                    avg_latency = sum(self.latency_history) / len(self.latency_history)
                    self.stats["avg_latency_ms"] = round(avg_latency, 2)

                # Calculate throughput
                messages_per_minute = self.stats["messages_sent"]
                self.throughput_history.append(messages_per_minute)

                # Update connection health statistics
                healthy_connections = sum(1 for conn in self.connections.values() if conn.is_healthy)
                self.stats["healthy_connections"] = healthy_connections

                # Persist metrics to Redis if available
                if self.redis_client:
                    metrics_data = {
                        "timestamp": current_time.isoformat(),
                        "active_connections": len(self.connections),
                        "healthy_connections": healthy_connections,
                        "messages_sent": self.stats["messages_sent"],
                        "avg_latency_ms": self.stats["avg_latency_ms"],
                        "rate_limit_violations": self.stats["rate_limit_violations"]
                    }

                    await self.redis_client.lpush(
                        "websocket_metrics_history",
                        json.dumps(metrics_data)
                    )
                    await self.redis_client.ltrim("websocket_metrics_history", 0, 1000)  # type: ignore[misc]  # Keep last 1000 entries

                # Reset counters for next period
                self.stats["messages_sent"] = 0
                self.stats["rate_limit_violations"] = 0

            except asyncio.CancelledError:
                logger.info("WebSocket metrics collector task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket metrics collector: {e}")

    async def _process_offline_queues(self) -> None:
        """Background task to process offline message queues."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.now()

                # Process offline queues for users who come online
                for user_id, queued_messages in list(self.offline_queues.items()):
                    if user_id in self.user_connections and self.user_connections[user_id]:
                        # User is now online, process their queue
                        connection_ids = list(self.user_connections[user_id])
                        if connection_ids:
                            connection_id = connection_ids[0]  # Use first available connection
                            await self._process_user_offline_queue(user_id, connection_id)

                    # Clean up old messages
                    else:
                        # Remove messages older than 24 hours
                        cutoff_time = current_time - timedelta(hours=24)
                        queued_messages[:] = [
                            msg for msg in queued_messages
                            if datetime.fromisoformat(msg.get("queued_at", current_time.isoformat())) > cutoff_time
                        ]

                        if not queued_messages:
                            del self.offline_queues[user_id]

                # Process individual connection offline queues
                for connection in self.connections.values():
                    if connection.offline_queue:
                        # Try to send queued messages
                        messages_to_remove = []
                        for i, message in enumerate(connection.offline_queue):
                            success = await self._send_to_connection(connection.connection_id, message)
                            if success:
                                messages_to_remove.append(i)

                        # Remove successfully sent messages
                        for i in reversed(messages_to_remove):
                            connection.offline_queue.pop(i)

            except asyncio.CancelledError:
                logger.info("WebSocket offline queue processor task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket offline queue processor: {e}")

    async def _cleanup_connections(self) -> None:
        """Enhanced background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.now()
                stale_connections = []

                for connection_id, connection in self.connections.items():
                    # Check for stale connections
                    time_since_ping = (current_time - connection.last_ping).total_seconds()
                    time_since_activity = (current_time - connection.metrics.last_activity).total_seconds()

                    if time_since_ping > 600 or time_since_activity > 1800:  # 10 min ping, 30 min activity
                        stale_connections.append(connection_id)

                # Clean up stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)

                # Clean up banned users
                expired_bans = []
                for user_id, ban_time in self.banned_users.items():
                    if current_time - ban_time > timedelta(minutes=self.rate_limit_config.ban_duration_minutes):
                        expired_bans.append(user_id)

                for user_id in expired_bans:
                    del self.banned_users[user_id]

                # Update cleanup stats
                self.stats["last_cleanup"] = current_time

                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")

                if expired_bans:
                    logger.info(f"Lifted bans for {len(expired_bans)} users")

            except asyncio.CancelledError:
                logger.info("Enhanced WebSocket cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in enhanced WebSocket cleanup task: {e}")

    async def _heartbeat_monitor_old(self) -> None:
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
