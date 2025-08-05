"""
Comprehensive tests for config_validation.py to achieve 100% coverage.

This module tests the configuration validation system that checks all external
dependencies, validates settings, and performs health checks critical for
system deployment and runtime reliability.
"""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

# Add src to path before importing modules
sys.path.insert(0, "src")

from malaria_predictor.config_validation import (
    ConfigValidationError,
    ConfigValidator,
    ExternalServiceStatus,
    HealthCheckResult,
)


class TestConfigValidator:
    """Test ConfigValidator class to achieve full coverage."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.database_url = "postgresql+asyncpg://user:pass@localhost:5432/test_db"
        config.redis_url = "redis://localhost:6379/0"
        config.era5_api_key = "test_era5_key"
        config.modis_api_key = "test_modis_key"
        config.chirps_api_endpoint = "https://api.chirps.test"
        config.worldpop_api_endpoint = "https://api.worldpop.test"
        config.map_api_endpoint = "https://api.map.test"
        config.data_path = "/tmp/test_data"
        config.model_path = "/tmp/test_models"
        config.log_level = "INFO"
        config.debug = False
        config.testing = True
        return config

    @pytest.fixture
    def validator(self, mock_config):
        """Create ConfigValidator instance."""
        return ConfigValidator(mock_config)

    def test_config_validator_initialization(self, mock_config):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator(mock_config)

        assert validator.config == mock_config
        assert validator.results == []
        assert validator.overall_status == "unknown"

    @pytest.mark.asyncio
    async def test_validate_all_success(self, validator):
        """Test successful validation of all configuration components."""
        with (
            patch.object(
                validator, "_validate_configuration", return_value=True
            ) as mock_validate_config,
            patch.object(
                validator, "_check_database_health", new_callable=AsyncMock
            ) as mock_db_health,
            patch.object(
                validator, "_check_redis_health", new_callable=AsyncMock
            ) as mock_redis_health,
            patch.object(
                validator, "_check_external_apis_health", new_callable=AsyncMock
            ) as mock_api_health,
            patch.object(
                validator, "_check_file_system_access", return_value=True
            ) as mock_fs_check,
            patch.object(
                validator, "_validate_model_requirements", return_value=True
            ) as mock_model_check,
        ):
            # Mock all health checks to pass
            mock_db_health.return_value = None
            mock_redis_health.return_value = None
            mock_api_health.return_value = None

            result = await validator.validate_all()

            assert result.overall_status == "healthy"
            assert result.passed_checks > 0
            assert result.failed_checks == 0
            assert len(result.results) > 0

            # Verify all validation methods were called
            mock_validate_config.assert_called_once()
            mock_db_health.assert_called_once()
            mock_redis_health.assert_called_once()
            mock_api_health.assert_called_once()
            mock_fs_check.assert_called_once()
            mock_model_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_all_with_failures(self, validator):
        """Test validation with some components failing."""
        with (
            patch.object(validator, "_validate_configuration", return_value=True),
            patch.object(
                validator, "_check_database_health", new_callable=AsyncMock
            ) as mock_db_health,
            patch.object(
                validator, "_check_redis_health", new_callable=AsyncMock
            ) as mock_redis_health,
            patch.object(
                validator, "_check_external_apis_health", new_callable=AsyncMock
            ) as mock_api_health,
            patch.object(validator, "_check_file_system_access", return_value=True),
            patch.object(validator, "_validate_model_requirements", return_value=True),
        ):
            # Mock database health check to fail
            mock_db_health.side_effect = Exception("Database connection failed")
            mock_redis_health.return_value = None
            mock_api_health.return_value = None

            result = await validator.validate_all()

            assert result.overall_status == "unhealthy"
            assert result.failed_checks > 0
            assert len(result.results) > 0

            # Check that failure was recorded
            db_result = next(
                (r for r in result.results if r.component == "database"), None
            )
            assert db_result is not None
            assert db_result.status == "failed"
            assert "Database connection failed" in db_result.error

    def test_validate_configuration_success(self, validator):
        """Test successful configuration validation."""
        result = validator._validate_configuration()

        assert result is True

        # Check that a result was added
        config_result = next(
            (r for r in validator.results if r.component == "configuration"), None
        )
        assert config_result is not None
        assert config_result.status == "passed"

    def test_validate_configuration_missing_database_url(self, validator):
        """Test configuration validation with missing database URL."""
        validator.config.database_url = None

        result = validator._validate_configuration()

        assert result is False

        # Check that failure was recorded
        config_result = next(
            (r for r in validator.results if r.component == "configuration"), None
        )
        assert config_result is not None
        assert config_result.status == "failed"
        assert "Database URL is required" in config_result.error

    def test_validate_configuration_missing_redis_url(self, validator):
        """Test configuration validation with missing Redis URL."""
        validator.config.redis_url = None

        result = validator._validate_configuration()

        assert result is False

        # Check that failure was recorded
        config_result = next(
            (r for r in validator.results if r.component == "configuration"), None
        )
        assert config_result is not None
        assert config_result.status == "failed"
        assert "Redis URL is required" in config_result.error

    def test_validate_configuration_missing_api_keys(self, validator):
        """Test configuration validation with missing API keys."""
        validator.config.era5_api_key = None
        validator.config.modis_api_key = None

        result = validator._validate_configuration()

        assert result is False

        # Check that failure was recorded
        config_result = next(
            (r for r in validator.results if r.component == "configuration"), None
        )
        assert config_result is not None
        assert config_result.status == "failed"
        assert "ERA5 API key is required" in config_result.error

    @pytest.mark.asyncio
    async def test_check_database_health_success(self, validator):
        """Test successful database health check."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_connection = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_connection.execute.return_value = mock_result
        mock_engine.begin.return_value.__aenter__.return_value = mock_connection

        with patch(
            "malaria_predictor.config_validation.create_async_engine",
            return_value=mock_engine,
        ):
            await validator._check_database_health()

            # Check that success was recorded
            db_result = next(
                (r for r in validator.results if r.component == "database"), None
            )
            assert db_result is not None
            assert db_result.status == "passed"

    @pytest.mark.asyncio
    async def test_check_database_health_connection_failure(self, validator):
        """Test database health check with connection failure."""
        with patch(
            "malaria_predictor.config_validation.create_async_engine"
        ) as mock_create_engine:
            mock_create_engine.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await validator._check_database_health()

    @pytest.mark.asyncio
    async def test_check_database_health_query_failure(self, validator):
        """Test database health check with query execution failure."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = Exception("Query failed")
        mock_engine.begin.return_value.__aenter__.return_value = mock_connection

        with patch(
            "malaria_predictor.config_validation.create_async_engine",
            return_value=mock_engine,
        ):
            with pytest.raises(Exception, match="Query failed"):
                await validator._check_database_health()

    @pytest.mark.asyncio
    async def test_check_redis_health_success(self, validator):
        """Test successful Redis health check."""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        with patch("aioredis.from_url", return_value=mock_redis):
            await validator._check_redis_health()

            # Check that success was recorded
            redis_result = next(
                (r for r in validator.results if r.component == "redis"), None
            )
            assert redis_result is not None
            assert redis_result.status == "passed"

            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_redis_health_connection_failure(self, validator):
        """Test Redis health check with connection failure."""
        with patch("aioredis.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Redis connection failed")

            with pytest.raises(Exception, match="Redis connection failed"):
                await validator._check_redis_health()

    @pytest.mark.asyncio
    async def test_check_redis_health_ping_failure(self, validator):
        """Test Redis health check with ping failure."""
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Ping failed")

        with patch("aioredis.from_url", return_value=mock_redis):
            with pytest.raises(Exception, match="Ping failed"):
                await validator._check_redis_health()

    @pytest.mark.asyncio
    async def test_check_external_apis_health_success(self, validator):
        """Test successful external APIs health check."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            await validator._check_external_apis_health()

            # Check that API health checks were recorded
            api_results = [r for r in validator.results if "api" in r.component.lower()]
            assert len(api_results) > 0

            # All API health checks should pass
            for result in api_results:
                assert result.status == "passed"

    @pytest.mark.asyncio
    async def test_check_external_apis_health_era5_failure(self, validator):
        """Test external APIs health check with ERA5 API failure."""
        mock_response = Mock()
        mock_response.status = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            await validator._check_external_apis_health()

            # Check that ERA5 API failure was recorded
            era5_result = next(
                (r for r in validator.results if "era5" in r.component.lower()), None
            )
            assert era5_result is not None
            assert era5_result.status == "failed"

    @pytest.mark.asyncio
    async def test_check_external_apis_health_network_error(self, validator):
        """Test external APIs health check with network error."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Network error")
            mock_session_class.return_value.__aenter__.return_value = mock_session

            await validator._check_external_apis_health()

            # Check that network errors were recorded for all APIs
            api_results = [r for r in validator.results if "api" in r.component.lower()]
            assert len(api_results) > 0

            for result in api_results:
                assert result.status == "failed"
                assert "Network error" in result.error

    def test_check_file_system_access_success(self, validator):
        """Test successful file system access check."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("os.access", return_value=True),
        ):
            result = validator._check_file_system_access()

            assert result is True

            # Check that success was recorded
            fs_result = next(
                (r for r in validator.results if r.component == "filesystem"), None
            )
            assert fs_result is not None
            assert fs_result.status == "passed"

    def test_check_file_system_access_data_path_missing(self, validator):
        """Test file system access check with missing data path."""
        with patch("pathlib.Path.exists", return_value=False):
            result = validator._check_file_system_access()

            assert result is False

            # Check that failure was recorded
            fs_result = next(
                (r for r in validator.results if r.component == "filesystem"), None
            )
            assert fs_result is not None
            assert fs_result.status == "failed"
            assert "Data path does not exist" in fs_result.error

    def test_check_file_system_access_permission_denied(self, validator):
        """Test file system access check with permission denied."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("os.access", return_value=False),
        ):
            result = validator._check_file_system_access()

            assert result is False

            # Check that failure was recorded
            fs_result = next(
                (r for r in validator.results if r.component == "filesystem"), None
            )
            assert fs_result is not None
            assert fs_result.status == "failed"
            assert "Data path is not writable" in fs_result.error

    def test_validate_model_requirements_success(self, validator):
        """Test successful model requirements validation."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
        ):
            result = validator._validate_model_requirements()

            assert result is True

            # Check that success was recorded
            model_result = next(
                (r for r in validator.results if r.component == "models"), None
            )
            assert model_result is not None
            assert model_result.status == "passed"

    def test_validate_model_requirements_path_missing(self, validator):
        """Test model requirements validation with missing model path."""
        with patch("pathlib.Path.exists", return_value=False):
            result = validator._validate_model_requirements()

            assert result is False

            # Check that failure was recorded
            model_result = next(
                (r for r in validator.results if r.component == "models"), None
            )
            assert model_result is not None
            assert model_result.status == "failed"
            assert "Model path does not exist" in model_result.error

    def test_add_result(self, validator):
        """Test adding validation results."""
        validator._add_result(
            "test_component", "passed", "Test success", response_time=0.1
        )

        assert len(validator.results) == 1
        result = validator.results[0]
        assert result.component == "test_component"
        assert result.status == "passed"
        assert result.message == "Test success"
        assert result.response_time == 0.1
        assert result.timestamp is not None

    def test_add_result_with_error(self, validator):
        """Test adding validation result with error."""
        validator._add_result(
            "test_component", "failed", "Test failed", error="Test error"
        )

        assert len(validator.results) == 1
        result = validator.results[0]
        assert result.component == "test_component"
        assert result.status == "failed"
        assert result.message == "Test failed"
        assert result.error == "Test error"

    def test_get_overall_status_all_passed(self, validator):
        """Test overall status calculation when all checks pass."""
        validator._add_result("test1", "passed", "Success")
        validator._add_result("test2", "passed", "Success")

        status = validator._get_overall_status()
        assert status == "healthy"

    def test_get_overall_status_some_failed(self, validator):
        """Test overall status calculation when some checks fail."""
        validator._add_result("test1", "passed", "Success")
        validator._add_result("test2", "failed", "Failed")

        status = validator._get_overall_status()
        assert status == "unhealthy"

    def test_get_overall_status_no_results(self, validator):
        """Test overall status calculation with no results."""
        status = validator._get_overall_status()
        assert status == "unknown"


class TestHealthCheckResult:
    """Test HealthCheckResult data class."""

    def test_health_check_result_creation(self):
        """Test creating HealthCheckResult instance."""
        result = HealthCheckResult(
            component="test",
            status="passed",
            message="Test message",
            timestamp=datetime.now(),
            response_time=0.1,
            error="Test error",
        )

        assert result.component == "test"
        assert result.status == "passed"
        assert result.message == "Test message"
        assert result.response_time == 0.1
        assert result.error == "Test error"
        assert result.timestamp is not None


class TestExternalServiceStatus:
    """Test ExternalServiceStatus data class."""

    def test_external_service_status_creation(self):
        """Test creating ExternalServiceStatus instance."""
        results = [
            HealthCheckResult("test1", "passed", "Success", datetime.now()),
            HealthCheckResult(
                "test2", "failed", "Failed", datetime.now(), error="Error"
            ),
        ]

        status = ExternalServiceStatus(
            overall_status="unhealthy",
            passed_checks=1,
            failed_checks=1,
            total_checks=2,
            results=results,
            validation_time=1.5,
        )

        assert status.overall_status == "unhealthy"
        assert status.passed_checks == 1
        assert status.failed_checks == 1
        assert status.total_checks == 2
        assert len(status.results) == 2
        assert status.validation_time == 1.5


class TestConfigValidationError:
    """Test ConfigValidationError exception."""

    def test_config_validation_error_creation(self):
        """Test creating ConfigValidationError instance."""
        error = ConfigValidationError("Test error message")

        assert str(error) == "Test error message"
        assert error.args[0] == "Test error message"

    def test_config_validation_error_with_cause(self):
        """Test creating ConfigValidationError with cause."""
        cause = ValueError("Original error")
        error = ConfigValidationError("Configuration failed", cause)

        assert str(error) == "Configuration failed"
        assert error.__cause__ == cause
