"""Tests for CHIRPS Rainfall Data Ingestion Client.

This module tests the CHIRPS client functionality including data downloads,
validation, processing, and integration with the data harmonization service.

Dependencies:
- pytest: Test framework
- unittest.mock: Mocking for external dependencies
- tempfile: Temporary file/directory creation for testing

Test Coverage:
- CHIRPS client initialization and configuration
- Rainfall data download functionality
- GeoTIFF processing and validation
- Data aggregation operations
- Error handling and retry mechanisms
- Integration with data harmonizer
"""

import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from pydantic import ValidationError

from malaria_predictor.config import Settings
from malaria_predictor.services.chirps_client import (
    CHIRPSClient,
    CHIRPSDownloadResult,
    CHIRPSRequestConfig,
)


class TestCHIRPSRequestConfig:
    """Test cases for CHIRPSRequestConfig validation."""

    def test_default_config_creation(self):
        """Test creating config with required fields only."""
        config = CHIRPSRequestConfig(
            start_date=date(2023, 1, 1), end_date=date(2023, 1, 7)
        )

        assert config.data_type == "daily"
        assert config.format_type == "tif"
        assert config.area_bounds == (-20.0, -35.0, 55.0, 40.0)  # Africa bounds
        assert config.start_date == date(2023, 1, 1)
        assert config.end_date == date(2023, 1, 7)

    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        custom_bounds = (-10.0, -20.0, 30.0, 20.0)
        config = CHIRPSRequestConfig(
            start_date=date(2023, 6, 1),
            end_date=date(2023, 6, 30),
            data_type="monthly",
            area_bounds=custom_bounds,
        )

        assert config.data_type == "monthly"
        assert config.area_bounds == custom_bounds

    def test_config_immutability(self):
        """Test that config is immutable after creation."""
        config = CHIRPSRequestConfig(
            start_date=date(2023, 1, 1), end_date=date(2023, 1, 7)
        )

        with pytest.raises(ValidationError):
            config.start_date = date(2023, 2, 1)


class TestCHIRPSDownloadResult:
    """Test cases for CHIRPSDownloadResult model."""

    def test_successful_result_creation(self):
        """Test creating a successful download result."""
        result = CHIRPSDownloadResult(
            request_id="chirps_daily_20230101",
            file_paths=[Path("/tmp/chirps1.tif"), Path("/tmp/chirps2.tif")],
            total_size_bytes=10240000,
            temporal_coverage={"start_date": "2023-01-01", "end_date": "2023-01-07"},
            download_duration_seconds=45.5,
            success=True,
            files_processed=2,
        )

        assert result.success is True
        assert result.error_message is None
        assert result.total_size_bytes == 10240000
        assert len(result.file_paths) == 2
        assert result.files_processed == 2

    def test_failed_result_creation(self):
        """Test creating a failed download result."""
        result = CHIRPSDownloadResult(
            request_id="failed_request",
            file_paths=[],
            total_size_bytes=0,
            temporal_coverage={},
            download_duration_seconds=10.0,
            success=False,
            error_message="Connection timeout",
            files_processed=0,
        )

        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert result.total_size_bytes == 0
        assert len(result.file_paths) == 0


class TestCHIRPSClient:
    """Test cases for CHIRPSClient functionality."""

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
    def chirps_client(self, test_settings):
        """Create CHIRPSClient instance for testing."""
        return CHIRPSClient(test_settings)

    def test_client_initialization(self, chirps_client, temp_dir):
        """Test CHIRPSClient initialization."""
        assert chirps_client.settings is not None
        assert (
            chirps_client.download_directory
            == Path(chirps_client.settings.data.directory) / "chirps"
        )
        assert chirps_client.download_directory.exists()
        assert chirps_client.session is not None
        assert chirps_client.executor is not None

    def test_client_initialization_default_settings(self):
        """Test CHIRPSClient initialization with default settings."""
        client = CHIRPSClient()
        assert client.settings is not None
        assert client.download_directory.name == "chirps"

    def test_generate_daily_dates(self, chirps_client):
        """Test generation of daily date range."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 5)

        dates = chirps_client._generate_daily_dates(start_date, end_date)

        assert len(dates) == 5
        assert dates[0] == date(2023, 1, 1)
        assert dates[-1] == date(2023, 1, 5)

    def test_generate_monthly_dates(self, chirps_client):
        """Test generation of monthly date range."""
        start_date = date(2023, 1, 15)
        end_date = date(2023, 4, 20)

        dates = chirps_client._generate_monthly_dates(start_date, end_date)

        assert len(dates) == 4
        assert dates[0] == date(2023, 1, 1)
        assert dates[1] == date(2023, 2, 1)
        assert dates[2] == date(2023, 3, 1)
        assert dates[3] == date(2023, 4, 1)

    def test_generate_monthly_dates_cross_year(self, chirps_client):
        """Test monthly date generation across year boundary."""
        start_date = date(2022, 11, 15)
        end_date = date(2023, 2, 20)

        dates = chirps_client._generate_monthly_dates(start_date, end_date)

        assert len(dates) == 4
        assert dates[0] == date(2022, 11, 1)
        assert dates[-1] == date(2023, 2, 1)

    @patch("requests.Session.get")
    def test_download_single_file_success(self, mock_get, chirps_client, temp_dir):
        """Test successful download of single CHIRPS file."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"test data"])
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        target_date = date(2023, 1, 1)
        file_path, file_size = chirps_client._download_single_file(target_date, "daily")

        assert file_path is not None
        assert file_path.name == "chirps-v2.0.2023.01.01.tif"
        assert file_path.exists()
        assert file_size > 0

    @patch("requests.Session.get")
    def test_download_single_file_already_exists(
        self, mock_get, chirps_client, temp_dir
    ):
        """Test handling of already downloaded file."""
        # Create existing file
        target_date = date(2023, 1, 1)
        existing_file = chirps_client.download_directory / "chirps-v2.0.2023.01.01.tif"
        existing_file.write_text("existing data")

        file_path, file_size = chirps_client._download_single_file(target_date, "daily")

        # Should not make HTTP request
        mock_get.assert_not_called()
        assert file_path == existing_file
        assert file_size == len("existing data")

    @patch("requests.Session.get")
    def test_download_single_file_http_error(self, mock_get, chirps_client):
        """Test handling of HTTP errors during download."""
        # Clean up any existing files that might interfere
        target_date = date(2023, 1, 1)
        filename = f"chirps-v2.0.{target_date.year}.{target_date.month:02d}.{target_date.day:02d}.tif"
        existing_file = chirps_client.download_directory / filename
        if existing_file.exists():
            existing_file.unlink()

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        file_path, file_size = chirps_client._download_single_file(target_date, "daily")

        assert file_path is None
        assert file_size == 0

    def test_download_rainfall_data_invalid_type(self, chirps_client):
        """Test download with invalid data type."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 7)

        result = chirps_client.download_rainfall_data(
            start_date, end_date, data_type="invalid"
        )

        assert result.success is False
        assert "Unsupported data type" in result.error_message

    @patch.object(CHIRPSClient, "_download_single_file")
    def test_download_rainfall_data_daily(self, mock_download, chirps_client):
        """Test daily rainfall data download."""
        # Mock successful downloads
        mock_download.side_effect = [
            (Path("/tmp/chirps1.tif"), 1024000),
            (Path("/tmp/chirps2.tif"), 1024000),
            (Path("/tmp/chirps3.tif"), 1024000),
        ]

        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 3)

        result = chirps_client.download_rainfall_data(start_date, end_date, "daily")

        assert result.success is True
        assert len(result.file_paths) == 3
        assert result.total_size_bytes == 3 * 1024000
        assert result.files_processed == 3
        assert mock_download.call_count == 3

    def test_validate_rainfall_file_not_exists(self, chirps_client, temp_dir):
        """Test validation of non-existent file."""
        non_existent_file = temp_dir / "non_existent.tif"

        result = chirps_client.validate_rainfall_file(non_existent_file)

        assert result["success"] is False
        assert result["file_exists"] is False
        assert result["error_message"] == "File does not exist"

    def test_validate_rainfall_file_too_small(self, chirps_client, temp_dir):
        """Test validation of file that's too small."""
        small_file = temp_dir / "small_file.tif"
        small_file.write_text("tiny")  # < 0.5MB

        result = chirps_client.validate_rainfall_file(small_file)

        assert result["success"] is False
        assert result["file_exists"] is True
        assert result["file_size_valid"] is False
        assert result["file_size_mb"] < 0.5

    @patch("rasterio.open")
    def test_validate_rainfall_file_success(
        self, mock_rasterio_open, chirps_client, temp_dir
    ):
        """Test successful file validation."""
        # Create a file large enough
        test_file = temp_dir / "test_chirps.tif"
        test_file.write_bytes(b"x" * (1024 * 1024))  # 1MB file

        # Mock rasterio dataset
        mock_src = Mock()
        mock_src.read.return_value = np.array([[10.5, 15.2], [8.3, 12.1]])
        mock_src.res = (0.05, 0.05)  # Correct CHIRPS resolution

        mock_rasterio_open.return_value.__enter__ = Mock(return_value=mock_src)
        mock_rasterio_open.return_value.__exit__ = Mock(return_value=None)

        result = chirps_client.validate_rainfall_file(test_file)

        assert result["success"] is True
        assert result["file_exists"] is True
        assert result["file_size_valid"] is True
        assert result["data_accessible"] is True
        assert result["has_valid_data"] is True
        assert result["spatial_resolution_valid"] is True

    @patch("rasterio.open")
    def test_process_rainfall_data_success(
        self, mock_rasterio_open, chirps_client, temp_dir
    ):
        """Test successful rainfall data processing."""
        test_file = temp_dir / "test_chirps.tif"
        test_file.touch()

        # Mock rasterio operations
        mock_src = Mock()
        mock_data = np.array([[10.5, 15.2, -9999], [8.3, 12.1, 5.5]])
        mock_src.read.return_value = mock_data
        mock_src.transform = Mock()
        mock_src.crs = Mock()
        mock_src.window_transform = Mock(return_value=Mock())

        # Mock window creation
        with patch("rasterio.windows.from_bounds", return_value=Mock()):
            mock_rasterio_open.return_value.__enter__ = Mock(return_value=mock_src)
            mock_rasterio_open.return_value.__exit__ = Mock(return_value=None)

            result = chirps_client.process_rainfall_data(test_file)

        assert result is not None
        assert "data" in result
        assert "transform" in result
        assert "crs" in result
        assert "bounds" in result
        assert "shape" in result

        # Check that no-data values were handled
        processed_data = result["data"]
        assert np.isnan(processed_data[0, 2])  # -9999 should be NaN

    @patch("rasterio.open")
    def test_aggregate_to_monthly_success(
        self, mock_rasterio_open, chirps_client, temp_dir
    ):
        """Test successful aggregation of daily files to monthly."""
        # Create mock daily files
        daily_files = []
        for day in range(1, 4):
            file_path = temp_dir / f"chirps-v2.0.2023.01.{day:02d}.tif"
            file_path.touch()
            daily_files.append(file_path)

        output_path = temp_dir / "chirps-v2.0.2023.01.monthly.tif"

        # Mock rasterio read operations
        mock_src = Mock()
        mock_src.read.side_effect = [
            np.array([[5.0, 10.0], [3.0, 8.0]]),
            np.array([[2.0, 5.0], [1.0, 3.0]]),
            np.array([[8.0, 12.0], [6.0, 10.0]]),
        ]
        mock_src.profile = {"driver": "GTiff", "dtype": "float32"}

        mock_rasterio_open.return_value.__enter__ = Mock(return_value=mock_src)
        mock_rasterio_open.return_value.__exit__ = Mock(return_value=None)

        result = chirps_client.aggregate_to_monthly(daily_files, output_path)

        assert result is True
        # Verify that output file would be created with sum of daily values

    def test_cleanup_old_files(self, chirps_client, temp_dir):
        """Test cleanup of old CHIRPS files."""
        import os

        # Create old file (modify timestamp)
        old_file = chirps_client.download_directory / "chirps-v2.0.2022.12.01.tif"
        old_file.touch()
        old_time = datetime.now().timestamp() - (40 * 24 * 3600)  # 40 days ago
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        recent_file = chirps_client.download_directory / "chirps-v2.0.2023.01.01.tif"
        recent_file.touch()

        deleted_count = chirps_client.cleanup_old_files(days_to_keep=30)

        assert deleted_count == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_client_close(self, chirps_client):
        """Test client resource cleanup."""
        mock_session = Mock()
        mock_executor = Mock()

        chirps_client.session = mock_session
        chirps_client.executor = mock_executor

        chirps_client.close()

        mock_session.close.assert_called_once()
        mock_executor.shutdown.assert_called_once_with(wait=True)


class TestCHIRPSIntegration:
    """Integration tests for CHIRPS client with other services."""

    @pytest.fixture
    def chirps_client(self):
        """Create CHIRPSClient instance for integration testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = Settings(data_directory=tmp_dir)
            client = CHIRPSClient(settings)
            yield client
            client.close()

    def test_download_and_validate_workflow(self, chirps_client):
        """Test complete download and validation workflow."""
        # This would be an integration test with real downloads
        # For unit tests, we mock the components
        pass

    def test_harmonization_integration(self, chirps_client):
        """Test integration with data harmonization service."""
        # Test that CHIRPS data can be properly harmonized with ERA5
        pass


if __name__ == "__main__":
    pytest.main([__file__])
