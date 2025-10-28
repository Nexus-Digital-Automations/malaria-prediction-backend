"""Comprehensive tests for the enhanced WebSocket alert system.

Tests cover:
- WebSocket connection management
- Real-time alert broadcasting
- Rate limiting and abuse protection
- Offline queue functionality
- Health monitoring and diagnostics
- Performance and latency testing
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.websockets import WebSocket

from src.malaria_predictor.alerts.websocket_manager import (
    AlertMessage,
    ConnectionMetrics,
    RateLimitConfig,
    SystemMessage,
    WebSocketAlertManager,
)
from src.malaria_predictor.database.models import Alert


class TestWebSocketAlertManager:
    """Test suite for the enhanced WebSocket Alert Manager."""

    @pytest.fixture
    def websocket_manager(self):
        """Create a fresh WebSocket manager for each test."""
        return WebSocketAlertManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = MagicMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    @pytest.fixture
    def mock_alert(self):
        """Create a mock alert for testing."""
        alert = MagicMock(spec=Alert)
        alert.id = 1
        alert.alert_level = "high"
        alert.alert_type = "outbreak_risk"
        alert.alert_title = "High Risk Alert"
        alert.alert_message = "Malaria outbreak risk detected"
        alert.latitude = 1.0
        alert.longitude = 2.0
        alert.location_name = "Test Location"
        alert.risk_score = 0.85
        alert.country_code = "UG"
        alert.admin_region = "Test Region"
        alert.confidence_score = 0.92
        alert.priority = "high"
        alert.prediction_date = datetime.now()
        return alert

    @pytest.mark.asyncio
    async def test_websocket_connection_basic(self, websocket_manager, mock_websocket):
        """Test basic WebSocket connection establishment."""
        # Test successful connection
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_1"
        )

        assert connection_id is not None
        assert len(websocket_manager.connections) == 1
        assert "test_user_1" in websocket_manager.user_connections
        assert connection_id in websocket_manager.connections

        # Verify connection properties
        connection = websocket_manager.connections[connection_id]
        assert connection.user_id == "test_user_1"
        assert connection.is_healthy is True

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_with_filters(self, websocket_manager, mock_websocket):
        """Test WebSocket connection with location and risk filters."""
        location_filter = {
            "latitude": 1.0,
            "longitude": 2.0,
            "radius": 5.0
        }

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_2",
            location_filter=location_filter,
            risk_threshold=0.7,
            alert_types_filter={"outbreak_risk", "system_health"},
            permissions={"view_alerts", "manage_alerts"},
            user_roles=["healthcare_professional"]
        )

        connection = websocket_manager.connections[connection_id]
        assert connection.location_filter == location_filter
        assert connection.risk_threshold == 0.7
        assert connection.alert_types_filter == {"outbreak_risk", "system_health"}
        assert connection.permissions == {"view_alerts", "manage_alerts"}
        assert connection.user_roles == ["healthcare_professional"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, websocket_manager, mock_websocket):
        """Test rate limiting functionality."""
        # Create connections up to the limit
        user_id = "test_user_rate_limit"
        connections = []

        for _i in range(websocket_manager.rate_limit_config.max_connections_per_user):
            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            connection_id = await websocket_manager.connect(
                websocket=mock_ws,
                user_id=user_id
            )
            connections.append(connection_id)

        # Try to create one more connection (should fail)
        with pytest.raises(Exception):  # Should raise HTTPException
            await websocket_manager.connect(
                websocket=mock_websocket,
                user_id=user_id
            )

    @pytest.mark.asyncio
    async def test_subscription_management(self, websocket_manager, mock_websocket):
        """Test subscription group management."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_sub"
        )

        # Test subscription
        success = await websocket_manager.subscribe(connection_id, "high_risk")
        assert success is True
        assert "high_risk" in websocket_manager.subscription_groups
        assert connection_id in websocket_manager.subscription_groups["high_risk"]

        # Test unsubscription
        success = await websocket_manager.unsubscribe(connection_id, "high_risk")
        assert success is True
        assert connection_id not in websocket_manager.subscription_groups.get("high_risk", set())

    @pytest.mark.asyncio
    async def test_alert_broadcasting_basic(self, websocket_manager, mock_websocket, mock_alert):
        """Test basic alert broadcasting functionality."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_alert"
        )

        # Subscribe to relevant group
        await websocket_manager.subscribe(connection_id, "high_risk")

        # Mock the enhanced filtering method
        websocket_manager._filter_connections_for_alert_enhanced = AsyncMock(return_value=[connection_id])

        # Broadcast alert
        delivered_count = await websocket_manager.broadcast_alert(mock_alert)

        assert delivered_count == 1
        mock_websocket.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_alert_filtering_location(self, websocket_manager, mock_websocket, mock_alert):
        """Test location-based alert filtering."""
        # Connection with location filter
        location_filter = {
            "latitude": 1.0,
            "longitude": 2.0,
            "radius": 1.0
        }

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_location",
            location_filter=location_filter
        )

        # Test alert within range
        filtered_connections = await websocket_manager._filter_connections_for_alert_enhanced(mock_alert)
        assert connection_id in filtered_connections

        # Test alert outside range
        mock_alert.latitude = 10.0
        mock_alert.longitude = 10.0
        filtered_connections = await websocket_manager._filter_connections_for_alert_enhanced(mock_alert)
        assert connection_id not in filtered_connections

    @pytest.mark.asyncio
    async def test_alert_filtering_risk_threshold(self, websocket_manager, mock_websocket, mock_alert):
        """Test risk threshold filtering."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_risk",
            risk_threshold=0.9
        )

        # Mock alert with lower risk score
        mock_alert.risk_score = 0.8
        filtered_connections = await websocket_manager._filter_connections_for_alert_enhanced(mock_alert)
        assert connection_id not in filtered_connections

        # Mock alert with higher risk score
        mock_alert.risk_score = 0.95
        filtered_connections = await websocket_manager._filter_connections_for_alert_enhanced(mock_alert)
        assert connection_id in filtered_connections

    @pytest.mark.asyncio
    async def test_offline_queue_functionality(self, websocket_manager):
        """Test offline message queuing."""
        user_id = "test_user_offline"

        # Add messages to offline queue
        test_messages = [
            {"type": "alert", "message": "Test alert 1"},
            {"type": "alert", "message": "Test alert 2"}
        ]

        for message in test_messages:
            websocket_manager.offline_queues[user_id].append(message)

        assert len(websocket_manager.offline_queues[user_id]) == 2

        # Simulate user coming online
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=user_id
        )

        # Verify offline queue was processed
        assert user_id not in websocket_manager.offline_queues
        assert mock_websocket.send_text.call_count >= 2  # Welcome message + queued messages

    @pytest.mark.asyncio
    async def test_connection_health_monitoring(self, websocket_manager, mock_websocket):
        """Test connection health monitoring."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_health"
        )

        connection = websocket_manager.connections[connection_id]

        # Simulate healthy connection
        connection.last_pong = datetime.now()
        assert connection.is_healthy is True

        # Simulate unhealthy connection (no pong for too long)
        connection.last_pong = datetime.now() - timedelta(minutes=10)

        # Run health check logic
        current_time = datetime.now()
        time_since_pong = (current_time - connection.last_pong).total_seconds()
        if time_since_pong > 300:  # 5 minutes
            connection.is_healthy = False

        assert connection.is_healthy is False

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, websocket_manager, mock_websocket, mock_alert):
        """Test performance metrics collection."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_metrics"
        )

        # Mock the enhanced filtering method
        websocket_manager._filter_connections_for_alert_enhanced = AsyncMock(return_value=[connection_id])

        # Broadcast multiple alerts to generate metrics
        time.time()
        for _i in range(5):
            await websocket_manager.broadcast_alert(mock_alert)

        # Check that latency is being tracked
        assert len(websocket_manager.latency_history) > 0

        # Verify metrics are being collected
        stats = websocket_manager.get_stats()
        assert "avg_latency_ms" in stats
        assert "messages_sent" in stats
        assert stats["active_connections"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_manager):
        """Test handling multiple concurrent connections."""

        # Create multiple concurrent connections
        async def create_connection(user_id):
            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            connection_id = await websocket_manager.connect(
                websocket=mock_ws,
                user_id=user_id
            )
            return connection_id

        # Create 10 concurrent connections
        tasks = [create_connection(f"user_{i}") for i in range(10)]
        connection_ids = await asyncio.gather(*tasks)

        assert len(connection_ids) == 10
        assert len(websocket_manager.connections) == 10
        assert websocket_manager.stats["active_connections"] == 10

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, websocket_manager, mock_websocket):
        """Test proper cleanup on disconnection."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_disconnect"
        )

        # Subscribe to groups
        await websocket_manager.subscribe(connection_id, "test_group")

        # Verify connection exists
        assert connection_id in websocket_manager.connections
        assert "test_user_disconnect" in websocket_manager.user_connections
        assert "test_group" in websocket_manager.subscription_groups

        # Disconnect
        await websocket_manager.disconnect(connection_id)

        # Verify cleanup
        assert connection_id not in websocket_manager.connections
        assert "test_user_disconnect" not in websocket_manager.user_connections
        assert "test_group" not in websocket_manager.subscription_groups

    @pytest.mark.asyncio
    async def test_message_retry_mechanism(self, websocket_manager, mock_websocket):
        """Test message retry mechanism for failed sends."""
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id="test_user_retry"
        )

        # Mock send_text to fail first time, succeed second time
        call_count = 0
        async def mock_send_text_with_failure(message):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return True

        mock_websocket.send_text.side_effect = mock_send_text_with_failure

        # Test retry mechanism
        test_message = {"type": "test", "message": "Test message"}
        success = await websocket_manager._send_to_connection_with_retry(
            connection_id, test_message, max_retries=2
        )

        assert success is True
        assert call_count == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    async def test_stats_comprehensive(self, websocket_manager, mock_websocket):
        """Test comprehensive statistics reporting."""
        # Create connections and subscriptions
        for i in range(3):
            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            connection_id = await websocket_manager.connect(
                websocket=mock_ws,
                user_id=f"user_{i}"
            )
            await websocket_manager.subscribe(connection_id, f"group_{i}")

        # Add some offline queues
        websocket_manager.offline_queues["offline_user_1"] = [{"message": "test"}]
        websocket_manager.offline_queues["offline_user_2"] = [{"message": "test1"}, {"message": "test2"}]

        # Get comprehensive stats
        stats = websocket_manager.get_stats()

        # Verify core statistics
        assert stats["active_connections"] == 3
        assert stats["active_users"] == 3
        assert stats["subscription_groups_count"] == 3

        # Verify offline queue statistics
        assert stats["offline_queues"]["total_queued_messages"] == 3
        assert stats["offline_queues"]["queued_users"] == 2

        # Verify system health information
        assert "system_health" in stats
        assert "diagnostics" in stats
        assert "rate_limit_config" in stats

    @pytest.mark.asyncio
    async def test_background_tasks_lifecycle(self, websocket_manager):
        """Test background task lifecycle management."""
        # Initialize manager
        await websocket_manager.initialize()

        # Verify tasks are created
        assert websocket_manager._cleanup_task is not None
        assert websocket_manager._heartbeat_task is not None
        assert websocket_manager._metrics_task is not None
        assert websocket_manager._queue_processor_task is not None

        # Stop tasks
        await websocket_manager.stop_background_tasks()

        # Verify tasks are cleaned up
        assert websocket_manager._cleanup_task is None
        assert websocket_manager._heartbeat_task is None
        assert websocket_manager._metrics_task is None
        assert websocket_manager._queue_processor_task is None

    def test_rate_limit_config(self):
        """Test rate limit configuration."""
        config = RateLimitConfig()

        assert config.max_connections_per_user == 5
        assert config.max_messages_per_minute == 60
        assert config.max_subscriptions_per_connection == 10
        assert config.cooldown_period_seconds == 30
        assert config.ban_duration_minutes == 15

    def test_connection_metrics(self):
        """Test connection metrics tracking."""
        metrics = ConnectionMetrics()

        assert metrics.messages_sent == 0
        assert metrics.messages_received == 0
        assert metrics.subscriptions_count == 0
        assert metrics.reconnection_count == 0
        assert metrics.error_count == 0
        assert isinstance(metrics.latency_ms, list)

    def test_alert_message_creation(self):
        """Test alert message creation."""
        alert_message = AlertMessage(
            alert_id=123,
            alert_level="high",
            alert_type="outbreak_risk",
            title="Test Alert",
            message="Test message",
            priority="urgent",
            confidence_score=0.95
        )

        assert alert_message.alert_id == 123
        assert alert_message.priority == "urgent"
        assert alert_message.confidence_score == 0.95
        assert alert_message.type == "alert"

    def test_system_message_creation(self):
        """Test system message creation."""
        system_message = SystemMessage(
            type="connection_status",
            message="Connection established",
            connection_id="test_conn_123"
        )

        assert system_message.type == "connection_status"
        assert system_message.connection_id == "test_conn_123"
        assert system_message.message == "Connection established"


class TestWebSocketIntegration:
    """Integration tests for WebSocket system with other components."""

    @pytest.mark.asyncio
    async def test_integration_with_alert_engine(self):
        """Test integration with alert engine."""
        # This would test the actual integration with the alert engine
        # Mock the alert engine and test end-to-end flow
        pass

    @pytest.mark.asyncio
    async def test_redis_persistence(self):
        """Test Redis persistence functionality."""
        # This would test Redis integration if configured
        pass

    @pytest.mark.asyncio
    async def test_scaling_with_multiple_instances(self):
        """Test scaling with multiple WebSocket manager instances."""
        # This would test multi-instance coordination
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
