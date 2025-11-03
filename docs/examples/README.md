# Code Examples

> **💻 Practical code examples for common use cases**

## Table of Contents
- [Quick Start Examples](#quick-start-examples)
- [API Usage Examples](#api-usage-examples)
- [ML Model Examples](#ml-model-examples)
- [Data Processing Examples](#data-processing-examples)
- [Integration Examples](#integration-examples)

---

## Quick Start Examples

### Simple Prediction Request

**Python**:
```python
import requests
from datetime import date

# API endpoint
BASE_URL = "https://api.example.com"

# Authenticate
auth_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "your_username", "password": "your_password"}
)
token = auth_response.json()["access_token"]

# Make prediction
headers = {"Authorization": f"Bearer {token}"}
prediction_request = {
    "location": {
        "latitude": -1.2921,
        "longitude": 36.8219,
        "area_name": "Nairobi, Kenya"
    },
    "environmental_data": {
        "mean_temperature": 22.5,
        "monthly_rainfall": 85.2,
        "relative_humidity": 68.5,
        "elevation": 1795.0
    },
    "prediction_date": date.today().isoformat(),
    "model_type": "ensemble"
}

response = requests.post(
    f"{BASE_URL}/predict/single",
    headers=headers,
    json=prediction_request
)

prediction = response.json()
print(f"Risk Score: {prediction['prediction']['risk_score']}")
print(f"Risk Level: {prediction['prediction']['risk_level']}")
```

**cURL**:
```bash
# Get token
TOKEN=$(curl -X POST "https://api.example.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | jq -r '.access_token')

# Make prediction
curl -X POST "https://api.example.com/predict/single" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "latitude": -1.2921,
      "longitude": 36.8219
    },
    "environmental_data": {
      "mean_temperature": 22.5,
      "monthly_rainfall": 85.2,
      "relative_humidity": 68.5,
      "elevation": 1795.0
    },
    "prediction_date": "2025-12-01",
    "model_type": "ensemble"
  }'
```

---

## API Usage Examples

### Batch Predictions

```python
# batch_predictions.py
from typing import List, Dict
import requests
import pandas as pd

class MalariaBatchPredictor:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def predict_from_csv(self, csv_path: str) -> pd.DataFrame:
        """Read locations from CSV and get batch predictions"""

        # Read locations
        locations_df = pd.read_csv(csv_path)

        # Prepare batch request
        locations = [
            {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "area_name": row.get("area_name", "")
            }
            for _, row in locations_df.iterrows()
        ]

        # Make batch request
        response = requests.post(
            f"{self.api_url}/predict/batch",
            headers=self.headers,
            json={
                "locations": locations,
                "time_horizon_days": 30,
                "model_type": "ensemble"
            }
        )

        # Parse results
        predictions = response.json()["predictions"]

        # Convert to DataFrame
        results = []
        for loc, pred in zip(locations, predictions):
            results.append({
                "area_name": loc["area_name"],
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "risk_score": pred["prediction"]["risk_score"],
                "risk_level": pred["prediction"]["risk_level"],
                "confidence": pred["prediction"]["confidence"]
            })

        return pd.DataFrame(results)

# Usage
predictor = MalariaBatchPredictor(
    api_url="https://api.example.com",
    token="your_token_here"
)

results_df = predictor.predict_from_csv("health_facilities.csv")
results_df.to_csv("predictions_output.csv", index=False)
print(results_df)
```

### Time Series Predictions

```python
# time_series_predictions.py
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def get_time_series_prediction(
    api_url: str,
    token: str,
    latitude: float,
    longitude: float,
    days: int = 90
) -> pd.DataFrame:
    """Get time series predictions for a location"""

    headers = {"Authorization": f"Bearer {token}"}

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    response = requests.post(
        f"{api_url}/predict/time-series",
        headers=headers,
        json={
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interval_days": 7
        }
    )

    predictions = response.json()["predictions"]

    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "date": pd.to_datetime(p["prediction_date"]),
            "risk_score": p["prediction"]["risk_score"],
            "risk_level": p["prediction"]["risk_level"],
            "confidence": p["prediction"]["confidence"]
        }
        for p in predictions
    ])

    return df

def plot_time_series(df: pd.DataFrame, location_name: str):
    """Plot time series predictions"""

    plt.figure(figsize=(12, 6))

    # Risk score trend
    plt.plot(df["date"], df["risk_score"], marker='o', label='Risk Score')

    # Risk level zones
    plt.axhline(y=0.3, color='green', linestyle='--', alpha=0.5, label='Low Risk')
    plt.axhline(y=0.6, color='yellow', linestyle='--', alpha=0.5, label='Medium Risk')
    plt.axhline(y=0.8, color='orange', linestyle='--', alpha=0.5, label='High Risk')

    plt.title(f'Malaria Risk Forecast - {location_name}')
    plt.xlabel('Date')
    plt.ylabel('Risk Score')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{location_name}_forecast.png')
    plt.show()

# Usage
df = get_time_series_prediction(
    api_url="https://api.example.com",
    token="your_token",
    latitude=-1.2921,
    longitude=36.8219,
    days=90
)

plot_time_series(df, "Nairobi")
```

---

## ML Model Examples

### Custom Model Training

```python
# train_custom_model.py
import torch
import pytorch_lightning as pl
from malaria_predictor.ml.models import LSTMModel
from malaria_predictor.ml.data import MalariaDataModule
import mlflow

def train_lstm_model(
    data_path: str,
    hidden_dim: int = 128,
    num_layers: int = 3,
    dropout: float = 0.3,
    max_epochs: int = 100
):
    """Train LSTM model with custom parameters"""

    # Setup MLflow
    mlflow.set_experiment("malaria_prediction")

    with mlflow.start_run():
        # Log parameters
        mlflow.log_params({
            "model_type": "lstm",
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout,
            "max_epochs": max_epochs
        })

        # Initialize data module
        data_module = MalariaDataModule(
            data_path=data_path,
            batch_size=64,
            sequence_length=90,
            num_workers=4
        )

        # Initialize model
        model = LSTMModel(
            input_dim=20,  # Number of environmental features
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            learning_rate=0.001
        )

        # Setup trainer
        trainer = pl.Trainer(
            max_epochs=max_epochs,
            accelerator="gpu" if torch.cuda.is_available() else "cpu",
            callbacks=[
                pl.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    mode='min'
                ),
                pl.callbacks.ModelCheckpoint(
                    monitor='val_loss',
                    dirpath='checkpoints/',
                    filename='lstm-{epoch:02d}-{val_loss:.2f}',
                    save_top_k=3,
                    mode='min'
                )
            ]
        )

        # Train model
        trainer.fit(model, data_module)

        # Evaluate on test set
        test_results = trainer.test(model, data_module)

        # Log metrics
        mlflow.log_metrics({
            "test_loss": test_results[0]["test_loss"],
            "test_accuracy": test_results[0]["test_accuracy"],
            "test_f1_score": test_results[0]["test_f1_score"]
        })

        # Log model
        mlflow.pytorch.log_model(model, "model")

        print(f"Training complete! Test accuracy: {test_results[0]['test_accuracy']:.4f}")

        return model

# Usage
model = train_lstm_model(
    data_path="training_data.parquet",
    hidden_dim=128,
    num_layers=3,
    dropout=0.3,
    max_epochs=100
)
```

### Model Inference

```python
# model_inference.py
import torch
import numpy as np
from malaria_predictor.ml.models import EnsembleModel
from malaria_predictor.ml.features import FeatureEngineer

class MalariaPredictor:
    def __init__(self, model_path: str):
        """Initialize predictor with trained model"""
        self.model = EnsembleModel.load_from_checkpoint(model_path)
        self.model.eval()
        self.feature_engineer = FeatureEngineer()

    def predict(
        self,
        environmental_data: dict,
        historical_data: np.ndarray
    ) -> dict:
        """Make prediction from environmental data"""

        # Engineer features
        features = self.feature_engineer.transform(
            environmental_data,
            historical_data
        )

        # Convert to tensor
        features_tensor = torch.FloatTensor(features).unsqueeze(0)

        # Make prediction
        with torch.no_grad():
            output = self.model(features_tensor)
            risk_score = torch.sigmoid(output).item()

            # Get uncertainty estimates
            uncertainty = self.model.predict_uncertainty(features_tensor)

        # Classify risk level
        risk_level = self._classify_risk(risk_score)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": 1 - uncertainty.item(),
            "uncertainty_bounds": {
                "lower": max(0, risk_score - uncertainty.item()),
                "upper": min(1, risk_score + uncertainty.item())
            }
        }

    def _classify_risk(self, risk_score: float) -> str:
        """Classify risk score into categories"""
        if risk_score < 0.3:
            return "LOW"
        elif risk_score < 0.6:
            return "MEDIUM"
        elif risk_score < 0.8:
            return "HIGH"
        else:
            return "VERY_HIGH"

# Usage
predictor = MalariaPredictor(model_path="models/ensemble_v1.2.0.ckpt")

environmental_data = {
    "temperature": 22.5,
    "rainfall": 85.2,
    "humidity": 68.5,
    "ndvi": 0.45
}

historical_data = np.random.randn(90, 20)  # 90 days of historical features

prediction = predictor.predict(environmental_data, historical_data)
print(prediction)
```

---

## Data Processing Examples

### Environmental Data Ingestion

```python
# ingest_era5_data.py
import cdsapi
import xarray as xr
import pandas as pd
from sqlalchemy import create_engine

class ERA5DataIngester:
    def __init__(self, database_url: str, cds_api_key: str):
        self.engine = create_engine(database_url)
        self.cds_client = cdsapi.Client(key=cds_api_key)

    def ingest_monthly_data(
        self,
        year: int,
        month: int,
        region: dict
    ):
        """Ingest ERA5 data for a specific month and region"""

        # Download data from CDS
        self.cds_client.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': [
                    '2m_temperature',
                    'total_precipitation',
                    'relative_humidity'
                ],
                'year': str(year),
                'month': f'{month:02d}',
                'day': [f'{d:02d}' for d in range(1, 32)],
                'time': '12:00',
                'area': [
                    region['north'], region['west'],
                    region['south'], region['east']
                ],
                'format': 'netcdf'
            },
            'era5_download.nc'
        )

        # Load and process data
        ds = xr.open_dataset('era5_download.nc')

        # Convert to DataFrame
        df = ds.to_dataframe().reset_index()

        # Transform data
        df['temperature_celsius'] = df['t2m'] - 273.15  # Kelvin to Celsius
        df['rainfall_mm'] = df['tp'] * 1000  # meters to millimeters

        # Insert into database
        df.to_sql(
            'environmental_data',
            self.engine,
            if_exists='append',
            index=False
        )

        print(f"Ingested ERA5 data for {year}-{month:02d}")

# Usage
ingester = ERA5DataIngester(
    database_url="postgresql://user:password@localhost/malaria_db",
    cds_api_key="your_cds_api_key"
)

ingester.ingest_monthly_data(
    year=2025,
    month=11,
    region={
        'north': 5,
        'south': -5,
        'east': 45,
        'west': 30
    }
)
```

### Data Harmonization

```python
# harmonize_data.py
import pandas as pd
import geopandas as gpd
from rasterio import features
from shapely.geometry import Point

class DataHarmonizer:
    def __init__(self, target_resolution: float = 0.01):
        """
        Initialize data harmonizer

        Args:
            target_resolution: Target spatial resolution in degrees (~1km)
        """
        self.target_resolution = target_resolution

    def harmonize_spatial(
        self,
        era5_data: pd.DataFrame,
        chirps_data: pd.DataFrame,
        modis_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Harmonize data from multiple sources to common grid"""

        # Create common grid
        grid = self._create_grid(era5_data)

        # Resample each dataset to common grid
        era5_resampled = self._resample_to_grid(era5_data, grid, "era5")
        chirps_resampled = self._resample_to_grid(chirps_data, grid, "chirps")
        modis_resampled = self._resample_to_grid(modis_data, grid, "modis")

        # Merge datasets
        harmonized = pd.merge(
            era5_resampled,
            chirps_resampled,
            on=['latitude', 'longitude', 'date'],
            how='outer'
        )

        harmonized = pd.merge(
            harmonized,
            modis_resampled,
            on=['latitude', 'longitude', 'date'],
            how='outer'
        )

        # Fill missing values
        harmonized = self._fill_missing_values(harmonized)

        return harmonized

    def _create_grid(self, reference_data: pd.DataFrame) -> gpd.GeoDataFrame:
        """Create regular grid based on reference data extent"""

        lat_min, lat_max = reference_data['latitude'].min(), reference_data['latitude'].max()
        lon_min, lon_max = reference_data['longitude'].min(), reference_data['longitude'].max()

        lats = np.arange(lat_min, lat_max, self.target_resolution)
        lons = np.arange(lon_min, lon_max, self.target_resolution)

        grid_points = [
            Point(lon, lat)
            for lat in lats
            for lon in lons
        ]

        return gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:4326")

    def _resample_to_grid(
        self,
        data: pd.DataFrame,
        grid: gpd.GeoDataFrame,
        source_name: str
    ) -> pd.DataFrame:
        """Resample data to common grid using interpolation"""

        # Implementation of spatial interpolation
        # Using nearest neighbor or kriging
        pass

    def _fill_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values using interpolation"""

        # Temporal interpolation
        data = data.groupby(['latitude', 'longitude']).apply(
            lambda group: group.interpolate(method='time', limit=7)
        )

        # Spatial interpolation for remaining gaps
        # Using inverse distance weighting or kriging

        return data

# Usage
harmonizer = DataHarmonizer(target_resolution=0.01)

harmonized_data = harmonizer.harmonize_spatial(
    era5_data=pd.read_csv('era5_data.csv'),
    chirps_data=pd.read_csv('chirps_data.csv'),
    modis_data=pd.read_csv('modis_data.csv')
)

harmonized_data.to_parquet('harmonized_data.parquet')
```

---

## Integration Examples

### Flask Webhook Integration

```python
# webhook_receiver.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook/prediction', methods=['POST'])
def receive_prediction():
    """Receive prediction webhook from API"""

    data = request.json

    # Extract prediction data
    risk_score = data['prediction']['risk_score']
    risk_level = data['prediction']['risk_level']
    location = data['metadata']['location']

    # Trigger actions based on risk level
    if risk_level in ['HIGH', 'VERY_HIGH']:
        # Send alert to health authorities
        send_alert(
            location=location,
            risk_score=risk_score,
            risk_level=risk_level
        )

        # Update dashboard
        update_dashboard(data)

    return jsonify({"status": "received"}), 200

def send_alert(location: dict, risk_score: float, risk_level: str):
    """Send alert to health authorities"""

    # Send email notification
    # Send SMS
    # Update monitoring dashboard
    pass

def update_dashboard(prediction_data: dict):
    """Update real-time dashboard"""

    # Push to WebSocket clients
    # Update database
    pass

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Additional Examples

More examples available in:
- [GitHub Repository Examples](https://github.com/yourorg/malaria-prediction-examples)
- [Jupyter Notebooks](../notebooks/)
- [User Guides](../user-guides/)

---

**Last Updated**: November 3, 2025
