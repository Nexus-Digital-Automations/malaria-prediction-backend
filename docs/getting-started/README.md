# Getting Started with Malaria Prediction System

> **🚀 Quick setup guide to get you up and running in minutes**

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development Setup](#local-development-setup)
- [First API Request](#first-api-request)
- [Running Tests](#running-tests)
- [Next Steps](#next-steps)

---

## Prerequisites

### Required Software
- **Docker** 20.10+ & Docker Compose (recommended for quickstart)
- **Python** 3.11+ (for local development)
- **uv** package manager (for local development)
- **Git** for version control

### Optional Tools
- **PostgreSQL** 14+ with TimescaleDB extension (if not using Docker)
- **Redis** 6+ (if not using Docker)
- **Node.js** 18+ (for development tools)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 20GB free space for datasets and models
- **OS**: Linux, macOS, or Windows with WSL2

---

## Quick Start (Docker)

**🎯 Get the system running in 5 minutes**

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/malaria-prediction-backend.git
cd malaria-prediction-backend
```

### 2. Configure Environment
```bash
# Copy the development environment template
cp .env.development .env

# (Optional) Edit .env to customize settings
nano .env
```

### 3. Start All Services
```bash
# Start API, database, Redis, monitoring stack
docker-compose up -d

# Check service health
docker-compose ps
```

### 4. Verify Installation
```bash
# Check API health
curl http://localhost:8000/health/liveness

# Expected response:
# {"status": "healthy", "timestamp": "2025-11-03T..."}

# Check detailed system status
curl http://localhost:8000/health/readiness

# Access API documentation
# Open browser to http://localhost:8000/docs
```

### 5. Access Monitoring Dashboards
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Operations Dashboard**: http://localhost:8000/operations/dashboard
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3000

**🎉 Your system is now running!**

---

## Local Development Setup

**For active development without Docker**

### 1. Install uv Package Manager
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### 2. Clone and Setup Project
```bash
git clone https://github.com/yourusername/malaria-prediction-backend.git
cd malaria-prediction-backend

# Install all dependencies (including dev dependencies)
uv sync --dev

# Verify Python environment
uv run python --version  # Should show Python 3.11+
```

### 3. Setup Local Database
```bash
# Option A: Use Docker for database only
docker-compose up -d db redis

# Option B: Install PostgreSQL + TimescaleDB locally
# Follow: https://docs.timescale.com/install/latest/

# Run database migrations
uv run alembic upgrade head
```

### 4. Configure Environment
```bash
# Copy and edit environment file
cp .env.development .env

# Update database connection for local development
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/malaria_db
# REDIS_URL=redis://localhost:6379/0
```

### 5. Start Development Server
```bash
# Start API with auto-reload
uv run malaria-predictor serve --reload

# API will be available at http://localhost:8000
```

### 6. Verify Development Setup
```bash
# In a new terminal, run tests
uv run pytest --cov

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/
```

---

## First API Request

### 1. Obtain Authentication Token

```bash
# Login and get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin_password"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }

# Save token for subsequent requests
export TOKEN="your_access_token_here"
```

### 2. Make a Prediction Request

```bash
# Single location prediction
curl -X POST "http://localhost:8000/predict/single" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "latitude": -1.2921,
      "longitude": 36.8219,
      "area_name": "Nairobi, Kenya"
    },
    "environmental_data": {
      "mean_temperature": 22.5,
      "monthly_rainfall": 85.2,
      "relative_humidity": 68.5,
      "elevation": 1795.0
    },
    "prediction_date": "2025-02-01",
    "model_type": "ensemble"
  }'

# Response:
# {
#   "prediction": {
#     "risk_score": 0.73,
#     "risk_level": "HIGH",
#     "confidence": 0.89,
#     "uncertainty_bounds": {"lower": 0.61, "upper": 0.85}
#   },
#   "factors": {
#     "temperature": {"contribution": 0.35, "value": 22.5},
#     "rainfall": {"contribution": 0.28, "value": 85.2},
#     "humidity": {"contribution": 0.22, "value": 68.5}
#   },
#   "metadata": {
#     "model_version": "ensemble-v1.2.0",
#     "prediction_date": "2025-02-01",
#     "generated_at": "2025-11-03T12:34:56Z"
#   }
# }
```

### 3. Explore Other Endpoints

```bash
# Batch predictions for multiple locations
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"latitude": -1.2921, "longitude": 36.8219, "area_name": "Nairobi"},
      {"latitude": -4.0435, "longitude": 39.6682, "area_name": "Mombasa"}
    ],
    "time_horizon_days": 30,
    "model_type": "ensemble"
  }'

# Time series prediction
curl -X POST "http://localhost:8000/predict/time-series" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": -1.2921, "longitude": 36.8219},
    "start_date": "2025-02-01",
    "end_date": "2025-05-01",
    "interval_days": 7
  }'

# Get system health metrics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/health/metrics"
```

---

## Running Tests

### Full Test Suite
```bash
# Run all tests with coverage
uv run pytest --cov --cov-report=html

# Open coverage report
# Open htmlcov/index.html in browser
```

### Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# API endpoint tests
uv run pytest tests/api/ -v

# ML model tests
uv run pytest tests/ml/ -v
```

### Code Quality Checks
```bash
# Linting (auto-fix issues)
uv run ruff check . --fix

# Type checking
uv run mypy src/

# Security scanning
uv run bandit -r src/

# All quality checks
uv run ruff check . && uv run mypy src/ && uv run bandit -r src/
```

---

## Next Steps

### Learn the System
1. **📖 Read Documentation**
   - [API Reference](../api/endpoints.md) - Explore all available endpoints
   - [ML Models](../ml/model-architecture.md) - Understand prediction models
   - [Data Sources](../data-sources/overview.md) - Learn about environmental data

2. **🔍 Explore Examples**
   - [Code Examples](../examples/) - Sample code snippets
   - [User Guides](../user-guides/) - Common use cases

3. **🏗️ Architecture Deep Dive**
   - [System Architecture](../architecture/) - Technical architecture
   - [Security](../security/) - Security features and compliance

### Development Workflow
1. **Make Changes**
   ```bash
   # Create feature branch
   git checkout -b feature/your-feature-name

   # Make code changes
   # ...

   # Run tests
   uv run pytest
   ```

2. **Pre-Commit Quality Checks**
   ```bash
   # Install pre-commit hooks
   uv run pre-commit install

   # Hooks will run automatically on commit
   # Or run manually:
   uv run pre-commit run --all-files
   ```

3. **Submit Changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name

   # Create Pull Request on GitHub
   ```

### Common Tasks
- **Train Models**: See [Training Guide](../ml/training-guide.md)
- **Ingest Data**: See [Data Sources](../data-sources/overview.md)
- **Deploy to Production**: See [Deployment](../deployment/DOCKER.md)
- **Monitor System**: See [Monitoring Guide](../monitoring/PRODUCTION_MONITORING_GUIDE.md)

---

## Troubleshooting

### Docker Issues
```bash
# Services not starting?
docker-compose logs api  # Check API logs
docker-compose logs db   # Check database logs

# Reset everything
docker-compose down -v  # Remove all containers and volumes
docker-compose up -d    # Start fresh
```

### Database Connection Issues
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify connection
docker-compose exec db psql -U postgres -d malaria_db -c "SELECT 1;"
```

### API Errors
```bash
# Check API logs
docker-compose logs -f api

# Verify environment variables
docker-compose exec api env | grep DATABASE_URL

# Restart API service
docker-compose restart api
```

### Permission Issues (Linux)
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Docker socket permissions
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

---

## Getting Help

- **📚 Documentation**: Check [docs/README.md](../README.md) for complete docs
- **🐛 Issues**: Report bugs on GitHub Issues
- **💬 Discussions**: Join GitHub Discussions
- **📧 Contact**: See main README for contact information

---

**🌍 Ready to make malaria prediction accessible through advanced AI!**

*Last Updated: November 3, 2025*
