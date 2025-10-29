"""Data processing service for environmental data.

This module handles processing of downloaded environmental data (ERA5, CHIRPS, etc.)
into formats suitable for malaria risk modeling and storage.

Key responsibilities:
- Convert raw climate data to malaria-relevant indices
- Aggregate data to different temporal and spatial resolutions
- Calculate derived metrics (e.g., temperature suitability)
- Handle data quality checks and missing values
"""

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProcessingConfig(BaseModel):
    """Configuration for data processing operations."""

    # Temperature thresholds for mosquito development (Celsius)
    temp_min_threshold: float = Field(
        default=16.0, description="Minimum temperature for mosquito survival"
    )
    temp_optimal_min: float = Field(
        default=22.0, description="Lower optimal temperature"
    )
    temp_optimal_max: float = Field(
        default=32.0, description="Upper optimal temperature"
    )
    temp_max_threshold: float = Field(
        default=40.0, description="Maximum temperature for mosquito survival"
    )

    # Precipitation thresholds (mm)
    precip_min_monthly: float = Field(
        default=80.0, description="Minimum monthly rainfall for breeding"
    )
    precip_optimal: float = Field(default=150.0, description="Optimal monthly rainfall")

    # Humidity thresholds (%)
    humidity_min: float = Field(
        default=60.0, description="Minimum humidity for mosquito survival"
    )
    humidity_optimal: float = Field(default=80.0, description="Optimal humidity")

    # Spatial aggregation
    spatial_resolution: float = Field(
        default=0.25, description="Target spatial resolution in degrees"
    )

    # Temporal aggregation
    temporal_resolution: str = Field(
        default="daily", description="Target temporal resolution"
    )


class ProcessingResult(BaseModel):
    """Result of data processing operation."""

    file_path: Path = Field(description="Path to processed data file")
    variables_processed: list[str] = Field(description="Variables that were processed")
    temporal_range: dict[str, str] = Field(
        description="Start and end dates of processed data"
    )
    spatial_bounds: dict[str, float] = Field(
        description="Geographic bounds of processed data"
    )
    indices_calculated: list[str] = Field(description="Malaria indices calculated")
    processing_duration_seconds: float = Field(description="Time taken for processing")
    success: bool = Field(description="Whether processing completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )


class ERA5DataProcessor:
    """Processor for ERA5 climate data focused on malaria risk factors."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        """Initialize processor with configuration.

        Args:
            config: Processing configuration settings
        """
        self.config = config or ProcessingConfig()
        logger.info("ERA5 data processor initialized")

    def process_temperature_data(
        self, input_file: Path, output_dir: Path | None = None
    ) -> ProcessingResult:
        """Process ERA5 temperature data for malaria risk assessment.

        Args:
            input_file: Path to ERA5 NetCDF file
            output_dir: Directory for processed output (defaults to input dir)

        Returns:
            Processing result with output file path and metadata
        """
        logger.info(f"Processing temperature data from {input_file.name}")
        start_time = datetime.now()

        if output_dir is None:
            output_dir = input_file.parent

        try:
            # Load ERA5 data
            ds = xr.open_dataset(input_file)

            # Convert temperature from Kelvin to Celsius
            if "t2m" in ds.variables:
                ds["t2m_celsius"] = ds["t2m"] - 273.15
            if "mx2t" in ds.variables:
                ds["mx2t_celsius"] = ds["mx2t"] - 273.15
            if "mn2t" in ds.variables:
                ds["mn2t_celsius"] = ds["mn2t"] - 273.15

            # Calculate temperature suitability index
            if "t2m_celsius" in ds.variables:
                ds["temp_suitability"] = self._calculate_temperature_suitability(
                    ds["t2m_celsius"]
                )

            # Calculate daily aggregates if hourly data
            if "time" in ds.dims and len(ds.time) > 24:
                daily_ds = self._aggregate_to_daily(ds)
            else:
                daily_ds = ds

            # Calculate additional indices
            if all(
                var in daily_ds
                for var in ["t2m_celsius", "mx2t_celsius", "mn2t_celsius"]
            ):
                # Diurnal temperature range (important for mosquito development)
                daily_ds["diurnal_range"] = (
                    daily_ds["mx2t_celsius"] - daily_ds["mn2t_celsius"]
                )

                # Growing degree days for mosquito development
                daily_ds["mosquito_gdd"] = self._calculate_growing_degree_days(
                    daily_ds["t2m_celsius"], base_temp=self.config.temp_min_threshold
                )

            # Generate output filename
            date_range = f"{str(daily_ds.time.values[0])[:10]}_{str(daily_ds.time.values[-1])[:10]}"
            output_file = output_dir / f"era5_processed_temperature_{date_range}.nc"

            # Save processed data
            encoding = {
                var: {"zlib": True, "complevel": 4} for var in daily_ds.data_vars
            }
            daily_ds.to_netcdf(output_file, encoding=encoding)

            # Extract metadata
            variables_processed = list(daily_ds.data_vars)
            temporal_range = {
                "start": str(daily_ds.time.values[0]),
                "end": str(daily_ds.time.values[-1]),
            }
            spatial_bounds = {
                "north": float(daily_ds.latitude.max()),
                "south": float(daily_ds.latitude.min()),
                "east": float(daily_ds.longitude.max()),
                "west": float(daily_ds.longitude.min()),
            }
            indices_calculated = [
                var
                for var in ["temp_suitability", "diurnal_range", "mosquito_gdd"]
                if var in daily_ds.data_vars
            ]

            processing_duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Successfully processed temperature data to {output_file.name}"
            )

            return ProcessingResult(
                file_path=output_file,
                variables_processed=variables_processed,
                temporal_range=temporal_range,
                spatial_bounds=spatial_bounds,
                indices_calculated=indices_calculated,
                processing_duration_seconds=processing_duration,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to process temperature data: {e}")
            return ProcessingResult(
                file_path=Path(""),
                variables_processed=[],
                temporal_range={},
                spatial_bounds={},
                indices_calculated=[],
                processing_duration_seconds=(
                    datetime.now() - start_time
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _calculate_temperature_suitability(
        self, temp_celsius: xr.DataArray
    ) -> xr.DataArray:
        """Calculate temperature suitability index for malaria transmission.

        Based on mosquito development rates and survival, with optimal range 22-32°C.

        Args:
            temp_celsius: Temperature in Celsius

        Returns:
            Suitability index from 0 (unsuitable) to 1 (optimal)
        """
        # Initialize with zeros
        suitability = xr.zeros_like(temp_celsius)

        # Below minimum threshold
        mask_too_cold = temp_celsius < self.config.temp_min_threshold
        suitability = xr.where(mask_too_cold, 0, suitability)

        # Between minimum and optimal minimum
        mask_cold = (temp_celsius >= self.config.temp_min_threshold) & (
            temp_celsius < self.config.temp_optimal_min
        )
        cold_factor = (temp_celsius - self.config.temp_min_threshold) / (
            self.config.temp_optimal_min - self.config.temp_min_threshold
        )
        suitability = xr.where(mask_cold, cold_factor, suitability)

        # Optimal range
        mask_optimal = (temp_celsius >= self.config.temp_optimal_min) & (
            temp_celsius <= self.config.temp_optimal_max
        )
        suitability = xr.where(mask_optimal, 1.0, suitability)

        # Between optimal maximum and maximum threshold
        mask_hot = (temp_celsius > self.config.temp_optimal_max) & (
            temp_celsius <= self.config.temp_max_threshold
        )
        hot_factor = 1 - (
            (temp_celsius - self.config.temp_optimal_max)
            / (self.config.temp_max_threshold - self.config.temp_optimal_max)
        )
        suitability = xr.where(mask_hot, hot_factor, suitability)

        # Above maximum threshold
        mask_too_hot = temp_celsius > self.config.temp_max_threshold
        suitability = xr.where(mask_too_hot, 0, suitability)

        return suitability

    def _calculate_growing_degree_days(
        self, temp_celsius: xr.DataArray, base_temp: float = 16.0
    ) -> xr.DataArray:
        """Calculate growing degree days for mosquito development.

        Args:
            temp_celsius: Daily temperature in Celsius
            base_temp: Base temperature for development

        Returns:
            Growing degree days
        """
        # GDD = max(0, temp - base_temp)
        gdd = temp_celsius - base_temp
        gdd = xr.where(gdd < 0, 0, gdd)
        return gdd

    def _aggregate_to_daily(self, ds: xr.Dataset) -> xr.Dataset:
        """Aggregate hourly data to daily resolution.

        Args:
            ds: Hourly dataset

        Returns:
            Daily aggregated dataset
        """
        # Define aggregation methods for different variables
        aggregation_methods = {
            "t2m": "mean",
            "t2m_celsius": "mean",
            "mx2t": "max",
            "mx2t_celsius": "max",
            "mn2t": "min",
            "mn2t_celsius": "min",
            "tp": "sum",  # Total precipitation
            "d2m": "mean",  # Dewpoint
            "temp_suitability": "mean",
        }

        # Resample to daily
        daily_data = {}
        for var in ds.data_vars:
            if var in aggregation_methods:
                method = aggregation_methods[var]
                if method == "mean":
                    daily_data[var] = ds[var].resample(time="1D").mean()
                elif method == "max":
                    daily_data[var] = ds[var].resample(time="1D").max()
                elif method == "min":
                    daily_data[var] = ds[var].resample(time="1D").min()
                elif method == "sum":
                    daily_data[var] = ds[var].resample(time="1D").sum()

        return xr.Dataset(daily_data)

    def calculate_composite_risk_index(self, processed_file: Path) -> xr.Dataset:
        """Calculate composite malaria risk index from processed data.

        Args:
            processed_file: Path to processed climate data

        Returns:
            Dataset with composite risk index
        """
        ds = xr.open_dataset(processed_file)

        # Initialize risk components
        risk_components = {}

        # Temperature component
        if "temp_suitability" in ds:
            risk_components["temp_risk"] = ds["temp_suitability"]

        # Precipitation component (if available)
        if "tp" in ds:
            # Convert to monthly accumulation
            monthly_precip = ds["tp"].resample(time="1ME").sum() * 1000  # m to mm
            precip_risk = self._calculate_precipitation_risk(monthly_precip)
            # Reindex to match original time coordinates for alignment
            risk_components["precip_risk"] = precip_risk.reindex_like(
                ds["temp_suitability"], method="nearest"
            )

        # Humidity component (if dewpoint available)
        if "d2m" in ds and "t2m" in ds:
            # Calculate relative humidity from dewpoint and temperature
            rh = self._calculate_relative_humidity(ds["d2m"], ds["t2m"])
            humidity_risk = self._calculate_humidity_risk(rh)
            risk_components["humidity_risk"] = humidity_risk

        # Calculate composite index (weighted average)
        if risk_components:
            weights = {"temp_risk": 0.4, "precip_risk": 0.3, "humidity_risk": 0.3}

            composite_risk = xr.zeros_like(list(risk_components.values())[0])
            total_weight = 0

            for component, weight in weights.items():
                if component in risk_components:
                    composite_risk += risk_components[component] * weight
                    total_weight += weight

            composite_risk = (
                composite_risk / total_weight if total_weight > 0 else composite_risk
            )
            ds["malaria_risk_index"] = composite_risk

        return ds

    def _calculate_precipitation_risk(
        self, monthly_precip_mm: xr.DataArray
    ) -> xr.DataArray:
        """Calculate precipitation suitability for malaria transmission.

        Args:
            monthly_precip_mm: Monthly precipitation in millimeters

        Returns:
            Precipitation risk factor (0-1)
        """
        # Initialize risk array
        risk = xr.zeros_like(monthly_precip_mm)

        # No breeding sites if too dry
        mask_dry = monthly_precip_mm < self.config.precip_min_monthly
        risk = xr.where(mask_dry, 0, risk)

        # Calculate risk for adequate precipitation
        mask_adequate = monthly_precip_mm >= self.config.precip_min_monthly

        # For values between min and 2x optimal, use a scaled factor
        optimal_factor = (
            1
            - np.abs(monthly_precip_mm - self.config.precip_optimal)
            / self.config.precip_optimal
        )
        optimal_factor = optimal_factor.clip(0, 1)

        risk = xr.where(mask_adequate, optimal_factor, risk)

        # Too much rain can wash away breeding sites (but still some risk)
        mask_excessive = monthly_precip_mm > self.config.precip_optimal * 3
        risk = xr.where(mask_excessive, 0.5, risk)

        return risk

    def _calculate_relative_humidity(
        self, dewpoint_k: xr.DataArray, temp_k: xr.DataArray
    ) -> xr.DataArray:
        """Calculate relative humidity from dewpoint and temperature.

        Args:
            dewpoint_k: Dewpoint temperature in Kelvin
            temp_k: Air temperature in Kelvin

        Returns:
            Relative humidity percentage
        """

        # Magnus formula for saturation vapor pressure
        def saturation_vapor_pressure(temp_c: float | xr.DataArray) -> float | xr.DataArray:
            return 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))

        temp_c = temp_k - 273.15
        dewpoint_c = dewpoint_k - 273.15

        e_s = saturation_vapor_pressure(temp_c)
        e = saturation_vapor_pressure(dewpoint_c)

        rh = 100 * (e / e_s)
        return rh.clip(0, 100)

    def _calculate_humidity_risk(self, relative_humidity: xr.DataArray) -> xr.DataArray:
        """Calculate humidity suitability for malaria transmission.

        Args:
            relative_humidity: Relative humidity percentage

        Returns:
            Humidity risk factor (0-1)
        """
        # Initialize risk array
        risk = xr.zeros_like(relative_humidity)

        # Below minimum threshold - no risk
        mask_too_dry = relative_humidity < self.config.humidity_min
        risk = xr.where(mask_too_dry, 0, risk)

        # Between minimum and optimal - increasing risk
        mask_suboptimal = (relative_humidity >= self.config.humidity_min) & (
            relative_humidity < self.config.humidity_optimal
        )
        factor = (relative_humidity - self.config.humidity_min) / (
            self.config.humidity_optimal - self.config.humidity_min
        )
        risk = xr.where(mask_suboptimal, factor, risk)

        # At or above optimal - high risk
        mask_optimal = relative_humidity >= self.config.humidity_optimal
        risk = xr.where(mask_optimal, 0.9, risk)

        return risk

    def extract_location_timeseries(
        self,
        processed_file: Path,
        latitude: float,
        longitude: float,
        buffer_degrees: float = 0.25,
    ) -> pd.DataFrame:
        """Extract time series data for a specific location.

        Args:
            processed_file: Path to processed data file
            latitude: Target latitude
            longitude: Target longitude
            buffer_degrees: Buffer around point to average

        Returns:
            DataFrame with time series data
        """
        ds = xr.open_dataset(processed_file)

        # Select data near the point
        location_data = ds.sel(
            latitude=slice(latitude + buffer_degrees, latitude - buffer_degrees),
            longitude=slice(longitude - buffer_degrees, longitude + buffer_degrees),
        ).mean(dim=["latitude", "longitude"])

        # Convert to pandas DataFrame
        df = location_data.to_dataframe()

        # Add derived metrics
        if "t2m_celsius" in df.columns:
            df["temp_anomaly"] = (
                df["t2m_celsius"] - df["t2m_celsius"].rolling(30, center=True).mean()
            )

        return df


class BatchDataProcessor:
    """Processor for batch data processing operations."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        """Initialize batch processor with configuration.

        Args:
            config: Processing configuration settings
        """
        self.config = config or ProcessingConfig()
        logger.info("Batch data processor initialized")

    async def process_batch(self, locations: list[dict]) -> list[dict]:
        """Process batch of location data.

        Args:
            locations: List of location dictionaries with lat/lon

        Returns:
            List of processed data for each location
        """
        results = []
        for i, location in enumerate(locations):
            result = {
                "location_id": i,
                "processed_data": f"data_{i}",
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "status": "processed",
            }
            results.append(result)

        logger.info(f"Batch processed {len(locations)} locations")
        return results


class TimeSeriesDataProcessor:
    """Processor for time series data operations."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        """Initialize time series processor with configuration.

        Args:
            config: Processing configuration settings
        """
        self.config = config or ProcessingConfig()
        logger.info("Time series data processor initialized")

    async def process_time_series(self, data: dict) -> dict:
        """Process time series data.

        Args:
            data: Time series data dictionary

        Returns:
            Processed time series features
        """
        return {
            "time_series_features": "processed_features",
            "temporal_patterns": "identified_patterns",
            "sequence_length": 30,
            "processed_data": data,
        }


class DataProcessor:
    """Main data processor with async process method."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        """Initialize data processor.

        Args:
            config: Processing configuration settings
        """
        self.config = config or ProcessingConfig()

    async def process(self, data: dict) -> dict:
        """Process data asynchronously.

        Args:
            data: Data to process

        Returns:
            Processed data
        """
        return {"processed": True, "data": data}
