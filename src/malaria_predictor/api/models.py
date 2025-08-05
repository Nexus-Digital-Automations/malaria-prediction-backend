"""
Pydantic Models for API Request/Response Validation.

This module defines the data models used for API request and response validation,
ensuring type safety and proper data structure for the malaria prediction service.
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ModelType(str, Enum):
    """Available model types for prediction."""

    LSTM = "lstm"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class PredictionHorizon(int, Enum):
    """Supported prediction horizons in days."""

    SHORT_TERM = 7
    MEDIUM_TERM = 15
    LONG_TERM = 30


class GeographicBounds(BaseModel):
    """Geographic bounding box for spatial queries."""

    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")

    @field_validator("east")
    def east_greater_than_west(cls, v, info):
        """Validate that east is greater than west."""
        if info.data and "west" in info.data and v <= info.data["west"]:
            raise ValueError("East longitude must be greater than west longitude")
        return v

    @field_validator("north")
    def north_greater_than_south(cls, v, info):
        """Validate that north is greater than south."""
        if info.data and "south" in info.data and v <= info.data["south"]:
            raise ValueError("North latitude must be greater than south latitude")
        return v


class LocationPoint(BaseModel):
    """Single geographic point for prediction."""

    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in decimal degrees"
    )
    name: str | None = Field(None, description="Optional location name")


class PredictionRequest(BaseModel):
    """Base prediction request model."""

    target_date: date = Field(..., description="Target date for prediction")
    model_type: ModelType = Field(
        ModelType.ENSEMBLE, description="Model to use for prediction"
    )
    prediction_horizon: PredictionHorizon = Field(
        PredictionHorizon.LONG_TERM, description="Prediction horizon in days"
    )
    include_uncertainty: bool = Field(True, description="Include uncertainty estimates")
    include_features: bool = Field(
        False, description="Include input features in response"
    )

    model_config = {"protected_namespaces": ()}


class SinglePredictionRequest(PredictionRequest):
    """Request for single location prediction."""

    location: LocationPoint = Field(
        ..., description="Geographic location for prediction"
    )


class BatchPredictionRequest(PredictionRequest):
    """Request for batch prediction across multiple locations."""

    locations: list[LocationPoint] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of locations for batch prediction",
    )


class SpatialPredictionRequest(PredictionRequest):
    """Request for spatial grid prediction."""

    bounds: GeographicBounds = Field(
        ..., description="Geographic bounds for prediction"
    )
    resolution: float = Field(
        0.1, ge=0.01, le=1.0, description="Spatial resolution in degrees"
    )


class TimeSeriesPredictionRequest(BaseModel):
    """Request for time series prediction."""

    location: LocationPoint = Field(..., description="Geographic location")
    start_date: date = Field(..., description="Start date for time series")
    end_date: date = Field(..., description="End date for time series")
    model_type: ModelType = Field(ModelType.ENSEMBLE, description="Model to use")
    include_uncertainty: bool = Field(True, description="Include uncertainty estimates")

    model_config = {"protected_namespaces": ()}

    @field_validator("end_date")
    def end_after_start(cls, v, info):
        """Validate that end_date is after start_date."""
        if info.data and "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class RiskLevel(str, Enum):
    """Risk level categories."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PredictionResult(BaseModel):
    """Single prediction result."""

    location: LocationPoint
    target_date: date
    risk_score: float = Field(..., ge=0, le=1, description="Risk score between 0 and 1")
    risk_level: RiskLevel = Field(..., description="Categorical risk level")
    uncertainty: float | None = Field(None, ge=0, description="Prediction uncertainty")
    confidence_interval: list[float] | None = Field(
        None, description="95% confidence interval [lower, upper]"
    )
    model_used: ModelType = Field(..., description="Model used for prediction")
    prediction_horizon: int = Field(..., description="Prediction horizon in days")

    model_config = {"protected_namespaces": ()}


class BatchPredictionResult(BaseModel):
    """Batch prediction results."""

    predictions: list[PredictionResult]
    total_locations: int = Field(..., description="Total number of locations processed")
    successful_predictions: int = Field(
        ..., description="Number of successful predictions"
    )
    failed_predictions: int = Field(..., description="Number of failed predictions")
    processing_time_ms: float = Field(
        ..., description="Total processing time in milliseconds"
    )


class TimeSeriesPoint(BaseModel):
    """Single point in time series prediction."""

    prediction_date: date
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    uncertainty: float | None = Field(None, ge=0)


class TimeSeriesPredictionResult(BaseModel):
    """Time series prediction result."""

    location: LocationPoint
    model_used: ModelType
    time_series: list[TimeSeriesPoint]
    summary_statistics: dict = Field(
        ..., description="Summary statistics for the time series"
    )

    model_config = {"protected_namespaces": ()}


class ModelMetrics(BaseModel):
    """Model performance metrics."""

    model_type: ModelType
    accuracy: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    auc_roc: float = Field(..., ge=0, le=1)
    rmse: float = Field(..., ge=0)
    mae: float = Field(..., ge=0)
    last_updated: datetime

    model_config = {"protected_namespaces": ()}


class HealthStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus
    timestamp: datetime
    version: str
    uptime_seconds: float
    models_loaded: list[ModelType]
    data_sources: dict = Field(..., description="Status of data sources")
    system_metrics: dict = Field(..., description="System resource metrics")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict = Field(..., description="Error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": 400,
                    "message": "Invalid request parameters",
                    "timestamp": 1640995200.0,
                    "path": "/predict/single",
                }
            }
        }
    }


class FeatureImportance(BaseModel):
    """Feature importance for model interpretability."""

    feature_name: str
    importance_score: float = Field(..., ge=0, le=1)
    category: str = Field(
        ..., description="Feature category (climate, vegetation, etc.)"
    )


class ModelExplanation(BaseModel):
    """Model prediction explanation."""

    prediction_id: str
    model_type: ModelType
    feature_importance: list[FeatureImportance]
    attention_weights: dict | None = Field(
        None, description="Attention weights for Transformer"
    )
    temporal_importance: list[float] | None = Field(
        None, description="Temporal importance weights"
    )

    model_config = {"protected_namespaces": ()}


class DataQualityMetrics(BaseModel):
    """Data quality metrics for input features."""

    source: str = Field(..., description="Data source name")
    completeness: float = Field(..., ge=0, le=1, description="Data completeness ratio")
    freshness_hours: float = Field(..., ge=0, description="Hours since last update")
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    issues: list[str] = Field(default_factory=list, description="Quality issues found")


# Database creation models for testing
class Location(BaseModel):
    """Location model for database operations."""

    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in decimal degrees"
    )


class EnvironmentalDataCreate(BaseModel):
    """Model for creating environmental data records."""

    location: Location = Field(..., description="Geographic location")
    timestamp: datetime = Field(..., description="Data timestamp")
    temperature: float | None = Field(None, description="Temperature in Celsius")
    precipitation: float | None = Field(None, description="Precipitation in mm")
    humidity: float | None = Field(None, description="Relative humidity percentage")
    data_source: str = Field("unknown", description="Data source identifier")


class MalariaIncidenceCreate(BaseModel):
    """Model for creating malaria incidence records."""

    location: Location = Field(..., description="Geographic location")
    incidence_date: date = Field(..., description="Incidence date")
    case_count: int = Field(..., ge=0, description="Number of confirmed cases")
    population: int | None = Field(None, ge=0, description="Population at risk")
    data_source: str = Field("unknown", description="Data source identifier")


class PredictionCreate(BaseModel):
    """Model for creating prediction records."""

    location: Location = Field(..., description="Geographic location")
    prediction_date: datetime = Field(..., description="When prediction was made")
    target_date: date = Field(..., description="Target date for prediction")
    risk_score: float = Field(..., ge=0, le=1, description="Predicted risk score")
    model_type: ModelType = Field(..., description="Model used for prediction")
    confidence: float | None = Field(
        None, ge=0, le=1, description="Prediction confidence"
    )


# Database model aliases for compatibility
class EnvironmentalData(BaseModel):
    """Environmental data model for database queries."""

    id: int | None = None
    timestamp: datetime
    latitude: float
    longitude: float
    temperature: float | None = None
    precipitation: float | None = None
    humidity: float | None = None
    data_source: str = "unknown"


class MalariaIncidenceData(BaseModel):
    """Malaria incidence data model for database queries."""

    id: int | None = None
    incidence_date: date
    latitude: float
    longitude: float
    case_count: int
    population: int | None = None
    data_source: str = "unknown"


class PredictionData(BaseModel):
    """Prediction data model for database queries."""

    id: int | None = None
    prediction_date: datetime
    target_date: date
    latitude: float
    longitude: float
    risk_score: float
    model_type: str
    confidence: float | None = None
