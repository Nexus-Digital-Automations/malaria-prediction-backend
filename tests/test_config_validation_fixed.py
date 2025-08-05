"""
Comprehensive tests for config_validation.py to achieve high coverage.

This module tests the configuration validation system that checks all external
dependencies, validates settings, and performs health checks critical for
system deployment and runtime reliability.
"""

import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from sqlalchemy.exc import OperationalError

# Add src to path before importing modules
sys.path.insert(0, "src")

from malaria_predictor.config import Settings
from malaria_predictor.config_validation import (
    ConfigurationError,
    ConfigValidator,
    HealthCheckError,
)


class TestConfigValidator:
    """Test ConfigValidator class to achieve comprehensive coverage."""

    @pytest.fixture
    def mock_settings(self):
        """Create a properly structured mock Settings object."""
        settings = Mock(spec=Settings)
        settings.environment = "testing"
        settings.debug = False
        settings.testing = True
        settings.workers = 4
        settings.is_production.return_value = False
        settings.get_database_url.return_value = (
            "postgresql://user:pass@localhost:5432/test_db"
        )

        # Also handle the sync parameter
        def mock_get_database_url(sync=False):
            return "postgresql://user:pass@localhost:5432/test_db"

        settings.get_database_url.side_effect = mock_get_database_url
        settings.get_redis_url.return_value = "redis://localhost:6379/0"

        # Mock nested settings objects with all required attributes
        security_mock = Mock()
        security_mock.secret_key = "test_secret_key_long_enough_for_validation"
        security_mock.jwt_expiration_hours = 24
        security_mock.rate_limit_per_minute = 100
        security_mock.cors_origins = ["https://example.com"]
        settings.security = security_mock

        database_mock = Mock()
        database_mock.url = "postgresql://user:pass@localhost:5432/test_db"
        database_mock.pool_size = 20
        settings.database = database_mock

        redis_mock = Mock()
        redis_mock.url = "redis://localhost:6379/0"
        redis_mock.max_connections = 50
        settings.redis = redis_mock

        ml_models_mock = Mock()
        ml_models_mock.storage_path = Path("/tmp/test_models")
        ml_models_mock.max_memory_usage = 4096
        settings.ml_models = ml_models_mock

        data_mock = Mock()
        data_mock.directory = Path("/tmp/test_data")
        settings.data = data_mock

        external_apis_mock = Mock()
        external_apis_mock.era5_api_url = "https://api.era5.test"
        external_apis_mock.chirps_api_endpoint = "https://api.chirps.test"
        external_apis_mock.modis_api_url = "https://api.modis.test"
        external_apis_mock.worldpop_api_endpoint = "https://api.worldpop.test"
        external_apis_mock.map_api_endpoint = "https://api.map.test"
        settings.external_apis = external_apis_mock

        return settings

    @pytest.fixture
    def validator(self, mock_settings):
        """Create ConfigValidator instance."""
        return ConfigValidator(mock_settings)

    def test_config_validator_initialization(self, mock_settings):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator(mock_settings)

        assert validator.settings == mock_settings
        assert validator.validation_results == {}
        assert validator.health_check_results == {}

    def test_validate_all_success(self, validator):
        """Test successful validation of all configuration components."""
        with (
            patch.object(
                validator, "_validate_configuration_original"
            ) as mock_validate_config,
            patch.object(validator, "_validate_secrets") as mock_validate_secrets,
            patch("asyncio.run") as mock_asyncio_run,
            patch.object(
                validator, "_run_health_checks", new_callable=AsyncMock
            ) as mock_health_checks,
        ):
            # Mock validation results
            mock_validate_config.return_value = {
                "environment": {"status": "pass"},
                "paths": {"status": "pass"},
                "urls": {"status": "pass"},
            }
            mock_validate_secrets.return_value = {"status": "pass"}
            mock_health_checks.return_value = {"database": {"status": "pass"}}
            mock_asyncio_run.return_value = {"database": {"status": "pass"}}

            result = validator.validate_all()

            assert "timestamp" in result
            assert result["environment"] == "testing"
            assert "validation_summary" in result
            assert "configuration_validation" in result
            assert "secrets_validation" in result
            assert "health_checks" in result

            # Verify validation methods were called
            mock_validate_config.assert_called_once()
            mock_validate_secrets.assert_called_once()
            mock_asyncio_run.assert_called_once()

    def test_validate_all_without_health_checks(self, validator):
        """Test validation without health checks."""
        with (
            patch.object(
                validator, "_validate_configuration_original"
            ) as mock_validate_config,
            patch.object(validator, "_validate_secrets") as mock_validate_secrets,
        ):
            mock_validate_config.return_value = {"status": "pass"}
            mock_validate_secrets.return_value = {"status": "pass"}

            result = validator.validate_all(include_health_checks=False)

            assert result["health_checks"] is None

    def test_validate_environment_valid(self, validator):
        """Test environment validation with valid environment."""
        result = validator._validate_environment()

        assert "environment_name" in result
        assert result["environment_name"]["status"] == "pass"
        assert result["environment_name"]["value"] == "testing"

    def test_validate_environment_invalid(self, validator):
        """Test environment validation with invalid environment."""
        validator.settings.environment = "invalid_env"

        result = validator._validate_environment()

        assert result["environment_name"]["status"] == "fail"
        assert result["environment_name"]["value"] == "invalid_env"

    def test_validate_environment_production_debug_disabled(self, validator):
        """Test environment validation for production with debug disabled."""
        validator.settings.environment = "production"
        validator.settings.is_production.return_value = True
        validator.settings.debug = False

        result = validator._validate_environment()

        assert "debug_disabled" in result
        assert result["debug_disabled"]["status"] == "pass"

    def test_validate_environment_production_debug_enabled(self, validator):
        """Test environment validation for production with debug enabled."""
        validator.settings.environment = "production"
        validator.settings.is_production.return_value = True
        validator.settings.debug = True

        result = validator._validate_environment()

        assert "debug_disabled" in result
        assert result["debug_disabled"]["status"] == "fail"

    def test_validate_paths_success(self, validator):
        """Test path validation with existing paths."""
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "write_text"),
            patch.object(Path, "unlink"),
        ):
            result = validator._validate_paths()

            assert "model_storage" in result
            assert "data_directory" in result
            assert result["model_storage"]["status"] == "pass"
            assert result["data_directory"]["status"] == "pass"

    def test_validate_paths_missing_paths(self, validator):
        """Test path validation with missing paths."""
        with patch.object(Path, "exists", return_value=False):
            result = validator._validate_paths()

            assert result["model_storage"]["status"] == "warning"
            assert result["data_directory"]["status"] == "warning"

    def test_validate_urls_success(self, validator):
        """Test URL validation with valid URLs."""
        result = validator._validate_urls()

        assert "database_url" in result
        assert "redis_url" in result
        assert result["database_url"]["status"] == "pass"
        assert result["redis_url"]["status"] == "pass"

    def test_validate_constraints_success(self, validator):
        """Test constraints validation with valid values."""
        result = validator._validate_constraints()

        assert "database_pool_size" in result
        assert "redis_connections" in result
        assert "model_memory" in result
        assert result["database_pool_size"]["status"] == "pass"
        assert result["redis_connections"]["status"] == "pass"
        assert result["model_memory"]["status"] == "pass"

    def test_validate_security_success(self, validator):
        """Test security validation with valid settings."""
        result = validator._validate_security()

        assert "secret_key_strength" in result
        assert "jwt_expiration" in result
        assert "rate_limiting" in result
        assert result["secret_key_strength"]["status"] == "pass"
        assert result["jwt_expiration"]["status"] == "pass"
        assert result["rate_limiting"]["status"] == "pass"

    def test_validate_security_weak_secret_key(self, validator):
        """Test security validation with weak secret key."""
        validator.settings.security.secret_key = "weak"

        result = validator._validate_security()

        assert result["secret_key_strength"]["status"] == "fail"

    def test_validate_secrets_success_production(self, validator):
        """Test secrets validation in production environment."""
        validator.settings.is_production.return_value = True

        with patch(
            "malaria_predictor.config_validation.validate_production_secrets"
        ) as mock_validate:
            mock_validate.return_value = {
                "status": "pass",
                "message": "All secrets valid",
            }

            result = validator._validate_secrets()

            assert result["status"] == "pass"
            mock_validate.assert_called_once()

    def test_validate_secrets_skipped_non_production(self, validator):
        """Test secrets validation in non-production environment."""
        result = validator._validate_secrets()

        assert result["status"] == "skipped"
        assert "non-production environment" in result["message"]

    def test_validate_secrets_exception(self, validator):
        """Test secrets validation with exception."""
        validator.settings.is_production.return_value = True

        with patch(
            "malaria_predictor.config_validation.validate_production_secrets"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Validation error")

            result = validator._validate_secrets()

            assert result["status"] == "fail"
            assert "Validation error" in result["message"]

    @pytest.mark.asyncio
    async def test_run_health_checks_success(self, validator):
        """Test health checks with all services healthy."""
        with (
            patch.object(
                validator, "_check_database_health", new_callable=AsyncMock
            ) as mock_db,
            patch.object(
                validator, "_check_redis_health", new_callable=AsyncMock
            ) as mock_redis,
            patch.object(
                validator, "_check_external_apis_health", new_callable=AsyncMock
            ) as mock_apis,
        ):
            mock_db.return_value = {"status": "pass"}
            mock_redis.return_value = {"status": "pass"}
            mock_apis.return_value = {"status": "pass"}

            result = await validator._run_health_checks()

            assert "database" in result
            assert "redis" in result
            assert "external_apis" in result

            mock_db.assert_called_once()
            mock_redis.assert_called_once()
            mock_apis.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health_success(self, validator):
        """Test successful database health check."""
        mock_engine = Mock()
        mock_connection = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (1,)
        mock_connection.execute.return_value = mock_result

        # Mock TimescaleDB extension check
        timescale_result = Mock()
        timescale_result.fetchone.return_value = ("timescaledb",)
        mock_connection.execute.side_effect = [mock_result, timescale_result]

        # Properly mock the context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_connection)
        mock_context.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_context

        with patch(
            "malaria_predictor.config_validation.create_engine",
            return_value=mock_engine,
        ):
            result = await validator._check_database_health()

            assert result["status"] == "pass"
            assert "response_time_ms" in result
            assert "timescaledb_available" in result

    @pytest.mark.asyncio
    async def test_check_database_health_failure(self, validator):
        """Test database health check failure."""
        with patch(
            "malaria_predictor.config_validation.create_engine",
            side_effect=OperationalError("", "", ""),
        ):
            result = await validator._check_database_health()

            assert result["status"] == "fail"
            assert "Database connection failed" in result["message"]

    @pytest.mark.asyncio
    async def test_check_redis_health_success(self, validator):
        """Test successful Redis health check."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_client.get.return_value = b"test_value"
        mock_client.delete.return_value = 1

        with patch("redis.asyncio.from_url", return_value=mock_client):
            result = await validator._check_redis_health()

            assert result["status"] == "pass"
            assert "response_time_ms" in result
            assert result["operations_successful"] is True
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_redis_health_failure(self, validator):
        """Test Redis health check failure."""
        with patch(
            "redis.asyncio.from_url", side_effect=Exception("Connection failed")
        ):
            result = await validator._check_redis_health()

            assert result["status"] == "fail"
            assert "Connection failed" in result["message"]

    @pytest.mark.asyncio
    async def test_check_external_apis_health_success(self, validator):
        """Test successful external APIs health check."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.head.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await validator._check_external_apis_health()

            # Check that all expected APIs are tested
            expected_apis = ["era5", "chirps", "modis", "worldpop", "map"]
            for api in expected_apis:
                assert api in result
                assert result[api]["status"] == "pass"

    @pytest.mark.asyncio
    async def test_check_external_apis_health_timeout(self, validator):
        """Test external APIs health check with timeout."""
        mock_client = AsyncMock()
        mock_client.head.side_effect = httpx.TimeoutException("Request timeout")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await validator._check_external_apis_health()

            # All APIs should show warning status due to timeout
            for api_result in result.values():
                assert api_result["status"] == "warning"
                assert "timed out" in api_result["message"]

    def test_update_summary(self, validator):
        """Test summary update functionality."""
        summary = {"passed": 0, "failed": 0, "warnings": 0}

        # Test with passing results
        results = {"test1": {"status": "pass"}, "test2": {"status": "pass"}}
        validator._update_summary(summary, results)

        assert summary["passed"] == 2
        assert summary["failed"] == 0

    def test_update_summary_with_failures_and_warnings(self, validator):
        """Test summary update with mixed results."""
        summary = {"passed": 0, "failed": 0, "warnings": 0}

        # Test with mixed results
        results = {
            "test1": {"status": "pass"},
            "test2": {"status": "fail"},
            "test3": {"status": "warning"},
        }
        validator._update_summary(summary, results)

        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["warnings"] == 1

    def test_update_summary_nested_results(self, validator):
        """Test summary update with nested results structure."""
        summary = {"passed": 0, "failed": 0, "warnings": 0}

        # Test with nested results structure
        results = {
            "category1": {"test1": {"status": "pass"}, "test2": {"status": "fail"}},
            "category2": {"test3": {"status": "pass"}},
        }
        validator._update_summary(summary, results)

        assert summary["passed"] == 2
        assert summary["failed"] == 1


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_creation(self):
        """Test creating ConfigurationError instance."""
        error = ConfigurationError("Test error message")

        assert str(error) == "Test error message"
        assert error.args[0] == "Test error message"


class TestHealthCheckError:
    """Test HealthCheckError exception."""

    def test_health_check_error_creation(self):
        """Test creating HealthCheckError instance."""
        error = HealthCheckError("Health check failed")

        assert str(error) == "Health check failed"
        assert error.args[0] == "Health check failed"


class TestConfigValidationCLI:
    """Test CLI validation function."""

    def test_validate_configuration_cli_success(self):
        """Test CLI validation with successful configuration."""
        mock_settings = Mock()

        with (
            patch(
                "malaria_predictor.config_validation.ConfigValidator"
            ) as mock_validator_class,
            patch("builtins.print") as mock_print,
        ):
            mock_validator = Mock()
            mock_validator.validate_all.return_value = {
                "timestamp": time.time(),
                "environment": "testing",
                "validation_summary": {"passed": 5, "failed": 0, "warnings": 0},
            }
            mock_validator_class.return_value = mock_validator

            from malaria_predictor.config_validation import validate_configuration_cli

            result = validate_configuration_cli(mock_settings)

            assert result is True
            mock_print.assert_called()

    def test_validate_configuration_cli_with_failures(self):
        """Test CLI validation with failures."""
        mock_settings = Mock()

        with (
            patch(
                "malaria_predictor.config_validation.ConfigValidator"
            ) as mock_validator_class,
            patch("builtins.print") as mock_print,
        ):
            mock_validator = Mock()
            mock_validator.validate_all.return_value = {
                "timestamp": time.time(),
                "environment": "testing",
                "validation_summary": {"passed": 3, "failed": 2, "warnings": 1},
            }
            mock_validator_class.return_value = mock_validator

            from malaria_predictor.config_validation import validate_configuration_cli

            result = validate_configuration_cli(mock_settings)

            assert result is False
            mock_print.assert_called()


class TestHealthCheckEndpoint:
    """Test health check endpoint creation."""

    def test_create_health_check_endpoint(self):
        """Test creating health check endpoint."""
        mock_settings = Mock()

        from malaria_predictor.config_validation import create_health_check_endpoint

        health_check_func = create_health_check_endpoint(mock_settings)

        assert callable(health_check_func)

    @pytest.mark.asyncio
    async def test_health_check_endpoint_healthy(self):
        """Test health check endpoint with healthy system."""
        mock_settings = Mock()

        with patch(
            "malaria_predictor.config_validation.ConfigValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_all.return_value = {
                "validation_summary": {"passed": 5, "failed": 0, "warnings": 0}
            }
            mock_validator_class.return_value = mock_validator

            from malaria_predictor.config_validation import create_health_check_endpoint

            health_check_func = create_health_check_endpoint(mock_settings)

            result = await health_check_func()

            assert result["status"] == "healthy"
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_health_check_endpoint_unhealthy(self):
        """Test health check endpoint with unhealthy system."""
        mock_settings = Mock()

        with patch(
            "malaria_predictor.config_validation.ConfigValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_all.return_value = {
                "validation_summary": {"passed": 3, "failed": 2, "warnings": 0}
            }
            mock_validator_class.return_value = mock_validator

            from malaria_predictor.config_validation import create_health_check_endpoint

            health_check_func = create_health_check_endpoint(mock_settings)

            result = await health_check_func()

            assert result["status"] == "unhealthy"
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_health_check_endpoint_exception(self):
        """Test health check endpoint with exception."""
        mock_settings = Mock()

        with patch(
            "malaria_predictor.config_validation.ConfigValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_all.side_effect = Exception("Validation failed")
            mock_validator_class.return_value = mock_validator

            from malaria_predictor.config_validation import create_health_check_endpoint

            health_check_func = create_health_check_endpoint(mock_settings)

            result = await health_check_func()

            assert result["status"] == "unhealthy"
            assert "error" in result
