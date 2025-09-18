"""
Comprehensive security module tests for malaria prediction backend.

Tests authentication, authorization, password hashing, JWT tokens,
and other security features to achieve 100% coverage for critical security modules.
"""

import sys
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt


# Mock database models before importing auth modules to avoid SQLAlchemy issues
class MockUser:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockAPIKey:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockAuditLog:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Mock the security models module before any imports
mock_security_models = MagicMock()
mock_security_models.User = MockUser
mock_security_models.APIKey = MockAPIKey
mock_security_models.AuditLog = MockAuditLog
sys.modules["malaria_predictor.database.security_models"] = mock_security_models

# Now safely import the auth modules
from malaria_predictor.api.auth import (  # noqa: E402
    AuthenticationError,
    AuthorizationError,
    authenticate_user,
    get_current_api_key,
    get_current_user,
    log_audit_event,
    require_role,
    require_scopes,
)
from malaria_predictor.api.security import (  # noqa: E402
    ALGORITHM,
    SECRET_KEY,
    SecurityAuditor,
    SecurityConfig,
    TokenData,
    UserCreate,
    UserResponse,
    constant_time_compare,
    create_access_token,
    create_api_key_token,
    create_refresh_token,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    generate_api_key,
    hash_api_key,
    hash_password,
    sanitize_input,
    validate_scopes,
    verify_password,
    verify_token,
)

# Set aliases to ensure consistency
User = MockUser
APIKey = MockAPIKey
AuditLog = MockAuditLog


class TestPasswordSecurity:
    """Test password hashing and verification functionality."""

    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Verify it's a valid bcrypt hash
        assert hashed.startswith("$2b$")
        assert len(hashed) >= 60
        assert hashed != password

    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different results."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct_password(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_inputs(self):
        """Test password verification with empty inputs."""
        # The actual implementation raises exception for empty hash
        with pytest.raises((ValueError, TypeError)):  # More specific exception types
            verify_password("", "")
        with pytest.raises((ValueError, TypeError)):
            verify_password("password", "")
        # Empty password against valid hash should return False
        valid_hash = hash_password("test_password")
        assert verify_password("", valid_hash) is False

    def test_hash_password_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_unicode_characters(self):
        """Test password hashing with unicode characters."""
        password = "пароль测试🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token_valid_payload(self):
        """Test creating access token with valid payload."""
        user_data = {"sub": "test_user_123", "scopes": ["read", "write"]}
        token = create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify using the verify_token function
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == "test_user_123"
        assert token_data.scopes == ["read", "write"]
        assert token_data.type == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test_user_123"
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify using the verify_token function
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == user_id
        assert token_data.type == "refresh"

    def test_verify_token_valid_token(self):
        """Test verifying valid access token."""
        user_data = {"sub": "test_user_123", "scopes": ["read", "write"]}
        token = create_access_token(user_data)

        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == "test_user_123"
        assert token_data.scopes == ["read", "write"]
        assert token_data.type == "access"

    def test_verify_token_invalid_token(self):
        """Test verifying invalid access token."""
        token_data = verify_token("invalid_token")
        assert token_data is None

    def test_verify_token_expired_token(self):
        """Test verifying expired access token (covers security.py lines 231-232)."""
        # Create a token that will pass JWT decoding but fail the datetime check
        past_time = int(time.time()) - 3600  # 1 hour ago
        token_payload = {
            "sub": "test_user_123",
            "type": "access",
            "exp": past_time,  # Expired timestamp
            "iat": past_time - 3600,  # Issued 2 hours ago
            "scopes": ["read"],
        }

        # Create token with proper signature but expired timestamp
        expired_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

        with (
            patch("malaria_predictor.api.security.logger") as mock_logger,
            patch("malaria_predictor.api.security.jwt.decode") as mock_decode,
        ):
            # Mock JWT decode to return the payload without checking expiration
            mock_decode.return_value = token_payload

            token_data = verify_token(expired_token)

            assert token_data is None
            # Verify the warning log is called (lines 231-232)
            mock_logger.warning.assert_called_with("Token has expired")

    def test_api_key_token_creation(self):
        """Test API key token creation."""
        api_key_id = "api_key_123"
        scopes = ["api.read", "api.write"]
        token = create_api_key_token(api_key_id, scopes)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify using the verify_token function
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == api_key_id
        assert token_data.scopes == scopes
        assert token_data.type == "api_key"

    def test_api_key_token_with_expiration(self):
        """Test API key token creation with expiration."""
        api_key_id = "api_key_123"
        scopes = ["api.read"]
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        token = create_api_key_token(api_key_id, scopes, expires_at)

        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == api_key_id
        assert token_data.scopes == scopes
        assert token_data.type == "api_key"

    def test_verify_token_missing_fields(self):
        """Test token verification with missing required fields."""
        # Create token manually without required fields
        import jwt as pyjwt

        # Token without 'sub' field
        payload = {
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
        }
        token = pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        token_data = verify_token(token)
        assert token_data is None

    def test_create_access_token_custom_expiration(self):
        """Test creating access token with custom expiration."""
        user_data = {"sub": "test_user_123"}
        custom_delta = timedelta(hours=2)

        token = create_access_token(user_data, custom_delta)
        token_data = verify_token(token)

        assert token_data is not None
        assert token_data.sub == "test_user_123"
        # Check that expiration is roughly 2 hours from now
        expected_exp = datetime.now(UTC) + custom_delta
        actual_exp = datetime.fromtimestamp(token_data.exp, UTC)
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 10  # Allow 10 second tolerance


class TestAuthenticationFunctions:
    """Test authentication and authorization functions."""

    def create_mock_request(self, client_host="127.0.0.1"):
        """Create a mock FastAPI request object."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = client_host
        return request

    def create_mock_user_data(self):
        """Create mock user data."""
        return Mock(
            id="test_user_123",
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("test_password"),
            full_name="Test User",
            organization="Test Org",
            role="user",
            is_active=True,
            is_verified=True,
            failed_login_attempts=0,
            locked_until=None,  # Not locked by default
            created_at=datetime.now(UTC),
            last_login=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting current user with valid token."""
        # Create valid token
        user_data = {"sub": "test_user_123"}
        token = create_access_token(user_data)

        # Mock database session and user data
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        # Mock SecurityAuditor to avoid logging side effects
        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await get_current_user(token, mock_session, request)

            assert user is not None
            assert user.id == "test_user_123"
            assert user.username == "testuser"
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        mock_session = AsyncMock()
        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user("invalid_token", mock_session, request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self):
        """Test getting current user when user doesn't exist."""
        user_data = {"sub": "nonexistent_user"}
        token = create_access_token(user_data)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # User not found
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(token, mock_session, request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_valid_credentials(self):
        """Test user authentication with valid credentials."""
        username = "testuser"
        password = "test_password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await authenticate_user(username, password, mock_session, request)

            assert user is not None
            assert user.id == "test_user_123"
            assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self):
        """Test user authentication with invalid credentials."""
        username = "testuser"
        password = "wrong_password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await authenticate_user(username, password, mock_session, request)

            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_user(self):
        """Test user authentication with nonexistent user."""
        username = "nonexistent"
        password = "password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # User not found
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await authenticate_user(username, password, mock_session, request)

            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_locked_account(self):
        """Test user authentication with locked account."""
        username = "testuser"
        password = "test_password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_user_data.locked_until = datetime.now(UTC) + timedelta(
            minutes=30
        )  # Locked
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await authenticate_user(username, password, mock_session, request)

            assert user is None

    @pytest.mark.asyncio
    async def test_get_current_api_key_valid(self):
        """Test getting current API key with valid credentials."""
        api_key = "test_api_key_123"
        hashed_key = hash_api_key(api_key)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_api_key_data = Mock(
            id="api_key_id_123",
            name="Test API Key",
            description="Test Description",
            hashed_key=hashed_key,
            scopes=["read", "write"],
            allowed_ips=None,
            rate_limit=1000,
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=None,
            last_used=datetime.now(UTC),
            usage_count=10,
            user_id="user_123",
        )
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            api_key_obj = await get_current_api_key(credentials, mock_session, request)

            assert api_key_obj is not None
            assert api_key_obj.id == "api_key_id_123"
            # Note: The APIKey object properties come from the mock data attributes

    @pytest.mark.asyncio
    async def test_get_current_api_key_invalid(self):
        """Test getting current API key with invalid credentials."""
        api_key = "invalid_api_key"
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # API key not found
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_api_key(credentials, mock_session, request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_api_key_expired(self):
        """Test getting current API key that is expired."""
        api_key = "test_api_key_123"
        hashed_key = hash_api_key(api_key)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_api_key_data = Mock(
            id="api_key_id_123",
            hashed_key=hashed_key,
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
            is_active=True,
        )
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_api_key(credentials, mock_session, request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_api_key_ip_blocked(self):
        """Test getting current API key with blocked IP."""
        api_key = "test_api_key_123"
        hashed_key = hash_api_key(api_key)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_api_key_data = Mock(
            id="api_key_id_123",
            hashed_key=hashed_key,
            expires_at=None,
            is_active=True,
            allowed_ips=["192.168.1.1", "10.0.0.1"],  # Client IP not in list
        )
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request("192.168.1.100")  # Different IP

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_api_key(credentials, mock_session, request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_successful_authentication_with_database_update(
        self,
    ):
        """Test get_current_user with successful authentication and database update (covers lines 119-131)."""
        # Create valid token
        user_data = {"sub": "test_user_123"}
        token = create_access_token(user_data)

        # Mock database session and user data
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        # Mock SecurityAuditor to avoid logging side effects
        with patch("malaria_predictor.api.auth.SecurityAuditor") as mock_auditor:
            user = await get_current_user(token, mock_session, request)

            # Verify database updates were called (lines 119-122)
            assert (
                mock_session.execute.call_count >= 2
            )  # One for select, one for update
            assert mock_session.commit.called

            # Verify security audit logging was called (lines 125-129)
            mock_auditor.log_security_event.assert_called_with(
                "user_authenticated", user_id=str(user.id), ip_address="127.0.0.1"
            )

    @pytest.mark.asyncio
    async def test_get_current_api_key_expired_key(self):
        """Test get_current_api_key with expired API key (covers lines 179-184)."""
        api_key = "test_api_key_123"
        hashed_key = hash_api_key(api_key)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        # Create expired API key
        mock_api_key_data = Mock(
            id="api_key_id_123",
            hashed_key=hashed_key,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            allowed_ips=None,
            is_active=True,
        )
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor") as mock_auditor:
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_api_key(credentials, mock_session, request)

            assert "API key expired" in str(exc_info.value)
            # Verify security audit logging for expired key (lines 179-183)
            mock_auditor.log_security_event.assert_called_with(
                "expired_api_key_attempt",
                api_key_id=str(mock_api_key_data.id),
                ip_address="127.0.0.1",
            )

    @pytest.mark.asyncio
    async def test_get_current_api_key_successful_with_database_update(self):
        """Test get_current_api_key successful authentication with database update (covers lines 215-228)."""
        api_key = "test_api_key_123"
        hashed_key = hash_api_key(api_key)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_api_key_data = Mock(
            id="api_key_id_123",
            name="Test API Key",
            description="Test Description",
            hashed_key=hashed_key,
            scopes=["read", "write"],
            allowed_ips=None,
            rate_limit=1000,
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=None,
            last_used=datetime.now(UTC),
            usage_count=10,
            user_id="user_123",
        )
        mock_result.fetchone.return_value = mock_api_key_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor") as mock_auditor:
            api_key_obj = await get_current_api_key(credentials, mock_session, request)

            # Verify database updates were called (lines 215-219)
            assert (
                mock_session.execute.call_count >= 2
            )  # One for select, one for update
            assert mock_session.commit.called

            # Verify security audit logging was called (lines 222-226)
            mock_auditor.log_security_event.assert_called_with(
                "api_key_authenticated",
                api_key_id=str(api_key_obj.id),
                ip_address="127.0.0.1",
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_account_lockout_after_failed_attempts(self):
        """Test authenticate_user triggering account lockout (covers line 288)."""
        username = "testuser"
        password = "wrong_password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_user_data.failed_login_attempts = (
            4  # One more attempt will trigger lockout
        )
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            user = await authenticate_user(username, password, mock_session, request)

            assert user is None
            # Verify database update for lockout (should include line 288)
            assert mock_session.execute.call_count >= 2  # Select + update
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_authenticate_user_successful_authentication_with_logging(self):
        """Test authenticate_user successful authentication with security logging (covers lines 328-334)."""
        username = "testuser"
        password = "test_password"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_user_data = self.create_mock_user_data()
        mock_result.fetchone.return_value = mock_user_data
        mock_session.execute.return_value = mock_result

        request = self.create_mock_request()

        with patch("malaria_predictor.api.auth.SecurityAuditor") as mock_auditor:
            user = await authenticate_user(username, password, mock_session, request)

            assert user is not None
            # Verify security audit logging for successful login (lines 328-332)
            mock_auditor.log_security_event.assert_called_with(
                "successful_login", user_id=str(user.id), ip_address="127.0.0.1"
            )

    @pytest.mark.asyncio
    async def test_log_audit_event_successful_database_commit(self):
        """Test log_audit_event successful database operations (covers lines 481-482)."""
        mock_session = AsyncMock()

        with patch("malaria_predictor.api.auth.AuditLog") as mock_audit_log_class:
            mock_audit_log_instance = Mock()
            mock_audit_log_class.return_value = mock_audit_log_instance

            await log_audit_event(
                event_type="test_event",
                session=mock_session,
                user_id="user_123",
                ip_address="192.168.1.1",
            )

            # Verify database operations (lines 481-482)
            mock_session.add.assert_called_once_with(mock_audit_log_instance)
            mock_session.commit.assert_called_once()

    async def test_authenticate_user_database_exception(self):
        """Test authenticate_user function handles database exceptions gracefully."""
        mock_session = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Mock database operation to raise an exception
        mock_session.execute.side_effect = Exception("Database connection error")

        result = await authenticate_user(
            username="testuser",
            password="testpass",
            session=mock_session,
            request=mock_request,
        )

        # Should return None when exception occurs
        assert result is None
        # Should have attempted to execute query
        mock_session.execute.assert_called_once()


class TestAuthorizationFunctions:
    """Test authorization functions."""

    def test_require_scopes_user_with_permissions(self):
        """Test require_scopes with user having required permissions."""
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.role = "admin"  # Admin has all scopes

        scope_dependency = require_scopes("read:predictions", "write:predictions")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            result = scope_dependency(current_user=mock_user, current_api_key=None)

            assert result == mock_user

    def test_require_scopes_user_without_permissions(self):
        """Test require_scopes with user lacking required permissions."""
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.role = "readonly"  # Readonly doesn't have write permissions

        scope_dependency = require_scopes("write:predictions")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthorizationError) as exc_info:
                scope_dependency(current_user=mock_user, current_api_key=None)

            assert exc_info.value.status_code == 403

    def test_require_scopes_api_key_with_permissions(self):
        """Test require_scopes with API key having required permissions."""
        mock_api_key = Mock()
        mock_api_key.id = "api_key_123"
        mock_api_key.scopes = ["read:predictions", "write:predictions"]

        scope_dependency = require_scopes("read:predictions")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            result = scope_dependency(current_user=None, current_api_key=mock_api_key)

            assert result == mock_api_key

    def test_require_scopes_api_key_without_permissions(self):
        """Test require_scopes with API key lacking required permissions."""
        mock_api_key = Mock()
        mock_api_key.id = "api_key_123"
        mock_api_key.scopes = ["read:predictions"]  # Missing write permission

        scope_dependency = require_scopes("write:predictions")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthorizationError) as exc_info:
                scope_dependency(current_user=None, current_api_key=mock_api_key)

            assert exc_info.value.status_code == 403

    def test_require_scopes_no_authentication(self):
        """Test require_scopes with no authentication provided."""
        scope_dependency = require_scopes("read:predictions")

        with pytest.raises(AuthenticationError) as exc_info:
            scope_dependency(current_user=None, current_api_key=None)

        assert exc_info.value.status_code == 401

    def test_require_role_user_with_role(self):
        """Test require_role with user having required role."""
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.role = "admin"

        role_dependency = require_role("admin", "researcher")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            result = role_dependency(current_user=mock_user)

            assert result == mock_user

    def test_require_role_user_without_role(self):
        """Test require_role with user lacking required role."""
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.role = "user"  # User role not in allowed roles

        role_dependency = require_role("admin", "researcher")

        with patch("malaria_predictor.api.auth.SecurityAuditor"):
            with pytest.raises(AuthorizationError) as exc_info:
                role_dependency(current_user=mock_user)

            assert exc_info.value.status_code == 403


class TestAuditLogging:
    """Test audit logging functionality."""

    @pytest.mark.asyncio
    async def test_log_audit_event(self):
        """Test audit event logging."""
        mock_session = AsyncMock()

        await log_audit_event(
            event_type="test_event",
            session=mock_session,
            user_id="user_123",
            ip_address="192.168.1.1",
            endpoint="/api/test",
            method="GET",
            success=True,
        )

        # Verify that session.add was called with an AuditLog instance
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_exception_handling(self):
        """Test audit event logging with exception handling."""
        mock_session = AsyncMock()
        mock_session.add.side_effect = Exception("Database error")

        # Should not raise exception even if logging fails
        await log_audit_event(
            event_type="test_event", session=mock_session, user_id="user_123"
        )

    async def test_log_audit_event_commit_exception(self):
        """Test log_audit_event function handles commit exceptions gracefully."""
        mock_session = AsyncMock()

        # Mock session.commit to raise an exception
        mock_session.commit.side_effect = Exception("Database commit error")

        # Should not raise an exception, just log the error
        await log_audit_event(
            event_type="test_event", session=mock_session, user_id="test-user-id"
        )

        # Verify session.add was called but commit failed gracefully
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestSecurityUtilities:
    """Test security utility functions."""

    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = generate_api_key()

        assert isinstance(api_key, str)
        assert api_key.startswith("mp_")
        assert len(api_key) == 67  # "mp_" + 64 characters

    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = "test_api_key_123"
        hashed = hash_api_key(api_key)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 produces 64-char hex string
        assert hashed != api_key

        # Same input should produce same hash
        hashed2 = hash_api_key(api_key)
        assert hashed == hashed2

    def test_sanitize_input_basic(self):
        """Test input sanitization for basic cases."""
        # Test HTML injection - should be HTML escaped
        malicious_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious_input)
        assert "&lt;script&gt;" in sanitized  # HTML escaped
        assert "alert" in sanitized  # Content preserved but escaped
        assert "<script>" not in sanitized  # Raw tags removed

    def test_sanitize_input_sql_injection(self):
        """Test input sanitization for SQL injection attempts."""
        malicious_input = "'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious_input)
        # After HTML escaping, the input should be safe
        assert "&#x27;" in sanitized  # Single quotes are HTML escaped
        assert "DROP TABLE" in sanitized.upper()  # Content is preserved but escaped

    def test_sanitize_input_normal_text(self):
        """Test input sanitization preserves normal text."""
        normal_input = "This is normal text with numbers 123 and symbols @#$"
        sanitized = sanitize_input(normal_input)
        assert "This is normal text" in sanitized
        assert "123" in sanitized

    def test_sanitize_input_max_length(self):
        """Test input sanitization with length limit."""
        long_input = "A" * 2000
        sanitized = sanitize_input(long_input, max_length=500)
        assert len(sanitized) <= 500

    def test_validate_scopes(self):
        """Test scope validation."""
        required_scopes = ["read:predictions", "write:predictions"]
        user_scopes = ["read:predictions", "write:predictions", "read:models"]

        assert validate_scopes(required_scopes, user_scopes) is True

        # Missing scope
        user_scopes_missing = ["read:predictions"]
        assert validate_scopes(required_scopes, user_scopes_missing) is False

    def test_constant_time_compare(self):
        """Test constant-time string comparison."""
        string1 = "secret_value_123"
        string2 = "secret_value_123"
        string3 = "different_value"

        assert constant_time_compare(string1, string2) is True
        assert constant_time_compare(string1, string3) is False

    def test_encrypt_decrypt_sensitive_data(self):
        """Test data encryption and decryption."""
        original_data = "sensitive_information_123"

        encrypted = encrypt_sensitive_data(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)

        decrypted = decrypt_sensitive_data(encrypted)
        assert decrypted == original_data


class TestSecurityAuditor:
    """Test SecurityAuditor functionality."""

    def test_log_security_event(self):
        """Test security event logging."""
        with patch("malaria_predictor.api.security.logger") as mock_logger:
            SecurityAuditor.log_security_event(
                "test_event",
                user_id="user_123",
                ip_address="192.168.1.1",
                details={"test": "data"},
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "SECURITY_AUDIT" in call_args
            assert "test_event" in call_args

    def test_detect_suspicious_activity(self):
        """Test suspicious activity detection."""
        result = SecurityAuditor.detect_suspicious_activity(
            user_id="user_123", ip_address="192.168.1.1", endpoint="/api/test"
        )

        # Current implementation always returns False
        assert result is False


class TestSecurityModels:
    """Test security-related Pydantic models."""

    def test_user_create_model_valid(self):
        """Test UserCreate model with valid data."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "secure_password_123",
            "full_name": "Test User",
        }

        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "secure_password_123"
        assert user.full_name == "Test User"

    def test_user_create_model_invalid_email(self):
        """Test UserCreate model with invalid email."""
        user_data = {
            "username": "testuser",
            "email": "invalid_email",
            "password": "secure_password_123",
        }

        with pytest.raises(ValueError):
            UserCreate(**user_data)

    def test_user_create_model_short_username(self):
        """Test UserCreate model with short username."""
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "secure_password_123",
        }

        with pytest.raises(ValueError):
            UserCreate(**user_data)

    def test_user_create_model_short_password(self):
        """Test UserCreate model with short password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Too short
        }

        with pytest.raises(ValueError):
            UserCreate(**user_data)

    def test_user_response_model(self):
        """Test UserResponse model."""
        user_data = {
            "id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "organization": "Test Org",
            "role": "user",
            "is_active": True,
            "created_at": datetime.now(UTC),
            "last_login": datetime.now(UTC),
        }

        user = UserResponse(**user_data)
        assert user.id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        # Password should not be in response model
        assert not hasattr(user, "password")

    def test_token_data_model(self):
        """Test TokenData model."""
        token_data = {
            "sub": "user_123",
            "type": "access",
            "exp": int(datetime.now(UTC).timestamp()) + 3600,
            "iat": int(datetime.now(UTC).timestamp()),
            "scopes": ["read", "write"],
        }

        token = TokenData(**token_data)
        assert token.sub == "user_123"
        assert token.type == "access"
        assert token.scopes == ["read", "write"]


class TestSecurityConfig:
    """Test SecurityConfig class."""

    def test_security_config_scopes(self):
        """Test SecurityConfig scopes definition."""
        assert "read:health" in SecurityConfig.SCOPES
        assert "write:admin" in SecurityConfig.SCOPES
        assert isinstance(SecurityConfig.SCOPES["read:health"], str)

    def test_security_config_role_scopes(self):
        """Test SecurityConfig role-based scopes."""
        assert "admin" in SecurityConfig.ROLE_SCOPES
        assert "user" in SecurityConfig.ROLE_SCOPES

        admin_scopes = SecurityConfig.ROLE_SCOPES["admin"]
        user_scopes = SecurityConfig.ROLE_SCOPES["user"]

        # Admin should have more scopes than user
        assert len(admin_scopes) > len(user_scopes)

        # User scopes should be subset of admin scopes
        for scope in user_scopes:
            assert scope in admin_scopes


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_authentication_error_default(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert "Could not validate credentials" in error.detail
        assert "Bearer" in error.headers["WWW-Authenticate"]

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        custom_message = "Token has expired"
        error = AuthenticationError(custom_message)
        assert error.status_code == 401
        assert error.detail == custom_message

    def test_authorization_error_default(self):
        """Test AuthorizationError with default message."""
        error = AuthorizationError()
        assert error.status_code == 403
        assert "Insufficient permissions" in error.detail

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message."""
        custom_message = "Admin role required"
        error = AuthorizationError(custom_message)
        assert error.status_code == 403
        assert error.detail == custom_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
