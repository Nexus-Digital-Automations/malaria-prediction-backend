"""
Data Export Service for Analytics Dashboard.

This module provides comprehensive data export functionality for analytics
dashboards, supporting multiple formats including CSV, Excel, PDF, and JSON.
"""

import csv
import json
import logging
from datetime import datetime
from io import BytesIO, StringIO
from typing import Any

import pandas as pd
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..database.models import (
    ERA5DataPoint,
    MalariaRiskIndex,
    MODISDataPoint,
    ProcessedClimateData,
)

logger = logging.getLogger(__name__)


class DataExportService:
    """Comprehensive data export service for analytics dashboards."""

    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize the data export service.

        Args:
            db_session: Database session for data queries
        """
        self.db = db_session
        self.supported_formats = ["json", "csv", "excel", "parquet"]

    async def export_prediction_accuracy_data(
        self,
        export_format: str = "csv",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        model_type: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, str | bytes | int]:
        """
        Export prediction accuracy data in specified format.

        Args:
            export_format: Export format (csv, json, excel, parquet)
            start_date: Start date filter
            end_date: End date filter
            model_type: Model type filter
            include_metadata: Include metadata in export

        Returns:
            Dictionary containing exported data and metadata
        """
        try:
            # Build query
            stmt = select(MalariaRiskIndex)

            if start_date:
                stmt = stmt.where(MalariaRiskIndex.assessment_date >= start_date)
            if end_date:
                stmt = stmt.where(MalariaRiskIndex.assessment_date <= end_date)
            if model_type:
                stmt = stmt.where(MalariaRiskIndex.model_type == model_type)

            # Get data
            result = await self.db.execute(stmt)
            risk_data = result.scalars().all()

            # Prepare data for export
            export_data = []
            for record in risk_data:
                row = {
                    "assessment_date": record.assessment_date.isoformat(),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "location_name": record.location_name,
                    "composite_risk_score": record.composite_risk_score,
                    "risk_level": record.risk_level,
                    "confidence_score": record.confidence_score,
                    "temperature_risk_component": record.temperature_risk_component,
                    "precipitation_risk_component": record.precipitation_risk_component,
                    "humidity_risk_component": record.humidity_risk_component,
                    "vegetation_risk_component": record.vegetation_risk_component,
                    "model_type": record.model_type,
                    "model_version": record.model_version,
                    "prediction_date": record.prediction_date.isoformat(),
                    "time_horizon_days": record.time_horizon_days,
                }

                if include_metadata:
                    row.update({
                        "created_at": record.created_at.isoformat(),
                        "data_sources": record.data_sources,
                        "additional_factors": record.additional_factors,
                    })

                export_data.append(row)

            # Export in requested format
            if export_format == "json":
                return {
                    "data": json.dumps(export_data, indent=2),
                    "content_type": "application/json",
                    "filename": f"prediction_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "size": len(json.dumps(export_data)),
                }

            elif export_format == "csv":
                csv_output = StringIO()
                if export_data:
                    writer = csv.DictWriter(csv_output, fieldnames=export_data[0].keys())
                    writer.writeheader()
                    writer.writerows(export_data)

                csv_data = csv_output.getvalue()
                return {
                    "data": csv_data,
                    "content_type": "text/csv",
                    "filename": f"prediction_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "size": len(csv_data),
                }

            elif export_format == "excel":
                df = pd.DataFrame(export_data)
                excel_output = BytesIO()

                with pd.ExcelWriter(excel_output, engine='openpyxl') as excel_writer:
                    df.to_excel(excel_writer, sheet_name='Prediction_Accuracy', index=False)

                    # Add metadata sheet if requested
                    if include_metadata:
                        metadata_df = pd.DataFrame([{
                            "export_date": datetime.now().isoformat(),
                            "total_records": len(export_data),
                            "date_range_start": start_date.isoformat() if start_date else "All",
                            "date_range_end": end_date.isoformat() if end_date else "All",
                            "model_filter": model_type or "All",
                        }])
                        metadata_df.to_excel(excel_writer, sheet_name='Metadata', index=False)

                excel_data = excel_output.getvalue()
                return {
                    "data": excel_data,
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "filename": f"prediction_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "size": len(excel_data),
                }

            elif export_format == "parquet":
                df = pd.DataFrame(export_data)
                parquet_output = BytesIO()
                df.to_parquet(parquet_output, index=False)

                parquet_data = parquet_output.getvalue()
                return {
                    "data": parquet_data,
                    "content_type": "application/octet-stream",
                    "filename": f"prediction_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                    "size": len(parquet_data),
                }

            else:
                raise ValueError(f"Unsupported export format: {export_format}")

        except Exception as e:
            logger.error(f"Error exporting prediction accuracy data: {e}")
            raise

    async def export_environmental_data(
        self,
        export_format: str = "csv",
        data_source: str = "processed_climate",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        location_bounds: dict[str, float] | None = None,
        aggregation_level: str = "daily",
        include_quality_flags: bool = True,
    ) -> dict[str, str | bytes | int]:
        """
        Export environmental data in specified format.

        Args:
            export_format: Export format
            data_source: Data source type (processed_climate, era5, chirps, modis)
            start_date: Start date filter
            end_date: End date filter
            location_bounds: Geographic bounds (lat_min, lat_max, lon_min, lon_max)
            aggregation_level: Data aggregation level
            include_quality_flags: Include data quality indicators

        Returns:
            Dictionary containing exported data and metadata
        """
        try:
            export_data = []

            if data_source == "processed_climate":
                stmt = select(ProcessedClimateData)

                if start_date:
                    stmt = stmt.where(ProcessedClimateData.date >= start_date)
                if end_date:
                    stmt = stmt.where(ProcessedClimateData.date <= end_date)
                if location_bounds:
                    stmt = stmt.where(
                        and_(
                            ProcessedClimateData.latitude.between(
                                location_bounds["lat_min"], location_bounds["lat_max"]
                            ),
                            ProcessedClimateData.longitude.between(
                                location_bounds["lon_min"], location_bounds["lon_max"]
                            ),
                        )
                    )

                stmt = stmt.limit(50000)  # Limit for performance
                result = await self.db.execute(stmt)
                climate_data = result.scalars().all()

                for record in climate_data:
                    row = {
                        "date": record.date.isoformat(),
                        "latitude": record.latitude,
                        "longitude": record.longitude,
                        "mean_temperature": record.mean_temperature,
                        "max_temperature": record.max_temperature,
                        "min_temperature": record.min_temperature,
                        "diurnal_temperature_range": record.diurnal_temperature_range,
                        "daily_precipitation_mm": record.daily_precipitation_mm,
                        "monthly_precipitation_mm": record.monthly_precipitation_mm,
                        "mean_relative_humidity": record.mean_relative_humidity,
                        "temperature_suitability": record.temperature_suitability,
                        "precipitation_risk_factor": record.precipitation_risk_factor,
                        "humidity_risk_factor": record.humidity_risk_factor,
                        "mosquito_growing_degree_days": record.mosquito_growing_degree_days,
                    }

                    if include_quality_flags:
                        row.update({
                            "processing_version": record.processing_version,
                            "processing_timestamp": record.processing_timestamp.isoformat(),
                        })

                    export_data.append(row)

            elif data_source == "era5":
                stmt = select(ERA5DataPoint)

                if start_date:
                    stmt = stmt.where(ERA5DataPoint.timestamp >= start_date)
                if end_date:
                    stmt = stmt.where(ERA5DataPoint.timestamp <= end_date)
                if location_bounds:
                    stmt = stmt.where(
                        and_(
                            ERA5DataPoint.latitude.between(
                                location_bounds["lat_min"], location_bounds["lat_max"]
                            ),
                            ERA5DataPoint.longitude.between(
                                location_bounds["lon_min"], location_bounds["lon_max"]
                            ),
                        )
                    )

                stmt = stmt.limit(50000)
                result = await self.db.execute(stmt)
                era5_data = result.scalars().all()

                for record in era5_data:
                    row = {
                        "timestamp": record.timestamp.isoformat(),
                        "latitude": record.latitude,
                        "longitude": record.longitude,
                        "temperature_2m": record.temperature_2m,
                        "temperature_2m_max": record.temperature_2m_max,
                        "temperature_2m_min": record.temperature_2m_min,
                        "dewpoint_2m": record.dewpoint_2m,
                        "total_precipitation": record.total_precipitation,
                        "wind_speed_10m": record.wind_speed_10m,
                        "wind_direction_10m": record.wind_direction_10m,
                        "surface_pressure": record.surface_pressure,
                    }

                    if include_quality_flags:
                        row.update({
                            "data_source": record.data_source,
                            "ingestion_timestamp": record.ingestion_timestamp.isoformat(),
                        })

                    export_data.append(row)

            elif data_source == "modis":
                stmt = select(MODISDataPoint)

                if start_date:
                    stmt = stmt.where(MODISDataPoint.date >= start_date)
                if end_date:
                    stmt = stmt.where(MODISDataPoint.date <= end_date)
                if location_bounds:
                    stmt = stmt.where(
                        and_(
                            MODISDataPoint.latitude.between(
                                location_bounds["lat_min"], location_bounds["lat_max"]
                            ),
                            MODISDataPoint.longitude.between(
                                location_bounds["lon_min"], location_bounds["lon_max"]
                            ),
                        )
                    )

                stmt = stmt.limit(50000)
                result = await self.db.execute(stmt)
                modis_data = result.scalars().all()

                for record in modis_data:
                    row = {
                        "date": record.date.isoformat(),
                        "latitude": record.latitude,
                        "longitude": record.longitude,
                        "ndvi": record.ndvi,
                        "evi": record.evi,
                        "lai": record.lai,
                        "fpar": record.fpar,
                        "lst_day_celsius": record.lst_day - 273.15 if record.lst_day else None,
                        "lst_night_celsius": record.lst_night - 273.15 if record.lst_night else None,
                        "composite_day_of_year": record.composite_day_of_year,
                    }

                    if include_quality_flags:
                        row.update({
                            "ndvi_quality": record.ndvi_quality,
                            "evi_quality": record.evi_quality,
                            "pixel_reliability": record.pixel_reliability,
                            "product_type": record.product_type,
                        })

                    export_data.append(row)

            # Export logic (similar to prediction accuracy export)
            return await self._format_export_data(
                export_data,
                export_format,
                f"{data_source}_environmental_data",
                include_quality_flags
            )

        except Exception as e:
            logger.error(f"Error exporting environmental data: {e}")
            raise

    async def export_custom_report(
        self,
        report_config: dict[str, Any],
        export_format: str = "json",
    ) -> dict[str, str | bytes | int]:
        """
        Generate and export custom report based on configuration.

        Args:
            report_config: Report configuration
            export_format: Export format

        Returns:
            Dictionary containing exported report and metadata
        """
        try:
            report_data: dict[str, Any] = {
                "report_metadata": {
                    "type": report_config.get("type", "custom"),
                    "generated_at": datetime.now().isoformat(),
                    "configuration": report_config,
                },
                "sections": [],
                "summary": {},
            }

            # Process each requested section
            data_sources = report_config.get("data_sources", [])
            time_range = report_config.get("time_range", {})

            for source in data_sources:
                if source == "risk_assessment":
                    risk_stmt = select(MalariaRiskIndex)

                    if time_range.get("start"):
                        risk_stmt = risk_stmt.where(
                            MalariaRiskIndex.assessment_date >= datetime.fromisoformat(time_range["start"])
                        )
                    if time_range.get("end"):
                        risk_stmt = risk_stmt.where(
                            MalariaRiskIndex.assessment_date <= datetime.fromisoformat(time_range["end"])
                        )

                    risk_stmt = risk_stmt.limit(10000)
                    risk_result = await self.db.execute(risk_stmt)
                    risk_data = risk_result.scalars().all()

                    section_data = {
                        "section_name": "risk_assessments",
                        "total_records": len(risk_data),
                        "summary_statistics": {
                            "avg_risk_score": sum(r.composite_risk_score for r in risk_data) / len(risk_data) if risk_data else 0,
                            "risk_distribution": {
                                level: len([r for r in risk_data if r.risk_level == level])
                                for level in ["low", "medium", "high", "critical"]
                            },
                        },
                        "sample_data": [
                            {
                                "date": r.assessment_date.isoformat(),
                                "location": r.location_name,
                                "risk_score": r.composite_risk_score,
                                "risk_level": r.risk_level,
                                "confidence": r.confidence_score,
                            }
                            for r in risk_data[:100]  # Sample of first 100 records
                        ],
                    }

                    report_data["sections"].append(section_data)

            # Generate summary
            total_records = sum(section.get("total_records", 0) for section in report_data["sections"])
            report_data["summary"] = {
                "total_data_points": total_records,
                "sections_included": len(report_data["sections"]),
                "time_range": time_range,
                "completeness_score": 1.0 if total_records > 0 else 0.0,
            }

            # Format and return
            return await self._format_export_data(
                [report_data],
                export_format,
                "custom_report",
                include_metadata=True
            )

        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            raise

    async def _format_export_data(
        self,
        data: list[dict[str, Any]],
        export_format: str,
        filename_prefix: str,
        include_metadata: bool = True,
    ) -> dict[str, str | bytes | int]:
        """
        Format data for export in specified format.

        Args:
            data: Data to export
            export_format: Target format
            filename_prefix: Prefix for filename
            include_metadata: Include metadata

        Returns:
            Formatted export data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_format == "json":
            json_data = json.dumps(data, indent=2)
            return {
                "data": json_data,
                "content_type": "application/json",
                "filename": f"{filename_prefix}_{timestamp}.json",
                "size": len(json_data),
                "record_count": len(data),
            }

        elif export_format == "csv":
            if not data:
                return {
                    "data": "",
                    "content_type": "text/csv",
                    "filename": f"{filename_prefix}_{timestamp}.csv",
                    "size": 0,
                    "record_count": 0,
                }

            csv_output = StringIO()
            writer = csv.DictWriter(csv_output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

            csv_data = csv_output.getvalue()
            return {
                "data": csv_data,
                "content_type": "text/csv",
                "filename": f"{filename_prefix}_{timestamp}.csv",
                "size": len(csv_data),
                "record_count": len(data),
            }

        elif export_format == "excel":
            df = pd.DataFrame(data)
            excel_output = BytesIO()

            with pd.ExcelWriter(excel_output, engine='openpyxl') as excel_writer:
                df.to_excel(excel_writer, sheet_name='Data', index=False)

                if include_metadata:
                    metadata_df = pd.DataFrame([{
                        "export_timestamp": datetime.now().isoformat(),
                        "total_records": len(data),
                        "export_format": export_format,
                        "filename_prefix": filename_prefix,
                    }])
                    metadata_df.to_excel(excel_writer, sheet_name='Export_Metadata', index=False)

            excel_data = excel_output.getvalue()
            return {
                "data": excel_data,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "filename": f"{filename_prefix}_{timestamp}.xlsx",
                "size": len(excel_data),
                "record_count": len(data),
            }

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats."""
        return self.supported_formats.copy()

    async def get_export_statistics(self) -> dict[str, Any]:
        """
        Get statistics about available data for export.

        Returns:
            Statistics about data availability
        """
        try:
            stats: dict[str, Any] = {
                "data_sources": {},
                "date_ranges": {},
                "record_counts": {},
                "last_updated": datetime.now().isoformat(),
            }

            # Risk assessment data stats
            risk_count_stmt = select(func.count()).select_from(MalariaRiskIndex)
            risk_count_result = await self.db.execute(risk_count_stmt)
            risk_count = risk_count_result.scalar() or 0

            risk_latest_stmt = select(MalariaRiskIndex).order_by(desc(MalariaRiskIndex.assessment_date)).limit(1)
            risk_latest_result = await self.db.execute(risk_latest_stmt)
            risk_latest = risk_latest_result.scalar()

            risk_earliest_stmt = select(MalariaRiskIndex).order_by(MalariaRiskIndex.assessment_date.asc()).limit(1)
            risk_earliest_result = await self.db.execute(risk_earliest_stmt)
            risk_earliest = risk_earliest_result.scalar()

            stats["data_sources"]["risk_assessments"] = {
                "available": risk_count > 0,
                "record_count": risk_count,
                "date_range": {
                    "earliest": risk_earliest.assessment_date.isoformat() if risk_earliest else None,
                    "latest": risk_latest.assessment_date.isoformat() if risk_latest else None,
                }
            }

            # Environmental data stats
            climate_count_stmt = select(func.count()).select_from(ProcessedClimateData)
            climate_count_result = await self.db.execute(climate_count_stmt)
            climate_count = climate_count_result.scalar() or 0

            climate_latest_stmt = select(ProcessedClimateData).order_by(desc(ProcessedClimateData.date)).limit(1)
            climate_latest_result = await self.db.execute(climate_latest_stmt)
            climate_latest = climate_latest_result.scalar()

            stats["data_sources"]["climate_data"] = {
                "available": climate_count > 0,
                "record_count": climate_count,
                "latest_date": climate_latest.date.isoformat() if climate_latest else None,
            }

            # ERA5 data stats
            era5_count_stmt = select(func.count()).select_from(ERA5DataPoint)
            era5_count_result = await self.db.execute(era5_count_stmt)
            era5_count = era5_count_result.scalar() or 0
            stats["data_sources"]["era5_data"] = {
                "available": era5_count > 0,
                "record_count": era5_count,
            }

            # MODIS data stats
            modis_count_stmt = select(func.count()).select_from(MODISDataPoint)
            modis_count_result = await self.db.execute(modis_count_stmt)
            modis_count = modis_count_result.scalar() or 0
            stats["data_sources"]["modis_data"] = {
                "available": modis_count > 0,
                "record_count": modis_count,
            }

            stats["summary"] = {
                "total_available_records": risk_count + climate_count + era5_count + modis_count,
                "data_sources_available": sum(
                    1 for source in stats["data_sources"].values() if source["available"]
                ),
                "export_formats_supported": len(self.supported_formats),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting export statistics: {e}")
            return {"error": str(e)}


async def get_data_export_service(db: AsyncSession) -> DataExportService:
    """Get configured data export service instance."""
    return DataExportService(db)
