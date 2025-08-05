# WorldPop Data Access Research

## Executive Summary

WorldPop provides comprehensive global population distribution data at high spatial resolution (100m and 1km), including demographic breakdowns by age and gender. This research document covers data access methods, available datasets, formats, and integration strategies for population-at-risk calculations in the malaria prediction system.

## WorldPop Data Portal Overview

### Organization Mission
WorldPop specializes in geospatial data integration to construct open datasets on subnational population age and sex structures. Since 2013, they have partnered with governments, UN agencies, and donors to construct more than 45,000 demographic datasets.

### Key Capabilities
- High-resolution population distribution (100m × 100m grid cells)
- Age and sex structure breakdowns
- Temporal coverage from 2000-2030
- Both constrained and unconstrained population distribution models
- Global coverage with focus on low and middle-income countries

## Available Datasets

### 1. Population Density Datasets

#### Global Population Counts
- **Resolution**: 100m × 100m and 1km × 1km grid cells
- **Coverage**: Global, with emphasis on low and middle-income countries
- **Temporal Range**: 2000-2021 (historical), 2022-2030 (projections)
- **Update Frequency**: Annual updates, with major releases aligned to census rounds

#### Dataset Types
1. **Unconstrained (Top-down)**
   - Population distributed based on environmental and infrastructure covariates
   - No administrative boundary constraints
   - Better for rural/remote areas

2. **Constrained (Top-down)**
   - Population totals matched to administrative unit boundaries
   - More accurate for administrative reporting
   - Preferred for official statistics alignment

### 2. Demographic Variables

#### Age Structure
- **Age Groups**:
  - 00: 0-12 months
  - 01: 1-4 years
  - 05: 5-9 years
  - Continuing in 5-year intervals up to 90+
- **Format**: Separate raster files for each age group
- **Resolution**: Available at both 100m and 1km

#### Gender Categories
- **Male (m)**: Separate raster files for male population
- **Female (f)**: Separate raster files for female population
- **Total (t)**: Combined population rasters

#### File Naming Convention
```
{iso}_{gender}_{age_group}_{year}_{type}_{resolution}.tif
```
Example: `nga_m_05_2020_CN_100m.tif` (Nigeria, male, 5-9 years, 2020, constrained, 100m)

### 3. Special Datasets

#### 2024 Alpha Release
- Unconstrained individual countries 2024 (100m resolution)
- Alpha version estimates subject to revision
- Full 2015-2030 time series expected early 2025

#### Urban/Rural Growth Adjustments
- Datasets adjusted using UN World Urbanization Prospects
- Available for 2010, 2015, and 2020 benchmarks
- Both adjusted and unadjusted versions available

## API Endpoints and Data Access Methods

### 1. REST API

#### Base URLs
- **Services API**: `https://api.worldpop.org/v1/services`
- **Data API**: `https://www.worldpop.org/rest/data`

#### Population Statistics Query
```
https://api.worldpop.org/v1/services/stats?dataset={dataset_name}&year={year}&geojson={geojson}&key={your_key}
```

Parameters:
- `dataset_name`: "wpgppop" (population) or "wpgpas" (age/sex)
- `year`: 2000-2020 (expanding to 2030)
- `geojson`: Area of interest in GeoJSON format
- `key`: API key for enhanced functionality

#### Example API Request
```python
import requests
import json

# Define area of interest (GeoJSON)
aoi = {
    "type": "Polygon",
    "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
}

# API request
url = "https://api.worldpop.org/v1/services/stats"
params = {
    "dataset": "wpgppop",
    "year": 2020,
    "geojson": json.dumps(aoi),
    "key": "your_api_key"
}

response = requests.get(url, params=params)
population_data = response.json()
```

### 2. Download Methods

#### Direct Web Download
- **URL**: https://www.worldpop.org/datacatalog/
- Tree-like navigation structure
- Individual file downloads
- Metadata available for each dataset

#### FTP Server
- Bulk download capability
- Mirror of website structure
- Suitable for automated synchronization
- Anonymous access available

#### Python Tools
- **wpgpDownload**: Python package for finding and downloading WorldPop data
- **wpgpDataAPD**: ESRI plugin/ArcPy toolbox
- Available on GitHub: https://github.com/wpgp

### 3. Platform Integrations

#### Google Earth Engine
- Collections available:
  - `WorldPop/GP/100m/pop`
  - `WorldPop/GP/100m/pop_age_sex`
  - `WorldPop/GP/100m/pop_age_sex_cons_unadj`

#### Humanitarian Data Exchange (HDX)
- 480+ datasets available
- Standardized metadata
- Regular updates
- API access through HDX platform

## Data Formats and Resolutions

### 1. Raster Formats

#### GeoTIFF
- **Primary format** for all population rasters
- **Projection**: Geographic Coordinate System, WGS84
- **Data type**: Float32
- **NoData value**: -99999
- **Units**: Number of people per grid cell

#### ASCII XYZ
- Alternative format for compatibility
- Text-based representation
- Larger file sizes but universal readability

### 2. Spatial Resolutions

#### 100m Resolution (3 arc-seconds)
- Approximately 100m × 100m at equator
- Varies with latitude
- Highest detail available
- Larger file sizes

#### 1km Resolution (30 arc-seconds)
- Approximately 1km × 1km at equator
- Suitable for regional analyses
- Smaller file sizes
- Faster processing

### 3. File Structure

#### Single-band Rasters
- One value per pixel (population count)
- Separate files for each demographic category
- Facilitates selective downloading

#### Metadata Files
- XML or JSON format
- Processing history
- Accuracy assessments
- Input data sources

## Temporal Coverage and Update Frequency

### Historical Data
- **2000-2021**: Complete annual time series
- Based on census rounds and projections
- Both constrained and unconstrained versions

### Current Estimates
- **2022-2024**: Latest estimates (2024 in alpha)
- Updated annually
- Incorporates latest census data

### Projections
- **2025-2030**: Future projections
- Based on UN population projections
- Accounts for urban/rural growth rates
- Full series release expected early 2025

### Update Schedule
- **Major updates**: Aligned with census rounds (typically decadal)
- **Annual updates**: Incorporate new data sources and improvements
- **Custom updates**: Available for specific regions/requirements

## Metadata and Quality Indicators

### 1. Accuracy Assessments

#### Internal Validation
- Prediction errors by administrative unit
- Cross-validation statistics
- Feature importance rankings

#### Uncertainty Quantification
- Per-pixel uncertainty estimates
- Confidence intervals
- Model uncertainty maps

### 2. Quality Indicators

#### Input Data Quality
- Census year and quality
- Number of administrative units
- Covariate data completeness

#### Model Performance
- R-squared values
- Root Mean Square Error (RMSE)
- Mean Absolute Error (MAE)

### 3. Metadata Standards

#### File-level Metadata
- Creation date
- Processing workflow
- Input datasets used
- Model parameters

#### Dataset Documentation
- Peer-reviewed methodology papers
- Technical documentation
- Known limitations
- Appropriate use cases

## Integration Patterns for Population-at-Risk Calculations

### 1. Basic Population Extraction

```python
import rasterio
import numpy as np
from rasterio.mask import mask
import geopandas as gpd

def extract_population(population_raster, area_of_interest):
    """Extract population within area of interest"""

    # Open population raster
    with rasterio.open(population_raster) as src:
        # Mask raster with area of interest
        out_image, out_transform = mask(
            src,
            area_of_interest.geometry,
            crop=True
        )

        # Sum population (excluding NoData)
        population = np.sum(out_image[out_image != src.nodata])

    return population
```

### 2. Age-Specific Population at Risk

```python
def calculate_age_specific_risk(base_path, country_iso, year, age_groups, aoi):
    """Calculate population at risk for specific age groups"""

    risk_population = {}

    for age in age_groups:
        # Construct filename
        filename = f"{country_iso}_t_{age}_{year}_CN_100m.tif"
        filepath = os.path.join(base_path, filename)

        # Extract population for age group
        pop = extract_population(filepath, aoi)
        risk_population[age] = pop

    return risk_population
```

### 3. Weighted Risk Calculations

```python
def weighted_population_risk(population_raster, risk_surface, aoi):
    """Calculate risk-weighted population"""

    with rasterio.open(population_raster) as pop_src:
        with rasterio.open(risk_surface) as risk_src:
            # Ensure same resolution/alignment
            # Resample if necessary

            # Read both rasters
            pop_data = pop_src.read(1)
            risk_data = risk_src.read(1)

            # Calculate weighted population
            weighted_pop = pop_data * risk_data

            # Sum for total at-risk population
            total_risk = np.sum(weighted_pop[weighted_pop > 0])

    return total_risk
```

### 4. Multi-temporal Analysis

```python
def population_change_analysis(country_iso, years, aoi):
    """Analyze population changes over time"""

    population_series = {}

    for year in years:
        pop_file = f"{country_iso}_ppp_{year}_UNadj.tif"
        population_series[year] = extract_population(pop_file, aoi)

    # Calculate growth rates
    growth_rates = {}
    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]
        growth = (population_series[curr_year] - population_series[prev_year]) / population_series[prev_year]
        growth_rates[f"{prev_year}-{curr_year}"] = growth

    return population_series, growth_rates
```

### 5. Integration with Malaria Risk Models

```python
class PopulationRiskIntegrator:
    """Integrate WorldPop data with malaria risk models"""

    def __init__(self, worldpop_api_key):
        self.api_key = worldpop_api_key
        self.base_url = "https://api.worldpop.org/v1/services"

    def get_population_for_district(self, district_geojson, year=2020):
        """Get population data via API for a district"""

        params = {
            "dataset": "wpgppop",
            "year": year,
            "geojson": json.dumps(district_geojson),
            "key": self.api_key
        }

        response = requests.get(f"{self.base_url}/stats", params=params)
        return response.json()

    def calculate_par(self, district_geojson, prevalence_rate):
        """Calculate Population at Risk (PAR)"""

        # Get total population
        pop_data = self.get_population_for_district(district_geojson)
        total_pop = pop_data['total_population']

        # Calculate PAR
        par = total_pop * prevalence_rate

        return {
            'total_population': total_pop,
            'prevalence_rate': prevalence_rate,
            'population_at_risk': par
        }
```

## Best Practices and Recommendations

### 1. Data Selection
- Use **constrained** datasets when administrative boundary alignment is important
- Use **unconstrained** datasets for environmental/ecological analyses
- Select appropriate resolution based on analysis scale and computational resources

### 2. Performance Optimization
- Use 1km resolution for national/regional analyses
- Implement tile-based processing for large areas
- Cache frequently accessed data locally
- Use cloud-optimized GeoTIFF (COG) format when available

### 3. Quality Assurance
- Always check metadata for data vintage
- Validate population totals against official statistics
- Consider uncertainty estimates in decision-making
- Document data sources and processing steps

### 4. Temporal Consistency
- Use same dataset version for time series analysis
- Account for methodology changes between versions
- Apply consistent processing workflows
- Document any adjustments or corrections

### 5. Integration Architecture
- Implement data versioning system
- Create abstraction layer for data access
- Build caching mechanism for API calls
- Design for graceful degradation if data unavailable

## Production Implementation Strategy

### Phase 1: Infrastructure Setup
1. Set up WorldPop data storage architecture
2. Implement API client with authentication
3. Create data download and update automation
4. Build local caching system

### Phase 2: Data Processing Pipeline
1. Develop raster processing utilities
2. Implement demographic data extraction
3. Create population aggregation functions
4. Build uncertainty quantification module

### Phase 3: Integration with Malaria Models
1. Design population-risk calculation engine
2. Implement age-specific risk assessments
3. Create temporal analysis capabilities
4. Build reporting and visualization tools

### Phase 4: Optimization and Scaling
1. Implement parallel processing for large areas
2. Optimize data storage and retrieval
3. Create data quality monitoring
4. Build automated update mechanisms

### Phase 5: Validation and Testing
1. Validate against known population figures
2. Test edge cases and error handling
3. Performance testing at scale
4. User acceptance testing

## Licensing and Attribution

WorldPop datasets are licensed under the **Creative Commons Attribution 4.0 International License**. Users must:
- Provide clear attribution to WorldPop
- Indicate if changes were made
- Link to the license
- Not apply legal terms that restrict others' use

### Citation Format
```
WorldPop (www.worldpop.org - School of Geography and Environmental Science,
University of Southampton; Department of Geography and Geosciences, University
of Louisville; Departement de Geographie, Universite de Namur) and Center for
International Earth Science Information Network (CIESIN), Columbia University
(2018). Global High Resolution Population Denominators Project - Funded by
The Bill and Melinda Gates Foundation (OPP1134076).
https://dx.doi.org/10.5258/SOTON/WP00[SPECIFIC_ID]
```

## Conclusion

WorldPop provides comprehensive, high-quality population data essential for calculating population at risk in malaria prediction models. The combination of high spatial resolution, demographic breakdowns, and temporal coverage makes it ideal for health risk assessment applications. The production implementation should focus on efficient data access, proper handling of large raster datasets, and integration with existing malaria risk models while maintaining data quality and uncertainty quantification throughout the pipeline.
