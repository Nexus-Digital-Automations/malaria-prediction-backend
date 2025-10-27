# ML Model Architecture

> **Multi-model malaria prediction system: LSTM + Transformer + Ensemble**

## Overview

The malaria prediction system uses three complementary deep learning models:

1. **LSTM (Long Short-Term Memory)** - Temporal pattern recognition
2. **Transformer** - Multi-head attention for complex dependencies
3. **Ensemble** - Combines LSTM + Transformer predictions

### Model Selection by Use Case

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| Short-term prediction (7-30 days) | LSTM | Excellent at recent pattern recognition |
| Long-term prediction (90+ days) | Transformer | Better at long-range dependencies |
| Critical decisions | Ensemble | Highest accuracy, combines strengths |
| Real-time low-latency | LSTM | Fastest inference time |
| Research/analysis | All models | Compare predictions and uncertainty |

---

## LSTM Model

### Architecture

```
Input Layer (Environmental Features)
    ↓
LSTM Layer 1 (256 units, return_sequences=True)
    ↓
Dropout (0.3)
    ↓
LSTM Layer 2 (128 units, return_sequences=True)
    ↓
Dropout (0.3)
    ↓
LSTM Layer 3 (64 units)
    ↓
Dense Layer (32 units, ReLU activation)
    ↓
Output Layer (1 unit, Sigmoid activation)
```

### Key Features

- **Sequence Length**: 90 days (3 months historical data)
- **Hidden Units**: 256 → 128 → 64 (progressively reducing)
- **Dropout Rate**: 0.3 (prevents overfitting)
- **Bidirectional**: Yes (processes sequences forward and backward)
- **Optimizer**: Adam with learning rate 0.001
- **Loss Function**: Binary cross-entropy with class weights

### Implementation

```python
from src.malaria_predictor.ml.models.lstm_model import LSTMPredictor

# Initialize model
model = LSTMPredictor(
    input_dim=15,  # Environmental features
    hidden_dim=256,
    num_layers=3,
    dropout=0.3,
    bidirectional=True
)

# Make prediction
risk_score = model.predict(
    environmental_data,  # Shape: (batch, sequence_length, features)
    prediction_horizon=30  # Days ahead
)
```

### Strengths

- ✅ Excellent short-term accuracy (7-30 days)
- ✅ Captures seasonal patterns effectively
- ✅ Fast inference (<50ms)
- ✅ Handles missing data gracefully

### Limitations

- ⚠️ Struggles with very long sequences (>180 days)
- ⚠️ Can overfit on limited data
- ⚠️ Vanishing gradient in very deep networks

---

## Transformer Model

### Architecture

```
Input Embedding (Environmental Features + Positional Encoding)
    ↓
Multi-Head Attention Block 1
    ├─ Multi-Head Self-Attention (8 heads)
    ├─ Add & Normalize
    ├─ Feed-Forward Network
    └─ Add & Normalize
    ↓
Multi-Head Attention Block 2 (repeat)
    ↓
Multi-Head Attention Block 3 (repeat)
    ↓
Global Average Pooling
    ↓
Dense Layer (128 units, ReLU)
    ↓
Dropout (0.2)
    ↓
Output Layer (1 unit, Sigmoid)
```

### Key Features

- **Attention Heads**: 8 (parallel attention mechanisms)
- **Model Dimension**: 512
- **Feed-Forward Dimension**: 2048
- **Number of Layers**: 3 encoder blocks
- **Positional Encoding**: Sinusoidal (preserves temporal order)
- **Dropout**: 0.2 in attention and FFN layers
- **Optimizer**: AdamW with warmup schedule
- **Loss**: Focal loss (handles class imbalance)

### Implementation

```python
from src.malaria_predictor.ml.models.transformer_model import TransformerPredictor

# Initialize model
model = TransformerPredictor(
    input_dim=15,
    model_dim=512,
    num_heads=8,
    num_layers=3,
    ff_dim=2048,
    dropout=0.2
)

# Make prediction
risk_score = model.predict(
    environmental_data,
    attention_mask=mask  # Optional: handle variable-length sequences
)
```

### Strengths

- ✅ Superior long-term predictions (90+ days)
- ✅ Captures complex dependencies between features
- ✅ Parallelizable (faster training than LSTM)
- ✅ Attention weights provide interpretability

### Limitations

- ⚠️ Requires more training data (>10,000 samples)
- ⚠️ Higher computational cost
- ⚠️ Can be overparameterized for simple patterns

---

## Ensemble Model

### Architecture

```
Environmental Data
    ↓
┌───────────────┬───────────────┐
│               │               │
LSTM Model    Transformer    Historical
(weight: 0.4)   (weight: 0.4)   Baseline
│               │               (weight: 0.2)
└───────────────┴───────────────┘
    ↓
Weighted Average + Uncertainty Estimation
    ↓
Final Risk Score + Confidence Interval
```

### Ensemble Strategy

**Weighted Average**:
```python
ensemble_score = (
    0.4 * lstm_prediction +
    0.4 * transformer_prediction +
    0.2 * historical_baseline
)
```

**Weights optimized via**:
- Cross-validation performance
- Prediction diversity
- Historical accuracy

### Uncertainty Quantification

Uses prediction variance to estimate confidence:

```python
predictions = [lstm_score, transformer_score, baseline_score]
uncertainty = np.std(predictions)
confidence_interval = [
    ensemble_score - 1.96 * uncertainty,
    ensemble_score + 1.96 * uncertainty
]
```

### Implementation

```python
from src.malaria_predictor.ml.models.ensemble_model import EnsemblePredictor

# Initialize ensemble
ensemble = EnsemblePredictor(
    lstm_model=lstm,
    transformer_model=transformer,
    weights={'lstm': 0.4, 'transformer': 0.4, 'baseline': 0.2}
)

# Make prediction with uncertainty
result = ensemble.predict_with_uncertainty(environmental_data)
# Returns: {risk_score, uncertainty, confidence_interval}
```

### Strengths

- ✅ Highest overall accuracy (92%+)
- ✅ Provides uncertainty estimates
- ✅ Robust to individual model failures
- ✅ Best for production use

### Limitations

- ⚠️ Slower inference (3x single model)
- ⚠️ Requires all models to be trained
- ⚠️ More complex deployment

---

## Feature Engineering

### Input Features (15 dimensions)

| Category | Features | Source |
|----------|----------|--------|
| **Climate** | Temperature (mean, min, max), Rainfall, Humidity | ERA5 |
| **Vegetation** | NDVI (Normalized Difference Vegetation Index), EVI | MODIS |
| **Population** | Population density, Urbanization rate | WorldPop |
| **Historical** | Previous malaria cases (7, 14, 30 day lags) | MAP |
| **Seasonality** | Month (sin/cos encoded), Season indicator | Derived |
| **Geographic** | Latitude, Longitude, Elevation | Static |

### Feature Preprocessing

```python
# Normalization
features = StandardScaler().fit_transform(raw_features)

# Temporal features
features['month_sin'] = np.sin(2 * np.pi * month / 12)
features['month_cos'] = np.cos(2 * np.pi * month / 12)

# Lag features
for lag in [7, 14, 30]:
    features[f'cases_lag_{lag}'] = cases.shift(lag)
```

---

## Model Performance

### Benchmark Results (Test Set)

| Model | Accuracy | Precision | Recall | F1 Score | MAE | RMSE |
|-------|----------|-----------|--------|----------|-----|------|
| LSTM | 0.89 | 0.87 | 0.91 | 0.89 | 0.06 | 0.09 |
| Transformer | 0.90 | 0.88 | 0.92 | 0.90 | 0.05 | 0.08 |
| Ensemble | **0.92** | **0.90** | **0.94** | **0.92** | **0.04** | **0.06** |

### Prediction Horizons

| Horizon | LSTM | Transformer | Ensemble |
|---------|------|-------------|----------|
| 7 days | 0.94 | 0.93 | **0.95** |
| 30 days | 0.91 | 0.92 | **0.93** |
| 90 days | 0.85 | **0.89** | **0.89** |
| 180 days | 0.78 | **0.84** | 0.82 |

### Inference Performance

| Model | Single Prediction | Batch (100) | GPU Required |
|-------|------------------|-------------|--------------|
| LSTM | 25ms | 450ms | No |
| Transformer | 75ms | 1.2s | Recommended |
| Ensemble | 150ms | 2.5s | Recommended |

---

## Model Selection Guide

### Decision Tree

```
Is latency critical (<50ms)?
├─ Yes → Use LSTM
└─ No
    │
    Is prediction horizon > 90 days?
    ├─ Yes → Use Transformer
    └─ No
        │
        Is accuracy paramount?
        ├─ Yes → Use Ensemble
        └─ No → Use LSTM (good balance)
```

### Production Deployment

**Recommended Setup**:
1. **Primary**: Ensemble model for critical predictions
2. **Fallback**: LSTM model for low-latency scenarios
3. **Research**: All models for analysis and comparison

---

## Model Training Requirements

### Hardware

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| RAM | 16GB | 32GB | 64GB |
| GPU | None | NVIDIA T4 | A100 |
| Storage | 50GB | 100GB | 500GB |
| CPU | 4 cores | 8 cores | 16 cores |

### Software

- **Python**: 3.11+
- **PyTorch**: 2.1+
- **PyTorch Lightning**: 2.1+
- **Transformers**: 4.35+ (Hugging Face)
- **NumPy**: 1.24+
- **Pandas**: 2.0+

### Training Time

| Model | Dataset Size | GPU | Training Time |
|-------|--------------|-----|---------------|
| LSTM | 50k samples | T4 | 2-3 hours |
| Transformer | 50k samples | T4 | 4-6 hours |
| Ensemble | 50k samples | T4 | 6-9 hours |

---

## Next Steps

- [Training Guide](./training-guide.md) - Train models from scratch
- [Deployment Workflow](./deployment-workflow.md) - Deploy models to production
- [Model Evaluation](./model-evaluation.md) - Evaluate model performance
- [Feature Engineering](./feature-engineering.md) - Create features from raw data

---

**Last Updated**: October 27, 2025
