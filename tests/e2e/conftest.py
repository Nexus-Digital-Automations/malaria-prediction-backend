"""
E2E Test Configuration and Fixtures.

This module provides shared fixtures and configuration for end-to-end tests,
inheriting from integration test fixtures and adding E2E-specific setup.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from malaria_predictor.api.main import app
from malaria_predictor.ml.models import MalariaEnsembleModel

# Import fixtures by importing the module directly


@pytest_asyncio.fixture
async def test_async_client():
    """Create async test client for E2E FastAPI application testing."""
    # Create a test app instance with testing configuration
    app.dependency_overrides = {}

    # Use ASGITransport for proper async client setup
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_environmental_data():
    """Create mock environmental data for E2E prediction tests."""
    return {
        "era5": {
            "temperature_2m": 25.5,
            "temperature_2m_max": 30.2,
            "temperature_2m_min": 20.8,
            "dewpoint_2m": 18.5,
            "total_precipitation": 2.3,
            "relative_humidity": 75.2,
            "surface_pressure": 1013.25,
            "data_quality": "good",
        },
        "chirps": {
            "precipitation_mm": 45.8,
            "precipitation_anomaly": 1.2,
            "drought_index": 0.3,
            "data_quality": "good",
        },
        "modis": {
            "ndvi": 0.75,
            "evi": 0.68,
            "lst_day": 35.2,
            "lst_night": 22.1,
            "water_mask": 0.1,
            "data_quality": "good",
        },
        "worldpop": {
            "population_density": 2500.5,
            "population_total": 125000,
            "urban_fraction": 0.85,
            "data_quality": "good",
        },
        "map": {
            "pfpr": 0.25,
            "incidence_rate": 150.3,
            "intervention_coverage": 0.65,
            "net_usage": 0.72,
            "data_quality": "good",
        },
    }


@pytest.fixture
def prediction_request():
    """Create sample prediction request for E2E tests."""
    from datetime import date, timedelta

    from malaria_predictor.api.models import (
        LocationPoint,
        ModelType,
        SinglePredictionRequest,
    )

    return SinglePredictionRequest(
        location=LocationPoint(
            latitude=-1.286389, longitude=36.817222, name="Nairobi, Kenya"
        ),
        target_date=date.today() + timedelta(days=7),
        model_type=ModelType.ENSEMBLE,
        include_uncertainty=True,
        include_features=True,
    )


@pytest.fixture
def nairobi_location():
    """Sample Nairobi location data for E2E testing."""
    return {
        "latitude": -1.286389,
        "longitude": 36.817222,
        "name": "Nairobi, Kenya",
        "elevation": 1795.0,
        "timezone": "Africa/Nairobi",
    }


@pytest.fixture
def mock_ensemble_model():
    """Create mock ensemble model for E2E prediction testing."""
    ensemble_model = Mock(spec=MalariaEnsembleModel)
    ensemble_model.predict.return_value = {
        "risk_score": 0.75,
        "confidence": 0.85,
        "predictions": [0.15, 0.35, 0.50],  # low, medium, high
        "uncertainty": 0.12,
        "component_predictions": {
            "lstm": 0.73,
            "transformer": 0.77,
        },
        "contributing_factors": {
            "temperature": 0.25,
            "precipitation": 0.30,
            "humidity": 0.20,
            "vegetation": 0.15,
            "population": 0.10,
        },
    }
    ensemble_model.is_loaded = True
    return ensemble_model


@pytest.fixture
def test_redis_client():
    """Create test Redis client for E2E tests."""
    import redis

    # Use test Redis configuration
    client = redis.Redis.from_url("redis://localhost:6380/0", decode_responses=True)

    # Clear test database before tests
    try:
        client.flushdb()
    except redis.ConnectionError:
        # If Redis is not available, return a mock client
        client = Mock()
        client.setex = Mock()
        client.get = Mock(return_value=None)
        client.flushdb = Mock()

    yield client

    # Cleanup after tests
    try:
        client.flushdb()
        if hasattr(client, "close"):
            client.close()
    except (redis.ConnectionError, AttributeError):
        pass  # Ignore cleanup errors for mock client


@pytest_asyncio.fixture
async def test_redis_async_client():
    """Create async Redis client for E2E tests."""
    try:
        import redis.asyncio as aioredis

        client = aioredis.Redis.from_url(
            "redis://localhost:6380/0", decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.close()
    except ImportError:
        # If redis asyncio is not available, return a mock
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock()
        client.flushdb = AsyncMock()
        yield client
