"""
Comprehensive unit tests for API authentication module.
Target: 100% coverage for src/malaria_predictor/api/auth.py
"""
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, status
from jose import jwt

# Import the auth module to test
from src.malaria_predictor.api.auth import (
    AuthService,
    JWTTokenService,
    SecurityManager,
    create_access_token,
    decode_access_token,
    get_current_user,
    get_user_permissions,
    hash_password,
    require_permissions,
    verify_api_key,
    verify_password,
)
from src.malaria_predictor.models import Permission, User, UserRole


class TestJWTTokenService:
    """Test JWT token operations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.jwt_service = JWTTokenService()
        self.test_user_data = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "researcher"
        }

    def test_create_access_token_success(self):
        """Test successful access token creation."""
        token = self.jwt_service.create_access_token(self.test_user_data)
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        expiry = timedelta(hours=2)
        token = self.jwt_service.create_access_token(
            self.test_user_data, expires_delta=expiry
        )

        # Decode and verify expiry
        decoded = self.jwt_service.decode_access_token(token)
        assert "exp" in decoded

    def test_decode_access_token_success(self):
        """Test successful token decoding."""
        token = self.jwt_service.create_access_token(self.test_user_data)
        decoded = self.jwt_service.decode_access_token(token)

        assert decoded["user_id"] == self.test_user_data["user_id"]
        assert decoded["email"] == self.test_user_data["email"]

    def test_decode_access_token_invalid(self):
        """Test decoding invalid token raises exception."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            self.jwt_service.decode_access_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decode_access_token_expired(self):
        """Test decoding expired token raises exception."""

        with patch("src.malaria_predictor.api.auth.jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.ExpiredSignatureError()

            with pytest.raises(HTTPException) as exc_info:
                self.jwt_service.decode_access_token("expired_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decode_access_token_invalid_signature(self):
        """Test decoding token with invalid signature."""
        with patch("src.malaria_predictor.api.auth.jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.InvalidTokenError()

            with pytest.raises(HTTPException) as exc_info:
                self.jwt_service.decode_access_token("invalid_signature_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed, not plain text
        assert len(hashed) > 50  # Bcrypt hashes are long

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password_456"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification failure."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_empty_string(self):
        """Test hashing empty password."""
        empty_password = ""
        hashed = hash_password(empty_password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_with_invalid_hash(self):
        """Test password verification with invalid hash format."""
        password = "test_password"
        invalid_hash = "not_a_valid_hash"

        # Should handle invalid hash gracefully
        result = verify_password(password, invalid_hash)
        assert result is False


class TestAuthService:
    """Test authentication service functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.auth_service = AuthService()
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user_123"
        self.mock_user.email = "test@example.com"
        self.mock_user.role = UserRole.RESEARCHER
        self.mock_user.is_active = True
        self.mock_user.password_hash = hash_password("test_password")

    @patch("src.malaria_predictor.api.auth.get_user_by_email")
    def test_authenticate_user_success(self, mock_get_user):
        """Test successful user authentication."""
        mock_get_user.return_value = self.mock_user

        result = self.auth_service.authenticate_user(
            "test@example.com", "test_password"
        )

        assert result == self.mock_user
        mock_get_user.assert_called_once_with("test@example.com")

    @patch("src.malaria_predictor.api.auth.get_user_by_email")
    def test_authenticate_user_not_found(self, mock_get_user):
        """Test authentication with non-existent user."""
        mock_get_user.return_value = None

        result = self.auth_service.authenticate_user(
            "nonexistent@example.com", "password"
        )

        assert result is None

    @patch("src.malaria_predictor.api.auth.get_user_by_email")
    def test_authenticate_user_wrong_password(self, mock_get_user):
        """Test authentication with wrong password."""
        mock_get_user.return_value = self.mock_user

        result = self.auth_service.authenticate_user(
            "test@example.com", "wrong_password"
        )

        assert result is None

    @patch("src.malaria_predictor.api.auth.get_user_by_email")
    def test_authenticate_user_inactive(self, mock_get_user):
        """Test authentication with inactive user."""
        self.mock_user.is_active = False
        mock_get_user.return_value = self.mock_user

        result = self.auth_service.authenticate_user(
            "test@example.com", "test_password"
        )

        assert result is None

    def test_generate_user_token(self):
        """Test user token generation."""
        token = self.auth_service.generate_user_token(self.mock_user)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_validate_token_success(self):
        """Test successful token validation."""
        token = self.auth_service.generate_user_token(self.mock_user)

        with patch("src.malaria_predictor.api.auth.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = self.mock_user

            result = self.auth_service.validate_token(token)
            assert result == self.mock_user

    def test_validate_token_invalid(self):
        """Test validation of invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.validate_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIKeyVerification:
    """Test API key verification functionality."""

    @patch("src.malaria_predictor.api.auth.get_api_key_details")
    def test_verify_api_key_success(self, mock_get_api_key):
        """Test successful API key verification."""
        mock_api_key = Mock()
        mock_api_key.is_active = True
        mock_api_key.rate_limit = 1000
        mock_api_key.permissions = ["read", "write"]
        mock_get_api_key.return_value = mock_api_key

        result = verify_api_key("valid_api_key")

        assert result == mock_api_key

    @patch("src.malaria_predictor.api.auth.get_api_key_details")
    def test_verify_api_key_not_found(self, mock_get_api_key):
        """Test API key verification for non-existent key."""
        mock_get_api_key.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("invalid_api_key")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.malaria_predictor.api.auth.get_api_key_details")
    def test_verify_api_key_inactive(self, mock_get_api_key):
        """Test API key verification for inactive key."""
        mock_api_key = Mock()
        mock_api_key.is_active = False
        mock_get_api_key.return_value = mock_api_key

        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("inactive_api_key")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestPermissionSystem:
    """Test permission-based access control."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user_123"
        self.mock_user.role = UserRole.RESEARCHER
        self.mock_user.permissions = [Permission.READ_DATA, Permission.WRITE_DATA]

    def test_get_user_permissions_success(self):
        """Test getting user permissions."""
        permissions = get_user_permissions(self.mock_user)

        assert Permission.READ_DATA in permissions
        assert Permission.WRITE_DATA in permissions

    def test_require_permissions_success(self):
        """Test permission requirement check success."""
        required_perms = [Permission.READ_DATA]

        # Should not raise exception
        require_permissions(self.mock_user, required_perms)

    def test_require_permissions_failure(self):
        """Test permission requirement check failure."""
        required_perms = [Permission.ADMIN_ACCESS]

        with pytest.raises(HTTPException) as exc_info:
            require_permissions(self.mock_user, required_perms)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_require_permissions_multiple_success(self):
        """Test multiple permission requirement success."""
        required_perms = [Permission.READ_DATA, Permission.WRITE_DATA]

        # Should not raise exception
        require_permissions(self.mock_user, required_perms)

    def test_require_permissions_partial_failure(self):
        """Test permission requirement failure with partial permissions."""
        required_perms = [Permission.READ_DATA, Permission.ADMIN_ACCESS]

        with pytest.raises(HTTPException) as exc_info:
            require_permissions(self.mock_user, required_perms)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestSecurityManager:
    """Test security manager functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.security_manager = SecurityManager()

    def test_rate_limit_check_success(self):
        """Test successful rate limit check."""
        api_key = "test_api_key"

        # First call should succeed
        result = self.security_manager.check_rate_limit(api_key)
        assert result is True

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        api_key = "limited_api_key"

        with patch("src.malaria_predictor.api.auth.get_rate_limit_status") as mock_status:
            mock_status.return_value = {"exceeded": True, "reset_time": 3600}

            with pytest.raises(HTTPException) as exc_info:
                self.security_manager.check_rate_limit(api_key)

            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_validate_request_signature(self):
        """Test request signature validation."""
        request_data = {"data": "test"}
        signature = "valid_signature"

        with patch("src.malaria_predictor.api.auth.verify_signature") as mock_verify:
            mock_verify.return_value = True

            result = self.security_manager.validate_request_signature(
                request_data, signature
            )
            assert result is True

    def test_validate_request_signature_invalid(self):
        """Test invalid request signature."""
        request_data = {"data": "test"}
        signature = "invalid_signature"

        with patch("src.malaria_predictor.api.auth.verify_signature") as mock_verify:
            mock_verify.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                self.security_manager.validate_request_signature(
                    request_data, signature
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestAsyncAuthDependencies:
    """Test async authentication dependencies."""

    async def test_get_current_user_success(self):
        """Test successful current user retrieval."""
        mock_token = "valid_token"
        mock_user = Mock(spec=User)
        mock_user.id = "user_123"

        with patch("src.malaria_predictor.api.auth.AuthService") as mock_auth_service:
            mock_auth_service.return_value.validate_token.return_value = mock_user

            result = await get_current_user(mock_token)
            assert result == mock_user

    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        invalid_token = "invalid_token"

        with patch("src.malaria_predictor.api.auth.AuthService") as mock_auth_service:
            mock_auth_service.return_value.validate_token.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(invalid_token)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenUtilities:
    """Test token utility functions."""

    def test_create_access_token_function(self):
        """Test standalone create_access_token function."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_access_token_with_expiry(self):
        """Test create_access_token with custom expiry."""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(hours=1)

        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        # Verify token contains expiry
        decoded = decode_access_token(token)
        assert "exp" in decoded

    def test_decode_access_token_function(self):
        """Test standalone decode_access_token function."""
        data = {"sub": "user@example.com", "user_id": "123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "user@example.com"
        assert decoded["user_id"] == "123"

    def test_decode_access_token_malformed(self):
        """Test decoding malformed token."""
        malformed_token = "not.a.valid.jwt.token.format"

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(malformed_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_credentials(self):
        """Test authentication with empty credentials."""
        auth_service = AuthService()

        result = auth_service.authenticate_user("", "")
        assert result is None

    def test_none_credentials(self):
        """Test authentication with None credentials."""
        auth_service = AuthService()

        with pytest.raises((TypeError, AttributeError)):
            auth_service.authenticate_user(None, None)

    def test_very_long_password(self):
        """Test handling of very long password."""
        long_password = "a" * 1000
        hashed = hash_password(long_password)

        assert verify_password(long_password, hashed) is True

    def test_unicode_password(self):
        """Test handling of unicode characters in password."""
        unicode_password = "пароль_тест_🔐"
        hashed = hash_password(unicode_password)

        assert verify_password(unicode_password, hashed) is True

    def test_special_characters_password(self):
        """Test password with special characters."""
        special_password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(special_password)

        assert verify_password(special_password, hashed) is True
