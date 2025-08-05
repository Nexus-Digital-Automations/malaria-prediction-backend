# Malaria Prediction System

AI-powered malaria outbreak prediction using LSTM and Transformers with environmental data from African data sources.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd malaria-prediction

# Install dependencies with uv
uv sync --dev

# Run tests
uv run pytest

# Start development server
uv run malaria-predictor serve --reload
```

## 🏗️ Architecture

The system combines multiple environmental data sources with advanced AI models to predict malaria outbreak risk:

- **Data Sources**: ERA5 climate data, CHIRPS rainfall, Malaria Atlas Project, WorldPop demographics
- **AI Models**: LSTM for time-series prediction + Transformers for pattern recognition
- **API**: FastAPI with async endpoints for area/time-based predictions
- **Database**: PostgreSQL with TimescaleDB for time-series environmental data

## 🌍 Environmental Factors

The system tracks key environmental determinants of malaria transmission:

- **Temperature**: Daily mean/min/max (optimal ~25°C, transmission window 18-34°C)
- **Rainfall**: Monthly patterns (80mm+ needed for transmission)
- **Vegetation**: NDVI/EVI indices from satellite imagery
- **Topography**: Elevation, slope, drainage characteristics
- **Population**: Density and housing quality factors

## 💻 Development

This project uses modern Python development practices:

- **Package Management**: `uv` for fast, reliable dependency management
- **Code Quality**: `ruff` (linting) + `mypy` (type checking)
- **Testing**: `pytest` with 95% coverage target
- **Documentation**: Comprehensive docs in `docs/development/`

### Development Commands
```bash
# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/

# Run tests with coverage
uv run pytest --cov

# Start development server
uv run malaria-predictor serve --host 0.0.0.0 --port 8000 --reload
```

### Project Structure
```
malaria-prediction/
├── src/malaria_predictor/          # Main application package
│   ├── __init__.py
│   ├── config.py                   # Configuration settings
│   ├── cli.py                      # Command-line interface
│   ├── models.py                   # Data models
│   └── services/                   # Business logic services
├── tests/                          # Test suite
├── docs/development/               # Development documentation
├── pyproject.toml                  # Project configuration
└── TODO.json                       # Task management
```

## 🔌 API Endpoints (Coming Soon)

- `GET /api/v1/predict/{area}` - Get malaria risk prediction for area
- `GET /api/v1/data/environmental` - Access historical environmental data
- `GET /api/v1/data/malaria` - Access historical malaria data
- `POST /api/v1/models/train` - Trigger model training

## 📊 Data Sources

The system integrates 80+ open-source environmental datasets:

### Priority Sources
- **ERA5**: Temperature data (31km resolution)
- **CHIRPS**: Rainfall data (5.5km resolution)
- **Malaria Atlas Project**: Historical malaria risk maps
- **MODIS**: Vegetation indices (250m resolution)
- **WorldPop**: Population distribution (100m resolution)

See `docs/development/` for comprehensive data source documentation.

## 🤖 AI/ML Pipeline

### LSTM Models
- Time-series prediction for seasonal malaria patterns
- Environmental factor sequence modeling
- Multi-step ahead forecasting

### Transformer Models
- Complex pattern recognition in multi-dimensional environmental data
- Cross-attention between different data modalities
- Uncertainty quantification in predictions

## 📈 Current Status

**Phase 1: Foundation** ✅ **COMPLETE**
- [x] Modern Python project setup with uv package manager
- [x] ADDER+ development environment (ruff, mypy, pytest)
- [x] Project structure and configuration following best practices
- [x] Comprehensive development documentation (34 files)
- [x] Core risk assessment system with research-based algorithms
- [x] 100% test coverage for business logic (708 lines code, 796 lines tests)
- [x] Full type safety and code quality standards
- [x] Working CLI interface with 4 commands

**Phase 2: Data Pipeline** (Next)
- [ ] Environmental data ingestion services
- [ ] Data validation and cleaning pipeline
- [ ] Time-series database setup
- [ ] Data harmonization layer

**Phase 3: AI/ML Development** (Planned)
- [ ] LSTM implementation
- [ ] Transformer models
- [ ] Feature engineering pipeline
- [ ] Model training infrastructure

**Phase 4: API & Deployment** (Planned)
- [ ] FastAPI application
- [ ] Prediction endpoints
- [ ] Authentication system
- [ ] Docker containerization

## 🤝 Contributing

This project follows modern Python development practices with automated code quality tools. See `modes/development.md` for detailed development guidelines.

## 📄 License

MIT License - See LICENSE file for details.

## 🔗 Links

- **Documentation**: `docs/development/`
- **Data Sources**: Over 80 open-source environmental datasets documented
- **Architecture**: See `docs/development/architecture-overview.md`
