# Data Quality Validation

> **Automated quality checks for environmental data**

## Validation Framework

```python
from src.malaria_predictor.services.data_validator import DataValidator

validator = DataValidator()

# Run all checks
results = validator.validate(data)

if not results['passed']:
    raise DataQualityError(f"Failed checks: {results['failed_checks']}")
```

## Quality Checks

### 1. Completeness

```python
def check_completeness(data, threshold=0.9):
    """Check for missing values."""
    valid_ratio = data.notnull().sum() / data.size

    return {
        'passed': valid_ratio >= threshold,
        'valid_ratio': valid_ratio,
        'missing_count': data.isnull().sum()
    }
```

### 2. Plausibility

```python
def check_plausibility(data, variable):
    """Check values are within realistic ranges."""
    ranges = {
        'temperature': (-50, 60),  # Celsius
        'rainfall': (0, 500),       # mm/day
        'humidity': (0, 100),       # percent
        'ndvi': (-1, 1)
    }

    min_val, max_val = ranges[variable]
    valid = data.between(min_val, max_val)

    return {
        'passed': valid.all(),
        'invalid_count': (~valid).sum()
    }
```

### 3. Consistency

```python
def check_consistency(data):
    """Check temporal consistency."""
    # No sudden jumps
    daily_change = data.diff()
    threshold = data.std() * 3  # 3 sigma

    anomalies = daily_change.abs() > threshold

    return {
        'passed': ~anomalies.any(),
        'anomaly_count': anomalies.sum()
    }
```

### 4. Timeliness

```python
def check_timeliness(data, max_lag_days=7):
    """Check data is recent enough."""
    latest_date = data.time.max()
    age_days = (datetime.now() - latest_date).days

    return {
        'passed': age_days <= max_lag_days,
        'age_days': age_days,
        'latest_date': latest_date
    }
```

## Automated Monitoring

```python
# Run validation daily
def daily_validation_job():
    sources = ['era5', 'chirps', 'modis']

    for source in sources:
        data = fetch_latest_data(source)
        results = validator.validate(data)

        if not results['passed']:
            alert_team(f"{source} quality check failed: {results}")
            log_failure(source, results)
```

---

**Last Updated**: October 27, 2025
