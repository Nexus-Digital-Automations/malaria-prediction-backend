# ADR-002: Ensemble ML Model Architecture

## Status
Accepted

## Context

We needed to design a machine learning architecture capable of:
- Predicting malaria outbreak risk with high accuracy
- Handling temporal patterns in environmental data (seasonality, trends)
- Providing uncertainty quantification for risk predictions
- Supporting both short-term and long-term forecasting
- Processing multi-dimensional environmental features

Options considered:
1. **Single LSTM Model** - Good for sequences, but limited perspective
2. **Single Transformer Model** - Excellent attention mechanism, computationally expensive
3. **Gradient Boosting (XGBoost/LightGBM)** - Fast, but less suited for sequences
4. **Ensemble Approach** - Combines multiple models for robustness

## Decision

We chose an **Ensemble Architecture** combining LSTM, Transformer, and ensemble fusion:

### Model Components

1. **LSTM Model (MalariaLSTM)**
   - Captures sequential dependencies in time-series data
   - Handles variable-length input sequences
   - Effective for short to medium-term patterns

2. **Transformer Model (MalariaTransformer)**
   - Self-attention mechanism for long-range dependencies
   - Parallel processing for faster training
   - Better at capturing complex feature interactions

3. **Ensemble Model (MalariaEnsembleModel)**
   - Weighted combination of LSTM and Transformer predictions
   - Learnable weights based on historical performance
   - Provides uncertainty estimation through model disagreement

### Architecture Details

```
Environmental Features (30-day sequences)
         │
         ▼
┌────────────────────────────────────┐
│      Feature Engineering           │
│  • Normalization                   │
│  • Temporal encoding               │
│  • Missing value handling          │
└────────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────────┐
│ LSTM  │ │Transformer│
│Model  │ │  Model    │
└───┬───┘ └─────┬─────┘
    │           │
    └─────┬─────┘
          ▼
┌────────────────────────────────────┐
│      Ensemble Fusion               │
│  • Weighted averaging              │
│  • Uncertainty quantification      │
│  • Confidence scoring              │
└────────────────────────────────────┘
          │
          ▼
    Risk Prediction
    (Low/Medium/High)
```

## Consequences

### Positive
- Higher prediction accuracy than single models
- Uncertainty quantification through model disagreement
- Robustness to different types of patterns
- Flexibility to add/remove models from ensemble
- MLflow integration for experiment tracking and model versioning

### Negative
- Higher computational requirements (3x inference time)
- More complex training and deployment pipeline
- Larger memory footprint
- Requires careful model synchronization

### Mitigations
- Model caching with Redis for repeated predictions
- Batch prediction support for efficiency
- Asynchronous model loading and inference
- Model quantization options for deployment

## References

- [ML Model Architecture Documentation](../../ml/model-architecture.md)
- [Training Guide](../../ml/training-guide.md)
- [PyTorch Lightning](https://lightning.ai/)
