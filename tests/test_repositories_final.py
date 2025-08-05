"""
Final test to achieve 100% coverage for repositories.py.

This test specifically targets the missing lines 283-298 in the get_location_data method.
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, "src")


class TestRepositoriesFinalCoverage:
    """Final tests to achieve 100% repositories.py coverage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_processed_climate_get_location_data_with_results(self, mock_session):
        """Test get_location_data with results - covers lines 283-298."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        # Create mock data objects that match the expected structure
        mock_data_obj = Mock()
        mock_data_obj.date = datetime(2024, 1, 15).date()
        mock_data_obj.mean_temperature = 25.5
        mock_data_obj.max_temperature = 30.2
        mock_data_obj.min_temperature = 20.1
        mock_data_obj.temperature_suitability = 0.85
        mock_data_obj.daily_precipitation_mm = 5.2
        mock_data_obj.mean_relative_humidity = 72.3

        # Mock the database query result properly
        mock_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = [
            mock_data_obj
        ]  # Return data to trigger lines 283-296
        mock_result.scalars.return_value = mock_scalars

        # Make execute return the result directly
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Create repository and call method
        repo = ProcessedClimateRepository(mock_session)
        result = await repo.get_location_data(
            latitude=10.5,
            longitude=-1.5,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )

        # Verify the DataFrame was created properly (lines 283-296 executed)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result) == 1

        # Verify the data conversion worked correctly
        row = result.iloc[0]
        assert row["date"] == datetime(2024, 1, 15).date()
        assert row["mean_temperature"] == 25.5
        assert row["max_temperature"] == 30.2
        assert row["min_temperature"] == 20.1
        assert row["temperature_suitability"] == 0.85
        assert row["daily_precipitation_mm"] == 5.2
        assert row["mean_relative_humidity"] == 72.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
