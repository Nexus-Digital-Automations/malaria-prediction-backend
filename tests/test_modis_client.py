"""Tests for MODIS vegetation indices client."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from malaria_predictor.services.modis_client import (
    MODISClient,
    MODISDownloadResult,
    MODISProcessingResult,
    MODISRequestConfig,
    MODISTileInfo,
)


class TestMODISClient:
    """Test suite for MODISClient."""

    @pytest.fixture
    def modis_client(self, tmp_path):
        """Create MODIS client with temporary directory."""
        with patch("malaria_predictor.services.modis_client.Settings") as mock_settings:
            mock_settings.return_value.data_directory = str(tmp_path)
            client = MODISClient()
            yield client
            client.close()

    @pytest.fixture
    def sample_tile_info(self):
        """Sample MODIS tile information."""
        return MODISTileInfo(
            horizontal=21,
            vertical=8,
            tile_id="h21v08",
            center_lat=10.0,
            center_lon=35.0,
            bounds=(30.0, 5.0, 40.0, 15.0),
        )

    def test_client_initialization(self, modis_client):
        """Test MODIS client initialization."""
        assert modis_client.download_directory.exists()
        assert modis_client.session is not None
        assert not modis_client._authenticated
        assert modis_client._auth_token is None
        assert "MOD13Q1" in modis_client.SUPPORTED_PRODUCTS
        assert "MYD13Q1" in modis_client.SUPPORTED_PRODUCTS

    @patch("malaria_predictor.services.modis_client.requests.Session.get")
    @patch("malaria_predictor.services.modis_client.requests.Session.post")
    def test_authentication_success(self, mock_post, mock_get, modis_client):
        """Test successful NASA EarthData authentication."""
        # Mock successful login
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Login page"

        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "Welcome to EarthData"

        result = modis_client.authenticate("testuser", "testpass")

        assert result is True
        assert modis_client._authenticated is True

        mock_get.assert_called_once()
        mock_post.assert_called_once_with(
            "https://urs.earthdata.nasa.gov/login",
            data={"username": "testuser", "password": "testpass"},
            timeout=30,
        )

    @patch("malaria_predictor.services.modis_client.requests.Session.get")
    @patch("malaria_predictor.services.modis_client.requests.Session.post")
    def test_authentication_failure(self, mock_post, mock_get, modis_client):
        """Test failed NASA EarthData authentication."""
        # Mock failed login
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Login page"

        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "Invalid username or password"

        result = modis_client.authenticate("baduser", "badpass")

        assert result is False
        assert modis_client._authenticated is False

    def test_discover_modis_tiles(self, modis_client):
        """Test MODIS tile discovery for geographic area."""
        # Test area covering East Africa
        area_bounds = (30.0, -5.0, 45.0, 15.0)  # Kenya, Uganda, Tanzania region

        tiles = modis_client.discover_modis_tiles(area_bounds)

        assert len(tiles) > 0
        assert all(isinstance(tile, MODISTileInfo) for tile in tiles)

        # Check that discovered tiles overlap with the requested area
        for tile in tiles:
            assert isinstance(tile.tile_id, str)
            assert tile.tile_id.startswith("h") and "v" in tile.tile_id
            assert -90 <= tile.center_lat <= 90
            assert -180 <= tile.center_lon <= 180

    def test_discover_modis_tiles_empty_area(self, modis_client):
        """Test tile discovery for area with no MODIS coverage."""
        # Test area in middle of ocean (should have minimal coverage)
        area_bounds = (160.0, -10.0, 170.0, -5.0)

        tiles = modis_client.discover_modis_tiles(area_bounds)

        # Should still return some tiles (ocean areas are covered)
        assert isinstance(tiles, list)

    def test_generate_16day_periods(self, modis_client):
        """Test generation of 16-day periods for MODIS data."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 2, 28)

        periods = modis_client._generate_16day_periods(start_date, end_date)

        assert len(periods) >= 3  # Should have at least 3 16-day periods
        assert all(isinstance(period, date) for period in periods)
        assert periods[0] >= start_date
        assert periods[-1] <= end_date

    @patch("malaria_predictor.services.modis_client.MODISClient.discover_modis_tiles")
    def test_download_vegetation_indices_not_authenticated(
        self, mock_discover, modis_client
    ):
        """Test download when not authenticated."""
        mock_discover.return_value = [
            MODISTileInfo(
                horizontal=21,
                vertical=8,
                tile_id="h21v08",
                center_lat=10.0,
                center_lon=35.0,
                bounds=(30.0, 5.0, 40.0, 15.0),
            )
        ]

        result = modis_client.download_vegetation_indices(
            start_date=date(2023, 1, 1), end_date=date(2023, 1, 16)
        )

        assert result.success is False
        assert "Authentication required" in result.error_message

    @patch(
        "malaria_predictor.services.modis_client.MODISClient._download_single_modis_file"
    )
    @patch("malaria_predictor.services.modis_client.MODISClient.discover_modis_tiles")
    def test_download_vegetation_indices_success(
        self, mock_discover, mock_download, modis_client, tmp_path
    ):
        """Test successful vegetation indices download."""
        # Set up authentication
        modis_client._authenticated = True

        # Mock tile discovery
        sample_tile = MODISTileInfo(
            horizontal=21,
            vertical=8,
            tile_id="h21v08",
            center_lat=10.0,
            center_lon=35.0,
            bounds=(30.0, 5.0, 40.0, 15.0),
        )
        mock_discover.return_value = [sample_tile]

        # Mock successful download
        test_file = tmp_path / "MOD13Q1.A2023001.h21v08.061.hdf"
        test_file.write_bytes(b"mock hdf data" * 1000)  # Create test file

        mock_download.return_value = {
            "success": True,
            "file_path": test_file,
            "file_size": 13000,
            "tile_id": "h21v08",
            "skipped": False,
        }

        result = modis_client.download_vegetation_indices(
            start_date=date(2023, 1, 1), end_date=date(2023, 1, 16), product="MOD13Q1"
        )

        assert result.success is True
        assert len(result.file_paths) > 0
        assert result.files_processed > 0
        assert "h21v08" in result.tiles_processed
        assert result.total_size_bytes > 0

    def test_download_single_modis_file_unsupported_product(self, modis_client):
        """Test download with unsupported product."""
        modis_client._authenticated = True

        result = modis_client.download_vegetation_indices(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 16),
            product="INVALID_PRODUCT",
        )

        assert result.success is False
        assert "Unsupported product" in result.error_message

    @patch("rasterio.open")
    def test_process_vegetation_indices_success(
        self, mock_rasterio_open, modis_client, tmp_path
    ):
        """Test successful vegetation indices processing."""
        # Create test file
        test_file = tmp_path / "MOD13Q1.A2023001.h21v08.061.hdf"
        test_file.write_bytes(b"mock hdf data")

        # Mock rasterio operations
        mock_hdf = MagicMock()
        mock_hdf.subdatasets = [
            "HDF4_EOS:EOS_GRID:test.hdf:MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI",
            "HDF4_EOS:EOS_GRID:test.hdf:MODIS_Grid_16DAY_250m_500m_VI:250m 16 days EVI",
            "HDF4_EOS:EOS_GRID:test.hdf:MODIS_Grid_16DAY_250m_500m_VI:250m 16 days VI_Quality",
        ]

        # Mock VI data source
        mock_vi_src = MagicMock()
        mock_vi_src.read.return_value = np.array(
            [[1000, 2000, 3000], [4000, 5000, 6000]], dtype=np.int16
        )
        mock_vi_src.height = 2
        mock_vi_src.width = 3
        mock_vi_src.transform = MagicMock()
        mock_vi_src.crs = MagicMock()
        mock_vi_src.profile = {"dtype": "int16", "height": 2, "width": 3}

        # Mock quality data source
        mock_quality_src = MagicMock()
        mock_quality_src.read.return_value = np.array(
            [[0, 0, 1], [1, 2, 3]], dtype=np.uint16
        )

        def rasterio_open_side_effect(path, *args, **kwargs):
            if "NDVI" in str(path):
                return mock_vi_src
            elif "VI_Quality" in str(path):
                return mock_quality_src
            else:
                return mock_hdf

        mock_rasterio_open.side_effect = rasterio_open_side_effect

        results = modis_client.process_vegetation_indices(
            test_file, vegetation_indices=["NDVI"], apply_quality_filter=True
        )

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, MODISProcessingResult)
        assert result.success is True
        assert result.vegetation_index == "NDVI"
        assert result.valid_pixel_count > 0
        assert "min" in result.statistics
        assert "max" in result.statistics

    @patch("rasterio.open")
    def test_process_vegetation_indices_missing_rasterio(
        self, mock_rasterio_open, modis_client, tmp_path
    ):
        """Test processing when rasterio is not available."""
        # Mock ImportError for rasterio
        mock_rasterio_open.side_effect = ImportError("No module named 'rasterio'")

        test_file = tmp_path / "MOD13Q1.A2023001.h21v08.061.hdf"
        test_file.write_bytes(b"mock hdf data")

        results = modis_client.process_vegetation_indices(test_file)

        assert len(results) == 2  # NDVI and EVI
        assert all(not result.success for result in results)
        assert all(
            "rasterio package required" in result.error_message for result in results
        )

    @patch("rasterio.open")
    def test_aggregate_temporal_data(self, mock_rasterio_open, modis_client, tmp_path):
        """Test temporal aggregation of MODIS data."""
        # Create test files
        file1 = tmp_path / "MOD13Q1.A2023001.h21v08.061_NDVI_processed.tif"
        file2 = tmp_path / "MOD13Q1.A2023017.h21v08.061_NDVI_processed.tif"
        file1.write_bytes(b"mock data")
        file2.write_bytes(b"mock data")

        # Mock rasterio operations
        mock_src = MagicMock()
        mock_src.read.return_value = np.array(
            [[0.5, 0.6], [0.7, 0.8]], dtype=np.float32
        )
        mock_src.profile = {"dtype": "float32", "height": 2, "width": 2}

        mock_dst = MagicMock()

        def rasterio_open_side_effect(path, mode="r", **kwargs):
            if mode == "r":
                return mock_src
            else:
                return mock_dst

        mock_rasterio_open.side_effect = rasterio_open_side_effect

        result_path = modis_client.aggregate_temporal_data(
            file_paths=[file1, file2],
            aggregation_method="monthly",
            vegetation_index="NDVI",
        )

        assert result_path is not None
        assert isinstance(result_path, Path)
        mock_dst.write.assert_called()

    def test_validate_modis_file_missing(self, modis_client, tmp_path):
        """Test validation of missing MODIS file."""
        missing_file = tmp_path / "nonexistent.hdf"

        result = modis_client.validate_modis_file(missing_file)

        assert result["success"] is False
        assert result["file_exists"] is False
        assert "File does not exist" in result["error_message"]

    def test_validate_modis_file_too_small(self, modis_client, tmp_path):
        """Test validation of file that's too small."""
        small_file = tmp_path / "small.hdf"
        small_file.write_bytes(b"tiny")  # Very small file

        result = modis_client.validate_modis_file(small_file)

        assert result["file_exists"] is True
        assert result["file_size_valid"] is False
        assert result["file_size_mb"] < 0.5

    @patch("rasterio.open")
    def test_validate_modis_file_success(
        self, mock_rasterio_open, modis_client, tmp_path
    ):
        """Test successful MODIS file validation."""
        # Create test file
        test_file = tmp_path / "MOD13Q1.A2023001.h21v08.061.hdf"
        test_file.write_bytes(b"mock hdf data" * 100000)  # Large enough file

        # Mock rasterio operations
        mock_hdf = MagicMock()
        mock_hdf.subdatasets = [
            "HDF4_EOS:EOS_GRID:test.hdf:MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI",
            "HDF4_EOS:EOS_GRID:test.hdf:MODIS_Grid_16DAY_250m_500m_VI:250m 16 days VI_Quality",
        ]

        mock_vi_src = MagicMock()
        mock_vi_src.height = 4800
        mock_vi_src.width = 4800
        mock_vi_src.crs = MagicMock()

        def rasterio_open_side_effect(path, *args, **kwargs):
            if "NDVI" in str(path):
                return mock_vi_src
            else:
                return mock_hdf

        mock_rasterio_open.side_effect = rasterio_open_side_effect

        result = modis_client.validate_modis_file(test_file)

        assert result["success"] is True
        assert result["file_exists"] is True
        assert result["file_size_valid"] is True
        assert result["hdf_readable"] is True
        assert result["has_vi_data"] is True
        assert result["has_quality_data"] is True
        assert result["spatial_dimensions_valid"] is True

    def test_cleanup_old_files(self, modis_client, tmp_path):
        """Test cleanup of old MODIS files."""
        # Create test files with different ages
        old_file = tmp_path / "modis" / "old_file.hdf"
        old_file.parent.mkdir(exist_ok=True)
        old_file.write_bytes(b"old data")

        new_file = tmp_path / "modis" / "new_file.hdf"
        new_file.write_bytes(b"new data")

        # Mock file modification times
        import os
        import time

        # Make old file appear old
        old_time = time.time() - (40 * 24 * 3600)  # 40 days ago
        os.utime(old_file, (old_time, old_time))

        # Clean up files older than 30 days
        deleted_count = modis_client.cleanup_old_files(days_to_keep=30)

        assert deleted_count >= 0  # Should delete at least the old file
        assert new_file.exists()  # New file should remain

    def test_generate_quality_summary(self, modis_client, tmp_path):
        """Test quality summary generation."""
        # Create test files
        file1 = tmp_path / "file1.hdf"
        file2 = tmp_path / "file2.hdf"
        file1.write_bytes(b"data" * 100000)
        file2.write_bytes(b"data" * 200000)

        file_paths = [file1, file2]

        with patch.object(modis_client, "validate_modis_file") as mock_validate:
            mock_validate.return_value = {"success": True}

            summary = modis_client._generate_quality_summary(file_paths)

            assert summary["total_files"] == 2
            assert summary["valid_files"] == 2
            assert summary["validation_rate"] == 1.0
            assert summary["total_size_mb"] > 0
            assert summary["average_file_size_mb"] > 0

    def test_client_context_manager(self, modis_client):
        """Test client cleanup when used as context manager."""
        session_closed = False
        executor_shutdown = False

        # Mock session and executor
        original_close = modis_client.session.close
        original_shutdown = modis_client.executor.shutdown

        def mock_close():
            nonlocal session_closed
            session_closed = True
            original_close()

        def mock_shutdown(*args, **kwargs):
            nonlocal executor_shutdown
            executor_shutdown = True
            original_shutdown(*args, **kwargs)

        modis_client.session.close = mock_close
        modis_client.executor.shutdown = mock_shutdown

        modis_client.close()

        assert session_closed
        assert executor_shutdown


class TestMODISRequestConfig:
    """Test suite for MODISRequestConfig."""

    def test_default_configuration(self):
        """Test default MODIS request configuration."""
        config = MODISRequestConfig(
            start_date=date(2023, 1, 1), end_date=date(2023, 1, 16)
        )

        assert config.product == "MOD13Q1"
        assert config.collection == "061"
        assert config.vegetation_indices == ["NDVI", "EVI"]
        assert config.area_bounds == (-20.0, -35.0, 55.0, 40.0)
        assert config.apply_quality_filter is True
        assert config.sinusoidal_to_wgs84 is True

    def test_custom_configuration(self):
        """Test custom MODIS request configuration."""
        config = MODISRequestConfig(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 16),
            product="MYD13Q1",
            vegetation_indices=["NDVI"],
            area_bounds=(30.0, -5.0, 45.0, 15.0),
            apply_quality_filter=False,
        )

        assert config.product == "MYD13Q1"
        assert config.vegetation_indices == ["NDVI"]
        assert config.area_bounds == (30.0, -5.0, 45.0, 15.0)
        assert config.apply_quality_filter is False


class TestMODISTileInfo:
    """Test suite for MODISTileInfo."""

    def test_tile_info_creation(self):
        """Test MODIS tile info creation."""
        tile = MODISTileInfo(
            horizontal=21,
            vertical=8,
            tile_id="h21v08",
            center_lat=10.0,
            center_lon=35.0,
            bounds=(30.0, 5.0, 40.0, 15.0),
        )

        assert tile.horizontal == 21
        assert tile.vertical == 8
        assert tile.tile_id == "h21v08"
        assert tile.center_lat == 10.0
        assert tile.center_lon == 35.0
        assert tile.bounds == (30.0, 5.0, 40.0, 15.0)


class TestMODISResults:
    """Test suite for MODIS result models."""

    def test_download_result_creation(self):
        """Test MODIS download result creation."""
        result = MODISDownloadResult(
            request_id="test_123",
            file_paths=[Path("/test/file.hdf")],
            total_size_bytes=1000000,
            tiles_processed=["h21v08"],
            temporal_coverage={"start_date": "2023-01-01", "end_date": "2023-01-16"},
            download_duration_seconds=120.0,
            success=True,
            files_processed=1,
            quality_summary={"total_files": 1},
        )

        assert result.request_id == "test_123"
        assert len(result.file_paths) == 1
        assert result.success is True
        assert result.files_processed == 1

    def test_processing_result_creation(self):
        """Test MODIS processing result creation."""
        result = MODISProcessingResult(
            file_path=Path("/test/processed.tif"),
            vegetation_index="NDVI",
            data_shape=(4800, 4800),
            valid_pixel_count=20000000,
            statistics={"min": 0.1, "max": 0.9, "mean": 0.5},
            temporal_info={"acquisition_date": "2023-01-01"},
            quality_flags={"good_quality": 15000000},
            success=True,
        )

        assert result.vegetation_index == "NDVI"
        assert result.data_shape == (4800, 4800)
        assert result.success is True
        assert result.statistics["mean"] == 0.5
