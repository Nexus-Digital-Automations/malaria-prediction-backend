# ML Model Training Guide

> **Step-by-step guide for training malaria prediction models**

## Quick Start

```bash
# 1. Prepare environment
cd /path/to/malaria-prediction-backend
source venv/bin/activate

# 2. Prepare training data
python -m src.malaria_predictor.ml.training.prepare_data \
  --start-date 2010-01-01 \
  --end-date 2023-12-31 \
  --output data/training/

# 3. Train models
python -m src.malaria_predictor.ml.training.pipeline \
  --model lstm \
  --data data/training/ \
  --output models/

# 4. Evaluate
python -m src.malaria_predictor.ml.evaluation.evaluate \
  --model models/lstm_best.pth \
  --test-data data/test/
```

## Data Preparation

### 1. Collect Training Data

```python
from src.malaria_predictor.services import (
    ERA5Client, CHIRPSClient, MODISClient
)

# Initialize data clients
era5 = ERA5Client()
chirps = CHIRPS Client()
modis = MODISClient()

# Fetch environmental data
climate_data = era5.get_historical_data(
    start_date='2010-01-01',
    end_date='2023-12-31',
    bounds=(-5, 34, 5, 42)  # East Africa region
)

rainfall_data = chirps.get_rainfall_data(...)
vegetation_data = modis.get_ndvi(...)
```

### 2. Create Training Dataset

```python
from src.malaria_predictor.ml.feature_extractor import FeatureExtractor

# Extract features
extractor = FeatureExtractor()
features = extractor.create_features(
    climate_data,
    rainfall_data,
    vegetation_data,
    malaria_cases  # Historical cases from MAP
)

# Create sequences (90-day windows)
X, y = extractor.create_sequences(
    features,
    sequence_length=90,
    prediction_horizon=30
)

# Split data (70% train, 15% val, 15% test)
X_train, X_val, X_test = split_data(X, ratios=[0.7, 0.15, 0.15])
y_train, y_val, y_test = split_data(y, ratios=[0.7, 0.15, 0.15])
```

### Data Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Historical Data | 5 years | 10+ years |
| Locations | 100 | 1000+ |
| Total Samples | 10,000 | 50,000+ |
| Features | 10 | 15+ |

## Training Configuration

### LSTM Model

**`config/lstm_training.yaml`**:
```yaml
model:
  input_dim: 15
  hidden_dim: 256
  num_layers: 3
  dropout: 0.3
  bidirectional: true

training:
  batch_size: 32
  learning_rate: 0.001
  epochs: 100
  early_stopping_patience: 10
  optimizer: adam

data:
  sequence_length: 90
  prediction_horizon: 30
  validation_split: 0.15
```

### Transformer Model

**`config/transformer_training.yaml`**:
```yaml
model:
  input_dim: 15
  model_dim: 512
  num_heads: 8
  num_layers: 3
  ff_dim: 2048
  dropout: 0.2

training:
  batch_size: 16  # Smaller for memory
  learning_rate: 0.0001
  epochs: 150
  warmup_steps: 1000
  optimizer: adamw
```

## Training Process

### 1. Initialize Model

```python
import pytorch_lightning as pl
from src.malaria_predictor.ml.models import LSTMPredictor

# Load config
config = load_config('config/lstm_training.yaml')

# Initialize model
model = LSTMPredictor(
    input_dim=config.model.input_dim,
    hidden_dim=config.model.hidden_dim,
    num_layers=config.model.num_layers,
    dropout=config.model.dropout
)
```

### 2. Setup Data Loaders

```python
from torch.utils.data import DataLoader, TensorDataset

# Create datasets
train_dataset = TensorDataset(X_train, y_train)
val_dataset = TensorDataset(X_val, y_val)

# Create data loaders
train_loader = DataLoader(
    train_dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4
)

val_loader = DataLoader(
    val_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=4
)
```

### 3. Configure Training

```python
from pytorch_lightning.callbacks import (
    EarlyStopping, ModelCheckpoint, LearningRateMonitor
)
from pytorch_lightning.loggers import MLFlowLogger

# Early stopping
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=10,
    mode='min'
)

# Model checkpointing
checkpoint = ModelCheckpoint(
    dirpath='models/checkpoints/',
    filename='lstm-{epoch:02d}-{val_loss:.4f}',
    monitor='val_loss',
    mode='min',
    save_top_k=3
)

# MLflow logging
mlflow_logger = MLFlowLogger(
    experiment_name='malaria_prediction',
    tracking_uri='http://localhost:5000'
)

# Learning rate monitoring
lr_monitor = LearningRateMonitor(logging_interval='step')
```

### 4. Train Model

```python
# Initialize trainer
trainer = pl.Trainer(
    max_epochs=100,
    accelerator='gpu',
    devices=1,
    callbacks=[early_stop, checkpoint, lr_monitor],
    logger=mlflow_logger,
    precision='16-mixed',  # Mixed precision for faster training
    gradient_clip_val=1.0
)

# Train
trainer.fit(
    model,
    train_dataloaders=train_loader,
    val_dataloaders=val_loader
)
```

## Monitoring Training

### TensorBoard

```bash
# Start TensorBoard
tensorboard --logdir=lightning_logs/

# View at http://localhost:6006
```

### MLflow

```bash
# Start MLflow UI
mlflow ui --port 5000

# View at http://localhost:5000
```

### Key Metrics to Monitor

- **Loss**: Should decrease steadily
- **Accuracy**: Should increase and plateau
- **Validation Loss**: Should track training loss (watch for overfitting)
- **Learning Rate**: Should decrease with schedule
- **Gradient Norm**: Should be stable (<10)

## Hyperparameter Tuning

### Grid Search

```python
from src.malaria_predictor.ml.training import hyperparameter_search

# Define search space
param_grid = {
    'hidden_dim': [128, 256, 512],
    'num_layers': [2, 3, 4],
    'dropout': [0.2, 0.3, 0.4],
    'learning_rate': [0.0001, 0.001, 0.01]
}

# Run search
best_params = hyperparameter_search(
    model_class=LSTMPredictor,
    param_grid=param_grid,
    train_data=(X_train, y_train),
    val_data=(X_val, y_val),
    metric='val_f1_score'
)
```

### Optuna (Automated)

```python
import optuna

def objective(trial):
    # Suggest hyperparameters
    hidden_dim = trial.suggest_int('hidden_dim', 64, 512)
    dropout = trial.suggest_float('dropout', 0.1, 0.5)
    lr = trial.suggest_loguniform('lr', 1e-5, 1e-2)

    # Train model
    model = train_model(hidden_dim, dropout, lr)

    # Return validation metric
    return model.val_f1_score

# Run optimization
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)

print(f"Best params: {study.best_params}")
```

## Best Practices

### 1. Class Imbalance

```python
# Calculate class weights
from sklearn.utils import class_weight

class_weights = class_weight.compute_class_weight(
    'balanced',
    classes=np.unique(y_train),
    y=y_train
)

# Use in loss function
criterion = nn.BCEWithLogitsLoss(
    pos_weight=torch.tensor(class_weights[1] / class_weights[0])
)
```

### 2. Data Augmentation

```python
# Add noise to features
def augment_data(X, noise_level=0.01):
    noise = np.random.normal(0, noise_level, X.shape)
    return X + noise

# Temporal shift
def temporal_augment(X, max_shift=7):
    shift = np.random.randint(-max_shift, max_shift)
    return np.roll(X, shift, axis=1)
```

### 3. Regularization

```python
# L2 regularization
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001,
    weight_decay=1e-5  # L2 penalty
)

# Dropout (in model architecture)
self.dropout = nn.Dropout(0.3)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Loss not decreasing | Learning rate too low | Increase LR or use LR scheduler |
| Loss exploding | Learning rate too high | Reduce LR, add gradient clipping |
| Overfitting | Model too complex | Add dropout, reduce model size |
| Underfitting | Model too simple | Increase model capacity, train longer |
| OOM errors | Batch size too large | Reduce batch size, use gradient accumulation |
| Slow training | CPU bottleneck | Use GPU, increase num_workers |

## Production Deployment

After training:

```bash
# 1. Save best model
torch.save(model.state_dict(), 'models/lstm_production.pth')

# 2. Export to ONNX (for faster inference)
torch.onnx.export(
    model,
    dummy_input,
    'models/lstm_production.onnx'
)

# 3. Test on production data
python -m src.malaria_predictor.ml.evaluation.production_test \
  --model models/lstm_production.pth \
  --test-set data/production_test/
```

See [Deployment Workflow](./deployment-workflow.md) for details.

---

**Last Updated**: October 27, 2025
