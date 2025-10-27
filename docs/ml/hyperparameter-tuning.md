# Hyperparameter Tuning

> **Optimize model hyperparameters for best performance**

## Key Hyperparameters

### LSTM Model

| Parameter | Range | Default | Impact |
|-----------|-------|---------|--------|
| `hidden_dim` | [64, 512] | 256 | Model capacity |
| `num_layers` | [2, 4] | 3 | Model depth |
| `dropout` | [0.1, 0.5] | 0.3 | Regularization |
| `learning_rate` | [1e-5, 1e-2] | 1e-3 | Convergence speed |
| `batch_size` | [16, 64] | 32 | Training stability |

### Transformer Model

| Parameter | Range | Default | Impact |
|-----------|-------|---------|--------|
| `model_dim` | [256, 1024] | 512 | Model capacity |
| `num_heads` | [4, 16] | 8 | Attention diversity |
| `num_layers` | [2, 6] | 3 | Model depth |
| `ff_dim` | [1024, 4096] | 2048 | FFN capacity |
| `dropout` | [0.1, 0.3] | 0.2 | Regularization |

## Tuning Methods

### Grid Search

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'hidden_dim': [128, 256, 512],
    'num_layers': [2, 3, 4],
    'dropout': [0.2, 0.3, 0.4]
}

grid_search = GridSearchCV(
    model,
    param_grid,
    cv=5,
    scoring='f1',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
```

### Random Search (Faster)

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import uniform, randint

param_distributions = {
    'hidden_dim': randint(64, 512),
    'dropout': uniform(0.1, 0.4),
    'learning_rate': uniform(1e-5, 1e-2)
}

random_search = RandomizedSearchCV(
    model,
    param_distributions,
    n_iter=50,
    cv=5,
    scoring='f1'
)

random_search.fit(X_train, y_train)
```

### Optuna (Bayesian Optimization)

```python
import optuna

def objective(trial):
    params = {
        'hidden_dim': trial.suggest_int('hidden_dim', 64, 512),
        'num_layers': trial.suggest_int('num_layers', 2, 4),
        'dropout': trial.suggest_float('dropout', 0.1, 0.5),
        'lr': trial.suggest_loguniform('lr', 1e-5, 1e-2)
    }

    model = train_model(**params)
    return model.val_f1_score

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)

print(f"Best hyperparameters: {study.best_params}")
```

## Best Practices

1. **Start with defaults** - Use known good values
2. **One parameter at a time** - Isolate effects
3. **Use validation set** - Never tune on test set
4. **Monitor overfitting** - Track train vs validation metrics
5. **Budget wisely** - More trials for critical parameters

---

**Last Updated**: October 27, 2025
