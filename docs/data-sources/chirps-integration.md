# CHIRPS Rainfall Data Integration

> **Climate Hazards Group InfraRed Precipitation with Station data**

## Overview

CHIRPS provides daily rainfall data at 0.05° resolution (50°S-50°N).

**Coverage**: Global quasi-global (50°S-50°N)
**Resolution**: 0.05° (~5km)
**Frequency**: Daily
**Latency**: ~2 days

## Setup

No API key required - data is publicly available.

```bash
# Install CHIRPS client
pip install requests netCDF4
```

## Usage

### Fetch Rainfall Data

```python
from src.malaria_predictor.services.chirps_client import CHIRPSClient

# Initialize
chirps = CHIRPSClient()

# Fetch data
rainfall = chirps.get_rainfall_data(
    bounds=(-5, 34, 5, 42),
    start_date='2024-01-01',
    end_date='2024-01-31',
    format='netcdf'  # or 'geotiff'
)

# Returns: xarray.Dataset with precipitation (mm/day)
```

### Calculate Monthly Totals

```python
# Sum daily rainfall to monthly
monthly_rainfall = rainfall.resample(time='1M').sum()

# Or use rolling windows
rainfall_7d = rainfall.rolling(time=7).sum()  # 7-day total
rainfall_30d = rainfall.rolling(time=30).sum()  # 30-day total
```

## Data Sources

CHIRPS data available from:
1. **UCSB Climate Hazards Center**: https://data.chc.ucsb.edu/products/CHIRPS-2.0/
2. **IRI Data Library**: https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/

## Data Format

```python
<xarray.Dataset>
Dimensions:        (time: 31, latitude: 200, longitude: 160)
Coordinates:
  * time           (time) datetime64[ns] 2024-01-01 ... 2024-01-31
  * latitude       (latitude) float64 -5.0 -4.95 ... 4.95 5.0
  * longitude      (longitude) float64 34.0 34.05 ... 41.95 42.0
Data variables:
    precipitation  (time, latitude, longitude) float32 ...  # mm/day
```

## Quality Flags

CHIRPS data includes quality indicators:
- **0**: No data
- **1-255**: Precipitation (mm/day * 100)

```python
# Filter invalid data
rainfall_clean = rainfall.where(rainfall > 0)
```

---

**Last Updated**: October 27, 2025
