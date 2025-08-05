"""
Corrected authentication tests with proper async mock handling.

This file fixes the failing authentication tests by properly handling
async mocks for database sessions and security event logging.
"""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path before importing modules
sys.path.insert(0, "src")


class TestAuthenticationAsyncFixes:
    """Test auth.py functions with proper async mock handling."""

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

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test get_current_user with valid token - proper async mock handling."""
        from malaria_predictor.api.auth import get_current_user

        with patch("malaria_predictor.api.auth.verify_token") as mock_verify:
            mock_token_data = Mock()
            mock_token_data.type = "access"
            mock_token_data.sub = "test-user-id"
            mock_verify.return_value = mock_token_data

            # Mock successful database lookup
            mock_result = Mock()
            mock_result.fetchone.return_value = mock_user_data
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                result = await get_current_user(
                    "valid_token", mock_session, mock_request
                )

                # Verify function executed properly - result should be actual User object
                assert result.id == "test-user-id"
                assert result.username == "testuser"
                assert result.email == "test@example.com"
                assert mock_session.execute.call_count >= 2  # Lookup + update
                mock_session.commit.assert_called()

                # Verify security event logged
                mock_log.assert_called_with(
                    "user_authenticated", user_id="test-user-id", ip_address="127.0.0.1"
                )

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_session, mock_request):
        """Test get_current_user when user not found."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_user

        with patch("malaria_predictor.api.auth.verify_token") as mock_verify:
            mock_token_data = Mock()
            mock_token_data.type = "access"
            mock_token_data.sub = "missing-user-id"
            mock_verify.return_value = mock_token_data

            # Mock no user found
            mock_result = Mock()
            mock_result.fetchone.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError) as exc_info:
                    await get_current_user("valid_token", mock_session, mock_request)

                assert "Authentication failed" in str(exc_info.value.detail)
                mock_log.assert_called_with(
                    "user_not_found", user_id="missing-user-id", ip_address="127.0.0.1"
                )

    @pytest.mark.asyncio
    async def test_get_current_api_key_valid(
        self, mock_session, mock_request, mock_api_key_data
    ):
        """Test get_current_api_key with valid API key."""
        from malaria_predictor.api.auth import get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_api_key"
        )

        # Mock successful API key lookup
        mock_result = Mock()
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_key_value"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                result = await get_current_api_key(
                    credentials, mock_session, mock_request
                )

                # Verify function executed properly - result should be actual APIKey object
                assert result.id == "test-api-key-id"
                assert result.name == "Test API Key"
                assert result.hashed_key == "hashed_key_value"
                assert mock_session.execute.call_count >= 2  # Lookup + update
                mock_session.commit.assert_called()

                # Verify security event logged
                mock_log.assert_called_with(
                    "api_key_authenticated",
                    api_key_id="test-api-key-id",
                    ip_address="127.0.0.1",
                )

    @pytest.mark.asyncio
    async def test_get_current_api_key_invalid(self, mock_session, mock_request):
        """Test get_current_api_key with invalid API key."""
        from malaria_predictor.api.auth import AuthenticationError, get_current_api_key

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_key"
        )

        # Mock no API key found
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "malaria_predictor.api.auth.hash_api_key", return_value="hashed_invalid_key"
        ):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                with pytest.raises(AuthenticationError) as exc_info:
                    await get_current_api_key(credentials, mock_session, mock_request)

                assert "Invalid API key" in str(exc_info.value.detail)
                mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_user_valid_credentials(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test authenticate_user with valid credentials."""
        from malaria_predictor.api.auth import authenticate_user

        # Mock successful user lookup
        mock_result = Mock()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("malaria_predictor.api.auth.verify_password", return_value=True):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                result = await authenticate_user(
                    "testuser", "password", mock_session, mock_request
                )

                # Verify function executed properly - result should be actual User object
                assert result.id == "test-user-id"
                assert result.username == "testuser"
                assert result.email == "test@example.com"
                assert mock_session.execute.call_count >= 2  # Lookup + update
                mock_session.commit.assert_called()

                # Verify security event logged
                mock_log.assert_called_with(
                    "successful_login", user_id="test-user-id", ip_address="127.0.0.1"
                )

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(
        self, mock_session, mock_request, mock_user_data
    ):
        """Test authenticate_user with invalid credentials."""
        from malaria_predictor.api.auth import authenticate_user

        # Mock successful user lookup but invalid password
        mock_result = Mock()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("malaria_predictor.api.auth.verify_password", return_value=False):
            with patch(
                "malaria_predictor.api.auth.SecurityAuditor.log_security_event"
            ) as mock_log:
                result = await authenticate_user(
                    "testuser", "wrongpassword", mock_session, mock_request
                )

                # Verify function returned None for invalid credentials
                assert result is None

                # Verify failed login attempts were incremented
                assert mock_session.execute.call_count >= 2  # Lookup + update
                mock_session.commit.assert_called()

                # Verify security event logged
                mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_log_audit_event(self, mock_session):
        """Test log_audit_event function."""
        from malaria_predictor.api.auth import log_audit_event

        mock_session.add = Mock()  # Not async
        mock_session.commit = AsyncMock()

        await log_audit_event(
            session=mock_session,
            event_type="test_event",
            user_id="test-user-id",
            success=True,
        )

        # Verify audit log was created and added
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_exception_handling(self, mock_session):
        """Test log_audit_event exception handling."""
        from malaria_predictor.api.auth import log_audit_event

        # Mock session.add to raise an exception
        mock_session.add = Mock(side_effect=Exception("Database error"))
        mock_session.commit = AsyncMock()

        with patch(
            "malaria_predictor.database.security_models.AuditLog"
        ) as MockAuditLog:
            with patch("malaria_predictor.api.auth.logger") as mock_logger:
                mock_audit_log = Mock()
                MockAuditLog.return_value = mock_audit_log

                # Should not raise exception, but should log error
                await log_audit_event(
                    session=mock_session,
                    event_type="test_event",
                    user_id="test-user-id",
                    success=True,
                )

                # Verify error was logged
                mock_logger.error.assert_called()
