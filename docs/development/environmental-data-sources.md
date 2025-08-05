# Environmental Data Sources for Malaria Prediction

## Priority Data Sources for Implementation

### Temperature Data (Critical)
- **ERA5 Reanalysis**: 31km resolution, historical data from 1940-present
  - API: Copernicus Climate Data Store
  - Updates: 5-day latency for preliminary data
  - Usage: Daily mean/min/max temperatures, diurnal ranges, anomalies

- **MODIS Land Surface Temperature**: 1km resolution, daily since 2000
  - Access: NASA LAADS portal, Google Earth Engine
  - Usage: Day/night temperature variations

### Rainfall & Hydrology (Critical)
- **CHIRPS**: 5.5km resolution, daily precipitation from 1981-present
  - Access: AWS S3, Digital Earth Africa
  - Usage: Primary rainfall dataset, 3-week latency for final products

- **GPM IMERG**: 11km resolution, 30-minute temporal resolution
  - Access: NASA DISC
  - Usage: Real-time precipitation events, flood detection

### Vegetation Indices (Important)
- **MODIS NDVI/EVI**: 250m resolution, 16-day updates
  - Access: NASA Earthdata, Google Earth Engine
  - Usage: Vegetation health, moisture indicators

- **Sentinel-2**: 10m resolution, 5-day revisit
  - Access: Digital Earth Africa, Copernicus Hub
  - Usage: High-resolution vegetation analysis

### Vector & Health Data (Essential)
- **Malaria Atlas Project**: 5km resolution malaria risk maps
  - Access: Web API, R package, direct downloads
  - Usage: Baseline risk assessment, model validation

- **MalariaGEN Vector Observatory**: Genomic data on 25,510+ specimens
  - Access: Python API
  - Usage: Vector resistance analysis

## Implementation Priority

1. **Phase 1**: ERA5 (temperature) + CHIRPS (rainfall) + MAP (malaria data)
2. **Phase 2**: MODIS vegetation + WorldPop (population)
3. **Phase 3**: High-resolution Sentinel-2 + vector surveillance data

## API Integration Notes

- Most sources require free registration
- Use Digital Earth Africa as unified platform for African data
- Implement caching for large datasets
- Consider data latency in prediction models (5-day to 3-week delays)
