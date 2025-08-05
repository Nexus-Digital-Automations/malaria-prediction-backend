# Development Documentation

This directory contains summarized development documentation for the malaria prediction system.

## Files Overview

- **`architecture-overview.md`**: High-level system architecture and component overview
- **`environmental-factors.md`**: Key environmental factors to track for malaria prediction
- **`environmental-data-sources.md`**: Priority data sources for implementation
- **`data-sources-summary.md`**: Comprehensive summary of 80+ available data sources

## Key Implementation Points

### Technology Stack
- **Backend**: FastAPI with Python 3.12
- **Package Management**: uv (modern Python package manager)
- **Code Quality**: ruff, mypy, pytest with 95% coverage target
- **AI/ML**: PyTorch for LSTM + Transformers
- **Database**: PostgreSQL + TimescaleDB for time-series data

### Data Pipeline Priority
1. **Phase 1**: ERA5 (temperature) + CHIRPS (rainfall) + MAP (malaria baseline)
2. **Phase 2**: MODIS/Sentinel-2 (vegetation) + WorldPop (population)
3. **Phase 3**: Vector surveillance + resistance data

### Environmental Factors
- Temperature is the primary limiting factor (optimal ~25°C, transmission window 18-34°C)
- Rainfall creates breeding sites (80mm+ monthly needed)
- Vegetation indices (NDVI/EVI) are strong predictors
- Topography affects risk (elevation thresholds 1,400-2,000m in East Africa)

### API Design
- RESTful endpoints for area/time-based predictions
- Authentication with API keys and rate limiting
- Real-time and historical data access
- OpenAPI documentation

## Next Development Steps

1. **Foundation**: Complete project setup with ADDER+ standards
2. **Data Ingestion**: Build scrapers for priority data sources
3. **ML Pipeline**: Implement LSTM/Transformer models
4. **API Development**: Create FastAPI endpoints
5. **Testing**: Achieve 95% test coverage
6. **Documentation**: Complete API and deployment docs
