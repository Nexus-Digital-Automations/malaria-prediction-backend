# Malaria Atlas Project (MAP) Data Access Research

## Executive Summary

The Malaria Atlas Project (MAP) provides comprehensive global malaria data through an open-access platform. Primary programmatic access is via the **malariaAtlas R package**, with data licensed under Creative Commons CC BY 3.0. While no official Python API exists, the data can be accessed through R and integrated into Python workflows.

## MAP Data Portal Overview

### Main Access Points
- **Interactive Data Portal**: https://data.malariaatlas.org/
- **Main Website**: https://malariaatlas.org/
- **GitHub Organization**: https://github.com/malaria-atlas-project

### Data Platform Components
1. **Interactive Maps**: Web-based visualization of malaria risk and intervention coverage
2. **Data Downloads**: Direct access to curated datasets
3. **API Access**: Through malariaAtlas R package
4. **Surveillance Data**: Available on request for some datasets

## Available Datasets

### 1. Parasite Rate (PR) Data
- **Description**: Geolocated survey points showing malaria parasite prevalence
- **Species Coverage**:
  - Plasmodium falciparum (Pf)
  - Plasmodium vivax (Pv)
- **Data Points**: Individual survey locations with:
  - Geographic coordinates
  - Sample size
  - Number positive
  - Age range
  - Survey year
  - Diagnostic method

### 2. Modeled Raster Outputs
- **Malaria Risk Maps**: Predicted parasite prevalence surfaces
- **Clinical Incidence**: Modeled disease burden estimates
- **Intervention Coverage**: Bed net distribution, treatment coverage
- **Environmental Covariates**:
  - Land Surface Temperature (LST) - Day and Night
  - Enhanced Vegetation Index (EVI)
  - Tasseled Cap Wetness (TCW)
  - Tasseled Cap Brightness (TCB)

### 3. Vector Occurrence Data
- **Coverage**: 41 dominant malaria vector species
- **Data Type**: Presence/absence points
- **Metadata**: Collection methods, habitat information
- **Species List**: Available via `listSpecies()` function

### 4. Administrative Boundaries
- **Shapefiles**: Country and sub-national boundaries
- **Versions**: Multiple versions available for temporal consistency
- **Formats**: Standard GIS shapefile format

## API Endpoints and Authentication

### malariaAtlas R Package API

#### Installation
```r
# From CRAN
install.packages("malariaAtlas")

# Development version
devtools::install_github('malaria-atlas-project/malariaAtlas')
```

#### Core Functions

##### Data Discovery
```r
# List available raster datasets
available_rasters <- listRaster()

# List countries with PR data
pr_countries <- listPRPointCountries()

# List vector species
species <- listSpecies()

# Check data availability for location
is_available <- isAvailable_pr(country = "Kenya")
```

##### Data Retrieval
```r
# Download parasite rate data
pr_data <- getPR(
  country = "Uganda",
  species = "both"  # "Pf", "Pv", or "both"
)

# Download vector occurrence data
vector_data <- getVecOcc(
  country = "Tanzania",
  species = "An.gambiae"
)

# Download raster data
risk_raster <- getRaster(
  dataset_id = "Plasmodium_falciparum_PR_2020",
  extent = c(20, 50, -35, -5)  # xmin, xmax, ymin, ymax
)

# Download shapefiles
admin_bounds <- getShp(
  country = "Kenya",
  admin_level = "admin1"
)
```

### Authentication Requirements
- **No authentication required** for public data access
- Data is open access under CC BY 3.0 license
- Registration required only for data upload (restricted)

## Data Formats

### Raster Data Specifications
- **Format**: GeoTIFF standard
- **Projection**: WGS-84 (EPSG:4326)
- **Resolution Options**:
  - ~1 km (30 arc-second) for fine-scale products
  - ~5 km for aggregated products
- **Data Type**: SpatRaster objects (terra package)
- **Quality Layers**: Accompanying uncertainty/quality rasters

### Vector Data Format
- **Format**: Data frame with spatial attributes
- **Required Fields**:
  - latitude/longitude (decimal degrees)
  - species name
  - collection date
  - presence/absence indicator
- **Optional Metadata**: Collection method, habitat type

## Spatial and Temporal Resolution

### Spatial Resolution
- **Point Data**: Exact GPS coordinates (survey locations)
- **Raster Products**:
  - Standard: 5×5 km pixels
  - High-resolution: 1×1 km pixels
  - Global coverage between 40°S and 60°N

### Temporal Resolution
- **Historical Coverage**:
  - PR data from 1985-present
  - Environmental covariates: 2000-2014
- **Update Frequency**:
  - Annual updates for modeled surfaces
  - Continuous updates for survey data
- **Temporal Products**:
  - 8-day composites (LST)
  - 16-day composites (vegetation indices)
  - Monthly aggregations
  - Annual summaries

## Download Methods and Tools

### 1. R Package Workflow
```r
library(malariaAtlas)
library(terra)
library(sf)

# Set up workspace
output_dir <- "map_data"
dir.create(output_dir, showWarnings = FALSE)

# Download and save PR data
pr_data <- getPR(country = "Kenya", species = "Pf")
write.csv(pr_data, file.path(output_dir, "kenya_pr_data.csv"))

# Download and save raster
pf_risk <- getRaster(
  dataset_id = "Plasmodium_falciparum_PR_2020",
  extent = c(33, 42, -5, 5)  # Kenya extent
)
writeRaster(pf_risk, file.path(output_dir, "kenya_pf_risk.tif"))
```

### 2. Python Integration Strategy
```python
# Option 1: Use rpy2 to call R functions
import rpy2.robjects as ro
from rpy2.robjects.packages import importr

# Load malariaAtlas
malariaAtlas = importr('malariaAtlas')

# Get data
pr_data = malariaAtlas.getPR(country="Kenya", species="Pf")

# Option 2: Pre-download with R, then load in Python
import rasterio
import geopandas as gpd
import pandas as pd

# Load pre-downloaded raster
with rasterio.open('kenya_pf_risk.tif') as src:
    risk_data = src.read(1)
    transform = src.transform
    crs = src.crs

# Load CSV data
pr_data = pd.read_csv('kenya_pr_data.csv')
```

### 3. Batch Download Script
```r
# R script for batch downloads
library(malariaAtlas)
library(purrr)

countries <- c("Kenya", "Uganda", "Tanzania")
years <- 2015:2020

# Download PR data for multiple countries
pr_data_list <- map(countries, ~getPR(country = .x, species = "both"))
names(pr_data_list) <- countries

# Download rasters for multiple years
raster_ids <- paste0("Plasmodium_falciparum_PR_", years)
rasters <- map(raster_ids, ~getRaster(dataset_id = .x))
```

## Rate Limits and Usage Policies

### Access Limitations
- **Rate Limits**: No documented API rate limits
- **Bulk Downloads**: Supported through package functions
- **Concurrent Requests**: No specified restrictions
- **Data Volume**: Large raster downloads may be slow

### Usage Policies
- **License**: Creative Commons Attribution 3.0 (CC BY 3.0)
- **Commercial Use**: Permitted with attribution
- **Redistribution**: Allowed with proper citation
- **Modifications**: Permitted with clear indication

### Citation Requirements
```
Pfeffer, D.A., Lucas, T.C., May, D., Harris, J., Rozier, J.,
Twohig, K.A., Dalrymple, U., Guerra, C.A., Moyes, C.L.,
Thorn, M., Nguyen, M., et al. (2018). malariaAtlas: an R
interface to global malariometric data hosted by the
Malaria Atlas Project. Malaria Journal, 17, 352.
```

## Integration Patterns for Production System

### 1. Data Pipeline Architecture
```python
# data_pipeline.py
class MAPDataPipeline:
    def __init__(self):
        self.r_interface = self._setup_r_interface()
        self.cache_dir = Path("data/map_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _setup_r_interface(self):
        """Initialize R interface with malariaAtlas"""
        import rpy2.robjects as ro
        ro.r('library(malariaAtlas)')
        return ro.r

    def fetch_pr_data(self, country, species="both", use_cache=True):
        """Fetch parasite rate data with caching"""
        cache_file = self.cache_dir / f"{country}_{species}_pr.csv"

        if use_cache and cache_file.exists():
            return pd.read_csv(cache_file)

        # Fetch from MAP
        pr_data = self.r_interface.getPR(country=country, species=species)
        df = self._r_to_pandas(pr_data)

        # Cache results
        df.to_csv(cache_file, index=False)
        return df

    def fetch_risk_raster(self, dataset_id, extent, resolution="5km"):
        """Fetch risk surface raster"""
        raster = self.r_interface.getRaster(
            dataset_id=dataset_id,
            extent=ro.FloatVector(extent)
        )
        return self._r_raster_to_numpy(raster)
```

### 2. Data Update Strategy
```python
# scheduled_updates.py
class MAPDataUpdater:
    def __init__(self, db_connection):
        self.db = db_connection
        self.pipeline = MAPDataPipeline()

    def update_country_data(self, country):
        """Update all MAP data for a country"""
        # Fetch latest PR data
        pr_data = self.pipeline.fetch_pr_data(country)

        # Update database
        self.db.bulk_upsert('pr_surveys', pr_data)

        # Fetch latest risk surfaces
        current_year = datetime.now().year
        dataset_id = f"Plasmodium_falciparum_PR_{current_year-1}"

        try:
            risk_data = self.pipeline.fetch_risk_raster(
                dataset_id=dataset_id,
                extent=self._get_country_extent(country)
            )
            self._store_raster(country, risk_data)
        except Exception as e:
            logger.warning(f"Risk raster not available for {current_year-1}")
```

### 3. Error Handling and Fallbacks
```python
class RobustMAPClient:
    def __init__(self):
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds

    def fetch_with_retry(self, fetch_func, *args, **kwargs):
        """Fetch data with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                return fetch_func(*args, **kwargs)
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise DataFetchError(f"Failed after {self.retry_attempts} attempts: {e}")
```

## Best Practices and Recommendations

### 1. Data Management
- **Cache frequently accessed data** locally to reduce API calls
- **Version control** downloaded datasets with timestamps
- **Validate data integrity** after downloads
- **Monitor for data updates** through MAP announcements

### 2. Performance Optimization
- **Batch requests** when downloading multiple countries/years
- **Use spatial indexing** for efficient point-in-polygon queries
- **Compress stored rasters** to save disk space
- **Implement parallel downloads** for large batch operations

### 3. Integration Considerations
- **Use R for data access**, Python for processing/analysis
- **Standardize coordinate systems** (WGS-84) across datasets
- **Handle missing data** appropriately in statistical models
- **Document data lineage** for reproducibility

### 4. Production Deployment
```yaml
# docker-compose.yml
services:
  map_data_service:
    build: ./map_service
    environment:
      - R_LIBS_USER=/usr/local/lib/R/site-library
    volumes:
      - ./data/map_cache:/app/data/map_cache
    command: python data_updater.py
```

## Alternative Data Sources

### 1. Google Earth Engine
- MAP data available via Earth Engine catalog
- Requires Google Cloud account
- Better for large-scale raster processing

### 2. Direct Downloads
- Some datasets available as static files
- Contact MAP team for bulk historical data
- Email: malariaatlas@telethonkids.org.au

### 3. Related APIs
- **WHO Malaria API**: Case/death statistics
- **Climate Data Store**: Environmental covariates
- **WorldPop**: Population density layers

## Conclusion

The Malaria Atlas Project provides comprehensive malaria data through the malariaAtlas R package. While no native Python API exists, integration is achievable through R-Python bridges or pre-processing workflows. The CC BY 3.0 license allows commercial use with attribution, and no rate limits are documented, making it suitable for production systems. Key considerations include implementing robust caching, handling data updates, and maintaining proper attribution.
