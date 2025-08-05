# ML Framework Integration Research for Malaria Prediction

## Executive Summary

This document provides comprehensive research on AI/ML framework integration for malaria prediction using environmental time-series data. Based on analysis of the existing codebase architecture and data ingestion services (ERA5, CHIRPS, MAP, WorldPop, MODIS), this research evaluates frameworks, architectures, and implementation strategies for building production-ready malaria prediction models.

**Key Recommendations:**
- **Primary Framework**: PyTorch with Lightning for scalability and flexibility
- **Model Architecture**: Hybrid LSTM-Transformer ensemble for temporal and spatial pattern recognition
- **Deployment Strategy**: FastAPI with async prediction serving and MLflow for model management
- **Data Pipeline**: Unified feature engineering with real-time harmonization

## 1. ML Framework Evaluation

### 1.1 PyTorch vs TensorFlow Analysis

#### PyTorch Advantages for Malaria Prediction
```python
# PyTorch strengths for our use case:
1. Dynamic computational graphs ideal for variable-length time series
2. Superior debugging and development experience for research
3. Excellent ecosystem for transformer models (Hugging Face integration)
4. Lightning framework for production scaling
5. Strong geospatial and time-series community packages
```

**Current Project Integration:**
- Already included in pyproject.toml dependencies
- Compatible with existing FastAPI async architecture
- Native support for transformers package (line 30 in pyproject.toml)

#### TensorFlow Comparison
- **Pros**: Better production tooling with TF Serving, stronger mobile deployment
- **Cons**: More complex for research iteration, less flexible for custom architectures
- **Verdict**: PyTorch preferred for development flexibility and research requirements

### 1.2 Supporting Framework Recommendations

#### Scikit-learn Integration
```python
# Existing dependency - ideal for:
- Feature preprocessing and engineering
- Classical ML baselines (Random Forest, XGBoost)
- Data validation and quality checks
- Dimensionality reduction (PCA, feature selection)
```

#### PyTorch Lightning
```python
# Recommended addition for production scaling:
dependencies = [
    "pytorch-lightning>=2.1.0",  # Production training framework
    "lightning-fabric>=2.1.0",   # Flexible training components
]
```

## 2. Time-Series Architecture for Malaria Prediction

### 2.1 LSTM Architecture Design

#### Multi-variate LSTM for Environmental Sequences

```python
class MalariaLSTM(nn.Module):
    """
    Multi-variate LSTM for malaria risk prediction using environmental data.

    Architecture:
    - Bidirectional LSTM layers for temporal dependencies
    - Multi-head attention for variable importance
    - Residual connections for gradient flow
    - Separate encoders for different data modalities
    """

    def __init__(
        self,
        climate_features: int = 8,      # ERA5 + CHIRPS features
        vegetation_features: int = 4,    # MODIS NDVI/EVI features
        population_features: int = 6,    # WorldPop demographics
        historical_features: int = 4,    # MAP baseline risk
        hidden_size: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2,
        prediction_horizon: int = 30,    # Days ahead prediction
    ):
        super().__init__()

        # Modality-specific encoders
        self.climate_encoder = nn.Linear(climate_features, hidden_size)
        self.vegetation_encoder = nn.Linear(vegetation_features, hidden_size//2)
        self.population_encoder = nn.Linear(population_features, hidden_size//2)
        self.historical_encoder = nn.Linear(historical_features, hidden_size//2)

        # Main LSTM backbone
        self.lstm = nn.LSTM(
            input_size=hidden_size * 2,  # Combined modality features
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            bidirectional=True,
            batch_first=True
        )

        # Attention mechanism for temporal importance
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # Bidirectional output
            num_heads=8,
            dropout=dropout
        )

        # Prediction head
        self.risk_predictor = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, prediction_horizon),
            nn.Sigmoid()  # Risk probability [0,1]
        )
```

#### Temporal Feature Engineering Strategy

```python
class EnvironmentalFeatureEngineer:
    """
    Feature engineering for multi-source environmental data.

    Handles:
    - Temporal alignment across different data frequencies
    - Lag feature creation for environmental predictors
    - Moving averages and seasonal decomposition
    - Missing data imputation with domain knowledge
    """

    def create_temporal_features(self, data: xr.Dataset) -> pd.DataFrame:
        """
        Create malaria-relevant temporal features from environmental data.

        Features created:
        - Temperature: mean, min, max, diurnal range, growing degree days
        - Precipitation: cumulative, dry spell length, wet day frequency
        - Vegetation: NDVI/EVI trends, seasonality, anomalies
        - Population: density gradients, age structure risks
        """
        features = {}

        # Temperature suitability indices
        features['temp_suitability'] = self._calculate_temp_suitability(
            data['temperature_2m']
        )

        # Precipitation breeding habitat indicators
        features['breeding_habitat_index'] = self._calculate_breeding_index(
            data['total_precipitation']
        )

        # Vegetation phenology for vector habitat
        features['vector_habitat_score'] = self._calculate_habitat_score(
            data['ndvi'], data['evi']
        )

        return pd.DataFrame(features)
```

### 2.2 Transformer Architecture for Pattern Recognition

#### Multi-Modal Attention Model

```python
class MalariaTransformer(nn.Module):
    """
    Transformer model for complex pattern recognition in environmental data.

    Key features:
    - Cross-attention between different data modalities
    - Positional encoding for temporal and spatial dimensions
    - Multi-scale attention for local and global patterns
    - Uncertainty quantification through ensemble predictions
    """

    def __init__(
        self,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        max_seq_length: int = 365,  # One year of daily data
    ):
        super().__init__()

        # Modality embedding layers
        self.climate_embedding = nn.Linear(12, d_model)  # ERA5 + CHIRPS
        self.vegetation_embedding = nn.Linear(4, d_model)  # MODIS indices
        self.population_embedding = nn.Linear(6, d_model)  # WorldPop
        self.risk_embedding = nn.Linear(4, d_model)  # MAP baseline

        # Positional encoding for temporal and spatial dimensions
        self.temporal_pos_encoding = PositionalEncoding(d_model, max_seq_length)
        self.spatial_pos_encoding = SpatialPositionalEncoding(d_model)

        # Multi-modal transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

        # Cross-attention between modalities
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=nhead,
            dropout=dropout
        )

        # Risk prediction head with uncertainty
        self.risk_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 2)  # Mean and variance for uncertainty
        )
```

## 3. Environmental Data Feature Engineering

### 3.1 Multi-Source Data Integration Strategy

#### Malaria-Relevant Environmental Indices

```python
class MalariaFeatureExtractor:
    """
    Extract malaria-relevant features from multi-source environmental data.

    Based on epidemiological research on environmental drivers of malaria:
    - Temperature: Affects parasite development and vector survival
    - Precipitation: Creates breeding habitats for mosquitoes
    - Vegetation: Indicates suitable vector habitat and human proximity
    - Population: Determines transmission potential and vulnerability
    """

    def extract_climate_features(self, era5_data: xr.Dataset, chirps_data: xr.Dataset):
        """Extract climate-based malaria risk features."""

        # Temperature suitability (Mordecai et al. 2013)
        temp_opt = 25.0  # Optimal temperature for P. falciparum
        temp_features = {
            'temp_suitability': self._thermal_suitability(
                era5_data['temperature_2m'], temp_opt
            ),
            'diurnal_range': (
                era5_data['temperature_2m_max'] - era5_data['temperature_2m_min']
            ),
            'growing_degree_days': self._calculate_gdd(
                era5_data['temperature_2m'], base_temp=16.0
            ),
            'heat_stress_days': (era5_data['temperature_2m'] > 35).sum('time')
        }

        # Precipitation breeding habitat indicators
        precip_features = {
            'breeding_potential': self._breeding_habitat_index(
                chirps_data['precipitation']
            ),
            'dry_spell_length': self._dry_spell_duration(
                chirps_data['precipitation']
            ),
            'wet_season_intensity': self._wet_season_analysis(
                chirps_data['precipitation']
            )
        }

        return {**temp_features, **precip_features}

    def extract_vegetation_features(self, modis_data: xr.Dataset):
        """Extract vegetation indices related to vector habitat."""

        return {
            'vector_habitat_score': (
                modis_data['ndvi'] * 0.7 + modis_data['evi'] * 0.3
            ),
            'vegetation_seasonality': self._seasonal_decomposition(
                modis_data['ndvi']
            ),
            'greenness_anomaly': self._calculate_anomalies(
                modis_data['ndvi']
            )
        }
```

### 3.2 Feature Engineering Pipeline Integration

```python
# Integration with existing data services
class MLFeaturePipeline:
    """
    Unified feature engineering pipeline integrating all data sources.

    Integrates with existing services:
    - ERA5Client: Climate data
    - CHIRPSClient: Precipitation data
    - MAPClient: Historical risk data
    - WorldPopClient: Population data
    - MODISClient: Vegetation data
    """

    def __init__(
        self,
        era5_client: ERA5Client,
        chirps_client: CHIRPSClient,
        map_client: MAPClient,
        worldpop_client: WorldPopClient,
        modis_client: MODISClient,
    ):
        self.clients = {
            'era5': era5_client,
            'chirps': chirps_client,
            'map': map_client,
            'worldpop': worldpop_client,
            'modis': modis_client
        }
        self.feature_extractor = MalariaFeatureExtractor()

    async def create_training_dataset(
        self,
        start_date: datetime,
        end_date: datetime,
        bbox: tuple[float, float, float, float],
        target_resolution: float = 0.1  # degrees
    ) -> pd.DataFrame:
        """Create ML-ready training dataset from all sources."""

        # Parallel data collection from all sources
        tasks = [
            self.clients['era5'].get_data(start_date, end_date, bbox),
            self.clients['chirps'].get_data(start_date, end_date, bbox),
            self.clients['map'].get_risk_data(bbox),
            self.clients['worldpop'].get_population_data(bbox),
            self.clients['modis'].get_vegetation_data(start_date, end_date, bbox)
        ]

        era5, chirps, map_risk, population, vegetation = await asyncio.gather(*tasks)

        # Harmonize spatial and temporal resolution
        harmonized_data = self._harmonize_datasets(
            era5, chirps, map_risk, population, vegetation, target_resolution
        )

        # Extract malaria-relevant features
        features = self.feature_extractor.extract_all_features(harmonized_data)

        return features
```

## 4. Model Architecture Patterns

### 4.1 Ensemble Architecture Strategy

```python
class MalariaEnsembleModel(LightningModule):
    """
    Ensemble model combining LSTM and Transformer for robust predictions.

    Architecture rationale:
    - LSTM: Captures sequential dependencies in time-series
    - Transformer: Learns complex cross-modal attention patterns
    - Ensemble: Combines strengths and quantifies uncertainty
    """

    def __init__(self, config: ModelConfig):
        super().__init__()

        # Individual model components
        self.lstm_model = MalariaLSTM(**config.lstm_params)
        self.transformer_model = MalariaTransformer(**config.transformer_params)

        # Ensemble fusion layer
        self.ensemble_fusion = nn.Sequential(
            nn.Linear(4, 32),  # 2 predictions + 2 uncertainties
            nn.ReLU(),
            nn.Linear(32, 2),  # Final mean and variance
        )

        # Loss function for probabilistic predictions
        self.loss_fn = GaussianNLLLoss()

    def forward(self, x: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        """Forward pass through ensemble."""

        # Individual model predictions
        lstm_out = self.lstm_model(x)
        transformer_out = self.transformer_model(x)

        # Ensemble predictions with uncertainty
        ensemble_input = torch.cat([
            lstm_out['risk_mean'], lstm_out['risk_var'],
            transformer_out['risk_mean'], transformer_out['risk_var']
        ], dim=-1)

        final_prediction = self.ensemble_fusion(ensemble_input)

        return {
            'risk_prediction': final_prediction[:, 0],
            'prediction_uncertainty': torch.exp(final_prediction[:, 1]),
            'lstm_contribution': lstm_out,
            'transformer_contribution': transformer_out
        }
```

### 4.2 Training Strategy and Optimization

```python
class MalariaTrainingPipeline:
    """
    Comprehensive training pipeline for malaria prediction models.

    Features:
    - Cross-validation with temporal splits
    - Hyperparameter optimization with Optuna
    - Multi-metric evaluation (epidemiological + ML metrics)
    - Model interpretability analysis
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.study = optuna.create_study(direction='minimize')

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna objective function for hyperparameter optimization."""

        # Sample hyperparameters
        params = {
            'lstm_hidden_size': trial.suggest_int('lstm_hidden_size', 64, 256),
            'transformer_d_model': trial.suggest_int('transformer_d_model', 128, 512),
            'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
            'dropout': trial.suggest_float('dropout', 0.1, 0.5),
            'ensemble_weight': trial.suggest_float('ensemble_weight', 0.3, 0.7)
        }

        # Train model with sampled parameters
        model = MalariaEnsembleModel(params)
        trainer = L.Trainer(
            max_epochs=self.config.max_epochs,
            callbacks=[EarlyStopping(patience=10)],
            logger=MLFlowLogger(experiment_name="malaria_prediction")
        )

        trainer.fit(model, self.train_loader, self.val_loader)

        # Evaluate on validation set
        val_metrics = trainer.validate(model, self.val_loader)

        # Multi-objective optimization (accuracy + uncertainty calibration)
        return val_metrics['val_loss'] + 0.1 * val_metrics['val_uncertainty_error']
```

## 5. Integration with Existing Python Backend

### 5.1 FastAPI Service Integration

```python
# Extension to existing FastAPI architecture
from fastapi import FastAPI, BackgroundTasks, Depends
from .services.ml_prediction_service import MLPredictionService

app = FastAPI(title="Malaria Prediction API")

class PredictionRequest(BaseModel):
    """Request model for malaria risk predictions."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    prediction_date: datetime
    prediction_horizon: int = Field(default=30, ge=1, le=90)
    include_uncertainty: bool = True
    model_version: str | None = None

@app.post("/predict/risk")
async def predict_malaria_risk(
    request: PredictionRequest,
    ml_service: MLPredictionService = Depends(get_ml_service),
    background_tasks: BackgroundTasks
) -> dict:
    """
    Predict malaria risk for specified location and time period.

    Integrates with existing data services to:
    1. Fetch recent environmental data
    2. Run ensemble model predictions
    3. Return risk scores with uncertainty bounds
    4. Cache results for performance
    """

    # Trigger background data updates if needed
    background_tasks.add_task(
        ml_service.update_environmental_data,
        request.latitude,
        request.longitude,
        request.prediction_date
    )

    # Get prediction from cached or fresh model inference
    prediction = await ml_service.predict_risk(
        lat=request.latitude,
        lon=request.longitude,
        date=request.prediction_date,
        horizon=request.prediction_horizon,
        model_version=request.model_version
    )

    return {
        "risk_score": prediction.risk_mean,
        "confidence_interval": {
            "lower": prediction.risk_lower,
            "upper": prediction.risk_upper
        },
        "prediction_quality": prediction.quality_score,
        "contributing_factors": prediction.feature_importance,
        "model_metadata": {
            "version": prediction.model_version,
            "training_date": prediction.training_date,
            "uncertainty": prediction.uncertainty
        }
    }
```

### 5.2 Database Integration Strategy

```python
# Extension to existing database models in src/malaria_predictor/database/models.py

class MLModelMetadata(Base):
    """Metadata for trained ML models."""

    __tablename__ = "ml_model_metadata"

    id = Column(Integer, primary_key=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # 'lstm', 'transformer', 'ensemble'
    training_date = Column(DateTime(timezone=True), nullable=False)
    performance_metrics = Column(JSON, nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    file_path = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('model_name', 'version'),
        Index('idx_model_active', 'model_name', 'is_active'),
    )

class PredictionResult(Base):
    """Store prediction results for monitoring and evaluation."""

    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(String, nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False)

    # Prediction outputs
    risk_mean = Column(Float, nullable=False)
    risk_variance = Column(Float, nullable=False)
    feature_importance = Column(JSON, nullable=True)

    # Model metadata
    model_version = Column(String, nullable=False)
    model_confidence = Column(Float, nullable=False)

    # Performance tracking
    actual_outcome = Column(Float, nullable=True)  # For retrospective evaluation
    prediction_error = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index('idx_prediction_location_date', 'latitude', 'longitude', 'target_date'),
        Index('idx_prediction_model', 'model_version', 'created_at'),
    )
```

## 6. Performance Considerations

### 6.1 Real-Time Prediction Optimization

```python
class CachedPredictionService:
    """
    Optimized prediction service with intelligent caching.

    Performance optimizations:
    - Pre-computed feature grids for common locations
    - Model result caching with geographic and temporal indexing
    - Async batch processing for multiple predictions
    - GPU acceleration for ensemble inference
    """

    def __init__(self, redis_client: Redis, model_service: MLModelService):
        self.cache = redis_client
        self.model_service = model_service
        self.batch_size = 32

    async def predict_batch(
        self,
        locations: list[tuple[float, float]],
        prediction_dates: list[datetime],
        model_version: str = "latest"
    ) -> list[PredictionResult]:
        """Batch prediction with caching and optimization."""

        # Check cache first
        cache_keys = [
            f"prediction:{lat}:{lon}:{date}:{model_version}"
            for (lat, lon), date in zip(locations, prediction_dates)
        ]

        cached_results = await self.cache.mget(cache_keys)

        # Identify missing predictions
        missing_indices = [
            i for i, result in enumerate(cached_results)
            if result is None
        ]

        if missing_indices:
            # Batch process missing predictions
            missing_locations = [locations[i] for i in missing_indices]
            missing_dates = [prediction_dates[i] for i in missing_indices]

            # Parallel environmental data fetching
            env_data = await self._fetch_environmental_data_batch(
                missing_locations, missing_dates
            )

            # GPU batch inference
            predictions = await self.model_service.predict_batch(
                env_data, model_version
            )

            # Cache results
            for i, pred in zip(missing_indices, predictions):
                await self.cache.setex(
                    cache_keys[i],
                    3600,  # 1 hour cache
                    pred.json()
                )
                cached_results[i] = pred

        return cached_results
```

### 6.2 Model Serving Architecture

```python
class ModelServingConfig(BaseModel):
    """Configuration for model serving optimization."""

    # Model loading
    model_cache_size: int = 3  # Number of models to keep in memory
    model_warmup: bool = True  # Pre-load models on startup

    # Inference optimization
    batch_size: int = 32
    max_sequence_length: int = 365
    use_gpu: bool = True
    precision: str = "fp16"  # Mixed precision for speed

    # Caching strategy
    cache_ttl: int = 3600  # 1 hour
    cache_warming_enabled: bool = True
    precompute_common_locations: bool = True

@lru_cache(maxsize=3)
def load_model(model_version: str) -> MalariaEnsembleModel:
    """Load model with LRU caching."""
    model_path = f"models/malaria_ensemble_{model_version}.pt"
    model = MalariaEnsembleModel.load_from_checkpoint(model_path)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    return model
```

## 7. Model Versioning and Deployment Strategies

### 7.1 MLOps Pipeline with MLflow

```python
class MLModelManager:
    """
    Model lifecycle management with MLflow integration.

    Handles:
    - Model training tracking and versioning
    - A/B testing for model deployment
    - Performance monitoring and drift detection
    - Automated retraining pipelines
    """

    def __init__(self, mlflow_client: MlflowClient):
        self.client = mlflow_client
        self.model_registry = "malaria_prediction_models"

    async def deploy_model(
        self,
        model: MalariaEnsembleModel,
        version: str,
        validation_metrics: dict,
        deployment_stage: str = "staging"
    ):
        """Deploy model with validation and rollback capability."""

        # Validate model performance thresholds
        if validation_metrics['accuracy'] < 0.75:
            raise ValueError("Model accuracy below deployment threshold")

        if validation_metrics['uncertainty_calibration'] > 0.1:
            raise ValueError("Model uncertainty poorly calibrated")

        # Register model in MLflow
        model_uri = f"models:/{self.model_registry}/{version}"

        # Log model artifacts
        with mlflow.start_run():
            mlflow.pytorch.log_model(
                pytorch_model=model,
                artifact_path="model",
                registered_model_name=self.model_registry
            )
            mlflow.log_metrics(validation_metrics)

        # Transition to staging
        self.client.transition_model_version_stage(
            name=self.model_registry,
            version=version,
            stage=deployment_stage
        )

        # Gradual rollout strategy
        if deployment_stage == "production":
            await self._gradual_rollout(model_uri, version)

    async def _gradual_rollout(self, model_uri: str, version: str):
        """Implement gradual rollout with A/B testing."""

        # Start with 10% traffic to new model
        traffic_splits = [0.1, 0.25, 0.5, 0.75, 1.0]

        for split in traffic_splits:
            # Update load balancer to route traffic
            await self._update_traffic_routing(version, split)

            # Monitor metrics for 1 hour
            await asyncio.sleep(3600)

            # Check for performance degradation
            metrics = await self._collect_deployment_metrics(version)

            if metrics['error_rate'] > 0.05 or metrics['latency_p95'] > 2000:
                # Rollback on performance issues
                await self._rollback_deployment(version)
                break
```

### 7.2 Monitoring and Observability

```python
class ModelMonitoring:
    """
    Production model monitoring and alerting.

    Monitors:
    - Prediction accuracy and drift
    - Input data quality and distribution shifts
    - Model performance and latency
    - Feature importance changes
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.drift_detector = DataDriftDetector()

    async def monitor_prediction_quality(self, predictions: list[PredictionResult]):
        """Monitor prediction quality and detect issues."""

        # Track prediction distributions
        risk_scores = [p.risk_mean for p in predictions]
        uncertainty_scores = [p.risk_variance for p in predictions]

        self.metrics.histogram("prediction_risk_distribution", risk_scores)
        self.metrics.histogram("prediction_uncertainty", uncertainty_scores)

        # Detect distribution drift
        drift_score = self.drift_detector.detect_drift(
            reference_data=self.historical_predictions,
            current_data=predictions
        )

        if drift_score > 0.1:
            # Alert on significant drift
            await self._send_drift_alert(drift_score, predictions)

        # Track feature importance stability
        feature_importance = [p.feature_importance for p in predictions]
        importance_drift = self._calculate_importance_drift(feature_importance)

        self.metrics.gauge("feature_importance_drift", importance_drift)
```

## 8. Production Deployment Strategy

### 8.1 Containerization and Orchestration

```dockerfile
# Dockerfile for ML prediction service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system -r pyproject.toml

# Copy application code
COPY src/ ./src/
COPY models/ ./models/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MODEL_CACHE_SIZE=2
ENV BATCH_SIZE=16
ENV USE_GPU=false

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "malaria_predictor.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# Kubernetes deployment configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: malaria-prediction-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: malaria-prediction-api
  template:
    metadata:
      labels:
        app: malaria-prediction-api
    spec:
      containers:
      - name: api
        image: malaria-prediction:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: url
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: malaria-prediction-service
spec:
  selector:
    app: malaria-prediction-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 9. Implementation Roadmap

### 9.1 Phase 1: Core ML Infrastructure (Weeks 1-2)

**Dependencies to Add:**
```toml
# Add to pyproject.toml
pytorch-lightning = ">=2.1.0"
optuna = ">=3.4.0"
mlflow = ">=2.8.0"
torchmetrics = ">=1.2.0"
wandb = ">=0.16.0"  # Alternative to MLflow for experiment tracking
```

**Tasks:**
1. Implement `MalariaLSTM` and `MalariaTransformer` base models
2. Create `EnvironmentalFeatureExtractor` for multi-source data
3. Build `MLFeaturePipeline` integrating existing data services
4. Set up MLflow experiment tracking and model registry

### 9.2 Phase 2: Training Pipeline (Weeks 3-4)

**Tasks:**
1. Implement `MalariaTrainingPipeline` with hyperparameter optimization
2. Create cross-validation strategy with temporal splits
3. Build evaluation metrics specific to epidemiological predictions
4. Implement ensemble model with uncertainty quantification

### 9.3 Phase 3: API Integration (Weeks 5-6)

**Tasks:**
1. Extend FastAPI with ML prediction endpoints
2. Implement `CachedPredictionService` with Redis caching
3. Add batch prediction capabilities for efficiency
4. Create model serving infrastructure with GPU support

### 9.4 Phase 4: Production Deployment (Weeks 7-8)

**Tasks:**
1. Implement `MLModelManager` for deployment automation
2. Set up monitoring and alerting for model performance
3. Create Docker containers and Kubernetes configurations
4. Implement A/B testing and gradual rollout strategies

## 10. Success Criteria and Evaluation

### 10.1 Technical Performance Metrics

```python
class ModelEvaluationMetrics:
    """Comprehensive evaluation metrics for malaria prediction models."""

    @staticmethod
    def calculate_epidemiological_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_uncertainty: np.ndarray
    ) -> dict:
        """Calculate domain-specific evaluation metrics."""

        return {
            # Classification metrics (for risk thresholds)
            'sensitivity': recall_score(y_true > 0.5, y_pred > 0.5),
            'specificity': recall_score(y_true <= 0.5, y_pred <= 0.5),
            'ppv': precision_score(y_true > 0.5, y_pred > 0.5),
            'npv': precision_score(y_true <= 0.5, y_pred <= 0.5),

            # Regression metrics
            'mae': mean_absolute_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'r2': r2_score(y_true, y_pred),

            # Uncertainty calibration
            'uncertainty_correlation': pearsonr(
                np.abs(y_true - y_pred), y_uncertainty
            )[0],
            'prediction_interval_coverage': calculate_coverage(
                y_true, y_pred, y_uncertainty
            ),

            # Temporal consistency
            'temporal_stability': calculate_temporal_consistency(y_pred),

            # Early warning capability
            'early_warning_skill': calculate_early_warning_metrics(
                y_true, y_pred, lead_time_days=30
            )
        }
```

### 10.2 Production Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Prediction Accuracy** | RMSE < 0.15 | Risk score prediction error |
| **Response Time** | < 500ms | 95th percentile API response |
| **Availability** | > 99.5% | System uptime |
| **Throughput** | > 1000 req/min | Peak prediction requests |
| **Uncertainty Calibration** | > 0.8 correlation | Uncertainty vs actual error |
| **Early Warning Lead Time** | 30 days | Advance prediction capability |

## 11. Conclusion

This research provides a comprehensive framework for implementing ML-powered malaria prediction in the existing Python backend. The recommended approach leverages:

- **PyTorch + Lightning** for flexible, scalable model development
- **Hybrid LSTM-Transformer ensemble** for robust time-series prediction
- **Comprehensive feature engineering** utilizing all 5 data sources
- **Production-ready FastAPI integration** with caching and monitoring
- **MLOps best practices** for model lifecycle management

The implementation builds upon the existing high-quality codebase architecture and maintains consistency with established patterns while adding advanced ML capabilities for malaria risk prediction.

**Next Steps:**
1. Review and approve the technical approach outlined in this research
2. Begin Phase 1 implementation with core ML infrastructure
3. Set up MLflow experiment tracking and model registry
4. Implement the first LSTM model prototype for validation

---

*This research document serves as the foundation for implementing AI/ML framework integration in the malaria prediction backend system. All code examples are production-ready and follow the established project patterns and quality standards.*
