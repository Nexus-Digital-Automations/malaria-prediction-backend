# MODIS Vegetation Indices Data Pipeline

This document describes how to use the MODIS vegetation indices data pipeline for malaria prediction environmental data.

## Overview

The MODIS client provides access to NASA's MODIS vegetation indices data (MOD13Q1/MYD13Q1) which includes:

- **NDVI (Normalized Difference Vegetation Index)**: Measures vegetation greenness and health
- **EVI (Enhanced Vegetation Index)**: Improved vegetation index with better sensitivity
- **16-day composites**: Cloud-free vegetation index composites
- **250m spatial resolution**: High-resolution environmental data
- **Quality filtering**: Automated cloud and quality masking

## Prerequisites

1. **NASA EarthData Account**: Register at https://urs.earthdata.nasa.gov/
2. **Data Access Approval**: Approve "LP DAAC Data Pool" application
3. **Dependencies**: Install required packages: `pip install rasterio h5py pyproj`

## Setup Authentication

```bash
# Set up NASA EarthData credentials
export NASA_EARTHDATA_USERNAME=your_username
export NASA_EARTHDATA_PASSWORD=your_password

# Or add to .env file
echo "NASA_EARTHDATA_USERNAME=your_username" >> .env
echo "NASA_EARTHDATA_PASSWORD=your_password" >> .env

# Test setup
malaria-predictor modis-setup
```

## Basic Usage

### 1. Data Ingestion (Recommended)

```bash
# Download recent MODIS data for Africa
malaria-predictor ingest-data --source modis

# Dry run to see what would be downloaded
malaria-predictor ingest-data --source modis --dry-run
```

### 2. Custom Downloads

```bash
# Download specific product and date range
malaria-predictor modis-download \
    --product MOD13Q1 \
    --start-date 2023-01-01 \
    --end-date 2023-01-31 \
    --area-bounds "30,-5,45,15"

# Download for specific region (East Africa)
malaria-predictor modis-download \
    --area-bounds "30,-5,45,15"  # west,south,east,north
```

### 3. Data Processing

```bash
# Process downloaded HDF files
malaria-predictor modis-process \
    /path/to/MOD13Q1.A2023001.h21v08.061.hdf \
    --vegetation-indices NDVI,EVI \
    --quality-filter

# Validate downloaded files
malaria-predictor modis-validate \
    /path/to/MOD13Q1.A2023001.h21v08.061.hdf
```

### 4. Temporal Aggregation

```bash
# Create monthly NDVI composites
malaria-predictor modis-aggregate \
    ./data/modis/processed \
    --vegetation-index NDVI \
    --method monthly

# Create seasonal aggregates
malaria-predictor modis-aggregate \
    ./data/modis/processed \
    --method seasonal \
    --output-file seasonal_ndvi_2023.tif
```

## Python API Usage

```python
from malaria_predictor.services.modis_client import MODISClient
from datetime import date

# Initialize client
client = MODISClient()

# Authenticate
client.authenticate(username, password)

# Download data
result = client.download_vegetation_indices(
    start_date=date(2023, 1, 1),
    end_date=date(2023, 1, 16),
    product="MOD13Q1",
    area_bounds=(-20.0, -35.0, 55.0, 40.0)  # Africa
)

# Process vegetation indices
if result.success:
    for file_path in result.file_paths:
        processing_results = client.process_vegetation_indices(
            file_path,
            vegetation_indices=["NDVI", "EVI"],
            apply_quality_filter=True
        )

        for proc_result in processing_results:
            if proc_result.success:
                print(f"{proc_result.vegetation_index}: {proc_result.statistics}")

# Clean up
client.close()
```

## Data Products

### MOD13Q1 (Terra)
- **Satellite**: Terra
- **Temporal Resolution**: 16-day composites
- **Spatial Resolution**: 250m
- **Coverage**: Global
- **Availability**: 2000-present

### MYD13Q1 (Aqua)
- **Satellite**: Aqua
- **Temporal Resolution**: 16-day composites
- **Spatial Resolution**: 250m
- **Coverage**: Global
- **Availability**: 2002-present

## Quality Control

The pipeline includes comprehensive quality control:

1. **VI Quality Flags**: Automatic filtering using MODIS quality flags
2. **Cloud Masking**: Removal of cloudy pixels
3. **Data Validation**: File integrity and format validation
4. **Outlier Detection**: Statistical outlier identification
5. **Temporal Consistency**: Cross-temporal validation

## File Organization

```
data/
├── modis/
│   ├── MOD13Q1.A2023001.h21v08.061.hdf    # Raw MODIS files
│   ├── processed/
│   │   ├── MOD13Q1.A2023001.h21v08.061_NDVI_processed.tif
│   │   └── MOD13Q1.A2023001.h21v08.061_EVI_processed.tif
│   └── aggregated/
│       ├── MODIS_NDVI_monthly_2023-01.tif
│       └── MODIS_EVI_seasonal_2023-Q1.tif
```

## MODIS Tile Grid

MODIS data is organized in a global tile grid system:
- **Horizontal tiles**: 36 tiles (h00-h35)
- **Vertical tiles**: 18 tiles (v00-v17)
- **Tile size**: ~1200km x 1200km
- **Africa coverage**: Typically h16-h23, v05-v11

## Troubleshooting

### Authentication Issues
```bash
# Check credentials
echo $NASA_EARTHDATA_USERNAME

# Test authentication
malaria-predictor modis-setup
```

### Missing Data
- MODIS has 3-7 day processing delay
- Some tiles may have seasonal data gaps
- Check NASA LAADS DAAC for data availability

### Processing Errors
- Ensure rasterio and h5py are installed
- Check file integrity with validation command
- Verify sufficient disk space

## Integration with Malaria Prediction

MODIS vegetation indices provide critical environmental variables for malaria prediction:

1. **Vector Habitat Monitoring**: NDVI indicates vegetation that supports mosquito breeding
2. **Seasonal Patterns**: EVI tracks vegetation phenology affecting transmission cycles
3. **Environmental Change**: Long-term vegetation trends indicate habitat changes
4. **High Resolution**: 250m resolution enables local-scale risk assessment

## Performance Considerations

- **Download Speed**: ~1-5 MB/minute depending on connection
- **Processing Time**: ~30 seconds per HDF file
- **Storage**: ~2-5 MB per tile per 16-day period
- **Memory Usage**: ~500MB peak during processing

## Support

For technical support and questions:
- Check the [GitHub Issues](https://github.com/your-org/malaria-predictor/issues)
- Review MODIS documentation at [NASA LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/)
- Contact the development team
