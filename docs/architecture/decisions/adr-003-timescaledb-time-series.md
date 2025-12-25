# ADR-003: TimescaleDB for Time-Series Data

## Status
Accepted

## Context

The system needs to store and query large volumes of time-series environmental data:
- Temperature, humidity, precipitation readings (hourly/daily)
- Vegetation indices from satellite imagery (weekly)
- Population density data (annual)
- Historical malaria incidence data (daily/weekly)

Requirements:
- Efficient time-range queries for ML training data
- High write throughput for data ingestion
- Automatic data retention and compression
- PostgreSQL compatibility for existing tooling
- Geospatial query support

Options considered:
1. **InfluxDB** - Purpose-built for time-series, but different query language
2. **PostgreSQL** - Standard SQL, but not optimized for time-series
3. **TimescaleDB** - PostgreSQL extension with time-series optimization
4. **Apache Cassandra** - Highly scalable, but complex operations

## Decision

We chose **TimescaleDB** as our time-series database:

1. **PostgreSQL Compatibility**: Full SQL support with existing PostgreSQL ecosystem (SQLAlchemy, psycopg2, asyncpg)

2. **Hypertables**: Automatic partitioning of time-series data for query performance

3. **Continuous Aggregates**: Materialized views that auto-update, perfect for dashboards

4. **Compression**: Native compression achieving 90%+ space savings

5. **PostGIS Integration**: Combined with PostGIS for geospatial queries on environmental data

### Schema Design

```sql
-- Environmental data hypertable
CREATE TABLE environmental_data (
    time        TIMESTAMPTZ NOT NULL,
    location_id UUID NOT NULL,
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    humidity    DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    ndvi        DOUBLE PRECISION,
    -- Additional columns...
);

SELECT create_hypertable('environmental_data', 'time');

-- Continuous aggregate for daily summaries
CREATE MATERIALIZED VIEW daily_environmental_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    location_id,
    AVG(temperature) as avg_temp,
    SUM(precipitation) as total_precip
FROM environmental_data
GROUP BY day, location_id;
```

## Consequences

### Positive
- Seamless integration with existing PostgreSQL infrastructure
- Familiar SQL interface for data scientists and developers
- Excellent query performance for time-range queries
- Automatic data lifecycle management (compression, retention)
- Strong geospatial support with PostGIS extension

### Negative
- Additional extension to manage
- Some features require TimescaleDB-specific SQL
- Scaling beyond single node requires TimescaleDB Cloud or manual setup
- Memory requirements for hypertables with many chunks

### Mitigations
- Proper chunk interval tuning based on query patterns
- Data retention policies to manage storage growth
- Connection pooling with PgBouncer for high concurrency
- Regular ANALYZE and VACUUM scheduling

## References

- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Database Schema Documentation](../../data-sources/overview.md)
- [Data Quality Validation](../../data-sources/data-quality-validation.md)
