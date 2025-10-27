# Environmental Data Sources Overview

> **80+ environmental data sources for malaria prediction**

## Data Pipeline Architecture

```
Data Sources → Ingestion → Validation → Harmonization → Feature Extraction → ML Models
```

## Primary Data Sources

| Source | Data Type | Spatial Resolution | Temporal Resolution | Coverage |
|--------|-----------|-------------------|---------------------|----------|
| **ERA5** | Climate (temp, humidity, wind) | 0.25° (~25km) | Hourly | Global |
| **CHIRPS** | Rainfall | 0.05° (~5km) | Daily | 50°S-50°N |
| **MODIS** | Vegetation (NDVI, EVI) | 250m-1km | 8-day, 16-day | Global |
| **MAP** | Malaria prevalence | Variable | Annual | Malaria-endemic regions |
| **WorldPop** | Population density | 100m | Annual | Global |

## Data Flow

```python
# Typical data ingestion workflow
from src.malaria_predictor.services import (
    ERA5Client, CHIRPSClient, MODISClient,
    MAPClient, WorldPopClient
)

# 1. Initialize clients
era5 = ERA5Client(api_key=os.getenv('ECMWF_API_KEY'))
chirps = CHIRPSClient()
modis = MODISClient()

# 2. Fetch data
climate_data = era5.get_data(
    variables=['temperature_2m', 'relative_humidity'],
    bounds=(-5, 34, 5, 42),  # East Africa
    start_date='2024-01-01',
    end_date='2024-01-31'
)

rainfall_data = chirps.get_rainfall(
    bounds=(-5, 34, 5, 42),
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# 3. Harmonize (align spatially and temporally)
from src.malaria_predictor.services.data_harmonizer import DataHarmonizer

harmonizer = DataHarmonizer()
aligned_data = harmonizer.harmonize(
    [climate_data, rainfall_data, modis_data],
    target_resolution='0.1 degrees',
    target_frequency='daily'
)

# 4. Extract features
features = extract_features(aligned_data)

# 5. Store in TimescaleDB
store_features(features)
```

## API Credentials Required

### ERA5 (ECMWF)
```bash
export ECMWF_API_KEY="your-api-key"
export ECMWF_API_URL="https://cds.climate.copernicus.eu/api/v2"
```

Registration: https://cds.climate.copernicus.eu/user/register

### NASA Earthdata (for MODIS)
```bash
export EARTHDATA_USERNAME="your-username"
export EARTHDATA_PASSWORD="your-password"
```

Registration: https://urs.earthdata.nasa.gov/users/new

### Google Earth Engine (optional)
```bash
export GEE_SERVICE_ACCOUNT="your-service-account@project.iam.gserviceaccount.com"
export GEE_PRIVATE_KEY_FILE="/path/to/private-key.json"
```

Setup: https://developers.google.com/earth-engine/guides/service_account

## Data Storage

### TimescaleDB Schema

```sql
CREATE TABLE environmental_data (
    time TIMESTAMPTZ NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    temperature_mean REAL,
    temperature_min REAL,
    temperature_max REAL,
    rainfall_mm REAL,
    humidity_percent REAL,
    ndvi REAL,
    evi REAL,
    population_density REAL
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('environmental_data', 'time');

-- Add spatial index
CREATE INDEX idx_location ON environmental_data USING GIST(location);
```

## Data Update Frequency

| Source | Update Schedule | Automated? | Lag Time |
|--------|----------------|------------|----------|
| ERA5 | Daily | Yes (cron) | 5 days |
| CHIRPS | Daily | Yes (cron) | 2 days |
| MODIS | 8 days | Yes (cron) | 3 days |
| MAP | Annually | Manual | Variable |
| WorldPop | Annually | Manual | Variable |

## Cron Jobs

```bash
# /etc/cron.d/malaria-data-ingestion

# ERA5 - Daily at 02:00 UTC
0 2 * * * /app/scripts/ingest_era5.sh >> /var/log/era5.log 2>&1

# CHIRPS - Daily at 03:00 UTC
0 3 * * * /app/scripts/ingest_chirps.sh >> /var/log/chirps.log 2>&1

# MODIS - Every 8 days at 04:00 UTC
0 4 */8 * * /app/scripts/ingest_modis.sh >> /var/log/modis.log 2>&1
```

## Data Quality Checks

```python
def validate_data(data):
    """Validate environmental data quality."""
    checks = {
        'completeness': check_completeness(data),
        'consistency': check_consistency(data),
        'plausibility': check_plausibility(data),
        'timeliness': check_timeliness(data)
    }

    if not all(checks.values()):
        raise DataQualityError(f"Quality checks failed: {checks}")

    return data
```

## Further Reading

- [ERA5 Integration](./era5-integration.md)
- [CHIRPS Integration](./chirps-integration.md)
- [MODIS Integration](./modis-integration.md)
- [MAP Integration](./map-integration.md)
- [WorldPop Integration](./worldpop-integration.md)
- [Data Quality Validation](./data-quality-validation.md)
- [Troubleshooting](./troubleshooting.md)

---

**Last Updated**: October 27, 2025
