"""
Simple integration tests for database repositories using real SQLite database.

This module demonstrates an alternative testing approach that uses a real
database instead of complex SQLAlchemy mocking. These tests provide more
confidence that the actual database operations work correctly.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pandas as pd
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_era5_repository_basic_operations(integration_era5_repository):
    """Test basic ERA5 repository operations with real database."""
    repo = integration_era5_repository

    # Test data
    test_data = [
        {
            "timestamp": datetime.now(UTC),
            "latitude": 40.7128,
            "longitude": -74.0060,
            "temperature_2m": 20.5,
            "temperature_2m_max": 25.0,
            "temperature_2m_min": 15.0,
            "total_precipitation": 0.001,
        }
    ]

    # Test bulk insert
    result = await repo.bulk_insert_data_points(test_data, upsert=False)
    assert result == 1

    # Test get latest timestamp
    latest = await repo.get_latest_timestamp()
    assert latest is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_climate_repository_save_and_retrieve(integration_climate_repository):
    """Test ProcessedClimateRepository save and retrieve operations."""
    repo = integration_climate_repository

    # Create mock processing result
    mock_result = Mock()
    mock_result.spatial_bounds = {"north": 40.7128, "west": -74.0060}
    mock_result.file_path = "/test/path"

    # Create test DataFrame
    test_data = pd.DataFrame(
        {
            "time": [datetime.now(UTC)],
            "latitude": [40.7128],
            "longitude": [-74.0060],
            "t2m_celsius": [20.5],
            "mx2t_celsius": [25.0],
            "mn2t_celsius": [15.0],
            "tp": [0.001],  # In meters
        }
    )

    # Test save operation
    result = await repo.save_processing_result(mock_result, test_data)
    assert result == 1

    # Test retrieve operation
    records = await repo.get_latest_processed_data(
        latitude=40.7128, longitude=-74.0060, limit=10
    )
    assert len(records) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_risk_repository_crud_operations(integration_risk_repository):
    """Test MalariaRiskRepository CRUD operations."""
    repo = integration_risk_repository

    # Test data
    risk_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "risk_level": "medium",
        "risk_score": 0.65,
        "assessment_date": datetime.now(UTC),
    }

    # Test store operation
    assessment_id = await repo.store_risk_assessment(risk_data)
    assert assessment_id is not None

    # Test get latest assessment
    latest = await repo.get_latest_assessment(latitude=40.7128, longitude=-74.0060)
    assert latest is not None
    assert latest.risk_level == "medium"

    # Test risk history
    history = await repo.get_risk_history(
        latitude=40.7128, longitude=-74.0060, days_back=30
    )
    assert len(history) >= 1

    # Test get current risk levels for multiple locations
    locations = [(40.7128, -74.0060), (34.0522, -118.2437)]
    current_levels = await repo.get_current_risk_levels(locations)
    assert len(current_levels) >= 1

    # Test update assessment
    updated_data = {"risk_level": "high", "risk_score": 0.85}
    rows_updated = await repo.update_risk_assessment(assessment_id, updated_data)
    assert rows_updated == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repository_transaction_isolation(
    integration_era5_repository, test_db_session
):
    """Test that repository operations are properly isolated in transactions."""
    repo = integration_era5_repository

    # Insert test data
    test_data = [
        {
            "timestamp": datetime.now(UTC),
            "latitude": 1.0,
            "longitude": 1.0,
            "temperature_2m": 30.0,
        }
    ]

    await repo.bulk_insert_data_points(test_data)

    # Data should be visible within the same session
    latest = await repo.get_latest_timestamp(latitude=1.0, longitude=1.0)
    assert latest is not None

    # Rollback should happen automatically after test
    # This is handled by the test_db_session fixture
