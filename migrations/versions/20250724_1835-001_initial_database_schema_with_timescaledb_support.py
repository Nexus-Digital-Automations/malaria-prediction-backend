"""Initial database schema with TimescaleDB support

Revision ID: 001
Revises:
Create Date: 2025-01-24 18:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial database schema with TimescaleDB support."""

    # Enable extensions first
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create ERA5 data points table
    op.create_table(
        "era5_data_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("temperature_2m", sa.Float(), nullable=True),
        sa.Column("temperature_2m_max", sa.Float(), nullable=True),
        sa.Column("temperature_2m_min", sa.Float(), nullable=True),
        sa.Column("dewpoint_2m", sa.Float(), nullable=True),
        sa.Column("total_precipitation", sa.Float(), nullable=True),
        sa.Column("wind_speed_10m", sa.Float(), nullable=True),
        sa.Column("wind_direction_10m", sa.Float(), nullable=True),
        sa.Column("surface_pressure", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_era5_location", "era5_data_points", ["latitude", "longitude"])
    op.create_index(
        "idx_era5_timestamp_location",
        "era5_data_points",
        ["timestamp", "latitude", "longitude"],
    )
    op.create_index(
        op.f("ix_era5_data_points_timestamp"), "era5_data_points", ["timestamp"]
    )

    # Create CHIRPS data points table
    op.create_table(
        "chirps_data_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("precipitation", sa.Float(), nullable=False),
        sa.Column("precipitation_accumulated_5d", sa.Float(), nullable=True),
        sa.Column("precipitation_accumulated_10d", sa.Float(), nullable=True),
        sa.Column("precipitation_accumulated_30d", sa.Float(), nullable=True),
        sa.Column("precipitation_anomaly", sa.Float(), nullable=True),
        sa.Column("precipitation_percentile", sa.Float(), nullable=True),
        sa.Column("data_quality_flag", sa.Integer(), nullable=True),
        sa.Column("station_count", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chirps_date_location",
        "chirps_data_points",
        ["date", "latitude", "longitude"],
    )
    op.create_index(
        "idx_chirps_location", "chirps_data_points", ["latitude", "longitude"]
    )
    op.create_index(op.f("ix_chirps_data_points_date"), "chirps_data_points", ["date"])

    # Create MODIS data points table
    op.create_table(
        "modis_data_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("ndvi", sa.Float(), nullable=True),
        sa.Column("evi", sa.Float(), nullable=True),
        sa.Column("lai", sa.Float(), nullable=True),
        sa.Column("fpar", sa.Float(), nullable=True),
        sa.Column("lst_day", sa.Float(), nullable=True),
        sa.Column("lst_night", sa.Float(), nullable=True),
        sa.Column("ndvi_quality", sa.Integer(), nullable=True),
        sa.Column("evi_quality", sa.Integer(), nullable=True),
        sa.Column("pixel_reliability", sa.Integer(), nullable=True),
        sa.Column("composite_day_of_year", sa.Integer(), nullable=True),
        sa.Column("composite_period_days", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column("product_type", sa.String(length=50), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_modis_date_location",
        "modis_data_points",
        ["date", "latitude", "longitude"],
    )
    op.create_index(
        "idx_modis_location", "modis_data_points", ["latitude", "longitude"]
    )
    op.create_index("idx_modis_ndvi", "modis_data_points", ["ndvi"])
    op.create_index(op.f("ix_modis_data_points_date"), "modis_data_points", ["date"])

    # Create MAP data points table
    op.create_table(
        "map_data_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("admin_unit", sa.String(length=200), nullable=True),
        sa.Column("pf_pr", sa.Float(), nullable=True),
        sa.Column("pv_pr", sa.Float(), nullable=True),
        sa.Column("pf_pr_lower", sa.Float(), nullable=True),
        sa.Column("pf_pr_upper", sa.Float(), nullable=True),
        sa.Column("pf_incidence", sa.Float(), nullable=True),
        sa.Column("pv_incidence", sa.Float(), nullable=True),
        sa.Column("total_incidence", sa.Float(), nullable=True),
        sa.Column("itn_coverage", sa.Float(), nullable=True),
        sa.Column("irs_coverage", sa.Float(), nullable=True),
        sa.Column("act_coverage", sa.Float(), nullable=True),
        sa.Column("transmission_suitability", sa.Float(), nullable=True),
        sa.Column("vector_suitability", sa.Float(), nullable=True),
        sa.Column("population_at_risk", sa.Integer(), nullable=True),
        sa.Column("population_total", sa.Integer(), nullable=True),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("uncertainty_lower", sa.Float(), nullable=True),
        sa.Column("uncertainty_upper", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column("data_version", sa.String(length=20), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("source_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_map_country", "map_data_points", ["country_code"])
    op.create_index("idx_map_location", "map_data_points", ["latitude", "longitude"])
    op.create_index(
        "idx_map_year_location", "map_data_points", ["year", "latitude", "longitude"]
    )
    op.create_index(op.f("ix_map_data_points_year"), "map_data_points", ["year"])

    # Create WorldPop data points table
    op.create_table(
        "worldpop_data_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("population_total", sa.Float(), nullable=False),
        sa.Column("population_density", sa.Float(), nullable=False),
        sa.Column("population_male", sa.Float(), nullable=True),
        sa.Column("population_female", sa.Float(), nullable=True),
        sa.Column("population_children_u5", sa.Float(), nullable=True),
        sa.Column("population_children_u1", sa.Float(), nullable=True),
        sa.Column("population_reproductive_age", sa.Float(), nullable=True),
        sa.Column("urban_rural_classification", sa.Float(), nullable=True),
        sa.Column("travel_time_to_cities", sa.Float(), nullable=True),
        sa.Column("travel_time_to_healthcare", sa.Float(), nullable=True),
        sa.Column("poverty_headcount", sa.Float(), nullable=True),
        sa.Column("literacy_rate", sa.Float(), nullable=True),
        sa.Column("data_quality_flag", sa.Integer(), nullable=True),
        sa.Column("spatial_resolution_m", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column("dataset_version", sa.String(length=20), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_worldpop_country", "worldpop_data_points", ["country_code"])
    op.create_index(
        "idx_worldpop_density", "worldpop_data_points", ["population_density"]
    )
    op.create_index(
        "idx_worldpop_location", "worldpop_data_points", ["latitude", "longitude"]
    )
    op.create_index(
        "idx_worldpop_year_location",
        "worldpop_data_points",
        ["year", "latitude", "longitude"],
    )
    op.create_index(
        op.f("ix_worldpop_data_points_year"), "worldpop_data_points", ["year"]
    )

    # Create processed climate data table
    op.create_table(
        "processed_climate_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("mean_temperature", sa.Float(), nullable=False),
        sa.Column("max_temperature", sa.Float(), nullable=False),
        sa.Column("min_temperature", sa.Float(), nullable=False),
        sa.Column("diurnal_temperature_range", sa.Float(), nullable=True),
        sa.Column("temperature_suitability", sa.Float(), nullable=True),
        sa.Column("mosquito_growing_degree_days", sa.Float(), nullable=True),
        sa.Column("daily_precipitation_mm", sa.Float(), nullable=True),
        sa.Column("monthly_precipitation_mm", sa.Float(), nullable=True),
        sa.Column("precipitation_risk_factor", sa.Float(), nullable=True),
        sa.Column("mean_relative_humidity", sa.Float(), nullable=True),
        sa.Column("humidity_risk_factor", sa.Float(), nullable=True),
        sa.Column("processing_version", sa.String(length=20), nullable=False),
        sa.Column(
            "processing_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("source_file_reference", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_processed_date_location",
        "processed_climate_data",
        ["date", "latitude", "longitude"],
    )
    op.create_index(
        "idx_processed_location", "processed_climate_data", ["latitude", "longitude"]
    )
    op.create_index(
        op.f("ix_processed_climate_data_date"), "processed_climate_data", ["date"]
    )

    # Create location time series table
    op.create_table(
        "location_time_series",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.String(length=100), nullable=False),
        sa.Column("location_name", sa.String(length=200), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("admin_level", sa.String(length=100), nullable=True),
        sa.Column(
            "climate_time_series", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "risk_time_series", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("avg_annual_temperature", sa.Float(), nullable=True),
        sa.Column("avg_annual_precipitation", sa.Float(), nullable=True),
        sa.Column("historical_outbreak_frequency", sa.Float(), nullable=True),
        sa.Column("series_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("series_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_location_coords", "location_time_series", ["latitude", "longitude"]
    )
    op.create_index(
        op.f("ix_location_time_series_location_id"),
        "location_time_series",
        ["location_id"],
    )

    # Create malaria risk indices table
    op.create_table(
        "malaria_risk_indices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_name", sa.String(length=200), nullable=True),
        sa.Column("composite_risk_score", sa.Float(), nullable=False),
        sa.Column("temperature_risk_component", sa.Float(), nullable=False),
        sa.Column("precipitation_risk_component", sa.Float(), nullable=False),
        sa.Column("humidity_risk_component", sa.Float(), nullable=False),
        sa.Column("vegetation_risk_component", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("prediction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_horizon_days", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=20), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column(
            "additional_factors", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "data_sources", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_risk_date_location",
        "malaria_risk_indices",
        ["assessment_date", "latitude", "longitude"],
    )
    op.create_index("idx_risk_level", "malaria_risk_indices", ["risk_level"])
    op.create_index(
        "idx_risk_location", "malaria_risk_indices", ["latitude", "longitude"]
    )
    op.create_index(
        op.f("ix_malaria_risk_indices_assessment_date"),
        "malaria_risk_indices",
        ["assessment_date"],
    )

    # Add unique constraints
    op.create_unique_constraint(
        "uq_era5_timestamp_location",
        "era5_data_points",
        ["timestamp", "latitude", "longitude"],
    )
    op.create_unique_constraint(
        "uq_chirps_date_location",
        "chirps_data_points",
        ["date", "latitude", "longitude"],
    )
    op.create_unique_constraint(
        "uq_modis_date_location_product",
        "modis_data_points",
        ["date", "latitude", "longitude", "product_type"],
    )
    op.create_unique_constraint(
        "uq_map_year_location", "map_data_points", ["year", "latitude", "longitude"]
    )
    op.create_unique_constraint(
        "uq_worldpop_year_location",
        "worldpop_data_points",
        ["year", "latitude", "longitude"],
    )
    op.create_unique_constraint(
        "uq_processed_date_location",
        "processed_climate_data",
        ["date", "latitude", "longitude"],
    )
    op.create_unique_constraint(
        "uq_location_id", "location_time_series", ["location_id"]
    )

    # Convert tables to hypertables (TimescaleDB specific)
    op.execute(
        """
        SELECT create_hypertable('era5_data_points', 'timestamp',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE);
    """
    )

    op.execute(
        """
        SELECT create_hypertable('chirps_data_points', 'date',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE);
    """
    )

    op.execute(
        """
        SELECT create_hypertable('modis_data_points', 'date',
            chunk_time_interval => INTERVAL '3 months',
            if_not_exists => TRUE);
    """
    )

    op.execute(
        """
        SELECT create_hypertable('processed_climate_data', 'date',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE);
    """
    )

    op.execute(
        """
        SELECT create_hypertable('malaria_risk_indices', 'assessment_date',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE);
    """
    )

    # Create spatial indexes for geospatial queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_era5_location_gist
        ON era5_data_points USING GIST (ST_Point(longitude, latitude));
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chirps_location_gist
        ON chirps_data_points USING GIST (ST_Point(longitude, latitude));
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_modis_location_gist
        ON modis_data_points USING GIST (ST_Point(longitude, latitude));
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_map_location_gist
        ON map_data_points USING GIST (ST_Point(longitude, latitude));
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_worldpop_location_gist
        ON worldpop_data_points USING GIST (ST_Point(longitude, latitude));
    """
    )


def downgrade() -> None:
    """Drop all tables and extensions."""

    # Drop tables in reverse order
    op.drop_table("malaria_risk_indices")
    op.drop_table("location_time_series")
    op.drop_table("processed_climate_data")
    op.drop_table("worldpop_data_points")
    op.drop_table("map_data_points")
    op.drop_table("modis_data_points")
    op.drop_table("chirps_data_points")
    op.drop_table("era5_data_points")

    # Note: We don't drop extensions as they might be used by other databases
    # op.execute("DROP EXTENSION IF EXISTS postgis")
    # op.execute("DROP EXTENSION IF EXISTS timescaledb")
