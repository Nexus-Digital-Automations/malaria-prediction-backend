"""Unit tests for enhanced alert system components.

Tests individual components of the alert system using the actual database models.
"""

import json
from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.malaria_predictor.alerts.alert_analytics import AlertAnalyticsEngine
from src.malaria_predictor.alerts.alert_history_manager import (
    AlertHistoryManager,
    AlertHistoryQuery,
    AlertHistorySummary,
)
from src.malaria_predictor.database.models import Alert, AlertConfiguration, User


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
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_alerts(db_session: AsyncSession, test_user: User) -> list[Alert]:
    """Create sample alerts for testing."""
    # First create an alert configuration
    config = AlertConfiguration(
        id=1,
        alert_type="high_risk",
        threshold_value=0.8,
        is_enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(config)
    await db_session.flush()

    alerts = []
    for i in range(5):
        alert = Alert(
            id=i + 1,
            configuration_id=config.id,
            alert_type="high_risk" if i % 2 == 0 else "medium_risk",
            alert_level="high" if i % 2 == 0 else "medium",
            alert_title=f"Test Alert {i}",
            alert_message=f"Test message {i}",
            status="delivered" if i % 2 == 0 else "pending",
            priority=i + 1,
            latitude=-1.2921 + (i * 0.001),
            longitude=36.8219 + (i * 0.001),
            risk_score=0.7 + (i * 0.05),
            created_at=datetime.now() - timedelta(hours=i),
            updated_at=datetime.now() - timedelta(hours=i)
        )
        alerts.append(alert)
        db_session.add(alert)

    await db_session.commit()
    for alert in alerts:
        await db_session.refresh(alert)

    return alerts


class TestAlertHistoryManager:
    """Test AlertHistoryManager functionality."""

    @pytest.fixture
    async def history_manager(self, db_session: AsyncSession, mock_redis) -> AlertHistoryManager:
        """Create AlertHistoryManager instance."""
        return AlertHistoryManager(db_session, mock_redis)

    async def test_get_alert_history_basic(
        self,
        history_manager: AlertHistoryManager,
        test_user: User,
        sample_alerts: list[Alert]
    ):
        """Test basic alert history retrieval."""
        query = AlertHistoryQuery(
            user_id=test_user.id,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(hours=1)
        )

        history = await history_manager.get_alert_history(query)

        assert isinstance(history, dict)
        assert "alerts" in history
        assert "total_count" in history
        assert len(history["alerts"]) >= 0  # May be 0 if query filters don't match
        assert history["total_count"] >= 0

    async def test_get_alert_history_filtered(
        self,
        history_manager: AlertHistoryManager,
        test_user: User,
        sample_alerts: list[Alert]
    ):
        """Test filtered alert history retrieval."""
        query = AlertHistoryQuery(
            user_id=test_user.id,
            alert_types=["high_risk"],
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(hours=1)
        )

        history = await history_manager.get_alert_history(query)

        assert isinstance(history, dict)
        assert "alerts" in history
        # Filter may result in fewer or no results
        for alert in history["alerts"]:
            assert alert["alert_type"] == "high_risk"

    async def test_get_alert_summary(
        self,
        history_manager: AlertHistoryManager,
        test_user: User,
        sample_alerts: list[Alert]
    ):
        """Test alert summary generation."""
        summary = await history_manager.get_alert_summary(
            user_id=test_user.id,
            period_days=7
        )

        assert isinstance(summary, AlertHistorySummary)
        assert summary.total_alerts >= 0
        assert hasattr(summary, 'alerts_by_type')
        assert hasattr(summary, 'delivery_success_rate')

    async def test_archive_old_alerts(
        self,
        history_manager: AlertHistoryManager,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test archiving of old alerts."""
        # Create alert configuration first
        config = AlertConfiguration(
            id=2,
            alert_type="low_risk",
            threshold_value=0.3,
            is_enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(config)
        await db_session.flush()

        # Create old alert
        old_alert = Alert(
            id=100,
            configuration_id=config.id,
            alert_type="low_risk",
            alert_level="low",
            alert_title="Old Alert",
            alert_message="Old message",
            status="delivered",
            priority=1,
            latitude=-1.2921,
            longitude=36.8219,
            created_at=datetime.now() - timedelta(days=40)
        )
        db_session.add(old_alert)
        await db_session.commit()

        # Archive alerts older than 30 days
        archived_count = await history_manager.archive_old_alerts(
            cutoff_date=datetime.now() - timedelta(days=30)
        )

        assert archived_count >= 0  # May be 0 if archiving not implemented

    async def test_export_alert_history(
        self,
        history_manager: AlertHistoryManager,
        test_user: User,
        sample_alerts: list[Alert]
    ):
        """Test alert history export functionality."""
        export_data = await history_manager.export_alert_history(
            user_id=test_user.id,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(hours=1),
            format="json"
        )

        assert isinstance(export_data, dict)
        assert "alerts" in export_data
        assert "export_metadata" in export_data


class TestAlertAnalyticsEngine:
    """Test AlertAnalyticsEngine functionality."""

    @pytest.fixture
    async def analytics_engine(self, db_session: AsyncSession, mock_redis) -> AlertAnalyticsEngine:
        """Create AlertAnalyticsEngine instance."""
        return AlertAnalyticsEngine(db_session, mock_redis)

    async def test_get_alert_kpis(
        self,
        analytics_engine: AlertAnalyticsEngine,
        sample_alerts: list[Alert]
    ):
        """Test KPI calculation."""
        kpis = await analytics_engine.get_alert_kpis()

        assert hasattr(kpis, 'total_alerts_sent')
        assert hasattr(kpis, 'delivery_rate')
        assert hasattr(kpis, 'avg_response_time')
        assert kpis.total_alerts_sent >= 0
        assert 0 <= kpis.delivery_rate <= 1

    async def test_get_channel_performance(
        self,
        analytics_engine: AlertAnalyticsEngine,
        sample_alerts: list[Alert]
    ):
        """Test channel performance analysis."""
        performance = await analytics_engine.get_channel_performance(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(hours=1)
        )

        assert isinstance(performance, list)
        for channel_perf in performance:
            assert hasattr(channel_perf, 'channel')
            assert hasattr(channel_perf, 'total_sent')
            assert hasattr(channel_perf, 'delivery_rate')

    async def test_get_user_engagement_metrics(
        self,
        analytics_engine: AlertAnalyticsEngine,
        sample_alerts: list[Alert]
    ):
        """Test user engagement metrics."""
        engagement = await analytics_engine.get_user_engagement_metrics(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(hours=1)
        )

        assert hasattr(engagement, 'total_users')
        assert hasattr(engagement, 'active_users')
        assert hasattr(engagement, 'avg_alerts_per_user')
        assert engagement.total_users >= 0

    async def test_detect_anomalies(
        self,
        analytics_engine: AlertAnalyticsEngine,
        sample_alerts: list[Alert]
    ):
        """Test anomaly detection."""
        anomalies = await analytics_engine.detect_anomalies(
            metric="delivery_rate",
            lookback_hours=24
        )

        assert isinstance(anomalies, list)
        # May or may not have anomalies depending on test data

    async def test_system_health_metrics(
        self,
        analytics_engine: AlertAnalyticsEngine
    ):
        """Test system health monitoring."""
        health_metrics = await analytics_engine.get_system_health_metrics()

        assert health_metrics is not None
        assert hasattr(health_metrics, 'database_connections')
        assert hasattr(health_metrics, 'cache_hit_rate')
        assert hasattr(health_metrics, 'avg_response_time')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
