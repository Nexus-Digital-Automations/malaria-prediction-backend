# MAP (Malaria Atlas Project) Client Usage Guide

The MAP client provides access to comprehensive malaria data from the Malaria Atlas Project, including parasite rate surfaces, vector occurrence data, and intervention coverage.

## Features

- **Parasite Rate Surfaces**: Download P. falciparum and P. vivax prevalence data
- **Vector Occurrence**: Access Anopheles mosquito distribution data
- **Intervention Coverage**: Get ITN, IRS, and ACT coverage data
- **Multiple Access Methods**: R integration via malariaAtlas package or HTTP fallback
- **Data Processing**: Convert raster data to arrays or DataFrames
- **Validation**: Comprehensive file validation
- **Caching**: Automatic local caching with cleanup utilities

## Installation

### Basic Installation
The MAP client is included with the malaria-predictor package:
```bash
pip install -e .
```

### Optional R Integration
For full functionality, install R and the malariaAtlas package:
```bash
# Install R (macOS example)
brew install r

# Install malariaAtlas package
R -e 'install.packages("malariaAtlas")'
```

### Python Dependencies
Required packages are included in the base installation:
- `rasterio`: For GeoTIFF processing
- `shapely`: For spatial operations
- `requests`: For HTTP downloads
- `numpy`: For array operations
- `pandas`: For DataFrame output (optional)

Optional for R integration:
```bash
pip install malaria-predictor[r-integration]
```

## CLI Usage

### 1. Basic Data Ingestion
Download all MAP data types:
```bash
malaria-predictor ingest-data --source map
```

Dry run to preview what would be downloaded:
```bash
malaria-predictor ingest-data --source map --dry-run
```

### 2. Download Specific Data

#### Parasite Rate Surface
```bash
# Download P. falciparum parasite rate for 2021
malaria-predictor map-download pr --year 2021 --species Pf --resolution 5km

# Download P. vivax data at 1km resolution
malaria-predictor map-download pr --year 2021 --species Pv --resolution 1km
```

#### Vector Occurrence Data
```bash
# Download Anopheles gambiae occurrence data
malaria-predictor map-download vector --year 2021
```

#### Intervention Coverage
```bash
# Download ITN (bed net) coverage
malaria-predictor map-download itn --year 2021

# Download IRS (indoor residual spraying) coverage
malaria-predictor map-download irs --year 2021

# Download ACT (artemisinin-based therapy) coverage
malaria-predictor map-download act --year 2021
```

### 3. Validate Downloaded Data
```bash
# Validate a MAP raster file
malaria-predictor map-validate ./data/map/Pf_parasite_rate_2021_5km.tif
```

### 4. Process Data
Extract statistics from raster files:
```bash
# Display statistics
malaria-predictor map-process ./data/map/Pf_parasite_rate_2021_5km.tif --output-format stats

# Convert to CSV
malaria-predictor map-process ./data/map/Pf_parasite_rate_2021_5km.tif \
    --output-format csv --output-file pr_data.csv
```

## Python API Usage

### Basic Example
```python
from malaria_predictor.services import MAPClient

# Initialize client
client = MAPClient()

# Download parasite rate data
result = client.download_parasite_rate_surface(
    year=2021,
    species="Pf",
    resolution="5km",
    area_bounds=(-20.0, -35.0, 55.0, 40.0)  # Africa bounds
)

if result.success:
    print(f"Downloaded {len(result.file_paths)} files")

    # Validate the file
    validation = client.validate_raster_file(result.file_paths[0])
    print(f"Valid: {validation['success']}")

    # Process the data
    pr_data = client.process_parasite_rate_data(
        result.file_paths[0],
        output_format="array"
    )
    print(f"Mean parasite rate: {pr_data.mean():.2f}%")

# Clean up
client.close()
```

### Advanced Processing
```python
import pandas as pd
from malaria_predictor.services import MAPClient

client = MAPClient()

# Download and process to DataFrame
result = client.download_parasite_rate_surface(year=2021)

if result.success:
    # Convert to DataFrame with lat/lon coordinates
    df = client.process_parasite_rate_data(
        result.file_paths[0],
        output_format="dataframe"
    )

    # Filter high-risk areas
    high_risk = df[df['parasite_rate'] > 20]
    print(f"High risk locations: {len(high_risk)}")

    # Save processed data
    high_risk.to_csv("high_risk_areas.csv", index=False)

client.close()
```

### Vector Data Example
```python
# Download vector occurrence data
vector_result = client.download_vector_occurrence_data(
    species_complex="gambiae",
    start_year=2015,
    end_year=2021,
    area_bounds=(-10, -20, 10, 0)  # Central Africa
)

if vector_result.success:
    # Read CSV data
    import pandas as pd
    df = pd.read_csv(vector_result.file_paths[0])

    # Analyze by year
    yearly_counts = df.groupby('year').size()
    print(yearly_counts)
```

## Data Formats

### Raster Files (GeoTIFF)
- **Parasite Rate**: Values 0-1 (multiply by 100 for percentage)
- **Intervention Coverage**: Values 0-1 (coverage fraction)
- **Resolution**: 5km (~0.05°) or 1km (~0.01°)
- **CRS**: WGS84 (EPSG:4326)

### Vector Data (CSV)
- **Columns**: species, latitude, longitude, year, month, source
- **Species**: Full taxonomic names (e.g., "Anopheles gambiae")
- **Coordinates**: Decimal degrees

## Configuration

### Environment Variables
```bash
# Set custom data directory
export MALARIA_DATA_DIR=/path/to/data

# Enable debug logging
export LOG_LEVEL=DEBUG
```

### Settings
```python
from malaria_predictor.config import Settings

settings = Settings(
    data_directory="/custom/data/path"
)

client = MAPClient(settings=settings)
```

## Troubleshooting

### R Integration Issues
If R integration is not working:
1. Check R installation: `R --version`
2. Check malariaAtlas package: `R -e 'library(malariaAtlas)'`
3. Install missing dependencies: `R -e 'install.packages(c("raster", "sp"))'`

### HTTP Fallback Limitations
When using HTTP fallback (no R):
- Limited to predefined datasets
- No custom spatial queries
- Some data types may be unavailable

### Common Errors

**File not found (404)**
- Check year availability (MAP data typically has 2-year delay)
- Verify data type and species combination
- Some historical data may not be available

**Large file downloads**
- MAP rasters can be large (>100MB for global data)
- Use area_bounds to limit spatial extent
- Consider using 5km resolution instead of 1km

**Memory issues**
- Process data in chunks for large areas
- Use area_bounds to limit data size
- Consider using cloud-optimized GeoTIFFs

## Best Practices

1. **Check R availability** first for optimal functionality
2. **Use area bounds** to limit download size and processing time
3. **Validate files** after download before processing
4. **Cache data locally** to avoid repeated downloads
5. **Clean up old files** periodically with `cleanup_old_files()`
6. **Handle missing data** - MAP uses NaN for no-data areas

## Data Citation

When using MAP data, please cite:
> Weiss et al. (2019). Mapping the global prevalence, incidence, and mortality of Plasmodium falciparum, 2000–17: a spatial and temporal modelling study. The Lancet, 394(10195), 322-331.

## Support

For issues specific to the MAP client:
- Check the [MAP website](https://malariaatlas.org/) for data availability
- Review the [malariaAtlas R package docs](https://github.com/malaria-atlas-project/malariaAtlas)
- Report bugs in the malaria-predictor issue tracker
