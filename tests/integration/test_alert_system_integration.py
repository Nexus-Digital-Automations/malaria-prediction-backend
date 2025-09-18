"""Comprehensive integration tests for the enhanced alert system.

Tests the interaction between all alert system components including:
- AlertEngine with AlertHistoryManager integration
- Enhanced Firebase service with template system
- Alert analytics and performance monitoring
- Bulk notification management
- WebSocket alert delivery
- Alert template management
- Alert history archiving and retrieval
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.malaria_predictor.models.alerts import (
    Alert,
    AlertChannel,
    AlertConfiguration,
    AlertPreference,
    AlertStatus,
    AlertType,
)
from src.malaria_predictor.models.models import User

from src.malaria_predictor.alerts.alert_analytics import AlertAnalyticsEngine
from src.malaria_predictor.alerts.alert_engine import AlertEngine
from src.malaria_predictor.alerts.alert_history_manager import AlertHistoryManager
from src.malaria_predictor.alerts.alert_template_manager import AlertTemplateManager
from src.malaria_predictor.alerts.bulk_notification_manager import (
    BulkNotificationManager,
)
from src.malaria_predictor.alerts.enhanced_firebase_service import (
    EnhancedFirebaseService,
)
from src.malaria_predictor.alerts.notification_service import NotificationService
from src.malaria_predictor.alerts.websocket_manager import WebSocketAlertManager

logger = logging.getLogger(__name__)


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expires: dict[str, datetime] = {}

    async def get(self, key: str) -> str | None:
        """Get value from Redis."""
        if key in self._expires and datetime.now() > self._expires[key]:
            del self._data[key]
            del self._expires[key]
            return None
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        """Set value in Redis."""
        self._data[key] = value
        if ex:
            self._expires[key] = datetime.now() + timedelta(seconds=ex)
        return True

    async def delete(self, key: str) -> int:
        """Delete key from Redis."""
        count = 0
        if key in self._data:
            del self._data[key]
            count += 1
        if key in self._expires:
            del self._expires[key]
        return count

    async def exists(self, key: str) -> int:
        """Check if key exists."""
        return 1 if key in self._data else 0

    async def incr(self, key: str) -> int:
        """Increment counter."""
        current = int(self._data.get(key, 0))
        self._data[key] = str(current + 1)
        return current + 1

    async def hget(self, key: str, field: str) -> str | None:
        """Get hash field."""
        hash_data = self._data.get(key, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        return hash_data.get(field)

    async def hset(self, key: str, field: str, value: str) -> int:
        """Set hash field."""
        hash_data = self._data.get(key, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        hash_data[field] = value
        self._data[key] = json.dumps(hash_data)
        return 1


@pytest.fixture
async def mock_redis():
    """Provide mock Redis client."""
    return MockRedisClient()


@pytest.fixture
async def mock_firebase_app():
    """Mock Firebase app for testing."""
    mock_app = MagicMock()
    mock_app.credential = MagicMock()
    return mock_app


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user for alert testing."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed_password",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        firebase_token="test_firebase_token"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def alert_config(db_session: AsyncSession, test_user: User) -> AlertConfiguration:
    """Create test alert configuration."""
    config = AlertConfiguration(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        alert_type=AlertType.HIGH_RISK,
        threshold=0.8,
        is_enabled=True,
        channels=[AlertChannel.PUSH, AlertChannel.EMAIL],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)
    return config


@pytest.fixture
async def alert_preference(db_session: AsyncSession, test_user: User) -> AlertPreference:
    """Create test alert preference."""
    preference = AlertPreference(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        alert_type=AlertType.HIGH_RISK,
        channel=AlertChannel.PUSH,
        is_enabled=True,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        frequency_limit=5,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(preference)
    await db_session.commit()
    await db_session.refresh(preference)
    return preference


@pytest.fixture
async def alert_history_manager(db_session: AsyncSession, mock_redis) -> AlertHistoryManager:
    """Create AlertHistoryManager for testing."""
    return AlertHistoryManager(db_session, mock_redis)


@pytest.fixture
async def alert_analytics_engine(db_session: AsyncSession, mock_redis) -> AlertAnalyticsEngine:
    """Create AlertAnalyticsEngine for testing."""
    return AlertAnalyticsEngine(db_session, mock_redis)


@pytest.fixture
async def alert_template_manager(db_session: AsyncSession, mock_redis) -> AlertTemplateManager:
    """Create AlertTemplateManager for testing."""
    return AlertTemplateManager(db_session, mock_redis)


@pytest.fixture
async def enhanced_firebase_service(mock_firebase_app, mock_redis) -> EnhancedFirebaseService:
    """Create EnhancedFirebaseService for testing."""
    with patch('firebase_admin.initialize_app', return_value=mock_firebase_app):
        with patch('firebase_admin.messaging.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = "message_id_123"
            service = EnhancedFirebaseService(mock_redis)
            return service


@pytest.fixture
async def bulk_notification_manager(
    db_session: AsyncSession,
    mock_redis,
    enhanced_firebase_service: EnhancedFirebaseService
) -> BulkNotificationManager:
    """Create BulkNotificationManager for testing."""
    notification_service = NotificationService(db_session, mock_redis)
    return BulkNotificationManager(db_session, mock_redis, notification_service, enhanced_firebase_service)


@pytest.fixture
async def websocket_manager(mock_redis) -> WebSocketAlertManager:
    """Create WebSocketAlertManager for testing."""
    return WebSocketAlertManager(mock_redis)


@pytest.fixture
async def alert_engine(
    db_session: AsyncSession,
    mock_redis,
    alert_history_manager: AlertHistoryManager,
    alert_analytics_engine: AlertAnalyticsEngine,
    enhanced_firebase_service: EnhancedFirebaseService,
    websocket_manager: WebSocketAlertManager
) -> AlertEngine:
    """Create AlertEngine with all dependencies for testing."""
    notification_service = NotificationService(db_session, mock_redis)

    engine = AlertEngine(db_session, mock_redis)
    # Inject dependencies for testing
    engine.history_manager = alert_history_manager
    engine.analytics_engine = alert_analytics_engine
    engine.firebase_service = enhanced_firebase_service
    engine.websocket_manager = websocket_manager
    engine.notification_service = notification_service

    return engine


class TestAlertSystemIntegration:
    """Integration tests for the complete alert system."""

    async def test_end_to_end_alert_workflow(
        self,
        alert_engine: AlertEngine,
        alert_history_manager: AlertHistoryManager,
        alert_analytics_engine: AlertAnalyticsEngine,
        test_user: User,
        alert_config: AlertConfiguration,
        alert_preference: AlertPreference,
        db_session: AsyncSession
    ):
        """Test complete alert workflow from creation to delivery and tracking."""
        # Create a high-risk alert
        alert_data = {
            "user_id": test_user.id,
            "alert_type": AlertType.HIGH_RISK,
            "title": "High Malaria Risk Detected",
            "message": "Risk level: 0.95 in your area",
            "risk_score": 0.95,
            "location": {"lat": -1.2921, "lng": 36.8219},
            "metadata": {"region": "Nairobi", "data_source": "ERA5"}
        }

        # Process alert through engine
        alert_id = await alert_engine.create_alert(
            user_id=test_user.id,
            alert_type=AlertType.HIGH_RISK,
            title=alert_data["title"],
            message=alert_data["message"],
            risk_score=alert_data["risk_score"],
            location=alert_data["location"],
            metadata=alert_data["metadata"]
        )

        assert alert_id is not None

        # Verify alert was created in database
        alert = await db_session.get(Alert, alert_id)
        assert alert is not None
        assert alert.alert_type == AlertType.HIGH_RISK
        assert alert.risk_score == 0.95

        # Verify alert appears in history
        from src.malaria_predictor.alerts.alert_history_manager import AlertHistoryQuery
        history_query = AlertHistoryQuery(
            user_id=test_user.id,
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )

        history = await alert_history_manager.get_alert_history(history_query)
        assert len(history["alerts"]) > 0
        assert any(a["id"] == alert_id for a in history["alerts"])

        # Verify analytics tracking
        kpis = await alert_analytics_engine.get_alert_kpis()
        assert kpis.total_alerts_sent > 0

    async def test_template_based_notification_integration(
        self,
        alert_template_manager: AlertTemplateManager,
        enhanced_firebase_service: EnhancedFirebaseService,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test template creation, rendering, and notification delivery."""
        # Create a custom template
        from src.malaria_predictor.alerts.alert_template_manager import AlertTemplate
        template = AlertTemplate(
            name="High Risk Alert",
            subject="⚠️ High Malaria Risk in {{location}}",
            body="Alert: Risk level {{risk_score}} detected in {{location}}. Take precautions.",
            template_type="risk_alert",
            variables=["location", "risk_score"],
            is_active=True,
            language="en"
        )

        template_id = await alert_template_manager.create_template(template, test_user.id)
        assert template_id is not None

        # Render template with variables
        variables = {
            "location": "Nairobi",
            "risk_score": "0.95"
        }

        rendered = await alert_template_manager.render_template(template_id, variables, "en")
        assert rendered is not None
        assert "High Malaria Risk in Nairobi" in rendered.subject
        assert "Risk level 0.95 detected" in rendered.body

        # Send notification using template
        with patch('firebase_admin.messaging.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = "message_123"

            result = await enhanced_firebase_service.send_template_notification(
                template_id=template_id,
                user_id=test_user.id,
                variables=variables
            )

            assert len(result) > 0
            assert all(res.success for res in result.values())
            mock_send.assert_called()

    async def test_bulk_notification_campaign_integration(
        self,
        bulk_notification_manager: BulkNotificationManager,
        alert_template_manager: AlertTemplateManager,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test bulk notification campaign creation and execution."""
        # Create template for campaign
        from src.malaria_predictor.alerts.alert_template_manager import AlertTemplate
        template = AlertTemplate(
            name="Seasonal Alert",
            subject="Seasonal Malaria Alert",
            body="Increased risk expected in the coming weeks. Stay protected.",
            template_type="seasonal_alert",
            variables=[],
            is_active=True,
            language="en"
        )

        template_id = await alert_template_manager.create_template(template, test_user.id)

        # Create bulk campaign
        from src.malaria_predictor.alerts.bulk_notification_manager import (
            BulkNotificationCampaign,
            NotificationTemplate,
            TargetingCriteria,
        )

        campaign = BulkNotificationCampaign(
            name="Seasonal Awareness Campaign",
            description="Alert users about seasonal malaria patterns",
            template=NotificationTemplate(
                template_id=template_id,
                variables={}
            ),
            targeting=TargetingCriteria(
                regions=["Nairobi"],
                user_segments=["high_risk_users"],
                min_risk_score=0.7
            ),
            schedule_time=datetime.now() + timedelta(minutes=1),
            channels=[AlertChannel.PUSH, AlertChannel.EMAIL]
        )

        # Execute campaign
        campaign_id = await bulk_notification_manager.create_campaign(campaign, test_user.id)
        assert campaign_id is not None

        # Verify campaign status
        status = await bulk_notification_manager.get_campaign_status(campaign_id)
        assert status is not None
        assert status.campaign_id == campaign_id

    async def test_alert_analytics_and_performance_monitoring(
        self,
        alert_analytics_engine: AlertAnalyticsEngine,
        alert_history_manager: AlertHistoryManager,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test analytics collection and performance monitoring."""
        # Create test alerts for analytics
        alerts_data = [
            {
                "user_id": test_user.id,
                "alert_type": AlertType.HIGH_RISK,
                "title": f"Test Alert {i}",
                "message": f"Test message {i}",
                "status": AlertStatus.DELIVERED if i % 2 == 0 else AlertStatus.FAILED,
                "delivery_channel": AlertChannel.PUSH,
                "created_at": datetime.now() - timedelta(hours=i)
            }
            for i in range(10)
        ]

        # Add alerts to database
        for alert_data in alerts_data:
            alert = Alert(
                id=str(uuid.uuid4()),
                **alert_data
            )
            db_session.add(alert)
        await db_session.commit()

        # Get analytics KPIs
        kpis = await alert_analytics_engine.get_alert_kpis()
        assert kpis.total_alerts_sent >= 10
        assert kpis.delivery_rate >= 0.0

        # Get channel performance
        channel_performance = await alert_analytics_engine.get_channel_performance(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        assert len(channel_performance) > 0
        assert AlertChannel.PUSH in [cp.channel for cp in channel_performance]

        # Get user engagement metrics
        engagement = await alert_analytics_engine.get_user_engagement_metrics(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        assert engagement.total_users >= 1

    async def test_alert_history_archiving_and_retrieval(
        self,
        alert_history_manager: AlertHistoryManager,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test alert history management, archiving, and retrieval."""
        # Create historical alerts
        old_alerts = []
        for i in range(5):
            alert = Alert(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                alert_type=AlertType.MEDIUM_RISK,
                title=f"Historical Alert {i}",
                message=f"Historical message {i}",
                status=AlertStatus.DELIVERED,
                delivery_channel=AlertChannel.EMAIL,
                created_at=datetime.now() - timedelta(days=40 + i)  # Old alerts
            )
            old_alerts.append(alert)
            db_session.add(alert)
        await db_session.commit()

        # Archive old alerts
        archived_count = await alert_history_manager.archive_old_alerts(
            cutoff_date=datetime.now() - timedelta(days=30)
        )
        assert archived_count == 5

        # Verify alerts are archived
        from src.malaria_predictor.alerts.alert_history_manager import AlertHistoryQuery
        query = AlertHistoryQuery(
            user_id=test_user.id,
            start_date=datetime.now() - timedelta(days=50),
            end_date=datetime.now() - timedelta(days=30),
            include_archived=True
        )

        history = await alert_history_manager.get_alert_history(query)
        archived_alerts = [a for a in history["alerts"] if a["is_archived"]]
        assert len(archived_alerts) == 5

        # Test alert summary generation
        summary = await alert_history_manager.get_alert_summary(
            user_id=test_user.id,
            period_days=60
        )
        assert summary is not None
        assert summary.total_alerts >= 5

    async def test_websocket_alert_delivery_integration(
        self,
        websocket_manager: WebSocketAlertManager,
        alert_engine: AlertEngine,
        test_user: User
    ):
        """Test WebSocket alert delivery integration."""
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # Register user connection
        await websocket_manager.register_user_connection(test_user.id, mock_websocket)

        # Verify connection is registered
        assert await websocket_manager.is_user_connected(test_user.id)

        # Create alert that should trigger WebSocket notification
        alert_data = {
            "user_id": test_user.id,
            "alert_type": AlertType.EMERGENCY,
            "title": "Emergency Alert",
            "message": "Immediate action required",
            "risk_score": 0.99
        }

        # Send alert via WebSocket
        await websocket_manager.send_user_alert(
            user_id=test_user.id,
            alert_data=alert_data
        )

        # Verify WebSocket send was called
        mock_websocket.send.assert_called_once()

        # Verify alert data was sent correctly
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["alert_type"] == AlertType.EMERGENCY.value
        assert sent_data["title"] == "Emergency Alert"

    async def test_firebase_and_template_error_handling(
        self,
        enhanced_firebase_service: EnhancedFirebaseService,
        alert_template_manager: AlertTemplateManager,
        test_user: User
    ):
        """Test error handling in Firebase and template services."""
        # Test template rendering with missing variables
        from src.malaria_predictor.alerts.alert_template_manager import AlertTemplate
        template = AlertTemplate(
            name="Test Template",
            subject="Hello {{name}}",
            body="Your score is {{score}}",
            template_type="test",
            variables=["name", "score"],
            is_active=True,
            language="en"
        )

        template_id = await alert_template_manager.create_template(template, test_user.id)

        # Try to render with missing variables
        incomplete_vars = {"name": "John"}  # Missing 'score'
        rendered = await alert_template_manager.render_template(
            template_id, incomplete_vars, "en"
        )

        # Should handle gracefully or return None
        assert rendered is None or "{{score}}" not in rendered.body

        # Test Firebase service with invalid token
        with patch('firebase_admin.messaging.send', side_effect=Exception("Invalid token")):
            from src.malaria_predictor.alerts.enhanced_firebase_service import (
                FirebaseNotification,
            )
            notification = FirebaseNotification(
                title="Test",
                body="Test message",
                data={}
            )

            result = await enhanced_firebase_service.send_notification(
                token="invalid_token",
                notification=notification
            )

            # Should handle error gracefully
            assert not result.success
            assert "error" in result.error_message.lower()

    async def test_system_health_and_monitoring_integration(
        self,
        alert_analytics_engine: AlertAnalyticsEngine,
        alert_engine: AlertEngine,
        db_session: AsyncSession
    ):
        """Test system health monitoring and alerting."""
        # Get system health metrics
        health_metrics = await alert_analytics_engine.get_system_health_metrics()
        assert health_metrics is not None
        assert hasattr(health_metrics, 'database_connections')
        assert hasattr(health_metrics, 'cache_hit_rate')
        assert hasattr(health_metrics, 'avg_response_time')

        # Test system performance monitoring
        performance_metrics = await alert_analytics_engine.calculate_performance_metrics(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now()
        )
        assert performance_metrics is not None

        # Verify monitoring data is properly collected
        assert performance_metrics.avg_processing_time >= 0
        assert performance_metrics.total_processed >= 0

    async def test_concurrent_alert_processing(
        self,
        alert_engine: AlertEngine,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test concurrent alert processing and thread safety."""
        # Create multiple alerts concurrently
        alert_tasks = []
        for i in range(10):
            task = alert_engine.create_alert(
                user_id=test_user.id,
                alert_type=AlertType.LOW_RISK,
                title=f"Concurrent Alert {i}",
                message=f"Test concurrent processing {i}",
                risk_score=0.3 + (i * 0.05)
            )
            alert_tasks.append(task)

        # Execute all tasks concurrently
        alert_ids = await asyncio.gather(*alert_tasks, return_exceptions=True)

        # Verify all alerts were created successfully
        successful_ids = [aid for aid in alert_ids if isinstance(aid, str)]
        assert len(successful_ids) == 10

        # Verify all alerts exist in database
        for alert_id in successful_ids:
            alert = await db_session.get(Alert, alert_id)
            assert alert is not None
            assert alert.user_id == test_user.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
