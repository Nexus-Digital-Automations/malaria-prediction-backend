"""
Focused security module tests to achieve 100% coverage.

This test file specifically targets uncovered lines in:
- src/malaria_predictor/api/auth.py (missing: 53, 96-101, 119-131, 170-175, 179-228, 231, 264-269, 273-334, 360-376, 381-389, 396, 417-425, 481-482)
- src/malaria_predictor/database/repositories.py (missing: 60-61, 101-121, 137-148, 162-172, 230-231, 283-298, 330-352, 370-380, 400-413)
- src/malaria_predictor/database/session.py (missing: 57-81, 92-103, 118-128, 173-192, 213, 263-302)
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path before importing modules
sys.path.insert(0, "src")


class TestAuthModuleCoverage:
    """Test auth.py module to achieve 100% coverage."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def mock_user_data(self):
        """Create mock user data."""
        user_data = Mock()
        user_data.id = "test-user-id"
        user_data.username = "testuser"
        user_data.email = "test@example.com"
        user_data.hashed_password = "hashed_password_value"
        user_data.full_name = "Test User"
        user_data.organization = "Test Org"
        user_data.role = "admin"
        user_data.is_active = True
        user_data.is_verified = True
        user_data.created_at = datetime.utcnow()
        user_data.last_login = datetime.utcnow()
        user_data.failed_login_attempts = 0
        user_data.locked_until = None
        return user_data

    @pytest.fixture
    def mock_api_key_data(self):
        """Create mock API key data."""
        api_key_data = Mock()
        api_key_data.id = "test-api-key-id"
        api_key_data.name = "Test API Key"
        api_key_data.description = "Test Description"
        api_key_data.hashed_key = "hashed_key_value"
        api_key_data.scopes = ["read", "write"]
        api_key_data.allowed_ips = None
        api_key_data.rate_limit = 1000
        api_key_data.is_active = True
        api_key_data.created_at = datetime.utcnow()
        api_key_data.expires_at = None
        api_key_data.last_used = datetime.utcnow()
        api_key_data.usage_count = 5
        api_key_data.user_id = "test-user-id"
        return api_key_data

    def test_authorization_error_init(self):
        """Test AuthorizationError initialization - covers line 53."""
        from malaria_predictor.api.auth import AuthorizationError

        # Test default message
        error = AuthorizationError()
        assert error.status_code == 403
        assert error.detail == "Insufficient permissions"

        # Test custom message
        error = AuthorizationError("Custom message")
        assert error.detail == "Custom message"

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_session, mock_request):
        """Test get_current_user when user not found - covers lines 96-101."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_user

        with patch("malaria_predictor.api.auth.verify_token") as mock_verify:
            mock_token_data = Mock()
            mock_token_data.type = "access"
            mock_token_data.sub = "missing-user-id"
            mock_verify.return_value = mock_token_data

            # Mock no user found
            mock_result = Mock()
            mock_result.fetchone.return_value = None
            mock_session.execute.return_value = mock_result

            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError):
                    await get_current_user("valid_token", mock_session, mock_request)

                mock_log.assert_called_with(
                    "user_not_found", user_id="missing-user-id", ip_address="127.0.0.1"
                )

    @pytest.mark.asyncio
    async def test_get_current_user_success_flow(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test successful get_current_user flow - covers lines 119-131."""
        from malaria_predictor.api.auth import get_current_user

        with patch("malaria_predictor.api.auth.verify_token") as mock_verify:
            mock_token_data = Mock()
            mock_token_data.type = "access"
            mock_token_data.sub = "test-user-id"
            mock_verify.return_value = mock_token_data

            # Mock successful user lookup
            mock_result = Mock()
            mock_result.fetchone.return_value = mock_user_data
            mock_session.execute.return_value = mock_result

            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with patch(
                    "malaria_predictor.database.security_models.User"
                ) as MockUser:
                    # Mock User constructor
                    mock_user_instance = Mock()
                    mock_user_instance.id = "test-user-id"
                    MockUser.return_value = mock_user_instance

                    await get_current_user("valid_token", mock_session, mock_request)

                    # Verify last login update query was executed
                    assert (
                        mock_session.execute.call_count >= 2
                    )  # One for lookup, one for update

                    # Verify security event logged
                    mock_log.assert_called_with(
                        "user_authenticated",
                        user_id="test-user-id",
                        ip_address="127.0.0.1",
                    )

    @pytest.mark.asyncio
    async def test_get_current_api_key_invalid_key(self, mock_session, mock_request):
        """Test get_current_api_key with invalid key - covers lines 170-175."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_key"
        )

        # Mock no API key found
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_invalid_key"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError):
                    await get_current_api_key(credentials, mock_session, mock_request)

                mock_log.assert_called_with(
                    "invalid_api_key_attempt",
                    ip_address="127.0.0.1",
                    details={"api_key_prefix": "invalid_ke"},  # Truncated to 10 chars
                )

    @pytest.mark.asyncio
    async def test_get_current_api_key_expired(
        self, mock_session, mock_request, mock_api_key_data
    ):
        """Test get_current_api_key with expired key - covers lines 179-184."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_api_key"
        )

        # Set expired timestamp
        mock_api_key_data.expires_at = datetime.utcnow() - timedelta(hours=1)

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_key_value"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError):
                    await get_current_api_key(credentials, mock_session, mock_request)

                mock_log.assert_called_with(
                    "expired_api_key_attempt",
                    api_key_id="test-api-key-id",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_get_current_api_key_ip_blocked(
        self, mock_session, mock_request, mock_api_key_data
    ):
        """Test get_current_api_key with IP restriction - covers lines 187-195."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_api_key"
        )

        # Set IP allowlist that doesn't include client IP
        mock_api_key_data.allowed_ips = ["192.168.1.1", "10.0.0.1"]
        mock_api_key_data.expires_at = None  # Not expired

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_key_value"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError):
                    await get_current_api_key(credentials, mock_session, mock_request)

                mock_log.assert_called_with(
                    "api_key_ip_blocked",
                    api_key_id="test-api-key-id",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_get_current_api_key_success_flow(
        self, mock_session, mock_request, mock_api_key_data
    ):
        """Test successful get_current_api_key flow - covers lines 198-228."""
        from malaria_predictor.api.auth import get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_api_key"
        )

        # Set valid API key data
        mock_api_key_data.expires_at = None
        mock_api_key_data.allowed_ips = None

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_key_value"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with patch(
                    "malaria_predictor.database.security_models.APIKey"
                ) as MockAPIKey:
                    mock_api_key_instance = Mock()
                    mock_api_key_instance.id = "test-api-key-id"
                    MockAPIKey.return_value = mock_api_key_instance

                    await get_current_api_key(credentials, mock_session, mock_request)

                    # Verify usage update query was executed
                    assert (
                        mock_session.execute.call_count >= 2
                    )  # One for lookup, one for update

                    # Verify security event logged
                    mock_log.assert_called_with(
                        "api_key_authenticated",
                        api_key_id="test-api-key-id",
                        ip_address="127.0.0.1",
                    )

    @pytest.mark.asyncio
    async def test_get_current_api_key_http_exception_reraise(
        self, mock_session, mock_request
    ):
        """Test get_current_api_key re-raising HTTPException - covers line 231."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_key"
        )

        with patch("malaria_predictor.api.auth.hash_api_key", return_value="hashed"):
            # Mock HTTPException being raised
            mock_session.execute.side_effect = AuthenticationError("Test HTTP error")

            with pytest.raises(AuthenticationError):
                await get_current_api_key(credentials, mock_session, mock_request)

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_session, mock_request):
        """Test authenticate_user when user not found - covers lines 264-269."""
        from malaria_predictor.api.auth import authenticate_user

        # Mock no user found
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
        ) as mock_log:
            result = await authenticate_user(
                "nonexistent", "password", mock_session, mock_request
            )

            assert result is None
            mock_log.assert_called_with(
                "login_attempt_invalid_user",
                ip_address="127.0.0.1",
                details={"username": "nonexistent"},
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_account_locked(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test authenticate_user with locked account - covers lines 272-278."""
        from malaria_predictor.api.auth import authenticate_user

        # Set locked account
        mock_user_data.locked_until = datetime.utcnow() + timedelta(minutes=10)

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        with patch(
            "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
        ) as mock_log:
            result = await authenticate_user(
                "testuser", "password", mock_session, mock_request
            )

            assert result is None
            mock_log.assert_called_with(
                "login_attempt_locked_account",
                user_id="test-user-id",
                ip_address="127.0.0.1",
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_account_lockout_threshold(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test authenticate_user hitting lockout threshold - covers line 288."""
        from malaria_predictor.api.auth import authenticate_user

        # Set failed attempts to trigger lockout
        mock_user_data.failed_login_attempts = 4  # Next failure will be 5th
        mock_user_data.locked_until = None

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        with patch("malaria_predictor.api.auth.verify_password", return_value=False):
            with patch("malaria_predictor.api.auth.SecurityAuditor.log_security_event"):
                result = await authenticate_user(
                    "testuser", "wrong_password", mock_session, mock_request
                )

                assert result is None
                # Should have triggered account lock
                assert mock_session.execute.call_count >= 2  # Lookup + update

    @pytest.mark.asyncio
    async def test_authenticate_user_successful_login(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test successful authenticate_user - covers lines 328-334."""
        from malaria_predictor.api.auth import authenticate_user

        mock_result = Mock()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        with patch("malaria_predictor.api.auth.verify_password", return_value=True):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with patch(
                    "malaria_predictor.database.security_models.User"
                ) as MockUser:
                    mock_user_instance = Mock()
                    mock_user_instance.id = "test-user-id"
                    MockUser.return_value = mock_user_instance

                    result = await authenticate_user(
                        "testuser", "correct_password", mock_session, mock_request
                    )

                    assert result is not None
                    mock_log.assert_called_with(
                        "successful_login",
                        user_id="test-user-id",
                        ip_address="127.0.0.1",
                    )

    @pytest.mark.asyncio
    async def test_log_audit_event_success(self, mock_session):
        """Test successful audit event logging - covers lines 481-482."""
        from malaria_predictor.api.auth import log_audit_event

        with patch("malaria_predictor.api.auth.AuditLog") as MockAuditLog:
            mock_audit_log = Mock()
            MockAuditLog.return_value = mock_audit_log

            await log_audit_event(
                event_type="test_event",
                session=mock_session,
                user_id="test-user",
                details={"key": "value"},
            )

            mock_session.add.assert_called_once_with(mock_audit_log)
            mock_session.commit.assert_called_once()

    def test_require_scopes_user_authentication(self):
        """Test require_scopes with user authentication."""
        from malaria_predictor.api.auth import require_scopes

        with patch("malaria_predictor.api.security.SecurityConfig") as MockConfig:
            MockConfig.ROLE_SCOPES = {"admin": ["read", "write", "delete"]}

            scope_dependency = require_scopes("read", "write")

            # Mock user with admin role
            mock_user = Mock()
            mock_user.role = "admin"
            mock_user.id = "test-user-id"

            with patch("malaria_predictor.api.auth.validate_scopes", return_value=True):
                result = scope_dependency(current_user=mock_user, current_api_key=None)
                assert result == mock_user

    def test_require_scopes_api_key_authentication(self):
        """Test require_scopes with API key authentication."""
        from malaria_predictor.api.auth import require_scopes

        scope_dependency = require_scopes("read")

        # Mock API key with required scopes
        mock_api_key = Mock()
        mock_api_key.scopes = ["read", "write"]
        mock_api_key.id = "test-api-key-id"

        with patch("malaria_predictor.api.auth.validate_scopes", return_value=True):
            result = scope_dependency(current_user=None, current_api_key=mock_api_key)
            assert result == mock_api_key

    def test_require_role_success(self):
        """Test require_role with valid role."""
        from malaria_predictor.api.auth import require_role

        role_dependency = require_role("admin", "superuser")

        mock_user = Mock()
        mock_user.role = "admin"
        mock_user.id = "test-user-id"

        result = role_dependency(current_user=mock_user)
        assert result == mock_user

    def test_require_role_insufficient_role(self):
        """Test require_role with insufficient role - covers lines 417-425."""
        from malaria_predictor.api.auth import AuthorizationError, require_role

        role_dependency = require_role("admin", "superuser")

        mock_user = Mock()
        mock_user.role = "user"  # Insufficient role
        mock_user.id = "test-user-id"

        with patch(
            "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
        ) as mock_log:
            with pytest.raises(AuthorizationError):
                role_dependency(current_user=mock_user)

            mock_log.assert_called_with(
                "insufficient_role",
                user_id="test-user-id",
                details={"required_roles": ["admin", "superuser"], "user_role": "user"},
            )

    def test_require_scopes_no_authentication(self):
        """Test require_scopes with no authentication - covers line 396."""
        from malaria_predictor.api.auth import AuthenticationError, require_scopes

        scope_dependency = require_scopes("read")

        with pytest.raises(AuthenticationError):
            scope_dependency(current_user=None, current_api_key=None)

    def test_require_scopes_insufficient_user_permissions(self):
        """Test require_scopes with insufficient user permissions - covers lines 363-374."""
        from malaria_predictor.api.auth import AuthorizationError, require_scopes

        with patch("malaria_predictor.api.security.SecurityConfig") as MockConfig:
            MockConfig.ROLE_SCOPES = {"user": ["read"]}  # User only has read

            scope_dependency = require_scopes(
                "read", "write", "delete"
            )  # Requires more

            mock_user = Mock()
            mock_user.role = "user"
            mock_user.id = "test-user-id"

            with patch(
                "malaria_predictor.api.auth.validate_scopes", return_value=False
            ):
                with patch(
                    "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
                ) as mock_log:
                    with pytest.raises(AuthorizationError):
                        scope_dependency(current_user=mock_user, current_api_key=None)

                    mock_log.assert_called_with(
                        "insufficient_permissions",
                        user_id="test-user-id",
                        details={
                            "required_scopes": ["read", "write", "delete"],
                            "user_scopes": ["read"],
                        },
                    )

    def test_require_scopes_insufficient_api_key_permissions(self):
        """Test require_scopes with insufficient API key permissions - covers lines 380-391."""
        from malaria_predictor.api.auth import AuthorizationError, require_scopes

        scope_dependency = require_scopes("read", "write", "delete")

        mock_api_key = Mock()
        mock_api_key.scopes = ["read"]  # Only has read permission
        mock_api_key.id = "test-api-key-id"

        with patch("malaria_predictor.api.auth.validate_scopes", return_value=False):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthorizationError):
                    scope_dependency(current_user=None, current_api_key=mock_api_key)

                mock_log.assert_called_with(
                    "insufficient_permissions",
                    api_key_id="test-api-key-id",
                    details={
                        "required_scopes": ["read", "write", "delete"],
                        "api_key_scopes": ["read"],
                    },
                )


class TestRepositoriesCoverage:
    """Test repositories.py module to achieve 100% coverage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.bind = Mock()
        session.bind.dialect = Mock()
        session.bind.dialect.name = "postgresql"
        return session

    @pytest.fixture
    def sample_era5_data(self):
        """Sample ERA5 data points."""
        return [
            {
                "timestamp": datetime.utcnow(),
                "latitude": 10.5,
                "longitude": -1.5,
                "temperature_2m": 25.0,
                "temperature_2m_max": 30.0,
                "temperature_2m_min": 20.0,
                "dewpoint_2m": 18.0,
                "total_precipitation": 0.5,
            }
        ]

    @pytest.mark.asyncio
    async def test_era5_repository_bulk_insert_empty_data(self, mock_session):
        """Test bulk_insert_data_points with empty data - covers line 48."""
        from malaria_predictor.database.repositories import ERA5Repository

        repo = ERA5Repository(mock_session)
        result = await repo.bulk_insert_data_points([])

        assert result == 0
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_era5_repository_bulk_insert_sqlite(
        self, mock_session, sample_era5_data
    ):
        """Test bulk_insert_data_points with SQLite - covers lines 54-57."""
        from malaria_predictor.database.repositories import ERA5Repository

        # Mock SQLite dialect
        mock_session.bind.dialect.name = "sqlite"

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.bulk_insert_data_points(sample_era5_data, upsert=True)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_era5_repository_bulk_insert_no_upsert(
        self, mock_session, sample_era5_data
    ):
        """Test bulk_insert_data_points without upsert - covers lines 72-73."""
        from malaria_predictor.database.repositories import ERA5Repository

        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.bulk_insert_data_points(sample_era5_data, upsert=False)

        assert result == 1

    @pytest.mark.asyncio
    async def test_processed_climate_repository_empty_data(self, mock_session):
        """Test save_processing_result with empty DataFrame - covers line 201."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        repo = ProcessedClimateRepository(mock_session)

        # Mock empty DataFrame
        empty_df = pd.DataFrame()
        mock_result = Mock()

        result = await repo.save_processing_result(mock_result, empty_df)

        assert result == 0
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_processed_climate_repository_sqlite(self, mock_session):
        """Test save_processing_result with SQLite - covers lines 226-228."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        # Mock SQLite dialect
        mock_session.bind.dialect.name = "sqlite"

        mock_execute_result = Mock()
        mock_execute_result.rowcount = 1
        mock_session.execute.return_value = mock_execute_result

        repo = ProcessedClimateRepository(mock_session)

        # Create sample DataFrame
        sample_data = pd.DataFrame(
            {
                "time": [datetime.utcnow()],
                "latitude": [10.5],
                "longitude": [-1.5],
                "t2m_celsius": [25.0],
                "mx2t_celsius": [30.0],
                "mn2t_celsius": [20.0],
                "tp": [0.0005],  # In meters, will be converted to mm
            }
        )

        mock_processing_result = Mock()
        mock_processing_result.spatial_bounds = {"north": 10.5, "west": -1.5}
        mock_processing_result.file_path = "/test/path"

        result = await repo.save_processing_result(mock_processing_result, sample_data)

        assert result == 1

    @pytest.mark.asyncio
    async def test_processed_climate_get_location_data_empty(self, mock_session):
        """Test get_location_data with no results - covers line 298."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = ProcessedClimateRepository(mock_session)
        result = await repo.get_location_data(
            latitude=10.5,
            longitude=-1.5,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )

        assert result.empty

    def test_malaria_risk_repository_risk_level_calculation(self):
        """Test _calculate_risk_level method - covers lines 424-431."""
        from malaria_predictor.database.repositories import MalariaRiskRepository

        repo = MalariaRiskRepository(Mock())

        assert repo._calculate_risk_level(0.1) == "low"
        assert repo._calculate_risk_level(0.3) == "medium"
        assert repo._calculate_risk_level(0.6) == "high"
        assert repo._calculate_risk_level(0.8) == "critical"

    @pytest.mark.asyncio
    async def test_era5_repository_postgresql_upsert(
        self, mock_session, sample_era5_data
    ):
        """Test bulk_insert_data_points with PostgreSQL upsert - covers lines 60-61."""
        from malaria_predictor.database.repositories import ERA5Repository

        # Mock PostgreSQL dialect (default in fixture)
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.bulk_insert_data_points(sample_era5_data, upsert=True)

        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_era5_repository_get_data_range_with_location(self, mock_session):
        """Test get_data_range with location filter - covers lines 101-121."""
        from malaria_predictor.database.repositories import ERA5Repository

        mock_result = Mock()
        mock_data_points = [Mock(), Mock()]
        mock_result.scalars.return_value.all.return_value = mock_data_points
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.get_data_range(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            latitude=10.5,
            longitude=-1.5,
            buffer_degrees=0.5,
        )

        assert result == mock_data_points

    @pytest.mark.asyncio
    async def test_era5_repository_get_latest_timestamp_with_location(
        self, mock_session
    ):
        """Test get_latest_timestamp with location filter - covers lines 137-148."""
        from malaria_predictor.database.repositories import ERA5Repository

        expected_timestamp = datetime.utcnow()
        mock_result = Mock()
        mock_result.scalar.return_value = expected_timestamp
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.get_latest_timestamp(latitude=10.5, longitude=-1.5)

        assert result == expected_timestamp

    @pytest.mark.asyncio
    async def test_era5_repository_delete_old_data(self, mock_session):
        """Test delete_old_data method - covers lines 162-172."""
        from malaria_predictor.database.repositories import ERA5Repository

        mock_result = Mock()
        mock_result.rowcount = 50
        mock_session.execute.return_value = mock_result

        repo = ERA5Repository(mock_session)
        result = await repo.delete_old_data(days_to_keep=30)

        assert result == 50
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_processed_climate_repository_postgresql_upsert(self, mock_session):
        """Test save_processing_result with PostgreSQL upsert - covers lines 230-231."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        # Mock PostgreSQL dialect (default in fixture)
        mock_execute_result = Mock()
        mock_execute_result.rowcount = 1
        mock_session.execute.return_value = mock_execute_result

        repo = ProcessedClimateRepository(mock_session)

        # Create sample DataFrame
        sample_data = pd.DataFrame(
            {
                "time": [datetime.utcnow()],
                "latitude": [10.5],
                "longitude": [-1.5],
                "t2m_celsius": [25.0],
                "mx2t_celsius": [30.0],
                "mn2t_celsius": [20.0],
                "tp": [0.0005],  # In meters, will be converted to mm
            }
        )

        mock_processing_result = Mock()
        mock_processing_result.spatial_bounds = {"north": 10.5, "west": -1.5}
        mock_processing_result.file_path = "/test/path"

        result = await repo.save_processing_result(mock_processing_result, sample_data)

        assert result == 1

    @pytest.mark.asyncio
    async def test_processed_climate_get_location_data_with_results(self, mock_session):
        """Test get_location_data with results - covers lines 283-298."""
        from malaria_predictor.database.repositories import ProcessedClimateRepository

        # Mock data results
        mock_data_obj = Mock()
        mock_data_obj.date = datetime.utcnow().date()
        mock_data_obj.mean_temperature = 25.0
        mock_data_obj.max_temperature = 30.0
        mock_data_obj.min_temperature = 20.0
        mock_data_obj.temperature_suitability = 0.8
        mock_data_obj.daily_precipitation_mm = 5.0
        mock_data_obj.mean_relative_humidity = 70.0

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_data_obj]
        mock_session.execute.return_value = mock_result

        repo = ProcessedClimateRepository(mock_session)
        result = await repo.get_location_data(
            latitude=10.5,
            longitude=-1.5,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )

        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]["mean_temperature"] == 25.0

    @pytest.mark.asyncio
    async def test_malaria_risk_repository_save_risk_assessment(self, mock_session):
        """Test save_risk_assessment method - covers lines 330-352."""
        from malaria_predictor.database.repositories import MalariaRiskRepository

        # Mock MalariaRiskIndex creation
        with patch(
            "malaria_predictor.database.repositories.MalariaRiskIndex"
        ) as MockRiskIndex:
            mock_risk_instance = Mock()
            MockRiskIndex.return_value = mock_risk_instance

            repo = MalariaRiskRepository(mock_session)

            risk_data = {
                "composite_score": 0.7,
                "temp_risk": 0.8,
                "precip_risk": 0.6,
                "humidity_risk": 0.7,
                "vegetation_risk": 0.5,
                "confidence": 0.9,
                "prediction_date": datetime.utcnow(),
                "time_horizon_days": 14,
                "model_type": "ml-ensemble",
                "data_sources": ["ERA5", "MODIS", "CHIRPS"],
            }

            await repo.save_risk_assessment(
                assessment_date=datetime.utcnow(),
                latitude=10.5,
                longitude=-1.5,
                risk_data=risk_data,
            )

            mock_session.add.assert_called_once_with(mock_risk_instance)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_risk_instance)

    @pytest.mark.asyncio
    async def test_malaria_risk_repository_get_latest_assessment(self, mock_session):
        """Test get_latest_assessment method - covers lines 370-380."""
        from malaria_predictor.database.repositories import MalariaRiskRepository

        mock_risk_assessment = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_risk_assessment
        mock_session.execute.return_value = mock_result

        repo = MalariaRiskRepository(mock_session)
        result = await repo.get_latest_assessment(
            latitude=10.5, longitude=-1.5, buffer_degrees=0.25
        )

        assert result == mock_risk_assessment

    @pytest.mark.asyncio
    async def test_malaria_risk_repository_get_risk_history(self, mock_session):
        """Test get_risk_history method - covers lines 400-413."""
        from malaria_predictor.database.repositories import MalariaRiskRepository

        mock_risk_assessments = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_risk_assessments
        mock_session.execute.return_value = mock_result

        repo = MalariaRiskRepository(mock_session)
        result = await repo.get_risk_history(
            latitude=10.5, longitude=-1.5, days_back=90, buffer_degrees=0.25
        )

        assert result == mock_risk_assessments
        assert len(result) == 3


class TestSessionCoverage:
    """Test session.py module to achieve 100% coverage."""

    @pytest.mark.asyncio
    async def test_get_session_with_retry_success_first_attempt(self):
        """Test get_session_with_retry success on first attempt - covers lines 145-148."""
        from malaria_predictor.database.session import get_session_with_retry

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            async with get_session_with_retry() as session:
                assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_session_with_retry_failure_then_success(self):
        """Test get_session_with_retry with retry logic - covers lines 149-157."""
        from malaria_predictor.database.session import get_session_with_retry

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            # First call fails, second succeeds
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.side_effect = [
                Exception("Connection failed"),
                mock_session,
            ]

            with patch("asyncio.sleep") as mock_sleep:
                async with get_session_with_retry(
                    max_retries=1, retry_delay=0.1
                ) as session:
                    assert session == mock_session

                mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    async def test_get_session_with_retry_all_attempts_fail(self):
        """Test get_session_with_retry when all attempts fail - covers lines 155-157."""
        from malaria_predictor.database.session import get_session_with_retry

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.side_effect = Exception(
                "Persistent failure"
            )

            with patch("asyncio.sleep"):
                with pytest.raises(Exception, match="Persistent failure"):
                    async with get_session_with_retry(max_retries=1, retry_delay=0.1):
                        pass

    @pytest.mark.asyncio
    async def test_init_database_timescaledb_warnings(self):
        """Test init_database with TimescaleDB warnings - covers lines 187-190."""
        from malaria_predictor.database.session import init_database

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_get_engine.return_value = mock_engine

            # Mock TimescaleDB command failure
            mock_conn.execute.side_effect = Exception("TimescaleDB not installed")

            with patch(
                "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                "CREATE EXTENSION timescaledb;",
            ):
                # Should not raise exception, just log warning
                await init_database()

    @pytest.mark.asyncio
    async def test_get_connection_pool_status_no_pool(self):
        """Test get_connection_pool_status with no pool - covers lines 202-210."""
        from malaria_predictor.database.session import get_connection_pool_status

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = Mock()
            # No sync_engine attribute
            (
                delattr(mock_engine, "sync_engine")
                if hasattr(mock_engine, "sync_engine")
                else None
            )
            mock_get_engine.return_value = mock_engine

            status = await get_connection_pool_status()

            assert status["pool_size"] is None
            assert status["checked_in"] is None
            assert status["checked_out"] is None

    @pytest.mark.asyncio
    async def test_check_database_health_timescaledb_failure(self):
        """Test check_database_health with TimescaleDB check failure - covers lines 271-273."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock different query results
            def execute_side_effect(query):
                query_str = str(query)
                mock_result = Mock()
                if "SELECT 1" in query_str:
                    mock_result.scalar.return_value = 1
                elif "COUNT(*)" in query_str and "tables" in query_str:
                    mock_result.scalar.return_value = 3
                elif "timescaledb" in query_str:
                    # TimescaleDB check fails
                    raise Exception("TimescaleDB extension not found")
                elif "postgis" in query_str:
                    mock_result.scalar.return_value = "3.1.0"
                elif "hypertables" in query_str:
                    raise Exception("Hypertables query failed")
                return mock_result

            mock_session.execute.side_effect = execute_side_effect

            result = await check_database_health()

            assert result["connected"] is True
            assert result["tables_exist"] is True
            assert result["timescaledb_enabled"] is False
            assert result["hypertables_count"] == 0

    @pytest.mark.asyncio
    async def test_check_database_health_complete_failure(self):
        """Test check_database_health with complete failure - covers lines 304-307."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.side_effect = Exception(
                "Database unreachable"
            )

            result = await check_database_health()

            assert result["connected"] is False
            assert result["error"] == "Database unreachable"
            assert result["response_time_ms"] is not None

    @pytest.mark.asyncio
    async def test_close_database_with_engine(self):
        """Test close_database when engine exists - covers lines 319-324."""
        from malaria_predictor.database import session

        # Set up global engine
        mock_engine = AsyncMock()
        session._engine = mock_engine
        session._async_session_maker = Mock()

        await session.close_database()

        mock_engine.dispose.assert_called_once()
        assert session._engine is None
        assert session._async_session_maker is None

    @pytest.mark.asyncio
    async def test_run_async_function(self):
        """Test run_async utility function - covers lines 339-340."""
        from malaria_predictor.database.session import run_async

        def sync_function(x, y=None):
            return x + (y or 0)

        result = await run_async(sync_function, 5, y=10)
        assert result == 15

    def test_get_engine_testing_config(self):
        """Test get_engine with testing configuration - covers lines 59-64."""
        from malaria_predictor.database import session

        # Reset engine to test creation
        session._engine = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = True
            mock_settings.database_url = "sqlite:///test.db"
            mock_settings.database_echo = False

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create:
                mock_engine = AsyncMock()
                mock_create.return_value = mock_engine

                result = session.get_engine()

                # Verify testing configuration was used
                assert mock_create.called
                call_kwargs = mock_create.call_args[1]
                assert "poolclass" in call_kwargs  # StaticPool for testing
                assert call_kwargs["pool_size"] == 5
                assert result == mock_engine

    def test_get_engine_production_config(self):
        """Test get_engine with production configuration - covers lines 60-64."""
        from malaria_predictor.database import session

        # Reset engine to test creation
        session._engine = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = False
            mock_settings.database_url = "postgresql+asyncpg://user:pass@localhost/db"
            mock_settings.database_echo = True

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create:
                mock_engine = AsyncMock()
                mock_create.return_value = mock_engine

                result = session.get_engine()

                # Verify production configuration was used
                assert mock_create.called
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["pool_size"] == 20
                assert call_kwargs["max_overflow"] == 30
                assert call_kwargs["echo_pool"] is True
                assert result == mock_engine

    def test_get_session_maker_creation(self):
        """Test get_session_maker creation - covers lines 92-103."""
        from malaria_predictor.database import session

        # Reset session maker to test creation
        session._async_session_maker = None

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine

            with patch(
                "malaria_predictor.database.session.async_sessionmaker"
            ) as mock_sessionmaker:
                mock_session_maker = AsyncMock()
                mock_sessionmaker.return_value = mock_session_maker

                result = session.get_session_maker()

                # Verify session maker was created with correct parameters
                mock_sessionmaker.assert_called_once_with(
                    mock_engine,
                    class_=session.AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
                assert result == mock_session_maker

    @pytest.mark.asyncio
    async def test_get_connection_pool_status_with_pool(self):
        """Test get_connection_pool_status with pool - covers lines 201-221."""
        from malaria_predictor.database.session import get_connection_pool_status

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = Mock()

            # Mock sync_engine with pool
            mock_sync_engine = Mock()
            mock_pool = Mock()
            mock_pool.size.return_value = 20
            mock_pool.checkedin.return_value = 15
            mock_pool.checkedout.return_value = 5
            mock_pool.overflow.return_value = 3
            mock_pool.invalid.return_value = 0

            mock_sync_engine.pool = mock_pool
            mock_engine.sync_engine = mock_sync_engine
            mock_get_engine.return_value = mock_engine

            result = await get_connection_pool_status()

            assert result["pool_size"] == 20
            assert result["checked_in"] == 15
            assert result["checked_out"] == 5
            assert result["overflow"] == 3
            assert result["invalid"] == 0

    @pytest.mark.asyncio
    async def test_check_database_health_postgis_success(self):
        """Test check_database_health with PostGIS success - covers lines 275-286."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            def execute_side_effect(query):
                query_str = str(query)
                mock_result = Mock()
                if "SELECT 1" in query_str:
                    mock_result.scalar.return_value = 1
                elif "COUNT(*)" in query_str and "tables" in query_str:
                    mock_result.scalar.return_value = 3
                elif "timescaledb" in query_str:
                    mock_result.scalar.return_value = "2.8.1"
                elif "postgis" in query_str:
                    mock_result.scalar.return_value = "3.2.0"
                elif "hypertables" in query_str:
                    mock_result.scalar.return_value = 2
                return mock_result

            mock_session.execute.side_effect = execute_side_effect

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool:
                mock_pool.return_value = {"pool_size": 20}

                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_event_loop = Mock()
                    mock_event_loop.time.side_effect = [1000.0, 1000.05]
                    mock_loop.return_value = mock_event_loop

                    result = await check_database_health()

                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is True
                    assert result["timescaledb_version"] == "2.8.1"
                    assert result["postgis_enabled"] is True
                    assert result["postgis_version"] == "3.2.0"
                    assert result["hypertables_count"] == 2
                    assert result["response_time_ms"] == 50

    @pytest.mark.asyncio
    async def test_close_database_no_engine(self):
        """Test close_database when no engine exists - covers lines 319-324."""
        from malaria_predictor.database import session

        # Ensure no engine exists
        session._engine = None
        session._async_session_maker = Mock()

        await session.close_database()

        # Should not raise exception, just reset globals
        assert session._engine is None
        assert session._async_session_maker is None

    @pytest.mark.asyncio
    async def test_run_async_function_fixed(self):
        """Test run_async utility function with proper parameter handling - covers lines 328-340."""
        from malaria_predictor.database.session import run_async

        def sync_function(x, y=None):
            return x + (y or 0)

        with patch("asyncio.get_event_loop") as mock_get_loop:
            mock_loop = Mock()
            # Fix: use *args not **kwargs for positional args
            mock_loop.run_in_executor = AsyncMock(return_value=15)
            mock_get_loop.return_value = mock_loop

            result = await run_async(sync_function, 5, y=10)

            assert result == 15
            # Verify the executor was called with the function and arguments
            mock_loop.run_in_executor.assert_called_once_with(
                None, sync_function, 5, y=10
            )

    @pytest.mark.asyncio
    async def test_init_database_with_drop_and_timescale_success(self):
        """Test init_database with drop_existing and successful TimescaleDB - covers lines 173-192."""
        from malaria_predictor.database.session import init_database

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION IF NOT EXISTS timescaledb; SELECT create_hypertable('era5_data_points', 'timestamp');",
                ):
                    await init_database(drop_existing=True)

                    # Verify drop_all was called
                    mock_conn.run_sync.assert_any_call(mock_metadata.drop_all)
                    # Verify create_all was called
                    mock_conn.run_sync.assert_any_call(mock_metadata.create_all)
                    # Verify TimescaleDB statements were executed
                    assert mock_conn.execute.call_count >= 2
                    assert mock_conn.commit.call_count >= 2

    @pytest.mark.asyncio
    async def test_check_database_health_exception_during_session_creation(self):
        """Test check_database_health when session creation fails - covers lines 304-309."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            # Session creation completely fails
            mock_get_session.return_value.__aenter__.side_effect = Exception(
                "Cannot create session"
            )

            with patch("asyncio.get_event_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_loop.time.side_effect = [1000.0, 1000.25]  # 250ms response time
                mock_get_loop.return_value = mock_loop

                result = await check_database_health()

                assert result["connected"] is False
                assert result["tables_exist"] is False
                assert result["timescaledb_enabled"] is False
                assert result["postgis_enabled"] is False
                assert result["response_time_ms"] == 250
                assert "Cannot create session" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
