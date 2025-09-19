"""Database models for malaria prediction system.

This module defines SQLAlchemy models for storing environmental data,
predictions, and risk assessments. Models are designed to work with
PostgreSQL and TimescaleDB for efficient time-series storage.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ERA5DataPoint(Base):
    """Raw ERA5 climate data points.

    Stores individual climate observations from ERA5 with support
    for TimescaleDB hypertable partitioning by timestamp.
    """

    __tablename__ = "era5_data_points"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Temperature data (Celsius)
    temperature_2m = Column(Float, nullable=True)
    temperature_2m_max = Column(Float, nullable=True)
    temperature_2m_min = Column(Float, nullable=True)
    dewpoint_2m = Column(Float, nullable=True)

    # Precipitation (mm)
    total_precipitation = Column(Float, nullable=True)

    # Wind data (m/s)
    wind_speed_10m = Column(Float, nullable=True)
    wind_direction_10m = Column(Float, nullable=True)

    # Pressure (Pa)
    surface_pressure = Column(Float, nullable=True)

    # Additional metadata
    data_source = Column(String(50), default="ERA5")
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_era5_location", "latitude", "longitude"),
        Index("idx_era5_timestamp_location", "timestamp", "latitude", "longitude"),
        UniqueConstraint(
            "timestamp", "latitude", "longitude", name="uq_era5_timestamp_location"
        ),
    )


class ProcessedClimateData(Base):
    """Processed and aggregated climate data.

    Stores daily aggregated climate data with calculated indices
    relevant to malaria transmission risk.
    """

    __tablename__ = "processed_climate_data"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Aggregated temperature metrics (Celsius)
    mean_temperature = Column(Float, nullable=False)
    max_temperature = Column(Float, nullable=False)
    min_temperature = Column(Float, nullable=False)
    diurnal_temperature_range = Column(Float, nullable=True)

    # Malaria-specific indices
    temperature_suitability = Column(Float, nullable=True)  # 0-1 scale
    mosquito_growing_degree_days = Column(Float, nullable=True)

    # Precipitation metrics
    daily_precipitation_mm = Column(Float, nullable=True)
    monthly_precipitation_mm = Column(Float, nullable=True)
    precipitation_risk_factor = Column(Float, nullable=True)  # 0-1 scale

    # Humidity metrics
    mean_relative_humidity = Column(Float, nullable=True)
    humidity_risk_factor = Column(Float, nullable=True)  # 0-1 scale

    # Processing metadata
    processing_version = Column(String(20), nullable=False)
    processing_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    source_file_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_processed_location", "latitude", "longitude"),
        Index("idx_processed_date_location", "date", "latitude", "longitude"),
        UniqueConstraint(
            "date", "latitude", "longitude", name="uq_processed_date_location"
        ),
    )


class LocationTimeSeries(Base):
    """Location-specific time series data.

    Stores pre-computed time series for specific geographic locations
    to enable fast querying of historical data for predictions.
    """

    __tablename__ = "location_time_series"

    id = Column(Integer, primary_key=True)
    location_id = Column(String(100), nullable=False, index=True)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country_code = Column(String(3), nullable=False)
    admin_level = Column(String(100), nullable=True)

    # Time series data stored as JSON for flexibility
    # Format: [{"date": "2023-01-01", "temp": 25.5, "precip": 120, ...}, ...]
    # Use JSONB on PostgreSQL, JSON on other databases
    climate_time_series = Column(JSON, nullable=True)
    risk_time_series = Column(JSON, nullable=True)

    # Summary statistics
    avg_annual_temperature = Column(Float, nullable=True)
    avg_annual_precipitation = Column(Float, nullable=True)
    historical_outbreak_frequency = Column(Float, nullable=True)

    # Metadata
    series_start_date = Column(DateTime(timezone=True), nullable=True)
    series_end_date = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_location_coords", "latitude", "longitude"),
        UniqueConstraint("location_id", name="uq_location_id"),
    )


class CHIRPSDataPoint(Base):
    """CHIRPS precipitation data points.

    Stores precipitation data from Climate Hazards Group InfraRed
    Precipitation with Station data (CHIRPS) dataset.
    """

    __tablename__ = "chirps_data_points"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Precipitation data (mm)
    precipitation = Column(Float, nullable=False)
    precipitation_accumulated_5d = Column(Float, nullable=True)
    precipitation_accumulated_10d = Column(Float, nullable=True)
    precipitation_accumulated_30d = Column(Float, nullable=True)

    # Anomaly data
    precipitation_anomaly = Column(Float, nullable=True)
    precipitation_percentile = Column(Float, nullable=True)

    # Quality metrics
    data_quality_flag = Column(Integer, default=0)  # 0=good, 1=interpolated, 2=missing
    station_count = Column(Integer, nullable=True)

    # Metadata
    data_source = Column(String(50), default="CHIRPS")
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_chirps_location", "latitude", "longitude"),
        Index("idx_chirps_date_location", "date", "latitude", "longitude"),
        UniqueConstraint(
            "date", "latitude", "longitude", name="uq_chirps_date_location"
        ),
    )


class MODISDataPoint(Base):
    """MODIS vegetation index data points.

    Stores vegetation indices from MODerate Resolution Imaging
    Spectroradiometer (MODIS) satellite data.
    """

    __tablename__ = "modis_data_points"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Vegetation indices
    ndvi = Column(Float, nullable=True)  # Normalized Difference Vegetation Index
    evi = Column(Float, nullable=True)  # Enhanced Vegetation Index
    lai = Column(Float, nullable=True)  # Leaf Area Index
    fpar = Column(
        Float, nullable=True
    )  # Fraction of Photosynthetically Active Radiation

    # Land surface temperature (Kelvin)
    lst_day = Column(Float, nullable=True)
    lst_night = Column(Float, nullable=True)

    # Quality indicators
    ndvi_quality = Column(Integer, nullable=True)
    evi_quality = Column(Integer, nullable=True)
    pixel_reliability = Column(Integer, nullable=True)

    # Composite period information
    composite_day_of_year = Column(Integer, nullable=True)
    composite_period_days = Column(Integer, default=16)

    # Metadata
    data_source = Column(String(50), default="MODIS")
    product_type = Column(String(50), nullable=True)  # MOD13Q1, MYD13Q1, etc.
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_modis_location", "latitude", "longitude"),
        Index("idx_modis_date_location", "date", "latitude", "longitude"),
        Index("idx_modis_ndvi", "ndvi"),
        UniqueConstraint(
            "date",
            "latitude",
            "longitude",
            "product_type",
            name="uq_modis_date_location_product",
        ),
    )


class MAPDataPoint(Base):
    """Malaria Atlas Project (MAP) data points.

    Stores malaria epidemiological data from the Malaria Atlas Project
    including prevalence, incidence, and intervention coverage data.
    """

    __tablename__ = "map_data_points"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country_code = Column(String(3), nullable=False)
    admin_unit = Column(String(200), nullable=True)

    # Parasite prevalence rates (%)
    pf_pr = Column(Float, nullable=True)  # P. falciparum prevalence rate
    pv_pr = Column(Float, nullable=True)  # P. vivax prevalence rate
    pf_pr_lower = Column(Float, nullable=True)
    pf_pr_upper = Column(Float, nullable=True)

    # Incidence rates (cases per 1000 population)
    pf_incidence = Column(Float, nullable=True)
    pv_incidence = Column(Float, nullable=True)
    total_incidence = Column(Float, nullable=True)

    # Intervention coverage (0-1 scale)
    itn_coverage = Column(Float, nullable=True)  # Insecticide-treated nets
    irs_coverage = Column(Float, nullable=True)  # Indoor residual spraying
    act_coverage = Column(Float, nullable=True)  # Artemisinin combination therapy

    # Environmental suitability (0-1 scale)
    transmission_suitability = Column(Float, nullable=True)
    vector_suitability = Column(Float, nullable=True)

    # Population data
    population_at_risk = Column(Integer, nullable=True)
    population_total = Column(Integer, nullable=True)

    # Data quality and uncertainty
    data_quality_score = Column(Float, nullable=True)
    uncertainty_lower = Column(Float, nullable=True)
    uncertainty_upper = Column(Float, nullable=True)

    # Metadata
    data_source = Column(String(50), default="MAP")
    data_version = Column(String(20), nullable=True)
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    source_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_map_location", "latitude", "longitude"),
        Index("idx_map_year_location", "year", "latitude", "longitude"),
        Index("idx_map_country", "country_code"),
        UniqueConstraint("year", "latitude", "longitude", name="uq_map_year_location"),
    )


class WorldPopDataPoint(Base):
    """WorldPop population data points.

    Stores population density and demographic data from WorldPop
    global population datasets.
    """

    __tablename__ = "worldpop_data_points"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country_code = Column(String(3), nullable=False)

    # Population counts and density
    population_total = Column(Float, nullable=False)
    population_density = Column(Float, nullable=False)  # people per km²

    # Age-stratified population
    population_male = Column(Float, nullable=True)
    population_female = Column(Float, nullable=True)
    population_children_u5 = Column(Float, nullable=True)
    population_children_u1 = Column(Float, nullable=True)
    population_reproductive_age = Column(Float, nullable=True)  # 15-49 years

    # Urban/rural classification
    urban_rural_classification = Column(Float, nullable=True)  # 0=rural, 1=urban

    # Accessibility metrics
    travel_time_to_cities = Column(Float, nullable=True)  # minutes
    travel_time_to_healthcare = Column(Float, nullable=True)  # minutes

    # Socioeconomic indicators (if available)
    poverty_headcount = Column(Float, nullable=True)
    literacy_rate = Column(Float, nullable=True)

    # Data quality
    data_quality_flag = Column(Integer, default=0)
    spatial_resolution_m = Column(Integer, nullable=True)

    # Metadata
    data_source = Column(String(50), default="WorldPop")
    dataset_version = Column(String(20), nullable=True)
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_reference = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_worldpop_location", "latitude", "longitude"),
        Index("idx_worldpop_year_location", "year", "latitude", "longitude"),
        Index("idx_worldpop_country", "country_code"),
        Index("idx_worldpop_density", "population_density"),
        UniqueConstraint(
            "year", "latitude", "longitude", name="uq_worldpop_year_location"
        ),
    )


class MalariaRiskIndex(Base):
    """Calculated malaria risk indices.

    Stores composite malaria risk assessments combining multiple
    environmental factors for specific locations and time periods.
    """

    __tablename__ = "malaria_risk_indices"

    id = Column(Integer, primary_key=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(200), nullable=True)

    # Risk scores (0-1 scale)
    composite_risk_score = Column(Float, nullable=False)
    temperature_risk_component = Column(Float, nullable=False)
    precipitation_risk_component = Column(Float, nullable=False)
    humidity_risk_component = Column(Float, nullable=False)
    vegetation_risk_component = Column(Float, nullable=True)

    # Risk level categorization
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence_score = Column(Float, nullable=False)

    # Time horizon
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    time_horizon_days = Column(Integer, nullable=False)

    # Model information
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # rule-based, ml, ensemble

    # Additional factors as JSON
    additional_factors = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_sources = Column(JSON, nullable=True)  # ["ERA5", "CHIRPS", etc.]

    __table_args__ = (
        Index("idx_risk_location", "latitude", "longitude"),
        Index("idx_risk_date_location", "assessment_date", "latitude", "longitude"),
        Index("idx_risk_level", "risk_level"),
    )


class AlertConfiguration(Base):
    """Alert configuration and threshold settings.

    Stores user-defined alert thresholds, notification preferences,
    and configuration settings for the alert system.
    """

    __tablename__ = "alert_configurations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    configuration_name = Column(String(200), nullable=False)

    # Alert thresholds (0-1 scale for risk scores)
    low_risk_threshold = Column(Float, nullable=False, default=0.3)
    medium_risk_threshold = Column(Float, nullable=False, default=0.6)
    high_risk_threshold = Column(Float, nullable=False, default=0.8)
    critical_risk_threshold = Column(Float, nullable=False, default=0.9)

    # Geographic filters
    latitude_min = Column(Float, nullable=True)
    latitude_max = Column(Float, nullable=True)
    longitude_min = Column(Float, nullable=True)
    longitude_max = Column(Float, nullable=True)
    country_codes = Column(JSON, nullable=True)  # List of ISO country codes
    admin_regions = Column(JSON, nullable=True)  # List of administrative regions

    # Time-based filters
    alert_frequency_hours = Column(Integer, nullable=False, default=24)  # Minimum hours between alerts
    time_horizon_days = Column(Integer, nullable=False, default=7)  # Prediction time horizon
    active_hours_start = Column(Integer, nullable=True)  # 0-23, local time
    active_hours_end = Column(Integer, nullable=True)  # 0-23, local time
    timezone = Column(String(50), nullable=False, default="UTC")

    # Notification channels
    enable_push_notifications = Column(Boolean, nullable=False, default=True)
    enable_email_notifications = Column(Boolean, nullable=False, default=True)
    enable_sms_notifications = Column(Boolean, nullable=False, default=False)
    enable_webhook_notifications = Column(Boolean, nullable=False, default=False)

    # Contact information
    email_addresses = Column(JSON, nullable=True)  # List of email addresses
    phone_numbers = Column(JSON, nullable=True)  # List of phone numbers
    webhook_urls = Column(JSON, nullable=True)  # List of webhook endpoints

    # Emergency response settings
    enable_emergency_escalation = Column(Boolean, nullable=False, default=False)
    emergency_contact_emails = Column(JSON, nullable=True)
    emergency_contact_phones = Column(JSON, nullable=True)
    emergency_escalation_threshold = Column(Float, nullable=False, default=0.95)

    # Configuration status
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_triggered = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_alert_config_user", "user_id"),
        Index("idx_alert_config_active", "is_active"),
    )


class AlertRule(Base):
    """Advanced alert rules with complex conditions.

    Stores sophisticated alert logic beyond simple thresholds,
    including multi-factor conditions and temporal patterns.
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    configuration_id = Column(Integer, ForeignKey("alert_configurations.id"), nullable=False)
    rule_name = Column(String(200), nullable=False)
    rule_description = Column(Text, nullable=True)

    # Rule conditions (stored as JSON for flexibility)
    # Example: {"and": [{"risk_score": {"gt": 0.8}}, {"trend": "increasing"}]}
    conditions = Column(JSON, nullable=False)

    # Rule type and metadata
    rule_type = Column(String(50), nullable=False)  # threshold, trend, pattern, ml
    rule_version = Column(String(20), nullable=False, default="1.0")

    # Execution settings
    evaluation_frequency_minutes = Column(Integer, nullable=False, default=60)
    min_data_points_required = Column(Integer, nullable=False, default=1)
    lookback_period_hours = Column(Integer, nullable=False, default=24)

    # Alert suppression
    cooldown_period_hours = Column(Integer, nullable=False, default=24)
    max_alerts_per_day = Column(Integer, nullable=False, default=5)

    # Priority and categorization
    alert_priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    alert_category = Column(String(50), nullable=False, default="outbreak_risk")

    # Status and performance tracking
    is_active = Column(Boolean, nullable=False, default=True)
    last_evaluation = Column(DateTime(timezone=True), nullable=True)
    evaluation_count = Column(Integer, nullable=False, default=0)
    triggered_count = Column(Integer, nullable=False, default=0)
    false_positive_count = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)

    # Relationships
    configuration = relationship("AlertConfiguration", backref="rules")

    __table_args__ = (
        Index("idx_alert_rule_config", "configuration_id"),
        Index("idx_alert_rule_active", "is_active"),
        Index("idx_alert_rule_priority", "alert_priority"),
    )


class Alert(Base):
    """Generated alerts and notifications.

    Stores all generated alerts with their status, delivery tracking,
    and performance metrics for system monitoring.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    configuration_id = Column(Integer, ForeignKey("alert_configurations.id"), nullable=False)

    # Alert identification
    alert_type = Column(String(50), nullable=False)  # outbreak_risk, system_health, data_quality
    alert_level = Column(String(20), nullable=False)  # low, medium, high, critical, emergency
    alert_title = Column(String(500), nullable=False)
    alert_message = Column(Text, nullable=False)
    alert_summary = Column(Text, nullable=True)

    # Geographic and temporal context
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(200), nullable=True)
    country_code = Column(String(3), nullable=True)
    admin_region = Column(String(200), nullable=True)

    # Risk and prediction data
    risk_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    prediction_date = Column(DateTime(timezone=True), nullable=True)
    time_horizon_days = Column(Integer, nullable=True)

    # Alert data and context (JSON for flexibility)
    # Includes: trigger conditions, data sources, model outputs, etc.
    alert_data = Column(JSON, nullable=True)
    environmental_data = Column(JSON, nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, default="generated")  # generated, sent, delivered, read, acknowledged, resolved
    priority = Column(String(20), nullable=False)  # low, medium, high, critical, emergency

    # Delivery tracking
    push_notification_sent = Column(Boolean, nullable=False, default=False)
    push_notification_delivered = Column(Boolean, nullable=False, default=False)
    email_notification_sent = Column(Boolean, nullable=False, default=False)
    email_notification_delivered = Column(Boolean, nullable=False, default=False)
    sms_notification_sent = Column(Boolean, nullable=False, default=False)
    sms_notification_delivered = Column(Boolean, nullable=False, default=False)
    webhook_notification_sent = Column(Boolean, nullable=False, default=False)
    webhook_notification_delivered = Column(Boolean, nullable=False, default=False)

    # User interaction tracking
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Emergency escalation
    is_emergency = Column(Boolean, nullable=False, default=False)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_level = Column(Integer, nullable=False, default=0)

    # Performance and feedback
    response_time_seconds = Column(Integer, nullable=True)  # Time from generation to acknowledgment
    feedback_rating = Column(Integer, nullable=True)  # 1-5 scale user feedback
    feedback_comments = Column(Text, nullable=True)
    false_positive = Column(Boolean, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rule = relationship("AlertRule", backref="alerts")
    configuration = relationship("AlertConfiguration", backref="alerts")

    __table_args__ = (
        Index("idx_alert_status", "status"),
        Index("idx_alert_level", "alert_level"),
        Index("idx_alert_priority", "priority"),
        Index("idx_alert_location", "latitude", "longitude"),
        Index("idx_alert_created", "created_at"),
        Index("idx_alert_type_level", "alert_type", "alert_level"),
        Index("idx_alert_emergency", "is_emergency"),
    )


class NotificationDelivery(Base):
    """Notification delivery tracking and retry management.

    Tracks individual notification delivery attempts across
    all channels with retry logic and failure analysis.
    """

    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)

    # Delivery channel and targeting
    channel = Column(String(20), nullable=False)  # push, email, sms, webhook
    recipient = Column(String(500), nullable=False)  # email, phone, device_token, webhook_url
    recipient_type = Column(String(50), nullable=False)  # user, admin, emergency_contact, system

    # Message content
    subject = Column(String(500), nullable=True)
    message_body = Column(Text, nullable=False)
    message_format = Column(String(20), nullable=False, default="text")  # text, html, json

    # Delivery status and tracking
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, delivered, failed, bounced
    delivery_provider = Column(String(50), nullable=True)  # firebase, sendgrid, twilio, etc.
    provider_message_id = Column(String(200), nullable=True)
    provider_response = Column(JSON, nullable=True)

    # Timing and retry logic
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    failure_reason = Column(String(100), nullable=True)  # invalid_recipient, service_unavailable, rate_limited

    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    delivery_time_ms = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    alert = relationship("Alert", backref="deliveries")

    __table_args__ = (
        Index("idx_notification_alert", "alert_id"),
        Index("idx_notification_status", "status"),
        Index("idx_notification_channel", "channel"),
        Index("idx_notification_scheduled", "scheduled_at"),
        Index("idx_notification_retry", "next_retry_at"),
    )


class AlertTemplate(Base):
    """Alert message templates for different notification channels.

    Stores customizable templates for generating alert messages
    across different channels and languages.
    """

    __tablename__ = "alert_templates"

    id = Column(Integer, primary_key=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)  # outbreak_risk, system_alert, emergency

    # Channel-specific templates
    channel = Column(String(20), nullable=False)  # push, email, sms, webhook
    language_code = Column(String(10), nullable=False, default="en")

    # Template content
    subject_template = Column(Text, nullable=True)
    message_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=True)

    # Template variables and metadata
    # Stores available variables: {risk_score}, {location}, {prediction_date}, etc.
    template_variables = Column(JSON, nullable=True)
    template_description = Column(Text, nullable=True)

    # Formatting and styling
    message_format = Column(String(20), nullable=False, default="text")  # text, html, markdown
    include_attachments = Column(Boolean, nullable=False, default=False)
    attachment_types = Column(JSON, nullable=True)  # ["map_image", "risk_chart", "data_export"]

    # Template management
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    version = Column(String(20), nullable=False, default="1.0")

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_template_type_channel", "template_type", "channel"),
        Index("idx_template_language", "language_code"),
        Index("idx_template_active", "is_active"),
        UniqueConstraint("template_name", "channel", "language_code", name="uq_template_name_channel_lang"),
    )


class UserDeviceToken(Base):
    """User device tokens for push notifications.

    Stores FCM (Firebase Cloud Messaging) device tokens
    for push notification delivery to mobile devices.
    """

    __tablename__ = "user_device_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)

    # Device and token information
    device_token = Column(String(500), nullable=False, unique=True)
    device_type = Column(String(20), nullable=False)  # ios, android, web
    device_id = Column(String(200), nullable=True)
    device_name = Column(String(200), nullable=True)

    # Platform-specific settings
    platform_version = Column(String(50), nullable=True)
    app_version = Column(String(50), nullable=True)

    # Token status and management
    is_active = Column(Boolean, nullable=False, default=True)
    is_valid = Column(Boolean, nullable=False, default=True)
    last_validated = Column(DateTime(timezone=True), nullable=True)
    validation_failures = Column(Integer, nullable=False, default=0)

    # Usage tracking
    last_notification_sent = Column(DateTime(timezone=True), nullable=True)
    notification_count = Column(Integer, nullable=False, default=0)
    successful_deliveries = Column(Integer, nullable=False, default=0)
    failed_deliveries = Column(Integer, nullable=False, default=0)

    # Token lifecycle
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    refreshed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    # Geographic context (for location-based notifications)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    location_updated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_device_token_user", "user_id"),
        Index("idx_device_token_active", "is_active"),
        Index("idx_device_token_type", "device_type"),
        Index("idx_device_token_location", "last_latitude", "last_longitude"),
    )


class AlertPerformanceMetrics(Base):
    """Alert system performance and analytics.

    Stores aggregated metrics for monitoring alert system
    performance, accuracy, and user engagement.
    """

    __tablename__ = "alert_performance_metrics"

    id = Column(Integer, primary_key=True)

    # Time aggregation
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    aggregation_period = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly

    # Alert generation metrics
    alerts_generated = Column(Integer, nullable=False, default=0)
    alerts_by_level = Column(JSON, nullable=True)  # {"low": 5, "medium": 3, "high": 1}
    alerts_by_type = Column(JSON, nullable=True)
    alerts_by_location = Column(JSON, nullable=True)

    # Delivery metrics
    notifications_sent = Column(Integer, nullable=False, default=0)
    notifications_delivered = Column(Integer, nullable=False, default=0)
    notifications_failed = Column(Integer, nullable=False, default=0)
    delivery_rate_percentage = Column(Float, nullable=True)

    # Channel performance
    push_delivery_rate = Column(Float, nullable=True)
    email_delivery_rate = Column(Float, nullable=True)
    sms_delivery_rate = Column(Float, nullable=True)
    webhook_delivery_rate = Column(Float, nullable=True)

    # User engagement metrics
    alerts_viewed = Column(Integer, nullable=False, default=0)
    alerts_acknowledged = Column(Integer, nullable=False, default=0)
    alerts_dismissed = Column(Integer, nullable=False, default=0)
    avg_response_time_seconds = Column(Float, nullable=True)
    engagement_rate_percentage = Column(Float, nullable=True)

    # Accuracy and feedback
    false_positive_count = Column(Integer, nullable=False, default=0)
    false_positive_rate = Column(Float, nullable=True)
    user_feedback_avg_rating = Column(Float, nullable=True)
    user_feedback_count = Column(Integer, nullable=False, default=0)

    # System performance
    avg_generation_time_ms = Column(Float, nullable=True)
    avg_delivery_time_ms = Column(Float, nullable=True)
    system_errors = Column(Integer, nullable=False, default=0)

    # Geographic and demographic breakdowns
    metrics_by_country = Column(JSON, nullable=True)
    metrics_by_risk_level = Column(JSON, nullable=True)
    metrics_by_user_type = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_version = Column(String(20), nullable=False, default="1.0")

    __table_args__ = (
        Index("idx_perf_metrics_date", "metric_date"),
        Index("idx_perf_metrics_period", "aggregation_period"),
        UniqueConstraint("metric_date", "aggregation_period", name="uq_metrics_date_period"),
    )


class Report(Base):
    """Report entity for storing generated reports and metadata.

    Stores comprehensive report information including generation metadata,
    content references, and export status for all supported formats.
    """

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Report configuration
    report_type = Column(String(50), nullable=False)  # analytics, prediction, outbreak, custom
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=True)

    # Generation metadata
    generated_by = Column(String(100), nullable=False, index=True)  # user_id
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    data_period_start = Column(DateTime(timezone=True), nullable=True)
    data_period_end = Column(DateTime(timezone=True), nullable=True)

    # Content and data
    report_data = Column(JSON, nullable=False)  # Structured report data
    chart_configurations = Column(JSON, nullable=True)  # Chart configs and data
    custom_parameters = Column(JSON, nullable=True)  # Custom filters/parameters

    # Export status and metadata
    export_formats = Column(JSON, nullable=True)  # ["pdf", "excel", "csv", "pptx"]
    export_status = Column(JSON, nullable=True)  # {format: {status, path, generated_at}}
    file_paths = Column(JSON, nullable=True)  # {format: relative_path}

    # Scheduling and automation
    is_scheduled = Column(Boolean, default=False)
    schedule_id = Column(Integer, ForeignKey("report_schedules.id"), nullable=True)

    # Performance and size metadata
    generation_time_seconds = Column(Float, nullable=True)
    file_sizes = Column(JSON, nullable=True)  # {format: size_bytes}
    data_points_count = Column(Integer, nullable=True)

    # Status and lifecycle
    status = Column(String(20), nullable=False, default="draft")  # draft, generating, completed, failed
    error_message = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("ReportTemplate", back_populates="reports")
    schedule = relationship("ReportSchedule", back_populates="reports")

    __table_args__ = (
        Index("idx_report_user_date", "generated_by", "generated_at"),
        Index("idx_report_type_status", "report_type", "status"),
        Index("idx_report_schedule", "schedule_id", "generated_at"),
    )


class ReportTemplate(Base):
    """Report template entity for customizable report layouts.

    Stores template configurations, widget layouts, and styling
    for reusable report generation.
    """

    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Template metadata
    created_by = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_by = Column(String(100), nullable=True)
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Template configuration
    template_type = Column(String(50), nullable=False)  # standard, custom, system
    category = Column(String(50), nullable=False)  # analytics, prediction, outbreak, operational

    # Layout and design
    layout_configuration = Column(JSON, nullable=False)  # Widget layout, positions, sizes
    style_configuration = Column(JSON, nullable=True)  # Colors, fonts, branding
    page_configuration = Column(JSON, nullable=True)  # Page settings, margins, orientation

    # Widget and component definitions
    widgets = Column(JSON, nullable=False)  # Widget definitions and configurations
    data_sources = Column(JSON, nullable=False)  # Data source configurations
    chart_configurations = Column(JSON, nullable=True)  # Default chart settings

    # Template behavior
    default_parameters = Column(JSON, nullable=True)  # Default filter/parameter values
    required_parameters = Column(JSON, nullable=True)  # Required parameters for generation
    export_formats = Column(JSON, nullable=True)  # Supported export formats

    # Usage and performance
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    average_generation_time = Column(Float, nullable=True)

    # Template status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Available to all users
    version = Column(String(20), nullable=False, default="1.0")

    # Relationships
    reports = relationship("Report", back_populates="template")
    schedules = relationship("ReportSchedule", back_populates="template")

    __table_args__ = (
        Index("idx_template_user_category", "created_by", "category"),
        Index("idx_template_type_active", "template_type", "is_active"),
        UniqueConstraint("name", "created_by", name="uq_template_name_user"),
    )


class ReportSchedule(Base):
    """Report schedule entity for automated report generation.

    Manages automated report generation schedules with flexible
    timing, delivery options, and configuration management.
    """

    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Schedule ownership
    created_by = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Template and configuration
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    report_configuration = Column(JSON, nullable=False)  # Report generation parameters

    # Schedule timing
    schedule_type = Column(String(20), nullable=False)  # cron, interval, one_time
    cron_expression = Column(String(100), nullable=True)  # For cron-based schedules
    interval_minutes = Column(Integer, nullable=True)  # For interval-based schedules
    timezone = Column(String(50), nullable=False, default="UTC")

    # Execution window
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    next_execution = Column(DateTime(timezone=True), nullable=True, index=True)
    last_execution = Column(DateTime(timezone=True), nullable=True)

    # Delivery configuration
    delivery_methods = Column(JSON, nullable=False)  # ["email", "webhook", "storage"]
    email_recipients = Column(JSON, nullable=True)  # List of email addresses
    webhook_urls = Column(JSON, nullable=True)  # List of webhook endpoints
    storage_locations = Column(JSON, nullable=True)  # Storage paths and configurations

    # Export and format settings
    export_formats = Column(JSON, nullable=False, default=["pdf"])  # Formats to generate
    compression_enabled = Column(Boolean, default=False)
    retention_days = Column(Integer, nullable=True)  # Auto-cleanup after N days

    # Schedule status and health
    is_active = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default="active")  # active, paused, failed, completed
    last_status = Column(String(20), nullable=True)  # Previous execution status
    error_count = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)

    # Performance tracking
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    average_execution_time = Column(Float, nullable=True)
    last_execution_time = Column(Float, nullable=True)

    # Relationships
    template = relationship("ReportTemplate", back_populates="schedules")
    reports = relationship("Report", back_populates="schedule")

    __table_args__ = (
        Index("idx_schedule_user_active", "created_by", "is_active"),
        Index("idx_schedule_next_execution", "next_execution", "is_active"),
        Index("idx_schedule_template", "template_id", "is_active"),
    )


class ReportMetrics(Base):
    """Report metrics entity for performance and usage analytics.

    Tracks comprehensive metrics for report generation performance,
    usage patterns, and system health monitoring.
    """

    __tablename__ = "report_metrics"

    id = Column(Integer, primary_key=True)
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    aggregation_period = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly

    # Report generation metrics
    total_reports_generated = Column(Integer, default=0)
    successful_reports = Column(Integer, default=0)
    failed_reports = Column(Integer, default=0)
    average_generation_time = Column(Float, nullable=True)
    max_generation_time = Column(Float, nullable=True)
    min_generation_time = Column(Float, nullable=True)

    # Export format metrics
    pdf_exports = Column(Integer, default=0)
    excel_exports = Column(Integer, default=0)
    csv_exports = Column(Integer, default=0)
    powerpoint_exports = Column(Integer, default=0)

    # Template usage metrics
    template_usage = Column(JSON, nullable=True)  # {template_id: usage_count}
    most_used_template_id = Column(Integer, nullable=True)
    custom_reports_count = Column(Integer, default=0)

    # Scheduling metrics
    scheduled_reports = Column(Integer, default=0)
    manual_reports = Column(Integer, default=0)
    schedule_failures = Column(Integer, default=0)
    average_schedule_execution_time = Column(Float, nullable=True)

    # Performance metrics
    total_data_points_processed = Column(Integer, default=0)
    average_data_points_per_report = Column(Float, nullable=True)
    total_storage_used_bytes = Column(Integer, default=0)
    average_file_size_bytes = Column(Float, nullable=True)

    # User engagement metrics
    unique_users = Column(Integer, default=0)
    reports_per_user = Column(Float, nullable=True)
    user_retention_rate = Column(Float, nullable=True)

    # Error and failure analysis
    error_categories = Column(JSON, nullable=True)  # {error_type: count}
    most_common_error = Column(String(255), nullable=True)
    error_rate_percentage = Column(Float, nullable=True)

    # System resource metrics
    peak_memory_usage_mb = Column(Float, nullable=True)
    average_cpu_usage_percent = Column(Float, nullable=True)
    peak_concurrent_generations = Column(Integer, nullable=True)
    queue_wait_time_seconds = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_version = Column(String(20), nullable=False, default="1.0")

    __table_args__ = (
        Index("idx_report_metrics_date", "metric_date"),
        Index("idx_report_metrics_period", "aggregation_period"),
        UniqueConstraint("metric_date", "aggregation_period", name="uq_report_metrics_date_period"),
    )


# TimescaleDB-specific setup queries
TIMESCALEDB_SETUP = """
-- Enable TimescaleDB and PostGIS extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Convert time-series tables to hypertables
SELECT create_hypertable('era5_data_points', 'timestamp',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('chirps_data_points', 'date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('modis_data_points', 'date',
    chunk_time_interval => INTERVAL '3 months',
    if_not_exists => TRUE);

SELECT create_hypertable('processed_climate_data', 'date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('malaria_risk_indices', 'assessment_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

-- Convert alert tables to hypertables for time-series performance
SELECT create_hypertable('alerts', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('notification_deliveries', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('alert_performance_metrics', 'metric_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

-- Convert report tables to hypertables for time-series performance
SELECT create_hypertable('reports', 'generated_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

SELECT create_hypertable('report_metrics', 'metric_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

-- Create spatial indexes for geospatial queries
CREATE INDEX IF NOT EXISTS idx_era5_location_gist
ON era5_data_points USING GIST (ST_Point(longitude, latitude));

CREATE INDEX IF NOT EXISTS idx_chirps_location_gist
ON chirps_data_points USING GIST (ST_Point(longitude, latitude));

CREATE INDEX IF NOT EXISTS idx_modis_location_gist
ON modis_data_points USING GIST (ST_Point(longitude, latitude));

CREATE INDEX IF NOT EXISTS idx_map_location_gist
ON map_data_points USING GIST (ST_Point(longitude, latitude));

CREATE INDEX IF NOT EXISTS idx_worldpop_location_gist
ON worldpop_data_points USING GIST (ST_Point(longitude, latitude));

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_climate_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    latitude,
    longitude,
    AVG(temperature_2m) as avg_temp,
    MAX(temperature_2m_max) as max_temp,
    MIN(temperature_2m_min) as min_temp,
    SUM(total_precipitation) as total_precip
FROM era5_data_points
GROUP BY day, latitude, longitude
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS weekly_precipitation_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('7 days', date) AS week,
    latitude,
    longitude,
    SUM(precipitation) as weekly_precip,
    AVG(precipitation) as avg_daily_precip,
    COUNT(*) as data_points
FROM chirps_data_points
GROUP BY week, latitude, longitude
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_vegetation_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', date) AS month,
    latitude,
    longitude,
    AVG(ndvi) as avg_ndvi,
    AVG(evi) as avg_evi,
    COUNT(*) as data_points
FROM modis_data_points
GROUP BY month, latitude, longitude
WITH NO DATA;

-- Refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('daily_climate_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('weekly_precipitation_summary',
    start_offset => INTERVAL '2 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '6 hours',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('monthly_vegetation_summary',
    start_offset => INTERVAL '6 months',
    end_offset => INTERVAL '1 week',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);
"""
