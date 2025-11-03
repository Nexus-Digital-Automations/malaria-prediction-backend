# User Guides

> **📖 Practical guides for common tasks and workflows**

## Table of Contents
- [Quick Reference](#quick-reference)
- [For Healthcare Professionals](#for-healthcare-professionals)
- [For Data Scientists](#for-data-scientists)
- [For System Administrators](#for-system-administrators)
- [For API Developers](#for-api-developers)
- [Common Tasks](#common-tasks)

---

## Quick Reference

### Common Operations

| Task | Guide |
|------|-------|
| Make a prediction | [Single Prediction Guide](#single-prediction) |
| Batch predictions | [Batch Prediction Guide](#batch-predictions) |
| View historical trends | [Time Series Analysis](#time-series-analysis) |
| Generate reports | [Report Generation](#report-generation) |
| Set up alerts | [Alert Configuration](#alert-configuration) |
| Train models | [Model Training Guide](#model-training) |
| Deploy updates | [Deployment Guide](#deployment) |

---

## For Healthcare Professionals

### Single Prediction

**Use Case**: Get malaria risk prediction for a specific location and date.

**Step-by-Step Guide:**

1. **Authenticate** (obtain JWT token):
```bash
curl -X POST "https://api.example.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr.smith",
    "password": "your_password"
  }'

# Save the access_token from response
export TOKEN="<your_access_token>"
```

2. **Prepare Location Data**:
```json
{
  "location": {
    "latitude": -1.2921,
    "longitude": 36.8219,
    "area_name": "Nairobi, Kenya"
  }
}
```

3. **Gather Environmental Data** (from local weather station or use auto-fetch):
```json
{
  "environmental_data": {
    "mean_temperature": 22.5,
    "monthly_rainfall": 85.2,
    "relative_humidity": 68.5,
    "elevation": 1795.0
  }
}
```

4. **Make Prediction Request**:
```bash
curl -X POST "https://api.example.com/predict/single" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    "prediction_date": "2025-12-01",
    "model_type": "ensemble"
  }'
```

5. **Interpret Results**:
```json
{
  "prediction": {
    "risk_score": 0.73,        // 0.0-1.0 scale
    "risk_level": "HIGH",      // LOW, MEDIUM, HIGH, VERY_HIGH
    "confidence": 0.89,        // Model confidence (0.0-1.0)
    "uncertainty_bounds": {
      "lower": 0.61,
      "upper": 0.85
    }
  },
  "factors": {
    "temperature": {
      "contribution": 0.35,    // 35% of risk score
      "value": 22.5,
      "optimal_range": [18, 34]
    },
    "rainfall": {
      "contribution": 0.28,
      "value": 85.2,
      "threshold": 80
    }
  },
  "recommendations": [
    "Increase mosquito surveillance",
    "Prepare antimalarial stockpiles",
    "Issue public health advisory"
  ]
}
```

**Risk Level Interpretation:**

- **LOW** (0.0-0.3): Minimal risk, routine surveillance
- **MEDIUM** (0.3-0.6): Moderate risk, enhanced monitoring
- **HIGH** (0.6-0.8): High risk, prepare interventions
- **VERY HIGH** (0.8-1.0): Critical risk, immediate action required

### Batch Predictions

**Use Case**: Assess risk across multiple healthcare facilities.

```bash
curl -X POST "https://api.example.com/predict/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {
        "latitude": -1.2921,
        "longitude": 36.8219,
        "area_name": "Kenyatta National Hospital"
      },
      {
        "latitude": -1.3194,
        "longitude": 36.8290,
        "area_name": "Aga Khan Hospital"
      },
      {
        "latitude": -1.2667,
        "longitude": 36.8000,
        "area_name": "Nairobi West Hospital"
      }
    ],
    "time_horizon_days": 30,
    "model_type": "ensemble"
  }'
```

**Response**: Array of predictions for each location, allowing you to prioritize resource allocation.

### Alert Configuration

**Use Case**: Receive notifications when risk exceeds threshold.

```bash
# Create alert rule
curl -X POST "https://api.example.com/alerts/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nairobi High Risk Alert",
    "location": {
      "latitude": -1.2921,
      "longitude": 36.8219,
      "radius_km": 50
    },
    "conditions": {
      "risk_threshold": 0.7,
      "confidence_threshold": 0.8
    },
    "notification_channels": ["email", "sms", "push"],
    "frequency": "daily"
  }'
```

---

## For Data Scientists

### Model Training

**Use Case**: Train custom ML models with your own data.

**Prerequisites**:
- Python 3.11+ installed
- Training data in required format
- GPU recommended (optional)

**Step 1: Prepare Training Data**

```python
# prepare_data.py
import pandas as pd
from malaria_predictor.ml.data import FeatureEngineer

# Load historical data
environmental_data = pd.read_csv("environmental_data.csv")
malaria_cases = pd.read_csv("malaria_cases.csv")

# Feature engineering
engineer = FeatureEngineer()
features = engineer.create_features(
    environmental_data=environmental_data,
    malaria_cases=malaria_cases,
    lookback_days=90,
    forecast_days=30
)

# Save processed features
features.to_parquet("training_features.parquet")
```

**Step 2: Configure Training**

```yaml
# training_config.yaml
model:
  type: lstm  # lstm, transformer, or ensemble
  architecture:
    input_dim: 20
    hidden_dim: 128
    num_layers: 3
    dropout: 0.3
    bidirectional: true

training:
  batch_size: 64
  learning_rate: 0.001
  epochs: 100
  early_stopping_patience: 10
  validation_split: 0.2

data:
  features_path: "training_features.parquet"
  target_column: "malaria_cases"
  sequence_length: 90

mlflow:
  experiment_name: "malaria_prediction_v2"
  tracking_uri: "http://localhost:5000"
```

**Step 3: Train Model**

```bash
# Train using CLI
uv run malaria-predictor train \
  --config training_config.yaml \
  --model lstm \
  --gpu

# Or use Python API
python <<EOF
from malaria_predictor.ml.training import ModelTrainer

trainer = ModelTrainer(config_path="training_config.yaml")
results = trainer.train()

print(f"Best validation loss: {results['best_val_loss']}")
print(f"Model saved to: {results['model_path']}")
EOF
```

**Step 4: Evaluate Model**

```bash
# Evaluate on test set
uv run malaria-predictor evaluate \
  --model-path models/lstm_v2.pth \
  --test-data test_features.parquet \
  --output-dir evaluation_results/

# Generate evaluation report
ls evaluation_results/
# - confusion_matrix.png
# - roc_curve.png
# - feature_importance.png
# - metrics.json
```

### Hyperparameter Tuning

**Use Case**: Optimize model performance.

```python
# hyperparameter_tuning.py
from malaria_predictor.ml.tuning import HyperparameterTuner
import optuna

# Define search space
search_space = {
    "hidden_dim": optuna.Trial.suggest_int("hidden_dim", 64, 256),
    "num_layers": optuna.Trial.suggest_int("num_layers", 2, 5),
    "dropout": optuna.Trial.suggest_float("dropout", 0.1, 0.5),
    "learning_rate": optuna.Trial.suggest_loguniform("learning_rate", 1e-5, 1e-2)
}

# Run tuning
tuner = HyperparameterTuner(
    model_type="lstm",
    search_space=search_space,
    n_trials=100,
    timeout=3600  # 1 hour
)

best_params = tuner.optimize()
print(f"Best hyperparameters: {best_params}")
```

### Feature Engineering

**Use Case**: Create custom environmental features.

```python
from malaria_predictor.ml.features import FeatureEngineer

engineer = FeatureEngineer()

# Add custom features
@engineer.register_feature("temperature_anomaly")
def temperature_anomaly(data):
    """Calculate temperature deviation from historical mean"""
    historical_mean = data["temperature"].rolling(window=365).mean()
    return data["temperature"] - historical_mean

# Generate features
features = engineer.transform(environmental_data)
```

---

## For System Administrators

### Deployment

**Use Case**: Deploy the system to production.

**Docker Deployment**:

```bash
# 1. Clone repository
git clone https://github.com/yourorg/malaria-prediction-backend.git
cd malaria-prediction-backend

# 2. Configure environment
cp .env.production .env
nano .env  # Edit database credentials, API keys, etc.

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify deployment
curl -f http://localhost:8000/health/readiness
docker-compose ps
docker-compose logs -f api
```

**Kubernetes Deployment**:

```bash
# 1. Create namespace
kubectl create namespace malaria-prediction

# 2. Create secrets
kubectl create secret generic api-secrets \
  --from-env-file=.env.production \
  -n malaria-prediction

# 3. Deploy application
kubectl apply -f k8s/ -n malaria-prediction

# 4. Check deployment status
kubectl get pods -n malaria-prediction
kubectl get svc -n malaria-prediction

# 5. Access logs
kubectl logs -f deployment/malaria-api -n malaria-prediction
```

### Monitoring Setup

**Use Case**: Set up production monitoring.

```bash
# 1. Deploy Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# 2. Configure Grafana dashboards
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Navigate to http://localhost:3000
# Import dashboard: dashboards/grafana/malaria-api-dashboard.json

# 3. Configure alerts
kubectl apply -f monitoring/alert-rules.yaml
```

### Backup & Recovery

**Use Case**: Implement disaster recovery.

```bash
# Automated backup script
#!/bin/bash
# backup.sh

# Database backup
pg_dump -h localhost -U postgres -d malaria_db | \
  gzip > backups/malaria_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Upload to S3
aws s3 cp backups/ s3://malaria-backups/db/ --recursive

# Model registry backup
tar -czf backups/mlflow_$(date +%Y%m%d).tar.gz mlflow/

# Retention: Keep last 30 days
find backups/ -type f -mtime +30 -delete
```

**Recovery**:

```bash
# Restore database
gunzip -c backups/malaria_db_20251103_120000.sql.gz | \
  psql -h localhost -U postgres -d malaria_db

# Restore MLflow models
tar -xzf backups/mlflow_20251103.tar.gz -C mlflow/
```

---

## For API Developers

### Python SDK Example

**Use Case**: Integrate predictions into your Python application.

```python
# malaria_client.py
from typing import List, Dict
import requests
from datetime import date

class MalariaPredictionClient:
    """Python client for Malaria Prediction API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.token = self._authenticate()

    def _authenticate(self) -> str:
        """Get JWT token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"api_key": self.api_key}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def predict(
        self,
        latitude: float,
        longitude: float,
        prediction_date: date,
        environmental_data: Dict
    ) -> Dict:
        """Make single prediction"""
        headers = {"Authorization": f"Bearer {self.token}"}

        payload = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "environmental_data": environmental_data,
            "prediction_date": prediction_date.isoformat(),
            "model_type": "ensemble"
        }

        response = requests.post(
            f"{self.base_url}/predict/single",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def batch_predict(
        self,
        locations: List[Dict],
        time_horizon_days: int = 30
    ) -> List[Dict]:
        """Make batch predictions"""
        headers = {"Authorization": f"Bearer {self.token}"}

        payload = {
            "locations": locations,
            "time_horizon_days": time_horizon_days,
            "model_type": "ensemble"
        }

        response = requests.post(
            f"{self.base_url}/predict/batch",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()["predictions"]

# Usage
client = MalariaPredictionClient(
    base_url="https://api.example.com",
    api_key="your_api_key"
)

prediction = client.predict(
    latitude=-1.2921,
    longitude=36.8219,
    prediction_date=date(2025, 12, 1),
    environmental_data={
        "mean_temperature": 22.5,
        "monthly_rainfall": 85.2,
        "relative_humidity": 68.5,
        "elevation": 1795.0
    }
)

print(f"Risk Score: {prediction['prediction']['risk_score']}")
print(f"Risk Level: {prediction['prediction']['risk_level']}")
```

### JavaScript/TypeScript SDK

```typescript
// malaria-client.ts
interface PredictionRequest {
  location: {
    latitude: number;
    longitude: number;
    area_name?: string;
  };
  environmental_data: {
    mean_temperature: number;
    monthly_rainfall: number;
    relative_humidity: number;
    elevation: number;
  };
  prediction_date: string;
  model_type: 'lstm' | 'transformer' | 'ensemble';
}

interface PredictionResponse {
  prediction: {
    risk_score: number;
    risk_level: string;
    confidence: number;
    uncertainty_bounds: {
      lower: number;
      upper: number;
    };
  };
  factors: Record<string, any>;
  metadata: Record<string, any>;
}

class MalariaPredictionClient {
  private baseUrl: string;
  private apiKey: string;
  private token: string | null = null;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async authenticate(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: this.apiKey })
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    const data = await response.json();
    this.token = data.access_token;
  }

  async predict(request: PredictionRequest): Promise<PredictionResponse> {
    if (!this.token) {
      await this.authenticate();
    }

    const response = await fetch(`${this.baseUrl}/predict/single`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Usage
const client = new MalariaPredictionClient(
  'https://api.example.com',
  'your_api_key'
);

const prediction = await client.predict({
  location: {
    latitude: -1.2921,
    longitude: 36.8219,
    area_name: 'Nairobi, Kenya'
  },
  environmental_data: {
    mean_temperature: 22.5,
    monthly_rainfall: 85.2,
    relative_humidity: 68.5,
    elevation: 1795.0
  },
  prediction_date: '2025-12-01',
  model_type: 'ensemble'
});

console.log(`Risk Score: ${prediction.prediction.risk_score}`);
console.log(`Risk Level: ${prediction.prediction.risk_level}`);
```

---

## Common Tasks

### Exporting Data

```bash
# Export predictions to CSV
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/predictions/export?start_date=2025-01-01&end_date=2025-12-31&format=csv" \
  -o predictions_2025.csv

# Export to JSON
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/predictions/export?start_date=2025-01-01&end_date=2025-12-31&format=json" \
  -o predictions_2025.json
```

### Generating Reports

```bash
# Generate PDF report
curl -X POST "https://api.example.com/reports/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "outbreak_analysis",
    "location": {"latitude": -1.2921, "longitude": 36.8219},
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-12-31"
    },
    "format": "pdf"
  }' \
  --output outbreak_analysis_2025.pdf
```

### Troubleshooting

**Common Issues**:

1. **Authentication Errors**:
```bash
# Verify credentials
curl -v -X POST "https://api.example.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

2. **Rate Limit Exceeded**:
```bash
# Check rate limit status
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/auth/rate-limit-status"

# Response shows remaining requests
```

3. **Prediction Errors**:
```bash
# Check API health
curl "https://api.example.com/health/readiness"

# Check model availability
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/models/status"
```

---

## Additional Resources

- [API Reference](../api/endpoints.md) - Complete API documentation
- [Code Examples](../examples/) - Sample code snippets
- [FAQ](#) - Frequently asked questions
- [Support](#) - Contact support team

---

**Last Updated**: November 3, 2025
