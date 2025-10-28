"""
Root Test Configuration and Fixtures.

This module provides shared fixtures and configuration for all tests,
including base test setup and common utilities.
"""

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Configure test environment variables for entire test session.

    Uses autouse=True to ensure environment is set up before any tests run.
    Modern pattern replaces module-level os.environ assignments.
    """
    test_env = {
        "TESTING": "true",
        "ENVIRONMENT": "testing",
        "DATABASE_URL": "postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction",
        "REDIS_URL": "redis://localhost:6380/0",
    }
    for key, value in test_env.items():
        os.environ[key] = value


# Note: Session-scoped event_loop fixture removed - pytest-asyncio 0.21+
# with asyncio_mode="auto" manages event loops automatically


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
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
def mock_settings():
    """Create mock settings for tests."""
    settings = Mock()
    settings.testing = True
    settings.environment = "test"
    settings.database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
    settings.redis_url = "redis://localhost:6380/0"
    settings.debug = True
    settings.log_level = "DEBUG"
    settings.secret_key = "test_secret_key"
    settings.database_echo = False
    return settings


# Common test data fixtures
@pytest.fixture
def sample_location_data():
    """Sample geographic location data for testing."""
    return {
        "latitude": -1.286389,
        "longitude": 36.817222,
        "name": "Nairobi, Kenya",
        "elevation": 1795.0,
    }


@pytest.fixture
def sample_climate_data():
    """Sample climate data for testing."""
    return {
        "temperature_mean": 22.5,
        "temperature_min": 18.2,
        "temperature_max": 28.1,
        "precipitation_total": 85.3,
        "humidity_mean": 65.8,
        "pressure_mean": 1013.2,
    }


@pytest.fixture
def sample_prediction_request():
    """Sample prediction request data for testing."""
    return {
        "location": {"latitude": -1.286389, "longitude": 36.817222},
        "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        "features": {
            "include_climate": True,
            "include_vegetation": True,
            "include_population": True,
        },
    }


# Mock external services
@pytest.fixture
def mock_era5_client():
    """Mock ERA5 client for testing."""
    client = Mock()
    client.get_climate_data.return_value = {
        "temperature_2m": [25.5, 26.2, 24.8],
        "precipitation": [0.0, 2.5, 0.8],
        "humidity": [65.2, 68.1, 63.7],
    }
    return client


@pytest.fixture
def mock_chirps_client():
    """Mock CHIRPS client for testing."""
    client = Mock()
    client.get_precipitation_data.return_value = {
        "precipitation": [15.2, 8.7, 22.1, 0.0, 5.3],
        "dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    }
    return client


@pytest.fixture
def mock_modis_client():
    """Mock MODIS client for testing."""
    client = Mock()
    client.get_vegetation_data.return_value = {
        "ndvi": [0.65, 0.72, 0.68],
        "evi": [0.58, 0.64, 0.61],
        "lst_day": [298.5, 301.2, 299.8],
        "lst_night": [285.1, 287.3, 286.2],
    }
    return client


@pytest.fixture
def mock_worldpop_client():
    """Mock WorldPop client for testing."""
    client = Mock()
    client.get_population_data.return_value = {
        "population_density": 450.2,
        "total_population": 25000,
        "age_structure": {"0-5": 0.18, "5-15": 0.22, "15-65": 0.55, "65+": 0.05},
    }
    return client


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Integration test database fixtures
@pytest.fixture
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create isolated test database engine with proper cleanup.

    Uses in-memory SQLite for fast, isolated testing.
    NullPool prevents connection pooling issues in tests.
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=NullPool,  # Disable pooling for test isolation
    )

    # Import and create all tables
    from malaria_predictor.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: dispose engine and close all connections
    await engine.dispose()


@pytest.fixture
async def test_db_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic rollback for isolation.

    Each test gets a fresh transaction that is automatically rolled back,
    preventing test pollution and ensuring complete isolation.
    """
    async_session_factory = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,  # Manual flush control for better test control
        autocommit=False,  # Explicit transaction management
    )

    async with async_session_factory() as session:
        async with session.begin():
            yield session
            # Automatic rollback on fixture teardown
            await session.rollback()


@pytest.fixture
def integration_era5_repository(test_db_session):
    """Create ERA5Repository with real database session for integration tests."""
    from malaria_predictor.database.repositories import ERA5Repository

    return ERA5Repository(test_db_session)


@pytest.fixture
def integration_climate_repository(test_db_session):
    """Create ProcessedClimateRepository with real database session for integration tests."""
    from malaria_predictor.database.repositories import ProcessedClimateRepository

    return ProcessedClimateRepository(test_db_session)


@pytest.fixture
def integration_risk_repository(test_db_session):
    """Create MalariaRiskRepository with real database session for integration tests."""
    from malaria_predictor.database.repositories import MalariaRiskRepository

    return MalariaRiskRepository(test_db_session)
