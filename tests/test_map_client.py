"""Tests for MAP (Malaria Atlas Project) data ingestion client.

This module contains comprehensive tests for the MAP client functionality,
including data downloads, validation, and processing capabilities.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from malaria_predictor.services.map_client import (
    MAPClient,
    MAPDownloadResult,
    MAPRequestConfig,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock()
    settings.data = Mock()
    settings.data.directory = tempfile.mkdtemp()
    return settings


@pytest.fixture
def map_client(mock_settings):
    """Create MAP client instance for testing."""
    return MAPClient(settings=mock_settings)


class TestMAPClient:
    """Test suite for MAP client functionality."""

    def test_client_initialization(self, mock_settings):
        """Test MAP client initialization."""
        client = MAPClient(settings=mock_settings)

        assert client.settings == mock_settings
        assert client.download_directory.exists()
        assert client.download_directory.name == "map"
        assert client.session is not None
        assert client.executor is not None

    def test_r_availability_check(self, map_client):
        """Test R availability checking."""
        # Test with R not available
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            assert map_client._check_r_availability() is False

        # Test with R available but no malariaAtlas
        with patch("subprocess.run") as mock_run:
            # First call checks R version
            # Second call checks malariaAtlas package
            mock_run.side_effect = [
                Mock(returncode=0, stdout="R version 4.0.0"),
                Mock(returncode=0, stdout="MISSING"),
            ]
            assert map_client._check_r_availability() is False

        # Test with R and malariaAtlas available
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="R version 4.0.0"),
                Mock(returncode=0, stdout="OK"),
            ]
            assert map_client._check_r_availability() is True

    @patch("requests.Session.get")
    @patch("malaria_predictor.services.map_client.MAPClient._crop_raster_to_bounds")
    def test_download_parasite_rate_surface_http(self, mock_crop, mock_get, map_client):
        """Test downloading parasite rate surface via HTTP."""
        # Mock R not available
        map_client._r_available = False

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"test_data"]
        mock_get.return_value = mock_response

        # Mock cropping to return the same path
        mock_crop.side_effect = lambda path, bounds: path

        # Test download
        result = map_client.download_parasite_rate_surface(
            year=2020, species="Pf", resolution="5km"
        )

        assert result.success is True
        assert result.data_type == "pr"
        assert result.temporal_coverage["year"] == 2020
        assert len(result.file_paths) > 0

        # Verify URL construction
        expected_url = "https://data.malariaatlas.org/rasters/pr/Pf/2020/Pf_parasite_rate_2020_5km.tif"
        mock_get.assert_called_with(expected_url, stream=True, timeout=300)

    @patch("subprocess.run")
    def test_download_parasite_rate_surface_r(self, mock_run, map_client):
        """Test downloading parasite rate surface via R."""
        # Mock R available
        map_client._r_available = True

        # Create a dummy file to simulate R download
        dummy_file = map_client.download_directory / "test_pr_2020.tif"
        dummy_file.write_bytes(b"dummy raster data")

        # Mock R script execution
        mock_run.return_value = Mock(
            returncode=0, stdout=f"DOWNLOADED: {dummy_file}\n", stderr=""
        )

        # Test download
        result = map_client.download_parasite_rate_surface(
            year=2020, species="Pf", resolution="5km"
        )

        assert result.success is True
        assert result.data_type == "pr"
        assert len(result.file_paths) == 1
        assert result.file_paths[0] == dummy_file

        # Clean up
        dummy_file.unlink()

    @patch("requests.Session.get")
    def test_download_vector_occurrence_data_http(self, mock_get, map_client):
        """Test downloading vector occurrence data via HTTP."""
        # Mock R not available
        map_client._r_available = False

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "species,latitude,longitude,year\ngambiae,0.5,30.2,2020\n"
        mock_get.return_value = mock_response

        # Test download
        result = map_client.download_vector_occurrence_data(
            species_complex="gambiae", start_year=2019, end_year=2020
        )

        assert result.success is True
        assert result.data_type == "vector"
        assert len(result.file_paths) == 1
        assert result.metadata["species_complex"] == "gambiae"

        # Verify CSV content
        csv_file = result.file_paths[0]
        assert csv_file.exists()
        content = csv_file.read_text()
        assert "gambiae" in content

    @patch("requests.Session.get")
    @patch("malaria_predictor.services.map_client.MAPClient._crop_raster_to_bounds")
    def test_download_intervention_coverage(self, mock_crop, mock_get, map_client):
        """Test downloading intervention coverage data."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"intervention_data"]
        mock_get.return_value = mock_response

        # Mock cropping to return the same path
        mock_crop.side_effect = lambda path, bounds: path

        # Test ITN coverage download
        result = map_client.download_intervention_coverage(
            intervention_type="ITN", year=2020
        )

        assert result.success is True
        assert result.data_type == "intervention"
        assert result.metadata["intervention_type"] == "ITN"
        assert len(result.file_paths) > 0

        # Verify URL construction
        expected_url = "https://data.malariaatlas.org/rasters/interventions/ITN_use/2020/ITN_use_2020.tif"
        mock_get.assert_called_with(expected_url, stream=True, timeout=300)

    def test_download_with_invalid_intervention_type(self, map_client):
        """Test download with invalid intervention type."""
        result = map_client.download_intervention_coverage(
            intervention_type="INVALID",  # type: ignore
            year=2020,
        )

        assert result.success is False
        assert "Unknown intervention type" in result.error_message

    def test_validate_raster_file(self, map_client):
        """Test raster file validation."""
        # Test with non-existent file
        result = map_client.validate_raster_file(Path("nonexistent.tif"))
        assert result["file_exists"] is False
        assert result["success"] is False

        # Create a dummy file for testing
        dummy_file = map_client.download_directory / "test_raster.tif"
        dummy_file.write_bytes(
            b"x" * (1024 * 200)
        )  # 200KB file (above 0.1MB threshold)

        # Test validation without rasterio
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'rasterio'")
        ):
            result = map_client.validate_raster_file(dummy_file)
            assert result["file_exists"] is True
            assert result["file_size_valid"] is True
            assert result["success"] is False  # Can't validate without rasterio
            assert "rasterio not available" in result["error_message"]

        # Clean up
        dummy_file.unlink()

    @patch("rasterio.open")
    def test_validate_raster_file_with_rasterio(self, mock_rasterio_open, map_client):
        """Test raster file validation with rasterio available."""
        # Create dummy file
        dummy_file = map_client.download_directory / "test_raster.tif"
        dummy_file.write_bytes(
            b"x" * (1024 * 200)
        )  # 200KB file (above 0.1MB threshold)

        # Mock rasterio dataset
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_dataset.res = (0.05, 0.05)  # 5km resolution
        mock_dataset.crs.to_epsg.return_value = 4326

        # Mock the context manager
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset
        mock_rasterio_open.return_value.__exit__.return_value = None

        # Test validation
        result = map_client.validate_raster_file(dummy_file)

        assert result["file_exists"] is True
        assert result["file_size_valid"] is True
        assert result["data_accessible"] is True
        assert result["has_valid_data"] is True
        assert result["spatial_resolution_valid"] is True
        assert result["crs_valid"] is True
        assert result["success"] is True

        # Clean up
        dummy_file.unlink()

    def test_process_parasite_rate_data_array(self, map_client):
        """Test processing parasite rate data to array."""
        # Create dummy file
        dummy_file = map_client.download_directory / "test_pr.tif"
        dummy_file.touch()

        # Mock rasterio through import mechanism
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.array([[0.001, 0.002], [0.003, 0.004]])

        mock_rasterio = MagicMock()
        mock_rasterio.open.return_value.__enter__.return_value = mock_dataset

        def mock_import(name, *args, **kwargs):
            if name == "rasterio":
                return mock_rasterio
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Test processing
            result = map_client.process_parasite_rate_data(
                dummy_file, output_format="array"
            )

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 2)
        assert result[0, 0] == 0.1  # Converted to percentage
        assert result[1, 1] == 0.4

        # Clean up
        dummy_file.unlink()

    @patch("rasterio.open")
    @patch("pandas.DataFrame")
    @patch("rasterio.transform.xy")
    def test_process_parasite_rate_data_dataframe(
        self, mock_xy, mock_dataframe, mock_rasterio_open, map_client
    ):
        """Test processing parasite rate data to DataFrame."""
        # Create dummy file
        dummy_file = map_client.download_directory / "test_pr.tif"
        dummy_file.touch()

        # Mock rasterio dataset
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.array([[0.001, 0.002], [0.003, 0.004]])
        mock_dataset.height = 2
        mock_dataset.width = 2
        mock_dataset.transform = MagicMock()

        # Mock rasterio open
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset
        mock_rasterio_open.return_value.__exit__.return_value = None

        # Mock coordinate transformation
        mock_xy.return_value = ([0, 1, 0, 1], [0, 0, 1, 1])

        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_df.dropna.return_value = mock_df
        mock_dataframe.return_value = mock_df

        # Test processing
        _result = map_client.process_parasite_rate_data(
            dummy_file, output_format="dataframe"
        )

        # Verify DataFrame creation
        mock_dataframe.assert_called_once()
        df_args = mock_dataframe.call_args[0][0]
        assert "latitude" in df_args
        assert "longitude" in df_args
        assert "parasite_rate" in df_args

        # Clean up
        dummy_file.unlink()

    def test_cleanup_old_files(self, map_client):
        """Test cleanup of old files."""
        # Create test files with different ages
        old_file = map_client.download_directory / "old_file.tif"
        old_file.touch()
        # Set modification time to 100 days ago
        old_time = datetime.now().timestamp() - (100 * 24 * 3600)
        import os

        os.utime(old_file, (old_time, old_time))

        recent_file = map_client.download_directory / "recent_file.tif"
        recent_file.touch()

        # Clean up files older than 90 days
        deleted_count = map_client.cleanup_old_files(days_to_keep=90)

        assert deleted_count == 1
        assert not old_file.exists()
        assert recent_file.exists()

        # Clean up
        recent_file.unlink()

    def test_crop_raster_to_bounds(self, map_client):
        """Test raster cropping functionality."""
        # Test without rasterio
        dummy_file = map_client.download_directory / "test.tif"
        dummy_file.touch()

        result = map_client._crop_raster_to_bounds(
            dummy_file, bounds=(-10, -20, 10, 20)
        )

        assert result is None  # Should fail without rasterio

        # Clean up
        if dummy_file.exists():
            dummy_file.unlink()

    def test_bounds_to_dict(self, map_client):
        """Test bounds tuple to dictionary conversion."""
        bounds = (-20.0, -35.0, 55.0, 40.0)
        result = map_client._bounds_to_dict(bounds)

        assert result["west"] == -20.0
        assert result["south"] == -35.0
        assert result["east"] == 55.0
        assert result["north"] == 40.0

    def test_generate_r_download_script(self, map_client):
        """Test R script generation."""
        script = map_client._generate_r_download_script(
            data_type="pr",
            year=2020,
            species="Pf",
            resolution="5km",
            area_bounds=None,
            output_dir="/tmp/map",
        )

        assert "library(malariaAtlas)" in script
        assert "getRaster" in script
        assert "Plasmodium falciparum PR2-10 2020" in script
        assert "/tmp/map" in script

    def test_close(self, map_client):
        """Test resource cleanup."""
        # Create mock session and executor
        map_client.session = Mock()
        map_client.executor = Mock()

        # Close client
        map_client.close()

        # Verify cleanup
        map_client.session.close.assert_called_once()
        map_client.executor.shutdown.assert_called_once_with(wait=True)


class TestMAPRequestConfig:
    """Test MAP request configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MAPRequestConfig(year=2020)

        assert config.data_type == "pr"
        assert config.species == "Pf"
        assert config.year == 2020
        assert config.area_bounds == (-20.0, -35.0, 55.0, 40.0)
        assert config.age_range == (2, 10)
        assert config.resolution == "5km"

    def test_custom_config(self):
        """Test custom configuration."""
        config = MAPRequestConfig(
            data_type="incidence",
            species="Pv",
            year=2021,
            area_bounds=(10, 20, 30, 40),
            age_range=(0, 5),
            resolution="1km",
        )

        assert config.data_type == "incidence"
        assert config.species == "Pv"
        assert config.year == 2021
        assert config.area_bounds == (10, 20, 30, 40)
        assert config.age_range == (0, 5)
        assert config.resolution == "1km"


class TestMAPDownloadResult:
    """Test MAP download result model."""

    def test_successful_result(self):
        """Test successful download result."""
        result = MAPDownloadResult(
            request_id="test_123",
            file_paths=[Path("/tmp/test.tif")],
            total_size_bytes=1024000,
            data_type="pr",
            temporal_coverage={"year": 2020},
            spatial_coverage={"west": -20, "east": 55},
            download_duration_seconds=10.5,
            success=True,
            error_message=None,
        )

        assert result.success is True
        assert result.error_message is None
        assert len(result.file_paths) == 1
        assert result.total_size_bytes == 1024000

    def test_failed_result(self):
        """Test failed download result."""
        result = MAPDownloadResult(
            request_id="failed_123",
            file_paths=[],
            total_size_bytes=0,
            data_type="pr",
            temporal_coverage={},
            spatial_coverage={},
            download_duration_seconds=5.0,
            success=False,
            error_message="Connection timeout",
        )

        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert len(result.file_paths) == 0
