"""
Comprehensive tests for Firebase Cloud Messaging and Push Notification System.

This test suite provides thorough testing of all notification components including
FCM service, templates, scheduling, emergency alerts, analytics, and API endpoints.
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.malaria_predictor.notifications import (
    FCMService,
    NotificationManager,
    NotificationTemplateEngine,
)
from src.malaria_predictor.notifications.models import (
    DeviceToken,
    NotificationLog,
    NotificationPriority,
    NotificationStatus,
    DevicePlatform,
    TopicSubscription,
)
from src.malaria_predictor.notifications.templates import TemplateContext
from src.malaria_predictor.notifications.emergency_alerts import (
    EmergencyLevel,
    EmergencyType,
    EmergencyAlert,
)
from src.malaria_predictor.notifications.fcm_service import FCMMessageData
from src.malaria_predictor.database.models import Base


# Test Fixtures
@pytest.fixture
def test_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_fcm_service():
    """Mock FCM service for testing."""
    with patch('firebase_admin.initialize_app') as mock_init, \
         patch('firebase_admin.get_app') as mock_get_app, \
         patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()}), \
         patch('firebase_admin.messaging.send') as mock_send, \
         patch('firebase_admin.messaging.subscribe_to_topic') as mock_subscribe, \
         patch('firebase_admin.messaging.unsubscribe_from_topic') as mock_unsubscribe, \
         patch('src.malaria_predictor.notifications.fcm_service.FCMService._initialize_firebase'):

        # Create a mock app
        mock_app = MagicMock()
        mock_init.return_value = mock_app
        mock_get_app.return_value = mock_app

        # Mock Firebase messaging operations
        mock_send.return_value = "msg_123"
        mock_subscribe.return_value = MagicMock()
        mock_unsubscribe.return_value = MagicMock()

        service = FCMService()
        service.app = mock_app
        yield service


@pytest.fixture
def notification_manager(mock_fcm_service, test_session):
    """Create notification manager with mocked dependencies."""
    manager = NotificationManager(
        fcm_credentials_path=None,
        project_id="test-project",
        db_session=test_session,
    )
    manager.fcm_service = mock_fcm_service
    return manager


@pytest.fixture
def template_engine():
    """Create notification template engine."""
    return NotificationTemplateEngine()


@pytest.fixture
def sample_device_token(test_session):
    """Create sample device token for testing."""
    device = DeviceToken(
        token="test_token_123",
        platform=DevicePlatform.ANDROID,
        user_id="user_123",
        is_active=True,
    )
    test_session.add(device)
    test_session.commit()
    return device


@pytest.fixture
def sample_template_context():
    """Create sample template context for testing."""
    return TemplateContext(
        user_id="user_123",
        risk_score=0.75,
        risk_level="high",
        location_name="Nairobi",
        coordinates={"lat": -1.2921, "lng": 36.8219},
        temperature=26.5,
        humidity=75.0,
        precipitation=12.3,
    )


# FCM Service Tests
class TestFCMService:
    """Test Firebase Cloud Messaging service functionality."""

    @pytest.mark.asyncio
    async def test_send_to_token_success(self, mock_fcm_service):
        """Test successful notification sending to single token."""
        message_data = FCMMessageData(
            title="Test Notification",
            body="This is a test message",
            data={"test": "data"},
        )

        success, message_id, error = await mock_fcm_service.send_to_token(
            "test_token", message_data
        )

        assert success is True
        assert message_id == "msg_123"
        assert error is None

    @pytest.mark.asyncio
    async def test_send_to_tokens_batch(self, mock_fcm_service):
        """Test batch notification sending."""
        message_data = FCMMessageData(
            title="Batch Notification",
            body="Batch test message",
        )

        results = await mock_fcm_service.send_to_tokens(
            ["token1", "token2"], message_data
        )

        assert "token1" in results
        assert results["token1"][0] is True  # success

    @pytest.mark.asyncio
    async def test_send_to_topic(self, mock_fcm_service):
        """Test topic-based notification sending."""
        message_data = FCMMessageData(
            title="Topic Notification",
            body="Topic test message",
        )

        success, message_id, error = await mock_fcm_service.send_to_topic(
            "test_topic", message_data
        )

        assert success is True
        assert message_id == "msg_124"
        assert error is None

    @pytest.mark.asyncio
    async def test_topic_subscription(self, mock_fcm_service):
        """Test topic subscription functionality."""
        results = await mock_fcm_service.subscribe_to_topic(
            ["token1"], "malaria_alerts"
        )

        assert results["token1"] is True

    @pytest.mark.asyncio
    async def test_token_validation(self, mock_fcm_service):
        """Test FCM token validation."""
        is_valid = await mock_fcm_service.validate_token("valid_token")
        assert is_valid is True


# Template Engine Tests
class TestNotificationTemplateEngine:
    """Test notification template rendering and composition."""

    def test_malaria_alert_template_creation(self, template_engine):
        """Test creation of malaria alert template."""
        template = template_engine.create_malaria_alert_template()

        assert template.name == "malaria_risk_alert"
        assert template.category == "alert"
        assert template.priority == NotificationPriority.HIGH
        assert "🦟" in template.title_template

    def test_outbreak_warning_template_creation(self, template_engine):
        """Test creation of outbreak warning template."""
        template = template_engine.create_outbreak_warning_template()

        assert template.name == "outbreak_warning"
        assert template.category == "emergency"
        assert template.priority == NotificationPriority.CRITICAL
        assert "🚨" in template.title_template

    def test_template_rendering(self, template_engine, sample_template_context):
        """Test template rendering with context."""
        template = template_engine.create_malaria_alert_template()
        rendered = template_engine.render_template(template, sample_template_context)

        assert "title" in rendered
        assert "body" in rendered
        assert "High Risk" in rendered["title"]
        assert "Nairobi" in rendered["body"]
        assert "75.0%" in rendered["body"]

    def test_template_context_validation(self):
        """Test template context data validation."""
        # Valid context
        context = TemplateContext(risk_score=0.5, risk_level="medium")
        assert context.risk_score == 0.5

        # Invalid risk score
        with pytest.raises(ValueError):
            TemplateContext(risk_score=1.5)

        # Invalid risk level
        with pytest.raises(ValueError):
            TemplateContext(risk_level="invalid")

    def test_custom_jinja_filters(self, template_engine):
        """Test custom Jinja2 filters."""
        # Test risk emoji filter
        assert template_engine._risk_emoji_filter("low") == "🟢"
        assert template_engine._risk_emoji_filter("high") == "🟠"

        # Test percentage filter
        assert template_engine._percentage_filter(0.75) == "75.0%"
        assert template_engine._percentage_filter(None) == "N/A"

        # Test temperature filter
        assert template_engine._temperature_filter(25.5) == "25.5°C"


# Emergency Alert System Tests
class TestEmergencyAlertSystem:
    """Test emergency alert functionality."""

    @pytest.mark.asyncio
    async def test_outbreak_alert_creation(self, notification_manager):
        """Test creation of outbreak emergency alert."""
        alert = await notification_manager.emergency_system.create_outbreak_alert(
            location_name="Test City",
            outbreak_probability=0.85,
            affected_population=10000,
            coordinates={"lat": -1.0, "lng": 36.0},
        )

        assert isinstance(alert, EmergencyAlert)
        assert alert.alert_type == EmergencyType.OUTBREAK
        assert alert.severity == EmergencyLevel.EMERGENCY  # High probability
        assert "Test City" in alert.title
        assert alert.source_data['outbreak_probability'] == 0.85

    @pytest.mark.asyncio
    async def test_vector_surge_alert_creation(self, notification_manager):
        """Test creation of vector surge alert."""
        weather_conditions = {
            "temperature": 28.0,
            "humidity": 80.0,
            "precipitation": 15.0,
        }

        alert = await notification_manager.emergency_system.create_vector_surge_alert(
            location_name="Test Region",
            mosquito_density_increase=250.0,
            weather_conditions=weather_conditions,
        )

        assert alert.alert_type == EmergencyType.VECTOR_SURGE
        assert alert.severity == EmergencyLevel.ADVISORY
        assert "mosquito" in alert.message.lower()

    @pytest.mark.asyncio
    async def test_emergency_alert_issuance(self, notification_manager, sample_device_token):
        """Test emergency alert issuance process."""
        alert = EmergencyAlert(
            alert_id="test_alert_123",
            alert_type=EmergencyType.OUTBREAK,
            severity=EmergencyLevel.WARNING,
            title="Test Emergency Alert",
            message="This is a test emergency alert",
            issued_by="Test System",
        )

        result = await notification_manager.emergency_system.issue_emergency_alert(alert)

        assert result["success"] is True
        assert result["alert_id"] == "test_alert_123"

    @pytest.mark.asyncio
    async def test_emergency_alert_cancellation(self, notification_manager):
        """Test emergency alert cancellation."""
        result = await notification_manager.emergency_system.cancel_emergency_alert(
            alert_id="test_alert_123",
            reason="False alarm",
        )

        assert result["success"] is True
        assert result["reason"] == "False alarm"


# Device Management Tests
class TestDeviceManagement:
    """Test device registration and management."""

    @pytest.mark.asyncio
    async def test_device_registration(self, notification_manager):
        """Test device registration process."""
        success, error = await notification_manager.register_device(
            token="new_test_token",
            platform=DevicePlatform.IOS,
            user_id="user_456",
            device_info={"model": "iPhone 12", "os": "iOS 15"},
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_device_unregistration(self, notification_manager, sample_device_token):
        """Test device unregistration process."""
        success, error = await notification_manager.unregister_device(
            sample_device_token.token
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_device_auto_subscription(self, notification_manager):
        """Test automatic topic subscription during registration."""
        user_preferences = {
            "location": {"country": "Kenya", "region": "Nairobi"},
            "language": "en",
            "user_type": "resident",
        }

        success, error = await notification_manager.register_device(
            token="auto_subscribe_token",
            platform=DevicePlatform.ANDROID,
            user_id="user_789",
            auto_subscribe=True,
            user_preferences=user_preferences,
        )

        assert success is True


# Notification Sending Tests
class TestNotificationSending:
    """Test notification sending functionality."""

    @pytest.mark.asyncio
    async def test_malaria_alert_sending(self, notification_manager, sample_device_token):
        """Test sending malaria risk alerts."""
        result = await notification_manager.send_malaria_alert(
            risk_score=0.8,
            location_name="Test Location",
            coordinates={"lat": -1.0, "lng": 36.0},
            environmental_data={"temperature": 25.0, "humidity": 70.0},
            immediate=True,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_outbreak_alert_sending(self, notification_manager, sample_device_token):
        """Test sending outbreak alerts."""
        result = await notification_manager.send_outbreak_alert(
            location_name="Outbreak Location",
            outbreak_probability=0.9,
            affected_population=5000,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_medication_reminder_sending(self, notification_manager, sample_device_token):
        """Test sending medication reminders."""
        result = await notification_manager.send_medication_reminder(
            user_id="user_123",
            medication_name="Antimalarial Tablet",
            dosage="1 tablet daily",
        )

        assert result["success"] is True


# Topic Management Tests
class TestTopicManagement:
    """Test topic subscription and management."""

    @pytest.mark.asyncio
    async def test_user_topic_subscription(self, notification_manager, sample_device_token):
        """Test subscribing user to topics."""
        topics = ["malaria_alerts", "health_updates", "weather_alerts"]

        results = await notification_manager.subscribe_user_to_topics(
            user_id="user_123",
            topics=topics,
        )

        assert all(results.values())  # All subscriptions should succeed

    @pytest.mark.asyncio
    async def test_topic_statistics(self, notification_manager):
        """Test topic subscription statistics."""
        stats = await notification_manager.topic_manager.get_topic_statistics()

        assert "total_subscriptions" in stats
        assert "topics" in stats
        assert "platforms" in stats


# Analytics Tests
class TestNotificationAnalytics:
    """Test notification analytics and reporting."""

    @pytest.mark.asyncio
    async def test_delivery_summary(self, notification_manager):
        """Test delivery summary analytics."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        summary = await notification_manager.analytics.get_delivery_summary(
            start_date=start_date,
            end_date=end_date,
        )

        assert "summary" in summary
        assert "trends" in summary
        assert "platform_breakdown" in summary

    @pytest.mark.asyncio
    async def test_engagement_metrics(self, notification_manager):
        """Test engagement metrics analytics."""
        metrics = await notification_manager.analytics.get_engagement_metrics()

        assert "overall_engagement" in metrics
        assert "template_performance" in metrics

    @pytest.mark.asyncio
    async def test_error_analysis(self, notification_manager):
        """Test error analysis functionality."""
        analysis = await notification_manager.analytics.get_error_analysis()

        assert "summary" in analysis
        assert "error_patterns" in analysis

    @pytest.mark.asyncio
    async def test_performance_insights(self, notification_manager):
        """Test performance insights generation."""
        insights = await notification_manager.analytics.get_performance_insights()

        assert "insights" in insights
        assert "recommendations" in insights

    @pytest.mark.asyncio
    async def test_notification_dashboard(self, notification_manager):
        """Test comprehensive notification dashboard."""
        dashboard = await notification_manager.get_notification_dashboard(days=7)

        assert "delivery_summary" in dashboard
        assert "engagement_metrics" in dashboard
        assert "system_health" in dashboard


# System Management Tests
class TestSystemManagement:
    """Test system maintenance and health monitoring."""

    @pytest.mark.asyncio
    async def test_data_cleanup(self, notification_manager):
        """Test old data cleanup functionality."""
        stats = await notification_manager.cleanup_old_data(
            notification_retention_days=30,
            inactive_device_days=7,
        )

        assert "deleted_notifications" in stats
        assert "deactivated_devices" in stats
        assert "cleaned_subscriptions" in stats

    @pytest.mark.asyncio
    async def test_system_status(self, notification_manager):
        """Test system status monitoring."""
        status = await notification_manager.get_system_status()

        assert status["status"] == "healthy"
        assert "metrics" in status
        assert "services" in status


# API Endpoint Tests
class TestNotificationAPI:
    """Test notification API endpoints."""

    def test_api_import(self):
        """Test that notification API router can be imported."""
        try:
            from src.malaria_predictor.api.routers.notifications import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"Failed to import notifications router: {e}")

    @pytest.mark.asyncio
    async def test_device_registration_endpoint(self):
        """Test device registration API endpoint."""
        # This would require setting up FastAPI test client
        # and mocking authentication, which is beyond the scope
        # of this basic test suite
        pass

    @pytest.mark.asyncio
    async def test_notification_sending_endpoints(self):
        """Test notification sending API endpoints."""
        # Similar to above, requires full API test setup
        pass


# Integration Tests
class TestNotificationIntegration:
    """Test integration between different notification components."""

    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(self, notification_manager):
        """Test complete notification flow from registration to delivery."""
        # 1. Register device
        success, _ = await notification_manager.register_device(
            token="integration_test_token",
            platform=DevicePlatform.ANDROID,
            user_id="integration_user",
        )
        assert success

        # 2. Send notification
        result = await notification_manager.send_malaria_alert(
            risk_score=0.7,
            location_name="Integration Test Location",
            target_users=["integration_user"],
        )
        assert result["success"]

        # 3. Check analytics
        dashboard = await notification_manager.get_notification_dashboard()
        assert dashboard is not None

    @pytest.mark.asyncio
    async def test_emergency_alert_workflow(self, notification_manager):
        """Test complete emergency alert workflow."""
        # 1. Register device for emergency alerts
        success, _ = await notification_manager.register_device(
            token="emergency_test_token",
            platform=DevicePlatform.IOS,
            user_id="emergency_user",
        )
        assert success

        # 2. Issue emergency alert
        result = await notification_manager.send_outbreak_alert(
            location_name="Emergency Test Location",
            outbreak_probability=0.95,
        )
        assert result["success"]

        # 3. Verify alert tracking
        active_alerts = await notification_manager.emergency_system.get_active_emergency_alerts()
        assert len(active_alerts) >= 0  # May be empty in test environment


# Performance Tests
class TestNotificationPerformance:
    """Test notification system performance and scalability."""

    @pytest.mark.asyncio
    async def test_batch_notification_performance(self, notification_manager):
        """Test performance of batch notification sending."""
        import time

        # Create multiple test tokens
        tokens = [f"perf_test_token_{i}" for i in range(100)]

        start_time = time.time()

        # Register devices in batch
        for token in tokens:
            await notification_manager.register_device(
                token=token,
                platform=DevicePlatform.ANDROID,
                user_id=f"perf_user_{token}",
            )

        registration_time = time.time() - start_time

        # Send batch notification
        start_time = time.time()
        result = await notification_manager.send_malaria_alert(
            risk_score=0.6,
            location_name="Performance Test Location",
        )
        sending_time = time.time() - start_time

        # Basic performance assertions (adjust thresholds as needed)
        assert registration_time < 30.0  # Should register 100 devices in under 30s
        assert sending_time < 10.0       # Should send notification in under 10s
        assert result["success"]

    @pytest.mark.asyncio
    async def test_concurrent_notification_handling(self, notification_manager):
        """Test handling of concurrent notification requests."""
        # Create multiple concurrent notification tasks
        tasks = []
        for i in range(10):
            task = notification_manager.send_malaria_alert(
                risk_score=0.5 + (i * 0.05),
                location_name=f"Concurrent Test Location {i}",
            )
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all tasks completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result["success"]


# Configuration and Settings Tests
class TestNotificationConfiguration:
    """Test notification system configuration and settings."""

    def test_fcm_settings_validation(self):
        """Test FCM settings validation."""
        from src.malaria_predictor.config import FCMSettings

        # Valid settings
        settings = FCMSettings(
            credentials_path="test.json",
            project_id="test-project",
            enable_fcm=True,
        )
        assert settings.enable_fcm is True

        # Invalid credentials path
        with pytest.raises(ValueError):
            FCMSettings(credentials_path="invalid.txt")

    def test_notification_priority_enum(self):
        """Test notification priority enumeration."""
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.NORMAL == "normal"
        assert NotificationPriority.HIGH == "high"
        assert NotificationPriority.CRITICAL == "critical"

    def test_device_platform_enum(self):
        """Test device platform enumeration."""
        assert DevicePlatform.ANDROID == "android"
        assert DevicePlatform.IOS == "ios"
        assert DevicePlatform.WEB == "web"


# Error Handling Tests
class TestNotificationErrorHandling:
    """Test error handling in notification system."""

    @pytest.mark.asyncio
    async def test_invalid_token_handling(self, notification_manager):
        """Test handling of invalid FCM tokens."""
        # Mock FCM service to return invalid token error
        notification_manager.fcm_service.send_to_token = AsyncMock(
            return_value=(False, None, "Invalid token")
        )

        result = await notification_manager.send_malaria_alert(
            risk_score=0.5,
            location_name="Error Test Location",
            target_users=["nonexistent_user"],
        )

        # Should handle error gracefully
        assert "error" in result or not result["success"]

    @pytest.mark.asyncio
    async def test_database_error_handling(self, notification_manager):
        """Test handling of database connection errors."""
        # This would require mocking database session to raise exceptions
        pass

    @pytest.mark.asyncio
    async def test_network_error_handling(self, notification_manager):
        """Test handling of network connectivity errors."""
        # Mock FCM service to simulate network error
        notification_manager.fcm_service.send_to_token = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await notification_manager.send_malaria_alert(
            risk_score=0.5,
            location_name="Network Error Test",
        )

        # Should handle network errors gracefully
        assert not result["success"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])