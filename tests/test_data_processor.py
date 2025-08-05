"""Tests for the data processing service.

This module tests the ERA5 data processor functionality including
temperature suitability calculations, temporal aggregation, and
malaria risk index computation.
"""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from malaria_predictor.services.data_processor import (
    ERA5DataProcessor,
    ProcessingConfig,
)


class TestProcessingConfig:
    """Test cases for ProcessingConfig validation."""

    def test_default_config_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()

        assert config.temp_min_threshold == 16.0
        assert config.temp_optimal_min == 22.0
        assert config.temp_optimal_max == 32.0
        assert config.temp_max_threshold == 40.0
        assert config.precip_min_monthly == 80.0
        assert config.precip_optimal == 150.0
        assert config.humidity_min == 60.0
        assert config.humidity_optimal == 80.0

    def test_custom_config_values(self):
        """Test custom configuration values."""
        config = ProcessingConfig(
            temp_optimal_min=20.0, temp_optimal_max=35.0, precip_optimal=200.0
        )

        assert config.temp_optimal_min == 20.0
        assert config.temp_optimal_max == 35.0
        assert config.precip_optimal == 200.0


class TestERA5DataProcessor:
    """Test cases for ERA5DataProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return ERA5DataProcessor()

    @pytest.fixture
    def sample_temperature_data(self):
        """Create sample temperature dataset."""
        # Create time coordinates
        times = pd.date_range("2023-01-01", periods=24, freq="h")
        lats = np.linspace(-10, 10, 5)
        lons = np.linspace(20, 40, 5)

        # Create temperature data in Kelvin
        temp_data = np.random.normal(298, 5, (24, 5, 5))  # ~25°C

        ds = xr.Dataset(
            {
                "t2m": (["time", "latitude", "longitude"], temp_data),
                "mx2t": (["time", "latitude", "longitude"], temp_data + 5),
                "mn2t": (["time", "latitude", "longitude"], temp_data - 5),
            },
            coords={"time": times, "latitude": lats, "longitude": lons},
        )

        return ds

    def test_processor_initialization(self):
        """Test processor initialization with default and custom config."""
        # Default config
        processor1 = ERA5DataProcessor()
        assert processor1.config.temp_optimal_min == 22.0

        # Custom config
        custom_config = ProcessingConfig(temp_optimal_min=20.0)
        processor2 = ERA5DataProcessor(custom_config)
        assert processor2.config.temp_optimal_min == 20.0

    def test_temperature_suitability_calculation(self, processor):
        """Test temperature suitability index calculation."""
        # Test temperatures in Celsius
        test_temps = xr.DataArray([10, 18, 25, 30, 35, 45])  # Various temperatures

        suitability = processor._calculate_temperature_suitability(test_temps)

        # Check suitability values
        assert suitability[0] == 0  # 10°C - too cold
        assert 0 < suitability[1] < 1  # 18°C - cold but suitable
        assert suitability[2] == 1  # 25°C - optimal
        assert suitability[3] == 1  # 30°C - optimal
        assert 0 < suitability[4] < 1  # 35°C - hot but suitable
        assert suitability[5] == 0  # 45°C - too hot

    def test_growing_degree_days_calculation(self, processor):
        """Test growing degree days calculation."""
        temps = xr.DataArray([10, 15, 20, 25, 30])
        base_temp = 16.0

        gdd = processor._calculate_growing_degree_days(temps, base_temp)

        assert gdd[0] == 0  # 10°C < 16°C base
        assert gdd[1] == 0  # 15°C < 16°C base
        assert gdd[2] == 4  # 20°C - 16°C = 4
        assert gdd[3] == 9  # 25°C - 16°C = 9
        assert gdd[4] == 14  # 30°C - 16°C = 14

    @patch("xarray.open_dataset")
    def test_process_temperature_data_success(
        self, mock_open_dataset, processor, sample_temperature_data, tmp_path
    ):
        """Test successful temperature data processing."""
        mock_open_dataset.return_value = sample_temperature_data

        input_file = Path("test_input.nc")
        output_dir = tmp_path

        # Patch to_netcdf on the actual dataset instance that will be created
        with patch("xarray.Dataset.to_netcdf"):
            result = processor.process_temperature_data(input_file, output_dir)

        assert result.success is True
        assert len(result.variables_processed) > 0
        assert "temp_suitability" in result.indices_calculated
        assert result.processing_duration_seconds > 0

    def test_aggregate_to_daily(self, processor, sample_temperature_data):
        """Test aggregation from hourly to daily data."""
        daily_ds = processor._aggregate_to_daily(sample_temperature_data)

        # Check that time dimension was reduced
        assert len(daily_ds.time) == 1  # 24 hours -> 1 day

        # Check aggregation methods
        assert "t2m" in daily_ds  # Should be mean
        assert "mx2t" in daily_ds  # Should be max
        assert "mn2t" in daily_ds  # Should be min

    def test_precipitation_risk_calculation(self, processor):
        """Test precipitation risk factor calculation."""
        # Test various precipitation amounts (mm/month)
        precip_values = xr.DataArray([0, 50, 80, 150, 300, 500])

        risk = processor._calculate_precipitation_risk(precip_values).values

        assert risk[0] == 0  # 0mm - too dry
        assert risk[1] == 0  # 50mm - below threshold
        assert risk[2] > 0  # 80mm - at minimum threshold
        assert risk[3] == 1  # 150mm - optimal
        assert risk[4] == 0  # 300mm - too far from optimal
        assert risk[5] == 0.5  # 500mm - excessive rain

    def test_relative_humidity_calculation(self, processor):
        """Test relative humidity calculation from dewpoint and temperature."""
        # Test with known values
        temp_k = xr.DataArray([293.15])  # 20°C
        dewpoint_k = xr.DataArray([283.15])  # 10°C

        rh = processor._calculate_relative_humidity(dewpoint_k, temp_k)

        # RH should be between 0 and 100
        assert 0 <= float(rh) <= 100
        # At 20°C with 10°C dewpoint, RH should be around 50-55%
        assert 45 <= float(rh) <= 60

    def test_humidity_risk_calculation(self, processor):
        """Test humidity risk factor calculation."""
        # Test various humidity levels
        humidity_values = xr.DataArray([30, 50, 60, 70, 80, 90])

        risk = processor._calculate_humidity_risk(humidity_values).values

        assert risk[0] == 0  # 30% - too dry
        assert risk[1] == 0  # 50% - too dry
        assert risk[2] == 0  # 60% - at minimum threshold (but factor is 0)
        assert risk[3] > 0  # 70% - above minimum
        assert risk[4] == 0.9  # 80% - optimal
        assert risk[5] == 0.9  # 90% - still good

    @patch("xarray.open_dataset")
    def test_calculate_composite_risk_index(self, mock_open_dataset, processor):
        """Test composite malaria risk index calculation."""
        # Create time dimension for proper dataset
        times = pd.date_range("2023-01-01", periods=1, freq="D")

        # Create mock processed data with risk components
        mock_data = xr.Dataset(
            {
                "temp_suitability": xr.DataArray(
                    [0.8], dims=["time"], coords={"time": times}
                ),
                "t2m": xr.DataArray([298.15], dims=["time"], coords={"time": times}),
                "d2m": xr.DataArray([293.15], dims=["time"], coords={"time": times}),
                "tp": xr.DataArray(
                    [0.005], dims=["time"], coords={"time": times}
                ),  # 5mm in meters
            }
        )
        mock_open_dataset.return_value = mock_data

        result_ds = processor.calculate_composite_risk_index(Path("test.nc"))

        # Check that malaria risk index was calculated
        assert "malaria_risk_index" in result_ds
        # Risk should be between 0 and 1
        assert 0 <= float(result_ds["malaria_risk_index"].values[0]) <= 1

    @patch("xarray.open_dataset")
    def test_extract_location_timeseries(self, mock_open_dataset, processor):
        """Test extraction of time series for a specific location."""
        # Create mock data with spatial dimensions
        times = pd.date_range("2023-01-01", periods=7, freq="D")
        lats = np.array([-1, 0, 1])
        lons = np.array([29, 30, 31])

        temp_data = np.random.normal(25, 2, (7, 3, 3))

        mock_ds = xr.Dataset(
            {"t2m_celsius": (["time", "latitude", "longitude"], temp_data)},
            coords={"time": times, "latitude": lats, "longitude": lons},
        )
        mock_open_dataset.return_value = mock_ds

        # Extract data for location (0°, 30°)
        df = processor.extract_location_timeseries(
            Path("test.nc"), latitude=0, longitude=30, buffer_degrees=1
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 7  # 7 days
        assert "t2m_celsius" in df.columns

    def test_process_temperature_data_error_handling(self, processor):
        """Test error handling in temperature data processing."""
        # Test with non-existent file
        result = processor.process_temperature_data(Path("non_existent.nc"))

        assert result.success is False
        assert result.error_message is not None
        assert result.processing_duration_seconds > 0


if __name__ == "__main__":
    pytest.main([__file__])
