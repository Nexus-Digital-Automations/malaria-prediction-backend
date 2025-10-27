# MAP (Malaria Atlas Project) Integration

> **Malaria prevalence and intervention data**

## Overview

MAP provides malaria prevalence estimates, intervention coverage, and historical case data.

**Datasets**:
- Malaria prevalence (Pf, Pv)
- Insecticide-treated net (ITN) coverage
- Indoor residual spraying (IRS) coverage
- Treatment-seeking behavior
- Drug resistance markers

## Data Access

### API Endpoint

```
https://malariaatlas.org/explorer/api
```

### Usage

```python
from src.malaria_predictor.services.map_client import MAPClient

# Initialize
map_client = MAPClient()

# Fetch prevalence data
prevalence = map_client.get_prevalence(
    species='pf',  # Plasmodium falciparum
    country='Kenya',
    year_range=(2010, 2023)
)

# Get intervention coverage
itn_coverage = map_client.get_itn_coverage(
    country='Kenya',
    year=2023
)
```

## Data Format

```python
{
    'location': {'latitude': -1.29, 'longitude': 36.82},
    'year': 2023,
    'prevalence_pf': 0.15,  # 15% prevalence
    'itn_coverage': 0.68,    # 68% coverage
    'irs_coverage': 0.12,
    'uncertainty_lower': 0.10,
    'uncertainty_upper': 0.22
}
```

## Integration

```python
# Use MAP data as ground truth for validation
def validate_predictions(predictions, map_data):
    actual = map_data['prevalence']
    predicted = predictions['risk_score']

    mae = np.mean(np.abs(actual - predicted))
    r2 = r2_score(actual, predicted)

    return {'mae': mae, 'r2': r2}
```

---

**Last Updated**: October 27, 2025
