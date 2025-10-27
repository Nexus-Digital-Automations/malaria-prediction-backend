# Model Evaluation

> **Performance metrics and validation procedures**

## Key Metrics

### Classification Metrics

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

# Calculate metrics
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)
auc_roc = roc_auc_score(y_true, y_pred_proba)
```

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Accuracy** | (TP + TN) / Total | Overall correctness |
| **Precision** | TP / (TP + FP) | Positive prediction accuracy |
| **Recall** | TP / (TP + FN) | True positive coverage |
| **F1 Score** | 2 × (Precision × Recall) / (Precision + Recall) | Harmonic mean |
| **AUC-ROC** | Area under ROC curve | Model discrimination ability |

### Regression Metrics

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

mae = mean_absolute_error(y_true, y_pred)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))
r2 = r2_score(y_true, y_pred)
```

## Production Benchmarks

| Model | Accuracy | F1 | MAE | Inference Time |
|-------|----------|-----|-----|----------------|
| LSTM | 0.89 | 0.89 | 0.06 | 25ms |
| Transformer | 0.90 | 0.90 | 0.05 | 75ms |
| Ensemble | **0.92** | **0.92** | **0.04** | 150ms |

## Cross-Validation

```python
from sklearn.model_selection import KFold, cross_val_score

kfold = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(
    model, X, y,
    cv=kfold,
    scoring='f1',
    n_jobs=-1
)

print(f"Mean F1: {scores.mean():.3f} (+/- {scores.std():.3f})")
```

## Monitoring in Production

```python
# Track prediction distribution
def monitor_predictions(predictions):
    mean_score = np.mean(predictions)
    std_score = np.std(predictions)

    if mean_score > 0.7:  # Unusually high
        alert_team("High risk scores detected")

    if std_score < 0.05:  # Low variance
        alert_team("Model may be degraded")
```

---

**Last Updated**: October 27, 2025
