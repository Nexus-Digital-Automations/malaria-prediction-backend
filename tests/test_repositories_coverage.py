"""
Comprehensive tests for database/repositories.py to achieve high coverage.

This module tests the repository pattern classes that encapsulate database
operations for different data types, promoting clean separation of concerns.
"""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path before importing modules
sys.path.insert(0, "src")

from malaria_predictor.database.repositories import (
    ERA5Repository,
    MalariaRiskRepository,
    ProcessedClimateRepository,
)
from malaria_predictor.services.data_processor import ProcessingResult


class TestERA5Repository:
    """Test ERA5Repository class to achieve comprehensive coverage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock(spec=AsyncSession)
        session.bind = Mock()
        session.bind.dialect.name = "postgresql"
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create ERA5Repository instance."""
        return ERA5Repository(mock_session)

    def test_era5_repository_initialization(self, mock_session):
        """Test ERA5Repository initialization."""
        repo = ERA5Repository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_bulk_insert_data_points_empty_list(self, repository):
        """Test bulk insert with empty data points list."""
        result = await repository.bulk_insert_data_points([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_bulk_insert_data_points_postgresql_upsert(
        self, repository, mock_session
    ):
        """Test bulk insert with PostgreSQL upsert."""
        data_points = [
            {
                "timestamp": datetime.now(),
                "latitude": 10.0,
                "longitude": 15.0,
                "temperature_2m": 25.5,
                "temperature_2m_max": 30.0,
                "temperature_2m_min": 20.0,
                "dewpoint_2m": 18.0,
                "total_precipitation": 5.2,
            }
        ]

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repository.bulk_insert_data_points(data_points, upsert=True)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_insert_data_points_sqlite(self, repository, mock_session):
        """Test bulk insert with SQLite (testing mode)."""
        mock_session.bind.dialect.name = "sqlite"

        data_points = [
            {
                "timestamp": datetime.now(),
                "latitude": 10.0,
                "longitude": 15.0,
                "temperature_2m": 25.5,
            }
        ]

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repository.bulk_insert_data_points(data_points, upsert=True)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_insert_data_points_no_upsert(self, repository, mock_session):
        """Test bulk insert without upsert."""
        data_points = [
            {
                "timestamp": datetime.now(),
                "latitude": 10.0,
                "longitude": 15.0,
                "temperature_2m": 25.5,
            }
        ]

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repository.bulk_insert_data_points(data_points, upsert=False)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_data_range(self, repository, mock_session):
        """Test getting data for a date range."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        mock_data_point = Mock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_data_point]
        mock_session.execute.return_value = mock_result

        result = await repository.get_data_range(start_date, end_date)

        assert result == [mock_data_point]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_data_range_with_location(self, repository, mock_session):
        """Test getting data for a date range with location filter."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        latitude = 10.0
        longitude = 15.0

        mock_data_point = Mock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_data_point]
        mock_session.execute.return_value = mock_result

        result = await repository.get_data_range(
            start_date, end_date, latitude, longitude, buffer_degrees=0.5
        )

        assert result == [mock_data_point]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_timestamp(self, repository, mock_session):
        """Test getting latest timestamp."""
        expected_timestamp = datetime.now()
        mock_result = Mock()
        mock_result.scalar.return_value = expected_timestamp
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_timestamp()

        assert result == expected_timestamp
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_timestamp_with_location(self, repository, mock_session):
        """Test getting latest timestamp with location filter."""
        expected_timestamp = datetime.now()
        mock_result = Mock()
        mock_result.scalar.return_value = expected_timestamp
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_timestamp(latitude=10.0, longitude=15.0)

        assert result == expected_timestamp
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_timestamp_none(self, repository, mock_session):
        """Test getting latest timestamp when no data exists."""
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_timestamp()

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_data(self, repository, mock_session):
        """Test deleting old data."""
        mock_result = Mock()
        mock_result.rowcount = 50
        mock_session.execute.return_value = mock_result

        result = await repository.delete_old_data(days_to_keep=30)

        assert result == 50
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestProcessedClimateRepository:
    """Test ProcessedClimateRepository class to achieve comprehensive coverage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock(spec=AsyncSession)
        session.bind = Mock()
        session.bind.dialect.name = "postgresql"
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create ProcessedClimateRepository instance."""
        return ProcessedClimateRepository(mock_session)

    @pytest.fixture
    def mock_processing_result(self):
        """Create a mock ProcessingResult."""
        result = Mock(spec=ProcessingResult)
        result.spatial_bounds = {
            "north": 10.5,
            "south": 9.5,
            "east": 15.5,
            "west": 14.5,
        }
        result.file_path = "/path/to/data.nc"
        return result

    def test_processed_climate_repository_initialization(self, mock_session):
        """Test ProcessedClimateRepository initialization."""
        repo = ProcessedClimateRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_save_processing_result_empty_data(
        self, repository, mock_processing_result
    ):
        """Test saving processing result with empty DataFrame."""
        empty_df = pd.DataFrame()

        result = await repository.save_processing_result(
            mock_processing_result, empty_df
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_save_processing_result_postgresql(
        self, repository, mock_session, mock_processing_result
    ):
        """Test saving processing result with PostgreSQL."""
        data = pd.DataFrame(
            {
                "time": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
                "latitude": [10.0, 10.1],
                "longitude": [15.0, 15.1],
                "t2m_celsius": [25.5, 26.0],
                "mx2t_celsius": [30.0, 31.0],
                "mn2t_celsius": [20.0, 21.0],
                "diurnal_range": [10.0, 10.0],
                "temp_suitability": [0.8, 0.9],
                "mosquito_gdd": [15.0, 16.0],
                "tp": [0.005, 0.003],  # in meters, will be converted to mm
                "relative_humidity": [70.0, 65.0],
            }
        )

        mock_result = Mock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result

        result = await repository.save_processing_result(mock_processing_result, data)

        assert result == 2
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_processing_result_sqlite(
        self, repository, mock_session, mock_processing_result
    ):
        """Test saving processing result with SQLite."""
        mock_session.bind.dialect.name = "sqlite"

        data = pd.DataFrame(
            {
                "time": [datetime(2023, 1, 1)],
                "latitude": [10.0],
                "longitude": [15.0],
                "t2m_celsius": [25.5],
                "tp": [0.005],
            }
        )

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repository.save_processing_result(mock_processing_result, data)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_location_data(self, repository, mock_session):
        """Test getting location data."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        latitude = 10.0
        longitude = 15.0

        # Mock database records
        mock_record1 = Mock()
        mock_record1.date = datetime(2023, 1, 1)
        mock_record1.mean_temperature = 25.5
        mock_record1.max_temperature = 30.0
        mock_record1.min_temperature = 20.0
        mock_record1.temperature_suitability = 0.8
        mock_record1.daily_precipitation_mm = 5.0
        mock_record1.mean_relative_humidity = 70.0

        mock_record2 = Mock()
        mock_record2.date = datetime(2023, 1, 2)
        mock_record2.mean_temperature = 26.0
        mock_record2.max_temperature = 31.0
        mock_record2.min_temperature = 21.0
        mock_record2.temperature_suitability = 0.9
        mock_record2.daily_precipitation_mm = 3.0
        mock_record2.mean_relative_humidity = 65.0

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_record1, mock_record2]
        mock_session.execute.return_value = mock_result

        result = await repository.get_location_data(
            latitude, longitude, start_date, end_date
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == [
            "date",
            "mean_temperature",
            "max_temperature",
            "min_temperature",
            "temperature_suitability",
            "daily_precipitation_mm",
            "mean_relative_humidity",
        ]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_location_data_empty(self, repository, mock_session):
        """Test getting location data with no results."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repository.get_location_data(10.0, 15.0, start_date, end_date)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        mock_session.execute.assert_called_once()


class TestMalariaRiskRepository:
    """Test MalariaRiskRepository class to achieve comprehensive coverage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create MalariaRiskRepository instance."""
        return MalariaRiskRepository(mock_session)

    def test_malaria_risk_repository_initialization(self, mock_session):
        """Test MalariaRiskRepository initialization."""
        repo = MalariaRiskRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_save_risk_assessment(self, repository, mock_session):
        """Test saving a risk assessment."""
        assessment_date = datetime(2023, 1, 1)
        latitude = 10.0
        longitude = 15.0
        risk_data = {
            "composite_score": 0.75,
            "temp_risk": 0.8,
            "precip_risk": 0.7,
            "humidity_risk": 0.9,
            "vegetation_risk": 0.6,
            "confidence": 0.85,
            "prediction_date": datetime(2023, 1, 15),
            "time_horizon_days": 14,
            "model_type": "ml-ensemble",
            "data_sources": ["ERA5", "MODIS", "CHIRPS"],
        }

        # Mock the created risk index
        Mock()
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        await repository.save_risk_assessment(
            assessment_date, latitude, longitude, risk_data
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_risk_assessment_minimal_data(self, repository, mock_session):
        """Test saving risk assessment with minimal data."""
        assessment_date = datetime(2023, 1, 1)
        latitude = 10.0
        longitude = 15.0
        risk_data = {}  # Empty risk data, should use defaults

        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        await repository.save_risk_assessment(
            assessment_date, latitude, longitude, risk_data
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_assessment(self, repository, mock_session):
        """Test getting latest risk assessment."""
        latitude = 10.0
        longitude = 15.0

        mock_assessment = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_assessment
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_assessment(latitude, longitude)

        assert result == mock_assessment
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_assessment_none(self, repository, mock_session):
        """Test getting latest risk assessment when none exists."""
        latitude = 10.0
        longitude = 15.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_assessment(latitude, longitude)

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_risk_history(self, repository, mock_session):
        """Test getting risk assessment history."""
        latitude = 10.0
        longitude = 15.0
        days_back = 30

        mock_assessment1 = Mock()
        mock_assessment2 = Mock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            mock_assessment1,
            mock_assessment2,
        ]
        mock_session.execute.return_value = mock_result

        result = await repository.get_risk_history(latitude, longitude, days_back)

        assert result == [mock_assessment1, mock_assessment2]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_risk_history_with_buffer(self, repository, mock_session):
        """Test getting risk history with custom buffer."""
        latitude = 10.0
        longitude = 15.0
        days_back = 60
        buffer_degrees = 0.5

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repository.get_risk_history(
            latitude, longitude, days_back, buffer_degrees
        )

        assert result == []
        mock_session.execute.assert_called_once()

    def test_calculate_risk_level_low(self, repository):
        """Test risk level calculation for low risk."""
        result = repository._calculate_risk_level(0.1)
        assert result == "low"

    def test_calculate_risk_level_medium(self, repository):
        """Test risk level calculation for medium risk."""
        result = repository._calculate_risk_level(0.3)
        assert result == "medium"

    def test_calculate_risk_level_high(self, repository):
        """Test risk level calculation for high risk."""
        result = repository._calculate_risk_level(0.6)
        assert result == "high"

    def test_calculate_risk_level_critical(self, repository):
        """Test risk level calculation for critical risk."""
        result = repository._calculate_risk_level(0.9)
        assert result == "critical"

    def test_calculate_risk_level_boundary_conditions(self, repository):
        """Test risk level calculation at boundary conditions."""
        assert repository._calculate_risk_level(0.0) == "low"
        assert repository._calculate_risk_level(0.24) == "low"
        assert repository._calculate_risk_level(0.25) == "medium"
        assert repository._calculate_risk_level(0.49) == "medium"
        assert repository._calculate_risk_level(0.5) == "high"
        assert repository._calculate_risk_level(0.74) == "high"
        assert repository._calculate_risk_level(0.75) == "critical"
        assert repository._calculate_risk_level(1.0) == "critical"
