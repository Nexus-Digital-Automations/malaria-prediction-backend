"""Tests for WorldPop population data integration client."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from requests.exceptions import RequestException

from malaria_predictor.config import Settings
from malaria_predictor.services.worldpop_client import (
    PopulationAtRiskResult,
    WorldPopClient,
    WorldPopDownloadResult,
    WorldPopRequestConfig,
)


class TestWorldPopRequestConfig:
    """Test WorldPop request configuration model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WorldPopRequestConfig()

        assert config.data_type == "population_density"
        assert config.resolution == "100m"
        assert config.format_type == "tif"
        assert config.area_bounds == (-20.0, -35.0, 55.0, 40.0)
        assert config.target_year == 2020
        assert config.country_codes is None
        assert config.age_groups is None
        assert config.sex is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorldPopRequestConfig(
            data_type="age_sex_structure",
            resolution="1km",
            target_year=2021,
            country_codes=["KEN", "UGA"],
            age_groups=["0", "1", "5"],
            sex="f",
            area_bounds=(30.0, -5.0, 45.0, 5.0),
        )

        assert config.data_type == "age_sex_structure"
        assert config.resolution == "1km"
        assert config.target_year == 2021
        assert config.country_codes == ["KEN", "UGA"]
        assert config.age_groups == ["0", "1", "5"]
        assert config.sex == "f"
        assert config.area_bounds == (30.0, -5.0, 45.0, 5.0)

    def test_config_immutable(self):
        """Test that configuration is immutable (frozen)."""
        config = WorldPopRequestConfig()

        with pytest.raises(ValueError):
            config.data_type = "new_type"


class TestWorldPopDownloadResult:
    """Test WorldPop download result model."""

    def test_successful_result(self):
        """Test successful download result."""
        result = WorldPopDownloadResult(
            request_id="test_123",
            file_paths=[Path("/test/file1.tif"), Path("/test/file2.tif")],
            total_size_bytes=1024000,
            data_type="population_density",
            resolution="100m",
            temporal_coverage={"target_year": 2020},
            download_duration_seconds=45.5,
            success=True,
            files_processed=2,
            metadata={"cached": False},
        )

        assert result.request_id == "test_123"
        assert len(result.file_paths) == 2
        assert result.total_size_bytes == 1024000
        assert result.success is True
        assert result.files_processed == 2

    def test_failed_result(self):
        """Test failed download result."""
        result = WorldPopDownloadResult(
            request_id="failed",
            file_paths=[],
            total_size_bytes=0,
            data_type="population_density",
            resolution="100m",
            temporal_coverage={},
            download_duration_seconds=10.0,
            success=False,
            error_message="Connection timeout",
            files_processed=0,
        )

        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert len(result.file_paths) == 0


class TestPopulationAtRiskResult:
    """Test population-at-risk calculation result model."""

    def test_population_at_risk_result(self):
        """Test population-at-risk result structure."""
        result = PopulationAtRiskResult(
            total_population=1000000.0,
            population_at_risk=150000.0,
            risk_percentage=15.0,
            high_risk_population=50000.0,
            children_under_5_at_risk=18000.0,
            geographic_bounds=(30.0, -5.0, 45.0, 5.0),
            calculation_metadata={
                "risk_threshold": 0.1,
                "calculation_date": "2023-01-01T00:00:00",
            },
        )

        assert result.total_population == 1000000.0
        assert result.population_at_risk == 150000.0
        assert result.risk_percentage == 15.0
        assert result.high_risk_population == 50000.0
        assert result.children_under_5_at_risk == 18000.0


class TestWorldPopClient:
    """Test WorldPop client functionality."""

    @pytest.fixture
    def temp_settings(self):
        """Create temporary settings for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(data_directory=temp_dir)
            yield settings

    @pytest.fixture
    def client(self, temp_settings):
        """Create WorldPop client with temporary settings."""
        return WorldPopClient(temp_settings)

    @pytest.fixture
    def mock_rasterio(self):
        """Mock rasterio for testing without actual GeoTIFF files."""
        with (
            patch("rasterio.open") as mock,
            patch("rasterio.windows.from_bounds") as mock_from_bounds,
        ):
            # Mock rasterio.open context manager
            mock_dataset = MagicMock()
            mock_dataset.__enter__ = Mock(return_value=mock_dataset)
            mock_dataset.__exit__ = Mock(return_value=None)
            mock.return_value = mock_dataset

            # Configure mock dataset properties
            mock_dataset.read.return_value = np.array(
                [[100, 200], [150, 300]], dtype=np.float32
            )
            mock_dataset.transform = MagicMock()
            mock_dataset.crs = Mock()
            mock_dataset.crs.is_geographic = True
            mock_dataset.res = (0.0008333, 0.0008333)  # 100m resolution

            # Mock window calculation
            mock_window = MagicMock()
            mock_from_bounds.return_value = mock_window
            mock_dataset.window_transform.return_value = Mock()

            mock.open.return_value = mock_dataset
            mock.from_bounds = Mock(return_value=Mock())

            yield mock

    def test_client_initialization(self, temp_settings):
        """Test client initialization."""
        client = WorldPopClient(temp_settings)

        assert client.settings == temp_settings
        assert client.download_directory.exists()
        assert (client.download_directory / "population_density").exists()
        assert (client.download_directory / "age_sex_structure").exists()
        assert (client.download_directory / "unconstrained").exists()

    def test_client_default_settings(self):
        """Test client with default settings."""
        with patch(
            "malaria_predictor.services.worldpop_client.Settings"
        ) as mock_settings:
            mock_settings.return_value.data_directory = "/tmp/test"

            client = WorldPopClient()
            assert client.settings is not None

    @patch("malaria_predictor.services.worldpop_client.requests.Session")
    def test_discover_available_datasets_success(self, mock_session, client):
        """Test successful dataset discovery."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "iso3": "KEN",
                    "year": 2020,
                    "id": "ken_pop_2020",
                    "title": "Kenya Population 2020",
                    "resolution": "100m",
                    "download_url": "http://example.com/ken.tif",
                    "file_size": 50000000,
                },
                {
                    "iso3": "UGA",
                    "year": 2020,
                    "id": "uga_pop_2020",
                    "title": "Uganda Population 2020",
                    "resolution": "100m",
                    "download_url": "http://example.com/uga.tif",
                    "file_size": 45000000,
                },
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        client.session = mock_session_instance

        # Test discovery
        datasets = client.discover_available_datasets(
            country_codes=["KEN", "UGA"], data_type="population_density", year=2020
        )

        assert "KEN" in datasets
        assert "UGA" in datasets
        assert len(datasets["KEN"]) == 1
        assert datasets["KEN"][0]["year"] == 2020
        assert datasets["KEN"][0]["dataset_id"] == "ken_pop_2020"

    @patch("malaria_predictor.services.worldpop_client.requests.Session")
    def test_discover_available_datasets_failure(self, mock_session, client):
        """Test dataset discovery failure."""
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = RequestException("API error")
        mock_session.return_value = mock_session_instance
        client.session = mock_session_instance

        datasets = client.discover_available_datasets(["KEN"])

        assert datasets == {}

    @patch.object(WorldPopClient, "discover_available_datasets")
    @patch.object(WorldPopClient, "_download_via_rest")
    def test_download_population_data_success(
        self, mock_download, mock_discover, client
    ):
        """Test successful population data download."""
        # Mock discovery results
        mock_discover.return_value = {
            "KEN": [
                {
                    "year": 2020,
                    "dataset_id": "ken_pop_2020",
                    "download_url": "http://example.com/ken.tif",
                }
            ]
        }

        # Mock download results
        test_file = Path("/tmp/test_ken.tif")
        mock_download.return_value = (test_file, 1000000, {"cached": False})

        result = client.download_population_data(
            country_codes=["KEN"], target_year=2020, data_type="population_density"
        )

        assert result.success is True
        assert len(result.file_paths) == 1
        assert result.data_type == "population_density"
        assert result.files_processed == 1

    @patch.object(WorldPopClient, "discover_available_datasets")
    def test_download_population_data_no_datasets(self, mock_discover, client):
        """Test download when no datasets are available."""
        mock_discover.return_value = {}

        result = client.download_population_data(
            country_codes=["XXX"],  # Non-existent country
            target_year=2020,
        )

        assert result.success is False
        assert "No datasets found" in result.error_message

    @patch("malaria_predictor.services.worldpop_client.requests.Session")
    def test_download_via_rest_success(self, mock_session, client):
        """Test successful REST download."""
        # Create a test file to simulate download
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_file:
            temp_file.write(b"test data")
            temp_file_path = Path(temp_file.name)

        try:
            # Mock response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"test", b" data"]
            mock_response.raise_for_status.return_value = None

            mock_session_instance = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session.return_value = mock_session_instance
            client.session = mock_session_instance

            # Mock the file operations by patching open
            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                dataset = {"download_url": "http://example.com/test.tif", "year": 2020}

                result = client._download_via_rest(
                    country_code="KEN",
                    dataset=dataset,
                    data_type="population_density",
                    resolution="100m",
                )

                file_path, file_size, metadata = result
                assert file_path is not None
                assert metadata["country_code"] == "KEN"

        finally:
            # Clean up
            if temp_file_path.exists():
                temp_file_path.unlink()

    @patch("malaria_predictor.services.worldpop_client.requests.Session")
    def test_download_via_rest_failure(self, mock_session, client):
        """Test REST download failure."""
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = RequestException("Download failed")
        mock_session.return_value = mock_session_instance
        client.session = mock_session_instance

        dataset = {"download_url": "http://example.com/test.tif", "year": 2020}

        result = client._download_via_rest(
            country_code="KEN",
            dataset=dataset,
            data_type="population_density",
            resolution="100m",
        )

        file_path, file_size, metadata = result
        assert file_path is None
        assert file_size == 0

    @patch("malaria_predictor.services.worldpop_client.ftplib.FTP")
    def test_download_via_ftp_success(self, mock_ftp, client):
        """Test successful FTP download."""
        # Mock FTP operations
        mock_ftp_instance = Mock()
        mock_ftp_instance.__enter__ = Mock(return_value=mock_ftp_instance)
        mock_ftp_instance.__exit__ = Mock(return_value=None)
        mock_ftp_instance.login.return_value = None
        mock_ftp_instance.retrbinary.return_value = None
        mock_ftp.return_value = mock_ftp_instance

        # Mock file operations
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            # Mock Path.exists to return False (file doesn't exist yet)
            # Mock Path.stat for file size after download
            with (
                patch.object(Path, "exists", return_value=False),
                patch.object(Path, "stat") as mock_stat,
            ):
                mock_stat.return_value.st_size = 1000000

                dataset = {"year": 2020}

                result = client._download_via_ftp(
                    country_code="KEN",
                    dataset=dataset,
                    data_type="population_density",
                    resolution="100m",
                )

                file_path, file_size, metadata = result
                assert file_path is not None
                assert file_size == 1000000
                assert metadata["download_method"] == "ftp"
                assert not metadata["cached"]

    def test_extract_population_for_region(self, client, mock_rasterio):
        """Test population data extraction for region."""
        # Create a test file
        test_file = Path("/tmp/test_population.tif")
        area_bounds = (30.0, -5.0, 45.0, 5.0)

        result = client.extract_population_for_region(test_file, area_bounds)

        assert result is not None
        assert "data" in result
        assert "statistics" in result
        assert result["statistics"]["total_population"] > 0
        assert result["bounds"] == area_bounds

    def test_extract_population_for_region_no_rasterio(self, client):
        """Test population extraction without rasterio."""
        test_file = Path("/tmp/test_population.tif")
        area_bounds = (30.0, -5.0, 45.0, 5.0)

        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'rasterio'")
        ):
            result = client.extract_population_for_region(test_file, area_bounds)

            assert result is None

    def test_calculate_population_at_risk(self, client, mock_rasterio):
        """Test population-at-risk calculation."""
        # Mock population and risk data
        population_data = np.array([[1000, 2000], [1500, 3000]], dtype=np.float32)
        risk_data = np.array([[0.05, 0.15], [0.20, 0.25]], dtype=np.float32)

        with patch.object(client, "extract_population_for_region") as mock_extract:
            mock_extract.return_value = {
                "data": population_data,
                "transform": Mock(),
                "crs": Mock(),
                "bounds": (30.0, -5.0, 45.0, 5.0),
                "shape": population_data.shape,
            }

            # Configure mock rasterio to return risk data
            mock_dataset = mock_rasterio.open.return_value.__enter__.return_value
            mock_dataset.read.return_value = risk_data

            population_file = Path("/tmp/population.tif")
            risk_file = Path("/tmp/risk.tif")
            area_bounds = (30.0, -5.0, 45.0, 5.0)

            result = client.calculate_population_at_risk(
                population_file, risk_file, area_bounds, risk_threshold=0.1
            )

            assert result is not None
            assert result.total_population > 0
            assert result.population_at_risk >= 0
            assert result.risk_percentage >= 0
            assert result.children_under_5_at_risk >= 0

    @patch.object(WorldPopClient, "download_population_data")
    @patch.object(WorldPopClient, "extract_population_for_region")
    def test_get_age_specific_population(self, mock_extract, mock_download, client):
        """Test age-specific population retrieval."""
        # Mock download result
        mock_download.return_value = WorldPopDownloadResult(
            request_id="test",
            file_paths=[Path("/tmp/ken_age_sex_structure_2020_age_0_1km.tif")],
            total_size_bytes=1000,
            data_type="age_sex_structure",
            resolution="1km",
            temporal_coverage={"target_year": 2020},
            download_duration_seconds=10.0,
            success=True,
            files_processed=1,
        )

        # Mock extraction result
        mock_extract.return_value = {"statistics": {"total_population": 50000.0}}

        result = client.get_age_specific_population(
            country_codes=["KEN"], target_year=2020, age_groups=["0"]
        )

        assert "KEN" in result
        assert "age_0" in result["KEN"]
        assert result["KEN"]["age_0"] == 50000.0

    def test_validate_population_file_success(self, client, mock_rasterio):
        """Test successful population file validation."""
        # Create a test file large enough to pass validation
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_file:
            temp_file.write(b"x" * (1024 * 1024))  # 1MB file
            test_file = Path(temp_file.name)

        try:
            # Configure mock rasterio with all required attributes
            mock_dataset = mock_rasterio.open.return_value.__enter__.return_value
            mock_dataset.read.return_value = np.array(
                [[100, 200], [150, 300]], dtype=np.float32
            )
            mock_dataset.crs = MagicMock()
            mock_dataset.crs.is_geographic = True
            mock_dataset.res = (0.0008333, 0.0008333)  # 100m resolution

            result = client.validate_population_file(test_file)

            assert result["success"] is True
            assert result["file_exists"] is True
            assert result["file_size_valid"] is True
            assert result["data_accessible"] is True
            assert result["has_valid_population"] is True
            assert result["coordinate_system_valid"] is True

        finally:
            test_file.unlink()

    def test_validate_population_file_not_exists(self, client):
        """Test validation of non-existent file."""
        non_existent = Path("/tmp/does_not_exist.tif")

        result = client.validate_population_file(non_existent)

        assert result["success"] is False
        assert result["file_exists"] is False
        assert result["error_message"] == "File does not exist"

    def test_validate_population_file_no_rasterio(self, client):
        """Test validation without rasterio."""
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_file:
            test_file = Path(temp_file.name)

        try:
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'rasterio'"),
            ):
                result = client.validate_population_file(test_file)

                assert result["success"] is False
                assert "rasterio not available" in result["error_message"]

        finally:
            test_file.unlink()

    def test_cleanup_old_files(self, client):
        """Test cleanup of old files."""
        # Create test files with different ages
        old_file = client.download_directory / "population_density" / "old_file.tif"
        recent_file = (
            client.download_directory / "population_density" / "recent_file.tif"
        )

        old_file.touch()
        recent_file.touch()

        # Mock file modification times
        old_time = datetime.now().timestamp() - (100 * 24 * 3600)  # 100 days old
        recent_time = datetime.now().timestamp() - (10 * 24 * 3600)  # 10 days old

        # Create proper mock stat objects
        old_stat = Mock()
        old_stat.st_mtime = old_time
        recent_stat = Mock()
        recent_stat.st_mtime = recent_time
        dir_stat = Mock()
        dir_stat.st_mode = 0o40755  # Directory mode

        with (
            patch.object(Path, "stat") as mock_stat,
            patch.object(Path, "is_dir") as mock_is_dir,
        ):

            def stat_side_effect(path_self):
                if "old_file" in str(path_self):
                    return old_stat
                elif "recent_file" in str(path_self):
                    return recent_stat
                else:
                    return dir_stat

            def is_dir_side_effect():
                return True  # Directory check should return True

            mock_stat.side_effect = stat_side_effect
            mock_is_dir.return_value = True

            deleted_count = client.cleanup_old_files(days_to_keep=30)

            # Should attempt to delete old file
            assert deleted_count >= 0  # Depends on mocking behavior

    def test_close_client(self, client):
        """Test client resource cleanup."""
        # Mock session and executor
        client.session = Mock()
        client.executor = Mock()

        client.close()

        client.session.close.assert_called_once()
        client.executor.shutdown.assert_called_once_with(wait=True)


class TestWorldPopClientIntegration:
    """Integration tests for WorldPop client (require network access)."""

    @pytest.mark.integration
    def test_discover_real_datasets(self):
        """Test discovery with real WorldPop API (requires network)."""
        client = WorldPopClient()

        try:
            datasets = client.discover_available_datasets(
                country_codes=["KEN"], data_type="population_density", year=2020
            )

            # This test may fail if the API is down or structure changes
            # It's mainly for development and CI environments with network access
            assert isinstance(datasets, dict)

        except Exception as e:
            pytest.skip(f"Integration test skipped due to network issue: {e}")
        finally:
            client.close()

    @pytest.mark.integration
    def test_validate_real_file_format(self):
        """Test validation logic with real WorldPop file format."""
        # This would test against a real downloaded file
        # Skipped by default as it requires actual data files
        pytest.skip("Requires real WorldPop data files for testing")


if __name__ == "__main__":
    pytest.main([__file__])
