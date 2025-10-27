# Model Deployment Workflow

> **Production deployment guide for ML models**

## Deployment Pipeline

```
Training → Validation → Versioning → Testing → Staging → Production
```

## 1. Model Preparation

### Export Trained Model

```python
# Save PyTorch model
torch.save({
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'config': model_config,
    'metrics': validation_metrics,
    'version': '2.1.0'
}, 'models/lstm_v2.1.0.pth')

# Export to ONNX for faster inference
torch.onnx.export(
    model,
    dummy_input,
    'models/lstm_v2.1.0.onnx',
    export_params=True,
    opset_version=14,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}}
)
```

### Model Versioning

**Semantic Versioning**: `major.minor.patch`
- **Major**: Breaking API changes, new architecture
- **Minor**: New features, performance improvements
- **Patch**: Bug fixes, minor tweaks

**Example**: `2.1.3`
- Major: 2 (Transformer-based)
- Minor: 1 (Added attention mechanism)
- Patch: 3 (Bug fix in normalization)

## 2. Model Registry (MLflow)

```python
import mlflow

# Log model
with mlflow.start_run():
    mlflow.pytorch.log_model(
        model,
        "lstm_model",
        registered_model_name="malaria_lstm"
    )

    # Log metrics
    mlflow.log_metrics({
        'accuracy': 0.92,
        'f1_score': 0.91,
        'inference_time_ms': 25
    })

    # Log artifacts
    mlflow.log_artifact('models/lstm_v2.1.0.pth')
    mlflow.log_dict(model_config, 'config.yaml')

# Transition to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="malaria_lstm",
    version=5,
    stage="Production"
)
```

## 3. Model Testing

### A/B Testing

```python
# Deploy new model alongside current
class ABTestPredictor:
    def __init__(self, model_a, model_b, traffic_split=0.9):
        self.model_a = model_a  # Current production
        self.model_b = model_b  # New candidate
        self.split = traffic_split

    def predict(self, features):
        if random.random() < self.split:
            return self.model_a.predict(features)
        else:
            result = self.model_b.predict(features)
            self.log_ab_test(result)  # Track new model performance
            return result
```

### Shadow Deployment

```python
# Run new model in parallel, don't return results
def predict_with_shadow(features):
    # Production prediction
    prod_result = production_model.predict(features)

    # Shadow prediction (async)
    asyncio.create_task(
        shadow_model.predict_and_log(features)
    )

    return prod_result
```

## 4. Production Deployment

### Docker Image

**`Dockerfile.model`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model files
COPY models/ ./models/
COPY src/ ./src/

# Expose API port
EXPOSE 8000

# Run inference server
CMD ["uvicorn", "src.malaria_predictor.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and push**:
```bash
# Build
docker build -f Dockerfile.model -t malaria-predictor:v2.1.0 .

# Tag
docker tag malaria-predictor:v2.1.0 registry.example.com/malaria-predictor:v2.1.0

# Push
docker push registry.example.com/malaria-predictor:v2.1.0
```

### Kubernetes Deployment

**`k8s/model-deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: malaria-predictor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: malaria-predictor
  template:
    metadata:
      labels:
        app: malaria-predictor
        version: v2.1.0
    spec:
      containers:
      - name: predictor
        image: registry.example.com/malaria-predictor:v2.1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
```

**Deploy**:
```bash
kubectl apply -f k8s/model-deployment.yaml
kubectl rollout status deployment/malaria-predictor
```

## 5. Rollback Strategy

### Automated Rollback

```python
# Monitor metrics
def check_model_health():
    metrics = get_current_metrics()

    if metrics['accuracy'] < 0.85:  # Threshold
        logger.error("Model performance degraded!")
        rollback_to_previous_version()
        alert_team("Model rollback triggered")

# Rollback function
def rollback_to_previous_version():
    # Kubernetes rollback
    subprocess.run([
        "kubectl", "rollout", "undo",
        "deployment/malaria-predictor"
    ])
```

### Blue-Green Deployment

```yaml
# Green (new version)
apiVersion: v1
kind: Service
metadata:
  name: malaria-predictor-green
spec:
  selector:
    app: malaria-predictor
    version: v2.1.0

# Blue (current)
apiVersion: v1
kind: Service
metadata:
  name: malaria-predictor-blue
spec:
  selector:
    app: malaria-predictor
    version: v2.0.5

# Switch traffic
# Update main service selector to point to green
```

## 6. Monitoring

### Metrics to Track

```python
from prometheus_client import Counter, Histogram

# Prediction metrics
predictions_total = Counter(
    'model_predictions_total',
    'Total predictions made'
)

prediction_latency = Histogram(
    'model_prediction_latency_seconds',
    'Prediction latency'
)

prediction_confidence = Histogram(
    'model_prediction_confidence',
    'Prediction confidence scores'
)

# Track predictions
@prediction_latency.time()
def make_prediction(features):
    prediction = model.predict(features)
    predictions_total.inc()
    prediction_confidence.observe(prediction.confidence)
    return prediction
```

### Alerting Rules

```yaml
# Prometheus alerts
groups:
- name: model_alerts
  rules:
  - alert: ModelAccuracyDegraded
    expr: model_accuracy < 0.85
    for: 5m
    annotations:
      summary: "Model accuracy below threshold"

  - alert: HighPredictionLatency
    expr: model_prediction_latency_p95 > 0.5
    for: 2m
    annotations:
      summary: "95th percentile latency > 500ms"
```

## 7. Model Updates

### Gradual Rollout

```python
# Canary deployment
class CanaryDeployment:
    def __init__(self):
        self.canary_percentage = 5  # Start with 5%

    def predict(self, features):
        if random.random() * 100 < self.canary_percentage:
            return new_model.predict(features)
        else:
            return current_model.predict(features)

    def increase_canary(self):
        # Gradually increase: 5% → 10% → 25% → 50% → 100%
        self.canary_percentage = min(self.canary_percentage * 2, 100)
```

## 8. Offline vs Online Deployment

| Aspect | Offline | Online |
|--------|---------|--------|
| **Use Case** | Batch predictions | Real-time API |
| **Latency** | Minutes to hours | <100ms |
| **Infrastructure** | Scheduled jobs | Always-on servers |
| **Scaling** | Horizontal (workers) | Horizontal + vertical |
| **Cost** | Lower (on-demand) | Higher (always running) |

**Offline Example**:
```python
# Daily batch job
def daily_prediction_batch():
    locations = get_all_monitored_locations()
    predictions = []

    for location in locations:
        pred = model.predict(location.features)
        predictions.append(pred)

    store_predictions(predictions)
```

---

**Last Updated**: October 27, 2025
