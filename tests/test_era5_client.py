"""Tests for ERA5 Climate Data Ingestion Client.

This module tests the ERA5 client functionality including authentication,
data downloads, validation, and automated updates.

Dependencies:
- pytest: Test framework
- unittest.mock: Mocking for external dependencies
- tempfile: Temporary file/directory creation for testing

Test Coverage:
- ERA5 client initialization and configuration
- CDS API authentication and credential validation
- Temperature data download functionality
- Data validation and quality checks
- Automated update scheduling
- Error handling and retry mechanisms
"""

import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from malaria_predictor.config import Settings
from malaria_predictor.services.era5_client import (
    ERA5Client,
    ERA5DownloadResult,
    ERA5RequestConfig,
)


class TestERA5RequestConfig:
    """Test cases for ERA5RequestConfig validation."""

    def test_default_config_creation(self):
        """Test creating config with required fields only."""
        config = ERA5RequestConfig(years=["2023"], months=["01"], days=["01"])

        assert config.product_type == "reanalysis"
        assert config.format_type == "netcdf"
        assert config.variables == [
            "2m_temperature",
            "2m_dewpoint_temperature",
            "total_precipitation",
        ]
        assert config.area == [40, -20, -35, 55]  # Africa bounds
        assert config.times == ["00:00", "06:00", "12:00", "18:00"]

    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        config = ERA5RequestConfig(
            years=["2022", "2023"],
            months=["06", "07"],
            days=["15", "16"],
            variables=["2m_temperature"],
            area=[10, -10, -10, 10],
            times=["12:00"],
        )

        assert config.years == ["2022", "2023"]
        assert config.variables == ["2m_temperature"]
        assert config.area == [10, -10, -10, 10]
        assert config.times == ["12:00"]

    def test_config_immutability(self):
        """Test that config is immutable after creation."""
        config = ERA5RequestConfig(years=["2023"], months=["01"], days=["01"])

        with pytest.raises(ValidationError):
            config.years = ["2024"]


class TestERA5DownloadResult:
    """Test cases for ERA5DownloadResult model."""

    def test_successful_result_creation(self):
        """Test creating a successful download result."""
        result = ERA5DownloadResult(
            request_id="test_request_123",
            file_path=Path("/tmp/era5_data.nc"),
            file_size_bytes=1024000,
            variables=["2m_temperature"],
            temporal_coverage={"start_date": "2023-01-01", "end_date": "2023-01-07"},
            download_duration_seconds=120.5,
            success=True,
        )

        assert result.success is True
        assert result.error_message is None
        assert result.file_size_bytes == 1024000
        assert "2m_temperature" in result.variables

    def test_failed_result_creation(self):
        """Test creating a failed download result."""
        result = ERA5DownloadResult(
            request_id="failed_request",
            file_path=Path(""),
            file_size_bytes=0,
            variables=[],
            temporal_coverage={},
            download_duration_seconds=30.0,
            success=False,
            error_message="API timeout",
        )

        assert result.success is False
        assert result.error_message == "API timeout"
        assert result.file_size_bytes == 0


class TestERA5Client:
    """Test cases for ERA5Client functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def test_settings(self, temp_dir):
        """Create test settings with temporary directory."""
        return Settings(data_directory=str(temp_dir))

    @pytest.fixture
    def era5_client(self, test_settings):
        """Create ERA5Client instance for testing."""
        return ERA5Client(test_settings)

    def test_client_initialization(self, era5_client, temp_dir):
        """Test ERA5Client initialization."""
        assert era5_client.settings is not None
        assert (
            era5_client.download_directory
            == Path(era5_client.settings.data.directory) / "era5"
        )
        assert era5_client.download_directory.exists()

    def test_client_initialization_default_settings(self):
        """Test ERA5Client initialization with default settings."""
        client = ERA5Client()
        assert client.settings is not None
        assert client.download_directory.name == "era5"

    def test_cds_client_property(self, era5_client):
        """Test lazy loading of CDS API client."""
        # Test that client starts as None and gets initialized when accessed
        assert era5_client._cds_client is None

        # Mock the client after it would be created
        mock_client = Mock()
        era5_client._cds_client = mock_client

        # Test that property returns the mock client
        client = era5_client.cds_client
        assert client == mock_client

    def test_cds_client_import_error(self, era5_client):
        """Test handling of missing cdsapi package."""
        # Reset the cached client to force reimport
        era5_client._cds_client = None

        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'cdsapi'")
        ):
            with pytest.raises(ImportError) as exc_info:
                _ = era5_client.cds_client

            assert "cdsapi package required" in str(exc_info.value)

    def test_validate_credentials_success(self, era5_client):
        """Test successful credential validation."""
        mock_client = Mock()
        mock_client.retrieve = Mock()
        era5_client._cds_client = mock_client

        result = era5_client.validate_credentials()

        assert result is True
        mock_client.retrieve.assert_called_once()

    def test_validate_credentials_failure(self, era5_client):
        """Test failed credential validation."""
        mock_client = Mock()
        mock_client.retrieve.side_effect = Exception("Invalid credentials")
        era5_client._cds_client = mock_client

        result = era5_client.validate_credentials()

        assert result is False

    def test_build_request_config(self, era5_client):
        """Test building request configuration from date parameters."""
        start_date = date(2023, 6, 15)
        end_date = date(2023, 6, 17)
        area_bounds = [20, -10, 10, 20]

        config = era5_client._build_request_config(start_date, end_date, area_bounds)

        assert config.years == ["2023"]
        assert config.months == ["06"]
        assert config.days == ["15", "16", "17"]
        assert config.area == area_bounds
        assert "2m_temperature" in config.variables
        assert (
            "maximum_2m_temperature_since_previous_post_processing" in config.variables
        )
        assert (
            "minimum_2m_temperature_since_previous_post_processing" in config.variables
        )

    def test_build_request_config_default_area(self, era5_client):
        """Test building request configuration with default Africa bounds."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 1)

        config = era5_client._build_request_config(start_date, end_date, None)

        assert config.area == [40, -20, -35, 55]  # Africa bounds

    def test_generate_filename(self, era5_client):
        """Test filename generation for downloaded data."""
        start_date = date(2023, 6, 15)
        end_date = date(2023, 6, 17)
        data_type = "temperature"

        filename = era5_client._generate_filename(start_date, end_date, data_type)

        expected_name = "era5_temperature_2023-06-15_2023-06-17.nc"
        assert filename.name == expected_name
        assert filename.parent == era5_client.download_directory

    def test_submit_cds_request(self, era5_client, temp_dir):
        """Test submitting request to CDS API."""
        mock_client = Mock()
        mock_client.retrieve = Mock()
        era5_client._cds_client = mock_client

        config = ERA5RequestConfig(years=["2023"], months=["01"], days=["01"])
        output_file = temp_dir / "test_output.nc"

        request_id = era5_client._submit_cds_request("temperature", config, output_file)

        mock_client.retrieve.assert_called_once()
        call_args = mock_client.retrieve.call_args

        assert call_args[0][0] == "reanalysis-era5-single-levels"
        assert call_args[0][2] == str(output_file)
        assert "era5_temperature_" in request_id

    def test_list_downloaded_files_empty(self, era5_client):
        """Test listing downloaded files when directory is empty."""
        # Clean up any existing files from previous tests
        for file_path in era5_client.download_directory.glob("era5_*.nc"):
            file_path.unlink()

        files = era5_client.list_downloaded_files()
        assert len(files) == 0

    def test_list_downloaded_files_with_files(self, era5_client, temp_dir):
        """Test listing downloaded files when files exist."""
        # Clean up any existing files from previous tests
        for file_path in era5_client.download_directory.glob("era5_*.nc"):
            file_path.unlink()

        # Create test files in the client's download directory
        era5_dir = era5_client.download_directory
        test_file1 = era5_dir / "era5_temperature_2023-01-01_2023-01-07.nc"
        test_file2 = era5_dir / "era5_precipitation_2023-01-01_2023-01-07.nc"
        other_file = era5_dir / "other_file.txt"

        test_file1.touch()
        test_file2.touch()
        other_file.touch()

        files = era5_client.list_downloaded_files()

        assert len(files) == 2
        assert test_file1 in files
        assert test_file2 in files
        assert other_file not in files

    def test_cleanup_old_files(self, era5_client, temp_dir):
        """Test cleanup of old downloaded files."""
        import os

        era5_dir = era5_client.download_directory

        # Create old file (modify timestamp)
        old_file = era5_dir / "era5_old_data.nc"
        old_file.touch()
        old_time = datetime.now().timestamp() - (40 * 24 * 3600)  # 40 days ago
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        recent_file = era5_dir / "era5_recent_data.nc"
        recent_file.touch()

        deleted_count = era5_client.cleanup_old_files(days_to_keep=30)

        assert deleted_count == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_validate_downloaded_file_not_exists(self, era5_client, temp_dir):
        """Test validation of non-existent file."""
        non_existent_file = temp_dir / "non_existent.nc"

        result = era5_client.validate_downloaded_file(non_existent_file)

        assert result["success"] is False
        assert result["file_exists"] is False
        assert result["error_message"] == "File does not exist"

    def test_validate_downloaded_file_too_small(self, era5_client, temp_dir):
        """Test validation of file that's too small."""
        small_file = temp_dir / "small_file.nc"
        small_file.write_text("small content")  # < 1MB

        result = era5_client.validate_downloaded_file(small_file)

        assert result["success"] is False
        assert result["file_exists"] is True
        assert result["file_size_valid"] is False
        assert result["file_size_mb"] < 1.0

    @patch("xarray.open_dataset")
    def test_validate_downloaded_file_success(
        self, mock_xr_open, era5_client, temp_dir
    ):
        """Test successful file validation."""
        # Create a file large enough
        test_file = temp_dir / "test_data.nc"
        test_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB file

        # Mock xarray dataset
        mock_ds = Mock()
        mock_ds.data_vars = {"t2m": Mock(), "mx2t": Mock()}
        mock_ds.coords = {"time": Mock(), "latitude": Mock(), "longitude": Mock()}
        mock_ds.time.values = ["2023-01-01T00:00:00", "2023-01-01T06:00:00"]
        mock_ds.latitude.min.return_value = -10.0
        mock_ds.latitude.max.return_value = 10.0
        mock_ds.longitude.min.return_value = 0.0
        mock_ds.longitude.max.return_value = 30.0

        mock_xr_open.return_value.__enter__ = Mock(return_value=mock_ds)
        mock_xr_open.return_value.__exit__ = Mock(return_value=None)

        result = era5_client.validate_downloaded_file(test_file)

        assert result["success"] is True
        assert result["file_exists"] is True
        assert result["file_size_valid"] is True
        assert result["data_accessible"] is True
        assert result["variables_present"] is True
        assert result["temporal_coverage_valid"] is True
        assert result["spatial_bounds_valid"] is True
        assert "t2m" in result["variables_found"]

    @patch("malaria_predictor.services.era5_client.schedule")
    def test_setup_automated_updates(self, mock_schedule, era5_client):
        """Test setup of automated update scheduling."""
        era5_client.setup_automated_updates()

        mock_schedule.every().day.at.assert_called_once_with("06:00")
        mock_schedule.every().month.do.assert_called_once()

    @patch.object(ERA5Client, "download_temperature_data")
    @patch.object(ERA5Client, "validate_downloaded_file")
    def test_daily_update_job_success(
        self, mock_validate, mock_download, era5_client, temp_dir
    ):
        """Test successful daily update job."""
        # Mock successful download
        mock_result = ERA5DownloadResult(
            request_id="test_123",
            file_path=temp_dir / "test_data.nc",
            file_size_bytes=1024000,
            variables=["2m_temperature"],
            temporal_coverage={"start": "2023-01-01", "end": "2023-01-07"},
            download_duration_seconds=120.0,
            success=True,
        )
        mock_download.return_value = mock_result

        # Mock successful validation
        mock_validate.return_value = {"success": True}

        era5_client._daily_update_job()

        mock_download.assert_called_once()
        mock_validate.assert_called_once_with(mock_result.file_path)

    @patch.object(ERA5Client, "download_temperature_data")
    def test_daily_update_job_download_failure(self, mock_download, era5_client):
        """Test daily update job with download failure."""
        # Mock failed download
        mock_result = ERA5DownloadResult(
            request_id="failed",
            file_path=Path(""),
            file_size_bytes=0,
            variables=[],
            temporal_coverage={},
            download_duration_seconds=30.0,
            success=False,
            error_message="API timeout",
        )
        mock_download.return_value = mock_result

        # Should not raise exception
        era5_client._daily_update_job()

        mock_download.assert_called_once()

    @patch.object(ERA5Client, "download_temperature_data")
    @patch.object(ERA5Client, "validate_downloaded_file")
    def test_monthly_update_job_success(
        self, mock_validate, mock_download, era5_client, temp_dir
    ):
        """Test successful monthly update job."""
        # Mock successful download
        mock_result = ERA5DownloadResult(
            request_id="monthly_123",
            file_path=temp_dir / "monthly_data.nc",
            file_size_bytes=5024000,
            variables=["2m_temperature"],
            temporal_coverage={"start": "2023-06-01", "end": "2023-06-30"},
            download_duration_seconds=300.0,
            success=True,
        )
        mock_download.return_value = mock_result

        # Mock successful validation
        mock_validate.return_value = {"success": True}

        # Mock cleanup
        with patch.object(era5_client, "cleanup_old_files") as mock_cleanup:
            era5_client._monthly_update_job()
            mock_cleanup.assert_called_once_with(days_to_keep=90)

        mock_download.assert_called_once()
        mock_validate.assert_called_once()

    @patch.object(ERA5Client, "download_temperature_data")
    @patch.object(ERA5Client, "validate_downloaded_file")
    def test_download_and_validate_temperature_data_success(
        self, mock_validate, mock_download, era5_client, temp_dir
    ):
        """Test successful download with validation and retry logic."""
        # Mock successful download
        mock_result = ERA5DownloadResult(
            request_id="retry_test",
            file_path=temp_dir / "validated_data.nc",
            file_size_bytes=2024000,
            variables=["2m_temperature"],
            temporal_coverage={"start": "2023-01-01", "end": "2023-01-07"},
            download_duration_seconds=180.0,
            success=True,
        )
        mock_download.return_value = mock_result

        # Mock successful validation
        mock_validate.return_value = {"success": True}

        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 7)

        result = era5_client.download_and_validate_temperature_data(
            start_date, end_date
        )

        assert result.success is True
        mock_download.assert_called_once()
        mock_validate.assert_called_once()

    @patch.object(ERA5Client, "download_temperature_data")
    @patch.object(ERA5Client, "validate_downloaded_file")
    @patch("time.sleep")  # Speed up test by mocking sleep
    def test_download_and_validate_with_retries(
        self, mock_sleep, mock_validate, mock_download, era5_client, temp_dir
    ):
        """Test download with retry logic on validation failure."""
        # First attempt: download succeeds but validation fails
        # Second attempt: both succeed
        mock_results = [
            ERA5DownloadResult(
                request_id="retry_1",
                file_path=temp_dir / "invalid_data.nc",
                file_size_bytes=1024000,
                variables=["2m_temperature"],
                temporal_coverage={"start": "2023-01-01", "end": "2023-01-07"},
                download_duration_seconds=120.0,
                success=True,
            ),
            ERA5DownloadResult(
                request_id="retry_2",
                file_path=temp_dir / "valid_data.nc",
                file_size_bytes=2024000,
                variables=["2m_temperature"],
                temporal_coverage={"start": "2023-01-01", "end": "2023-01-07"},
                download_duration_seconds=150.0,
                success=True,
            ),
        ]
        mock_download.side_effect = mock_results

        # First validation fails, second succeeds
        mock_validate.side_effect = [
            {"success": False, "error_message": "Invalid data"},
            {"success": True},
        ]

        # Create mock files that can be deleted
        for mock_result in mock_results:
            mock_result.file_path.touch()

        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 7)

        result = era5_client.download_and_validate_temperature_data(
            start_date, end_date, max_retries=2
        )

        assert result.success is True
        assert mock_download.call_count == 2
        assert mock_validate.call_count == 2
        mock_sleep.assert_called()  # Should have waited between retries

    @patch.object(ERA5Client, "download_temperature_data")
    @patch("time.sleep")  # Speed up test
    def test_download_and_validate_all_retries_fail(
        self, mock_sleep, mock_download, era5_client
    ):
        """Test download when all retry attempts fail."""
        # All attempts fail
        mock_result = ERA5DownloadResult(
            request_id="failed",
            file_path=Path(""),
            file_size_bytes=0,
            variables=[],
            temporal_coverage={},
            download_duration_seconds=30.0,
            success=False,
            error_message="Persistent API failure",
        )
        mock_download.return_value = mock_result

        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 7)

        result = era5_client.download_and_validate_temperature_data(
            start_date, end_date, max_retries=2
        )

        assert result.success is False
        assert "All 2 attempts failed" in result.error_message
        assert mock_download.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
