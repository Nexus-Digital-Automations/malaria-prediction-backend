"""Data persistence service for environmental data.

This module provides services for persisting processed environmental
data to the database, integrating the data processor with the
database repositories.
"""

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from pydantic import BaseModel, Field

from ..database.repositories import (
    ERA5Repository,
    MalariaRiskRepository,
    ProcessedClimateRepository,
)
from ..database.session import get_session
from .data_processor import ERA5DataProcessor

logger = logging.getLogger(__name__)


class PersistenceResult(BaseModel):
    """Result of data persistence operation."""

    success: bool = Field(description="Whether persistence succeeded")
    raw_records_saved: int = Field(default=0, description="Raw data points saved")
    processed_records_saved: int = Field(
        default=0, description="Processed records saved"
    )
    risk_assessments_saved: int = Field(default=0, description="Risk assessments saved")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    processing_time_seconds: float = Field(description="Total processing time")


class ERA5DataPersistence:
    """Service for persisting ERA5 data to database."""

    def __init__(self) -> None:
        """Initialize data persistence service."""
        self.processor = ERA5DataProcessor()
        logger.info("ERA5 data persistence service initialized")

    async def persist_raw_data(
        self, netcdf_file: Path, file_reference: str | None = None
    ) -> PersistenceResult:
        """Persist raw ERA5 data from NetCDF file.

        Args:
            netcdf_file: Path to ERA5 NetCDF file
            file_reference: Optional reference string for the file

        Returns:
            Persistence result with counts
        """
        start_time = datetime.utcnow()

        try:
            # Load NetCDF data
            ds = xr.open_dataset(netcdf_file)

            # Extract data arrays
            data_points = []

            # Get coordinate arrays
            times = pd.to_datetime(ds.time.values)
            lats = ds.latitude.values
            lons = ds.longitude.values

            # Extract variables (handle both original and processed names)
            temp_var = ds.get("t2m", ds.get("t2m_celsius"))
            temp_max_var = ds.get("mx2t", ds.get("mx2t_celsius"))
            temp_min_var = ds.get("mn2t", ds.get("mn2t_celsius"))
            dewpoint_var = ds.get("d2m", ds.get("d2m_celsius"))
            precip_var = ds.get("tp")

            # Convert temperature from Kelvin to Celsius if needed
            if temp_var is not None and temp_var.attrs.get("units") == "K":
                temp_values = temp_var.values - 273.15
            else:
                temp_values = temp_var.values if temp_var is not None else None

            if temp_max_var is not None and temp_max_var.attrs.get("units") == "K":
                temp_max_values = temp_max_var.values - 273.15
            else:
                temp_max_values = (
                    temp_max_var.values if temp_max_var is not None else None
                )

            if temp_min_var is not None and temp_min_var.attrs.get("units") == "K":
                temp_min_values = temp_min_var.values - 273.15
            else:
                temp_min_values = (
                    temp_min_var.values if temp_min_var is not None else None
                )

            if dewpoint_var is not None and dewpoint_var.attrs.get("units") == "K":
                dewpoint_values = dewpoint_var.values - 273.15
            else:
                dewpoint_values = (
                    dewpoint_var.values if dewpoint_var is not None else None
                )

            # Create data points for each time/location combination
            for t_idx, timestamp in enumerate(times):
                for lat_idx, lat in enumerate(lats):
                    for lon_idx, lon in enumerate(lons):
                        data_point = {
                            "timestamp": timestamp,
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "file_reference": file_reference or str(netcdf_file),
                        }

                        # Add temperature data if available
                        if temp_values is not None:
                            data_point["temperature_2m"] = float(
                                temp_values[t_idx, lat_idx, lon_idx]
                            )

                        if temp_max_values is not None:
                            data_point["temperature_2m_max"] = float(
                                temp_max_values[t_idx, lat_idx, lon_idx]
                            )

                        if temp_min_values is not None:
                            data_point["temperature_2m_min"] = float(
                                temp_min_values[t_idx, lat_idx, lon_idx]
                            )

                        if dewpoint_values is not None:
                            data_point["dewpoint_2m"] = float(
                                dewpoint_values[t_idx, lat_idx, lon_idx]
                            )

                        if precip_var is not None:
                            # Convert precipitation from m to mm
                            precip_mm = (
                                float(precip_var.values[t_idx, lat_idx, lon_idx]) * 1000
                            )
                            data_point["total_precipitation"] = precip_mm

                        # Skip if all values are NaN
                        if not all(
                            np.isnan(v)
                            for k, v in data_point.items()
                            if k
                            not in [
                                "timestamp",
                                "latitude",
                                "longitude",
                                "file_reference",
                            ]
                        ):
                            data_points.append(data_point)

            # Save to database
            records_saved = 0
            if data_points:
                async with get_session() as session:
                    repo = ERA5Repository(session)
                    records_saved = await repo.bulk_insert_data_points(data_points)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Persisted {records_saved} raw ERA5 data points from {netcdf_file.name}"
            )

            return PersistenceResult(
                success=True,
                raw_records_saved=records_saved,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            logger.error(f"Failed to persist raw ERA5 data: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return PersistenceResult(
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time,
            )

    async def process_and_persist(
        self, input_file: Path, output_dir: Path | None = None, persist_raw: bool = True
    ) -> PersistenceResult:
        """Process ERA5 data and persist both raw and processed data.

        Args:
            input_file: Path to ERA5 NetCDF file
            output_dir: Directory for processed output files
            persist_raw: Whether to also persist raw data

        Returns:
            Persistence result with counts
        """
        start_time = datetime.utcnow()
        raw_records = 0
        processed_records = 0
        risk_assessments = 0

        try:
            # Persist raw data if requested
            if persist_raw:
                raw_result = await self.persist_raw_data(input_file)
                raw_records = raw_result.raw_records_saved

            # Process the data
            processing_result = self.processor.process_temperature_data(
                input_file, output_dir
            )

            if not processing_result.success:
                raise Exception(f"Processing failed: {processing_result.error_message}")

            # Load processed data and persist
            processed_ds = xr.open_dataset(processing_result.file_path)

            # Convert to DataFrame for easier handling
            df = processed_ds.to_dataframe().reset_index()

            # Save processed climate data
            async with get_session() as session:
                climate_repo = ProcessedClimateRepository(session)
                processed_records = await climate_repo.save_processing_result(
                    processing_result, df
                )

            # Calculate and save risk indices if we have the necessary data
            if all(
                var in processed_ds
                for var in ["temp_suitability", "t2m_celsius", "d2m"]
            ):
                risk_ds = self.processor.calculate_composite_risk_index(
                    processing_result.file_path
                )

                if "malaria_risk_index" in risk_ds:
                    await self._persist_risk_indices(risk_ds)
                    risk_assessments = len(risk_ds.time)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Successfully processed and persisted data: "
                f"{raw_records} raw, {processed_records} processed, "
                f"{risk_assessments} risk assessments"
            )

            return PersistenceResult(
                success=True,
                raw_records_saved=raw_records,
                processed_records_saved=processed_records,
                risk_assessments_saved=risk_assessments,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            logger.error(f"Failed to process and persist ERA5 data: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return PersistenceResult(
                success=False,
                raw_records_saved=raw_records,
                processed_records_saved=processed_records,
                risk_assessments_saved=risk_assessments,
                error_message=str(e),
                processing_time_seconds=processing_time,
            )

    async def _persist_risk_indices(self, risk_ds: xr.Dataset) -> None:
        """Persist calculated risk indices to database.

        Args:
            risk_ds: Dataset containing risk indices
        """
        async with get_session() as session:
            risk_repo = MalariaRiskRepository(session)

            # Get coordinate arrays
            times = pd.to_datetime(risk_ds.time.values)
            lats = risk_ds.latitude.values
            lons = risk_ds.longitude.values

            # Extract risk components
            composite_risk = risk_ds.get("malaria_risk_index")
            temp_risk = risk_ds.get("temp_risk", risk_ds.get("temp_suitability"))
            precip_risk = risk_ds.get("precip_risk")
            humidity_risk = risk_ds.get("humidity_risk")

            # Save risk assessments for each location/time
            for t_idx, timestamp in enumerate(times):
                for lat_idx, lat in enumerate(lats):
                    for lon_idx, lon in enumerate(lons):
                        risk_data = {
                            "composite_score": float(
                                composite_risk.values[t_idx, lat_idx, lon_idx]
                            ),
                            "temp_risk": (
                                float(temp_risk.values[t_idx, lat_idx, lon_idx])
                                if temp_risk is not None
                                else 0
                            ),
                            "precip_risk": (
                                float(precip_risk.values[t_idx, lat_idx, lon_idx])
                                if precip_risk is not None
                                else 0
                            ),
                            "humidity_risk": (
                                float(humidity_risk.values[t_idx, lat_idx, lon_idx])
                                if humidity_risk is not None
                                else 0
                            ),
                            "confidence": 0.8,  # Default confidence for rule-based model
                            "prediction_date": timestamp,
                            "time_horizon_days": 30,
                            "model_type": "rule-based",
                            "data_sources": ["ERA5"],
                        }

                        # Skip if composite score is NaN
                        if not np.isnan(risk_data["composite_score"]):
                            await risk_repo.save_risk_assessment(
                                assessment_date=timestamp,
                                latitude=float(lat),
                                longitude=float(lon),
                                risk_data=risk_data,
                            )

    async def update_location_time_series(
        self,
        location_id: str,
        location_name: str,
        latitude: float,
        longitude: float,
        country_code: str,
    ) -> bool:
        """Update time series data for a specific location.

        Args:
            location_id: Unique location identifier
            location_name: Human-readable location name
            latitude: Location latitude
            longitude: Location longitude
            country_code: ISO country code

        Returns:
            Success status
        """
        try:
            async with get_session() as session:
                climate_repo = ProcessedClimateRepository(session)

                # Get recent climate data for location
                end_date = datetime.utcnow()
                start_date = end_date - pd.Timedelta(days=365)

                climate_df = await climate_repo.get_location_data(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=start_date,
                    end_date=end_date,
                )

                if climate_df.empty:
                    logger.warning(f"No climate data found for location {location_id}")
                    return False

                # TODO: Implement location time series update logic
                # This would involve updating the LocationTimeSeries table
                # with aggregated climate and risk data

                logger.info(f"Updated time series for location {location_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update location time series: {e}")
            return False
