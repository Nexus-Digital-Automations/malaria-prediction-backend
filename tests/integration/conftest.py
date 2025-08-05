"""
Integration Test Configuration and Fixtures.

This module provides shared fixtures and configuration for integration tests,
including database setup, Redis connections, and mock services.
"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import Mock

import pytest
import pytest_asyncio
import redis
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from malaria_predictor.api.main import app
from malaria_predictor.config import Settings
from malaria_predictor.database.models import Base
from malaria_predictor.database.session import get_session
from malaria_predictor.ml.models import (
    MalariaEnsembleModel,
    MalariaLSTM,
    MalariaTransformer,
)

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
TEST_REDIS_URL = "redis://localhost:6380/0"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_database_engine():
    """Create test database engine for integration tests."""
    # Create test database if it doesn't exist
    sync_engine = create_engine(
        "postgresql://test_user:test_password@localhost:5433/postgres"
    )

    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT"))  # Close any existing transaction

        # Check if test database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'test_malaria_prediction'")
        )

        if not result.fetchone():
            conn.execute(text("CREATE DATABASE test_malaria_prediction"))

    sync_engine.dispose()

    # Create async engine for tests with NullPool for testing isolation
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_database_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with proper cleanup."""
    async_session_maker = sessionmaker(
        test_database_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            # Ensure session is properly closed
            if hasattr(session, "_transaction") and session._transaction:
                await session.rollback()
            await session.close()


@pytest.fixture(scope="session")
def test_redis_client():
    """Create test Redis client for integration tests."""
    client = redis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)

    # Clear test database
    client.flushdb()

    yield client

    # Cleanup
    client.flushdb()
    client.close()


@pytest_asyncio.fixture
async def test_redis_async_client():
    """Create async Redis client for integration tests."""
    import redis.asyncio as aioredis

    client = aioredis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)

    # Clear test database
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
def test_settings():
    """Create test configuration settings."""
    return Settings(
        environment="testing",
        database__url=TEST_DATABASE_URL,
        redis__url=TEST_REDIS_URL,
        debug=True,
        testing=True,
        secret_key="test_secret_key",
        era5_api_key="test_era5_key",
        modis_api_key="test_modis_key",
        log_level="DEBUG",
        enable_metrics=False,
        enable_tracing=False,
    )


@pytest.fixture
def test_app(test_settings, test_db_session):
    """Create test FastAPI application with overridden dependencies."""

    # Override database dependency
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    yield app

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_app):
    """Create test client for FastAPI application."""
    with TestClient(test_app) as client:
        yield client


@pytest_asyncio.fixture
async def test_async_client(test_app):
    """Create async test client for FastAPI application."""
    from httpx import ASGITransport

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)

        # Create subdirectories
        (test_dir / "era5").mkdir()
        (test_dir / "chirps").mkdir()
        (test_dir / "modis").mkdir()
        (test_dir / "worldpop").mkdir()
        (test_dir / "map").mkdir()
        (test_dir / "models").mkdir()

        yield test_dir


@pytest.fixture
def model_directory():
    """Create temporary directory with mock model files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model_dir = Path(temp_dir)

        # Create mock model files
        (model_dir / "lstm_model.pth").touch()
        (model_dir / "transformer_model.pth").touch()
        (model_dir / "ensemble_model.pth").touch()

        # Create model metadata
        metadata = {
            "version": "1.0.0",
            "trained_on": "2024-01-01",
            "performance": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
            },
            "input_features": [
                "temperature",
                "precipitation",
                "humidity",
                "ndvi",
                "evi",
                "population_density",
                "elevation",
                "malaria_history",
            ],
            "output_classes": ["low_risk", "medium_risk", "high_risk"],
        }

        import json

        for model_name in ["lstm", "transformer", "ensemble"]:
            with open(model_dir / f"{model_name}_metadata.json", "w") as f:
                json.dump(metadata, f)

        yield model_dir


@pytest.fixture
def training_data():
    """Create synthetic training data."""
    import numpy as np

    # Generate synthetic environmental data
    n_samples = 1000
    sequence_length = 30
    n_features = 8

    X = np.random.rand(n_samples, sequence_length, n_features).astype(np.float32)

    # Generate synthetic labels with some patterns
    # Higher risk for higher temperature and lower NDVI
    temperature_risk = (X[:, :, 0].mean(axis=1) - 0.5) * 2  # Normalize to [-1, 1]
    ndvi_risk = -(X[:, :, 4].mean(axis=1) - 0.5) * 2  # Invert NDVI

    combined_risk = (temperature_risk + ndvi_risk) / 2
    y = np.digitize(combined_risk, bins=[-0.5, 0.5])  # 3 classes: 0, 1, 2

    return X, y


@pytest.fixture
def training_pipeline():
    """Create training pipeline for testing."""
    from unittest.mock import Mock

    from malaria_predictor.ml.training.pipeline import MalariaTrainingPipeline

    mock_harmonizer = Mock()
    config = {
        "model_types": ["lstm", "transformer", "ensemble"],
        "validation_split": 0.2,
        "batch_size": 32,
        "epochs": 10,
        "early_stopping_patience": 3,
    }
    return MalariaTrainingPipeline(data_harmonizer=mock_harmonizer, config=config)


@pytest.fixture
def mock_lstm_model():
    """Create mock LSTM model for testing."""
    from unittest.mock import MagicMock

    import torch

    model = MagicMock(spec=MalariaLSTM)
    model.is_loaded = True
    model.device = "cpu"

    # Mock prediction output
    mock_output = torch.tensor([[0.2, 0.3, 0.5]])  # Probabilities for 3 classes
    model.forward.return_value = mock_output

    # Mock async predict method
    async def mock_predict(features):
        return {
            "risk_score": 0.75,
            "confidence": 0.85,
            "predictions": [0.2, 0.3, 0.5],
            "uncertainty": 0.15,
        }

    model.predict = mock_predict

    # Mock batch prediction
    async def mock_predict_batch(batch_features):
        return [
            {
                "risk_score": 0.7 + (i * 0.05),
                "confidence": 0.8,
                "predictions": [0.2, 0.3, 0.5],
                "uncertainty": 0.2,
            }
            for i in range(len(batch_features))
        ]

    model.predict_batch = mock_predict_batch

    return model


@pytest.fixture
def mock_transformer_model():
    """Create mock Transformer model for testing."""
    from unittest.mock import MagicMock

    import torch

    model = MagicMock(spec=MalariaTransformer)
    model.is_loaded = True
    model.device = "cpu"

    # Mock prediction output
    mock_output = torch.tensor([[0.3, 0.4, 0.3]])  # Probabilities for 3 classes
    model.forward.return_value = mock_output

    # Mock async predict method
    async def mock_predict(features):
        return {
            "risk_score": 0.72,
            "confidence": 0.82,
            "predictions": [0.3, 0.4, 0.3],
            "uncertainty": 0.18,
        }

    model.predict = mock_predict

    # Mock batch prediction
    async def mock_predict_batch(batch_features):
        return [
            {
                "risk_score": 0.6 + (i * 0.02),
                "confidence": 0.85,
                "predictions": [0.3, 0.4, 0.3],
                "uncertainty": 0.15,
            }
            for i in range(len(batch_features))
        ]

    model.predict_batch = mock_predict_batch

    return model


@pytest.fixture
def mock_ml_models(mock_lstm_model, mock_transformer_model):
    """Create mock ML models for testing."""
    # Mock Ensemble model
    ensemble_model = Mock(spec=MalariaEnsembleModel)

    # Mock async predict method for ensemble
    async def mock_ensemble_predict(features):
        return {
            "risk_score": 0.735,
            "confidence": 0.87,
            "predictions": [0.25, 0.35, 0.4],
            "uncertainty": 0.13,
            "component_predictions": {
                "lstm": 0.75,
                "transformer": 0.72,
            },
        }

    ensemble_model.predict = mock_ensemble_predict
    ensemble_model.is_loaded = True

    return {
        "lstm": mock_lstm_model,
        "transformer": mock_transformer_model,
        "ensemble": ensemble_model,
    }


@pytest.fixture
def mock_external_apis():
    """Create mock external API responses."""

    # ERA5 API mock response
    era5_response = {
        "data": {
            "temperature_2m": [25.5, 26.2, 24.8],
            "precipitation": [0.0, 2.5, 0.8],
            "humidity": [65.2, 68.1, 63.7],
            "timestamps": [
                "2024-01-01T00:00:00",
                "2024-01-01T06:00:00",
                "2024-01-01T12:00:00",
            ],
        },
        "status": "success",
        "metadata": {
            "location": {"lat": -1.286389, "lon": 36.817222},
            "resolution": "0.25",
            "source": "era5",
        },
    }

    # CHIRPS API mock response
    chirps_response = {
        "data": {
            "precipitation": [15.2, 8.7, 22.1, 0.0, 5.3],
            "dates": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
        },
        "status": "success",
        "metadata": {
            "location": {"lat": -1.286389, "lon": 36.817222},
            "resolution": "0.05",
            "source": "chirps",
        },
    }

    # MODIS API mock response
    modis_response = {
        "data": {
            "ndvi": [0.65, 0.72, 0.68],
            "evi": [0.58, 0.64, 0.61],
            "lst_day": [298.5, 301.2, 299.8],
            "lst_night": [285.1, 287.3, 286.2],
            "dates": ["2024-01-01", "2024-01-09", "2024-01-17"],
        },
        "status": "success",
        "metadata": {
            "location": {"lat": -1.286389, "lon": 36.817222},
            "resolution": "250m",
            "source": "modis",
        },
    }

    # WorldPop API mock response
    worldpop_response = {
        "data": {
            "population_density": 450.2,
            "total_population": 25000,
            "age_structure": {
                "0-5": 0.18,
                "5-15": 0.22,
                "15-65": 0.55,
                "65+": 0.05,
            },
        },
        "status": "success",
        "metadata": {
            "location": {"lat": -1.286389, "lon": 36.817222},
            "resolution": "100m",
            "source": "worldpop",
            "year": 2023,
        },
    }

    # MAP API mock response
    map_response = {
        "data": {
            "malaria_incidence": 0.12,
            "parasite_rate": 0.08,
            "intervention_coverage": {
                "itn": 0.75,
                "irs": 0.45,
                "act": 0.82,
            },
            "environmental_suitability": 0.68,
        },
        "status": "success",
        "metadata": {
            "location": {"lat": -1.286389, "lon": 36.817222},
            "source": "map",
            "year": 2023,
        },
    }

    return {
        "era5": era5_response,
        "chirps": chirps_response,
        "modis": modis_response,
        "worldpop": worldpop_response,
        "map": map_response,
    }


@pytest.fixture
def sample_environmental_data():
    """Create sample environmental data for testing."""
    return {
        "location": {
            "latitude": -1.286389,
            "longitude": 36.817222,
            "name": "Nairobi, Kenya",
        },
        "date_range": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
        "climate_data": {
            "temperature_mean": 22.5,
            "temperature_min": 18.2,
            "temperature_max": 28.1,
            "precipitation_total": 85.3,
            "humidity_mean": 65.8,
        },
        "vegetation_data": {
            "ndvi_mean": 0.68,
            "evi_mean": 0.61,
            "lst_day_mean": 299.5,
            "lst_night_mean": 286.2,
        },
        "population_data": {
            "density": 450.2,
            "total": 25000,
            "urban_fraction": 0.85,
        },
        "malaria_data": {
            "historical_incidence": 0.12,
            "intervention_coverage": 0.67,
            "environmental_suitability": 0.68,
        },
    }


@pytest_asyncio.fixture
async def integration_test_setup(
    test_database_engine,
    test_redis_client,
    test_data_dir,
    mock_ml_models,
    mock_external_apis,
):
    """Complete integration test setup with all dependencies."""
    setup_data = {
        "database_engine": test_database_engine,
        "redis_client": test_redis_client,
        "data_dir": test_data_dir,
        "ml_models": mock_ml_models,
        "api_responses": mock_external_apis,
    }

    yield setup_data

    # Cleanup
    test_redis_client.flushdb()


class IntegrationTestCase:
    """Base class for integration test cases with common utilities."""

    @staticmethod
    def assert_prediction_response(response_data: dict):
        """Assert that prediction response has expected structure."""
        assert "risk_score" in response_data
        assert "confidence" in response_data
        assert "predictions" in response_data
        assert "metadata" in response_data

        # Validate data types and ranges
        assert isinstance(response_data["risk_score"], int | float)
        assert 0 <= response_data["risk_score"] <= 1
        assert isinstance(response_data["confidence"], int | float)
        assert 0 <= response_data["confidence"] <= 1
        assert isinstance(response_data["predictions"], list)
        assert len(response_data["predictions"]) > 0

    @staticmethod
    def assert_environmental_data(data: dict):
        """Assert that environmental data has expected structure."""
        required_keys = ["location", "date_range", "climate_data"]
        for key in required_keys:
            assert key in data

        # Validate location data
        location = data["location"]
        assert "latitude" in location
        assert "longitude" in location
        assert -90 <= location["latitude"] <= 90
        assert -180 <= location["longitude"] <= 180

    @staticmethod
    def assert_database_record(record: dict, expected_fields: list):
        """Assert that database record has expected fields."""
        for field in expected_fields:
            assert field in record
            assert record[field] is not None
