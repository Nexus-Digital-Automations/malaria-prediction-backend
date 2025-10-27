# ERA5 Climate Data Integration

> **Copernicus ERA5 reanalysis climate data**

## Overview

ERA5 provides hourly climate data at 0.25° resolution globally.

**Variables Used**:
- 2m temperature (mean, min, max)
- Relative humidity
- Surface pressure
- 10m wind components (U, V)
- Total precipitation

## Setup

### 1. Register for API Access

1. Visit: https://cds.climate.copernicus.eu/user/register
2. Accept terms and conditions
3. Get API key from: https://cds.climate.copernicus.eu/api-how-to

### 2. Configure Credentials

```bash
# .env file
ECMWF_API_KEY="your-api-key-here"
ECMWF_API_URL="https://cds.climate.copernicus.eu/api/v2"
```

### 3. Install Client

```bash
pip install cdsapi
```

## Usage

### Fetch Historical Data

```python
from src.malaria_predictor.services.era5_client import ERA5Client

# Initialize client
era5 = ERA5Client(
    api_key=os.getenv('ECMWF_API_KEY'),
    api_url=os.getenv('ECMWF_API_URL')
)

# Fetch data
data = era5.get_historical_data(
    variables=['2m_temperature', 'relative_humidity', 'total_precipitation'],
    bounds=(-5, 34, 5, 42),  # (south, west, north, east)
    start_date='2024-01-01',
    end_date='2024-01-31',
    time_resolution='daily'  # or 'hourly'
)

# Returns: xarray.Dataset with shape (time, lat, lon)
```

### Aggregate to Daily

```python
# ERA5 is hourly by default - aggregate to daily
daily_data = data.resample(time='1D').mean()

# Or use built-in method
daily_data = era5.get_daily_data(
    variables=['2m_temperature'],
    bounds=(-5, 34, 5, 42),
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

## Data Format

```python
<xarray.Dataset>
Dimensions:    (time: 31, latitude: 40, longitude: 32)
Coordinates:
  * time       (time) datetime64[ns] 2024-01-01 ... 2024-01-31
  * latitude   (latitude) float64 -5.0 -4.75 -4.5 ... 4.5 4.75 5.0
  * longitude  (longitude) float64 34.0 34.25 34.5 ... 41.5 41.75 42.0
Data variables:
    t2m        (time, latitude, longitude) float32 ...  # Temperature (K)
    rh         (time, latitude, longitude) float32 ...  # Humidity (%)
    tp         (time, latitude, longitude) float32 ...  # Precipitation (m)
```

## Rate Limits

- **Requests**: 20 per hour
- **Data volume**: 100 GB per request
- **Queue**: Requests are queued and processed asynchronously

## Best Practices

```python
# Cache results to avoid repeated downloads
import functools
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=86400)  # 24-hour cache

@functools.lru_cache(maxsize=100)
def fetch_era5_cached(start_date, end_date):
    return era5.get_data(start_date=start_date, end_date=end_date)
```

---

**Last Updated**: October 27, 2025
