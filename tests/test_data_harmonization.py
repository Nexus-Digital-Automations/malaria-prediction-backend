"""
Comprehensive tests for the data harmonization pipeline.

Tests cover temporal harmonization, spatial harmonization, feature engineering,
quality management, and the unified harmonization service.
"""

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import h5py
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from malaria_predictor.config import Settings
from malaria_predictor.services.data_harmonizer import (
    HarmonizedDataResult,
    SpatialHarmonizer,
    TemporalHarmonizer,
)
from malaria_predictor.services.feature_engineering import (
    FeatureEngineer,
    QualityManager,
)
from malaria_predictor.services.unified_data_harmonizer import (
    CacheManager,
    UnifiedDataHarmonizer,
)


class TestTemporalHarmonizer:
    """Test suite for TemporalHarmonizer class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.harmonizer = TemporalHarmonizer()

        # Create sample datasets
        self.era5_data = self._create_sample_era5_dataset()
        self.chirps_data = self._create_sample_chirps_dataset()
        self.modis_data = self._create_sample_modis_dataset()
        self.map_data = self._create_sample_map_dataset()
        self.worldpop_data = self._create_sample_worldpop_dataset()

    def _create_sample_era5_dataset(self):
        """Create sample ERA5 dataset."""
        dates = pd.date_range("2023-01-01", "2023-01-31", freq="D")
        lats = np.linspace(-10, 10, 20)
        lons = np.linspace(0, 20, 20)

        # Temperature data with realistic values
        temp_data = 25 + 5 * np.random.randn(len(dates), len(lats), len(lons))

        return xr.Dataset(
            {"temperature_2m": (["time", "latitude", "longitude"], temp_data)},
            coords={"time": dates, "latitude": lats, "longitude": lons},
        )

    def _create_sample_chirps_dataset(self):
        """Create sample CHIRPS dataset."""
        dates = pd.date_range("2023-01-01", "2023-01-31", freq="D")
        lats = np.linspace(-10, 10, 20)
        lons = np.linspace(0, 20, 20)

        # Precipitation data
        precip_data = np.abs(2 * np.random.randn(len(dates), len(lats), len(lons)))

        return xr.Dataset(
            {"precipitation": (["time", "latitude", "longitude"], precip_data)},
            coords={"time": dates, "latitude": lats, "longitude": lons},
        )

    def _create_sample_modis_dataset(self):
        """Create sample MODIS dataset."""
        # 16-day composites
        dates = pd.date_range("2023-01-01", "2023-01-31", freq="16D")
        lats = np.linspace(-10, 10, 20)
        lons = np.linspace(0, 20, 20)

        # NDVI data
        ndvi_data = 0.3 + 0.4 * np.random.rand(len(dates), len(lats), len(lons))

        return xr.Dataset(
            {"ndvi": (["time", "latitude", "longitude"], ndvi_data)},
            coords={"time": dates, "latitude": lats, "longitude": lons},
        )

    def _create_sample_map_dataset(self):
        """Create sample MAP dataset."""
        lats = np.linspace(-10, 10, 20)
        lons = np.linspace(0, 20, 20)

        # Malaria prevalence data
        pr_data = 20 * np.random.rand(len(lats), len(lons))

        return xr.Dataset(
            {"pr": (["latitude", "longitude"], pr_data)},
            coords={"latitude": lats, "longitude": lons},
        )

    def _create_sample_worldpop_dataset(self):
        """Create sample WorldPop dataset."""
        lats = np.linspace(-10, 10, 20)
        lons = np.linspace(0, 20, 20)

        # Population density data
        pop_data = 100 * np.random.rand(len(lats), len(lons))

        return xr.Dataset(
            {"population": (["latitude", "longitude"], pop_data)},
            coords={"latitude": lats, "longitude": lons},
        )

    def test_create_unified_temporal_index(self):
        """Test creation of unified temporal index."""
        data_sources = {
            "era5": self.era5_data,
            "chirps": self.chirps_data,
            "modis": self.modis_data,
        }

        temporal_index = self.harmonizer._create_unified_temporal_index(
            data_sources, "daily"
        )

        assert isinstance(temporal_index, pd.DatetimeIndex)
        assert len(temporal_index) > 0
        assert temporal_index.freq == "D"

    def test_resample_daily_data(self):
        """Test resampling of daily data."""
        temporal_index = pd.date_range("2023-01-01", "2023-01-31", freq="D")

        resampled = self.harmonizer._resample_daily_data(
            self.era5_data, temporal_index, "daily"
        )

        assert isinstance(resampled, xr.Dataset)
        assert "temperature_2m" in resampled
        assert len(resampled.time) == len(temporal_index)

    def test_interpolate_modis_data(self):
        """Test interpolation of MODIS 16-day composites."""
        temporal_index = pd.date_range("2023-01-01", "2023-01-31", freq="D")

        interpolated = self.harmonizer._interpolate_modis_data(
            self.modis_data, temporal_index
        )

        assert isinstance(interpolated, xr.Dataset)
        assert "ndvi" in interpolated
        assert len(interpolated.time) == len(temporal_index)

    def test_interpolate_annual_data(self):
        """Test interpolation of annual data."""
        temporal_index = pd.date_range("2023-01-01", "2023-01-31", freq="D")

        interpolated = self.harmonizer._interpolate_annual_data(
            self.map_data, temporal_index
        )

        assert isinstance(interpolated, xr.Dataset)
        assert "pr" in interpolated
        assert len(interpolated.time) == len(temporal_index)

    def test_harmonize_temporal_full_pipeline(self):
        """Test complete temporal harmonization pipeline."""
        data_sources = {
            "era5": self.era5_data,
            "chirps": self.chirps_data,
            "modis": self.modis_data,
            "map": self.map_data,
            "worldpop": self.worldpop_data,
        }

        harmonized = self.harmonizer.harmonize_temporal(data_sources, "daily")

        assert isinstance(harmonized, dict)
        assert len(harmonized) == len(data_sources)

        # Check that all datasets have the same temporal dimension
        time_lengths = [len(ds.time) for ds in harmonized.values()]
        assert len(set(time_lengths)) == 1  # All should be the same length

    def test_fill_temporal_gaps(self):
        """Test temporal gap filling."""
        # Create data with gaps
        era5_with_gaps = self.era5_data.copy()
        era5_with_gaps["temperature_2m"][5:8, :, :] = np.nan

        data_dict = {"era5": era5_with_gaps}
        filled_data = self.harmonizer.fill_temporal_gaps(data_dict)

        assert "era5" in filled_data
        # Check that some gaps were filled
        original_nans = np.sum(np.isnan(era5_with_gaps["temperature_2m"].values))
        filled_nans = np.sum(np.isnan(filled_data["era5"]["temperature_2m"].values))
        assert filled_nans <= original_nans


class TestSpatialHarmonizer:
    """Test suite for SpatialHarmonizer class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.harmonizer = SpatialHarmonizer(target_resolution="1km")

    def test_create_target_grid(self):
        """Test creation of target spatial grid."""
        data_sources = {
            "era5": {"bounds": (-10, -5, 10, 5)},
            "chirps": {"bounds": (-8, -3, 8, 3)},
        }

        target_grid = self.harmonizer._create_target_grid(data_sources)

        assert isinstance(target_grid, dict)
        assert "bounds" in target_grid
        assert "width" in target_grid
        assert "height" in target_grid
        assert "transform" in target_grid
        assert "crs" in target_grid

        # Check bounds are union of input bounds
        bounds = target_grid["bounds"]
        assert bounds[0] <= -10  # west
        assert bounds[1] <= -5  # south
        assert bounds[2] >= 10  # east
        assert bounds[3] >= 5  # north

    def test_resample_from_array(self):
        """Test resampling from numpy array."""
        # Create sample data
        data_array = np.random.rand(50, 50)
        target_grid = {
            "bounds": (-1, -1, 1, 1),
            "width": 100,
            "height": 100,
            "transform": None,  # Will be created
            "crs": "EPSG:4326",
        }

        # Create transform for target grid
        from rasterio.transform import from_bounds

        target_grid["transform"] = from_bounds(
            target_grid["bounds"][0],
            target_grid["bounds"][1],
            target_grid["bounds"][2],
            target_grid["bounds"][3],
            target_grid["width"],
            target_grid["height"],
        )

        data_info = {"array": data_array, "bounds": (-2, -2, 2, 2), "crs": "EPSG:4326"}

        # Create transform for source data
        from rasterio.transform import from_bounds

        data_info["transform"] = from_bounds(
            data_info["bounds"][0],
            data_info["bounds"][1],
            data_info["bounds"][2],
            data_info["bounds"][3],
            data_array.shape[1],
            data_array.shape[0],
        )

        result = self.harmonizer._resample_from_array(
            data_info, target_grid, "bilinear"
        )

        assert isinstance(result, dict)
        assert "data" in result
        assert result["data"].shape == (target_grid["height"], target_grid["width"])


class TestFeatureEngineer:
    """Test suite for FeatureEngineer class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engineer = FeatureEngineer()

        # Create sample harmonized data
        self.harmonized_data = self._create_sample_harmonized_data()

    def _create_sample_harmonized_data(self):
        """Create sample harmonized data."""
        return {
            "era5": {"data": 25 + 5 * np.random.randn(100, 100).astype(np.float32)},
            "chirps": {
                "data": np.abs(10 * np.random.randn(100, 100)).astype(np.float32)
            },
            "modis": {"data": 0.3 + 0.4 * np.random.rand(100, 100).astype(np.float32)},
            "map": {"data": 20 * np.random.rand(100, 100).astype(np.float32)},
            "worldpop": {"data": 100 * np.random.rand(100, 100).astype(np.float32)},
        }

    def test_temperature_suitability_curve(self):
        """Test temperature suitability calculation."""
        temperature = np.array([15, 20, 25, 27.5, 30, 35, 40])
        suitability = self.engineer._temperature_suitability_curve(temperature)

        assert len(suitability) == len(temperature)
        assert np.all(suitability >= 0)
        assert np.all(suitability <= 1)

        # Check that optimal range (25-30°C) has high suitability
        optimal_mask = (temperature >= 25) & (temperature <= 30)
        assert np.all(suitability[optimal_mask] >= 0.8)

    def test_calculate_breeding_habitat(self):
        """Test breeding habitat index calculation."""
        temperature = np.full((50, 50), 27.0)  # Optimal temperature
        precipitation = np.full((50, 50), 30.0)  # Good precipitation
        ndvi = np.full((50, 50), 0.5)  # Moderate vegetation

        breeding_index = self.engineer._calculate_breeding_habitat(
            temperature, precipitation, ndvi
        )

        assert breeding_index.shape == (50, 50)
        assert np.all(breeding_index >= 0)
        assert np.all(breeding_index <= 1)
        assert np.mean(breeding_index) > 0.5  # Should be favorable

    def test_extract_basic_features(self):
        """Test extraction of basic features."""
        features = self.engineer._extract_basic_features(self.harmonized_data)

        assert isinstance(features, dict)

        # Check ERA5 features
        assert "era5_temp_mean" in features
        assert features["era5_temp_mean"].shape == (100, 100)

        # Check CHIRPS features
        assert "chirps_precip_daily" in features
        assert features["chirps_precip_daily"].shape == (100, 100)

        # Check MODIS features
        assert "modis_ndvi_current" in features
        assert features["modis_ndvi_current"].shape == (100, 100)

        # Check MAP features
        assert "map_pr_baseline" in features
        assert features["map_pr_baseline"].shape == (100, 100)

        # Check WorldPop features
        assert "worldpop_density" in features
        assert "worldpop_density_log" in features
        assert features["worldpop_density"].shape == (100, 100)

    def test_calculate_derived_features(self):
        """Test calculation of derived features."""
        basic_features = self.engineer._extract_basic_features(self.harmonized_data)
        derived_features = self.engineer._calculate_derived_features(basic_features)

        assert isinstance(derived_features, dict)

        # Check temperature suitability
        if "era5_temp_suitability" in derived_features:
            suitability = derived_features["era5_temp_suitability"]
            assert np.all(suitability >= 0)
            assert np.all(suitability <= 1)

        # Check population at risk
        if "population_at_risk" in derived_features:
            pop_risk = derived_features["population_at_risk"]
            assert pop_risk.shape == (100, 100)
            assert np.all(pop_risk >= 0)

    def test_generate_ml_features_full_pipeline(self):
        """Test complete ML feature generation pipeline."""
        target_date = datetime(2023, 6, 15)

        features = self.engineer.generate_ml_features(self.harmonized_data, target_date)

        assert isinstance(features, dict)
        assert len(features) > 0

        # Check that all features are float32 arrays
        for _name, feature_array in features.items():
            assert isinstance(feature_array, np.ndarray)
            assert feature_array.dtype == np.float32
            assert feature_array.shape == (100, 100)

    def test_validate_and_normalize(self):
        """Test feature validation and normalization."""
        # Create features with various issues
        features = {
            "valid_feature": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
            "inf_feature": np.array([[1.0, np.inf], [3.0, 4.0]], dtype=np.float64),
            "none_feature": None,
        }

        validated = self.engineer._validate_and_normalize(features)

        assert "valid_feature" in validated
        assert "inf_feature" in validated
        assert "none_feature" not in validated

        # Check that inf values were converted to nan
        assert np.isnan(validated["inf_feature"][0, 1])

        # Check that all features are float32
        for feature_array in validated.values():
            assert feature_array.dtype == np.float32


class TestQualityManager:
    """Test suite for QualityManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.quality_manager = QualityManager()

        # Create sample harmonized data
        self.harmonized_data = self._create_sample_harmonized_data()

    def _create_sample_harmonized_data(self):
        """Create sample harmonized data."""
        return {
            "era5": {"data": 25 + 5 * np.random.randn(50, 50).astype(np.float32)},
            "chirps": {"data": np.abs(10 * np.random.randn(50, 50)).astype(np.float32)},
            "modis": {"data": 0.3 + 0.4 * np.random.rand(50, 50).astype(np.float32)},
        }

    def test_assess_source_quality_era5(self):
        """Test quality assessment for ERA5 data."""
        source_data = {"data": 25 + 5 * np.random.randn(100, 100)}

        quality = self.quality_manager._assess_source_quality("era5", source_data)

        assert isinstance(quality, dict)
        assert "score" in quality
        assert "flags" in quality
        assert "details" in quality
        assert 0 <= quality["score"] <= 1

    def test_assess_source_quality_with_outliers(self):
        """Test quality assessment with outliers."""
        # Create data with temperature outliers
        data_array = np.full((100, 100), 25.0)
        data_array[0, 0] = 100.0  # Extreme temperature
        source_data = {"data": data_array}

        quality = self.quality_manager._assess_source_quality("era5", source_data)

        assert quality["score"] < 1.0  # Should be penalized
        assert len(quality["flags"]) > 0

    def test_assess_source_quality_with_missing_data(self):
        """Test quality assessment with missing data."""
        data_array = np.full((100, 100), 25.0)
        data_array[0:10, 0:10] = np.nan  # Missing data region
        source_data = {"data": data_array}

        quality = self.quality_manager._assess_source_quality("era5", source_data)

        assert quality["score"] < 1.0  # Should be penalized
        assert "missing_data_ratio" in quality["details"]

    def test_validate_cross_source_consistency(self):
        """Test cross-source consistency validation."""
        consistency = self.quality_manager._validate_cross_source_consistency(
            self.harmonized_data
        )

        assert isinstance(consistency, dict)
        assert "overall_consistency" in consistency
        assert "checks" in consistency
        assert "num_checks" in consistency
        assert isinstance(consistency["overall_consistency"], bool)

    def test_assess_data_completeness(self):
        """Test data completeness assessment."""
        completeness = self.quality_manager._assess_data_completeness(
            self.harmonized_data
        )

        assert isinstance(completeness, dict)
        assert "source_completeness" in completeness
        assert "overall_completeness" in completeness
        assert "complete_sources" in completeness
        assert "total_sources" in completeness

        assert 0 <= completeness["overall_completeness"] <= 1
        assert completeness["total_sources"] == len(self.harmonized_data)

    def test_assess_harmonized_quality_full_pipeline(self):
        """Test complete quality assessment pipeline."""
        quality_assessment = self.quality_manager.assess_harmonized_quality(
            self.harmonized_data
        )

        assert isinstance(quality_assessment, dict)
        assert "overall_quality" in quality_assessment
        assert "source_quality" in quality_assessment
        assert "consistency_checks" in quality_assessment
        assert "data_completeness" in quality_assessment
        assert "quality_category" in quality_assessment

        assert 0 <= quality_assessment["overall_quality"] <= 1
        assert quality_assessment["quality_category"] in ["high", "medium", "low"]


class TestCacheManager:
    """Test suite for CacheManager class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(self.temp_dir)

        # Create sample harmonized data result
        self.sample_result = self._create_sample_result()

    def _create_sample_result(self):
        """Create sample harmonized data result."""
        return HarmonizedDataResult(
            data={
                "feature1": np.random.rand(50, 50).astype(np.float32),
                "feature2": np.random.rand(50, 50).astype(np.float32),
            },
            metadata={"test": True},
            quality_metrics={"overall_quality": 0.8},
            feature_names=["feature1", "feature2"],
            spatial_bounds=(-10, -5, 10, 5),
            temporal_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
            target_resolution="1km",
            processing_timestamp=datetime.now(),
        )

    def test_cache_and_retrieve_data(self):
        """Test caching and retrieving harmonized data."""
        region_bounds = (-10, -5, 10, 5)
        date_range = (date(2023, 1, 1), date(2023, 1, 31))
        resolution = "1km"

        # Cache the data
        self.cache_manager.cache_harmonized_data(
            self.sample_result, region_bounds, date_range, resolution
        )

        # Retrieve the data
        retrieved = self.cache_manager.get_cached_harmonized_data(
            region_bounds, date_range, resolution
        )

        assert retrieved is not None
        assert isinstance(retrieved, HarmonizedDataResult)
        assert len(retrieved.data) == len(self.sample_result.data)
        assert retrieved.feature_names == self.sample_result.feature_names

    def test_cache_key_generation(self):
        """Test cache key generation."""
        region_bounds = (-10.123, -5.456, 10.789, 5.012)
        date_range = (date(2023, 1, 1), date(2023, 1, 31))
        resolution = "1km"

        cache_key = self.cache_manager._generate_cache_key(
            region_bounds, date_range, resolution
        )

        assert isinstance(cache_key, str)
        assert "harmonized" in cache_key
        assert "2023-01-01" in cache_key
        assert "2023-01-31" in cache_key
        assert "1km" in cache_key

    def test_cache_expiration(self):
        """Test cache expiration logic."""
        # Create a cache file with old timestamp
        region_bounds = (-10, -5, 10, 5)
        date_range = (date(2023, 1, 1), date(2023, 1, 31))
        resolution = "1km"

        cache_key = self.cache_manager._generate_cache_key(
            region_bounds, date_range, resolution
        )
        cache_path = self.cache_manager.cache_dir / f"{cache_key}.h5"

        # Create cache file with old timestamp
        with h5py.File(cache_path, "w") as f:
            f.create_dataset("features/test", data=np.array([1, 2, 3]))
            old_time = datetime.now() - timedelta(hours=25)
            f.attrs["created"] = old_time.isoformat()
            f.attrs["date_range_start"] = date_range[0].isoformat()
            f.attrs["date_range_end"] = date_range[1].isoformat()

        # Should not retrieve expired cache
        is_valid = self.cache_manager._is_cache_valid(cache_path, date_range)
        assert not is_valid


@pytest.mark.asyncio
class TestUnifiedDataHarmonizer:
    """Test suite for UnifiedDataHarmonizer class."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock settings object
        self.settings = Mock()
        self.settings.cache_directory = tempfile.mkdtemp()

        # Create persistent mock clients that will be used throughout the test
        self.mock_era5_client = Mock()
        self.mock_chirps_client = Mock()
        self.mock_modis_client = Mock()
        self.mock_map_client = Mock()
        self.mock_worldpop_client = Mock()

        # Patch the client classes to return our mocks
        patcher_era5 = patch(
            "malaria_predictor.services.unified_data_harmonizer.ERA5Client"
        )
        patcher_chirps = patch(
            "malaria_predictor.services.unified_data_harmonizer.CHIRPSClient"
        )
        patcher_modis = patch(
            "malaria_predictor.services.unified_data_harmonizer.MODISClient"
        )
        patcher_map = patch(
            "malaria_predictor.services.unified_data_harmonizer.MAPClient"
        )
        patcher_worldpop = patch(
            "malaria_predictor.services.unified_data_harmonizer.WorldPopClient"
        )

        self.mock_era5_class = patcher_era5.start()
        self.mock_chirps_class = patcher_chirps.start()
        self.mock_modis_class = patcher_modis.start()
        self.mock_map_class = patcher_map.start()
        self.mock_worldpop_class = patcher_worldpop.start()

        # Configure the classes to return our mock instances
        self.mock_era5_class.return_value = self.mock_era5_client
        self.mock_chirps_class.return_value = self.mock_chirps_client
        self.mock_modis_class.return_value = self.mock_modis_client
        self.mock_map_class.return_value = self.mock_map_client
        self.mock_worldpop_class.return_value = self.mock_worldpop_client

        # Store patchers for cleanup
        self.patchers = [
            patcher_era5,
            patcher_chirps,
            patcher_modis,
            patcher_map,
            patcher_worldpop,
        ]

        # Now create the harmonizer
        self.harmonizer = UnifiedDataHarmonizer(self.settings)

    def teardown_method(self):
        """Clean up patches."""
        for patcher in self.patchers:
            patcher.stop()

    def test_initialization(self):
        """Test harmonizer initialization."""
        assert hasattr(self.harmonizer, "era5_client")
        assert hasattr(self.harmonizer, "chirps_client")
        assert hasattr(self.harmonizer, "modis_client")
        assert hasattr(self.harmonizer, "map_client")
        assert hasattr(self.harmonizer, "worldpop_client")

        assert hasattr(self.harmonizer, "temporal_harmonizer")
        assert hasattr(self.harmonizer, "spatial_harmonizer")
        assert hasattr(self.harmonizer, "feature_engineer")
        assert hasattr(self.harmonizer, "quality_manager")
        assert hasattr(self.harmonizer, "cache_manager")

    def test_validate_region_bounds(self):
        """Test region bounds validation."""
        # Valid bounds
        valid_bounds = (-10, -5, 10, 5)
        assert self.harmonizer.validate_region_bounds(valid_bounds)

        # Invalid bounds (west >= east)
        invalid_bounds1 = (10, -5, -10, 5)
        assert not self.harmonizer.validate_region_bounds(invalid_bounds1)

        # Invalid bounds (south >= north)
        invalid_bounds2 = (-10, 5, 10, -5)
        assert not self.harmonizer.validate_region_bounds(invalid_bounds2)

        # Invalid bounds (out of range)
        invalid_bounds3 = (-200, -5, 10, 5)
        assert not self.harmonizer.validate_region_bounds(invalid_bounds3)

        # Too large bounds
        invalid_bounds4 = (-50, -50, 50, 50)
        assert not self.harmonizer.validate_region_bounds(invalid_bounds4)

    def test_bounds_to_countries(self):
        """Test conversion of bounds to country list."""
        africa_bounds = (0, -10, 20, 10)
        countries = self.harmonizer._bounds_to_countries(africa_bounds)

        assert isinstance(countries, list)
        assert len(countries) > 0
        assert all(isinstance(country, str) for country in countries)

    async def test_download_era5_data(self):
        """Test ERA5 data download."""
        # Mock the client method
        mock_result = Mock()
        mock_result.success = True

        with patch.object(
            self.harmonizer.era5_client,
            "download_temperature_data",
            return_value=mock_result,
        ):
            result = await self.harmonizer._download_era5_data(
                date(2023, 1, 1), date(2023, 1, 31), (-10, -5, 10, 5)
            )

            assert result == mock_result

    @patch("malaria_predictor.services.unified_data_harmonizer.asyncio.to_thread")
    async def test_orchestrate_data_download(self, mock_to_thread):
        """Test orchestration of data downloads."""
        # Mock successful downloads
        mock_results = []
        for _i in range(5):  # 5 data sources
            mock_result = Mock()
            mock_result.success = True
            mock_results.append(mock_result)

        mock_to_thread.side_effect = mock_results

        result = await self.harmonizer._orchestrate_data_download(
            (-10, -5, 10, 5), date(2023, 1, 1), date(2023, 1, 31)
        )

        assert isinstance(result, dict)
        assert len(result) == 5  # Should have all 5 sources

        # Verify all download methods were called
        assert mock_to_thread.call_count == 5

    def test_convert_to_xarray(self):
        """Test conversion of raw data to xarray datasets."""
        # Create mock raw data
        mock_result = Mock()
        mock_result.file_paths = []
        mock_result.data = np.random.rand(10, 50, 50)

        raw_data = {"era5": mock_result}

        xr_datasets = self.harmonizer._convert_to_xarray(raw_data)

        assert isinstance(xr_datasets, dict)
        assert "era5" in xr_datasets
        assert isinstance(xr_datasets["era5"], xr.Dataset)

    def test_convert_for_spatial_harmonization(self):
        """Test conversion of temporal data for spatial harmonization."""
        # Create sample xarray data
        dates = pd.date_range("2023-01-01", "2023-01-03", freq="D")
        data = np.random.rand(3, 20, 20)

        xr_data = {
            "era5": xr.Dataset(
                {"temperature": (["time", "y", "x"], data)}, coords={"time": dates}
            )
        }

        raw_data = {"era5": Mock()}

        spatial_data = self.harmonizer._convert_for_spatial_harmonization(
            xr_data, raw_data
        )

        assert isinstance(spatial_data, dict)
        assert "era5" in spatial_data
        assert "array" in spatial_data["era5"]
        assert spatial_data["era5"]["array"].shape == (20, 20)  # Latest time slice

    def test_get_feature_schema(self):
        """Test getting feature schema."""
        schema = self.harmonizer.get_feature_schema()

        assert isinstance(schema, dict)
        assert len(schema) > 0

        # Check some expected features
        expected_features = [
            "era5_temp_mean",
            "chirps_precip_daily",
            "modis_ndvi_current",
            "map_pr_baseline",
            "worldpop_density",
        ]

        for feature in expected_features:
            assert feature in schema


# Integration test
@pytest.mark.asyncio
async def test_full_harmonization_pipeline_integration():
    """Integration test for the complete harmonization pipeline."""

    # Create temporary directory for cache
    temp_dir = tempfile.mkdtemp()

    # Mock settings
    settings = Mock(spec=Settings)
    settings.cache_directory = temp_dir

    # Create sample data for each source
    def create_mock_client_result(data_shape):
        result = Mock()
        result.success = True
        result.data = np.random.rand(*data_shape).astype(np.float32)
        result.file_paths = []
        result.bounds = (-10, -5, 10, 5)
        result.transform = None
        return result

    # Mock all data clients
    with patch.multiple(
        "malaria_predictor.services.unified_data_harmonizer",
        ERA5Client=Mock,
        CHIRPSClient=Mock,
        MODISClient=Mock,
        MAPClient=Mock,
        WorldPopClient=Mock,
    ) as _mocks:
        harmonizer = UnifiedDataHarmonizer(settings)

        # Mock client return values
        harmonizer.era5_client.download_temperature_data.return_value = (
            create_mock_client_result((30, 50, 50))
        )
        harmonizer.chirps_client.download_rainfall_data.return_value = (
            create_mock_client_result((30, 50, 50))
        )
        harmonizer.modis_client.download_vegetation_indices.return_value = (
            create_mock_client_result((2, 50, 50))
        )
        harmonizer.map_client.download_parasite_rate_surface.return_value = (
            create_mock_client_result((50, 50))
        )
        harmonizer.worldpop_client.download_population_data.return_value = (
            create_mock_client_result((50, 50))
        )

        # Test the full pipeline
        region_bounds = (-10, -5, 10, 5)
        target_date = date(2023, 6, 15)

        result = await harmonizer.get_harmonized_features(
            region_bounds=region_bounds, target_date=target_date, lookback_days=30
        )

        # Verify result structure
        assert isinstance(result, HarmonizedDataResult)
        assert isinstance(result.data, dict)
        assert len(result.data) > 0
        assert isinstance(result.feature_names, list)
        assert len(result.feature_names) > 0
        assert result.spatial_bounds == region_bounds

        # Verify features are properly shaped
        for _feature_name, feature_data in result.data.items():
            assert isinstance(feature_data, np.ndarray)
            assert feature_data.dtype == np.float32
            assert len(feature_data.shape) == 2  # Should be 2D spatial data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
