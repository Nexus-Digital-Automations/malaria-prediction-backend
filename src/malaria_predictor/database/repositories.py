"""Repository pattern for database operations.

This module provides repository classes that encapsulate
database operations for different data types, promoting
clean separation of concerns and testability.
"""

import logging
from datetime import datetime, timedelta
from typing import cast

import pandas as pd
from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.data_processor import ProcessingResult
from .models import (
    CHIRPSDataPoint,
    ERA5DataPoint,
    MalariaRiskIndex,
    MODISDataPoint,
    ProcessedClimateData,
    WorldPopDataPoint,
)
from .security_models import User

logger = logging.getLogger(__name__)


class ERA5Repository:
    """Repository for ERA5 climate data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def bulk_insert_data_points(
        self, data_points: list[dict], upsert: bool = True
    ) -> int:
        """Bulk insert ERA5 data points.

        Args:
            data_points: List of data point dictionaries
            upsert: Whether to update on conflict

        Returns:
            Number of rows inserted/updated
        """
        if not data_points:
            return 0

        if upsert:
            # Check if we're using SQLite (for testing) or PostgreSQL
            dialect_name = self.session.bind.dialect.name

            if dialect_name == "sqlite":
                # SQLite doesn't support ON CONFLICT the same way
                # For testing, just do a simple insert
                stmt = insert(ERA5DataPoint).values(data_points)
            else:
                # Use PostgreSQL ON CONFLICT for efficient upserts
                stmt = insert(ERA5DataPoint).values(data_points)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_era5_timestamp_location",
                    set_={
                        "temperature_2m": stmt.excluded.temperature_2m,
                        "temperature_2m_max": stmt.excluded.temperature_2m_max,
                        "temperature_2m_min": stmt.excluded.temperature_2m_min,
                        "dewpoint_2m": stmt.excluded.dewpoint_2m,
                        "total_precipitation": stmt.excluded.total_precipitation,
                        "ingestion_timestamp": func.now(),
                    },
                )
        else:
            stmt = insert(ERA5DataPoint).values(data_points)

        result = await self.session.execute(stmt)
        await self.session.commit()

        logger.info(f"Bulk inserted/updated {result.rowcount} ERA5 data points")
        return cast(int, result.rowcount) # type: ignore[redundant-cast]

    async def get_data_range(
        self,
        start_date: datetime,
        end_date: datetime,
        latitude: float | None = None,
        longitude: float | None = None,
        buffer_degrees: float = 0.25,
    ) -> list[ERA5DataPoint]:
        """Get ERA5 data for a date range and optional location.

        Args:
            start_date: Start of date range
            end_date: End of date range
            latitude: Optional center latitude
            longitude: Optional center longitude
            buffer_degrees: Buffer around location point

        Returns:
            List of ERA5 data points
        """
        query = select(ERA5DataPoint).where(
            and_(
                ERA5DataPoint.timestamp >= start_date,
                ERA5DataPoint.timestamp <= end_date,
            )
        )

        if latitude is not None and longitude is not None:
            query = query.where(
                and_(
                    ERA5DataPoint.latitude >= latitude - buffer_degrees,
                    ERA5DataPoint.latitude <= latitude + buffer_degrees,
                    ERA5DataPoint.longitude >= longitude - buffer_degrees,
                    ERA5DataPoint.longitude <= longitude + buffer_degrees,
                )
            )

        query = query.order_by(ERA5DataPoint.timestamp)

        result = await self.session.execute(query)
        return cast(list[ERA5DataPoint], result.scalars().all())

    async def get_data_by_location_and_timerange(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        buffer_degrees: float = 0.25,
    ) -> list[ERA5DataPoint]:
        """Get ERA5 data for a specific location and time range.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            start_date: Start of date range
            end_date: End of date range
            buffer_degrees: Buffer around location point

        Returns:
            List of ERA5 data points
        """
        return await self.get_data_range(
            start_date=start_date,
            end_date=end_date,
            latitude=latitude,
            longitude=longitude,
            buffer_degrees=buffer_degrees,
        )

    async def get_latest_timestamp(
        self, latitude: float | None = None, longitude: float | None = None
    ) -> datetime | None:
        """Get the latest data timestamp.

        Args:
            latitude: Optional latitude filter
            longitude: Optional longitude filter

        Returns:
            Latest timestamp or None if no data
        """
        query = select(func.max(ERA5DataPoint.timestamp))

        if latitude is not None and longitude is not None:
            query = query.where(
                and_(
                    ERA5DataPoint.latitude == latitude,
                    ERA5DataPoint.longitude == longitude,
                )
            )

        result = await self.session.execute(query)
        return cast(datetime | None, result.scalar()) # type: ignore[redundant-cast]

    async def delete_old_data(self, days_to_keep: int = 365) -> int:
        """Delete data older than specified days.

        Args:
            days_to_keep: Number of days of data to retain

        Returns:
            Number of rows deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        result = await self.session.execute(
            ERA5DataPoint.__table__.delete().where( # type: ignore[attr-defined]
                ERA5DataPoint.timestamp < cutoff_date
            )
        )
        await self.session.commit()

        logger.info(f"Deleted {result.rowcount} old ERA5 data points") # type: ignore[attr-defined]
        return cast(int, result.rowcount) # type: ignore[attr-defined]


class ProcessedClimateRepository:
    """Repository for processed climate data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save_processing_result(
        self, result: ProcessingResult, data: pd.DataFrame
    ) -> int:
        """Save processed climate data from a processing result.

        Args:
            result: Processing result metadata
            data: DataFrame with processed climate data

        Returns:
            Number of rows saved
        """
        if data.empty:
            return 0

        # Convert DataFrame to list of dictionaries
        records = []
        for _, row in data.iterrows():
            record = {
                "date": pd.to_datetime(row.get("time", row.name)),
                "latitude": row.get("latitude", result.spatial_bounds["north"]),
                "longitude": row.get("longitude", result.spatial_bounds["west"]),
                "mean_temperature": row.get(
                    "t2m_celsius", row.get("temperature_2m", 0)
                ),
                "max_temperature": row.get(
                    "mx2t_celsius", row.get("temperature_2m_max", 0)
                ),
                "min_temperature": row.get(
                    "mn2t_celsius", row.get("temperature_2m_min", 0)
                ),
                "diurnal_temperature_range": row.get("diurnal_range", 0),
                "temperature_suitability": row.get("temp_suitability", 0),
                "mosquito_growing_degree_days": row.get("mosquito_gdd", 0),
                "daily_precipitation_mm": row.get("tp", 0) * 1000,  # Convert m to mm
                "mean_relative_humidity": row.get("relative_humidity", 0),
                "processing_version": "1.0.0",
                "source_file_reference": str(result.file_path),
            }
            records.append(record)

        # Bulk upsert
        dialect_name = self.session.bind.dialect.name

        if dialect_name == "sqlite":
            # SQLite doesn't support ON CONFLICT the same way
            stmt = insert(ProcessedClimateData).values(records)
        else:
            stmt = insert(ProcessedClimateData).values(records)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_processed_date_location",
                set_={
                    "mean_temperature": stmt.excluded.mean_temperature,
                    "max_temperature": stmt.excluded.max_temperature,
                    "min_temperature": stmt.excluded.min_temperature,
                    "temperature_suitability": stmt.excluded.temperature_suitability,
                    "processing_timestamp": func.now(),
                },
            )

        result = await self.session.execute(stmt) # type: ignore[assignment]
        await self.session.commit()

        logger.info(f"Saved {result.rowcount} processed climate records") # type: ignore[attr-defined]
        return cast(int, result.rowcount) # type: ignore[attr-defined]

    async def get_location_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        buffer_degrees: float = 0.25,
    ) -> pd.DataFrame:
        """Get processed climate data for a location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            start_date: Start date
            end_date: End date
            buffer_degrees: Buffer around location

        Returns:
            DataFrame with climate data
        """
        query = (
            select(ProcessedClimateData)
            .where(
                and_(
                    ProcessedClimateData.date >= start_date,
                    ProcessedClimateData.date <= end_date,
                    ProcessedClimateData.latitude >= latitude - buffer_degrees,
                    ProcessedClimateData.latitude <= latitude + buffer_degrees,
                    ProcessedClimateData.longitude >= longitude - buffer_degrees,
                    ProcessedClimateData.longitude <= longitude + buffer_degrees,
                )
            )
            .order_by(ProcessedClimateData.date)
        )

        result = await self.session.execute(query)
        data = result.scalars().all()

        # Convert to DataFrame
        if data:
            records = [
                {
                    "date": d.date,
                    "mean_temperature": d.mean_temperature,
                    "max_temperature": d.max_temperature,
                    "min_temperature": d.min_temperature,
                    "temperature_suitability": d.temperature_suitability,
                    "daily_precipitation_mm": d.daily_precipitation_mm,
                    "mean_relative_humidity": d.mean_relative_humidity,
                }
                for d in data
            ]
            return pd.DataFrame(records)

        return pd.DataFrame()

    async def get_latest_processed_data(
        self, latitude: float, longitude: float, limit: int = 10
    ) -> list[ProcessedClimateData]:
        """Get latest processed climate data for a location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            limit: Maximum number of records to return

        Returns:
            List of latest processed climate data records
        """
        query = (
            select(ProcessedClimateData)
            .where(
                and_(
                    ProcessedClimateData.latitude == latitude,
                    ProcessedClimateData.longitude == longitude,
                )
            )
            .order_by(ProcessedClimateData.date.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return cast(list[ProcessedClimateData], result.scalars().all())


class MalariaRiskRepository:
    """Repository for malaria risk index operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save_risk_assessment(
        self,
        assessment_date: datetime,
        latitude: float,
        longitude: float,
        risk_data: dict,
    ) -> MalariaRiskIndex:
        """Save a malaria risk assessment.

        Args:
            assessment_date: Date of assessment
            latitude: Location latitude
            longitude: Location longitude
            risk_data: Dictionary with risk components

        Returns:
            Created MalariaRiskIndex instance
        """
        risk_index = MalariaRiskIndex(
            assessment_date=assessment_date,
            latitude=latitude,
            longitude=longitude,
            composite_risk_score=risk_data.get("composite_score", 0),
            temperature_risk_component=risk_data.get("temp_risk", 0),
            precipitation_risk_component=risk_data.get("precip_risk", 0),
            humidity_risk_component=risk_data.get("humidity_risk", 0),
            vegetation_risk_component=risk_data.get("vegetation_risk", 0),
            risk_level=self._calculate_risk_level(risk_data.get("composite_score", 0)),
            confidence_score=risk_data.get("confidence", 0.8),
            prediction_date=risk_data.get("prediction_date", assessment_date),
            time_horizon_days=risk_data.get("time_horizon_days", 30),
            model_version="1.0.0",
            model_type=risk_data.get("model_type", "rule-based"),
            data_sources=risk_data.get("data_sources", ["ERA5"]),
        )

        self.session.add(risk_index)
        await self.session.commit()
        await self.session.refresh(risk_index)

        return risk_index

    async def get_latest_assessment(
        self, latitude: float, longitude: float, buffer_degrees: float = 0.25
    ) -> MalariaRiskIndex | None:
        """Get the latest risk assessment for a location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            buffer_degrees: Buffer around location

        Returns:
            Latest MalariaRiskIndex or None
        """
        query = (
            select(MalariaRiskIndex)
            .where(
                and_(
                    MalariaRiskIndex.latitude >= latitude - buffer_degrees,
                    MalariaRiskIndex.latitude <= latitude + buffer_degrees,
                    MalariaRiskIndex.longitude >= longitude - buffer_degrees,
                    MalariaRiskIndex.longitude <= longitude + buffer_degrees,
                )
            )
            .order_by(MalariaRiskIndex.assessment_date.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return cast(MalariaRiskIndex | None, result.scalar_one_or_none()) # type: ignore[redundant-cast]

    async def get_risk_history(
        self,
        latitude: float,
        longitude: float,
        days_back: int = 90,
        buffer_degrees: float = 0.25,
    ) -> list[MalariaRiskIndex]:
        """Get risk assessment history for a location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            days_back: Number of days of history
            buffer_degrees: Buffer around location

        Returns:
            List of risk assessments
        """
        start_date = datetime.utcnow() - timedelta(days=days_back)

        query = (
            select(MalariaRiskIndex)
            .where(
                and_(
                    MalariaRiskIndex.assessment_date >= start_date,
                    MalariaRiskIndex.latitude >= latitude - buffer_degrees,
                    MalariaRiskIndex.latitude <= latitude + buffer_degrees,
                    MalariaRiskIndex.longitude >= longitude - buffer_degrees,
                    MalariaRiskIndex.longitude <= longitude + buffer_degrees,
                )
            )
            .order_by(MalariaRiskIndex.assessment_date)
        )

        result = await self.session.execute(query)
        return cast(list[MalariaRiskIndex], result.scalars().all())

    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level from numeric score.

        Args:
            risk_score: Numeric risk score (0-1)

        Returns:
            Risk level string
        """
        if risk_score < 0.25:
            return "low"
        elif risk_score < 0.5:
            return "medium"
        elif risk_score < 0.75:
            return "high"
        else:
            return "critical"

    async def store_risk_assessment(self, risk_data: dict) -> str:
        """Store a malaria risk assessment.

        Args:
            risk_data: Dictionary with risk assessment data

        Returns:
            Assessment ID
        """
        assessment_date = risk_data.get("assessment_date", datetime.utcnow())

        risk_index = MalariaRiskIndex(
            assessment_date=assessment_date,
            latitude=risk_data.get("latitude"),
            longitude=risk_data.get("longitude"),
            composite_risk_score=risk_data.get("risk_score", 0),
            temperature_risk_component=risk_data.get("temp_risk", 0),
            precipitation_risk_component=risk_data.get("precip_risk", 0),
            humidity_risk_component=risk_data.get("humidity_risk", 0),
            vegetation_risk_component=risk_data.get("vegetation_risk", 0),
            risk_level=risk_data.get("risk_level", "medium"),
            confidence_score=risk_data.get("confidence", 0.8),
            prediction_date=risk_data.get("prediction_date", assessment_date),
            time_horizon_days=risk_data.get("time_horizon_days", 30),
            model_version="1.0.0",
            model_type=risk_data.get("model_type", "rule-based"),
            data_sources=risk_data.get("data_sources", ["ERA5"]),
        )

        self.session.add(risk_index)
        await self.session.commit()
        await self.session.refresh(risk_index)

        return str(risk_index.id)

    async def get_current_risk_levels(
        self, locations: list[tuple[float, float]]
    ) -> list[MalariaRiskIndex]:
        """Get current risk levels for multiple locations.

        Args:
            locations: List of (latitude, longitude) tuples

        Returns:
            List of current risk assessments
        """
        if not locations:
            return []

        # Create OR conditions for all locations
        from sqlalchemy import or_

        location_conditions = []
        for lat, lon in locations:
            location_conditions.append(
                and_(
                    MalariaRiskIndex.latitude == lat, MalariaRiskIndex.longitude == lon
                )
            )

        query = (
            select(MalariaRiskIndex)
            .where(or_(*location_conditions))
            .order_by(MalariaRiskIndex.assessment_date.desc())
        )

        result = await self.session.execute(query)
        return cast(list[MalariaRiskIndex], result.scalars().all())

    async def update_risk_assessment(
        self, assessment_id: str, updated_data: dict
    ) -> int:
        """Update existing risk assessment.

        Args:
            assessment_id: Assessment ID to update
            updated_data: Dictionary with updated data

        Returns:
            Number of rows updated
        """
        from sqlalchemy import update

        stmt = (
            update(MalariaRiskIndex)
            .where(MalariaRiskIndex.id == assessment_id)
            .values(**updated_data)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return cast(int, result.rowcount) # type: ignore[redundant-cast]


class EnvironmentalDataRepository:
    """Repository for environmental data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def store_data(self, data: dict) -> str:
        """Store environmental data.

        Args:
            data: Environmental data dictionary containing MODIS or other environmental data

        Returns:
            Data record ID
        """
        data_type = data.get("type", "modis")

        if data_type == "modis":
            # Store MODIS vegetation data
            modis_record = MODISDataPoint(
                date=data.get("date", datetime.utcnow()),
                latitude=data["latitude"],
                longitude=data["longitude"],
                ndvi=data.get("ndvi"),
                evi=data.get("evi"),
                lst_day=data.get("lst_day"),
                lst_night=data.get("lst_night"),
                pixel_reliability=data.get("quality_flags", 0),
                ingestion_timestamp=datetime.utcnow(),
            )

            self.session.add(modis_record)
            await self.session.commit()
            await self.session.refresh(modis_record)

            logger.info(f"Stored MODIS environmental data record {modis_record.id}")
            return str(modis_record.id)

        elif data_type == "worldpop":
            # Store WorldPop population data
            worldpop_record = WorldPopDataPoint(
                year=data.get("year", datetime.utcnow().year),
                latitude=data["latitude"],
                longitude=data["longitude"],
                country_code=data.get("country_code", "UNK"),
                population_total=data.get("population_count", 0),
                population_density=data.get("population_density", 0),
                urban_rural_classification=data.get("urban_rural", 0.0),
                ingestion_timestamp=datetime.utcnow(),
            )

            self.session.add(worldpop_record)
            await self.session.commit()
            await self.session.refresh(worldpop_record)

            logger.info(
                f"Stored WorldPop environmental data record {worldpop_record.id}"
            )
            return str(worldpop_record.id)

        else:
            raise ValueError(f"Unsupported environmental data type: {data_type}")

    async def get_by_location(
        self,
        latitude: float,
        longitude: float,
        buffer_degrees: float = 0.25,
        data_type: str = "modis",
    ) -> list:
        """Get environmental data by location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            buffer_degrees: Buffer around location in degrees
            data_type: Type of environmental data (modis, worldpop)

        Returns:
            List of environmental data records
        """
        if data_type == "modis":
            query = (
                select(MODISDataPoint)
                .where(
                    and_(
                        MODISDataPoint.latitude >= latitude - buffer_degrees,
                        MODISDataPoint.latitude <= latitude + buffer_degrees,
                        MODISDataPoint.longitude >= longitude - buffer_degrees,
                        MODISDataPoint.longitude <= longitude + buffer_degrees,
                    )
                )
                .order_by(MODISDataPoint.date.desc())
                .limit(100)
            )

        elif data_type == "worldpop":
            query = (
                select(WorldPopDataPoint) # type: ignore[assignment]
                .where(
                    and_(
                        WorldPopDataPoint.latitude >= latitude - buffer_degrees,
                        WorldPopDataPoint.latitude <= latitude + buffer_degrees,
                        WorldPopDataPoint.longitude >= longitude - buffer_degrees,
                        WorldPopDataPoint.longitude <= longitude + buffer_degrees,
                    )
                )
                .order_by(WorldPopDataPoint.year.desc())
                .limit(100)
            )

        else:
            raise ValueError(f"Unsupported environmental data type: {data_type}")

        result = await self.session.execute(query)
        return cast(list, result.scalars().all())


class MalariaIncidenceRepository:
    """Repository for malaria incidence data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def store_incidence(self, data: dict) -> str:
        """Store malaria incidence data using CHIRPSDataPoint as a proxy.

        Args:
            data: Incidence data dictionary

        Returns:
            Incidence record ID
        """
        # Using CHIRPSDataPoint as a proxy for incidence data storage
        # In a real implementation, this would use a dedicated MalariaIncidenceDataPoint model
        incidence_record = CHIRPSDataPoint(
            date=data.get("date", datetime.utcnow()),
            latitude=data["latitude"],
            longitude=data["longitude"],
            precipitation=data.get(
                "incidence_rate", 0.0
            ),  # Using precipitation field for incidence rate
            data_quality_flag=data.get("quality_flags", 0),
            ingestion_timestamp=datetime.utcnow(),
        )

        self.session.add(incidence_record)
        await self.session.commit()
        await self.session.refresh(incidence_record)

        logger.info(f"Stored malaria incidence data record {incidence_record.id}")
        return str(incidence_record.id)

    async def get_by_location(
        self, latitude: float, longitude: float, buffer_degrees: float = 0.25
    ) -> list:
        """Get incidence data by location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            buffer_degrees: Buffer around location in degrees

        Returns:
            List of incidence data records
        """
        # Using CHIRPSDataPoint as a proxy for incidence data retrieval
        query = (
            select(CHIRPSDataPoint)
            .where(
                and_(
                    CHIRPSDataPoint.latitude >= latitude - buffer_degrees,
                    CHIRPSDataPoint.latitude <= latitude + buffer_degrees,
                    CHIRPSDataPoint.longitude >= longitude - buffer_degrees,
                    CHIRPSDataPoint.longitude <= longitude + buffer_degrees,
                )
            )
            .order_by(CHIRPSDataPoint.date.desc())
            .limit(100)
        )

        result = await self.session.execute(query)
        return cast(list, result.scalars().all())


class PredictionRepository:
    """Repository for prediction data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def store_prediction(self, data: dict) -> str:
        """Store prediction data using MalariaRiskIndex.

        Args:
            data: Prediction data dictionary

        Returns:
            Prediction record ID
        """
        # Store predictions as risk assessments in MalariaRiskIndex
        prediction_record = MalariaRiskIndex(
            assessment_date=data.get("prediction_date", datetime.utcnow()),
            latitude=data["latitude"],
            longitude=data["longitude"],
            composite_risk_score=data.get("risk_score", 0.5),
            temperature_risk_component=data.get("temp_component", 0.0),
            precipitation_risk_component=data.get("precip_component", 0.0),
            humidity_risk_component=data.get("humidity_component", 0.0),
            vegetation_risk_component=data.get("vegetation_component", 0.0),
            risk_level=data.get("risk_level", "medium"),
            confidence_score=data.get("confidence", 0.8),
            prediction_date=data.get("prediction_date", datetime.utcnow()),
            time_horizon_days=data.get("time_horizon_days", 30),
            model_version=data.get("model_version", "1.0.0"),
            model_type=data.get("model_type", "prediction"),
            data_sources=data.get("data_sources", ["prediction_model"]),
        )

        self.session.add(prediction_record)
        await self.session.commit()
        await self.session.refresh(prediction_record)

        logger.info(f"Stored prediction data record {prediction_record.id}")
        return str(prediction_record.id)

    async def get_by_location(
        self, latitude: float, longitude: float, buffer_degrees: float = 0.25
    ) -> list:
        """Get predictions by location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            buffer_degrees: Buffer around location in degrees

        Returns:
            List of prediction records
        """
        # Retrieve predictions from MalariaRiskIndex where model_type is prediction
        query = (
            select(MalariaRiskIndex)
            .where(
                and_(
                    MalariaRiskIndex.latitude >= latitude - buffer_degrees,
                    MalariaRiskIndex.latitude <= latitude + buffer_degrees,
                    MalariaRiskIndex.longitude >= longitude - buffer_degrees,
                    MalariaRiskIndex.longitude <= longitude + buffer_degrees,
                    MalariaRiskIndex.model_type == "prediction",
                )
            )
            .order_by(MalariaRiskIndex.prediction_date.desc())
            .limit(100)
        )

        result = await self.session.execute(query)
        return cast(list, result.scalars().all())


class UserRepository:
    """Repository for user data operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create_user(self, user_data: dict) -> str:
        """Create a new user.

        Args:
            user_data: User data dictionary containing username, email, password, etc.

        Returns:
            User ID
        """
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            full_name=user_data.get("full_name"),
            organization=user_data.get("organization"),
            role=user_data.get("role", "user"),
            is_active=user_data.get("is_active", True),
            is_verified=user_data.get("is_verified", False),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"Created user {user.username} with ID {user.id}")
        return str(user.id)

    async def get_by_id(self, user_id: str) -> dict | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User data dictionary or None
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "organization": user.organization,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }

        return None

    async def get_by_username(self, username: str) -> dict | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User data dictionary or None
        """
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "hashed_password": user.hashed_password,
                "full_name": user.full_name,
                "organization": user.organization,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }

        return None

    async def update_user(self, user_id: str, user_data: dict) -> bool:
        """Update user data.

        Args:
            user_id: User ID
            user_data: Dictionary of fields to update

        Returns:
            True if user was updated, False if not found
        """
        from sqlalchemy import update

        stmt = update(User).where(User.id == user_id).values(**user_data)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return cast(int, result.rowcount) > 0 # type: ignore[redundant-cast]

    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID.

        Args:
            user_id: User ID

        Returns:
            True if user was deleted, False if not found
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            await self.session.delete(user)
            await self.session.commit()
            logger.info(f"Deleted user {user.username} with ID {user_id}")
            return True

        return False
