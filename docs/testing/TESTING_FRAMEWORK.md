# Malaria Prediction Backend - Testing Framework

## Overview

This document describes the comprehensive testing framework for the Malaria Prediction Backend, including integration tests, end-to-end tests, performance testing, and CI/CD automation.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Test Types](#test-types)
3. [Test Environment Setup](#test-environment-setup)
4. [Running Tests](#running-tests)
5. [Test Data Management](#test-data-management)
6. [Performance Testing](#performance-testing)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)

## Test Structure

The testing framework is organized into several categories:

```
tests/
├── __init__.py                 # Test package initialization
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── conftest.py            # Integration test fixtures
│   ├── test_database_integration.py
│   ├── test_redis_integration.py
│   ├── test_external_api_integration.py
│   ├── test_ml_model_integration.py
│   └── test_fastapi_integration.py
├── e2e/                       # End-to-end tests
│   ├── __init__.py
│   └── test_prediction_pipeline.py
├── fixtures/                  # Test data and fixtures
│   ├── __init__.py
│   ├── data_factory.py       # Test data generation
│   ├── data/                 # Static test data
│   └── mock-api/             # Mock API services
└── performance/              # Performance tests
    └── test_api_performance.py
```

## Test Types

### 1. Integration Tests

Integration tests validate that different components of the system work together correctly.

#### Database Integration Tests
- **File**: `tests/integration/test_database_integration.py`
- **Purpose**: Test database operations, TimescaleDB functionality, and data persistence
- **Coverage**: Database connectivity, CRUD operations, spatial/temporal queries, transactions

```python
# Example: Testing database connectivity
@pytest.mark.asyncio
async def test_database_connection(test_db_session):
    result = await test_db_session.execute(text("SELECT 1 as test"))
    assert result.scalar() == 1
```

#### Redis Integration Tests
- **File**: `tests/integration/test_redis_integration.py`
- **Purpose**: Test caching functionality and Redis operations
- **Coverage**: Cache operations, session management, invalidation strategies

#### External API Integration Tests
- **File**: `tests/integration/test_external_api_integration.py`
- **Purpose**: Test integration with external APIs using mock services
- **Coverage**: ERA5, CHIRPS, MODIS, WorldPop, MAP API integrations

#### ML Model Integration Tests
- **File**: `tests/integration/test_ml_model_integration.py`
- **Purpose**: Test ML model loading, inference, and management
- **Coverage**: Model loading, inference pipeline, feature extraction, evaluation

#### FastAPI Integration Tests
- **File**: `tests/integration/test_fastapi_integration.py`
- **Purpose**: Test FastAPI endpoints and middleware
- **Coverage**: Authentication, prediction endpoints, error handling, middleware

### 2. End-to-End Tests

End-to-end tests validate complete workflows from data ingestion to prediction delivery.

#### Prediction Pipeline Tests
- **File**: `tests/e2e/test_prediction_pipeline.py`
- **Purpose**: Test complete prediction workflows
- **Coverage**: Single predictions, batch processing, time series, spatial grids

### 3. Performance Tests

Performance tests validate system performance and identify bottlenecks.

#### API Performance Tests
- **File**: `tests/performance/test_api_performance.py`
- **Purpose**: Test API response times and throughput
- **Coverage**: Response time regression, throughput testing, load testing

## Test Environment Setup

### Docker Compose Test Environment

The test environment uses Docker Compose to provide isolated, reproducible testing conditions:

```yaml
# docker-compose.test.yml
services:
  test-database:    # TimescaleDB with PostGIS
  test-redis:       # Redis cache
  test-api:         # FastAPI application
  mock-api:         # Mock external APIs
  test-runner:      # Test execution environment
```

### Service Configuration

- **PostgreSQL**: Port 5433 (test), isolated test database
- **Redis**: Port 6380 (test), isolated test cache
- **API**: Port 8001 (test), test configuration
- **Mock APIs**: Ports 9000-9005, realistic mock responses

### Environment Variables

```bash
# Test database
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction

# Test cache
REDIS_URL=redis://localhost:6380/0

# Test environment
ENVIRONMENT=test
TESTING=true
```

## Running Tests

### Using the Test Script

The comprehensive test script provides multiple execution options:

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test types
./scripts/run_tests.sh --type unit
./scripts/run_tests.sh --type integration
./scripts/run_tests.sh --type e2e
./scripts/run_tests.sh --type performance

# Run with options
./scripts/run_tests.sh --verbose --no-cleanup
./scripts/run_tests.sh --parallel --type integration
```

### Manual Test Execution

#### Unit Tests
```bash
uv run pytest tests/ \
  --ignore=tests/integration \
  --ignore=tests/e2e \
  --ignore=tests/performance \
  --cov=src/malaria_predictor
```

#### Integration Tests
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d test-database test-redis mock-api

# Run integration tests
uv run pytest tests/integration/
```

#### End-to-End Tests
```bash
# Start full test environment
docker-compose -f docker-compose.test.yml up -d

# Run E2E tests
uv run pytest tests/e2e/
```

### Docker-Based Test Execution

```bash
# Run all tests in Docker
docker-compose -f docker-compose.test.yml up test-runner

# Run specific test suites
docker-compose -f docker-compose.test.yml up integration-tests
docker-compose -f docker-compose.test.yml up e2e-tests
```

## Test Data Management

### Test Data Factory

The `DataFactory` classes provide realistic test data generation:

```python
# Environmental data
era5_data = EnvironmentalDataFactory.create_era5_data(
    location=Location(latitude=-1.286389, longitude=36.817222),
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Prediction responses
prediction = PredictionDataFactory.create_prediction_response(
    risk_level="medium",
    model_type="ensemble"
)
```

### Test Fixtures

#### Locations
Pre-defined test locations with known characteristics:
- **Nairobi, Kenya**: High altitude, urban, moderate malaria risk
- **Lagos, Nigeria**: Coastal, urban, high malaria risk
- **Kinshasa, DRC**: Tropical, urban, very high malaria risk
- **Cape Town, South Africa**: Mediterranean climate, low malaria risk

#### Data Sources
Realistic mock data for all external APIs:
- ERA5 climate data with seasonal patterns
- CHIRPS precipitation with realistic distribution
- MODIS vegetation indices with quality flags
- WorldPop demographic data with age structure
- MAP malaria data with intervention coverage

### Database Test Data

```python
# Create test environmental records
records = DatabaseTestDataFactory.create_environmental_records(
    locations=[nairobi_location, lagos_location],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

## Performance Testing

### Performance Benchmarks

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Single Prediction | < 2.0s | Complete single prediction workflow |
| Batch Throughput | > 10 predictions/s | Batch prediction processing rate |
| Database Query | < 0.5s | Average database query time |
| Cache Hit Ratio | > 80% | Minimum cache efficiency |
| Memory Usage | < 1GB | Maximum memory consumption |
| Model Inference | < 0.1s | ML model prediction time |

### Performance Test Examples

```python
@pytest.mark.asyncio
async def test_prediction_response_time():
    start_time = time.time()

    response = await client.post("/predict/single", json=request_data)

    end_time = time.time()
    response_time = end_time - start_time

    assert response.status_code == 200
    assert response_time < 2.0  # Performance threshold
```

### Load Testing

```python
@pytest.mark.asyncio
async def test_concurrent_predictions():
    tasks = [
        client.post("/predict/single", json=request)
        for request in prediction_requests
    ]

    responses = await asyncio.gather(*tasks)

    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)

    # Performance should not degrade significantly
    assert max_response_time < threshold
```

## CI/CD Integration

### GitHub Actions Workflow

The CI/CD pipeline includes multiple test stages:

1. **Code Quality**: Linting, formatting, type checking
2. **Unit Tests**: Fast, isolated component tests
3. **Integration Tests**: Component interaction tests
4. **End-to-End Tests**: Complete workflow validation
5. **Performance Tests**: Performance regression detection
6. **Security Scanning**: Vulnerability detection

### Workflow Triggers

- **Pull Requests**: Full test suite on main/develop branches
- **Pushes**: Incremental testing based on changes
- **Scheduled**: Nightly performance and regression tests
- **Manual**: On-demand test execution with custom parameters

### Test Parallelization

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
    test-type: ['unit', 'integration']
```

### Coverage Reporting

- **Codecov Integration**: Automatic coverage reporting
- **HTML Reports**: Detailed coverage analysis
- **Coverage Thresholds**: Minimum coverage requirements
- **Differential Coverage**: Coverage on changed code

## Test Configuration

### Pytest Configuration

```ini
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=src/malaria_predictor --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "performance: marks tests as performance tests",
    "slow: marks tests as slow running",
]
```

### Test Fixtures Configuration

```python
# pytest configuration in conftest.py
@pytest.fixture(scope="session")
def test_database_engine():
    # Database setup for integration tests

@pytest.fixture
def test_client():
    # FastAPI test client

@pytest.fixture
def mock_external_apis():
    # Mock API responses
```

## Mock Services

### Mock API Server

The mock API server provides realistic responses for external services:

```python
# Mock ERA5 API
@era5_app.get("/climate-data")
async def get_era5_climate_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
):
    # Generate realistic climate data
    return generate_synthetic_era5_data(latitude, longitude, start_date, end_date)
```

### Mock Service Features

- **Realistic Data**: Location-based data generation
- **Response Delays**: Simulated network latency
- **Error Scenarios**: Failure simulation for resilience testing
- **Data Consistency**: Correlated responses across services

## Troubleshooting

### Common Issues

#### Test Environment Setup

**Issue**: Services not starting properly
```bash
# Check service health
docker-compose -f docker-compose.test.yml ps
docker-compose -f docker-compose.test.yml logs [service-name]

# Reset environment
docker-compose -f docker-compose.test.yml down --volumes
docker-compose -f docker-compose.test.yml up -d
```

#### Database Connection Issues

**Issue**: Database connection failures
```bash
# Check database connectivity
pg_isready -h localhost -p 5433 -U test_user

# Run migrations manually
export DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction
uv run alembic upgrade head
```

#### Redis Connection Issues

**Issue**: Redis connection failures
```bash
# Check Redis connectivity
redis-cli -h localhost -p 6380 ping

# Clear Redis cache
redis-cli -h localhost -p 6380 flushdb
```

### Test Debugging

#### Verbose Test Output
```bash
./scripts/run_tests.sh --verbose --type integration
```

#### Preserve Test Environment
```bash
./scripts/run_tests.sh --no-cleanup --type e2e
```

#### Container Logs
```bash
# View real-time logs
docker-compose -f docker-compose.test.yml logs -f test-api

# Save logs to file
docker-compose -f docker-compose.test.yml logs test-api > api.log
```

### Performance Debugging

#### Profiling Tests
```python
import cProfile
import pstats

def test_with_profiling():
    profiler = cProfile.Profile()
    profiler.enable()

    # Test code here

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
```

#### Memory Usage Monitoring
```python
import psutil
import os

def test_memory_usage():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Test code here

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    assert memory_increase < MEMORY_THRESHOLD
```

## Best Practices

### Test Organization

1. **Separation of Concerns**: Keep unit, integration, and E2E tests separate
2. **Test Independence**: Each test should be able to run independently
3. **Realistic Data**: Use representative test data that mirrors production
4. **Clear Naming**: Test names should clearly describe what is being tested

### Test Data Management

1. **Factory Pattern**: Use factories for consistent test data generation
2. **Fixture Cleanup**: Ensure proper cleanup to avoid test interference
3. **Data Isolation**: Use separate databases/schemas for concurrent tests
4. **Seed Consistency**: Use fixed seeds for reproducible random data

### Performance Testing

1. **Baseline Establishment**: Set clear performance baselines
2. **Trend Monitoring**: Track performance over time
3. **Realistic Load**: Use production-like load patterns
4. **Resource Monitoring**: Monitor CPU, memory, and I/O during tests

### CI/CD Integration

1. **Fast Feedback**: Optimize test execution time for quick feedback
2. **Parallel Execution**: Run tests in parallel where possible
3. **Incremental Testing**: Run relevant tests based on code changes
4. **Artifact Management**: Preserve test results and logs for analysis

## Conclusion

This comprehensive testing framework ensures the reliability, performance, and maintainability of the Malaria Prediction Backend. The framework includes:

- **Complete Coverage**: Unit, integration, E2E, and performance tests
- **Production-like Environment**: Docker-based test environment with realistic data
- **Automated Execution**: CI/CD integration with comprehensive reporting
- **Performance Monitoring**: Continuous performance validation and regression detection
- **Debugging Support**: Tools and practices for effective test debugging

The framework is designed to scale with the application and provide confidence in code changes while maintaining high development velocity.
