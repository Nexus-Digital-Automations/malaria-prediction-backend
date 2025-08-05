"""Database models for malaria prediction system.

This module defines SQLAlchemy models for storing environmental data,
predictions, and risk assessments. Models are designed to work with
PostgreSQL and TimescaleDB for efficient time-series storage.
"""

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base

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
