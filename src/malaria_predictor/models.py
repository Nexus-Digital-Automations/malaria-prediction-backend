"""Core data models for malaria prediction system.

This module defines the fundamental data structures used throughout the system
for environmental data, risk assessments, and prediction results. Models are
built using Pydantic for robust validation and serialization.
"""

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskLevel(str, Enum):
    """Malaria outbreak risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnvironmentalFactors(BaseModel):
    """Environmental factors affecting malaria transmission.

    Based on research showing temperature (18-34°C optimal), rainfall (80mm+ monthly),
    humidity (60%+ needed), and vegetation indices as key predictors.
    """

    # Temperature factors (°C)
    mean_temperature: float = Field(
        ge=-10.0, le=50.0, description="Daily mean temperature in Celsius"
    )
    min_temperature: float = Field(
        ge=-20.0, le=45.0, description="Daily minimum temperature in Celsius"
    )
    max_temperature: float = Field(
        ge=-5.0, le=55.0, description="Daily maximum temperature in Celsius"
    )

    # Precipitation (mm)
    monthly_rainfall: float = Field(
        ge=0.0, le=2000.0, description="Monthly rainfall in millimeters"
    )

    # Humidity (%)
    relative_humidity: float = Field(
        ge=0.0, le=100.0, description="Relative humidity percentage"
    )

    # Vegetation indices
    ndvi: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Normalized Difference Vegetation Index",
    )
    evi: float | None = Field(
        default=None, ge=-1.0, le=1.0, description="Enhanced Vegetation Index"
    )

    # Topographical factors
    elevation: float = Field(
        ge=-500.0, le=6000.0, description="Elevation in meters above sea level"
    )
    slope: float | None = Field(
        default=None, ge=0.0, le=90.0, description="Terrain slope in degrees"
    )

    # Population factors
    population_density: float | None = Field(
        default=None, ge=0.0, description="Population density per square kilometer"
    )

    @field_validator("max_temperature")
    @classmethod
    def validate_temperature_range(cls, v: float, info: Any) -> float:
        """Ensure max temperature >= min temperature."""
        if (
            info.data
            and "min_temperature" in info.data
            and v < info.data["min_temperature"]
        ):
            raise ValueError("Max temperature must be >= min temperature")
        return v


class GeographicLocation(BaseModel):
    """Geographic location information."""

    latitude: float = Field(
        ge=-90.0, le=90.0, description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ge=-180.0, le=180.0, description="Longitude in decimal degrees"
    )
    area_name: str = Field(
        min_length=1, max_length=200, description="Human-readable area name"
    )
    country_code: str = Field(
        min_length=2, max_length=3, description="ISO country code"
    )
    admin_level: str | None = Field(
        default=None,
        max_length=100,
        description="Administrative level (district, province, etc.)",
    )


class RiskAssessment(BaseModel):
    """Malaria outbreak risk assessment result."""

    model_config = ConfigDict(protected_namespaces=())

    risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Numerical risk score from 0.0 (no risk) to 1.0 (maximum risk)",
    )
    risk_level: RiskLevel = Field(description="Categorical risk level")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score in the prediction"
    )

    # Contributing factors
    temperature_factor: float = Field(
        ge=0.0, le=1.0, description="Temperature contribution to risk score"
    )
    rainfall_factor: float = Field(
        ge=0.0, le=1.0, description="Rainfall contribution to risk score"
    )
    humidity_factor: float = Field(
        ge=0.0, le=1.0, description="Humidity contribution to risk score"
    )
    vegetation_factor: float = Field(
        ge=0.0, le=1.0, description="Vegetation contribution to risk score"
    )
    elevation_factor: float = Field(
        ge=0.0, le=1.0, description="Elevation contribution to risk score"
    )

    assessment_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this assessment was calculated",
    )
    model_version: str = Field(
        default="1.0.0", description="Version of the risk model used"
    )


class MalariaPrediction(BaseModel):
    """Complete malaria outbreak prediction for a location and time period."""

    location: GeographicLocation
    environmental_data: EnvironmentalFactors
    risk_assessment: RiskAssessment

    prediction_date: date = Field(description="Date this prediction is for")
    time_horizon_days: int = Field(
        ge=1, le=365, description="Number of days ahead this prediction covers"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this prediction was created",
    )
    data_sources: list[str] = Field(
        default_factory=list, description="Environmental data sources used"
    )

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat(), date: lambda v: v.isoformat()}
    )
