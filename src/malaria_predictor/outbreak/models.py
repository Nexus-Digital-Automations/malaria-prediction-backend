"""
Outbreak Pattern Recognition Data Models

Comprehensive data models for representing outbreak events, epidemiological patterns,
case clusters, and surveillance metrics. Designed for real-time monitoring and
analysis of malaria transmission patterns.

Author: AI Agent - Outbreak Pattern Recognition Specialist
"""

from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from geojson_pydantic import Point, Polygon
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


class OutbreakSeverity(str, Enum):
    """Classification of outbreak severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class OutbreakStatus(str, Enum):
    """Current status of outbreak event."""
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    ONGOING = "ongoing"
    CONTAINED = "contained"
    RESOLVED = "resolved"


class TransmissionType(str, Enum):
    """Type of malaria transmission pattern."""
    ENDEMIC = "endemic"
    EPIDEMIC = "epidemic"
    SEASONAL = "seasonal"
    SPORADIC = "sporadic"
    IMPORTED = "imported"


class ClusterType(str, Enum):
    """Type of case clustering pattern."""
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    SPATIOTEMPORAL = "spatiotemporal"
    HOUSEHOLD = "household"
    WORKPLACE = "workplace"
    SCHOOL = "school"


class OutbreakEvent(BaseModel):
    """
    Represents a malaria outbreak event with timeline and location data.

    Core entity for tracking outbreak occurrences, providing comprehensive
    information about outbreak characteristics, location, timeline, and impact.
    """

    # Identification
    outbreak_id: str = Field(..., description="Unique outbreak identifier")
    event_name: str = Field(..., description="Human-readable outbreak name")

    # Geographic Information
    location: Point = Field(..., description="Primary outbreak location (GeoJSON Point)")
    affected_areas: list[Polygon] = Field(
        default_factory=list,
        description="Geographic areas affected by outbreak"
    )
    administrative_units: list[str] = Field(
        default_factory=list,
        description="Administrative units affected (districts, constituencies)"
    )

    # Temporal Information
    detection_date: datetime = Field(..., description="Date outbreak was first detected")
    onset_date: datetime | None = Field(None, description="Estimated outbreak onset date")
    peak_date: datetime | None = Field(None, description="Date of peak incidence")
    end_date: datetime | None = Field(None, description="Date outbreak ended")

    # Classification
    severity: OutbreakSeverity = Field(..., description="Outbreak severity classification")
    status: OutbreakStatus = Field(..., description="Current outbreak status")
    transmission_type: TransmissionType = Field(..., description="Type of transmission pattern")

    # Case Information
    total_cases: int = Field(0, ge=0, description="Total confirmed cases")
    suspected_cases: int = Field(0, ge=0, description="Total suspected cases")
    deaths: int = Field(0, ge=0, description="Total deaths attributed to outbreak")
    case_fatality_rate: float | None = Field(
        None, ge=0, le=1,
        description="Case fatality rate (0-1)"
    )

    # Population Impact
    population_at_risk: int = Field(0, ge=0, description="Population in affected areas")
    attack_rate: float | None = Field(
        None, ge=0, le=1,
        description="Attack rate in affected population"
    )

    # Source and Attribution
    source_organization: str = Field(..., description="Organization reporting outbreak")
    data_quality_score: float = Field(
        1.0, ge=0, le=1,
        description="Data quality assessment score"
    )
    confidence_level: float = Field(
        1.0, ge=0, le=1,
        description="Confidence in outbreak classification"
    )

    # Response Information
    response_measures: list[str] = Field(
        default_factory=list,
        description="Control measures implemented"
    )
    resources_deployed: dict[str, Any] = Field(
        default_factory=dict,
        description="Resources allocated for response"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User/system that created record")

    @validator('case_fatality_rate')
    def validate_cfr(cls, v: float | None, values: dict[str, Any]) -> float | None:
        """Validate case fatality rate calculation."""
        if v is not None and 'total_cases' in values:
            if values['total_cases'] == 0 and v > 0:
                raise ValueError("Case fatality rate cannot be > 0 with 0 total cases")
        return v

    @validator('attack_rate')
    def validate_attack_rate(cls, v: float | None, values: dict[str, Any]) -> float | None:
        """Validate attack rate calculation."""
        if v is not None and 'population_at_risk' in values:
            if values['population_at_risk'] == 0 and v > 0:
                raise ValueError("Attack rate cannot be > 0 with 0 population at risk")
        return v

    def duration_days(self) -> int | None:
        """Calculate outbreak duration in days."""
        if self.onset_date and self.end_date:
            return (self.end_date - self.onset_date).days
        return None

    def is_active(self) -> bool:
        """Check if outbreak is currently active."""
        return self.status in [OutbreakStatus.SUSPECTED, OutbreakStatus.CONFIRMED, OutbreakStatus.ONGOING]

    def severity_score(self) -> float:
        """Calculate numerical severity score (0-1)."""
        severity_mapping = {
            OutbreakSeverity.LOW: 0.2,
            OutbreakSeverity.MODERATE: 0.4,
            OutbreakSeverity.HIGH: 0.6,
            OutbreakSeverity.CRITICAL: 0.8,
            OutbreakSeverity.EMERGENCY: 1.0
        }
        return severity_mapping.get(self.severity, 0.0)


class EpidemiologicalPattern(BaseModel):
    """
    Represents epidemiological patterns for trend analysis.

    Captures temporal and spatial patterns in malaria transmission,
    including seasonal trends, cyclical patterns, and anomalies.
    """

    # Identification
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_name: str = Field(..., description="Descriptive pattern name")

    # Geographic Scope
    geographic_scope: Point | Polygon = Field(
        ..., description="Geographic area covered by pattern"
    )
    administrative_level: str = Field(..., description="Administrative level (national, regional, district)")

    # Temporal Characteristics
    observation_period: dict[str, datetime] = Field(
        ..., description="Start and end dates of observation period"
    )
    pattern_frequency: str = Field(..., description="Pattern frequency (seasonal, annual, cyclical)")
    peak_months: list[int] = Field(
        default_factory=list,
        description="Months with peak transmission (1-12)"
    )
    trough_months: list[int] = Field(
        default_factory=list,
        description="Months with lowest transmission (1-12)"
    )

    # Pattern Metrics
    seasonal_amplitude: float = Field(0.0, ge=0, description="Seasonal variation amplitude")
    trend_direction: str = Field(..., description="Overall trend (increasing, decreasing, stable)")
    trend_strength: float = Field(0.0, ge=0, le=1, description="Strength of trend (0-1)")
    cyclical_period: int | None = Field(None, description="Cyclical period in months")

    # Statistical Measures
    mean_incidence: float = Field(0.0, ge=0, description="Mean incidence rate")
    variance: float = Field(0.0, ge=0, description="Variance in incidence")
    coefficient_variation: float = Field(0.0, ge=0, description="Coefficient of variation")
    autocorrelation: float = Field(0.0, ge=-1, le=1, description="Temporal autocorrelation")

    # Environmental Correlations
    climate_correlations: dict[str, float] = Field(
        default_factory=dict,
        description="Correlations with climate variables"
    )
    environmental_drivers: list[str] = Field(
        default_factory=list,
        description="Key environmental drivers identified"
    )

    # Anomaly Detection
    anomaly_threshold: float = Field(0.95, ge=0, le=1, description="Anomaly detection threshold")
    recent_anomalies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent anomalous events detected"
    )

    # Model Performance
    model_type: str = Field(..., description="Pattern analysis model used")
    model_accuracy: float = Field(0.0, ge=0, le=1, description="Model accuracy score")
    confidence_intervals: dict[str, list[float]] = Field(
        default_factory=dict,
        description="Confidence intervals for predictions"
    )

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_sources: list[str] = Field(default_factory=list, description="Data sources used")
    analysis_method: str = Field(..., description="Analysis methodology")

    def is_seasonal(self) -> bool:
        """Check if pattern shows seasonal characteristics."""
        return len(self.peak_months) > 0 and self.seasonal_amplitude > 0.1

    def predict_next_peak(self) -> datetime | None:
        """Predict next peak based on pattern."""
        if not self.is_seasonal() or not self.peak_months:
            return None

        # Simple prediction based on historical peak months
        current_date = datetime.utcnow()
        next_peak_month = min([m for m in self.peak_months if m > current_date.month] or [self.peak_months[0]])

        if next_peak_month <= current_date.month:
            # Next year
            return datetime(current_date.year + 1, next_peak_month, 15)
        else:
            # This year
            return datetime(current_date.year, next_peak_month, 15)


class CaseCluster(BaseModel):
    """
    Represents case clustering for geographic analysis.

    Identifies and characterizes spatial, temporal, or spatiotemporal
    clusters of malaria cases for outbreak investigation.
    """

    # Identification
    cluster_id: str = Field(..., description="Unique cluster identifier")
    cluster_name: str = Field(..., description="Descriptive cluster name")

    # Clustering Characteristics
    cluster_type: ClusterType = Field(..., description="Type of clustering")
    detection_method: str = Field(..., description="Method used to detect cluster")
    statistical_significance: float = Field(0.0, ge=0, le=1, description="Statistical significance (p-value)")

    # Geographic Information
    centroid: Point = Field(..., description="Geographic centroid of cluster")
    boundary: Polygon = Field(..., description="Cluster boundary polygon")
    radius_km: float = Field(0.0, ge=0, description="Cluster radius in kilometers")

    # Temporal Information
    start_date: datetime = Field(..., description="Cluster start date")
    end_date: datetime | None = Field(None, description="Cluster end date")
    duration_days: int | None = Field(None, description="Cluster duration in days")

    # Case Information
    case_count: int = Field(0, ge=0, description="Number of cases in cluster")
    expected_cases: float = Field(0.0, ge=0, description="Expected number of cases")
    relative_risk: float = Field(1.0, ge=0, description="Relative risk compared to background")

    # Population Context
    population_density: float = Field(0.0, ge=0, description="Population density per km²")
    total_population: int = Field(0, ge=0, description="Total population in cluster area")
    demographic_profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Demographic characteristics"
    )

    # Risk Factors
    environmental_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Environmental risk factors"
    )
    socioeconomic_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Socioeconomic risk factors"
    )
    vector_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Vector-related factors"
    )

    # Investigation Status
    investigation_status: str = Field("pending", description="Investigation status")
    investigation_findings: list[str] = Field(
        default_factory=list,
        description="Key investigation findings"
    )
    control_measures: list[str] = Field(
        default_factory=list,
        description="Control measures implemented"
    )

    # Quality Metrics
    data_completeness: float = Field(1.0, ge=0, le=1, description="Data completeness score")
    spatial_accuracy: float = Field(1.0, ge=0, le=1, description="Spatial data accuracy")

    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Detection system/user")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if cluster is currently active."""
        if self.end_date:
            return datetime.utcnow() <= self.end_date
        return True

    def cluster_intensity(self) -> float:
        """Calculate cluster intensity score."""
        if self.expected_cases > 0:
            return self.case_count / self.expected_cases
        return 0.0

    def urgency_score(self) -> float:
        """Calculate urgency score for response prioritization."""
        # Combine relative risk, case count, and statistical significance
        base_score = min(self.relative_risk / 5.0, 1.0)  # Normalize RR
        case_weight = min(self.case_count / 100.0, 1.0)  # Normalize case count
        significance_weight = 1.0 - self.statistical_significance

        return (base_score * 0.4 + case_weight * 0.3 + significance_weight * 0.3)


class OutbreakMetrics(BaseModel):
    """
    Outbreak metrics with severity indicators.

    Comprehensive metrics for evaluating outbreak severity, impact,
    and response effectiveness.
    """

    # Identification
    metrics_id: str = Field(..., description="Unique metrics identifier")
    outbreak_id: str = Field(..., description="Associated outbreak identifier")
    calculation_date: datetime = Field(default_factory=datetime.utcnow)

    # Epidemiological Metrics
    attack_rate: float = Field(0.0, ge=0, le=1, description="Attack rate (cases/population)")
    case_fatality_rate: float = Field(0.0, ge=0, le=1, description="Case fatality rate")
    incidence_rate: float = Field(0.0, ge=0, description="Incidence rate per 100,000")
    doubling_time: float | None = Field(None, description="Case doubling time in days")
    reproduction_number: float | None = Field(None, description="Effective reproduction number")

    # Severity Indicators
    severity_index: float = Field(0.0, ge=0, le=1, description="Composite severity index")
    impact_score: float = Field(0.0, ge=0, le=1, description="Population impact score")
    urgency_level: int = Field(1, ge=1, le=5, description="Response urgency level (1-5)")

    # Geographic Spread
    spatial_extent_km2: float = Field(0.0, ge=0, description="Geographic extent in km²")
    affected_communities: int = Field(0, ge=0, description="Number of affected communities")
    cross_border_risk: float = Field(0.0, ge=0, le=1, description="Cross-border spread risk")

    # Temporal Dynamics
    growth_rate: float = Field(0.0, description="Case growth rate (daily %)")
    acceleration: float = Field(0.0, description="Growth acceleration (change in growth rate)")
    epidemic_phase: str = Field("unknown", description="Current epidemic phase")

    # Healthcare Impact
    healthcare_utilization: float = Field(0.0, ge=0, description="Healthcare system utilization")
    bed_occupancy_rate: float = Field(0.0, ge=0, le=1, description="Hospital bed occupancy")
    resource_strain_index: float = Field(0.0, ge=0, le=1, description="Resource strain indicator")

    # Economic Impact
    estimated_cost: float | None = Field(None, description="Estimated economic cost (USD)")
    productivity_loss: float | None = Field(None, description="Productivity loss estimate")
    response_cost: float | None = Field(None, description="Response cost estimate")

    # Response Effectiveness
    response_time_hours: float | None = Field(None, description="Time to response in hours")
    intervention_coverage: float = Field(0.0, ge=0, le=1, description="Intervention coverage rate")
    control_effectiveness: float = Field(0.0, ge=0, le=1, description="Control measure effectiveness")

    # Confidence and Quality
    confidence_score: float = Field(1.0, ge=0, le=1, description="Overall confidence in metrics")
    data_quality: float = Field(1.0, ge=0, le=1, description="Data quality assessment")
    uncertainty_range: dict[str, list[float]] = Field(
        default_factory=dict,
        description="Uncertainty ranges for key metrics"
    )

    # Comparative Context
    historical_percentile: float | None = Field(
        None, ge=0, le=1,
        description="Percentile compared to historical outbreaks"
    )
    regional_comparison: float | None = Field(
        None, description="Comparison to regional average"
    )

    def calculate_severity_index(self) -> float:
        """Calculate composite severity index."""
        # Weighted combination of key indicators
        weights = {
            'attack_rate': 0.25,
            'case_fatality_rate': 0.20,
            'spatial_extent': 0.15,
            'growth_rate': 0.15,
            'healthcare_impact': 0.15,
            'population_impact': 0.10
        }

        # Normalize components (0-1 scale)
        components = {
            'attack_rate': min(self.attack_rate * 10, 1.0),  # Assume 10% is max
            'case_fatality_rate': self.case_fatality_rate,
            'spatial_extent': min(self.spatial_extent_km2 / 10000, 1.0),  # 10,000 km² as reference
            'growth_rate': min(abs(self.growth_rate) / 20, 1.0),  # 20% daily growth as reference
            'healthcare_impact': self.healthcare_utilization,
            'population_impact': self.impact_score
        }

        # Calculate weighted average
        severity = sum(components[k] * weights[k] for k in weights)
        return min(severity, 1.0)

    def risk_category(self) -> str:
        """Determine risk category based on severity index."""
        severity = self.calculate_severity_index()
        if severity >= 0.8:
            return "Critical"
        elif severity >= 0.6:
            return "High"
        elif severity >= 0.4:
            return "Moderate"
        elif severity >= 0.2:
            return "Low"
        else:
            return "Minimal"


class TransmissionPattern(BaseModel):
    """
    Transmission pattern analysis for spread analysis.

    Analyzes patterns of malaria transmission including routes,
    drivers, and network characteristics.
    """

    # Identification
    pattern_id: str = Field(..., description="Unique pattern identifier")
    analysis_period: dict[str, datetime] = Field(
        ..., description="Analysis time period"
    )
    geographic_scope: Polygon = Field(..., description="Geographic analysis area")

    # Transmission Characteristics
    transmission_mode: TransmissionType = Field(..., description="Primary transmission mode")
    transmission_intensity: float = Field(0.0, ge=0, description="Transmission intensity measure")
    seasonality_index: float = Field(0.0, ge=0, le=1, description="Seasonality strength")

    # Network Analysis
    transmission_networks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Identified transmission networks"
    )
    connectivity_index: float = Field(0.0, ge=0, le=1, description="Network connectivity")
    centrality_measures: dict[str, float] = Field(
        default_factory=dict,
        description="Network centrality measures"
    )

    # Spatial Patterns
    spatial_clustering: float = Field(0.0, ge=0, description="Spatial clustering coefficient")
    hotspot_locations: list[Point] = Field(
        default_factory=list,
        description="Identified transmission hotspots"
    )
    spread_vectors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Transmission spread vectors"
    )

    # Risk Factors
    environmental_drivers: dict[str, float] = Field(
        default_factory=dict,
        description="Environmental transmission drivers"
    )
    socioeconomic_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Socioeconomic factors affecting transmission"
    )
    vector_characteristics: dict[str, Any] = Field(
        default_factory=dict,
        description="Vector population characteristics"
    )

    # Temporal Dynamics
    generation_time: float | None = Field(None, description="Generation time in days")
    serial_interval: float | None = Field(None, description="Serial interval in days")
    incubation_period: float | None = Field(None, description="Incubation period in days")

    # Model Results
    model_type: str = Field(..., description="Transmission model used")
    model_parameters: dict[str, float] = Field(
        default_factory=dict,
        description="Model parameter estimates"
    )
    goodness_of_fit: float = Field(0.0, ge=0, le=1, description="Model goodness of fit")

    # Predictions
    future_risk_areas: list[Polygon] = Field(
        default_factory=list,
        description="Predicted future risk areas"
    )
    transmission_forecast: dict[str, Any] = Field(
        default_factory=dict,
        description="Transmission intensity forecasts"
    )
    intervention_scenarios: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intervention impact scenarios"
    )

    # Quality Metrics
    data_coverage: float = Field(1.0, ge=0, le=1, description="Spatial data coverage")
    temporal_resolution: int = Field(1, ge=1, description="Temporal resolution in days")
    uncertainty_level: float = Field(0.0, ge=0, le=1, description="Overall uncertainty")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_method: str = Field(..., description="Analysis methodology")
    data_sources: list[str] = Field(default_factory=list)

    def transmission_risk_score(self) -> float:
        """Calculate overall transmission risk score."""
        # Combine intensity, connectivity, and environmental factors
        base_score = min(self.transmission_intensity / 10.0, 1.0)  # Normalize
        network_factor = self.connectivity_index
        environmental_factor = sum(self.environmental_drivers.values()) / len(self.environmental_drivers) if self.environmental_drivers else 0

        return (base_score * 0.4 + network_factor * 0.3 + environmental_factor * 0.3)


class SurveillanceData(BaseModel):
    """
    Real-time surveillance data for monitoring.

    Captures real-time surveillance information for continuous
    monitoring and early warning systems.
    """

    # Identification
    surveillance_id: str = Field(..., description="Unique surveillance record ID")
    monitoring_site: str = Field(..., description="Surveillance site identifier")
    reporting_period: dict[str, datetime] = Field(
        ..., description="Reporting period start and end"
    )

    # Geographic Context
    location: Point = Field(..., description="Surveillance location")
    coverage_area: Polygon = Field(..., description="Surveillance coverage area")
    population_monitored: int = Field(0, ge=0, description="Population under surveillance")

    # Case Data
    confirmed_cases: int = Field(0, ge=0, description="Confirmed malaria cases")
    suspected_cases: int = Field(0, ge=0, description="Suspected malaria cases")
    severe_cases: int = Field(0, ge=0, description="Severe malaria cases")
    deaths: int = Field(0, ge=0, description="Malaria-related deaths")

    # Laboratory Data
    tests_performed: int = Field(0, ge=0, description="Total tests performed")
    positive_tests: int = Field(0, ge=0, description="Positive test results")
    test_positivity_rate: float = Field(0.0, ge=0, le=1, description="Test positivity rate")

    # Vector Surveillance
    vector_density: float | None = Field(None, description="Vector density per trap")
    sporozoite_rate: float | None = Field(None, description="Sporozoite rate in vectors")
    entomological_inoculation_rate: float | None = Field(
        None, description="Entomological inoculation rate"
    )

    # Environmental Monitoring
    temperature_avg: float | None = Field(None, description="Average temperature (°C)")
    rainfall_mm: float | None = Field(None, description="Rainfall amount (mm)")
    humidity_avg: float | None = Field(None, description="Average humidity (%)")
    vegetation_index: float | None = Field(None, description="Vegetation index (NDVI)")

    # Alert Thresholds
    alert_threshold_exceeded: bool = Field(False, description="Alert threshold exceeded")
    threshold_type: str | None = Field(None, description="Type of threshold exceeded")
    alert_level: int = Field(0, ge=0, le=5, description="Alert level (0-5)")

    # Data Quality
    completeness_score: float = Field(1.0, ge=0, le=1, description="Data completeness")
    timeliness_score: float = Field(1.0, ge=0, le=1, description="Reporting timeliness")
    data_source_reliability: float = Field(1.0, ge=0, le=1, description="Source reliability")

    # Response Status
    response_triggered: bool = Field(False, description="Response action triggered")
    response_type: str | None = Field(None, description="Type of response action")
    response_time_hours: float | None = Field(None, description="Response time in hours")

    # Metadata
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    reported_by: str = Field(..., description="Reporting entity")
    data_collection_method: str = Field(..., description="Data collection methodology")

    def calculate_alert_score(self) -> float:
        """Calculate composite alert score."""
        # Combine case rates, test positivity, and environmental factors
        case_rate = self.confirmed_cases / max(self.population_monitored, 1) * 100000
        case_component = min(case_rate / 1000, 1.0)  # Normalize to 1000 cases per 100k

        test_component = self.test_positivity_rate

        # Environmental risk factors
        env_risk = 0.0
        if self.temperature_avg and self.rainfall_mm:
            # Simple environmental risk calculation
            temp_risk = 1.0 if 20 <= self.temperature_avg <= 30 else 0.5
            rain_risk = 1.0 if 50 <= self.rainfall_mm <= 300 else 0.5
            env_risk = (temp_risk + rain_risk) / 2

        # Weighted combination
        return (case_component * 0.5 + test_component * 0.3 + env_risk * 0.2)

    def should_trigger_alert(self, threshold: float = 0.7) -> bool:
        """Determine if surveillance data should trigger an alert."""
        return self.calculate_alert_score() >= threshold

    def quality_score(self) -> float:
        """Calculate overall data quality score."""
        return (self.completeness_score * 0.4 +
                self.timeliness_score * 0.3 +
                self.data_source_reliability * 0.3)
