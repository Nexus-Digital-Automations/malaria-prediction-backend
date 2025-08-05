"""Tests for database models and repositories.

This module tests the database layer including models,
repositories, and data persistence operations.
"""

import asyncio
from datetime import datetime, timedelta

import pandas as pd
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from malaria_predictor.database.models import (
    Base,
    ERA5DataPoint,
    ProcessedClimateData,
)
from malaria_predictor.database.repositories import (
    ERA5Repository,
    MalariaRiskRepository,
    ProcessedClimateRepository,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create async test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async test database session."""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


class TestERA5Repository:
    """Test cases for ERA5Repository."""

    @pytest.mark.asyncio
    async def test_bulk_insert_data_points(self, async_session):
        """Test bulk insertion of ERA5 data points."""
        repo = ERA5Repository(async_session)

        # Create test data
        data_points = [
            {
                "timestamp": datetime.utcnow(),
                "latitude": 0.0,
                "longitude": 30.0,
                "temperature_2m": 25.0,
                "temperature_2m_max": 28.0,
                "temperature_2m_min": 22.0,
                "total_precipitation": 5.0,
            },
            {
                "timestamp": datetime.utcnow() + timedelta(hours=1),
                "latitude": 0.0,
                "longitude": 30.0,
                "temperature_2m": 26.0,
                "temperature_2m_max": 29.0,
                "temperature_2m_min": 23.0,
                "total_precipitation": 0.0,
            },
        ]

        # Insert data
        count = await repo.bulk_insert_data_points(data_points)
        assert count == 2

        # Verify data was inserted
        result = await async_session.execute(select(ERA5DataPoint))
        points = result.scalars().all()
        assert len(points) == 2
        assert points[0].temperature_2m == 25.0

    @pytest.mark.asyncio
    async def test_get_data_range(self, async_session):
        """Test retrieving data by date range."""
        repo = ERA5Repository(async_session)

        # Insert test data
        base_time = datetime.utcnow()
        data_points = []
        for i in range(5):
            data_points.append(
                {
                    "timestamp": base_time + timedelta(hours=i),
                    "latitude": 0.0,
                    "longitude": 30.0,
                    "temperature_2m": 25.0 + i,
                }
            )

        await repo.bulk_insert_data_points(data_points)

        # Query data range
        start = base_time + timedelta(hours=1)
        end = base_time + timedelta(hours=3)

        results = await repo.get_data_range(start, end)
        assert len(results) == 3
        assert results[0].temperature_2m == 26.0

    @pytest.mark.asyncio
    async def test_get_latest_timestamp(self, async_session):
        """Test getting latest data timestamp."""
        repo = ERA5Repository(async_session)

        # Insert test data
        times = [
            datetime.utcnow() - timedelta(hours=2),
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow(),
        ]

        data_points = []
        for t in times:
            data_points.append(
                {
                    "timestamp": t,
                    "latitude": 0.0,
                    "longitude": 30.0,
                    "temperature_2m": 25.0,
                }
            )

        await repo.bulk_insert_data_points(data_points)

        # Get latest timestamp
        latest = await repo.get_latest_timestamp()
        assert latest == times[-1]


class TestProcessedClimateRepository:
    """Test cases for ProcessedClimateRepository."""

    @pytest.mark.asyncio
    async def test_save_processing_result(self, async_session):
        """Test saving processed climate data."""
        from malaria_predictor.services.data_processor import ProcessingResult

        repo = ProcessedClimateRepository(async_session)

        # Create mock processing result
        result = ProcessingResult(
            file_path="/tmp/test.nc",
            variables_processed=["temperature", "precipitation"],
            temporal_range={"start": "2023-01-01", "end": "2023-01-31"},
            spatial_bounds={"north": 10, "south": -10, "east": 40, "west": 20},
            indices_calculated=["temp_suitability"],
            processing_duration_seconds=10.5,
            success=True,
        )

        # Create test DataFrame
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "time": dates,
                "latitude": [0.0] * 5,
                "longitude": [30.0] * 5,
                "t2m_celsius": [25.0, 26.0, 24.0, 27.0, 25.5],
                "mx2t_celsius": [28.0, 29.0, 27.0, 30.0, 28.5],
                "mn2t_celsius": [22.0, 23.0, 21.0, 24.0, 22.5],
                "temp_suitability": [0.9, 0.95, 0.85, 1.0, 0.92],
            }
        )

        # Save data
        count = await repo.save_processing_result(result, data)
        assert count == 5

        # Verify data was saved
        result = await async_session.execute(select(ProcessedClimateData))
        records = result.scalars().all()
        assert len(records) == 5
        assert records[0].mean_temperature == 25.0

    @pytest.mark.asyncio
    async def test_get_location_data(self, async_session):
        """Test retrieving location-specific climate data."""
        repo = ProcessedClimateRepository(async_session)

        # Insert test data directly
        for i in range(5):
            record = ProcessedClimateData(
                date=datetime.utcnow() - timedelta(days=i),
                latitude=0.0,
                longitude=30.0,
                mean_temperature=25.0 + i,
                max_temperature=28.0 + i,
                min_temperature=22.0 + i,
                temperature_suitability=0.9,
                processing_version="1.0.0",
            )
            async_session.add(record)

        await async_session.commit()

        # Query location data
        start = datetime.utcnow() - timedelta(days=10)
        end = datetime.utcnow()

        df = await repo.get_location_data(
            latitude=0.0, longitude=30.0, start_date=start, end_date=end
        )

        assert len(df) == 5
        assert "mean_temperature" in df.columns
        assert df["mean_temperature"].min() >= 25.0


class TestMalariaRiskRepository:
    """Test cases for MalariaRiskRepository."""

    @pytest.mark.asyncio
    async def test_save_risk_assessment(self, async_session):
        """Test saving risk assessment."""
        repo = MalariaRiskRepository(async_session)

        # Create risk data
        risk_data = {
            "composite_score": 0.75,
            "temp_risk": 0.8,
            "precip_risk": 0.7,
            "humidity_risk": 0.75,
            "confidence": 0.9,
            "prediction_date": datetime.utcnow(),
            "time_horizon_days": 30,
            "model_type": "rule-based",
            "data_sources": ["ERA5"],
        }

        # Save assessment
        assessment = await repo.save_risk_assessment(
            assessment_date=datetime.utcnow(),
            latitude=0.0,
            longitude=30.0,
            risk_data=risk_data,
        )

        assert assessment.id is not None
        assert assessment.composite_risk_score == 0.75
        assert assessment.risk_level == "critical"  # 0.75 is at the critical threshold

    @pytest.mark.asyncio
    async def test_get_latest_assessment(self, async_session):
        """Test retrieving latest risk assessment."""
        repo = MalariaRiskRepository(async_session)

        # Insert multiple assessments
        for i in range(3):
            risk_data = {
                "composite_score": 0.5 + i * 0.1,
                "temp_risk": 0.8,
                "precip_risk": 0.7,
                "humidity_risk": 0.75,
                "confidence": 0.9,
            }

            await repo.save_risk_assessment(
                assessment_date=datetime.utcnow() - timedelta(days=i),
                latitude=0.0,
                longitude=30.0,
                risk_data=risk_data,
            )

        # Get latest
        latest = await repo.get_latest_assessment(0.0, 30.0)
        assert latest is not None
        assert latest.composite_risk_score == 0.5

    @pytest.mark.asyncio
    async def test_risk_level_calculation(self, async_session):
        """Test risk level categorization."""
        repo = MalariaRiskRepository(async_session)

        # Test different risk scores
        test_cases = [(0.1, "low"), (0.3, "medium"), (0.6, "high"), (0.9, "critical")]

        for score, expected_level in test_cases:
            risk_data = {
                "composite_score": score,
                "temp_risk": score,
                "precip_risk": score,
                "humidity_risk": score,
                "confidence": 0.9,
            }

            assessment = await repo.save_risk_assessment(
                assessment_date=datetime.utcnow(),
                latitude=0.0 + score,  # Vary location to avoid conflicts
                longitude=30.0,
                risk_data=risk_data,
            )

            assert assessment.risk_level == expected_level


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
