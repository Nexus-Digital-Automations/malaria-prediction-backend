"""
Comprehensive Enterprise-Grade Test Suite for ERA5 Climate Data Client.

This module provides extensive testing for the ERA5Client class covering:
- Authentication methods (config_file, environment, explicit)
- Variable and regional preset resolution
- Climate data downloads with CDS API mocking
- Physical range validation for 7 variables
- Temporal aggregation (daily, monthly, seasonal)
- Point data extraction with buffer logic
- Retry mechanism with exponential backoff
- File validation and quality scoring
- NetCDF operations and attribute preservation
- Error handling and edge cases

Target: Increase coverage from 14.39% to 80%+ for era5_client.py
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from malaria_predictor.services.era5_client import (
    ERA5Client,
    ERA5DownloadResult,
    ERA5RequestConfig,
)


# ========================================================================================
# FIXTURES AND TEST DATA
# ========================================================================================


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create temporary download directory for ERA5 tests."""
    download_dir = tmp_path / "era5_downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture
def sample_era5_netcdf(tmp_path):
    """Create sample NetCDF file mimicking ERA5 climate data structure."""
    file_path = tmp_path / "sample_era5.nc"

    # Create sample data with realistic ERA5 structure
    times = pd.date_range('2023-01-01', periods=7, freq='D')
    lats = np.linspace(-10, 10, 20)
    lons = np.linspace(25, 45, 20)

    # Realistic climate variable values
    temperature = np.random.uniform(273, 310, (7, 20, 20))  # 0-37°C in Kelvin
    humidity = np.random.uniform(20, 90, (7, 20, 20))
    rainfall = np.random.uniform(0, 50, (7, 20, 20))

    ds = xr.Dataset(
        {
            't2m': (['time', 'latitude', 'longitude'], temperature),
            'r': (['time', 'latitude', 'longitude'], humidity),
            'tp': (['time', 'latitude', 'longitude'], rainfall),
        },
        coords={
            'time': times,
            'latitude': lats,
            'longitude': lons,
        },
    )

    ds.to_netcdf(file_path)
    return file_path


@pytest.fixture
def mock_cds_client():
    """Mock CDS API client for testing without real API calls."""
    with patch('malaria_predictor.services.era5_client.cdsapi.Client') as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def era5_client_with_temp_dir(temp_download_dir):
    """Create ERA5Client instance with temporary download directory."""
    # Mock cdsapi to avoid ImportError
    with patch('malaria_predictor.services.era5_client.cdsapi'):
        client = ERA5Client(download_dir=str(temp_download_dir))
        return client


# ========================================================================================
# AUTHENTICATION TESTS
# ========================================================================================


class TestAuthentication:
    """Test ERA5 authentication methods and credential handling."""

    def test_initialization_with_config_file(self, temp_download_dir):
        """Test client initialization using ~/.cdsapirc config file."""
        with patch('malaria_predictor.services.era5_client.cdsapi') as mock_cds:
            client = ERA5Client(
                download_dir=str(temp_download_dir),
                auth_method='config_file'
            )

            assert client.download_dir == Path(temp_download_dir)
            assert client.auth_method == 'config_file'
            # CDS client should be lazy-loaded (not initialized yet)
            assert client._cds_client is None

    def test_initialization_with_environment_vars(self, temp_download_dir, monkeypatch):
        """Test client initialization using environment variables."""
        monkeypatch.setenv('CDS_URL', 'https://cds.climate.copernicus.eu/api')
        monkeypatch.setenv('CDS_KEY', 'test-uid:test-api-key')

        with patch('malaria_predictor.services.era5_client.cdsapi') as mock_cds:
            client = ERA5Client(
                download_dir=str(temp_download_dir),
                auth_method='environment'
            )

            assert client.auth_method == 'environment'
            assert client._cds_client is None  # Lazy-loaded

    def test_lazy_cds_client_initialization(self, era5_client_with_temp_dir, mock_cds_client):
        """Test that CDS client is lazy-loaded on first use."""
        client = era5_client_with_temp_dir

        # Should be None before first use
        assert client._cds_client is None

        # Access the property to trigger lazy loading
        with patch.object(client, '_initialize_cds_client', return_value=mock_cds_client):
            cds_client = client.cds_client

            assert cds_client is not None
            assert client._cds_client == mock_cds_client

    def test_missing_credentials_raises_error(self, temp_download_dir, monkeypatch):
        """Test that missing credentials raise appropriate error."""
        # Remove environment variables
        monkeypatch.delenv('CDS_URL', raising=False)
        monkeypatch.delenv('CDS_KEY', raising=False)

        with patch('malaria_predictor.services.era5_client.cdsapi') as mock_cds:
            mock_cds.Client.side_effect = Exception("No credentials found")

            client = ERA5Client(download_dir=str(temp_download_dir))

            with pytest.raises(Exception, match="No credentials found"):
                _ = client.cds_client


# ========================================================================================
# VARIABLE AND REGIONAL PRESET TESTS
# ========================================================================================


class TestPresets:
    """Test variable and regional preset resolution logic."""

    def test_malaria_core_preset(self, era5_client_with_temp_dir):
        """Test malaria_core variable preset resolution."""
        client = era5_client_with_temp_dir

        variables = client._resolve_variable_preset('malaria_core')

        # Core malaria variables
        assert '2m_temperature' in variables
        assert 'total_precipitation' in variables
        assert 'relative_humidity' in variables or '2m_dewpoint_temperature' in variables

    def test_malaria_extended_preset(self, era5_client_with_temp_dir):
        """Test malaria_extended variable preset includes all core variables."""
        client = era5_client_with_temp_dir

        variables = client._resolve_variable_preset('malaria_extended')
        core_variables = client._resolve_variable_preset('malaria_core')

        # Extended should include all core variables
        for var in core_variables:
            assert var in variables

        # Extended should have more variables than core
        assert len(variables) > len(core_variables)

    def test_africa_regional_preset(self, era5_client_with_temp_dir):
        """Test Africa regional preset provides correct geographic bounds."""
        client = era5_client_with_temp_dir

        bounds = client._resolve_regional_preset('africa')

        # Africa bounds: approximately (N, W, S, E)
        assert bounds['north'] > bounds['south']
        assert bounds['east'] > bounds['west']
        assert -40 <= bounds['south'] <= 0  # Southern Africa
        assert 0 <= bounds['north'] <= 40  # Northern Africa
        assert -20 <= bounds['west'] <= 0  # West coast
        assert 30 <= bounds['east'] <= 60  # East coast

    def test_custom_variables_list(self, era5_client_with_temp_dir):
        """Test using custom variable list instead of preset."""
        client = era5_client_with_temp_dir

        custom_vars = ['2m_temperature', 'total_precipitation']
        resolved = client._resolve_variable_preset(custom_vars)

        assert resolved == custom_vars

    def test_invalid_preset_raises_error(self, era5_client_with_temp_dir):
        """Test that invalid preset name raises appropriate error."""
        client = era5_client_with_temp_dir

        with pytest.raises((ValueError, KeyError)):
            client._resolve_variable_preset('invalid_preset_name')


# ========================================================================================
# DOWNLOAD AND VALIDATION TESTS
# ========================================================================================


class TestDownloads:
    """Test climate data download workflows with mocked CDS API."""

    @pytest.mark.asyncio
    async def test_successful_download(self, era5_client_with_temp_dir, mock_cds_client, temp_download_dir):
        """Test successful climate data download."""
        client = era5_client_with_temp_dir

        # Mock CDS retrieve to create a file
        def create_mock_file(*args, **kwargs):
            target_file = kwargs.get('target', args[1] if len(args) > 1 else None)
            if target_file:
                Path(target_file).touch()
            return None

        mock_cds_client.retrieve.side_effect = create_mock_file
        client._cds_client = mock_cds_client

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 7)

        result = await client.download_climate_data(
            start_date=start_date,
            end_date=end_date,
            variables=['2m_temperature'],
            area_preset='east_africa'
        )

        assert result.success is True
        assert result.file_path is not None
        assert Path(result.file_path).exists()

    @pytest.mark.asyncio
    async def test_download_with_retry_on_failure(self, era5_client_with_temp_dir, mock_cds_client):
        """Test retry mechanism on download failure."""
        client = era5_client_with_temp_dir

        # Fail first 2 attempts, succeed on 3rd
        attempt_count = 0
        def retry_mock(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary CDS failure")
            target_file = kwargs.get('target', args[1] if len(args) > 1 else None)
            if target_file:
                Path(target_file).touch()

        mock_cds_client.retrieve.side_effect = retry_mock
        client._cds_client = mock_cds_client

        with patch('time.sleep'):  # Speed up test by mocking sleep
            result = await client.download_and_validate_climate_data(
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 7),
                variable_preset='temperature_only',
                max_retries=3
            )

        assert attempt_count == 3
        assert result.success is True


# ========================================================================================
# PHYSICAL RANGE VALIDATION TESTS
# ========================================================================================


class TestValidation:
    """Test physical range validation for ERA5 climate variables."""

    def test_temperature_validation(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test temperature within valid physical range (200-330K)."""
        client = era5_client_with_temp_dir

        validation_result = client.validate_downloaded_file(sample_era5_netcdf)

        assert validation_result['is_valid'] is True
        assert 'temperature' in validation_result['checks']
        assert validation_result['checks']['temperature']['passed'] is True

    def test_humidity_validation(self, era5_client_with_temp_dir, tmp_path):
        """Test humidity validation (0-100%)."""
        # Create NetCDF with invalid humidity
        file_path = tmp_path / "invalid_humidity.nc"
        ds = xr.Dataset({
            'r': (['time', 'lat', 'lon'], np.array([[[150.0]]]))  # >100%
        }, coords={'time': [datetime(2023, 1, 1)], 'lat': [0], 'lon': [0]})
        ds.to_netcdf(file_path)

        client = era5_client_with_temp_dir
        validation_result = client.validate_downloaded_file(file_path)

        assert validation_result['is_valid'] is False
        assert validation_result['checks']['humidity']['passed'] is False

    def test_quality_score_calculation(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test validation quality score calculation."""
        client = era5_client_with_temp_dir

        validation_result = client.validate_downloaded_file(sample_era5_netcdf)

        assert 'quality_score' in validation_result
        assert 0.0 <= validation_result['quality_score'] <= 1.0


# ========================================================================================
# TEMPORAL AGGREGATION TESTS
# ========================================================================================


class TestAggregation:
    """Test temporal aggregation methods."""

    def test_daily_to_monthly_aggregation(self, era5_client_with_temp_dir, tmp_path):
        """Test aggregation from daily to monthly data."""
        # Create daily NetCDF
        times = pd.date_range('2023-01-01', periods=31, freq='D')
        ds = xr.Dataset({
            't2m': (['time'], np.random.uniform(273, 310, 31))
        }, coords={'time': times})

        daily_file = tmp_path / "daily.nc"
        ds.to_netcdf(daily_file)

        client = era5_client_with_temp_dir
        output_file = client.aggregate_temporal_data(
            file_path=daily_file,
            aggregation_method='monthly'
        )

        assert output_file.exists()

        # Verify aggregated data
        aggregated = xr.open_dataset(output_file)
        assert len(aggregated.time) == 1  # Should have 1 month
        aggregated.close()

    def test_seasonal_aggregation(self, era5_client_with_temp_dir, tmp_path):
        """Test seasonal aggregation (DJF, MAM, JJA, SON)."""
        # Create annual NetCDF
        times = pd.date_range('2023-01-01', periods=365, freq='D')
        ds = xr.Dataset({
            't2m': (['time'], np.random.uniform(273, 310, 365))
        }, coords={'time': times})

        annual_file = tmp_path / "annual.nc"
        ds.to_netcdf(annual_file)

        client = era5_client_with_temp_dir
        output_file = client.aggregate_temporal_data(
            file_path=annual_file,
            aggregation_method='seasonal'
        )

        assert output_file.exists()

        # Verify 4 seasons
        seasonal = xr.open_dataset(output_file)
        assert len(seasonal.time) == 4
        seasonal.close()


# ========================================================================================
# POINT DATA EXTRACTION TESTS
# ========================================================================================


class TestPointExtraction:
    """Test point data extraction with buffer logic."""

    def test_extract_point_data(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test extraction of climate data for specific point."""
        client = era5_client_with_temp_dir

        lat, lon = 0.0, 35.0  # Nairobi area

        point_data = client.extract_point_data(
            file_path=sample_era5_netcdf,
            latitude=lat,
            longitude=lon,
            buffer_km=50
        )

        assert point_data is not None
        assert 't2m' in point_data or 'temperature' in point_data

    def test_buffer_logic(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test that buffer creates appropriate spatial window."""
        client = era5_client_with_temp_dir

        # Extract with different buffer sizes
        data_small = client.extract_point_data(
            sample_era5_netcdf, 0.0, 35.0, buffer_km=10
        )
        data_large = client.extract_point_data(
            sample_era5_netcdf, 0.0, 35.0, buffer_km=100
        )

        # Larger buffer should include more data points
        assert len(data_large) >= len(data_small)


# ========================================================================================
# ERROR HANDLING TESTS
# ========================================================================================


class TestErrorHandling:
    """Test error scenarios and edge cases."""

    def test_file_not_found_error(self, era5_client_with_temp_dir):
        """Test handling of non-existent file."""
        client = era5_client_with_temp_dir

        with pytest.raises(FileNotFoundError):
            client.validate_downloaded_file(Path("/nonexistent/file.nc"))

    def test_corrupt_netcdf_file(self, era5_client_with_temp_dir, tmp_path):
        """Test handling of corrupt NetCDF file."""
        corrupt_file = tmp_path / "corrupt.nc"
        corrupt_file.write_text("This is not a valid NetCDF file")

        client = era5_client_with_temp_dir

        with pytest.raises((OSError, ValueError)):
            client.validate_downloaded_file(corrupt_file)

    def test_missing_variable_in_netcdf(self, era5_client_with_temp_dir, tmp_path):
        """Test handling of NetCDF missing required variables."""
        file_path = tmp_path / "missing_var.nc"
        ds = xr.Dataset({
            'unexpected_var': (['time'], [1, 2, 3])
        }, coords={'time': pd.date_range('2023-01-01', periods=3)})
        ds.to_netcdf(file_path)

        client = era5_client_with_temp_dir
        validation_result = client.validate_downloaded_file(file_path)

        # Should mark as invalid due to missing expected variables
        assert validation_result['is_valid'] is False


# ========================================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ========================================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_day_download(self, era5_client_with_temp_dir, mock_cds_client):
        """Test download for single day (start_date == end_date)."""
        client = era5_client_with_temp_dir
        client._cds_client = mock_cds_client

        single_date = datetime(2023, 1, 1)

        # Mock CDS client
        mock_cds_client.retrieve.return_value = None

        with patch.object(Path, 'exists', return_value=True):
            result = client.download_climate_data(
                start_date=single_date,
                end_date=single_date,
                variables=['2m_temperature']
            )

        # Should handle single-day request
        mock_cds_client.retrieve.assert_called_once()

    def test_leap_year_handling(self, era5_client_with_temp_dir):
        """Test correct handling of leap year dates."""
        client = era5_client_with_temp_dir

        # February 29, 2024 (leap year)
        start_date = datetime(2024, 2, 28)
        end_date = datetime(2024, 3, 1)

        # Should not raise ValueError
        date_range = client._generate_date_range(start_date, end_date)

        assert datetime(2024, 2, 29) in date_range

    def test_zero_length_array(self, era5_client_with_temp_dir, tmp_path):
        """Test handling of empty arrays in NetCDF."""
        file_path = tmp_path / "empty.nc"
        ds = xr.Dataset({
            't2m': (['time'], np.array([]))
        }, coords={'time': []})
        ds.to_netcdf(file_path)

        client = era5_client_with_temp_dir

        # Should handle gracefully without crashing
        validation_result = client.validate_downloaded_file(file_path)
        assert validation_result['is_valid'] is False


# ========================================================================================
# PERFORMANCE AND INTEGRATION TESTS
# ========================================================================================


@pytest.mark.slow
class TestPerformance:
    """Performance tests for ERA5 client (marked slow for CI exclusion)."""

    def test_large_date_range_handling(self, era5_client_with_temp_dir):
        """Test handling of large date ranges (1 year)."""
        client = era5_client_with_temp_dir

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        date_range = client._generate_date_range(start_date, end_date)

        assert len(date_range) == 365

    def test_concurrent_validation_checks(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test that validation checks can run concurrently."""
        client = era5_client_with_temp_dir

        import time
        start_time = time.time()

        # Run validation multiple times
        for _ in range(5):
            client.validate_downloaded_file(sample_era5_netcdf)

        duration = time.time() - start_time

        # Should complete reasonably fast (not sequential delays)
        assert duration < 5.0  # seconds


# ========================================================================================
# CONFIGURATION AND REQUEST CONFIG TESTS
# ========================================================================================


class TestRequestConfig:
    """Test ERA5RequestConfig Pydantic model."""

    def test_valid_config_creation(self):
        """Test creation of valid ERA5RequestConfig."""
        config = ERA5RequestConfig(
            variables=['2m_temperature', 'total_precipitation'],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 7),
            north=10.0,
            west=30.0,
            south=-10.0,
            east=50.0
        )

        assert config.variables == ['2m_temperature', 'total_precipitation']
        assert config.start_date == datetime(2023, 1, 1)

    def test_frozen_config(self):
        """Test that ERA5RequestConfig is frozen (immutable)."""
        config = ERA5RequestConfig(
            variables=['2m_temperature'],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 7)
        )

        with pytest.raises(Exception):  # Pydantic ValidationError or AttributeError
            config.variables = ['different_variable']

    def test_invalid_date_range(self):
        """Test that end_date before start_date raises validation error."""
        with pytest.raises(ValueError):
            ERA5RequestConfig(
                variables=['2m_temperature'],
                start_date=datetime(2023, 1, 7),
                end_date=datetime(2023, 1, 1)  # Before start_date
            )


# ========================================================================================
# UTILITY METHOD TESTS
# ========================================================================================


class TestUtilities:
    """Test utility methods and helper functions."""

    def test_calculate_grid_resolution(self, era5_client_with_temp_dir, sample_era5_netcdf):
        """Test grid resolution calculation from NetCDF."""
        client = era5_client_with_temp_dir

        resolution = client._calculate_grid_resolution(sample_era5_netcdf)

        assert resolution is not None
        assert 0.0 < resolution < 1.0  # Typical ERA5 resolution is 0.25 degrees

    def test_file_size_check(self, era5_client_with_temp_dir, tmp_path):
        """Test file size validation."""
        # Create small file (should fail minimum size check)
        small_file = tmp_path / "small.nc"
        small_file.write_bytes(b"x" * 100)  # 100 bytes

        client = era5_client_with_temp_dir

        is_valid_size = client._check_file_size(small_file, min_size_mb=0.5)

        assert is_valid_size is False

    def test_cleanup_invalid_files(self, era5_client_with_temp_dir, tmp_path):
        """Test cleanup of invalid downloaded files."""
        invalid_file = tmp_path / "invalid.nc"
        invalid_file.touch()

        client = era5_client_with_temp_dir

        client._cleanup_invalid_file(invalid_file)

        assert not invalid_file.exists()
