# WorldPop Population Data Integration

> **High-resolution population distribution data**

## Overview

WorldPop provides population density estimates at 100m resolution.

**Datasets**:
- Population count
- Population density
- Age/sex structure
- Urbanization

## Data Access

### Download

```python
from src.malaria_predictor.services.worldpop_client import WorldPopClient

# Initialize
worldpop = WorldPopClient()

# Fetch population density
pop_data = worldpop.get_population_density(
    country='KEN',  # ISO 3-letter code
    year=2023,
    resolution='100m'
)

# Returns: GeoTIFF raster
```

### API Endpoint

```
https://www.worldpop.org/rest/data/{country}/{dataset}/{year}
```

## Data Format

```python
<xarray.DataArray>
Dimensions:  (latitude: 10000, longitude: 8000)
Coordinates:
  * latitude   (latitude) float64 ...
  * longitude  (longitude) float64 ...
Data:
    population_density  (latitude, longitude) float32 ...  # persons/km²
```

## Integration

```python
# Calculate affected population for high-risk areas
def calculate_affected_population(risk_map, population):
    high_risk_mask = risk_map > 0.7
    affected_pop = population.where(high_risk_mask).sum()

    return affected_pop.values
```

---

**Last Updated**: October 27, 2025
