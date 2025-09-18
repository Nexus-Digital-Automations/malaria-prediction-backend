# ERA5 Data Access via Copernicus Climate Data Store (CDS) API
## Comprehensive Implementation Guide for Malaria Prediction Systems

---

## 1. Authentication & Setup

### CDS Account Registration
1. Register at https://cds.climate.copernicus.eu/
2. Accept Terms of Use for each dataset (must be done manually via web interface)
3. Copy your personal access token from the user profile

### API Key Configuration

Create a `.cdsapirc` file in your home directory:

```bash
# ~/.cdsapirc format
url: https://cds.climate.copernicus.eu/api/v2
key: {uid}:{api-key}
```

Example configuration:
```
url: https://cds.climate.copernicus.eu/api/v2
key: 12345:abcd1234-ef56-7890-ghij-klmnopqrstuv
```

### Python Package Installation

```bash
pip install cdsapi
pip install xarray netCDF4 cfgrib  # For data processing
pip install h5netcdf  # Alternative NetCDF engine (often faster)
```

### Alternative Authentication (Programmatic)
```python
import cdsapi

# Method 1: Default configuration file
client = cdsapi.Client()

# Method 2: Explicit credentials
URL = 'https://cds.climate.copernicus.eu/api/v2'
KEY = '12345:your-api-key-here'
client = cdsapi.Client(url=URL, key=KEY)
```

---

## 2. ERA5 Data Catalog for Malaria Prediction

### Key Meteorological Variables

#### Temperature Variables
- **2m temperature**: Surface air temperature (essential for mosquito development)
- **Maximum 2m temperature**: Daily temperature maxima
- **Minimum 2m temperature**: Daily temperature minima
- **Temperature at pressure levels**: Upper air temperature profiles

#### Precipitation Variables
- **Total precipitation**: Total rainfall accumulation
- **Large-scale precipitation**: Stratiform rainfall
- **Convective precipitation**: Thunderstorm rainfall

#### Humidity Variables
- **Relative humidity**: Moisture content (affects mosquito longevity)
- **2m dewpoint temperature**: Moisture indicator
- **Precipitable water vapor (PWV)**: Total atmospheric water content

#### Additional Relevant Variables
- **10m wind components**: Wind speed and direction
- **Surface pressure**: Atmospheric pressure
- **Soil moisture**: Land surface wetness
- **Evaporation**: Water cycle component

### Temporal Resolutions
- **Hourly**: 1-hour intervals (most detailed)
- **Daily**: Aggregated daily values
- **Monthly**: Long-term climatological analysis

### Spatial Resolution
- **Grid Resolution**: 0.25° × 0.25° (approximately 31 km)
- **Uncertainty Estimates**: 0.5° × 0.5° grid
- **Vertical Levels**: 137 levels from surface to 80 km altitude

### Data Availability
- **Historical Coverage**: 1940 to present
- **Operational Updates**: Near real-time (within 3-5 days)
- **Geographic Coverage**: Global
- **Africa Performance**: Improved representation over previous reanalyses

---

## 3. API Usage Patterns & Restrictions

### Rate Limits and Quotas

#### Field Limits
- **ERA5 Hourly Data**: Maximum 120,000 fields per request
- **ERA5 Monthly Data**: Maximum 10,000 fields per request
- **ERA5-Land Data**: Maximum 1,000 items per request

#### Request Queuing
- CDS queues requests that exceed resource limits
- Processing times vary significantly based on data location:
  - **CDS Disks**: Fast retrieval (minutes to hours)
  - **MARS Tape Archive**: Slow retrieval (hours to days)

### Data Storage Locations

#### Fast Access (CDS Disks)
- Standard ERA5 single levels dataset
- ERA5 pressure levels dataset
- Common variables readily available

#### Slow Access (MARS Archive)
- ERA5 complete dataset
- Historical deep archive data
- Specialized variables

### Best Practices for API Usage

#### Request Optimization
```python
# Good: Small, focused requests
client.retrieve('reanalysis-era5-single-levels', {
    'product_type': 'reanalysis',
    'variable': ['2m_temperature'],
    'year': '2023',
    'month': '01',
    'day': ['01', '02', '03'],  # Few specific days
    'time': ['00:00', '12:00'],
    'area': [10, -20, -10, 30],  # Africa subset
    'format': 'netcdf',
}, 'temperature_jan2023.nc')

# Bad: Large, unfocused requests
# Don't request entire years of hourly data in single API call
```

#### Efficient Bulk Downloads
```python
# Download one month at a time for large datasets
import calendar

def download_monthly_era5(year, variables, area):
    for month in range(1, 13):
        days_in_month = calendar.monthrange(year, month)[1]
        days = [f"{day:02d}" for day in range(1, days_in_month + 1)]

        client.retrieve('reanalysis-era5-single-levels', {
            'product_type': 'reanalysis',
            'variable': variables,
            'year': str(year),
            'month': f"{month:02d}",
            'day': days,
            'time': [f"{hour:02d}:00" for hour in range(0, 24)],
            'area': area,
            'format': 'netcdf',
        }, f'era5_{year}_{month:02d}.nc')
```

### Error Handling and Retry Strategies

```python
import time
import logging
from cdsapi.api import APIException

def robust_era5_download(request_params, output_file, max_retries=3):
    """Robust ERA5 download with retry mechanism"""
    client = cdsapi.Client()

    for attempt in range(max_retries):
        try:
            client.retrieve('reanalysis-era5-single-levels',
                          request_params, output_file)
            logging.info(f"Successfully downloaded {output_file}")
            return True

        except APIException as e:
            if "Request too large" in str(e):
                logging.error(f"Request too large: {e}")
                return False
            elif attempt < max_retries - 1:
                wait_time = 2 ** attempt * 60  # Exponential backoff
                logging.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                logging.error(f"All {max_retries} attempts failed: {e}")
                return False

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(60)
            else:
                return False

    return False
```

---

## 4. Data Formats & Processing

### Format Comparison

#### GRIB Format
- **Advantages**: Smallest file size, meteorological standard
- **File Size**: Most compact (baseline)
- **Use Case**: Operational meteorology, tape storage

#### NetCDF4 Format
- **Advantages**: Self-describing, Python-friendly, better metadata
- **File Size**: ~3x larger than GRIB (uncompressed), similar with compression
- **Compression**: Use `complevel=9` for best compression
- **Use Case**: Research applications, data analysis

### File Size Expectations

```python
# Typical file sizes for 1 month of Africa region data
# Temperature at hourly resolution:
# - GRIB: ~30-50 MB
# - NetCDF4 uncompressed: ~150-200 MB
# - NetCDF4 compressed: ~40-60 MB
```

### Processing Libraries

#### Primary Tools
```python
import xarray as xr
import netCDF4
import cfgrib  # For GRIB files
import h5netcdf  # Alternative NetCDF engine
```

#### GRIB File Processing
```python
# Open GRIB files with xarray
ds = xr.open_dataset('era5_data.grib', engine='cfgrib')

# Convert GRIB to NetCDF
ds.to_netcdf('era5_data.nc',
             encoding={'temperature': {'zlib': True, 'complevel': 9}})
```

#### NetCDF File Processing
```python
# Standard xarray approach
ds = xr.open_dataset('era5_data.nc')

# Faster alternative engine
ds = xr.open_dataset('era5_data.nc', engine='h5netcdf')

# Multiple files
ds = xr.open_mfdataset('era5_*.nc', combine='by_coords')
```

### Coordinate Systems

#### ERA5 Grid Specifications
- **Coordinate System**: Regular latitude-longitude grid
- **Latitude Range**: 90° to -90° (North to South)
- **Longitude Range**: 0° to 359.75° (East, 0-360° format)
- **Resolution**: 0.25° spacing

#### Geographic Subsetting for Africa
```python
# Africa bounding box
africa_bounds = {
    'north': 40,    # Northern boundary
    'south': -35,   # Southern boundary
    'west': -25,    # Western boundary
    'east': 55      # Eastern boundary
}

# CDS API area format: [North, West, South, East]
africa_area = [40, -25, -35, 55]
```

---

## 5. Implementation Examples

### Basic Temperature Download (Africa)
```python
import cdsapi

client = cdsapi.Client()

# Download daily temperature data for Africa
client.retrieve('reanalysis-era5-single-levels', {
    'product_type': 'reanalysis',
    'variable': [
        '2m_temperature',
        'maximum_2m_temperature_since_previous_post_processing',
        'minimum_2m_temperature_since_previous_post_processing'
    ],
    'year': '2023',
    'month': ['01', '02', '03'],
    'day': [f"{day:02d}" for day in range(1, 32)],
    'time': ['00:00'],  # Once daily for min/max
    'area': [40, -25, -35, 55],  # Africa
    'format': 'netcdf',
}, 'africa_temperature_q1_2023.nc')
```

### Precipitation and Humidity Download
```python
# Download precipitation and humidity data
client.retrieve('reanalysis-era5-single-levels', {
    'product_type': 'reanalysis',
    'variable': [
        'total_precipitation',
        '2m_dewpoint_temperature',
        'relative_humidity'
    ],
    'pressure_level': '1000',  # For relative humidity
    'year': '2023',
    'month': '06',  # Rainy season
    'day': [f"{day:02d}" for day in range(1, 31)],
    'time': ['00:00', '06:00', '12:00', '18:00'],
    'area': [15, -20, -10, 45],  # Sub-Saharan Africa
    'format': 'netcdf',
}, 'africa_precip_humidity_jun2023.nc')
```

### Multi-Variable Batch Processing
```python
import concurrent.futures
from datetime import datetime, timedelta
import logging

class ERA5MalariaDownloader:
    def __init__(self):
        self.client = cdsapi.Client()
        self.africa_area = [40, -25, -35, 55]

    def download_monthly_data(self, year, month, variables):
        """Download one month of data for specified variables"""
        days_in_month = calendar.monthrange(year, month)[1]
        days = [f"{day:02d}" for day in range(1, days_in_month + 1)]

        request = {
            'product_type': 'reanalysis',
            'variable': variables,
            'year': str(year),
            'month': f"{month:02d}",
            'day': days,
            'time': ['00:00', '06:00', '12:00', '18:00'],
            'area': self.africa_area,
            'format': 'netcdf',
        }

        output_file = f'era5_malaria_{year}_{month:02d}.nc'

        try:
            self.client.retrieve('reanalysis-era5-single-levels',
                               request, output_file)
            logging.info(f"Downloaded {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Failed to download {output_file}: {e}")
            return None

    def bulk_download(self, start_year, end_year):
        """Download multiple years of malaria-relevant ERA5 data"""
        variables = [
            '2m_temperature',
            'maximum_2m_temperature_since_previous_post_processing',
            'minimum_2m_temperature_since_previous_post_processing',
            'total_precipitation',
            '2m_dewpoint_temperature',
            '2m_relative_humidity'
        ]

        tasks = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                tasks.append((year, month, variables))

        # Sequential processing to respect API limits
        for year, month, vars in tasks:
            self.download_monthly_data(year, month, vars)
            time.sleep(10)  # Rate limiting

# Usage
downloader = ERA5MalariaDownloader()
downloader.bulk_download(2020, 2023)
```

### Async Data Processing Pipeline
```python
import asyncio
import xarray as xr
import pandas as pd
from pathlib import Path

class ERA5MalariaProcessor:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    async def process_temperature_data(self, file_path):
        """Process temperature data for malaria modeling"""
        ds = xr.open_dataset(file_path)

        # Calculate daily temperature statistics
        daily_stats = ds.resample(time='1D').agg({
            't2m': ['mean', 'min', 'max'],
            'tp': 'sum',
            'd2m': 'mean'
        })

        # Convert to DataFrame for analysis
        df = daily_stats.to_dataframe()
        return df

    async def batch_process_files(self, file_pattern="era5_malaria_*.nc"):
        """Process multiple ERA5 files concurrently"""
        files = list(self.data_dir.glob(file_pattern))

        tasks = []
        for file_path in files:
            task = self.process_temperature_data(file_path)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        valid_results = [r for r in results if isinstance(r, pd.DataFrame)]
        combined_df = pd.concat(valid_results, ignore_index=True)

        return combined_df

# Usage
async def main():
    processor = ERA5MalariaProcessor('/path/to/era5/data')
    malaria_data = await processor.batch_process_files()
    malaria_data.to_csv('processed_malaria_climate_data.csv')

# asyncio.run(main())
```

---

## 6. Production Considerations

### Data Storage Architecture

#### Directory Structure
```
/data/era5/
├── raw/
│   ├── temperature/
│   │   ├── 2020/
│   │   ├── 2021/
│   │   └── 2022/
│   ├── precipitation/
│   └── humidity/
├── processed/
│   ├── daily_aggregates/
│   ├── monthly_summaries/
│   └── malaria_indices/
└── logs/
    ├── downloads/
    └── processing/
```

#### Storage Requirements
```python
# Estimated storage for Africa region malaria data
# Variables: temp, precip, humidity (6 vars total)
# Timespan: 10 years hourly data
# Region: Africa (40N, 25W, 35S, 55E)

storage_estimate = {
    'raw_netcdf_compressed': '~500 GB',
    'processed_daily': '~50 GB',
    'monthly_aggregates': '~5 GB',
    'malaria_indices': '~1 GB'
}
```

### Automated Data Pipeline

```python
import schedule
import time
from datetime import datetime, timedelta
import logging

class ERA5ProductionPipeline:
    def __init__(self, config):
        self.config = config
        self.client = cdsapi.Client()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/data/era5/logs/pipeline.log'),
                logging.StreamHandler()
            ]
        )

    def download_latest_data(self):
        """Download most recent ERA5 data"""
        # ERA5 has ~3-5 day delay
        end_date = datetime.now() - timedelta(days=5)
        start_date = end_date - timedelta(days=7)  # 1 week window

        for date in pd.date_range(start_date, end_date):
            self.download_daily_data(date)

    def download_daily_data(self, date):
        """Download one day of ERA5 data"""
        request = {
            'product_type': 'reanalysis',
            'variable': self.config['variables'],
            'year': str(date.year),
            'month': f"{date.month:02d}",
            'day': f"{date.day:02d}",
            'time': ['00:00', '06:00', '12:00', '18:00'],
            'area': self.config['africa_area'],
            'format': 'netcdf',
        }

        output_file = f"/data/era5/raw/era5_{date.strftime('%Y%m%d')}.nc"

        try:
            self.client.retrieve('reanalysis-era5-single-levels',
                               request, output_file)
            logging.info(f"Downloaded {output_file}")

            # Process immediately after download
            self.process_daily_file(output_file)

        except Exception as e:
            logging.error(f"Download failed for {date}: {e}")

    def process_daily_file(self, file_path):
        """Process downloaded ERA5 file"""
        try:
            ds = xr.open_dataset(file_path)

            # Calculate malaria-relevant indices
            malaria_data = self.calculate_malaria_indices(ds)

            # Save processed data
            output_path = file_path.replace('/raw/', '/processed/')
            malaria_data.to_netcdf(output_path)

            logging.info(f"Processed {file_path}")

        except Exception as e:
            logging.error(f"Processing failed for {file_path}: {e}")

    def calculate_malaria_indices(self, ds):
        """Calculate malaria transmission indices"""
        # Temperature suitability (optimal ~25-30°C)
        temp_c = ds['t2m'] - 273.15  # Convert K to C
        temp_suitability = np.exp(-((temp_c - 27.5) / 10) ** 2)

        # Precipitation accumulation
        precip_mm = ds['tp'] * 1000  # Convert m to mm

        # Humidity index
        humidity_index = ds['d2m'] - 273.15  # Dewpoint in Celsius

        # Combine indices
        malaria_index = temp_suitability * np.tanh(precip_mm / 50)

        return xr.Dataset({
            'temperature_suitability': temp_suitability,
            'precipitation_mm': precip_mm,
            'humidity_index': humidity_index,
            'malaria_transmission_index': malaria_index
        })

# Production scheduler
config = {
    'variables': [
        '2m_temperature', 'total_precipitation',
        '2m_dewpoint_temperature', '2m_relative_humidity'
    ],
    'africa_area': [40, -25, -35, 55]
}

pipeline = ERA5ProductionPipeline(config)

# Schedule daily updates
schedule.every().day.at("06:00").do(pipeline.download_latest_data)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

### Error Monitoring and Alerts

```python
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class ERA5Monitor:
    def __init__(self, email_config):
        self.email_config = email_config

    def check_data_freshness(self):
        """Check if ERA5 data is up to date"""
        latest_file = self.get_latest_file()
        if not latest_file:
            self.send_alert("No ERA5 files found")
            return False

        file_date = self.extract_date_from_filename(latest_file)
        expected_date = datetime.now() - timedelta(days=5)

        if file_date < expected_date:
            self.send_alert(f"ERA5 data is stale. Latest: {file_date}")
            return False

        return True

    def check_download_failures(self):
        """Check for recent download failures"""
        with open('/data/era5/logs/pipeline.log', 'r') as f:
            recent_logs = f.readlines()[-100:]  # Last 100 lines

        error_count = sum(1 for line in recent_logs if 'ERROR' in line)

        if error_count > 5:
            self.send_alert(f"High error rate: {error_count} errors in recent logs")

    def send_alert(self, message):
        """Send email alert"""
        msg = MimeMultipart()
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']
        msg['Subject'] = "ERA5 Pipeline Alert"

        body = f"ERA5 Data Pipeline Alert:\n\n{message}"
        msg.attach(MimeText(body, 'plain'))

        with smtplib.SMTP(self.email_config['smtp_server'], 587) as server:
            server.starttls()
            server.login(self.email_config['username'],
                        self.email_config['password'])
            server.send_message(msg)

# Run monitoring checks
monitor = ERA5Monitor(email_config)
schedule.every().hour.do(monitor.check_data_freshness)
schedule.every().hour.do(monitor.check_download_failures)
```

### Performance Optimization Techniques

#### Memory-Efficient Processing
```python
def process_large_era5_dataset(file_paths, chunk_size='100MB'):
    """Process large ERA5 datasets with memory efficiency"""
    # Use dask for lazy loading
    import dask.array as da

    datasets = []
    for file_path in file_paths:
        ds = xr.open_dataset(file_path, chunks={'time': 24})  # Daily chunks
        datasets.append(ds)

    # Concatenate along time dimension
    combined = xr.concat(datasets, dim='time')

    # Process in chunks
    result = combined.groupby('time.month').mean()

    # Compute and save
    result.to_netcdf('monthly_climatology.nc')
```

#### Parallel Processing
```python
from multiprocessing import Pool
import functools

def process_single_file(file_path, processing_func):
    """Process single ERA5 file"""
    return processing_func(file_path)

def parallel_era5_processing(file_paths, processing_func, n_workers=4):
    """Process multiple ERA5 files in parallel"""
    partial_func = functools.partial(process_single_file,
                                   processing_func=processing_func)

    with Pool(n_workers) as pool:
        results = pool.map(partial_func, file_paths)

    return results
```

---

## Key Implementation Summary

### Critical Setup Steps
1. **Account Setup**: Register at CDS, configure `.cdsapirc`
2. **Accept Terms**: Manually accept dataset terms via web interface
3. **Install Dependencies**: `pip install cdsapi xarray netCDF4 cfgrib`
4. **Test Connection**: Verify API access with simple request

### Essential Variables for Malaria Prediction
- **2m_temperature**: Primary vector development indicator
- **total_precipitation**: Breeding site availability
- **2m_dewpoint_temperature**: Humidity/moisture content
- **2m_relative_humidity**: Mosquito survival conditions

### Production Best Practices
- **Small Requests**: Download monthly chunks, not yearly datasets
- **Error Handling**: Implement retry logic with exponential backoff
- **Rate Limiting**: Respect API quotas, add delays between requests
- **Monitoring**: Track data freshness and download failures
- **Storage**: Organize by variable, year, and processing level

### Performance Considerations
- **Format Choice**: NetCDF4 with compression for analysis, GRIB for storage
- **Memory Management**: Use chunked processing for large datasets
- **Parallel Processing**: Process multiple files concurrently
- **Caching**: Store processed derivatives to avoid recomputation

This comprehensive guide provides the foundation for building a robust, production-ready ERA5 data ingestion service specifically tailored for malaria prediction applications.
