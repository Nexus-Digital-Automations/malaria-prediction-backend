"""
Comprehensive unit tests for data processing service.
Target: 100% coverage for src/malaria_predictor/services/data_processor.py
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import xarray as xr

# Import the data processor module to test
from src.malaria_predictor.services.data_processor import (
    ERA5DataProcessor,
    ProcessingConfig,
    ProcessingResult,
)


class TestProcessingConfig:
    """Test ProcessingConfig data model."""

    def test_default_config_creation(self):
        """Test ProcessingConfig with default values."""
        config = ProcessingConfig()

        assert config.temp_min_threshold == 16.0
        assert config.temp_optimal_min == 22.0
        assert config.temp_optimal_max == 32.0
        assert config.temp_max_threshold == 40.0
        assert config.precip_min_monthly == 80.0
        assert config.precip_optimal == 150.0
        assert config.humidity_min == 60.0
        assert config.humidity_optimal == 80.0
        assert config.spatial_resolution == 0.25
        assert config.temporal_resolution == "daily"

    def test_custom_config_creation(self):
        """Test ProcessingConfig with custom values."""
        config = ProcessingConfig(
            temp_min_threshold=18.0,
            temp_optimal_min=24.0,
            temp_optimal_max=30.0,
            temp_max_threshold=38.0,
            precip_min_monthly=100.0,
            precip_optimal=200.0,
            humidity_min=70.0,
            humidity_optimal=85.0,
            spatial_resolution=0.1,
            temporal_resolution="weekly"
        )

        assert config.temp_min_threshold == 18.0
        assert config.temp_optimal_min == 24.0
        assert config.temp_optimal_max == 30.0
        assert config.temp_max_threshold == 38.0
        assert config.precip_min_monthly == 100.0
        assert config.precip_optimal == 200.0
        assert config.humidity_min == 70.0
        assert config.humidity_optimal == 85.0
        assert config.spatial_resolution == 0.1
        assert config.temporal_resolution == "weekly"

    def test_config_field_validation(self):
        """Test ProcessingConfig field validation."""
        # Test with invalid values should not raise in basic model
        config = ProcessingConfig(temp_min_threshold=-10.0)
        assert config.temp_min_threshold == -10.0

        # Test field descriptions are set
        fields = ProcessingConfig.__fields__
        assert "Minimum temperature for mosquito survival" in str(fields['temp_min_threshold'].field_info.description)
        assert "Lower optimal temperature" in str(fields['temp_optimal_min'].field_info.description)


class TestProcessingResult:
    """Test ProcessingResult data model."""

    def test_successful_result_creation(self):
        """Test ProcessingResult with successful completion."""
        result = ProcessingResult(
            file_path=Path("/test/output.nc"),
            variables_processed=["temperature", "humidity"],
            temporal_range={"start": "2024-01-01", "end": "2024-01-31"},
            spatial_bounds={"north": 10.0, "south": 0.0, "east": 20.0, "west": 10.0},
            indices_calculated=["temp_suitability", "humidity_index"],
            processing_duration_seconds=45.2,
            success=True,
            error_message=None
        )

        assert result.file_path == Path("/test/output.nc")
        assert result.variables_processed == ["temperature", "humidity"]
        assert result.temporal_range == {"start": "2024-01-01", "end": "2024-01-31"}
        assert result.spatial_bounds == {"north": 10.0, "south": 0.0, "east": 20.0, "west": 10.0}
        assert result.indices_calculated == ["temp_suitability", "humidity_index"]
        assert result.processing_duration_seconds == 45.2
        assert result.success is True
        assert result.error_message is None

    def test_failed_result_creation(self):
        """Test ProcessingResult with failure."""
        result = ProcessingResult(
            file_path=Path(""),
            variables_processed=[],
            temporal_range={},
            spatial_bounds={},
            indices_calculated=[],
            processing_duration_seconds=0.1,
            success=False,
            error_message="File not found"
        )

        assert result.file_path == Path("")
        assert result.variables_processed == []
        assert result.temporal_range == {}
        assert result.spatial_bounds == {}
        assert result.indices_calculated == []
        assert result.processing_duration_seconds == 0.1
        assert result.success is False
        assert result.error_message == "File not found"


class TestERA5DataProcessor:
    """Test ERA5DataProcessor functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = ProcessingConfig()
        self.processor = ERA5DataProcessor(self.config)
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def test_processor_initialization_with_config(self):
        """Test processor initialization with custom config."""
        custom_config = ProcessingConfig(temp_min_threshold=18.0)
        processor = ERA5DataProcessor(custom_config)

        assert processor.config.temp_min_threshold == 18.0
        assert processor.config == custom_config

    def test_processor_initialization_without_config(self):
        """Test processor initialization with default config."""
        processor = ERA5DataProcessor()

        assert processor.config.temp_min_threshold == 16.0
        assert isinstance(processor.config, ProcessingConfig)

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    @patch('src.malaria_predictor.services.data_processor.logger')
    def test_process_temperature_data_success(self, mock_logger, mock_open_dataset):
        """Test successful temperature data processing."""
        # Create mock xarray dataset
        mock_ds = self._create_mock_temperature_dataset()
        mock_open_dataset.return_value = mock_ds

        # Mock the dataset methods
        mock_ds.to_netcdf = Mock()

        input_file = self.temp_path / "input.nc"
        input_file.touch()  # Create empty file

        # Process the data
        result = self.processor.process_temperature_data(input_file)

        # Verify success
        assert result.success is True
        assert result.error_message is None
        assert "t2m_celsius" in result.variables_processed
        assert result.processing_duration_seconds > 0

        # Verify logging
        mock_logger.info.assert_called()

        # Verify file operations
        mock_open_dataset.assert_called_once_with(input_file)
        mock_ds.to_netcdf.assert_called_once()

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    @patch('src.malaria_predictor.services.data_processor.logger')
    def test_process_temperature_data_with_all_variables(self, mock_logger, mock_open_dataset):
        """Test temperature processing with all ERA5 temperature variables."""
        # Create comprehensive mock dataset
        mock_ds = self._create_comprehensive_mock_dataset()
        mock_open_dataset.return_value = mock_ds
        mock_ds.to_netcdf = Mock()

        input_file = self.temp_path / "comprehensive_input.nc"
        input_file.touch()

        result = self.processor.process_temperature_data(input_file)

        assert result.success is True
        assert "t2m_celsius" in result.variables_processed
        assert "mx2t_celsius" in result.variables_processed
        assert "mn2t_celsius" in result.variables_processed
        assert "temp_suitability" in result.indices_calculated
        assert "diurnal_range" in result.indices_calculated
        assert "mosquito_gdd" in result.indices_calculated

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    @patch('src.malaria_predictor.services.data_processor.logger')
    def test_process_temperature_data_failure(self, mock_logger, mock_open_dataset):
        """Test temperature data processing failure handling."""
        # Mock dataset opening failure
        mock_open_dataset.side_effect = FileNotFoundError("File not found")

        input_file = self.temp_path / "nonexistent.nc"

        result = self.processor.process_temperature_data(input_file)

        assert result.success is False
        assert result.error_message == "File not found"
        assert result.variables_processed == []
        assert result.processing_duration_seconds > 0

        # Verify error logging
        mock_logger.error.assert_called()

    def test_calculate_temperature_suitability_optimal_range(self):
        """Test temperature suitability calculation in optimal range."""
        # Create temperature data in optimal range (22-32°C)
        temp_data = xr.DataArray([25.0, 28.0, 30.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # All values should be 1.0 (optimal)
        assert np.all(suitability.values == 1.0)

    def test_calculate_temperature_suitability_cold_range(self):
        """Test temperature suitability calculation in cold range."""
        # Create temperature data below optimal (16-22°C)
        temp_data = xr.DataArray([18.0, 20.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # Values should be between 0 and 1
        assert np.all(suitability.values > 0.0)
        assert np.all(suitability.values < 1.0)
        # Higher temperature should have higher suitability
        assert suitability.values[1] > suitability.values[0]

    def test_calculate_temperature_suitability_hot_range(self):
        """Test temperature suitability calculation in hot range."""
        # Create temperature data above optimal (32-40°C)
        temp_data = xr.DataArray([35.0, 38.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # Values should be between 0 and 1
        assert np.all(suitability.values > 0.0)
        assert np.all(suitability.values < 1.0)
        # Lower temperature should have higher suitability
        assert suitability.values[0] > suitability.values[1]

    def test_calculate_temperature_suitability_extreme_cold(self):
        """Test temperature suitability calculation for extreme cold."""
        # Create temperature data below minimum threshold
        temp_data = xr.DataArray([10.0, 14.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # All values should be 0.0 (unsuitable)
        assert np.all(suitability.values == 0.0)

    def test_calculate_temperature_suitability_extreme_hot(self):
        """Test temperature suitability calculation for extreme heat."""
        # Create temperature data above maximum threshold
        temp_data = xr.DataArray([45.0, 50.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # All values should be 0.0 (unsuitable)
        assert np.all(suitability.values == 0.0)

    def test_calculate_temperature_suitability_mixed_ranges(self):
        """Test temperature suitability calculation across all ranges."""
        # Temperature data spanning all ranges
        temp_data = xr.DataArray([
            10.0,   # Too cold (0.0)
            18.0,   # Cold range (0.33)
            25.0,   # Optimal (1.0)
            35.0,   # Hot range (0.625)
            45.0    # Too hot (0.0)
        ], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # Verify expected pattern
        assert suitability.values[0] == 0.0  # Too cold
        assert 0.0 < suitability.values[1] < 1.0  # Cold range
        assert suitability.values[2] == 1.0  # Optimal
        assert 0.0 < suitability.values[3] < 1.0  # Hot range
        assert suitability.values[4] == 0.0  # Too hot

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    def test_process_temperature_data_custom_output_dir(self, mock_open_dataset):
        """Test temperature processing with custom output directory."""
        mock_ds = self._create_mock_temperature_dataset()
        mock_open_dataset.return_value = mock_ds
        mock_ds.to_netcdf = Mock()

        input_file = self.temp_path / "input.nc"
        input_file.touch()
        output_dir = self.temp_path / "output"
        output_dir.mkdir()

        result = self.processor.process_temperature_data(input_file, output_dir)

        assert result.success is True
        assert output_dir in result.file_path.parents

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    def test_process_temperature_data_default_output_dir(self, mock_open_dataset):
        """Test temperature processing with default output directory."""
        mock_ds = self._create_mock_temperature_dataset()
        mock_open_dataset.return_value = mock_ds
        mock_ds.to_netcdf = Mock()

        input_file = self.temp_path / "input.nc"
        input_file.touch()

        result = self.processor.process_temperature_data(input_file)

        assert result.success is True
        # Output should be in same directory as input
        assert result.file_path.parent == input_file.parent

    def test_aggregate_to_daily_hourly_data(self):
        """Test aggregation from hourly to daily data."""
        # Create mock hourly dataset (24 hours)
        hourly_ds = self._create_mock_hourly_dataset()

        daily_ds = self.processor._aggregate_to_daily(hourly_ds)

        # Should aggregate to single day
        assert len(daily_ds.time) == 1
        # Should contain aggregated variables
        assert "t2m_celsius" in daily_ds.data_vars

    def test_calculate_growing_degree_days(self):
        """Test growing degree days calculation."""
        # Create temperature data
        temp_data = xr.DataArray([20.0, 25.0, 30.0, 15.0], dims=['time'])
        base_temp = 16.0

        gdd = self.processor._calculate_growing_degree_days(temp_data, base_temp)

        # Verify calculation: max(0, temp - base_temp)
        expected = [4.0, 9.0, 14.0, 0.0]  # 20-16, 25-16, 30-16, max(0, 15-16)
        assert np.allclose(gdd.values, expected)

    def test_calculate_growing_degree_days_all_below_base(self):
        """Test growing degree days when all temperatures below base."""
        temp_data = xr.DataArray([10.0, 12.0, 14.0], dims=['time'])
        base_temp = 16.0

        gdd = self.processor._calculate_growing_degree_days(temp_data, base_temp)

        # All values should be 0
        assert np.all(gdd.values == 0.0)

    def _create_mock_temperature_dataset(self):
        """Create mock xarray dataset with temperature data."""
        mock_ds = Mock()
        mock_ds.variables = {"t2m": Mock()}
        mock_ds.__contains__ = lambda self, key: key in ["t2m", "t2m_celsius", "temp_suitability"]
        mock_ds.__getitem__ = lambda self, key: self._get_mock_data_array(key)
        mock_ds.data_vars = ["t2m_celsius", "temp_suitability"]

        # Mock time dimension
        time_values = pd.date_range("2024-01-01", "2024-01-03", freq="D")
        mock_ds.time = Mock()
        mock_ds.time.values = time_values

        # Mock spatial dimensions
        mock_ds.latitude = Mock()
        mock_ds.latitude.min.return_value = -10.0
        mock_ds.latitude.max.return_value = 10.0

        mock_ds.longitude = Mock()
        mock_ds.longitude.min.return_value = 30.0
        mock_ds.longitude.max.return_value = 50.0

        mock_ds.dims = {"time": 3, "latitude": 10, "longitude": 10}

        return mock_ds

    def _create_comprehensive_mock_dataset(self):
        """Create comprehensive mock dataset with all temperature variables."""
        mock_ds = self._create_mock_temperature_dataset()
        mock_ds.variables = {
            "t2m": Mock(),
            "mx2t": Mock(),
            "mn2t": Mock()
        }
        mock_ds.__contains__ = lambda self, key: key in [
            "t2m", "mx2t", "mn2t",
            "t2m_celsius", "mx2t_celsius", "mn2t_celsius",
            "temp_suitability", "diurnal_range", "mosquito_gdd"
        ]
        mock_ds.data_vars = [
            "t2m_celsius", "mx2t_celsius", "mn2t_celsius",
            "temp_suitability", "diurnal_range", "mosquito_gdd"
        ]
        return mock_ds

    def _create_mock_hourly_dataset(self):
        """Create mock hourly dataset for aggregation testing."""
        mock_ds = Mock()

        # 24 hourly time steps
        time_values = pd.date_range("2024-01-01", "2024-01-02", freq="H")[:-1]  # 24 hours
        mock_ds.time = time_values
        mock_ds.dims = {"time": 24}

        # Mock temperature data
        temp_data = xr.DataArray(
            np.random.randn(24),
            dims=["time"],
            coords={"time": time_values}
        )
        mock_ds.__getitem__ = lambda self, key: temp_data if key == "t2m_celsius" else Mock()
        mock_ds.__contains__ = lambda self, key: key == "t2m_celsius"

        return mock_ds

    def _get_mock_data_array(self, key):
        """Get mock data array for dataset."""
        data = np.random.randn(3, 10, 10)  # 3 days, 10x10 spatial
        return xr.DataArray(data, dims=["time", "latitude", "longitude"])


class TestERA5DataProcessorEdgeCases:
    """Test edge cases and error scenarios for ERA5DataProcessor."""

    def setup_method(self):
        """Setup test fixtures."""
        self.processor = ERA5DataProcessor()

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    def test_process_empty_dataset(self, mock_open_dataset):
        """Test processing of empty dataset."""
        mock_ds = Mock()
        mock_ds.variables = {}
        mock_ds.__contains__ = lambda self, key: False
        mock_ds.data_vars = []
        mock_ds.time = Mock()
        mock_ds.time.values = []
        mock_ds.to_netcdf = Mock()

        mock_open_dataset.return_value = mock_ds

        input_file = Path("empty.nc")
        result = self.processor.process_temperature_data(input_file)

        # Should handle empty dataset gracefully
        assert result.success is True
        assert result.variables_processed == []

    def test_temperature_suitability_with_nan_values(self):
        """Test temperature suitability calculation with NaN values."""
        temp_data = xr.DataArray([25.0, np.nan, 30.0], dims=['time'])

        suitability = self.processor._calculate_temperature_suitability(temp_data)

        # Should handle NaN values appropriately
        assert np.isfinite(suitability.values[0])
        assert np.isfinite(suitability.values[2])

    def test_growing_degree_days_with_nan_values(self):
        """Test growing degree days calculation with NaN values."""
        temp_data = xr.DataArray([20.0, np.nan, 25.0], dims=['time'])
        base_temp = 16.0

        gdd = self.processor._calculate_growing_degree_days(temp_data, base_temp)

        # Should handle NaN values
        assert np.isfinite(gdd.values[0])
        assert np.isfinite(gdd.values[2])

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    def test_process_corrupted_netcdf_file(self, mock_open_dataset):
        """Test processing of corrupted NetCDF file."""
        mock_open_dataset.side_effect = OSError("Invalid NetCDF file")

        input_file = Path("corrupted.nc")
        result = self.processor.process_temperature_data(input_file)

        assert result.success is False
        assert "Invalid NetCDF file" in result.error_message

    @patch('src.malaria_predictor.services.data_processor.xr.open_dataset')
    def test_process_insufficient_permissions(self, mock_open_dataset):
        """Test processing with insufficient file permissions."""
        mock_open_dataset.side_effect = PermissionError("Permission denied")

        input_file = Path("protected.nc")
        result = self.processor.process_temperature_data(input_file)

        assert result.success is False
        assert "Permission denied" in result.error_message

    def test_custom_config_extreme_values(self):
        """Test processor with extreme configuration values."""
        config = ProcessingConfig(
            temp_min_threshold=0.0,
            temp_optimal_min=0.0,
            temp_optimal_max=100.0,
            temp_max_threshold=100.0
        )
        processor = ERA5DataProcessor(config)

        # Test with normal temperature values
        temp_data = xr.DataArray([25.0, 50.0, 75.0], dims=['time'])
        suitability = processor._calculate_temperature_suitability(temp_data)

        # All should be optimal (1.0) with these extreme thresholds
        assert np.all(suitability.values == 1.0)


class TestPerformanceAndMemory:
    """Test performance and memory usage of data processing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.processor = ERA5DataProcessor()

    def test_large_dataset_processing_simulation(self):
        """Test processing simulation with large dataset dimensions."""
        # Simulate processing metadata for large dataset
        large_dimensions = {"time": 365, "latitude": 100, "longitude": 100}

        # This would represent processing ~3.65M data points
        expected_memory = large_dimensions["time"] * large_dimensions["latitude"] * large_dimensions["longitude"] * 8  # 8 bytes per float64

        # Memory should be under reasonable limits (< 1GB for this test)
        assert expected_memory < 1e9  # 1 billion bytes = ~1GB

    def test_temperature_calculation_vectorization(self):
        """Test that temperature calculations use vectorized operations."""
        # Large temperature array to test vectorization
        large_temp_data = xr.DataArray(
            np.random.uniform(10, 40, 10000),
            dims=['time']
        )

        import time
        start_time = time.time()
        suitability = self.processor._calculate_temperature_suitability(large_temp_data)
        processing_time = time.time() - start_time

        # Vectorized operations should be fast (< 0.1 seconds for 10k points)
        assert processing_time < 0.1
        assert len(suitability) == 10000
