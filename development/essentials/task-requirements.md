# Task Requirements - Malaria Prediction Backend

## Project-Specific Success Criteria

All feature tasks must satisfy these requirements before completion:

### 1. Build Success ✅
- **Command**: `uv run ruff check .`  
- **Requirement**: Zero linting violations - all code quality rules pass
- **Alternative**: `python -m ruff check .` if uv not available

### 2. Application Startup ✅
- **FastAPI Backend**: Application starts without errors
- **Database**: PostgreSQL/TimescaleDB connections functional  
- **Environment**: All required environment variables loaded
- **Services**: Background task services (Celery/Redis) operational

### 3. Code Quality Standards ✅
- **Linting**: All Python files pass ruff checks with zero violations
- **Type Checking**: mypy strict mode compliance for critical modules
- **Documentation**: All public functions, classes, and modules documented
- **Security**: No exposed secrets, credentials, or sensitive data

### 4. Testing Requirements ✅
- **Unit Tests**: All existing tests continue to pass
- **Coverage**: New features achieve 90%+ test coverage
- **Integration**: API endpoints functional and tested
- **Data Processing**: Environmental data pipelines working correctly

### 5. Environmental Data Integration ✅
- **Data Sources**: ERA5, CHIRPS, MODIS, MAP, WorldPop connections functional
- **Processing**: Data ingestion and transformation pipelines operational
- **Validation**: Data quality checks and error handling working
- **Storage**: TimescaleDB time-series data storage functional

### 6. API Functionality ✅
- **Health Endpoints**: `/health/status`, `/health/models` operational
- **Prediction Endpoints**: `/predict/single`, `/predict/batch` functional
- **Authentication**: JWT token validation and user permissions working
- **Documentation**: OpenAPI/Swagger documentation accessible and complete

### 7. Backend-Only Data Policy Compliance ✅
- **No Mock Data**: Zero hardcoded malaria prediction data in codebase
- **API Integration**: All data sources connected to actual backend services
- **Validation**: No simulated environmental data or risk assessments
- **Enforcement**: Code review checkpoints for mock data prevention

## Task Categories and Standards

### Feature Tasks
- Must pass ALL 7 requirements above
- Include comprehensive logging and monitoring
- Document all architectural decisions
- Provide usage examples and integration guides

### Error Tasks
- Fix underlying root causes, not symptoms
- Include preventive measures to avoid recurrence
- Document resolution steps and learnings
- Validate fix doesn't break existing functionality

### Test Tasks
- Achieve target coverage percentages (90%+ for critical modules)
- Include edge cases and error scenarios
- Test both happy path and failure conditions
- Document test strategies and coverage reports

## Validation Commands

Run these commands before marking any feature task complete:

```bash
# 1. Code Quality
uv run ruff check .                    # Zero violations required
python -m mypy src/                    # Type checking

# 2. Testing
uv run pytest tests/                   # All tests pass
uv run pytest --cov=src tests/        # Coverage reporting

# 3. Application Health
python -m uvicorn src.malaria_predictor.api.main:app --reload  # Startup test

# 4. Database Connectivity
python -c "from src.malaria_predictor.database import get_database; print('DB OK')"

# 5. API Documentation
curl http://localhost:8000/docs        # Swagger UI accessible
```

## Failure Protocols

### Linter Failures
- Create immediate linter-error task
- Fix all violations before continuing
- Document fixes in commit messages

### Build Failures  
- Investigate root cause (dependencies, configuration, environment)
- Fix underlying issues, not symptoms
- Validate complete build process

### Test Failures
- If due to outdated tests: Create test-update task and continue feature work
- If due to feature bugs: Fix bugs before completing feature task
- Document test failure analysis and resolution

### Startup Failures
- Check environment variables and configuration
- Validate database connections and migrations
- Ensure all required services are running

## Documentation Standards

All completed features must include:
- Comprehensive inline code documentation
- API endpoint documentation with examples
- Architecture decisions and data flow diagrams
- Integration guides for external systems
- Performance considerations and optimization notes

## Security Requirements

- No secrets or credentials in code or logs
- Input validation and sanitization
- Proper error handling without information leakage
- Audit logging for security-relevant operations
- Compliance with backend-only data policy

---

**Created**: 2025-09-18  
**Purpose**: Ensure consistent quality standards across all development work  
**Enforcement**: Mandatory validation before task completion