# Malaria Prediction System Architecture

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Sources   │    │   Data Pipeline  │    │   AI/ML Models  │
│                 │    │                  │    │                 │
│ • ERA5/CHIRPS   │───▶│ • Ingestion     │───▶│ • LSTM Models   │
│ • MAP/WorldPop  │    │ • Validation    │    │ • Transformers  │
│ • MODIS/Sentinel│    │ • Cleaning      │    │ • Feature Eng   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Frontend UI    │    │   FastAPI App    │    │   Predictions   │
│                 │◀───│                  │◀───│                 │
│ • Risk Maps     │    │ • REST API       │    │ • Area-based    │
│ • Alerts        │    │ • Authentication │    │ • Time-based    │
│ • Dashboards    │    │ • Rate Limiting  │    │ • Risk Scores   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Data Layer
- **Environmental Data Ingestion**: Automated scrapers for WHO, MAP, CHIRPS, ERA5, WorldPop
- **Time-Series Database**: PostgreSQL + TimescaleDB for environmental data
- **Data Validation**: Pydantic models for data consistency
- **Harmonization**: Standardize different source formats/resolutions

### 2. AI/ML Layer
- **LSTM Models**: Time-series prediction for outbreak patterns
- **Transformer Models**: Complex pattern recognition in multi-dimensional data
- **Feature Engineering**: Climate, population, historical outbreak preparation
- **Model Training**: Automated pipelines with MLflow tracking
- **Model Serving**: Optimized inference endpoints

### 3. API Layer
- **FastAPI Application**: Async REST API with OpenAPI documentation
- **Prediction Endpoints**: Area/time-based outbreak predictions
- **Data Access**: Historical environmental/malaria data retrieval
- **Authentication**: API key management with rate limiting

### 4. Infrastructure Layer
- **Job Scheduling**: Celery + Redis for background tasks
- **Monitoring**: System health, model performance tracking
- **Caching**: Redis for prediction results
- **Configuration**: Environment-based settings

## Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Package Management**: uv
- **Code Quality**: ruff, mypy, pytest
- **AI/ML**: PyTorch, Transformers, scikit-learn
- **Database**: PostgreSQL + TimescaleDB
- **Task Queue**: Celery + Redis
- **Monitoring**: MLflow, structlog

## Data Flow

1. **Ingestion**: Automated collection from environmental data sources
2. **Processing**: Clean, validate, and harmonize data
3. **Feature Engineering**: Extract relevant environmental factors
4. **Model Training**: Train LSTM/Transformer models on historical data
5. **Prediction**: Generate area/time-based malaria risk predictions
6. **API Response**: Serve predictions via REST endpoints
7. **Monitoring**: Track model performance and data quality
