# CHIRPS Rainfall Data Access Research

## Overview
CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) is a 40+ year quasi-global rainfall dataset combining satellite imagery with in-situ station data to create gridded rainfall time series for trend analysis and seasonal drought monitoring.

## Data Sources and Access Methods

### 1. Primary Data Portal
- **Website**: https://data.chc.ucsb.edu/products/CHIRPS-2.0/
- **Institution**: Climate Hazards Center, UC Santa Barbara
- **Access Method**: HTTP/FTP direct downloads
- **Authentication**: None required (open access)

### 2. FTP Server Access
```
ftp://ftp.chc.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/
```

### 3. Alternative Access Points
- **Google Earth Engine**: UCSB-CHG/CHIRPS/DAILY and UCSB-CHG/CHIRPS/PENTAD
- **IRI Data Library**: http://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/
- **THREDDS Server**: https://thredds.chc.ucsb.edu/thredds/catalog/ucsb_chg/chirps/

## Data Formats and Structures

### Available Formats
1. **GeoTIFF (.tif)**
   - Most common format for individual daily/monthly files
   - Georeferenced raster data
   - Single-band precipitation values
   - Compression: LZW

2. **NetCDF (.nc)**
   - Available for aggregated time series
   - CF-compliant metadata
   - Multiple time steps in single file

3. **BIL (Band Interleaved by Line)**
   - Binary format with header file
   - Efficient for large-scale processing
   - Requires accompanying .hdr file

### Data Structure
```
CHIRPS-2.0/
├── global_daily/
│   └── tifs/
│       └── p05/
│           └── {year}/
│               └── chirps-v2.0.{year}.{month}.{day}.tif
├── global_pentad/
├── global_dekad/
├── global_monthly/
│   └── tifs/
│       └── chirps-v2.0.{year}.{month}.tif
└── global_annual/
```

## Temporal and Spatial Characteristics

### Temporal Resolution
- **Daily**: 1981-present, ~2-3 day latency
- **Pentad** (5-day): Aggregated from daily
- **Dekad** (10-day): Aggregated from daily
- **Monthly**: Aggregated from daily
- **Annual**: Aggregated from monthly

### Spatial Resolution
- **Resolution**: 0.05° × 0.05° (approximately 5.5 km at equator)
- **Coverage**: 50°S-50°N, all longitudes
- **Grid**: 7200 × 2000 pixels (global)
- **Projection**: Geographic (WGS84)

### Africa-Specific Coverage
- **Bounds**: 40°N to 35°S, 20°W to 55°E
- **Grid cells**: ~1200 × 1500 for Africa subset
- **File size**: ~3-5 MB per daily file (Africa subset)

## Download Automation Approaches

### 1. Direct HTTP Download
```python
import requests
from datetime import date, timedelta

def download_chirps_daily(target_date: date, output_path: str):
    base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05"
    filename = f"chirps-v2.0.{target_date.year}.{target_date.month:02d}.{target_date.day:02d}.tif"
    url = f"{base_url}/{target_date.year}/{filename}"

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
```

### 2. Bulk Download via wget/curl
```bash
# Download entire month
wget -r -np -nH --cut-dirs=5 -A "chirps-v2.0.2023.10.*.tif" \
  https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/2023/
```

### 3. Python Libraries
- **chirps**: Unofficial Python package for CHIRPS data access
- **pydap**: For OPeNDAP access to THREDDS server
- **earthengine-api**: For Google Earth Engine access

## Data Processing Workflows

### 1. Single File Processing
```python
import rasterio
import numpy as np

def extract_africa_rainfall(chirps_file: str, bounds: tuple) -> np.ndarray:
    """Extract Africa subset from global CHIRPS file"""
    with rasterio.open(chirps_file) as src:
        # Define Africa window
        window = rasterio.windows.from_bounds(
            *bounds,  # (west, south, east, north)
            transform=src.transform
        )
        # Read data for Africa region
        rainfall_data = src.read(1, window=window)
        # Replace no-data values
        rainfall_data[rainfall_data < 0] = np.nan
        return rainfall_data
```

### 2. Time Series Aggregation
```python
def aggregate_to_monthly(daily_files: list) -> np.ndarray:
    """Aggregate daily CHIRPS files to monthly total"""
    monthly_sum = None
    valid_days = 0

    for file_path in daily_files:
        daily_data = extract_africa_rainfall(file_path, africa_bounds)
        if monthly_sum is None:
            monthly_sum = np.zeros_like(daily_data)

        # Add daily rainfall (handling NaN)
        valid_mask = ~np.isnan(daily_data)
        monthly_sum[valid_mask] += daily_data[valid_mask]
        valid_days += 1

    return monthly_sum
```

### 3. Data Validation
```python
def validate_chirps_data(file_path: str) -> dict:
    """Validate CHIRPS data file"""
    with rasterio.open(file_path) as src:
        return {
            'valid': True,
            'crs': src.crs.to_string(),
            'bounds': src.bounds,
            'resolution': src.res,
            'nodata': src.nodata,
            'min_value': src.read(1).min(),
            'max_value': src.read(1).max(),
            'has_data': (src.read(1) >= 0).any()
        }
```

## Production Implementation Strategy

### 1. Data Pipeline Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  CHIRPS Server  │────▶│  Download Worker │────▶│ Validation     │
└─────────────────┘     └──────────────────┘     └────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│    Database     │◀────│   Data Loader    │◀────│  Processing    │
└─────────────────┘     └──────────────────┘     └────────────────┘
```

### 2. Key Implementation Considerations

#### Performance Optimization
- **Parallel downloads**: Use asyncio/aiohttp for concurrent downloads
- **Chunked processing**: Process large files in memory-efficient chunks
- **Caching**: Local cache of frequently accessed data
- **CDN usage**: Prefer regional mirrors when available

#### Reliability
- **Retry logic**: Exponential backoff for failed downloads
- **Checksum validation**: Verify file integrity
- **Fallback sources**: Alternative data sources (FTP, THREDDS)
- **Monitoring**: Track download success rates and latency

#### Storage Strategy
- **Raw data**: Keep original CHIRPS files for 30-90 days
- **Processed data**: Store Africa-subset in optimized format
- **Compression**: Use Cloud-Optimized GeoTIFF (COG) format
- **Archival**: Monthly aggregates to cold storage

### 3. Integration with Existing System

#### Database Schema
```sql
CREATE TABLE chirps_rainfall_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    rainfall_mm FLOAT,
    data_quality SMALLINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, latitude, longitude)
);

-- TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('chirps_rainfall_data', 'date');
```

#### Service Implementation
```python
class CHIRPSClient:
    def __init__(self, settings: Settings):
        self.base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
        self.africa_bounds = (-20, -35, 55, 40)  # W, S, E, N

    async def download_rainfall_data(
        self,
        start_date: date,
        end_date: date
    ) -> CHIRPSDownloadResult:
        """Download CHIRPS rainfall data for date range"""
        # Implementation details...

    def validate_rainfall_file(self, file_path: Path) -> bool:
        """Validate downloaded CHIRPS file"""
        # Implementation details...
```

### 4. Automation Schedule
- **Daily updates**: Download previous day's data at 10:00 UTC
- **Weekly validation**: Verify last 7 days of data completeness
- **Monthly aggregation**: Create monthly summaries on day 3
- **Quarterly cleanup**: Remove raw files older than 90 days

## API Rate Limits and Best Practices

### Access Patterns
- **No authentication required**: Open access data
- **No formal rate limits**: But be respectful
- **Recommended**: Max 10 concurrent connections
- **Bulk downloads**: Use off-peak hours (night US Pacific time)

### Best Practices
1. **User-Agent**: Set descriptive user agent string
2. **Compression**: Accept gzip encoding for transfers
3. **Partial downloads**: Use HTTP range requests for large files
4. **Error handling**: Implement robust retry logic
5. **Monitoring**: Track bandwidth usage and adjust accordingly

## Summary and Recommendations

### Key Advantages
- Free and open access data
- Long historical record (1981-present)
- Regular updates with low latency
- Multiple resolutions available
- Well-documented and widely used

### Implementation Priority
1. Start with monthly data for initial development
2. Add daily data once pipeline is stable
3. Implement near-real-time updates for operational use
4. Consider pentad/dekad for specific use cases

### Next Steps
1. Implement CHIRPSClient class following ERA5Client pattern
2. Add rainfall-specific data validation
3. Create data processing pipeline for malaria risk factors
4. Integrate with existing database schema
5. Add CLI commands for CHIRPS data management
