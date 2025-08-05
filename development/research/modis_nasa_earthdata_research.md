# MODIS NASA EarthData Access Research

## Executive Summary

**Research Question**: How to access MODIS vegetation indices (NDVI/EVI) data through NASA EarthData for malaria prediction applications?

**Recommendation**: Implement a comprehensive MODIS data pipeline using the NASA earthaccess Python library with MOD13Q1/MYD13Q1 products at 250m resolution for vegetation monitoring in malaria-endemic regions.

**Key Findings**:
- NASA EarthData migration to unified platform ongoing through 2026
- Version 6.1 products now recommended (Version 6 decommissioned July 2023)
- earthaccess library provides streamlined authentication and data access
- 16-day composite products at 250m resolution optimal for malaria applications
- HDF4 and NetCDF formats with comprehensive quality flags available

**Implementation Timeline**: 2-3 weeks for full pipeline development

**Estimated Cost**: Minimal - free NASA EarthData account, compute resources for processing

## NASA EarthData Portal Overview and Authentication (EDL)

### NASA EarthData Login (EDL) System

NASA's Earthdata Login (EDL) provides a single sign-on authentication system for accessing NASA's Earth science data and applications. As of 2025, NASA is migrating all Earth science data sites into the unified Earthdata platform, with completion expected by end of 2026.

#### Account Requirements
- **Free Registration**: Open a free account at https://urs.earthdata.nasa.gov/
- **Global Access**: No restrictions on institutional affiliation
- **Multiple Authentication Methods**: Support for credentials, tokens, and .netrc files

#### Authentication Methods

1. **Credential-based Authentication**
   ```python
   import earthaccess

   # Interactive login
   auth = earthaccess.login()

   # Manual credentials
   auth = earthaccess.login(username="your_username", password="your_password")
   ```

2. **Environment Variables**
   ```bash
   export EARTHDATA_USERNAME="your_username"
   export EARTHDATA_PASSWORD="your_password"
   # OR
   export EARTHDATA_TOKEN="your_token"
   ```

3. **NetRC File Authentication**
   ```bash
   # ~/.netrc file format
   machine urs.earthdata.nasa.gov
   login your_username
   password your_password
   ```

4. **Persistent Authentication**
   ```python
   # Save credentials for future use
   auth = earthaccess.login(persist=True)
   ```

#### User Acceptance Testing (UAT)
For authorized users accessing UAT environments:
```python
import earthaccess
auth = earthaccess.login(system=earthaccess.UAT)
```

## MODIS Vegetation Products (MOD13/MYD13) Specifications

### Product Overview

MODIS vegetation indices are produced from atmospherically-corrected surface reflectance and provide consistent spatial and temporal comparisons of vegetation canopy greenness. Two primary satellites provide complementary coverage:

- **Terra MODIS (MOD13)**: Morning overpass (~10:30 AM local time)
- **Aqua MODIS (MYD13)**: Afternoon overpass (~1:30 PM local time)

### Available Products and Resolutions

#### MOD13Q1/MYD13Q1 - 250m Resolution
- **Spatial Resolution**: 250m × 250m
- **Temporal Resolution**: 16-day composites
- **Coverage**: Global
- **Projection**: Sinusoidal (SIN)
- **Recommended for**: Detailed vegetation monitoring, malaria vector habitat analysis

#### MOD13A1/MYD13A1 - 500m Resolution
- **Spatial Resolution**: 500m × 500m
- **Temporal Resolution**: 16-day composites
- **Coverage**: Global
- **Use Case**: Regional vegetation analysis

#### MOD13A2/MYD13A2 - 1km Resolution
- **Spatial Resolution**: 1km × 1km
- **Temporal Resolution**: 16-day composites
- **Coverage**: Global
- **Use Case**: Large-scale ecosystem monitoring

#### MOD13A3/MYD13A3 - Monthly Products
- **Spatial Resolution**: 1km × 1km
- **Temporal Resolution**: Monthly composites
- **Coverage**: Global
- **Use Case**: Seasonal vegetation analysis

#### Climate Modeling Grid (CMG) Products
- **MOD13C1/MYD13C1**: 16-day, 0.05° (~5.6km)
- **MOD13C2/MYD13C2**: Monthly, 0.05° (~5.6km)
- **Projection**: Geographic (lat/lon)
- **Use Case**: Climate modeling, large-scale analysis

### Vegetation Indices Computed

#### Normalized Difference Vegetation Index (NDVI)
- **Formula**: (NIR - Red) / (NIR + Red)
- **Range**: -1.0 to +1.0
- **Characteristics**:
  - Continuity with NOAA-AVHRR record
  - Sensitive to atmospheric effects
  - Standard for vegetation monitoring

#### Enhanced Vegetation Index (EVI)
- **Formula**: G × (NIR - Red) / (NIR + C1 × Red - C2 × Blue + L)
- **Coefficients**: G=2.5, C1=6, C2=7.5, L=1
- **Range**: -1.0 to +1.0
- **Advantages**:
  - Improved sensitivity over high biomass regions
  - Reduced atmospheric and soil background effects
  - Better performance in dense vegetation

### Data Layers

Each MODIS vegetation index product contains multiple Science Data Sets (SDS):

1. **NDVI**: Normalized Difference Vegetation Index
2. **EVI**: Enhanced Vegetation Index
3. **VI Quality**: Vegetation Index Quality Assessment
4. **Red Reflectance**: MODIS Band 1 (620-670 nm)
5. **NIR Reflectance**: MODIS Band 2 (841-876 nm)
6. **Blue Reflectance**: MODIS Band 3 (459-479 nm)
7. **MIR Reflectance**: MODIS Band 7 (2105-2155 nm)
8. **View Zenith Angle**: Sensor view angle
9. **Sun Zenith Angle**: Solar illumination angle
10. **Relative Azimuth Angle**: Relative sensor-sun geometry
11. **Composite Day of Year**: Day of year for selected pixel
12. **Pixel Reliability**: Overall pixel quality assessment

## Data Formats and Processing Tools

### Primary Data Formats

#### HDF4 (Hierarchical Data Format)
- **Native Format**: Original MODIS data format
- **Structure**: Multi-layer hierarchical
- **Metadata**: Comprehensive embedded metadata
- **Tools**: GDAL, rasterio, pyhdf libraries

#### NetCDF4 (.nc4)
- **Modern Format**: NASA's preferred format for new products
- **Advantages**:
  - Better compression
  - Improved metadata structure
  - Native Python support via xarray/netCDF4

#### GeoTIFF (Processed)
- **Converted Format**: Single-band or multi-band GeoTIFF
- **Advantages**: Universal compatibility, direct use in GIS
- **Creation**: Via GDAL translation or custom processing

### Metadata Structure

#### Global Attributes
```python
# Example metadata fields
{
    'ALGORITHMDOI': '10.5067/MODIS/MOD13Q1.061',
    'AUTOMATICQUALITYFLAGS': 'Useful',
    'AUTOMATICQUALITYFLAGSEXPLANATION': 'Cloud/shadow/snow/water/aerosol quantity',
    'SHORTNAME': 'MOD13Q1',
    'VERSIONID': '061',
    'TEMPORALRESOLUTION': '16-day',
    'SPATIALRESOLUTION': '250m',
    'WESTBOUNDINGCOORDINATE': -180.0,
    'EASTBOUNDINGCOORDINATE': 180.0,
    'NORTHBOUNDINGCOORDINATE': 90.0,
    'SOUTHBOUNDINGCOORDINATE': -90.0,
    'STARTTIME': '2023-01-01',
    'ENDTIME': '2023-01-16'
}
```

#### Science Data Set Attributes
```python
# Example SDS metadata
{
    'long_name': 'MODIS 16 day NDVI',
    'units': 'dimensionless',
    'valid_range': [-2000, 10000],
    'scale_factor': 0.0001,
    'add_offset': 0.0,
    '_FillValue': -3000
}
```

## Spatial and Temporal Resolutions

### Spatial Resolution Details

#### 250m Products (MOD13Q1/MYD13Q1)
- **Nominal Resolution**: 250m at nadir
- **Actual Resolution**: Varies with latitude and view angle
- **Grid Size**: 4800 × 4800 pixels per tile
- **Coverage per Tile**: ~1200km × 1200km at equator

#### Sinusoidal Projection
- **EPSG Code**: Custom sinusoidal
- **Characteristics**:
  - Equal-area projection
  - Preserves area measurements
  - Minimal distortion near equator
  - Increasingly distorted towards poles

#### Global Tiling System
```
Horizontal Tiles (h): 0-35 (36 tiles, 10° each)
Vertical Tiles (v): 0-17 (18 tiles, 10° each)
Total Tiles: 648 possible (460 contain land)
Tile Naming: h##v## (e.g., h21v09 for Central Africa)
```

### Temporal Resolution Characteristics

#### 16-Day Composite Algorithm
1. **Acquisition Period**: 16 consecutive days
2. **Selection Criteria**:
   - Lowest cloud cover
   - Smallest view zenith angle
   - Highest vegetation index value
3. **Quality Ranking**: Pixels ranked by composite criteria
4. **Output**: Single "best" pixel per 16-day period

#### Temporal Coverage
- **Start Date**: February 2000 (Terra), July 2002 (Aqua)
- **Frequency**: 23 composites per year
- **Composite Schedule**: Days 1, 17, 33, 49, etc.
- **Near Real-time**: ~2-3 day processing lag

## Cloud Masking and Quality Assessment Procedures

### Quality Assessment Framework

MODIS vegetation index products include comprehensive quality information through multiple assessment layers designed to help users identify and filter problematic pixels.

#### VI Quality Layer (Primary QA)
**Bit Structure** (16-bit integer):
```
Bits 0-1: VI quality
  00: VI produced with good quality
  01: VI produced but check other QA
  10: Pixel produced but most probably cloudy
  11: Pixel not produced due to other reasons

Bits 2-5: VI usefulness
  0000: Highest quality
  0001: Lower quality
  0010: Decreasing quality
  ...
  1111: Lowest quality

Bits 6-7: Aerosol quantity
  00: Climatology
  01: Low
  10: Average
  11: High

Bits 8-9: Adjacent cloud detected
  00: No
  01: Yes

Bits 10-13: Atmosphere BRDF correction
  0000: No correction
  0001: Correction applied
  ...

Bits 14-15: Mixed clouds
  00: No
  01: Yes
```

#### Pixel Reliability Layer
**Categories**:
- **0**: Very good (water, snow/ice)
- **1**: Good (no vegetation, minimal atmospheric effects)
- **2**: Fair (some vegetation, possible atmospheric effects)
- **3**: Poor (cloud/shadow contamination)

### Cloud Masking Algorithm

#### Collection 6.1 Improvements
- Enhanced cloud detection algorithms
- Improved aerosol retrieval corrections
- Better handling of bright surfaces
- Reduced false cloud detection over deserts

#### Multi-temporal Consistency
```python
def apply_quality_mask(vi_data, quality_data, reliability_data):
    """Apply comprehensive quality filtering"""

    # Extract quality bits
    vi_quality = quality_data & 3  # Bits 0-1
    pixel_reliability = reliability_data

    # Create mask for good quality pixels
    good_pixels = (
        (vi_quality <= 1) &  # Good or acceptable VI quality
        (pixel_reliability <= 2)  # Good to fair reliability
    )

    # Apply mask
    filtered_vi = np.where(good_pixels, vi_data, np.nan)

    return filtered_vi
```

### Atmospheric Correction

#### BRDF (Bidirectional Reflectance Distribution Function) Correction
- **Purpose**: Account for sun-sensor geometry effects
- **Implementation**: MODIS BRDF/Albedo parameters
- **Benefits**: Improved temporal consistency

#### Aerosol Correction
- **Data Source**: MODIS aerosol retrievals
- **Categories**: Low, average, high, climatology
- **Impact**: Reduced atmospheric scattering effects

## Python Libraries and Tools

### Primary Libraries

#### 1. earthaccess (NASA Official)
**Installation**:
```bash
pip install earthaccess
```

**Key Features**:
- Unified authentication with EDL
- Simplified data search and discovery
- Automatic handling of cloud vs. on-premises data
- Integration with xarray and pandas

**Example Usage**:
```python
import earthaccess

# Authenticate
earthaccess.login()

# Search for MODIS vegetation indices
results = earthaccess.search_data(
    short_name="MOD13Q1",
    version="061",
    temporal=("2023-01-01", "2023-12-31"),
    bounding_box=(-10, -10, 10, 10)  # lat/lon bounds
)

# Open data files
files = earthaccess.open(results)
```

#### 2. rasterio
**Installation**:
```bash
pip install rasterio
```

**Capabilities**:
- Read/write raster data formats
- Geospatial transformations
- Reprojection and resampling
- Integration with NumPy

**MODIS-specific Usage**:
```python
import rasterio
from rasterio.warp import calculate_default_transform, reproject

# Open MODIS HDF subdataset
with rasterio.open('HDF4_EOS:EOS_GRID:"MOD13Q1.hdf":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI') as src:
    ndvi = src.read(1)
    transform = src.transform
    crs = src.crs

# Reproject to geographic coordinates
dst_crs = 'EPSG:4326'
transform, width, height = calculate_default_transform(
    src.crs, dst_crs, src.width, src.height, *src.bounds
)
```

#### 3. xarray with rioxarray
**Installation**:
```bash
pip install xarray rioxarray netcdf4
```

**Benefits**:
- Multi-dimensional data handling
- Built-in metadata preservation
- Efficient subsetting and aggregation
- Time series analysis tools

**Example**:
```python
import xarray as xr
import rioxarray as rxr

# Open MODIS NetCDF with geospatial extensions
ds = rxr.open_rasterio("MOD13Q1.nc", chunks={'time': 1})

# Select NDVI variable
ndvi = ds['NDVI']

# Apply quality filtering
good_quality = ds['VI_Quality'] <= 1
ndvi_filtered = ndvi.where(good_quality)

# Temporal aggregation
monthly_mean = ndvi_filtered.groupby('time.month').mean()
```

#### 4. pyModis
**Installation**:
```bash
pip install pymodis
```

**Specialized Functions**:
- Bulk download automation
- Tile mosaicking
- Sinusoidal to geographic projection
- Quality assessment interpretation

**Example**:
```python
from pymodis import downmodis, convertmodis

# Download MODIS data
modisDown = downmodis.downModis(
    destinationFolder="/data/modis",
    user="earthdata_username",
    password="earthdata_password",
    product="MOD13Q1.061",
    tiles="h21v09,h22v09",
    path="MOLT",
    today="2023-01-01",
    enddate="2023-01-16"
)
modisDown.downloadsAllDay()

# Convert and mosaic
convertM = convertmodis.convertModis(
    hdfname="/data/modis/MOD13Q1.hdf",
    prefix="NDVI_",
    subset=[1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Select NDVI and EVI only
)
convertM.run()
```

#### 5. GDAL Python Bindings
**Installation**:
```bash
pip install gdal
```

**HDF4 Handling**:
```python
from osgeo import gdal

# Open HDF4 file
hdf_file = gdal.Open("MOD13Q1.A2023001.h21v09.061.2023018055414.hdf")

# List subdatasets
subdatasets = hdf_file.GetSubDatasets()
for idx, (name, desc) in enumerate(subdatasets):
    print(f"{idx}: {desc}")

# Open specific subdataset (NDVI)
ndvi_ds = gdal.Open(subdatasets[0][0])  # First subdataset
ndvi_array = ndvi_ds.ReadAsArray()
```

### Supporting Libraries

#### Scientific Computing
```python
import numpy as np          # Array operations
import pandas as pd         # Data manipulation
import scipy as sp          # Scientific functions
from sklearn import *       # Machine learning
```

#### Geospatial Analysis
```python
import geopandas as gpd     # Vector data
import shapely              # Geometric operations
import cartopy              # Map projections
import rasterio.features    # Vector-raster operations
```

#### Visualization
```python
import matplotlib.pyplot as plt
import seaborn as sns
import folium               # Interactive maps
import plotly               # Interactive plots
```

## Download Automation and Bulk Access Methods

### earthaccess Automation

#### Batch Download Setup
```python
import earthaccess
import os
from datetime import datetime, timedelta

class MODISDownloader:
    def __init__(self, download_dir="/data/modis"):
        self.download_dir = download_dir
        self.auth = earthaccess.login()

    def download_time_series(self, product, version, start_date, end_date,
                           tiles=None, bbox=None):
        """Download MODIS time series data"""

        # Search for data
        results = earthaccess.search_data(
            short_name=product,
            version=version,
            temporal=(start_date, end_date),
            bounding_box=bbox
        )

        # Filter by tiles if specified
        if tiles:
            filtered_results = []
            for result in results:
                granule_id = result['meta']['concept-id']
                if any(tile in granule_id for tile in tiles):
                    filtered_results.append(result)
            results = filtered_results

        # Download files
        files = earthaccess.download(
            results,
            local_path=self.download_dir
        )

        return files

    def bulk_download_region(self, bbox, years, products=None):
        """Download multiple years of data for a region"""

        if products is None:
            products = ["MOD13Q1", "MYD13Q1"]

        all_files = {}

        for product in products:
            all_files[product] = []

            for year in years:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"

                files = self.download_time_series(
                    product=product,
                    version="061",
                    start_date=start_date,
                    end_date=end_date,
                    bbox=bbox
                )

                all_files[product].extend(files)

        return all_files
```

#### Parallel Download Implementation
```python
import concurrent.futures
from functools import partial

def download_tile_year(tile, year, product, download_dir):
    """Download one tile for one year"""
    downloader = MODISDownloader(download_dir)
    return downloader.download_time_series(
        product=product,
        version="061",
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        tiles=[tile]
    )

def parallel_bulk_download(tiles, years, products, download_dir, max_workers=4):
    """Download multiple tiles/years in parallel"""

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for product in products:
            for tile in tiles:
                for year in years:
                    future = executor.submit(
                        download_tile_year, tile, year, product, download_dir
                    )
                    futures.append(future)

        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.extend(result)
            except Exception as exc:
                print(f'Download generated an exception: {exc}')

    return results
```

### FTP and HTTP Access

#### NASA LAADS DAAC
```python
import requests
from urllib.parse import urljoin

class LAADSDownloader:
    def __init__(self, token):
        self.base_url = "https://ladsweb.modaps.eosdis.nasa.gov/"
        self.token = token

    def search_files(self, product, collection, date, tiles=None):
        """Search for MODIS files on LAADS"""

        search_url = urljoin(self.base_url, "api/v2/content/details")

        params = {
            'products': product,
            'collection': collection,
            'dateRanges': date,
            'areaOfInterest': tiles if tiles else '',
            'coordsOrTiles': 'tiles' if tiles else 'coords'
        }

        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(search_url, params=params, headers=headers)
        return response.json()

    def download_file(self, file_url, local_path):
        """Download single file from LAADS"""

        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(file_url, headers=headers, stream=True)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
```

### Scheduled Automation

#### Cron-based Updates
```python
import schedule
import time
from datetime import datetime, timedelta

class MODISUpdater:
    def __init__(self, config):
        self.config = config
        self.downloader = MODISDownloader(config['download_dir'])

    def daily_update(self):
        """Check for and download new MODIS data"""

        # Calculate date range for recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Check last 30 days

        # Download latest data
        for product in self.config['products']:
            try:
                files = self.downloader.download_time_series(
                    product=product,
                    version="061",
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    bbox=self.config['bbox']
                )

                print(f"Downloaded {len(files)} files for {product}")

            except Exception as e:
                print(f"Error downloading {product}: {e}")

    def run_scheduler(self):
        """Run scheduled updates"""

        schedule.every().day.at("02:00").do(self.daily_update)

        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour

# Configuration
config = {
    'products': ['MOD13Q1', 'MYD13Q1'],
    'download_dir': '/data/modis',
    'bbox': (-10, -10, 10, 10)  # Example bounding box
}

# Start scheduler
updater = MODISUpdater(config)
updater.run_scheduler()
```

## Integration Patterns for Vegetation Index Analysis

### Data Processing Pipeline

#### 1. Data Ingestion and Preprocessing
```python
import xarray as xr
import numpy as np
from pathlib import Path

class MODISProcessor:
    def __init__(self, data_dir, output_dir):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def preprocess_modis_file(self, filepath):
        """Preprocess single MODIS file"""

        # Open dataset
        ds = xr.open_dataset(filepath, engine='rasterio')

        # Apply quality filtering
        vi_quality = ds['VI_Quality']
        pixel_reliability = ds['pixel_reliability']

        # Create quality mask
        good_quality = (
            (vi_quality & 3) <= 1  # VI quality good/acceptable
        ) & (
            pixel_reliability <= 2  # Pixel reliability good/fair
        )

        # Apply mask to vegetation indices
        ndvi_clean = ds['NDVI'].where(good_quality)
        evi_clean = ds['EVI'].where(good_quality)

        # Scale to physical values
        ndvi_clean = ndvi_clean * 0.0001
        evi_clean = evi_clean * 0.0001

        # Create cleaned dataset
        ds_clean = xr.Dataset({
            'NDVI': ndvi_clean,
            'EVI': evi_clean,
            'quality_mask': good_quality
        })

        return ds_clean

    def process_time_series(self, tile, start_year, end_year):
        """Process time series for a tile"""

        all_files = list(self.data_dir.glob(f"*{tile}*.hdf"))
        all_files.sort()

        datasets = []
        for file in all_files:
            try:
                ds = self.preprocess_modis_file(file)
                datasets.append(ds)
            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Concatenate time series
        ts = xr.concat(datasets, dim='time')

        # Save processed time series
        output_file = self.output_dir / f"MODIS_VI_{tile}_{start_year}_{end_year}.nc"
        ts.to_netcdf(output_file)

        return ts
```

#### 2. Spatial Mosaicking
```python
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject

class MODISMosaicker:
    def __init__(self):
        self.temp_dir = Path("/tmp/modis_mosaic")
        self.temp_dir.mkdir(exist_ok=True)

    def mosaic_tiles(self, file_list, output_path, target_crs="EPSG:4326"):
        """Mosaic multiple MODIS tiles"""

        # Convert HDF to GeoTIFF if needed
        tiff_files = []
        for hdf_file in file_list:
            tiff_file = self.convert_hdf_to_tiff(hdf_file)
            tiff_files.append(tiff_file)

        # Open all files
        src_files = [rasterio.open(f) for f in tiff_files]

        # Mosaic
        mosaic, out_transform = merge(src_files)

        # Get metadata from first file
        out_meta = src_files[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_transform,
            "crs": target_crs
        })

        # Write mosaic
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)

        # Clean up
        for src in src_files:
            src.close()

        return output_path
```

#### 3. Temporal Analysis
```python
def calculate_vegetation_metrics(ndvi_ts, evi_ts):
    """Calculate vegetation phenology metrics"""

    metrics = {}

    # Annual statistics
    metrics['ndvi_max'] = ndvi_ts.groupby('time.year').max()
    metrics['ndvi_min'] = ndvi_ts.groupby('time.year').min()
    metrics['ndvi_mean'] = ndvi_ts.groupby('time.year').mean()
    metrics['ndvi_std'] = ndvi_ts.groupby('time.year').std()

    metrics['evi_max'] = evi_ts.groupby('time.year').max()
    metrics['evi_min'] = evi_ts.groupby('time.year').min()
    metrics['evi_mean'] = evi_ts.groupby('time.year').mean()
    metrics['evi_std'] = evi_ts.groupby('time.year').std()

    # Seasonal patterns
    metrics['ndvi_seasonal'] = ndvi_ts.groupby('time.month').mean()
    metrics['evi_seasonal'] = evi_ts.groupby('time.month').mean()

    # Growing season metrics
    ndvi_threshold = metrics['ndvi_mean'] + 0.1 * metrics['ndvi_std']
    growing_season = ndvi_ts > ndvi_threshold

    metrics['growing_season_length'] = growing_season.groupby('time.year').sum()
    metrics['growing_season_start'] = growing_season.groupby('time.year').idxmax()

    return metrics

def detect_vegetation_anomalies(ndvi_ts, window=5):
    """Detect vegetation anomalies using moving statistics"""

    # Calculate moving average and standard deviation
    ndvi_rolling_mean = ndvi_ts.rolling(time=window, center=True).mean()
    ndvi_rolling_std = ndvi_ts.rolling(time=window, center=True).std()

    # Calculate anomalies (z-scores)
    anomalies = (ndvi_ts - ndvi_rolling_mean) / ndvi_rolling_std

    # Flag significant anomalies
    severe_anomalies = np.abs(anomalies) > 2.0

    return anomalies, severe_anomalies
```

#### 4. Malaria Vector Habitat Analysis
```python
class VectorHabitatAnalyzer:
    def __init__(self):
        self.habitat_thresholds = {
            'anopheles_gambiae': {
                'ndvi_min': 0.2,
                'ndvi_max': 0.7,
                'water_proximity': 1000  # meters
            },
            'anopheles_funestus': {
                'ndvi_min': 0.3,
                'ndvi_max': 0.8,
                'water_proximity': 500   # meters
            }
        }

    def identify_potential_habitats(self, ndvi, evi, water_bodies, species):
        """Identify potential vector breeding habitats"""

        thresholds = self.habitat_thresholds[species]

        # Vegetation suitability
        veg_suitable = (
            (ndvi >= thresholds['ndvi_min']) &
            (ndvi <= thresholds['ndvi_max'])
        )

        # Water proximity (requires water bodies layer)
        water_distance = calculate_distance_to_water(water_bodies)
        water_suitable = water_distance <= thresholds['water_proximity']

        # Combined habitat suitability
        habitat_suitability = veg_suitable & water_suitable

        return habitat_suitability

    def temporal_habitat_dynamics(self, ndvi_ts, water_ts, species):
        """Analyze seasonal habitat availability"""

        habitat_ts = []

        for time_step in ndvi_ts.time:
            ndvi_t = ndvi_ts.sel(time=time_step)
            water_t = water_ts.sel(time=time_step)

            habitat_t = self.identify_potential_habitats(
                ndvi_t, None, water_t, species
            )

            habitat_ts.append(habitat_t)

        # Concatenate time series
        habitat_ts = xr.concat(habitat_ts, dim='time')

        # Calculate habitat metrics
        metrics = {
            'seasonal_availability': habitat_ts.groupby('time.month').mean(),
            'peak_habitat_month': habitat_ts.groupby('time.month').mean().argmax(),
            'habitat_persistence': habitat_ts.sum(dim='time') / len(habitat_ts.time)
        }

        return habitat_ts, metrics
```

#### 5. Integration with Climate Data
```python
def integrate_vegetation_climate(ndvi_ts, temperature_ts, precipitation_ts):
    """Integrate vegetation indices with climate data"""

    # Align temporal dimensions
    common_times = np.intersect1d(ndvi_ts.time, temperature_ts.time)
    common_times = np.intersect1d(common_times, precipitation_ts.time)

    ndvi_aligned = ndvi_ts.sel(time=common_times)
    temp_aligned = temperature_ts.sel(time=common_times)
    precip_aligned = precipitation_ts.sel(time=common_times)

    # Calculate correlations
    ndvi_temp_corr = xr.corr(ndvi_aligned, temp_aligned, dim='time')
    ndvi_precip_corr = xr.corr(ndvi_aligned, precip_aligned, dim='time')

    # Create environmental suitability index
    # Normalize all variables to 0-1 scale
    ndvi_norm = (ndvi_aligned - ndvi_aligned.min()) / (ndvi_aligned.max() - ndvi_aligned.min())
    temp_norm = (temp_aligned - temp_aligned.min()) / (temp_aligned.max() - temp_aligned.min())
    precip_norm = (precip_aligned - precip_aligned.min()) / (precip_aligned.max() - precip_aligned.min())

    # Calculate composite environmental index
    env_index = (ndvi_norm + temp_norm + precip_norm) / 3

    return {
        'ndvi_temperature_correlation': ndvi_temp_corr,
        'ndvi_precipitation_correlation': ndvi_precip_corr,
        'environmental_suitability_index': env_index
    }
```

## Production Implementation Strategy

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 Authentication and Access Setup
```python
# config/earthdata_config.py
import os
from pathlib import Path

class EarthDataConfig:
    def __init__(self):
        self.credentials_file = Path.home() / ".netrc"
        self.setup_authentication()

    def setup_authentication(self):
        """Setup NASA EarthData authentication"""

        if not self.credentials_file.exists():
            username = input("NASA EarthData username: ")
            password = input("NASA EarthData password: ")

            with open(self.credentials_file, 'w') as f:
                f.write(f"machine urs.earthdata.nasa.gov\n")
                f.write(f"login {username}\n")
                f.write(f"password {password}\n")

            # Set proper permissions
            os.chmod(self.credentials_file, 0o600)

        # Test authentication
        import earthaccess
        auth = earthaccess.login()
        if auth:
            print("✓ NASA EarthData authentication successful")
        else:
            raise Exception("❌ NASA EarthData authentication failed")
```

#### 1.2 Data Storage Architecture
```python
# storage/modis_storage.py
from pathlib import Path
import json

class MODISStorageManager:
    def __init__(self, base_path="/data/modis"):
        self.base_path = Path(base_path)
        self.setup_directory_structure()

    def setup_directory_structure(self):
        """Create organized directory structure"""

        directories = [
            "raw/terra/mod13q1",      # Raw Terra 250m data
            "raw/aqua/myd13q1",       # Raw Aqua 250m data
            "processed/mosaics",       # Processed mosaics
            "processed/time_series",   # Time series data
            "processed/quality",       # Quality assessment
            "cache/downloads",         # Download cache
            "metadata",                # Metadata storage
            "logs"                     # Processing logs
        ]

        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)

    def get_path(self, data_type, *args):
        """Get standardized paths for different data types"""

        path_map = {
            'raw_terra': self.base_path / "raw/terra/mod13q1",
            'raw_aqua': self.base_path / "raw/aqua/myd13q1",
            'processed': self.base_path / "processed",
            'cache': self.base_path / "cache/downloads",
            'metadata': self.base_path / "metadata",
            'logs': self.base_path / "logs"
        }

        base = path_map[data_type]
        return base.joinpath(*args) if args else base
```

#### 1.3 Configuration Management
```python
# config/modis_config.py
import yaml
from pathlib import Path

class MODISConfig:
    def __init__(self, config_file="config/modis.yaml"):
        self.config_file = Path(config_file)
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file"""

        default_config = {
            'data_sources': {
                'products': ['MOD13Q1', 'MYD13Q1'],
                'version': '061',
                'resolution': '250m'
            },
            'processing': {
                'quality_threshold': 1,
                'cloud_threshold': 0.3,
                'temporal_window': 16
            },
            'storage': {
                'base_path': '/data/modis',
                'compression': 'gzip',
                'chunking': True
            },
            'regions': {
                'africa': {
                    'bbox': [-20, -35, 55, 40],
                    'tiles': ['h20v07', 'h20v08', 'h21v07', 'h21v08', 'h21v09']
                }
            }
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
```

### Phase 2: Data Pipeline Development (Week 2)

#### 2.1 Download Automation
```python
# pipeline/data_downloader.py
import earthaccess
from datetime import datetime, timedelta
import logging

class MODISDownloader:
    def __init__(self, config, storage_manager):
        self.config = config
        self.storage = storage_manager
        self.logger = self.setup_logging()

        # Authenticate with NASA EarthData
        self.auth = earthaccess.login()

    def setup_logging(self):
        """Setup logging for download operations"""

        log_file = self.storage.get_path('logs', 'download.log')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        return logging.getLogger(__name__)

    def download_region_timeframe(self, region_name, start_date, end_date):
        """Download MODIS data for a region and timeframe"""

        region_config = self.config.config['regions'][region_name]
        products = self.config.config['data_sources']['products']
        version = self.config.config['data_sources']['version']

        all_downloads = []

        for product in products:
            self.logger.info(f"Downloading {product} for {region_name}")

            try:
                # Search for data
                results = earthaccess.search_data(
                    short_name=product,
                    version=version,
                    temporal=(start_date, end_date),
                    bounding_box=region_config['bbox']
                )

                # Filter by tiles if specified
                if 'tiles' in region_config:
                    results = self.filter_by_tiles(results, region_config['tiles'])

                # Download files
                download_path = self.storage.get_path('cache')
                files = earthaccess.download(results, local_path=str(download_path))

                # Organize downloaded files
                organized_files = self.organize_downloads(files, product)
                all_downloads.extend(organized_files)

                self.logger.info(f"Downloaded {len(files)} files for {product}")

            except Exception as e:
                self.logger.error(f"Error downloading {product}: {e}")

        return all_downloads

    def filter_by_tiles(self, results, target_tiles):
        """Filter search results by MODIS tiles"""

        filtered = []
        for result in results:
            granule_id = result.get('meta', {}).get('native-id', '')
            if any(tile in granule_id for tile in target_tiles):
                filtered.append(result)

        return filtered

    def organize_downloads(self, files, product):
        """Organize downloaded files into proper directory structure"""

        organized = []

        for file_path in files:
            file_path = Path(file_path)

            # Determine target directory
            if product.startswith('MOD'):
                target_dir = self.storage.get_path('raw_terra')
            else:  # MYD products
                target_dir = self.storage.get_path('raw_aqua')

            # Move file to organized location
            target_path = target_dir / file_path.name
            file_path.rename(target_path)
            organized.append(target_path)

        return organized
```

#### 2.2 Data Processing Pipeline
```python
# pipeline/data_processor.py
import xarray as xr
import numpy as np
from rasterio.warp import reproject
import dask

class MODISProcessor:
    def __init__(self, config, storage_manager):
        self.config = config
        self.storage = storage_manager
        self.logger = self.setup_logging()

    def process_file(self, input_file):
        """Process single MODIS HDF file"""

        try:
            # Open HDF file with xarray
            ds = xr.open_dataset(input_file, engine='rasterio')

            # Extract vegetation indices and quality layers
            ndvi = ds['NDVI']
            evi = ds['EVI']
            vi_quality = ds['VI_Quality']
            pixel_reliability = ds['pixel_reliability']

            # Apply quality filtering
            quality_mask = self.create_quality_mask(vi_quality, pixel_reliability)

            # Scale to physical values
            ndvi_scaled = ndvi * 0.0001
            evi_scaled = evi * 0.0001

            # Apply quality mask
            ndvi_clean = ndvi_scaled.where(quality_mask)
            evi_clean = evi_scaled.where(quality_mask)

            # Create processed dataset
            processed = xr.Dataset({
                'NDVI': ndvi_clean,
                'EVI': evi_clean,
                'quality_mask': quality_mask,
                'pixel_reliability': pixel_reliability
            })

            # Add metadata
            processed.attrs.update({
                'source_file': str(input_file),
                'processing_date': datetime.now().isoformat(),
                'quality_threshold': self.config.config['processing']['quality_threshold']
            })

            return processed

        except Exception as e:
            self.logger.error(f"Error processing {input_file}: {e}")
            return None

    def create_quality_mask(self, vi_quality, pixel_reliability):
        """Create quality mask for filtering"""

        quality_threshold = self.config.config['processing']['quality_threshold']

        # VI quality check (bits 0-1)
        vi_good = (vi_quality & 3) <= quality_threshold

        # Pixel reliability check
        pixel_good = pixel_reliability <= 2

        # Combined mask
        quality_mask = vi_good & pixel_good

        return quality_mask

    @dask.delayed
    def process_time_series(self, file_list, output_path):
        """Process time series of MODIS files"""

        processed_datasets = []

        for file_path in file_list:
            ds = self.process_file(file_path)
            if ds is not None:
                processed_datasets.append(ds)

        if processed_datasets:
            # Concatenate time series
            ts = xr.concat(processed_datasets, dim='time')

            # Save to NetCDF
            ts.to_netcdf(output_path, encoding={
                'NDVI': {'zlib': True, 'complevel': 6},
                'EVI': {'zlib': True, 'complevel': 6}
            })

            self.logger.info(f"Processed time series saved to {output_path}")
            return output_path

        return None
```

### Phase 3: Quality Assurance and Validation (Week 3)

#### 3.1 Data Quality Assessment
```python
# quality/quality_assessor.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class MODISQualityAssessor:
    def __init__(self, storage_manager):
        self.storage = storage_manager

    def assess_time_series_quality(self, time_series_file):
        """Assess quality of processed time series"""

        ds = xr.open_dataset(time_series_file)

        quality_metrics = {}

        # Data availability
        ndvi_availability = (~ds['NDVI'].isnull()).sum() / ds['NDVI'].size
        evi_availability = (~ds['EVI'].isnull()).sum() / ds['EVI'].size

        quality_metrics['data_availability'] = {
            'ndvi': float(ndvi_availability),
            'evi': float(evi_availability)
        }

        # Temporal consistency
        ndvi_temporal_std = ds['NDVI'].std(dim='time')
        evi_temporal_std = ds['EVI'].std(dim='time')

        quality_metrics['temporal_variability'] = {
            'ndvi_std_mean': float(ndvi_temporal_std.mean()),
            'evi_std_mean': float(evi_temporal_std.mean())
        }

        # Spatial patterns
        quality_metrics['spatial_patterns'] = self.assess_spatial_patterns(ds)

        # Phenological consistency
        quality_metrics['phenology'] = self.assess_phenological_patterns(ds)

        return quality_metrics

    def assess_spatial_patterns(self, ds):
        """Assess spatial patterns in the data"""

        # Calculate spatial autocorrelation
        ndvi_mean = ds['NDVI'].mean(dim='time')
        spatial_autocorr = self.calculate_spatial_autocorrelation(ndvi_mean)

        # Detect spatial outliers
        spatial_outliers = self.detect_spatial_outliers(ndvi_mean)

        return {
            'spatial_autocorrelation': float(spatial_autocorr),
            'spatial_outlier_fraction': float(spatial_outliers.sum() / spatial_outliers.size)
        }

    def generate_quality_report(self, quality_metrics, output_path):
        """Generate comprehensive quality report"""

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Data availability plot
        availability = quality_metrics['data_availability']
        axes[0, 0].bar(['NDVI', 'EVI'], [availability['ndvi'], availability['evi']])
        axes[0, 0].set_title('Data Availability')
        axes[0, 0].set_ylabel('Fraction Available')

        # Temporal variability
        temp_var = quality_metrics['temporal_variability']
        axes[0, 1].bar(['NDVI', 'EVI'], [temp_var['ndvi_std_mean'], temp_var['evi_std_mean']])
        axes[0, 1].set_title('Temporal Variability')
        axes[0, 1].set_ylabel('Standard Deviation')

        # Spatial patterns
        spatial = quality_metrics['spatial_patterns']
        axes[1, 0].bar(['Autocorrelation', 'Outliers'],
                      [spatial['spatial_autocorrelation'], spatial['spatial_outlier_fraction']])
        axes[1, 0].set_title('Spatial Patterns')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
```

#### 3.2 Validation Against Reference Data
```python
# validation/data_validator.py
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib.pyplot as plt

class MODISValidator:
    def __init__(self, config):
        self.config = config

    def validate_against_reference(self, modis_data, reference_data):
        """Validate MODIS data against reference measurements"""

        # Align datasets spatially and temporally
        aligned_modis, aligned_ref = self.align_datasets(modis_data, reference_data)

        # Calculate validation metrics
        validation_results = {}

        for variable in ['NDVI', 'EVI']:
            if variable in aligned_modis and variable in aligned_ref:
                modis_vals = aligned_modis[variable].values.flatten()
                ref_vals = aligned_ref[variable].values.flatten()

                # Remove NaN values
                valid_mask = ~(np.isnan(modis_vals) | np.isnan(ref_vals))
                modis_clean = modis_vals[valid_mask]
                ref_clean = ref_vals[valid_mask]

                if len(modis_clean) > 0:
                    validation_results[variable] = {
                        'r2': r2_score(ref_clean, modis_clean),
                        'mae': mean_absolute_error(ref_clean, modis_clean),
                        'rmse': np.sqrt(np.mean((ref_clean - modis_clean)**2)),
                        'bias': np.mean(modis_clean - ref_clean),
                        'n_samples': len(modis_clean)
                    }

        return validation_results

    def create_validation_plots(self, validation_results, output_dir):
        """Create validation scatter plots"""

        for variable, metrics in validation_results.items():
            fig, ax = plt.subplots(figsize=(8, 8))

            # Scatter plot
            ax.scatter(metrics['reference'], metrics['modis'], alpha=0.6)

            # 1:1 line
            min_val = min(metrics['reference'].min(), metrics['modis'].min())
            max_val = max(metrics['reference'].max(), metrics['modis'].max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)

            # Add statistics
            ax.text(0.05, 0.95, f"R² = {metrics['r2']:.3f}\n"
                               f"RMSE = {metrics['rmse']:.3f}\n"
                               f"MAE = {metrics['mae']:.3f}\n"
                               f"Bias = {metrics['bias']:.3f}",
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            ax.set_xlabel(f'Reference {variable}')
            ax.set_ylabel(f'MODIS {variable}')
            ax.set_title(f'{variable} Validation')

            plt.savefig(output_dir / f'{variable}_validation.png', dpi=300, bbox_inches='tight')
            plt.close()
```

## Best Practices and Recommendations

### 1. Data Management
- **Version Control**: Always use the latest product version (v061 as of 2025)
- **Quality Filtering**: Apply comprehensive quality filtering using both VI Quality and Pixel Reliability layers
- **Temporal Consistency**: Maintain consistent processing across time series
- **Backup Strategy**: Implement automated backup of processed data

### 2. Processing Optimization
- **Parallel Processing**: Use Dask or multiprocessing for large-scale operations
- **Chunking**: Implement appropriate chunking for memory efficiency
- **Caching**: Cache intermediate results to avoid reprocessing
- **Cloud Optimization**: Leverage cloud-optimized formats (COG, Zarr)

### 3. Quality Assurance
- **Automated QA**: Implement automated quality assessment pipelines
- **Validation**: Regular validation against ground truth or higher-resolution data
- **Anomaly Detection**: Monitor for unusual patterns or processing errors
- **Documentation**: Maintain detailed processing logs and metadata

### 4. Integration Considerations
- **Coordinate Systems**: Ensure proper handling of sinusoidal projection
- **Temporal Alignment**: Account for composite periods when integrating with other data
- **Scale Factors**: Apply proper scaling to convert from integer to physical values
- **Uncertainty**: Propagate quality information through analysis pipeline

## Licensing and Attribution

### MODIS Data Usage
MODIS data are freely available for research and operational use. Users should:

**Citation Requirements**:
```
Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061.
NASA EOSDIS Land Processes DAAC.
https://doi.org/10.5067/MODIS/MOD13Q1.061

Didan, K. (2021). MODIS/Aqua Vegetation Indices 16-Day L3 Global 250m SIN Grid V061.
NASA EOSDIS Land Processes DAAC.
https://doi.org/10.5067/MODIS/MYD13Q1.061
```

**Attribution Requirements**:
- Acknowledge NASA EOSDIS Land Processes DAAC
- Include proper DOI citations
- Mention processing level and version
- Credit algorithm developers and data producers

### Software Licensing
- **earthaccess**: MIT License
- **rasterio**: BSD-3-Clause License
- **xarray**: Apache 2.0 License
- **pyModis**: GPL v2+ License

## Conclusion

MODIS vegetation indices provide critical data for understanding vegetation dynamics in malaria-endemic regions. The NASA EarthData ecosystem, particularly the earthaccess library, significantly simplifies data access and processing. The 250m resolution MOD13Q1/MYD13Q1 products offer the optimal balance of spatial detail and temporal frequency for malaria vector habitat monitoring.

Key implementation priorities include:
1. Robust authentication and data access infrastructure
2. Comprehensive quality filtering and validation
3. Efficient processing pipelines for large-scale analysis
4. Integration with existing malaria prediction frameworks
5. Automated monitoring and update systems

The production implementation should prioritize data quality, processing efficiency, and seamless integration with other environmental data sources while maintaining flexibility for future enhancements and research applications.
