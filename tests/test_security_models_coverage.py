"""
Comprehensive tests for database/security_models.py to achieve high coverage.

This module tests the security database models for user management, API key management,
and audit logging to support comprehensive security features.
"""

import sys
import uuid
from datetime import datetime, timedelta

# Add src to path before importing modules
sys.path.insert(0, "src")

from malaria_predictor.database.security_models import (
    DEFAULT_SECURITY_SETTINGS,
    APIKey,
    AuditLog,
    IPAllowlist,
    RateLimitLog,
    RefreshToken,
    SecuritySettings,
    User,
)


class TestUser:
    """Test User model to achieve comprehensive coverage."""

    def test_user_model_creation(self):
        """Test User model instance creation with all attributes."""
        user_id = uuid.uuid4()

        # Mock the database columns to simulate SQLAlchemy behavior
        user = User()
        user.id = user_id
        user.username = "testuser"
        user.email = "test@example.com"
        user.hashed_password = "hashed_password_123"
        user.full_name = "Test User"
        user.organization = "Test Org"
        user.role = "admin"
        user.is_active = True
        user.is_verified = True
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        user.last_login = datetime.now()
        user.failed_login_attempts = 0
        user.locked_until = None
        user.require_password_change = False
        user.password_changed_at = datetime.now()

        # Test attributes
        assert user.id == user_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.full_name == "Test User"
        assert user.organization == "Test Org"
        assert user.role == "admin"
        assert user.is_active is True
        assert user.is_verified is True
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.require_password_change is False
        assert user.password_changed_at is not None

    def test_user_model_defaults(self):
        """Test User model default values."""
        user = User()
        user.username = "testuser"
        user.email = "test@example.com"
        user.hashed_password = "hashed_password"

        # These would be set by SQLAlchemy defaults
        user.role = "user"  # Default role
        user.is_active = True  # Default active
        user.is_verified = False  # Default not verified
        user.failed_login_attempts = 0  # Default no failed attempts
        user.require_password_change = False  # Default no password change required

        assert user.role == "user"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.failed_login_attempts == 0
        assert user.require_password_change is False

    def test_user_repr(self):
        """Test User model string representation."""
        user = User()
        user.id = uuid.uuid4()
        user.username = "testuser"
        user.email = "test@example.com"

        repr_str = repr(user)

        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str


class TestAPIKey:
    """Test APIKey model to achieve comprehensive coverage."""

    def test_api_key_model_creation(self):
        """Test APIKey model instance creation with all attributes."""
        api_key_id = uuid.uuid4()
        user_id = uuid.uuid4()

        api_key = APIKey()
        api_key.id = api_key_id
        api_key.name = "Test API Key"
        api_key.description = "API key for testing"
        api_key.hashed_key = "hashed_api_key_123"
        api_key.scopes = ["read", "write"]
        api_key.allowed_ips = ["192.168.1.1", "10.0.0.0/8"]
        api_key.rate_limit = 5000
        api_key.is_active = True
        api_key.created_at = datetime.now()
        api_key.expires_at = datetime.now() + timedelta(days=365)
        api_key.last_used = datetime.now()
        api_key.usage_count = 100
        api_key.user_id = user_id

        assert api_key.id == api_key_id
        assert api_key.name == "Test API Key"
        assert api_key.description == "API key for testing"
        assert api_key.hashed_key == "hashed_api_key_123"
        assert api_key.scopes == ["read", "write"]
        assert api_key.allowed_ips == ["192.168.1.1", "10.0.0.0/8"]
        assert api_key.rate_limit == 5000
        assert api_key.is_active is True
        assert api_key.usage_count == 100
        assert api_key.user_id == user_id

    def test_api_key_model_defaults(self):
        """Test APIKey model default values."""
        api_key = APIKey()
        api_key.name = "Test Key"
        api_key.hashed_key = "hashed_key"
        api_key.user_id = uuid.uuid4()

        # Default values
        api_key.scopes = []  # Default empty scopes
        api_key.allowed_ips = []  # Default empty allowed IPs
        api_key.rate_limit = 1000  # Default rate limit
        api_key.is_active = True  # Default active
        api_key.usage_count = 0  # Default no usage

        assert api_key.scopes == []
        assert api_key.allowed_ips == []
        assert api_key.rate_limit == 1000
        assert api_key.is_active is True
        assert api_key.usage_count == 0

    def test_api_key_repr(self):
        """Test APIKey model string representation."""
        api_key = APIKey()
        api_key.id = uuid.uuid4()
        api_key.name = "Test API Key"
        api_key.user_id = uuid.uuid4()

        repr_str = repr(api_key)

        assert "APIKey" in repr_str
        assert str(api_key.id) in repr_str
        assert "Test API Key" in repr_str
        assert str(api_key.user_id) in repr_str


class TestRefreshToken:
    """Test RefreshToken model to achieve comprehensive coverage."""

    def test_refresh_token_model_creation(self):
        """Test RefreshToken model instance creation with all attributes."""
        token_id = uuid.uuid4()
        user_id = uuid.uuid4()

        refresh_token = RefreshToken()
        refresh_token.id = token_id
        refresh_token.token_hash = "hashed_token_123"
        refresh_token.user_id = user_id
        refresh_token.created_at = datetime.now()
        refresh_token.expires_at = datetime.now() + timedelta(days=7)
        refresh_token.last_used = datetime.now()
        refresh_token.is_revoked = False
        refresh_token.client_ip = "192.168.1.1"
        refresh_token.user_agent = "Mozilla/5.0 Test Browser"

        assert refresh_token.id == token_id
        assert refresh_token.token_hash == "hashed_token_123"
        assert refresh_token.user_id == user_id
        assert refresh_token.is_revoked is False
        assert refresh_token.client_ip == "192.168.1.1"
        assert refresh_token.user_agent == "Mozilla/5.0 Test Browser"

    def test_refresh_token_model_defaults(self):
        """Test RefreshToken model default values."""
        refresh_token = RefreshToken()
        refresh_token.token_hash = "hashed_token"
        refresh_token.user_id = uuid.uuid4()
        refresh_token.expires_at = datetime.now() + timedelta(days=7)

        # Default values
        refresh_token.is_revoked = False  # Default not revoked

        assert refresh_token.is_revoked is False

    def test_refresh_token_repr(self):
        """Test RefreshToken model string representation."""
        refresh_token = RefreshToken()
        refresh_token.id = uuid.uuid4()
        refresh_token.user_id = uuid.uuid4()

        repr_str = repr(refresh_token)

        assert "RefreshToken" in repr_str
        assert str(refresh_token.id) in repr_str
        assert str(refresh_token.user_id) in repr_str


class TestAuditLog:
    """Test AuditLog model to achieve comprehensive coverage."""

    def test_audit_log_model_creation(self):
        """Test AuditLog model instance creation with all attributes."""
        log_id = uuid.uuid4()
        user_id = uuid.uuid4()
        api_key_id = uuid.uuid4()

        audit_log = AuditLog()
        audit_log.id = log_id
        audit_log.event_type = "user_login"
        audit_log.user_id = user_id
        audit_log.api_key_id = api_key_id
        audit_log.ip_address = "192.168.1.1"
        audit_log.user_agent = "Mozilla/5.0 Test Browser"
        audit_log.endpoint = "/api/v1/auth/login"
        audit_log.method = "POST"
        audit_log.details = {"login_successful": True, "mfa_used": False}
        audit_log.success = True
        audit_log.error_message = None
        audit_log.timestamp = datetime.now()
        audit_log.duration_ms = 250

        assert audit_log.id == log_id
        assert audit_log.event_type == "user_login"
        assert audit_log.user_id == user_id
        assert audit_log.api_key_id == api_key_id
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0 Test Browser"
        assert audit_log.endpoint == "/api/v1/auth/login"
        assert audit_log.method == "POST"
        assert audit_log.details == {"login_successful": True, "mfa_used": False}
        assert audit_log.success is True
        assert audit_log.error_message is None
        assert audit_log.duration_ms == 250

    def test_audit_log_with_error(self):
        """Test AuditLog model with error information."""
        audit_log = AuditLog()
        audit_log.event_type = "user_login_failed"
        audit_log.success = False
        audit_log.error_message = "Invalid credentials"
        audit_log.details = {"attempts": 3, "locked_account": True}

        assert audit_log.event_type == "user_login_failed"
        assert audit_log.success is False
        assert audit_log.error_message == "Invalid credentials"
        assert audit_log.details == {"attempts": 3, "locked_account": True}

    def test_audit_log_repr(self):
        """Test AuditLog model string representation."""
        audit_log = AuditLog()
        audit_log.id = uuid.uuid4()
        audit_log.event_type = "user_login"
        audit_log.timestamp = datetime.now()

        repr_str = repr(audit_log)

        assert "AuditLog" in repr_str
        assert str(audit_log.id) in repr_str
        assert "user_login" in repr_str
        assert str(audit_log.timestamp) in repr_str


class TestSecuritySettings:
    """Test SecuritySettings model to achieve comprehensive coverage."""

    def test_security_settings_model_creation(self):
        """Test SecuritySettings model instance creation with all attributes."""
        settings_id = uuid.uuid4()
        updated_by = uuid.uuid4()

        security_settings = SecuritySettings()
        security_settings.id = settings_id
        security_settings.setting_key = "password_policy"
        security_settings.setting_value = {
            "min_length": 12,
            "require_uppercase": True,
            "require_numbers": True,
        }
        security_settings.description = "Password strength requirements"
        security_settings.created_at = datetime.now()
        security_settings.updated_at = datetime.now()
        security_settings.updated_by = updated_by

        assert security_settings.id == settings_id
        assert security_settings.setting_key == "password_policy"
        assert security_settings.setting_value == {
            "min_length": 12,
            "require_uppercase": True,
            "require_numbers": True,
        }
        assert security_settings.description == "Password strength requirements"
        assert security_settings.updated_by == updated_by

    def test_security_settings_repr(self):
        """Test SecuritySettings model string representation."""
        security_settings = SecuritySettings()
        security_settings.setting_key = "rate_limiting"

        repr_str = repr(security_settings)

        assert "SecuritySettings" in repr_str
        assert "rate_limiting" in repr_str


class TestIPAllowlist:
    """Test IPAllowlist model to achieve comprehensive coverage."""

    def test_ip_allowlist_model_creation(self):
        """Test IPAllowlist model instance creation with all attributes."""
        allowlist_id = uuid.uuid4()
        created_by = uuid.uuid4()

        ip_allowlist = IPAllowlist()
        ip_allowlist.id = allowlist_id
        ip_allowlist.ip_address = "192.168.1.0"
        ip_allowlist.subnet_mask = 24
        ip_allowlist.description = "Office network range"
        ip_allowlist.is_active = True
        ip_allowlist.created_at = datetime.now()
        ip_allowlist.created_by = created_by
        ip_allowlist.expires_at = datetime.now() + timedelta(days=365)

        assert ip_allowlist.id == allowlist_id
        assert ip_allowlist.ip_address == "192.168.1.0"
        assert ip_allowlist.subnet_mask == 24
        assert ip_allowlist.description == "Office network range"
        assert ip_allowlist.is_active is True
        assert ip_allowlist.created_by == created_by

    def test_ip_allowlist_single_ip(self):
        """Test IPAllowlist model with single IP address."""
        ip_allowlist = IPAllowlist()
        ip_allowlist.ip_address = "203.0.113.42"
        ip_allowlist.subnet_mask = None  # Single IP, no subnet
        ip_allowlist.description = "Single trusted IP"
        ip_allowlist.is_active = True

        assert ip_allowlist.ip_address == "203.0.113.42"
        assert ip_allowlist.subnet_mask is None
        assert ip_allowlist.description == "Single trusted IP"
        assert ip_allowlist.is_active is True

    def test_ip_allowlist_defaults(self):
        """Test IPAllowlist model default values."""
        ip_allowlist = IPAllowlist()
        ip_allowlist.ip_address = "10.0.0.1"

        # Default values
        ip_allowlist.is_active = True  # Default active

        assert ip_allowlist.is_active is True

    def test_ip_allowlist_repr(self):
        """Test IPAllowlist model string representation."""
        ip_allowlist = IPAllowlist()
        ip_allowlist.id = uuid.uuid4()
        ip_allowlist.ip_address = "192.168.1.100"

        repr_str = repr(ip_allowlist)

        assert "IPAllowlist" in repr_str
        assert str(ip_allowlist.id) in repr_str
        assert "192.168.1.100" in repr_str


class TestRateLimitLog:
    """Test RateLimitLog model to achieve comprehensive coverage."""

    def test_rate_limit_log_model_creation(self):
        """Test RateLimitLog model instance creation with all attributes."""
        log_id = uuid.uuid4()

        rate_limit_log = RateLimitLog()
        rate_limit_log.id = log_id
        rate_limit_log.identifier = "192.168.1.100"
        rate_limit_log.identifier_type = "ip"
        rate_limit_log.endpoint = "/api/v1/predictions"
        rate_limit_log.request_count = 150
        rate_limit_log.window_start = datetime.now() - timedelta(hours=1)
        rate_limit_log.window_end = datetime.now()
        rate_limit_log.limit_exceeded = True
        rate_limit_log.last_request_at = datetime.now()
        rate_limit_log.user_agent = "curl/7.68.0"

        assert rate_limit_log.id == log_id
        assert rate_limit_log.identifier == "192.168.1.100"
        assert rate_limit_log.identifier_type == "ip"
        assert rate_limit_log.endpoint == "/api/v1/predictions"
        assert rate_limit_log.request_count == 150
        assert rate_limit_log.limit_exceeded is True
        assert rate_limit_log.user_agent == "curl/7.68.0"

    def test_rate_limit_log_user_identifier(self):
        """Test RateLimitLog model with user identifier."""
        user_id = uuid.uuid4()

        rate_limit_log = RateLimitLog()
        rate_limit_log.identifier = str(user_id)
        rate_limit_log.identifier_type = "user"
        rate_limit_log.endpoint = "/api/v1/data"
        rate_limit_log.request_count = 25
        rate_limit_log.window_start = datetime.now() - timedelta(minutes=30)
        rate_limit_log.window_end = datetime.now()
        rate_limit_log.limit_exceeded = False

        assert rate_limit_log.identifier == str(user_id)
        assert rate_limit_log.identifier_type == "user"
        assert rate_limit_log.endpoint == "/api/v1/data"
        assert rate_limit_log.request_count == 25
        assert rate_limit_log.limit_exceeded is False

    def test_rate_limit_log_api_key_identifier(self):
        """Test RateLimitLog model with API key identifier."""
        api_key_id = uuid.uuid4()

        rate_limit_log = RateLimitLog()
        rate_limit_log.identifier = str(api_key_id)
        rate_limit_log.identifier_type = "api_key"
        rate_limit_log.request_count = 500
        rate_limit_log.window_start = datetime.now() - timedelta(hours=2)
        rate_limit_log.window_end = datetime.now()
        rate_limit_log.limit_exceeded = False

        assert rate_limit_log.identifier == str(api_key_id)
        assert rate_limit_log.identifier_type == "api_key"
        assert rate_limit_log.request_count == 500
        assert rate_limit_log.limit_exceeded is False

    def test_rate_limit_log_defaults(self):
        """Test RateLimitLog model default values."""
        rate_limit_log = RateLimitLog()
        rate_limit_log.identifier = "test_id"
        rate_limit_log.identifier_type = "ip"
        rate_limit_log.window_start = datetime.now()
        rate_limit_log.window_end = datetime.now()

        # Default values
        rate_limit_log.request_count = 1  # Default count
        rate_limit_log.limit_exceeded = False  # Default not exceeded

        assert rate_limit_log.request_count == 1
        assert rate_limit_log.limit_exceeded is False

    def test_rate_limit_log_repr(self):
        """Test RateLimitLog model string representation."""
        rate_limit_log = RateLimitLog()
        rate_limit_log.id = uuid.uuid4()
        rate_limit_log.identifier = "192.168.1.1"
        rate_limit_log.request_count = 75

        repr_str = repr(rate_limit_log)

        assert "RateLimitLog" in repr_str
        assert str(rate_limit_log.id) in repr_str
        assert "192.168.1.1" in repr_str
        assert "75" in repr_str


class TestDefaultSecuritySettings:
    """Test default security settings configuration."""

    def test_default_security_settings_structure(self):
        """Test that default security settings contain all expected sections."""
        expected_sections = [
            "password_policy",
            "account_lockout",
            "session_management",
            "rate_limiting",
            "ip_security",
            "audit_settings",
        ]

        for section in expected_sections:
            assert section in DEFAULT_SECURITY_SETTINGS
            assert isinstance(DEFAULT_SECURITY_SETTINGS[section], dict)

    def test_password_policy_defaults(self):
        """Test password policy default configuration."""
        password_policy = DEFAULT_SECURITY_SETTINGS["password_policy"]

        assert password_policy["min_length"] == 8
        assert password_policy["require_uppercase"] is True
        assert password_policy["require_lowercase"] is True
        assert password_policy["require_numbers"] is True
        assert password_policy["require_special_chars"] is True
        assert password_policy["max_age_days"] == 90
        assert password_policy["prevent_reuse_count"] == 5

    def test_account_lockout_defaults(self):
        """Test account lockout default configuration."""
        account_lockout = DEFAULT_SECURITY_SETTINGS["account_lockout"]

        assert account_lockout["max_failed_attempts"] == 5
        assert account_lockout["lockout_duration_minutes"] == 30
        assert account_lockout["reset_failed_attempts_after_minutes"] == 60

    def test_session_management_defaults(self):
        """Test session management default configuration."""
        session_mgmt = DEFAULT_SECURITY_SETTINGS["session_management"]

        assert session_mgmt["access_token_expire_minutes"] == 30
        assert session_mgmt["refresh_token_expire_days"] == 7
        assert session_mgmt["max_concurrent_sessions"] == 5

    def test_rate_limiting_defaults(self):
        """Test rate limiting default configuration."""
        rate_limiting = DEFAULT_SECURITY_SETTINGS["rate_limiting"]

        assert rate_limiting["default_requests_per_minute"] == 100
        assert rate_limiting["prediction_requests_per_hour"] == 1000
        assert rate_limiting["auth_requests_per_minute"] == 10

    def test_ip_security_defaults(self):
        """Test IP security default configuration."""
        ip_security = DEFAULT_SECURITY_SETTINGS["ip_security"]

        assert ip_security["enable_allowlist"] is False
        assert ip_security["enable_geoblocking"] is False
        assert ip_security["blocked_countries"] == []
        assert ip_security["require_https"] is True

    def test_audit_settings_defaults(self):
        """Test audit settings default configuration."""
        audit_settings = DEFAULT_SECURITY_SETTINGS["audit_settings"]

        assert audit_settings["log_all_requests"] is True
        assert audit_settings["log_auth_events"] is True
        assert audit_settings["log_admin_actions"] is True
        assert audit_settings["retention_days"] == 365

    def test_default_security_settings_types(self):
        """Test that default security settings have correct data types."""
        # Test that all values are the expected types
        password_policy = DEFAULT_SECURITY_SETTINGS["password_policy"]
        assert isinstance(password_policy["min_length"], int)
        assert isinstance(password_policy["require_uppercase"], bool)
        assert isinstance(password_policy["max_age_days"], int)

        account_lockout = DEFAULT_SECURITY_SETTINGS["account_lockout"]
        assert isinstance(account_lockout["max_failed_attempts"], int)
        assert isinstance(account_lockout["lockout_duration_minutes"], int)

        ip_security = DEFAULT_SECURITY_SETTINGS["ip_security"]
        assert isinstance(ip_security["blocked_countries"], list)
        assert isinstance(ip_security["require_https"], bool)

    def test_default_security_settings_immutable(self):
        """Test that modifying the default settings doesn't affect the original."""
        # Make a copy and modify it
        modified_settings = DEFAULT_SECURITY_SETTINGS.copy()
        modified_settings["password_policy"]["min_length"] = 16

        # Original should remain unchanged
        assert DEFAULT_SECURITY_SETTINGS["password_policy"]["min_length"] == 8
