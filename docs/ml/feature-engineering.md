# Feature Engineering

> **Transform raw environmental data into ML-ready features**

## Feature Categories

### 1. Climate Features (ERA5)
```python
# Temperature features
features['temp_mean'] = normalize(era5_data['temperature_2m'])
features['temp_min'] = normalize(era5_data['temperature_2m_min'])
features['temp_max'] = normalize(era5_data['temperature_2m_max'])
features['temp_range'] = features['temp_max'] - features['temp_min']

# Rainfall
features['rainfall_mm'] = normalize(chirps_data['precipitation'])
features['rainfall_7d'] = rolling_sum(features['rainfall_mm'], 7)
features['rainfall_30d'] = rolling_sum(features['rainfall_mm'], 30)

# Humidity
features['humidity'] = normalize(era5_data['relative_humidity'])
```

### 2. Vegetation Features (MODIS)
```python
# NDVI (Normalized Difference Vegetation Index)
features['ndvi'] = modis_data['ndvi']
features['ndvi_anomaly'] = features['ndvi'] - features['ndvi'].rolling(90).mean()

# EVI (Enhanced Vegetation Index)
features['evi'] = modis_data['evi']
```

### 3. Temporal Features
```python
# Seasonality encoding
features['month_sin'] = np.sin(2 * np.pi * month / 12)
features['month_cos'] = np.cos(2 * np.pi * month / 12)

# Lag features
for lag in [7, 14, 30]:
    features[f'cases_lag_{lag}'] = malaria_cases.shift(lag)
```

### 4. Geographic Features
```python
# Static features
features['latitude'] = location.latitude
features['longitude'] = location.longitude
features['elevation'] = get_elevation(location)
features['population_density'] = worldpop_data['density']
```

## Feature Importance

| Feature | Importance | Source |
|---------|-----------|--------|
| Rainfall (30d sum) | 0.28 | CHIRPS |
| Temperature (mean) | 0.22 | ERA5 |
| Cases (lag 7d) | 0.18 | MAP |
| NDVI | 0.12 | MODIS |
| Humidity | 0.10 | ERA5 |
| Others | 0.10 | Various |

## Normalization

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Standard scaling (mean=0, std=1)
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Min-max scaling ([0, 1])
minmax = MinMaxScaler()
features_normalized = minmax.fit_transform(features)
```

---

**Last Updated**: October 27, 2025
