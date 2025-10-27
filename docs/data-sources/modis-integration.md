# MODIS Vegetation Data Integration

> **NASA MODIS satellite vegetation indices**

## Overview

MODIS provides vegetation indices (NDVI, EVI) indicating vegetation health.

**Products Used**:
- MOD13A2: NDVI/EVI at 1km, 16-day composite
- MOD13Q1: NDVI/EVI at 250m, 16-day composite

## Setup

### 1. NASA Earthdata Account

Register at: https://urs.earthdata.nasa.gov/users/new

### 2. Configure Credentials

```bash
# .env
EARTHDATA_USERNAME="your-username"
EARTHDATA_PASSWORD="your-password"
```

## Usage

### Fetch NDVI Data

```python
from src.malaria_predictor.services.modis_client import MODISClient

# Initialize
modis = MODISClient(
    username=os.getenv('EARTHDATA_USERNAME'),
    password=os.getenv('EARTHDATA_PASSWORD')
)

# Fetch NDVI
ndvi = modis.get_ndvi(
    product='MOD13A2',  # 1km resolution
    bounds=(-5, 34, 5, 42),
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Returns: xarray.Dataset with NDVI values [-1, 1]
```

### Interpret Values

| NDVI Range | Interpretation |
|------------|----------------|
| < 0 | Water, clouds, snow |
| 0-0.2 | Bare soil, rock |
| 0.2-0.5 | Sparse vegetation |
| 0.5-0.7 | Moderate vegetation |
| > 0.7 | Dense vegetation |

## Data Format

```python
<xarray.Dataset>
Dimensions:  (time: 2, latitude: 1000, longitude: 800)
Coordinates:
  * time     (time) datetime64[ns] 2024-01-01 2024-01-17
  * latitude (latitude) float64 ...
  * longitude(longitude) float64 ...
Data variables:
    ndvi     (time, latitude, longitude) float32 ...  # [-1, 1]
    evi      (time, latitude, longitude) float32 ...  # [-1, 1]
    quality  (time, latitude, longitude) uint16 ...   # Quality flags
```

## Quality Filtering

```python
# Filter high-quality pixels only
high_quality = ndvi.where(ndvi.quality == 0)  # 0 = best quality
```

---

**Last Updated**: October 27, 2025
