"""
Unified Data Harmonization Service for Multi-Source Environmental Data Integration.

This module provides the main service that orchestrates harmonization across all
data sources (ERA5, CHIRPS, MAP, WorldPop, MODIS) and integrates with existing
data clients to provide ML-ready feature vectors.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import h5py
import xarray as xr

from ..config import Settings
from .chirps_client import CHIRPSClient, CHIRPSDownloadResult
from .data_harmonizer import HarmonizedDataResult, SpatialHarmonizer, TemporalHarmonizer
from .era5_client import ERA5Client, ERA5DownloadResult
from .feature_engineering import FeatureEngineer, QualityManager
from .map_client import MAPClient, MAPDownloadResult
from .modis_client import MODISClient, MODISDownloadResult
from .worldpop_client import WorldPopClient, WorldPopDownloadResult

# Configure logging
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of harmonized data using HDF5 for efficient storage.
    Provides smart caching with validation and automated cache invalidation
    based on data freshness and processing parameters.
    """

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_store: dict[str, Any] = {}

    def get_cached_harmonized_data(
        self,
        region_bounds: tuple[float, float, float, float],
        date_range: tuple[date, date],
        resolution: str,
    ) -> HarmonizedDataResult | None:
        """Retrieve cached harmonized data if available and valid."""
        cache_key = self._generate_cache_key(region_bounds, date_range, resolution)
        cache_path = self.cache_dir / f"{cache_key}.h5"

        if cache_path.exists():
            # Check if cache is still valid
            if self._is_cache_valid(cache_path, date_range):
                logger.info(f"Loading from cache: {cache_key}")
                return self._load_from_cache(cache_path)

        return None

    def cache_harmonized_data(
        self,
        data: HarmonizedDataResult,
        region_bounds: tuple[float, float, float, float],
        date_range: tuple[date, date],
        resolution: str,
    ) -> None:
        """Cache harmonized data for future use."""
        cache_key = self._generate_cache_key(region_bounds, date_range, resolution)
        cache_path = self.cache_dir / f"{cache_key}.h5"

        try:
            # Save to HDF5 for efficient storage
            with h5py.File(cache_path, "w") as f:
                for feature_name, feature_data in data.data.items():
                    f.create_dataset(f"features/{feature_name}", data=feature_data)

                # Store metadata
                f.attrs["bounds"] = region_bounds
                f.attrs["date_range_start"] = date_range[0].isoformat()
                f.attrs["date_range_end"] = date_range[1].isoformat()
                f.attrs["resolution"] = resolution
                f.attrs["created"] = datetime.now().isoformat()
                f.attrs["feature_names"] = [
                    name.encode() for name in data.feature_names
                ]

                # Store quality metrics
                for metric_name, metric_value in data.quality_metrics.items():
                    f.attrs[f"quality_{metric_name}"] = metric_value

            logger.info(f"Cached harmonized data: {cache_key}")

        except Exception as e:
            logger.error(f"Failed to cache harmonized data: {e}")

    def _generate_cache_key(
        self,
        region_bounds: tuple[float, float, float, float],
        date_range: tuple[date, date],
        resolution: str,
    ) -> str:
        """Generate unique cache key for data parameters."""
        bounds_str = f"{region_bounds[0]:.3f}_{region_bounds[1]:.3f}_{region_bounds[2]:.3f}_{region_bounds[3]:.3f}"
        date_str = f"{date_range[0].isoformat()}_{date_range[1].isoformat()}"
        return f"harmonized_{bounds_str}_{date_str}_{resolution}"

    def _is_cache_valid(self, cache_path: Path, date_range: tuple[date, date]) -> bool:
        """Check if cached data is still valid."""
        try:
            with h5py.File(cache_path, "r") as f:
                # Check if cache is recent (within 24 hours for current data)
                created_str = f.attrs.get("created", "")
                if created_str:
                    created_time = datetime.fromisoformat(created_str)
                    age_hours = (datetime.now() - created_time).total_seconds() / 3600

                    # For recent data (within last week), cache valid for 6 hours
                    # For older data, cache valid for 24 hours
                    days_old = (datetime.now().date() - date_range[1]).days
                    max_age = 6 if days_old <= 7 else 24

                    return age_hours < max_age

                return False

        except Exception as e:
            logger.warning(f"Failed to validate cache {cache_path}: {e}")
            return False

    def _load_from_cache(self, cache_path: Path) -> HarmonizedDataResult:
        """Load harmonized data from HDF5 cache."""
        try:
            with h5py.File(cache_path, "r") as f:
                # Load feature data
                data = {}
                for feature_name in f["features"].keys():
                    data[feature_name] = f[f"features/{feature_name}"][:]

                # Load metadata
                feature_names_raw = f.attrs["feature_names"]
                if isinstance(feature_names_raw[0], bytes):
                    feature_names = [name.decode() for name in feature_names_raw]
                else:
                    feature_names = list(feature_names_raw)
                bounds = tuple(f.attrs["bounds"])

                date_start = datetime.fromisoformat(f.attrs["date_range_start"]).date()
                date_end = datetime.fromisoformat(f.attrs["date_range_end"]).date()
                temporal_range = (
                    datetime.combine(date_start, datetime.min.time()),
                    datetime.combine(date_end, datetime.min.time()),
                )

                resolution = f.attrs["resolution"]
                processing_timestamp = datetime.fromisoformat(f.attrs["created"])

                # Load quality metrics
                quality_metrics = {}
                for attr_name in f.attrs.keys():
                    if attr_name.startswith("quality_"):
                        metric_name = attr_name[8:]  # Remove 'quality_' prefix
                        quality_metrics[metric_name] = f.attrs[attr_name]

                return HarmonizedDataResult(
                    data=data,
                    metadata={"cache_loaded": True},
                    quality_metrics=quality_metrics,
                    feature_names=feature_names,
                    spatial_bounds=bounds,
                    temporal_range=temporal_range,
                    target_resolution=resolution,
                    processing_timestamp=processing_timestamp,
                )

        except Exception as e:
            logger.error(f"Failed to load from cache {cache_path}: {e}")
            raise


class UnifiedDataHarmonizer:
    """
    Main service that orchestrates harmonization across all data sources.
    Integrates with existing data clients and provides a unified interface
    for obtaining ML-ready harmonized environmental features.
    """

    def __init__(self, settings: Settings) -> None:
        # Initialize existing data clients
        self.era5_client = ERA5Client(settings)
        self.chirps_client = CHIRPSClient(settings)
        self.modis_client = MODISClient(settings)
        self.map_client = MAPClient(settings)
        self.worldpop_client = WorldPopClient(settings)

        # Initialize harmonization components
        self.temporal_harmonizer = TemporalHarmonizer()
        self.spatial_harmonizer = SpatialHarmonizer()
        self.feature_engineer = FeatureEngineer()
        self.quality_manager = QualityManager()

        # Initialize caching
        cache_dir = Path(settings.cache_directory) / "harmonized_data"
        self.cache_manager = CacheManager(cache_dir)

        logger.info("UnifiedDataHarmonizer initialized with all data sources")

    async def get_harmonized_features(
        self,
        region_bounds: tuple[float, float, float, float],
        target_date: date,
        lookback_days: int = 90,
        target_resolution: str = "1km",
    ) -> HarmonizedDataResult:
        """
        Main entry point for getting harmonized ML features.
        Args:
            region_bounds: (west, south, east, north) bounding box
            target_date: Target date for prediction
            lookback_days: Number of days to look back for temporal features
            target_resolution: Target spatial resolution ("1km", "5km", "10km")
        Returns:
            HarmonizedDataResult with ML-ready features
        """
        # Define date range
        end_date = target_date
        start_date = target_date - timedelta(days=lookback_days)

        logger.info(
            f"Harmonizing data for {region_bounds} from {start_date} to {end_date}"
        )

        # Check cache first
        cached_data = self.cache_manager.get_cached_harmonized_data(
            region_bounds, (start_date, end_date), target_resolution
        )

        if cached_data:
            logger.info("Using cached harmonized data")
            return cached_data

        # Download/load raw data from all sources
        raw_data = await self._orchestrate_data_download(
            region_bounds, start_date, end_date
        )

        # Apply harmonization pipeline
        harmonized_result = self._apply_harmonization_pipeline(
            raw_data, target_date, region_bounds, target_resolution
        )

        # Cache results
        self.cache_manager.cache_harmonized_data(
            harmonized_result, region_bounds, (start_date, end_date), target_resolution
        )

        return harmonized_result

    async def _orchestrate_data_download(
        self,
        bounds: tuple[float, float, float, float],
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Orchestrate parallel data download from all sources."""

        download_tasks = {
            "era5": self._download_era5_data(start_date, end_date, bounds),
            "chirps": self._download_chirps_data(start_date, end_date, bounds),
            "modis": self._download_modis_data(start_date, end_date, bounds),
            "map": self._download_map_data(end_date, bounds),
            "worldpop": self._download_worldpop_data(end_date, bounds),
        }

        # Execute downloads concurrently
        raw_data = {}
        results = await asyncio.gather(*download_tasks.values(), return_exceptions=True)

        for (source_name, _), result in zip(
            download_tasks.items(), results, strict=False
        ):
            if isinstance(result, Exception):
                logger.error(f"Failed to download {source_name}: {result}")
            elif result and getattr(result, "success", False):
                raw_data[source_name] = result
            else:
                logger.warning(f"No data available for {source_name}")

        logger.info(f"Successfully downloaded data from {len(raw_data)} sources")
        return raw_data

    async def _download_era5_data(
        self,
        start_date: date,
        end_date: date,
        bounds: tuple[float, float, float, float],
    ) -> ERA5DownloadResult | None:
        """Download ERA5 temperature data."""
        try:
            result = await asyncio.to_thread(
                self.era5_client.download_temperature_data, start_date, end_date, bounds
            )
            return result
        except Exception as e:
            logger.error(f"ERA5 download failed: {e}")
            return None

    async def _download_chirps_data(
        self,
        start_date: date,
        end_date: date,
        bounds: tuple[float, float, float, float],
    ) -> CHIRPSDownloadResult | None:
        """Download CHIRPS rainfall data."""
        try:
            result = await asyncio.to_thread(
                self.chirps_client.download_rainfall_data,
                start_date,
                end_date,
                "daily",
                bounds,
            )
            return result
        except Exception as e:
            logger.error(f"CHIRPS download failed: {e}")
            return None

    async def _download_modis_data(
        self,
        start_date: date,
        end_date: date,
        bounds: tuple[float, float, float, float],
    ) -> MODISDownloadResult | None:
        """Download MODIS vegetation data."""
        try:
            result = await asyncio.to_thread(
                self.modis_client.download_vegetation_indices,
                start_date,
                end_date,
                "MOD13Q1",
                bounds,
            )
            return result
        except Exception as e:
            logger.error(f"MODIS download failed: {e}")
            return None

    async def _download_map_data(
        self, target_date: date, bounds: tuple[float, float, float, float]
    ) -> MAPDownloadResult | None:
        """Download MAP malaria risk data."""
        try:
            result = await asyncio.to_thread(
                self.map_client.download_parasite_rate_surface,
                target_date.year,
                "Pf",
                True,
                "1km",
                bounds,
            )
            return result
        except Exception as e:
            logger.error(f"MAP download failed: {e}")
            return None

    async def _download_worldpop_data(
        self, target_date: date, bounds: tuple[float, float, float, float]
    ) -> WorldPopDownloadResult | None:
        """Download WorldPop population data."""
        try:
            # Convert bounds to country list (simplified)
            countries = self._bounds_to_countries(bounds)
            result = await asyncio.to_thread(
                self.worldpop_client.download_population_data,
                countries,
                target_date.year,
            )
            return result
        except Exception as e:
            logger.error(f"WorldPop download failed: {e}")
            return None

    def _bounds_to_countries(
        self, bounds: tuple[float, float, float, float]
    ) -> list[str]:
        """Convert geographic bounds to country list (simplified implementation)."""
        # This is a simplified implementation
        # In practice, would use a spatial lookup service
        west, south, east, north = bounds

        # Basic Africa country mapping based on bounds
        if -20 <= west <= 55 and -35 <= south <= 40:
            return ["NGA", "KEN", "GHA", "UGA"]  # Major malaria-endemic countries
        else:
            return ["NGA"]  # Default fallback

    def _apply_harmonization_pipeline(
        self,
        raw_data: dict[str, Any],
        target_date: date,
        region_bounds: tuple[float, float, float, float],
        target_resolution: str,
    ) -> HarmonizedDataResult:
        """Apply complete harmonization pipeline to raw data."""

        logger.info("Starting harmonization pipeline")

        # Step 1: Convert raw data to xarray datasets
        xr_datasets = self._convert_to_xarray(raw_data)

        # Step 2: Temporal harmonization
        logger.info("Performing temporal harmonization")
        temporally_harmonized = self.temporal_harmonizer.harmonize_temporal(xr_datasets)

        # Step 3: Convert to spatial data format
        spatial_data = self._convert_for_spatial_harmonization(
            temporally_harmonized, raw_data
        )

        # Step 4: Spatial harmonization
        logger.info("Performing spatial harmonization")
        spatially_harmonized = self.spatial_harmonizer.harmonize_spatial_data(
            spatial_data
        )

        # Step 5: Feature engineering
        logger.info("Generating ML features")
        target_datetime = datetime.combine(target_date, datetime.min.time())
        features = self.feature_engineer.generate_ml_features(
            spatially_harmonized, target_datetime
        )

        # Step 6: Quality assessment
        logger.info("Assessing data quality")
        quality_assessment = self.quality_manager.assess_harmonized_quality(
            spatially_harmonized
        )

        # Create result
        result = HarmonizedDataResult(
            data=features,
            metadata={
                "raw_sources": list(raw_data.keys()),
                "harmonization_steps": [
                    "temporal",
                    "spatial",
                    "feature_engineering",
                    "quality_assessment",
                ],
                "target_date": target_date.isoformat(),
                "lookback_days": (
                    target_date
                    - datetime.combine(target_date, datetime.min.time()).date()
                ).days,
            },
            quality_metrics=quality_assessment,
            feature_names=list(features.keys()),
            spatial_bounds=region_bounds,
            temporal_range=(
                datetime.combine(target_date, datetime.min.time()),
                datetime.combine(target_date, datetime.min.time()),
            ),
            target_resolution=target_resolution,
            processing_timestamp=datetime.now(),
        )

        logger.info(
            f"Harmonization pipeline completed: {len(features)} features generated"
        )
        return result

    def _convert_to_xarray(self, raw_data: dict[str, Any]) -> dict[str, xr.Dataset]:
        """Convert raw data to xarray datasets for temporal harmonization."""
        xr_datasets = {}

        for source_name, source_result in raw_data.items():
            try:
                if hasattr(source_result, "file_paths") and source_result.file_paths:
                    # Load data from files
                    file_path = source_result.file_paths[0]  # Use first file

                    if source_name in ["era5", "chirps", "modis"]:
                        # Time series data
                        xr_datasets[source_name] = xr.open_dataset(file_path)
                    else:
                        # Static data (MAP, WorldPop)
                        with xr.open_dataset(file_path) as ds:
                            # Add dummy time dimension for consistency
                            ds = ds.expand_dims(time=[datetime.now()])
                            xr_datasets[source_name] = ds

                elif hasattr(source_result, "data") and source_result.data is not None:
                    # Create xarray from numpy array
                    data_array = source_result.data

                    # Create simple xarray dataset
                    if data_array.ndim == 2:
                        # 2D spatial data
                        ds = xr.Dataset(
                            {f"{source_name}_data": (["y", "x"], data_array)}
                        )
                        ds = ds.expand_dims(time=[datetime.now()])
                    elif data_array.ndim == 3:
                        # 3D spatiotemporal data
                        time_coords = [
                            datetime.now() - timedelta(days=i)
                            for i in range(data_array.shape[0])
                        ]
                        ds = xr.Dataset(
                            {
                                f"{source_name}_data": (["time", "y", "x"], data_array),
                                "time": time_coords,
                            }
                        )
                    else:
                        logger.warning(
                            f"Unsupported data dimensions for {source_name}: {data_array.ndim}"
                        )
                        continue

                    xr_datasets[source_name] = ds

            except Exception as e:
                logger.error(f"Failed to convert {source_name} to xarray: {e}")

        return xr_datasets

    def _convert_for_spatial_harmonization(
        self, temporal_data: dict[str, xr.Dataset], raw_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Convert temporally harmonized data for spatial harmonization."""
        spatial_data = {}

        for source_name, dataset in temporal_data.items():
            try:
                # Extract the most recent time slice for spatial harmonization
                if "time" in dataset.dims:
                    latest_data = dataset.isel(time=-1)
                else:
                    latest_data = dataset

                # Convert to numpy array
                data_vars = list(latest_data.data_vars.keys())
                if data_vars:
                    main_var = data_vars[0]
                    data_array = latest_data[main_var].values

                    # Get spatial metadata from raw data if available
                    source_result = raw_data.get(source_name)
                    bounds = getattr(source_result, "bounds", None)
                    transform = getattr(source_result, "transform", None)

                    spatial_data[source_name] = {
                        "array": data_array,
                        "bounds": bounds,
                        "transform": transform,
                        "crs": "EPSG:4326",  # Default to WGS84
                    }

            except Exception as e:
                logger.error(
                    f"Failed to convert {source_name} for spatial harmonization: {e}"
                )

        return spatial_data

    def get_feature_schema(self) -> dict[str, str]:
        """Get the schema of available features."""
        return self.feature_engineer.schema

    def validate_region_bounds(self, bounds: tuple[float, float, float, float]) -> bool:
        """Validate that region bounds are reasonable."""
        west, south, east, north = bounds

        # Basic validation
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            return False
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            return False
        if west >= east or south >= north:
            return False

        # Check reasonable size (not too large)
        width = east - west
        height = north - south
        max_size = 20.0  # degrees

        return width <= max_size and height <= max_size
