# Malaria Prediction Backend - Testing Framework

## Overview

This document describes the comprehensive testing framework implemented for the malaria prediction backend system. The testing suite covers unit tests, integration tests, performance tests, and end-to-end workflows.

## Test Structure

```
tests/
├── README.md                          # This documentation
├── conftest.py                        # Shared test fixtures and configuration
├── __init__.py                        # Test module initialization
│
├── Unit Tests                         # Test individual components
│   ├── test_models_final.py          # Core Pydantic models (100% coverage)
│   ├── test_ml_models_comprehensive.py # ML models (LSTM, Transformer, Ensemble)
│   ├── test_config.py                 # Configuration validation
│   ├── test_database.py              # Database models and operations
│   └── test_services_*.py            # Business logic services
│
├── integration/                       # Test component interactions
│   ├── conftest.py                   # Integration test fixtures
│   ├── test_database_integration.py  # Database + API integration
│   ├── test_ml_model_integration.py  # ML models + data pipeline
│   ├── test_external_api_integration.py # External data sources
│   └── test_end_to_end_prediction_workflow.py # Complete workflows
│
├── performance/                       # Performance and load testing
│   ├── __init__.py
│   └── test_performance_benchmarks.py # ML inference, API response times
│
└── e2e/                              # End-to-end testing
    ├── conftest.py
    └── test_prediction_pipeline.py   # Complete prediction workflows
```

## Testing Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation
**Coverage Target**: 90%+ for critical modules

#### Core Models (`test_models_final.py`)
- **RiskLevel**: Enum validation and string conversion
- **EnvironmentalFactors**: Field validation, bounds checking, serialization
- **GeographicLocation**: Coordinate validation, required fields
- **RiskAssessment**: Risk scoring, factor validation, confidence metrics
- **MalariaPrediction**: Complete prediction workflow integration

**Current Coverage**: 100% for models.py (53/53 lines)

#### ML Models (`test_ml_models_comprehensive.py`)
- **LSTM Models**: Architecture validation, forward pass, serialization
- **Transformer Models**: Attention mechanisms, sequence handling
- **Ensemble Models**: Multi-model integration, uncertainty estimation
- **Performance**: GPU acceleration, memory usage, gradient flow

### 2. Integration Tests

**Purpose**: Test component interactions and data flow
**Scope**: Database + API, ML + Data Pipeline, External APIs

#### Database Integration
- Connection handling and session management
- Repository pattern validation
- Transaction handling and rollback scenarios
- TimescaleDB time-series operations

#### ML Model Integration
- Data preprocessing → Model inference → Results
- Feature extraction pipeline validation
- Model loading and caching mechanisms
- Batch processing workflows

#### External API Integration
- ERA5, CHIRPS, MODIS, MAP, WorldPop data sources
- API rate limiting and error handling
- Data quality validation and harmonization
- Retry mechanisms and fallback strategies

### 3. Performance Tests

**Purpose**: Validate system performance under load
**Metrics**: Response time, throughput, memory usage, CPU utilization

#### ML Model Performance
```python
# Performance benchmarks for different batch sizes
test_cases = [
    (1, 30, 15),    # Single prediction
    (10, 30, 15),   # Small batch
    (50, 30, 15),   # Medium batch
    (100, 30, 15),  # Large batch
]

# Performance targets
assert response_time_p95 < 2.0  # 95% under 2 seconds
assert memory_usage < 2000      # Under 2GB
assert throughput > 10          # 10+ predictions/second
```

#### API Performance
- Health endpoint: <100ms average response time
- Single prediction: <500ms average, <1s p95
- Batch prediction: >5 predictions/second throughput
- Concurrent requests: 50 concurrent users supported

### 4. End-to-End Tests

**Purpose**: Test complete user workflows
**Scope**: Full prediction pipeline from data ingestion to risk assessment

## Test Execution

### Running All Tests

```bash
# Full test suite with coverage
uv run pytest tests/ --cov=src/malaria_predictor --cov-report=html

# Unit tests only
uv run pytest tests/test_*.py -v

# Integration tests only  
uv run pytest tests/integration/ -v

# Performance tests only
uv run pytest tests/performance/ -v

# Specific test class
uv run pytest tests/test_models_final.py::TestEnvironmentalFactors -v
```

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest --cov=src/malaria_predictor --cov-report=html
open htmlcov/index.html

# Terminal coverage report
uv run pytest --cov=src/malaria_predictor --cov-report=term-missing

# Coverage with branch analysis
uv run pytest --cov=src/malaria_predictor --cov-branch --cov-report=term
```

## Current Test Coverage

| Module | Coverage | Lines | Missing |
|--------|----------|-------|---------|
| models.py | 100% | 53/53 | None |
| config.py | 58% | 134/231 | Config loading, env validation |
| secrets.py | 16% | 21/130 | Security utilities |
| **Overall** | **1.65%** | **210/12,886** | Most modules |

### Priority Areas for Additional Testing

1. **High Priority** (Core functionality):
   - `api/main.py` - FastAPI application
   - `api/routers/prediction.py` - Prediction endpoints
   - `services/risk_calculator.py` - Risk assessment logic
   - `ml/models/` - All ML model implementations

2. **Medium Priority** (Business logic):
   - `services/data_processor.py` - Data processing pipelines
   - `database/repositories.py` - Data access layer
   - `api/auth.py` - Authentication and authorization

3. **Lower Priority** (Infrastructure):
   - `monitoring/` - Monitoring and observability
   - `cli.py` - Command-line interface
   - `config_validation.py` - Configuration validation

## Test Data and Fixtures

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def sample_environmental_data():
    """Standard environmental data for testing."""
    return EnvironmentalFactors(
        mean_temperature=25.5,
        min_temperature=20.0,
        max_temperature=30.0,
        monthly_rainfall=120.0,
        relative_humidity=75.0,
        ndvi=0.6,
        elevation=1200.0,
        population_density=150.0
    )

@pytest.fixture
def sample_location():
    """Standard geographic location for testing."""
    return GeographicLocation(
        latitude=-1.2921,
        longitude=36.8219,
        area_name="Nairobi County",
        country_code="KE",
        admin_level="County"
    )
```

### Test Data Principles

1. **Realistic Data**: Use actual coordinate ranges, environmental conditions
2. **Edge Cases**: Test boundary conditions, extreme values
3. **Error Conditions**: Invalid inputs, missing fields, out-of-range values
4. **Consistency**: Reusable fixtures for common test scenarios

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
- Unit Tests: All platforms, Python 3.12
- Integration Tests: PostgreSQL + Redis services
- Performance Tests: Benchmark tracking
- Security Scanning: Bandit, Safety, Trivy
- Code Quality: Ruff, MyPy, coverage reports
```

### Quality Gates

- **All unit tests must pass** (0 failures tolerated)
- **Coverage threshold**: 90% for new code
- **Linting**: Zero Ruff violations
- **Security**: No high-severity vulnerabilities
- **Performance**: Response times within SLA

## Testing Best Practices

### 1. Test Naming Convention

```python
def test_[component]_[scenario]_[expected_outcome]():
    """Clear description of what is being tested."""
```

### 2. Test Structure (AAA Pattern)

```python
def test_risk_assessment_validation():
    # Arrange
    risk_data = create_test_risk_data()
    
    # Act
    risk = RiskAssessment(**risk_data)
    
    # Assert
    assert risk.risk_score == 0.75
    assert risk.risk_level == RiskLevel.HIGH
```

### 3. Assertion Guidelines

- **Specific assertions**: Test exact values, not just truthiness
- **Error testing**: Use `pytest.raises()` for expected exceptions
- **Multiple assertions**: Group related assertions logically
- **Descriptive messages**: Include context in assertion messages

### 4. Mock Usage

```python
# Mock external dependencies
@patch('malaria_predictor.services.era5_client.ERA5Client.fetch_data')
def test_data_integration_with_mocked_api(mock_fetch):
    mock_fetch.return_value = sample_era5_data()
    # Test logic here
```

## Performance Benchmarks

### Current Benchmarks

| Component | Metric | Target | Current |
|-----------|--------|--------|---------|
| LSTM Inference | P95 Response Time | <2s | ~1.2s |
| Transformer Inference | P95 Response Time | <5s | ~3.8s |
| API Health Check | Average Response | <100ms | ~45ms |
| Batch Prediction | Throughput | >5/s | ~12/s |

### Monitoring and Alerts

- **Performance regression detection**: 20% increase in response time
- **Memory leak detection**: Steady memory increase over test runs
- **Throughput degradation**: 10% decrease in requests/second

## Future Improvements

### Short Term (Next Sprint)

1. **Increase Unit Test Coverage**:
   - Target: 90% coverage for `api/`, `services/`, `ml/` modules
   - Add tests for error handling and edge cases
   - Mock external dependencies properly

2. **Enhanced Integration Tests**:
   - Database migration testing
   - Real external API integration (with rate limiting)
   - Cross-service communication validation

### Medium Term (Next Month)

1. **Load Testing**:
   - Implement Locust-based load tests
   - Test system behavior under 100+ concurrent users
   - Database connection pool testing

2. **Chaos Engineering**:
   - Network failure simulation
   - Database failover testing
   - External API outage scenarios

### Long Term (Next Quarter)

1. **Property-Based Testing**:
   - Hypothesis-based test generation
   - Fuzzing for environmental data inputs
   - Model invariant validation

2. **Visual Regression Testing**:
   - API response format validation
   - Model output consistency checks
   - Data visualization testing

## Troubleshooting Common Issues

### Test Environment Setup

```bash
# If tests fail to import modules
export PYTHONPATH="${PYTHONPATH}:/app/src"

# If database tests fail
docker-compose up -d postgres
# Wait for database to be ready
docker-compose exec postgres pg_isready

# If Redis tests fail
docker-compose up -d redis
```

### Common Test Failures

1. **Import Errors**: Check PYTHONPATH and virtual environment
2. **Database Connection**: Ensure test database is running
3. **Async Test Issues**: Use `pytest-asyncio` plugin correctly
4. **Memory Leaks in Tests**: Clean up large objects in teardown

## Contributing

When adding new tests:

1. **Follow the existing structure** and naming conventions
2. **Add tests for both happy path and error cases**
3. **Update this documentation** for new test categories
4. **Ensure tests are deterministic** and don't depend on external state
5. **Use appropriate fixtures** to avoid code duplication

For questions about testing, refer to:
- Project maintainers
- Existing test examples in the codebase
- This documentation for patterns and best practices