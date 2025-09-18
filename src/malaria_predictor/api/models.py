"""
API Models for Analytics Dashboard.

This module defines Pydantic models for analytics API requests and responses,
providing comprehensive data structures for visualization and reporting.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Enumeration of available ML model types."""

    LSTM = "lstm"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class AnalyticsRequest(BaseModel):
    """Base analytics request model."""

    start_date: str | None = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: str | None = Field(None, description="End date in YYYY-MM-DD format")
    location_lat: float | None = Field(None, ge=-90, le=90, description="Latitude")
    location_lon: float | None = Field(None, ge=-180, le=180, description="Longitude")
    radius_km: float | None = Field(50, gt=0, le=1000, description="Radius in kilometers")


class PredictionAccuracyRequest(AnalyticsRequest):
    """Request model for prediction accuracy analytics."""

    model_type: str | None = Field(None, description="Model type filter")
    region: str | None = Field(None, description="Geographic region filter")
    confidence_threshold: float | None = Field(0.7, ge=0, le=1, description="Confidence threshold")


class EnvironmentalTrendsRequest(AnalyticsRequest):
    """Request model for environmental trends analysis."""

    days_back: int = Field(365, gt=0, le=3650, description="Number of days to analyze")
    data_sources: str | None = Field("era5,chirps,modis", description="Comma-separated data sources")
    aggregation: str = Field("daily", description="Aggregation level")
    include_anomalies: bool = Field(True, description="Include anomaly detection")


class OutbreakPatternsRequest(AnalyticsRequest):
    """Request model for outbreak pattern analysis."""

    region: str | None = Field(None, description="Geographic region")
    time_scale: str = Field("monthly", description="Time scale for analysis")
    risk_threshold: float = Field(0.7, ge=0, le=1, description="Risk threshold for outbreak classification")
    years_back: int = Field(5, gt=0, le=20, description="Number of years to analyze")
    include_seasonality: bool = Field(True, description="Include seasonal analysis")


class DataExplorationRequest(AnalyticsRequest):
    """Request model for interactive data exploration."""

    data_type: str = Field(..., description="Data type to explore")
    aggregation_method: str = Field("mean", description="Aggregation method")
    group_by: str = Field("month", description="Grouping method")
    limit: int = Field(1000, gt=0, le=10000, description="Maximum records to return")
    include_metadata: bool = Field(True, description="Include data quality metadata")


class CustomReportRequest(BaseModel):
    """Request model for custom report generation."""

    report_type: str = Field("summary", description="Type of report to generate")
    data_sources: list[str] = Field(default_factory=list, description="Data sources to include")
    time_range: dict[str, Any] = Field(default_factory=dict, description="Time range configuration")
    geographic_scope: dict[str, Any] = Field(default_factory=dict, description="Geographic scope")
    visualizations: list[dict[str, Any]] = Field(default_factory=list, description="Visualization configurations")
    export_format: str = Field("json", description="Export format")
    include_raw_data: bool = Field(False, description="Include raw data in report")


# Response Models

class ChartDataPoint(BaseModel):
    """Single chart data point."""

    x: str | float | int = Field(..., description="X-axis value")
    y: str | float | int = Field(..., description="Y-axis value")
    category: str | None = Field(None, description="Category for grouping")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ChartSeries(BaseModel):
    """Chart data series."""

    name: str = Field(..., description="Series name")
    data: list[ChartDataPoint] = Field(..., description="Data points")
    color: str | None = Field(None, description="Series color")
    chart_type: str | None = Field(None, description="Chart type for this series")


class VisualizationConfig(BaseModel):
    """Visualization configuration for frontend rendering."""

    chart_type: str = Field(..., description="Type of chart")
    title: str = Field(..., description="Chart title")
    x_axis_label: str | None = Field(None, description="X-axis label")
    y_axis_label: str | None = Field(None, description="Y-axis label")
    color_scheme: str | None = Field("default", description="Color scheme")
    interactive: bool = Field(True, description="Enable interactivity")
    show_legend: bool = Field(True, description="Show legend")
    animation_enabled: bool = Field(True, description="Enable animations")


class StatisticalSummary(BaseModel):
    """Statistical summary for a dataset."""

    count: int = Field(..., description="Number of data points")
    mean: float | None = Field(None, description="Mean value")
    median: float | None = Field(None, description="Median value")
    std_dev: float | None = Field(None, description="Standard deviation")
    min_value: float | None = Field(None, description="Minimum value")
    max_value: float | None = Field(None, description="Maximum value")
    percentiles: dict[str, float] | None = Field(None, description="Percentile values")


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics."""

    model_name: str = Field(..., description="Model name")
    accuracy: float = Field(..., ge=0, le=1, description="Model accuracy")
    precision: float = Field(..., ge=0, le=1, description="Model precision")
    recall: float = Field(..., ge=0, le=1, description="Model recall")
    f1_score: float = Field(..., ge=0, le=1, description="F1 score")
    confidence_score: float = Field(..., ge=0, le=1, description="Average confidence")
    total_predictions: int = Field(..., ge=0, description="Total predictions made")
    high_confidence_rate: float = Field(..., ge=0, le=1, description="Rate of high confidence predictions")


class GeographicDistribution(BaseModel):
    """Geographic distribution data."""

    location: str = Field(..., description="Location name or coordinates")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    value: float = Field(..., description="Metric value for this location")
    category: str | None = Field(None, description="Category classification")
    population: int | None = Field(None, description="Population in this area")


class TemporalTrend(BaseModel):
    """Temporal trend data point."""

    timestamp: datetime = Field(..., description="Timestamp for this data point")
    value: float = Field(..., description="Metric value")
    trend_direction: str | None = Field(None, description="Trend direction (up/down/stable)")
    anomaly_score: float | None = Field(None, description="Anomaly detection score")
    confidence_interval: dict[str, float] | None = Field(None, description="Confidence interval")


class SeasonalPattern(BaseModel):
    """Seasonal pattern analysis."""

    season: str = Field(..., description="Season name")
    average_value: float = Field(..., description="Average value for this season")
    peak_month: int = Field(..., ge=1, le=12, description="Peak month")
    peak_value: float = Field(..., description="Peak value")
    seasonal_index: float = Field(..., description="Seasonal index (relative to annual average)")


class AnalyticsResponse(BaseModel):
    """Base analytics response model."""

    success: bool = Field(True, description="Response success status")
    data: dict[str, Any] = Field(..., description="Response data")
    metadata: dict[str, Any] = Field(..., description="Response metadata")
    generated_at: datetime = Field(default_factory=datetime.now, description="Response generation time")


class PredictionAccuracyResponse(AnalyticsResponse):
    """Response model for prediction accuracy analytics."""

    model_performance: list[ModelPerformanceMetrics] = Field(..., description="Model performance metrics")
    temporal_trends: list[TemporalTrend] = Field(..., description="Accuracy trends over time")
    confidence_distribution: dict[str, int] = Field(..., description="Confidence score distribution")
    visualization_config: VisualizationConfig = Field(..., description="Suggested visualization configuration")


class EnvironmentalTrendsResponse(AnalyticsResponse):
    """Response model for environmental trends analysis."""

    temperature_trends: list[TemporalTrend] = Field(..., description="Temperature trend data")
    precipitation_trends: list[TemporalTrend] = Field(..., description="Precipitation trend data")
    vegetation_trends: list[TemporalTrend] = Field(..., description="Vegetation index trends")
    correlation_matrix: dict[str, dict[str, float]] = Field(..., description="Variable correlation matrix")
    seasonal_patterns: list[SeasonalPattern] = Field(..., description="Seasonal pattern analysis")
    anomaly_detection: dict[str, Any] = Field(..., description="Anomaly detection results")


class OutbreakPatternsResponse(AnalyticsResponse):
    """Response model for outbreak pattern analysis."""

    outbreak_frequency: dict[str, int] = Field(..., description="Outbreak frequency by time period")
    geographic_distribution: list[GeographicDistribution] = Field(..., description="Geographic outbreak distribution")
    seasonal_patterns: list[SeasonalPattern] = Field(..., description="Seasonal outbreak patterns")
    risk_escalation_events: list[dict[str, Any]] = Field(..., description="Risk escalation events")
    clustering_analysis: dict[str, Any] = Field(..., description="Spatial-temporal clustering results")


class DataExplorationResponse(AnalyticsResponse):
    """Response model for data exploration."""

    dataset_summary: StatisticalSummary = Field(..., description="Dataset statistical summary")
    data_points: list[dict[str, Any]] = Field(..., description="Raw or aggregated data points")
    data_quality_metrics: dict[str, Any] = Field(..., description="Data quality assessment")
    suggested_visualizations: list[VisualizationConfig] = Field(..., description="Suggested visualizations")
    export_options: dict[str, str] = Field(..., description="Available export formats")


class CustomReportResponse(AnalyticsResponse):
    """Response model for custom reports."""

    report_id: str = Field(..., description="Unique report identifier")
    report_sections: list[dict[str, Any]] = Field(..., description="Report sections")
    visualizations: list[dict[str, Any]] = Field(..., description="Generated visualizations")
    summary_statistics: dict[str, Any] = Field(..., description="Summary statistics")
    export_links: dict[str, str] = Field(..., description="Export download links")
    report_metadata: dict[str, Any] = Field(..., description="Report generation metadata")


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""

    widget_id: str = Field(..., description="Unique widget identifier")
    widget_type: str = Field(..., description="Widget type")
    title: str = Field(..., description="Widget title")
    position: dict[str, int] = Field(..., description="Widget position and size")
    data_endpoint: str = Field(..., description="API endpoint for widget data")
    refresh_interval: int | None = Field(None, description="Refresh interval in seconds")
    chart_config: dict[str, Any] | None = Field(None, description="Chart configuration")
    alert_thresholds: dict[str, float] | None = Field(None, description="Alert thresholds")


class DashboardLayout(BaseModel):
    """Dashboard layout configuration."""

    dashboard_id: str = Field(..., description="Dashboard identifier")
    dashboard_type: str = Field(..., description="Dashboard type")
    layout_config: dict[str, Any] = Field(..., description="Layout configuration")
    widgets: list[DashboardWidget] = Field(..., description="Dashboard widgets")
    theme_config: dict[str, Any] = Field(..., description="Theme configuration")
    auto_refresh: bool = Field(True, description="Auto-refresh enabled")
    refresh_interval: int = Field(300, description="Global refresh interval")


class AlertConfiguration(BaseModel):
    """Alert configuration for analytics monitoring."""

    alert_id: str = Field(..., description="Alert identifier")
    alert_name: str = Field(..., description="Human-readable alert name")
    metric_name: str = Field(..., description="Metric being monitored")
    threshold_value: float = Field(..., description="Alert threshold")
    threshold_type: str = Field(..., description="Threshold type (above/below/equal)")
    severity: str = Field(..., description="Alert severity level")
    notification_channels: list[str] = Field(..., description="Notification channels")
    cooldown_period: int = Field(300, description="Cooldown period in seconds")


class ExportConfiguration(BaseModel):
    """Data export configuration."""

    export_format: str = Field(..., description="Export format")
    include_metadata: bool = Field(True, description="Include metadata in export")
    compression: str | None = Field(None, description="Compression format")
    date_range: dict[str, str] | None = Field(None, description="Date range for export")
    filters: dict[str, Any] | None = Field(None, description="Data filters")
    aggregation_level: str | None = Field(None, description="Data aggregation level")


class AnalyticsHealthCheck(BaseModel):
    """Analytics system health check response."""

    system_status: str = Field(..., description="Overall system status")
    data_pipeline_status: dict[str, str] = Field(..., description="Data pipeline statuses")
    model_status: dict[str, str] = Field(..., description="ML model statuses")
    cache_status: str = Field(..., description="Cache system status")
    database_status: str = Field(..., description="Database connectivity status")
    last_data_update: datetime = Field(..., description="Last data update timestamp")
    alerts_active: int = Field(..., description="Number of active alerts")
    performance_metrics: dict[str, float] = Field(..., description="Performance metrics")


class HealthStatus(BaseModel):
    """Health status enumeration."""

    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    checks: dict[str, str] = Field(..., description="Individual health check results")
    timestamp: datetime = Field(..., description="Health check timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")
    checks: dict[str, HealthStatus] = Field(..., description="Detailed health checks")
    environment: str = Field(..., description="Environment name")
    timestamp: datetime = Field(..., description="Response timestamp")


class LocationPoint(BaseModel):
    """Geographic location point."""

    latitude: float = Field(..., description="Latitude coordinate", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180, le=180)
    name: str | None = Field(None, description="Location name")


class RiskLevel(BaseModel):
    """Risk level classification."""

    level: str = Field(..., description="Risk level (low, medium, high, critical)")
    value: float = Field(..., description="Numeric risk value", ge=0, le=1)
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    factors: dict[str, float] | None = Field(None, description="Contributing risk factors")


# Prediction Request/Response Models
class SinglePredictionRequest(BaseModel):
    """Single location prediction request."""

    location: LocationPoint = Field(..., description="Geographic location")
    time_horizon_days: int = Field(default=30, description="Prediction time horizon in days", ge=1, le=365)
    include_factors: bool = Field(default=True, description="Include risk factor breakdown")


class BatchPredictionRequest(BaseModel):
    """Batch prediction request for multiple locations."""

    locations: list[LocationPoint] = Field(..., description="List of geographic locations", min_items=1, max_items=100)
    time_horizon_days: int = Field(default=30, description="Prediction time horizon in days", ge=1, le=365)
    include_factors: bool = Field(default=True, description="Include risk factor breakdown")


class SpatialPredictionRequest(BaseModel):
    """Spatial prediction request for area coverage."""

    bounds: dict[str, float] = Field(..., description="Geographic bounds (north, south, east, west)")
    resolution: float = Field(default=0.1, description="Grid resolution in degrees", gt=0, le=1)
    time_horizon_days: int = Field(default=30, description="Prediction time horizon in days", ge=1, le=365)


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    value: float = Field(..., description="Risk value", ge=0, le=1)
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)


class TimeSeriesPredictionRequest(BaseModel):
    """Time series prediction request."""

    location: LocationPoint = Field(..., description="Geographic location")
    start_date: datetime = Field(..., description="Start date for time series")
    end_date: datetime = Field(..., description="End date for time series")
    interval_days: int = Field(default=7, description="Interval between predictions in days", ge=1, le=30)


class PredictionResult(BaseModel):
    """Single prediction result."""

    location: LocationPoint = Field(..., description="Prediction location")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    prediction_date: datetime = Field(..., description="Prediction timestamp")
    time_horizon_days: int = Field(..., description="Prediction time horizon")
    model_version: str = Field(..., description="ML model version used")
    factors: dict[str, float] | None = Field(None, description="Contributing factors")


class BatchPredictionResult(BaseModel):
    """Batch prediction result."""

    predictions: list[PredictionResult] = Field(..., description="Individual prediction results")
    request_id: str = Field(..., description="Request identifier")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_version: str = Field(..., description="ML model version used")


class TimeSeriesPredictionResult(BaseModel):
    """Time series prediction result."""

    location: LocationPoint = Field(..., description="Prediction location")
    time_series: list[TimeSeriesPoint] = Field(..., description="Time series predictions")
    request_id: str = Field(..., description="Request identifier")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_version: str = Field(..., description="ML model version used")
    start_date: datetime = Field(..., description="Time series start date")
    end_date: datetime = Field(..., description="Time series end date")
