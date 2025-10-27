# Contributing to Malaria Prediction Backend

Thank you for your interest in contributing to the Malaria Prediction Backend! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a professional code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Prioritize the project's health and sustainability
- Maintain confidentiality regarding security vulnerabilities

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **uv**: Modern Python package manager ([installation](https://github.com/astral-sh/uv))
- **Docker**: For containerized development
- **Git**: Version control

### Initial Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/malaria-prediction-backend.git
cd malaria-prediction-backend

# 2. Install dependencies
uv sync --dev

# 3. Set up pre-commit hooks
uv run pre-commit install

# 4. Copy environment configuration
cp .env.development .env

# 5. Start development services
docker-compose up -d postgres redis

# 6. Run tests to verify setup
uv run pytest
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch Naming**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Follow these principles:
- Write clear, self-documenting code
- Add comprehensive type annotations
- Include docstrings for all public functions/classes
- Follow existing code patterns and architecture

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=html

# Run specific test file
uv run pytest tests/test_your_module.py

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/
```

### 4. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

git commit -m "feat(api): add batch prediction endpoint"
git commit -m "fix(ml): resolve LSTM training instability"
git commit -m "docs(api): update authentication guide"
git commit -m "test(services): add ERA5 client tests"
```

**Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/improvements
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## Code Quality Standards

### Python Style

We use **Ruff** for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Safety

All code must have **type annotations** and pass **mypy** strict mode:

```python
# ✅ Good
def predict_risk(
    features: np.ndarray,
    model_type: str = "ensemble"
) -> tuple[float, float]:
    """
    Predict malaria risk from environmental features.

    Args:
        features: Environmental feature array
        model_type: Model to use for prediction

    Returns:
        Tuple of (risk_score, uncertainty)
    """
    ...

# ❌ Bad - missing types
def predict_risk(features, model_type="ensemble"):
    ...
```

### Code Documentation

All public functions and classes require docstrings:

```python
def calculate_risk_level(risk_score: float) -> RiskLevel:
    """
    Convert continuous risk score to categorical level.

    Args:
        risk_score: Normalized risk score [0.0, 1.0]

    Returns:
        Categorical risk level (LOW, MEDIUM, HIGH, VERY_HIGH)

    Raises:
        ValueError: If risk_score is outside [0.0, 1.0]

    Examples:
        >>> calculate_risk_level(0.15)
        RiskLevel.LOW
        >>> calculate_risk_level(0.85)
        RiskLevel.VERY_HIGH
    """
    if not 0.0 <= risk_score <= 1.0:
        raise ValueError(f"Risk score must be in [0, 1], got {risk_score}")

    if risk_score < 0.25:
        return RiskLevel.LOW
    elif risk_score < 0.5:
        return RiskLevel.MEDIUM
    elif risk_score < 0.75:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH
```

### Logging

Use comprehensive logging:

```python
import logging

logger = logging.getLogger(__name__)

def fetch_climate_data(location: Location, date: datetime) -> ClimateData:
    """Fetch climate data for location and date."""
    logger.info(
        "Fetching climate data",
        extra={
            "location": location.to_dict(),
            "date": date.isoformat(),
            "function": "fetch_climate_data"
        }
    )

    try:
        data = era5_client.get_data(location, date)
        logger.debug(
            "Climate data fetched successfully",
            extra={"data_points": len(data), "source": "ERA5"}
        )
        return data
    except Exception as e:
        logger.error(
            "Failed to fetch climate data",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "location": location.to_dict()
            },
            exc_info=True
        )
        raise
```

## Testing Requirements

### Coverage Target

**95%+ test coverage** is required for all new code.

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── e2e/              # End-to-end tests
├── performance/       # Performance benchmarks
└── fixtures/         # Test data and mocks
```

### Writing Tests

```python
import pytest
from src.malaria_predictor.ml.models import LSTMPredictor


class TestLSTMPredictor:
    """Tests for LSTM prediction model."""

    @pytest.fixture
    def model(self):
        """Create LSTM model instance."""
        return LSTMPredictor(input_dim=15, hidden_dim=128)

    @pytest.fixture
    def sample_data(self):
        """Create sample environmental data."""
        return np.random.randn(32, 90, 15)  # (batch, sequence, features)

    def test_model_initialization(self, model):
        """Test model initializes with correct architecture."""
        assert model.input_dim == 15
        assert model.hidden_dim == 128
        assert model.num_layers == 3

    def test_forward_pass(self, model, sample_data):
        """Test model forward pass produces valid output."""
        output = model(sample_data)

        assert output.shape == (32, 1)  # (batch, output_dim)
        assert torch.all((output >= 0) & (output <= 1))  # Sigmoid output

    def test_prediction_consistency(self, model, sample_data):
        """Test model produces consistent predictions."""
        model.eval()

        with torch.no_grad():
            output1 = model(sample_data)
            output2 = model(sample_data)

        torch.testing.assert_close(output1, output2)

    def test_handles_missing_data(self, model):
        """Test model gracefully handles missing data."""
        data_with_nan = np.random.randn(32, 90, 15)
        data_with_nan[0, 10:20, :] = np.nan

        with pytest.raises(ValueError, match="contains NaN"):
            model(torch.from_numpy(data_with_nan))
```

### Running Tests

```bash
# All tests with coverage
uv run pytest --cov --cov-report=html

# Specific test category
uv run pytest tests/unit/
uv run pytest tests/integration/

# Specific test file or function
uv run pytest tests/unit/test_models.py
uv run pytest tests/unit/test_models.py::TestLSTMPredictor::test_forward_pass

# Performance benchmarks
uv run pytest tests/performance/ --benchmark-only
```

## Documentation

### When to Update Documentation

Update documentation when you:
- Add new API endpoints
- Create new features
- Change existing behavior
- Add new data sources
- Modify deployment procedures

### Documentation Locations

- **API Documentation**: `docs/api/`
- **ML Documentation**: `docs/ml/`
- **Data Sources**: `docs/data-sources/`
- **Deployment**: `docs/deployment/`
- **Code Documentation**: Inline docstrings

### Documentation Style

Follow the existing documentation style:
- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Cross-reference related documentation

## Submitting Changes

### Pull Request Process

1. **Update Documentation**: Ensure all docs are current
2. **Run All Tests**: `uv run pytest --cov`
3. **Run Linting**: `uv run ruff check . && uv run mypy src/`
4. **Push Changes**: `git push origin feature/your-feature-name`
5. **Create Pull Request**: Use the PR template

### Pull Request Template

```markdown
## Description

Brief description of changes and motivation.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass
- [ ] Coverage >= 95%

## Checklist

- [ ] Code follows project style guide
- [ ] Type annotations added
- [ ] Docstrings updated
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] No security vulnerabilities introduced

## Related Issues

Closes #123
```

### Code Review Process

All pull requests require:
1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one approving review
3. **Documentation Review**: Docs updated appropriately
4. **Testing**: 95%+ coverage maintained

### Review Criteria

Reviewers will check:
- Code quality and style
- Test coverage and quality
- Documentation completeness
- Security considerations
- Performance implications
- API compatibility

## Security

### Reporting Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Instead:
1. Email: security@malaria-prediction.example.com
2. Include: Description, impact, reproduction steps
3. Wait for acknowledgment before public disclosure

### Security Best Practices

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Follow OWASP security guidelines
- Run security scans: `uv run bandit -r src/`

## Questions?

- **Documentation**: Check [docs/README.md](./docs/README.md)
- **API Questions**: See [docs/api/](./docs/api/)
- **ML Questions**: See [docs/ml/](./docs/ml/)
- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and feature requests

---

## Thank You!

Your contributions make this project better for everyone working on malaria prediction and prevention.

**Together, we're making malaria prediction accessible through advanced AI and comprehensive environmental data integration. 🌍**
