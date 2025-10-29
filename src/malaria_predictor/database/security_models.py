"""
Security Database Models for Malaria Prediction API.

This module defines database models for user management, API key management,
and audit logging to support comprehensive security features.
"""

import copy
import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .models import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    organization = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False, default="user")

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Security settings
    require_password_change = Column(Boolean, default=False)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class APIKey(Base):
    """API key model for external service authentication."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    hashed_key = Column(String(255), nullable=False, unique=True, index=True)

    # Permissions and access control
    scopes = Column(JSON, nullable=False, default=list)
    allowed_ips = Column(JSON, nullable=False, default=list)
    rate_limit = Column(Integer, nullable=False, default=1000)  # requests per hour

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", back_populates="api_keys")
    audit_logs = relationship("AuditLog", back_populates="api_key")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class RefreshToken(Base):
    """Refresh token model for JWT token management."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Token metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False)

    # Client information
    client_ip = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class AuditLog(Base):
    """Audit log model for security and compliance tracking."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)

    # Actor information
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    api_key_id = Column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True, index=True
    )

    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)

    # Event details
    details = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    duration_ms = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    api_key = relationship("APIKey", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', timestamp={self.timestamp})>"


class SecuritySettings(Base):
    """Global security settings and configuration."""

    __tablename__ = "security_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<SecuritySettings(key='{self.setting_key}')>"


class IPAllowlist(Base):
    """IP allowlist for enhanced security."""

    __tablename__ = "ip_allowlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 compatible
    subnet_mask = Column(Integer, nullable=True)  # For CIDR notation
    description = Column(Text, nullable=True)

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<IPAllowlist(id={self.id}, ip_address='{self.ip_address}')>"


class RateLimitLog(Base):
    """Rate limiting tracking for abuse prevention."""

    __tablename__ = "rate_limit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(
        String(255), nullable=False, index=True
    )  # IP, user_id, or api_key_id
    identifier_type = Column(String(20), nullable=False)  # 'ip', 'user', 'api_key'
    endpoint = Column(String(255), nullable=True)

    # Rate limiting data
    request_count = Column(Integer, nullable=False, default=1)
    window_start = Column(DateTime(timezone=True), nullable=False, index=True)
    window_end = Column(DateTime(timezone=True), nullable=False)
    limit_exceeded = Column(Boolean, default=False)

    # Request details
    last_request_at = Column(DateTime(timezone=True), server_default=func.now())
    user_agent = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RateLimitLog(id={self.id}, identifier='{self.identifier}', count={self.request_count})>"


# Default security settings (private, use get_default_security_settings() for access)
_DEFAULT_SECURITY_SETTINGS = {
    "password_policy": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "max_age_days": 90,
        "prevent_reuse_count": 5,
    },
    "account_lockout": {
        "max_failed_attempts": 5,
        "lockout_duration_minutes": 30,
        "reset_failed_attempts_after_minutes": 60,
    },
    "session_management": {
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7,
        "max_concurrent_sessions": 5,
    },
    "rate_limiting": {
        "default_requests_per_minute": 100,
        "prediction_requests_per_hour": 1000,
        "auth_requests_per_minute": 10,
    },
    "ip_security": {
        "enable_allowlist": False,
        "enable_geoblocking": False,
        "blocked_countries": [],
        "require_https": True,
    },
    "audit_settings": {
        "log_all_requests": True,
        "log_auth_events": True,
        "log_admin_actions": True,
        "retention_days": 365,
    },
}


def get_default_security_settings() -> dict:
    """
    Get a deep copy of the default security settings.

    Returns:
        dict: Deep copy of default security settings
    """
    return copy.deepcopy(_DEFAULT_SECURITY_SETTINGS)


class _DefaultSecuritySettingsProxy:
    """Proxy class that always returns a fresh deep copy of settings."""

    def __getitem__(self, key: str) -> Any:
        return get_default_security_settings()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("DEFAULT_SECURITY_SETTINGS is read-only")

    def __contains__(self, key: str) -> bool:
        return key in get_default_security_settings()

    def get(self, key: str, default: Any = None) -> Any:
        return get_default_security_settings().get(key, default)

    def keys(self) -> Any:
        return get_default_security_settings().keys()

    def values(self) -> Any:
        return get_default_security_settings().values()

    def items(self) -> Any:
        return get_default_security_settings().items()

    def copy(self) -> dict[str, Any]:
        return get_default_security_settings()


# Backward compatibility - this always returns fresh copies to prevent mutation
DEFAULT_SECURITY_SETTINGS = _DefaultSecuritySettingsProxy()
