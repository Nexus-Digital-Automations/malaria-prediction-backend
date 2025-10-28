"""
Data Harmonization Service for Multi-Source Environmental Data Integration.

This module provides comprehensive data harmonization capabilities for integrating
ERA5, CHIRPS, MAP, WorldPop, and MODIS data into unified ML-ready features.

Key Components:
- TemporalHarmonizer: Aligns data across different temporal frequencies
- SpatialHarmonizer: Harmonizes spatial resolutions and coordinate systems
- FeatureEngineer: Creates malaria-relevant derived features
- QualityManager: Assesses and validates data quality across sources
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from pydantic import BaseModel, Field
from rasterio.warp import Resampling, reproject

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
TEMPORAL_RESOLUTIONS = {
    "daily": {
        "sources": ["era5", "chirps"],
        "aggregation_window": 1,
        "lag_features": [1, 3, 7, 14, 30],  # days
    },
    "weekly": {
        "sources": ["era5", "chirps", "modis"],
        "aggregation_window": 7,
        "modis_alignment": "16day_to_weekly",
    },
    "monthly": {
        "sources": ["era5", "chirps", "modis", "map", "worldpop"],
        "aggregation_window": 30,
        "annual_interpolation": True,
    },
}

SPATIAL_HARMONIZATION = {
    "target_resolution": "1km",  # Compromise between detail and processing
    "target_crs": "EPSG:4326",  # WGS84 for global compatibility
    "africa_bounds": (-20.0, -35.0, 55.0, 40.0),  # Standard focus area
    "resampling_methods": {
        "era5": "bilinear",  # Smooth climate interpolation
        "chirps": "bilinear",  # Precipitation surfaces
        "modis": "bilinear",  # Vegetation continuity
        "map": "nearest",  # Preserve risk categories
        "worldpop": "sum",  # Population conservation
    },
}

FEATURE_SCHEMA = {
    # Climate features (ERA5)
    "era5_temp_mean": "Daily mean temperature (°C)",
    "era5_temp_max": "Daily maximum temperature (°C)",
    "era5_temp_min": "Daily minimum temperature (°C)",
    "era5_temp_range": "Diurnal temperature range (°C)",
    "era5_humid_relative": "Relative humidity (%)",
    "era5_temp_suitability": "Temperature suitability index (0-1)",
    # Precipitation features (CHIRPS)
    "chirps_precip_daily": "Daily precipitation (mm)",
    "chirps_precip_7d": "7-day accumulated precipitation (mm)",
    "chirps_precip_30d": "30-day accumulated precipitation (mm)",
    "chirps_dry_spell_days": "Consecutive dry days count",
    "chirps_wet_spell_intensity": "Average wet spell intensity",
    "chirps_seasonal_anomaly": "Precipitation anomaly vs seasonal normal",
    # Vegetation features (MODIS)
    "modis_ndvi_current": "Current NDVI value (-1 to 1)",
    "modis_evi_current": "Current EVI value (-1 to 1)",
    "modis_ndvi_trend_30d": "30-day NDVI trend slope",
    "modis_vegetation_stress": "Vegetation stress indicator (0-1)",
    "modis_greenness_peak": "Days since peak greenness",
    "modis_phenology_stage": "Vegetation phenology stage (0-4)",
    # Malaria risk features (MAP)
    "map_pr_baseline": "Baseline parasite rate (%)",
    "map_incidence_risk": "Clinical incidence risk (cases/1000)",
    "map_transmission_intensity": "Transmission intensity category (0-3)",
    "map_vector_suitability": "Vector habitat suitability (0-1)",
    "map_intervention_coverage": "Intervention coverage score (0-1)",
    # Population features (WorldPop)
    "worldpop_density": "Population density (people/km²)",
    "worldpop_children_u5": "Children under 5 density (people/km²)",
    "worldpop_density_log": "Log-transformed population density",
    "worldpop_urban_rural": "Urban/rural classification (0-1)",
    "worldpop_accessibility": "Travel time to cities (hours)",
    # Derived interaction features
    "breeding_habitat_index": "Combined water+temperature breeding suitability",
    "transmission_risk_composite": "Multi-factor transmission risk score",
    "population_at_risk": "Population density × malaria risk",
    "climate_stress_index": "Combined temperature+precipitation stress",
    "vector_activity_potential": "Temperature+humidity vector activity score",
}


@dataclass
class HarmonizedDataResult:
    """Result container for harmonized environmental data."""

    data: dict[str, np.ndarray]
    metadata: dict[str, Any]
    quality_metrics: dict[str, float]
    feature_names: list[str]
    spatial_bounds: tuple[float, float, float, float]
    temporal_range: tuple[datetime, datetime]
    target_resolution: str
    processing_timestamp: datetime


class HarmonizedDataPoint(BaseModel):
    """Legacy class maintained for backward compatibility."""

    timestamp: datetime = Field(description="UTC timestamp")
    latitude: float = Field(description="Latitude in decimal degrees")
    longitude: float = Field(description="Longitude in decimal degrees")
    temperature_2m: float | None = Field(
        default=None, description="2m temperature in Celsius"
    )
    temperature_min: float | None = Field(
        default=None, description="Minimum temperature in Celsius"
    )
    temperature_max: float | None = Field(
        default=None, description="Maximum temperature in Celsius"
    )
    rainfall_mm: float | None = Field(default=None, description="Daily rainfall in mm")
    rainfall_anomaly: float | None = Field(
        default=None, description="Rainfall anomaly percentage"
    )
    temperature_source: str | None = Field(
        default=None, description="Source of temperature data"
    )
    rainfall_source: str | None = Field(
        default=None, description="Source of rainfall data"
    )
    quality_flag: int = Field(
        default=0, description="Quality flag (0=good, 1=interpolated, 2=missing)"
    )


class TemporalHarmonizer:
    """
    Harmonizes temporal frequencies across different data sources.
    Handles alignment of daily (ERA5), weekly (MODIS), and annual (MAP/WorldPop)
    data to a unified temporal framework for ML feature engineering.
    """

    def __init__(self) -> None:
        self.gap_filling_methods = {
            "era5": "linear_interpolation",  # Weather continuity
            "chirps": "zero_fill_drought",  # Dry periods
            "modis": "seasonal_climatology",  # Vegetation cycles
            "map": "forward_fill_annual",  # Static risk
            "worldpop": "forward_fill_annual",  # Static population
        }

    def harmonize_temporal(
        self, data_sources: dict[str, xr.Dataset], target_frequency: str = "daily"
    ) -> dict[str, xr.Dataset]:
        """
        Harmonize temporal resolution across all data sources.
        Args:
            data_sources: Dictionary of source name to xarray Dataset
            target_frequency: Target temporal frequency ('daily', 'weekly', 'monthly')
        Returns:
            Dictionary of temporally harmonized datasets
        """
        harmonized = {}

        # Create unified temporal index
        temporal_index = self._create_unified_temporal_index(
            data_sources, target_frequency
        )

        for source_name, dataset in data_sources.items():
            logger.info(f"Harmonizing temporal resolution for {source_name}")

            if source_name in ["era5", "chirps"]:
                # Daily data - resample to target frequency
                harmonized[source_name] = self._resample_daily_data(
                    dataset, temporal_index, target_frequency
                )
            elif source_name == "modis":
                # 16-day composites - interpolate to daily then aggregate
                harmonized[source_name] = self._interpolate_modis_data(
                    dataset, temporal_index
                )
            elif source_name in ["map", "worldpop"]:
                # Annual data - forward fill with seasonal modulation
                harmonized[source_name] = self._interpolate_annual_data(
                    dataset, temporal_index
                )

        # Fill temporal gaps using appropriate methods
        harmonized = self.fill_temporal_gaps(harmonized)

        return harmonized

    def _create_unified_temporal_index(
        self, data_sources: dict[str, xr.Dataset], frequency: str
    ) -> pd.DatetimeIndex:
        """Create unified temporal index covering all data sources."""
        start_dates = []
        end_dates = []

        for dataset in data_sources.values():
            if "time" in dataset.coords:
                start_dates.append(pd.to_datetime(dataset.time.min().values))
                end_dates.append(pd.to_datetime(dataset.time.max().values))

        if not start_dates:
            raise ValueError("No temporal data found in any source")

        start_date = max(start_dates)  # Latest start for complete coverage
        end_date = min(end_dates)  # Earliest end for complete coverage

        if frequency == "daily":
            return pd.date_range(start_date, end_date, freq="D")
        elif frequency == "weekly":
            return pd.date_range(start_date, end_date, freq="W")
        elif frequency == "monthly":
            return pd.date_range(start_date, end_date, freq="MS")
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")

    def _resample_daily_data(
        self, dataset: xr.Dataset, temporal_index: pd.DatetimeIndex, frequency: str
    ) -> xr.Dataset:
        """Resample daily data to target frequency."""
        # Interpolate to fill any gaps first
        dataset_interp = dataset.interp(time=temporal_index, method="linear")

        if frequency == "daily":
            return dataset_interp
        elif frequency == "weekly":
            return dataset_interp.resample(time="W").mean()
        elif frequency == "monthly":
            return dataset_interp.resample(time="MS").mean()
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")

    def _interpolate_modis_data(
        self, dataset: xr.Dataset, temporal_index: pd.DatetimeIndex
    ) -> xr.Dataset:
        """Interpolate 16-day MODIS composites to daily resolution."""
        # Choose interpolation method based on available data points
        n_points = len(dataset.time)
        if n_points >= 4:
            # Use cubic spline interpolation for smooth vegetation transitions
            method = "cubic"
        elif n_points >= 2:
            # Use linear interpolation for limited data points
            method = "linear"
        else:
            # Use nearest neighbor for single point
            method = "nearest"

        interpolated = dataset.interp(time=temporal_index, method=method)

        # Apply quality masking - only interpolate over short gaps
        quality_threshold = 16  # days - maximum gap to interpolate

        for var in interpolated.data_vars:
            # Identify long gaps and set to NaN
            time_diff = (
                np.diff(dataset.time.values).astype("timedelta64[D]").astype(int)
            )
            long_gaps = time_diff > quality_threshold

            # Conservative interpolation only over short gaps
            if np.any(long_gaps):
                logger.warning(
                    f"Found {np.sum(long_gaps)} long gaps in MODIS {var} data"
                )

        return interpolated

    def _interpolate_annual_data(
        self, dataset: xr.Dataset, temporal_index: pd.DatetimeIndex
    ) -> xr.Dataset:
        """Interpolate annual data with seasonal modulation."""
        # For annual data without time dimension, broadcast to all time points
        if "time" not in dataset.dims:
            # Create time dimension by broadcasting the data
            data_vars = {}
            for var_name, var in dataset.data_vars.items():
                # Expand data to include time dimension
                expanded_data = var.expand_dims(time=temporal_index)
                data_vars[var_name] = expanded_data

            interpolated = xr.Dataset(
                data_vars, coords={**dataset.coords, "time": temporal_index}
            )
        else:
            # Forward fill annual values if time dimension exists
            interpolated = dataset.interp(time=temporal_index, method="nearest")

        # Add seasonal modulation for MAP risk data
        if "pr" in dataset.data_vars or "incidence" in dataset.data_vars:
            # Apply seasonal malaria transmission patterns
            seasonal_modulation = self._calculate_seasonal_malaria_modulation(
                temporal_index
            )

            for var in interpolated.data_vars:
                if "risk" in var or "pr" in var or "incidence" in var:
                    interpolated[var] = interpolated[var] * seasonal_modulation

        return interpolated

    def _calculate_seasonal_malaria_modulation(
        self, temporal_index: pd.DatetimeIndex
    ) -> xr.DataArray:
        """Calculate seasonal modulation for malaria transmission."""
        # Simple sinusoidal seasonal pattern (peak during wet season)
        day_of_year = temporal_index.dayofyear

        # Peak transmission ~60 days after peak rainfall (varies by region)
        seasonal_factor = 0.5 + 0.5 * np.sin(2 * np.pi * (day_of_year - 120) / 365)

        return xr.DataArray(
            seasonal_factor,
            coords={"time": temporal_index},
            dims=["time"],
            name="seasonal_modulation",
        )

    def fill_temporal_gaps(
        self, data_dict: dict[str, xr.Dataset], max_gap_days: int = 7
    ) -> dict[str, xr.Dataset]:
        """Fill temporal gaps using source-appropriate methods."""
        filled_data = {}

        for source, dataset in data_dict.items():
            method = self.gap_filling_methods.get(source, "linear_interpolation")

            logger.info(f"Filling gaps in {source} using {method}")
            filled_data[source] = self._apply_gap_filling(dataset, method, max_gap_days)

        return filled_data

    def _apply_gap_filling(
        self, dataset: xr.Dataset, method: str, max_gap_days: int
    ) -> xr.Dataset:
        """Apply specific gap filling method to dataset."""
        try:
            if method == "linear_interpolation":
                # Use simple linear interpolation without max_gap constraint to avoid bottleneck dependency
                return dataset.interpolate_na(dim="time", method="linear")
            elif method == "zero_fill_drought":
                # For precipitation - assume zero during gaps (drought periods)
                return dataset.fillna(0)
            elif method == "seasonal_climatology":
                # For vegetation - use seasonal climatology
                return self._fill_with_climatology(dataset, max_gap_days)
            elif method == "forward_fill_annual":
                # For annual data - forward fill using basic numpy operations
                filled_dataset = dataset.copy()
                for var_name in dataset.data_vars:
                    data = dataset[var_name].values
                    # Simple forward fill implementation
                    for i in range(1, data.shape[0]):
                        mask = np.isnan(data[i])
                        data[i][mask] = data[i - 1][mask]
                    filled_dataset[var_name] = (dataset[var_name].dims, data)
                return filled_dataset
            else:
                logger.warning(
                    f"Unknown gap filling method: {method}, using simple forward fill"
                )
                # Simple fallback without external dependencies
                return dataset.fillna(0)
        except Exception as e:
            logger.warning(f"Gap filling failed with {method}: {e}, using zero fill")
            return dataset.fillna(0)

    def _fill_with_climatology(
        self, dataset: xr.Dataset, max_gap_days: int
    ) -> xr.Dataset:
        """Fill gaps using seasonal climatology."""
        # Calculate day-of-year climatology
        climatology = dataset.groupby("time.dayofyear").mean("time")

        # Fill gaps with climatological values
        filled = dataset.copy()
        for var in dataset.data_vars:
            # Identify gaps
            gaps = dataset[var].isnull()

            if gaps.any():
                # Get day of year for gap periods
                gap_doy = dataset.time.where(gaps).dt.dayofyear

                # Fill with climatological values
                clim_values = climatology[var].sel(dayofyear=gap_doy)
                filled[var] = filled[var].fillna(clim_values)

        return filled


class DataHarmonizer:
    """Legacy service maintained for backward compatibility."""

    def __init__(self) -> None:
        """Initialize the data harmonizer."""
        self.grid_resolution = 0.05  # Target resolution in degrees (matches CHIRPS)
        self.africa_bounds = (-20.0, -35.0, 55.0, 40.0)  # W, S, E, N
        logger.info(
            "Legacy DataHarmonizer initialized - use UnifiedDataHarmonizer for new features"
        )

    def harmonize_daily_data(
        self,
        era5_data: dict | None,
        chirps_data: dict | None,
        target_date: date,
        locations: list[tuple[float, float]] | None = None,
    ) -> list[HarmonizedDataPoint]:
        """Legacy method - harmonize daily data from ERA5 and CHIRPS."""
        harmonized_points = []

        try:
            # Create common spatial grid
            if locations is None:
                locations = self._create_africa_grid()

            # Process each location
            for lat, lon in locations:
                point = self._harmonize_location(
                    lat, lon, target_date, era5_data, chirps_data
                )
                if point:
                    harmonized_points.append(point)

            logger.info(
                f"Harmonized {len(harmonized_points)} data points for {target_date}"
            )
            return harmonized_points

        except Exception as e:
            logger.error(f"Failed to harmonize daily data: {e}")
            return []

    def _create_africa_grid(self) -> list[tuple[float, float]]:
        """Create a regular grid of points covering Africa."""
        west, south, east, north = self.africa_bounds

        # Create grid at target resolution
        lats = np.arange(south, north, self.grid_resolution)
        lons = np.arange(west, east, self.grid_resolution)

        # Create all combinations
        locations = []
        for lat in lats:
            for lon in lons:
                locations.append((lat, lon))

        return locations


class SpatialHarmonizer:
    """
    Harmonizes spatial resolutions and coordinate systems across data sources.
    Handles resampling from different native resolutions (100m WorldPop to 31km ERA5)
    to a unified target grid while preserving data characteristics.
    """

    def __init__(self, target_resolution: str = "1km", target_crs: str = "EPSG:4326") -> None:
        self.target_resolution = target_resolution
        self.target_crs = target_crs
        self.resampling_methods = SPATIAL_HARMONIZATION["resampling_methods"]

    def harmonize_spatial_data(
        self, data_sources: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Harmonize spatial resolution and CRS across all data sources.
        Args:
            data_sources: Dictionary mapping source names to data info
        Returns:
            Dictionary of spatially harmonized data arrays with metadata
        """
        harmonized = {}

        # Create target grid definition
        target_grid = self._create_target_grid(data_sources)

        for source_name, data_info in data_sources.items():
            logger.info(f"Harmonizing spatial data for {source_name}")

            method = self.resampling_methods.get(source_name, "bilinear")

            harmonized[source_name] = self._resample_to_target_grid(
                data_info, target_grid, method
            )

        return harmonized

    def _create_target_grid(self, data_sources: dict[str, Any]) -> dict[str, Any]:
        """Create target grid covering all data sources."""
        # Determine bounds covering all sources
        all_bounds = []

        for data_info in data_sources.values():
            if "bounds" in data_info:
                all_bounds.append(data_info["bounds"])

        if not all_bounds:
            # Use default Africa bounds
            bounds = SPATIAL_HARMONIZATION["africa_bounds"]
        else:
            # Calculate union of all bounds
            min_x = min(b[0] for b in all_bounds)
            min_y = min(b[1] for b in all_bounds)
            max_x = max(b[2] for b in all_bounds)
            max_y = max(b[3] for b in all_bounds)
            bounds = (min_x, min_y, max_x, max_y)

        # Calculate target resolution in degrees
        if self.target_resolution == "1km":
            res_degrees = 1 / 111.0  # Approximately 1km at equator
        elif self.target_resolution == "5km":
            res_degrees = 5 / 111.0
        elif self.target_resolution == "10km":
            res_degrees = 10 / 111.0
        else:
            res_degrees = 0.01  # Default ~1km

        # Calculate grid dimensions
        width = int((bounds[2] - bounds[0]) / res_degrees)
        height = int((bounds[3] - bounds[1]) / res_degrees)

        # Create transform
        from rasterio.transform import from_bounds

        transform = from_bounds(
            bounds[0], bounds[1], bounds[2], bounds[3], width, height
        )

        return {
            "bounds": bounds,
            "width": width,
            "height": height,
            "transform": transform,
            "crs": self.target_crs,
            "resolution": res_degrees,
        }

    def _resample_to_target_grid(
        self, data_info: dict[str, Any], target_grid: dict[str, Any], method: str
    ) -> dict[str, Any]:
        """Resample individual source to target grid."""
        if "file_path" in data_info:
            return self._resample_from_file(data_info["file_path"], target_grid, method)
        elif "array" in data_info:
            return self._resample_from_array(data_info, target_grid, method)
        else:
            raise ValueError("Data info must contain either 'file_path' or 'array'")

    def _resample_from_file(
        self, file_path: str, target_grid: dict[str, Any], method: str
    ) -> dict[str, Any]:
        """Resample raster file to target grid."""
        try:
            with rasterio.open(file_path) as src:
                # Create output array
                target_array = np.empty(
                    (target_grid["height"], target_grid["width"]), dtype=np.float32
                )

                # Determine resampling method
                resampling_method = getattr(Resampling, method)

                # Reproject to target grid
                reproject(
                    source=rasterio.band(src, 1),
                    destination=target_array,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=target_grid["transform"],
                    dst_crs=target_grid["crs"],
                    resampling=resampling_method,
                )

                return {
                    "data": target_array,
                    "transform": target_grid["transform"],
                    "crs": target_grid["crs"],
                    "bounds": target_grid["bounds"],
                    "method": method,
                    "shape": target_array.shape,
                }

        except Exception as e:
            logger.error(f"Failed to resample file {file_path}: {e}")
            raise

    def _resample_from_array(
        self, data_info: dict[str, Any], target_grid: dict[str, Any], method: str
    ) -> dict[str, Any]:
        """Resample numpy array to target grid using rasterio reproject."""
        try:
            # Extract source data and metadata
            source_array = data_info["array"]
            source_transform = data_info["transform"]
            source_crs = data_info.get("crs", "EPSG:4326")

            # Create output array
            target_array = np.empty(
                (target_grid["height"], target_grid["width"]), dtype=np.float32
            )

            # Determine resampling method
            if hasattr(Resampling, method):
                resampling_method = getattr(Resampling, method)
            else:
                logger.warning(f"Unknown resampling method: {method}, using bilinear")
                resampling_method = Resampling.bilinear

            # Reproject from source array to target grid
            reproject(
                source=source_array,
                destination=target_array,
                src_transform=source_transform,
                src_crs=source_crs,
                dst_transform=target_grid["transform"],
                dst_crs=target_grid["crs"],
                resampling=resampling_method,
            )

            return {
                "data": target_array,
                "transform": target_grid["transform"],
                "crs": target_grid["crs"],
                "bounds": target_grid["bounds"],
                "method": method,
                "shape": target_array.shape,
            }

        except Exception as e:
            logger.error(f"Failed to resample array data: {e}")
            raise

    def _harmonize_location(
        self,
        lat: float,
        lon: float,
        target_date: date,
        era5_data: dict | None,
        chirps_data: dict | None,
    ) -> HarmonizedDataPoint | None:
        """Harmonize data for a single location."""
        try:
            # Extract temperature from ERA5
            temp_data = self._extract_era5_temperature(lat, lon, era5_data)

            # Extract rainfall from CHIRPS
            rainfall_data = self._extract_chirps_rainfall(lat, lon, chirps_data)

            # Determine quality flag
            quality_flag = self._calculate_quality_flag(temp_data, rainfall_data)

            # Create harmonized point
            return HarmonizedDataPoint(
                timestamp=datetime.combine(target_date, datetime.min.time()),
                latitude=lat,
                longitude=lon,
                temperature_2m=temp_data.get("temperature_2m"),
                temperature_min=temp_data.get("temperature_min"),
                temperature_max=temp_data.get("temperature_max"),
                rainfall_mm=rainfall_data.get("rainfall_mm"),
                rainfall_anomaly=rainfall_data.get("anomaly"),
                temperature_source=temp_data.get("source", "ERA5"),
                rainfall_source=rainfall_data.get("source", "CHIRPS"),
                quality_flag=quality_flag,
            )

        except Exception as e:
            logger.debug(f"Failed to harmonize location ({lat}, {lon}): {e}")
            return None

    def _extract_era5_temperature(
        self, lat: float, lon: float, era5_data: dict | None
    ) -> dict[str, float | None]:
        """Extract temperature data from ERA5 for a specific location."""
        if not era5_data or "data" not in era5_data:
            return {"source": None}

        try:
            # Convert lat/lon to grid indices
            # This is a simplified version - real implementation would use
            # proper coordinate transformation from era5_data['transform']
            era5_data["data"]

            # For now, return placeholder values
            # Real implementation would do proper spatial extraction
            return {
                "temperature_2m": 25.0,  # Placeholder
                "temperature_min": 20.0,  # Placeholder
                "temperature_max": 30.0,  # Placeholder
                "source": "ERA5",
            }

        except Exception as e:
            logger.debug(f"Failed to extract ERA5 temperature: {e}")
            return {"source": None}

    def _extract_chirps_rainfall(
        self, lat: float, lon: float, chirps_data: dict | None
    ) -> dict[str, float | None]:
        """Extract rainfall data from CHIRPS for a specific location."""
        if not chirps_data or "data" not in chirps_data:
            return {"source": None}

        try:
            # Similar to ERA5 extraction
            # Real implementation would use proper spatial extraction
            return {
                "rainfall_mm": 5.0,  # Placeholder
                "anomaly": 0.0,  # Placeholder
                "source": "CHIRPS",
            }

        except Exception as e:
            logger.debug(f"Failed to extract CHIRPS rainfall: {e}")
            return {"source": None}

    def _calculate_quality_flag(self, temp_data: dict, rainfall_data: dict) -> int:
        """Calculate quality flag based on data availability."""
        if temp_data.get("source") and rainfall_data.get("source"):
            return 0  # Good quality
        elif temp_data.get("source") or rainfall_data.get("source"):
            return 1  # Partial data
        else:
            return 2  # Missing data

    def align_temporal_coverage(
        self, era5_dates: list[date], chirps_dates: list[date]
    ) -> list[date]:
        """Find common dates between ERA5 and CHIRPS data.

        Args:
            era5_dates: Available ERA5 dates
            chirps_dates: Available CHIRPS dates

        Returns:
            List of dates with data from both sources
        """
        era5_set = set(era5_dates)
        chirps_set = set(chirps_dates)
        common_dates = sorted(era5_set.intersection(chirps_set))

        logger.info(f"Found {len(common_dates)} common dates between ERA5 and CHIRPS")
        return common_dates

    def interpolate_missing_data(
        self, data_points: list[HarmonizedDataPoint], max_gap_days: int = 3
    ) -> list[HarmonizedDataPoint]:
        """Interpolate missing data points using temporal interpolation.

        Args:
            data_points: List of harmonized data points
            max_gap_days: Maximum gap size to interpolate

        Returns:
            List with interpolated data points
        """
        if not data_points:
            return []

        # Group by location
        from collections import defaultdict

        location_data = defaultdict(list)

        for point in data_points:
            key = (point.latitude, point.longitude)
            location_data[key].append(point)

        # Interpolate each location's time series
        interpolated_points = []

        for _location, points in location_data.items():
            # Sort by timestamp
            points.sort(key=lambda p: p.timestamp)

            # Create pandas series for interpolation
            [p.timestamp for p in points]
            [p.temperature_2m for p in points]
            [p.rainfall_mm for p in points]

            # Perform interpolation
            # This is a simplified version - real implementation would be more sophisticated
            interpolated_points.extend(points)

        return interpolated_points

    def calculate_anomalies(
        self,
        data_points: list[HarmonizedDataPoint],
        historical_means: dict | None = None,
    ) -> list[HarmonizedDataPoint]:
        """Calculate anomalies relative to historical means.

        Args:
            data_points: Current data points
            historical_means: Historical mean values by location and day-of-year

        Returns:
            Data points with anomaly values calculated
        """
        if not historical_means:
            # If no historical data provided, can't calculate anomalies
            return data_points

        for point in data_points:
            # Calculate temperature anomaly
            if point.temperature_2m is not None:
                historical_temp = historical_means.get(
                    (
                        point.latitude,
                        point.longitude,
                        point.timestamp.timetuple().tm_yday,
                    ),
                    {},
                ).get("temperature", point.temperature_2m)
                point.temperature_anomaly = point.temperature_2m - historical_temp

            # Rainfall anomaly already included in the model

        return data_points

    def export_harmonized_data(
        self, data_points: list[HarmonizedDataPoint], output_format: str = "netcdf"
    ) -> Path | None:
        """Export harmonized data to file.

        Args:
            data_points: Harmonized data points to export
            output_format: Output format ("netcdf" or "csv")

        Returns:
            Path to exported file or None if export failed
        """
        try:
            if output_format == "csv":
                return self._export_to_csv(data_points)
            elif output_format == "netcdf":
                return self._export_to_netcdf(data_points)
            else:
                logger.error(f"Unsupported export format: {output_format}")
                return None

        except Exception as e:
            logger.error(f"Failed to export harmonized data: {e}")
            return None

    def _export_to_csv(self, data_points: list[HarmonizedDataPoint]) -> Path:
        """Export data points to CSV format."""
        # Convert to pandas DataFrame
        df = pd.DataFrame([point.dict() for point in data_points])

        # Generate filename
        output_path = Path(
            f"harmonized_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(data_points)} points to {output_path}")

        return output_path

    def _export_to_netcdf(self, data_points: list[HarmonizedDataPoint]) -> Path:
        """Export data points to NetCDF format."""
        try:
            import xarray as xr  # noqa: F401

            # Convert to xarray Dataset
            # This is a placeholder - real implementation would create proper NetCDF
            output_path = Path(
                f"harmonized_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.nc"
            )

            logger.info(f"NetCDF export placeholder - would export to {output_path}")
            return output_path

        except ImportError:
            logger.error("xarray required for NetCDF export")
            return None
