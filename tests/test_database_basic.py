"""Basic database tests to improve coverage."""

from datetime import datetime
from unittest.mock import Mock, patch

from malaria_predictor.database.models import (
    ERA5DataPoint,
    MalariaRiskIndex,
    ProcessedClimateData,
)


def test_era5_data_point_creation():
    """Test ERA5DataPoint model creation."""
    data_point = ERA5DataPoint(
        timestamp=datetime.now(),
        latitude=5.0,
        longitude=35.0,
        temperature_2m=25.5,
        precipitation=10.2,
        humidity=75.0,
        wind_speed=3.2,
        pressure=1013.25,
        source="ERA5",
        file_reference="test_file.nc",
    )

    assert data_point.latitude == 5.0
    assert data_point.longitude == 35.0
    assert data_point.temperature_2m == 25.5
    assert data_point.source == "ERA5"


def test_processed_climate_data_creation():
    """Test ProcessedClimateData model creation."""
    climate_data = ProcessedClimateData(
        date=datetime.now().date(),
        latitude=5.0,
        longitude=35.0,
        avg_temperature=26.5,
        total_precipitation=15.3,
        avg_humidity=80.0,
        temperature_range=8.5,
        precipitation_anomaly=2.1,
        drought_index=0.3,
        heat_index=28.2,
    )

    assert climate_data.avg_temperature == 26.5
    assert climate_data.total_precipitation == 15.3
    assert climate_data.drought_index == 0.3


def test_malaria_risk_index_creation():
    """Test MalariaRiskIndex model creation."""
    risk_index = MalariaRiskIndex(
        date=datetime.now().date(),
        latitude=5.0,
        longitude=35.0,
        risk_score=0.75,
        environmental_factors={
            "temperature": 0.8,
            "precipitation": 0.7,
            "humidity": 0.8,
        },
        population_density=150.5,
        vector_presence=True,
        risk_category="High",
    )

    assert risk_index.risk_score == 0.75
    assert risk_index.risk_category == "High"
    assert risk_index.vector_presence is True


def test_era5_data_point_repr():
    """Test ERA5DataPoint string representation."""
    data_point = ERA5DataPoint(
        timestamp=datetime(2023, 6, 15, 12, 0),
        latitude=5.0,
        longitude=35.0,
        temperature_2m=25.5,
        source="ERA5",
    )

    repr_str = str(data_point)
    assert "ERA5DataPoint" in repr_str
    assert "2023-06-15" in repr_str


@patch("malaria_predictor.database.session.create_engine")
def test_session_creation_basic(mock_create_engine):
    """Test basic session creation."""
    from malaria_predictor.database.session import get_session

    # Mock engine and session
    mock_engine = Mock()
    mock_session = Mock()
    mock_create_engine.return_value = mock_engine

    with patch(
        "malaria_predictor.database.session.async_sessionmaker"
    ) as mock_sessionmaker:
        mock_sessionmaker.return_value = lambda: mock_session

        # This will test import and basic structure
        assert get_session is not None


def test_model_table_names():
    """Test that models have correct table names."""
    assert ERA5DataPoint.__tablename__ == "era5_data_points"
    assert ProcessedClimateData.__tablename__ == "processed_climate_data"
    assert MalariaRiskIndex.__tablename__ == "malaria_risk_indices"
