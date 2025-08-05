"""
Security Module for Malaria Prediction API.

This module provides comprehensive security features including:
- JWT token management and validation
- Password hashing and verification
- User authentication and authorization
- API key management and validation
- Security utilities and helpers

Designed for health data applications with HIPAA-level security compliance.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-super-secret-key-change-in-production"  # Should be from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Data encryption for sensitive fields
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)


class TokenData(BaseModel):
    """Token payload data structure."""

    sub: str  # subject (user ID or API key ID)
    type: str  # "access" or "refresh" or "api_key"
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    scopes: list[str] = Field(default_factory=list)  # permissions/scopes


class UserCreate(BaseModel):
    """User creation request model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=100)
    organization: str | None = Field(None, max_length=100)
    role: str = Field(default="user")


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""

    id: str
    username: str
    email: str
    full_name: str | None
    organization: str | None
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None


class APIKeyCreate(BaseModel):
    """API key creation request model."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    rate_limit: int = Field(default=1000, ge=1, le=10000)  # requests per hour
    allowed_ips: list[str] = Field(default_factory=list)


class APIKeyResponse(BaseModel):
    """API key response model (excludes key value)."""

    id: str
    name: str
    description: str | None
    scopes: list[str]
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
    last_used: datetime | None
    usage_count: int
    rate_limit: int
    allowed_ips: list[str]


class Token(BaseModel):
    """Authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SecurityConfig:
    """Security configuration and utilities."""

    # Available scopes for API access
    SCOPES = {
        "read:health": "Read health check endpoints",
        "read:predictions": "Read prediction endpoints",
        "write:predictions": "Create prediction requests",
        "read:models": "Read model information",
        "write:models": "Manage models",
        "read:admin": "Read administrative data",
        "write:admin": "Administrative operations",
        "read:audit": "Read audit logs",
        "write:audit": "Write audit logs",
    }

    # Role-based default scopes
    ROLE_SCOPES = {
        "admin": list(SCOPES.keys()),
        "researcher": [
            "read:health",
            "read:predictions",
            "write:predictions",
            "read:models",
            "read:audit",
        ],
        "user": ["read:health", "read:predictions", "write:predictions"],
        "readonly": ["read:health", "read:predictions", "read:models"],
    }


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data for storage."""
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "access"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_api_key_token(
    api_key_id: str, scopes: list[str], expires_at: datetime | None = None
) -> str:
    """Create a JWT token for API key authentication."""
    to_encode = {
        "sub": api_key_id,
        "scopes": scopes,
        "type": "api_key",
        "iat": datetime.now(UTC),
    }

    # Set expiration - either provided or default to 1 year for API keys
    if expires_at:
        to_encode["exp"] = expires_at
    else:
        # Default API key tokens expire in 1 year
        to_encode["exp"] = datetime.now(UTC) + timedelta(days=365)

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData | None:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Validate required fields
        sub = payload.get("sub")
        token_type = payload.get("type")
        exp = payload.get("exp")
        iat = payload.get("iat")

        if not all([sub, token_type, exp, iat]):
            logger.warning("Token missing required fields")
            return None

        # Check if token is expired
        if datetime.fromtimestamp(exp, UTC) < datetime.now(UTC):
            logger.warning("Token has expired")
            return None

        scopes = payload.get("scopes", [])

        return TokenData(sub=sub, type=token_type, exp=exp, iat=iat, scopes=scopes)

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def generate_api_key() -> str:
    """Generate a secure API key."""
    import secrets
    import string

    # Generate a 64-character API key
    alphabet = string.ascii_letters + string.digits
    api_key = "".join(secrets.choice(alphabet) for _ in range(64))

    return f"mp_{api_key}"  # Add prefix for identification


def validate_scopes(required_scopes: list[str], user_scopes: list[str]) -> bool:
    """Check if user has required scopes."""
    return all(scope in user_scopes for scope in required_scopes)


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    import html
    import re

    # HTML escape
    sanitized = html.escape(data)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r"<script.*?</script>",
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"onload=",
        r"onerror=",
        r"onclick=",
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    import hashlib

    # Use SHA-256 for API key hashing (faster than bcrypt for high-frequency checks)
    return hashlib.sha256(api_key.encode()).hexdigest()


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    import hmac

    return hmac.compare_digest(val1, val2)


class SecurityAuditor:
    """Security audit utilities."""

    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: str | None = None,
        api_key_id: str | None = None,
        ip_address: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Log security-related events for audit purposes."""
        audit_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "api_key_id": api_key_id,
            "ip_address": ip_address,
            "details": details or {},
        }

        # In production, this should write to a secure audit log
        logger.info(f"SECURITY_AUDIT: {audit_data}")

    @staticmethod
    def detect_suspicious_activity(
        user_id: str, ip_address: str, endpoint: str
    ) -> bool:
        """Basic suspicious activity detection."""
        # This is a simplified implementation
        # In production, implement more sophisticated detection

        # Check for rapid requests (basic rate limiting detection)
        # Check for unusual geographic patterns
        # Check for unusual endpoint access patterns

        # For now, just log the activity
        SecurityAuditor.log_security_event(
            "api_access",
            user_id=user_id,
            ip_address=ip_address,
            details={"endpoint": endpoint},
        )

        return False  # No suspicious activity detected in this basic implementation
