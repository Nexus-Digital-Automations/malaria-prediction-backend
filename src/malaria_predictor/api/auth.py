"""
Authentication and Authorization Module for Malaria Prediction API.

This module provides comprehensive authentication and authorization functionality
including JWT token management, user authentication, API key validation,
and role-based access control.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.security_models import APIKey, AuditLog, User
from ..database.session import get_session
from .security import (
    SecurityAuditor,
    hash_api_key,
    validate_scopes,
    verify_password,
    verify_token,
)

logger = logging.getLogger(__name__)

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
api_key_scheme = HTTPBearer(scheme_name="API Key")


class AuthenticationError(HTTPException):
    """Custom authentication error."""

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT access token
        session: Database session
        request: FastAPI request object

    Returns:
        User: Authenticated user object

    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    # Verify and decode token
    token_data = verify_token(token)
    if not token_data or token_data.type != "access":
        SecurityAuditor.log_security_event(
            "invalid_token_attempt",
            ip_address=request.client.host if request.client else None,
            details={"token_type": token_data.type if token_data else "invalid"},
        )
        raise AuthenticationError("Invalid token")

    # Get user from database
    try:
        result = await session.execute(
            f"SELECT * FROM users WHERE id = '{token_data.sub}' AND is_active = true"
        )
        user_data = result.fetchone()

        if not user_data:
            SecurityAuditor.log_security_event(
                "user_not_found",
                user_id=token_data.sub,
                ip_address=request.client.host if request.client else None,
            )
            raise AuthenticationError("User not found")

        # Convert to User object
        user = User(
            id=user_data.id,
            username=user_data.username,
            email=user_data.email,
            hashed_password=user_data.hashed_password,
            full_name=user_data.full_name,
            organization=user_data.organization,
            role=user_data.role,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_at=user_data.created_at,
            last_login=user_data.last_login,
        )

        # Update last login
        await session.execute(
            f"UPDATE users SET last_login = '{datetime.utcnow()}' WHERE id = '{user.id}'"
        )
        await session.commit()

        # Log successful authentication
        SecurityAuditor.log_security_event(
            "user_authenticated",
            user_id=str(user.id),
            ip_address=request.client.host if request.client else None,
        )

        return user

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise AuthenticationError("Authentication failed") from e


async def get_current_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(api_key_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> APIKey:
    """
    Get the current authenticated API key.

    Args:
        credentials: HTTP Bearer credentials
        session: Database session
        request: FastAPI request object

    Returns:
        APIKey: Authenticated API key object

    Raises:
        AuthenticationError: If API key is invalid or not found
    """
    api_key = credentials.credentials

    # Hash the provided API key
    hashed_key = hash_api_key(api_key)

    try:
        # Get API key from database
        result = await session.execute(
            f"SELECT * FROM api_keys WHERE hashed_key = '{hashed_key}' AND is_active = true"
        )
        api_key_data = result.fetchone()

        if not api_key_data:
            SecurityAuditor.log_security_event(
                "invalid_api_key_attempt",
                ip_address=request.client.host if request.client else None,
                details={
                    "api_key_prefix": api_key[:10] if len(api_key) > 10 else api_key
                },
            )
            raise AuthenticationError("Invalid API key")

        # Check if API key is expired
        if api_key_data.expires_at and api_key_data.expires_at < datetime.utcnow():
            SecurityAuditor.log_security_event(
                "expired_api_key_attempt",
                api_key_id=str(api_key_data.id),
                ip_address=request.client.host if request.client else None,
            )
            raise AuthenticationError("API key expired")

        # Check IP allowlist if configured
        if api_key_data.allowed_ips:
            client_ip = request.client.host if request.client else None
            if client_ip and client_ip not in api_key_data.allowed_ips:
                SecurityAuditor.log_security_event(
                    "api_key_ip_blocked",
                    api_key_id=str(api_key_data.id),
                    ip_address=client_ip,
                )
                raise AuthenticationError("IP address not allowed")

        # Convert to APIKey object
        api_key_obj = APIKey(
            id=api_key_data.id,
            name=api_key_data.name,
            description=api_key_data.description,
            hashed_key=api_key_data.hashed_key,
            scopes=api_key_data.scopes,
            allowed_ips=api_key_data.allowed_ips,
            rate_limit=api_key_data.rate_limit,
            is_active=api_key_data.is_active,
            created_at=api_key_data.created_at,
            expires_at=api_key_data.expires_at,
            last_used=api_key_data.last_used,
            usage_count=api_key_data.usage_count,
            user_id=api_key_data.user_id,
        )

        # Update usage statistics
        await session.execute(
            f"UPDATE api_keys SET last_used = '{datetime.utcnow()}', "
            f"usage_count = usage_count + 1 WHERE id = '{api_key_obj.id}'"
        )
        await session.commit()

        # Log successful API key authentication
        SecurityAuditor.log_security_event(
            "api_key_authenticated",
            api_key_id=str(api_key_obj.id),
            ip_address=request.client.host if request.client else None,
        )

        return api_key_obj

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise AuthenticationError("API key validation failed") from e


async def authenticate_user(
    username: str,
    password: str,
    session: AsyncSession,
    request: Request,
) -> User | None:
    """
    Authenticate a user with username and password.

    Args:
        username: Username or email
        password: Plain text password
        session: Database session
        request: FastAPI request object

    Returns:
        User: Authenticated user or None if authentication fails
    """
    try:
        # Get user by username or email
        result = await session.execute(
            f"SELECT * FROM users WHERE (username = '{username}' OR email = '{username}') "
            f"AND is_active = true"
        )
        user_data = result.fetchone()

        if not user_data:
            SecurityAuditor.log_security_event(
                "login_attempt_invalid_user",
                ip_address=request.client.host if request.client else None,
                details={"username": username},
            )
            return None

        # Check if account is locked
        if user_data.locked_until and user_data.locked_until > datetime.utcnow():
            SecurityAuditor.log_security_event(
                "login_attempt_locked_account",
                user_id=str(user_data.id),
                ip_address=request.client.host if request.client else None,
            )
            return None

        # Verify password
        if not verify_password(password, user_data.hashed_password):
            # Increment failed login attempts
            failed_attempts = user_data.failed_login_attempts + 1
            locked_until = None

            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                locked_until = datetime.utcnow() + timedelta(minutes=30)

            locked_until_value = "NULL" if locked_until is None else f"'{locked_until}'"
            await session.execute(
                f"UPDATE users SET failed_login_attempts = {failed_attempts}, "
                f"locked_until = {locked_until_value} "
                f"WHERE id = '{user_data.id}'"
            )
            await session.commit()

            SecurityAuditor.log_security_event(
                "login_attempt_invalid_password",
                user_id=str(user_data.id),
                ip_address=request.client.host if request.client else None,
                details={"failed_attempts": failed_attempts},
            )
            return None

        # Reset failed login attempts on successful authentication
        await session.execute(
            f"UPDATE users SET failed_login_attempts = 0, locked_until = NULL, "
            f"last_login = '{datetime.utcnow()}' WHERE id = '{user_data.id}'"
        )
        await session.commit()

        # Convert to User object
        user = User(
            id=user_data.id,
            username=user_data.username,
            email=user_data.email,
            hashed_password=user_data.hashed_password,
            full_name=user_data.full_name,
            organization=user_data.organization,
            role=user_data.role,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_at=user_data.created_at,
            last_login=datetime.utcnow(),
        )

        SecurityAuditor.log_security_event(
            "successful_login",
            user_id=str(user.id),
            ip_address=request.client.host if request.client else None,
        )

        return user

    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None


def require_scopes(*required_scopes: str):
    """
    Dependency factory for requiring specific scopes.

    Args:
        *required_scopes: Required permission scopes

    Returns:
        Dependency function that validates scopes
    """

    def scope_dependency(
        current_user: Annotated[User, Depends(get_current_user)] = None,
        current_api_key: Annotated[APIKey, Depends(get_current_api_key)] = None,
    ) -> User | APIKey:
        """Validate that the authenticated entity has required scopes."""

        # Determine authentication method and scopes
        if current_user:
            # User authentication - get scopes from role
            from .security import SecurityConfig

            user_scopes = SecurityConfig.ROLE_SCOPES.get(current_user.role, [])

            if not validate_scopes(list(required_scopes), user_scopes):
                SecurityAuditor.log_security_event(
                    "insufficient_permissions",
                    user_id=str(current_user.id),
                    details={
                        "required_scopes": list(required_scopes),
                        "user_scopes": user_scopes,
                    },
                )
                raise AuthorizationError(
                    f"Missing required permissions: {', '.join(required_scopes)}"
                )

            return current_user

        elif current_api_key:
            # API key authentication - check explicit scopes
            if not validate_scopes(list(required_scopes), current_api_key.scopes):
                SecurityAuditor.log_security_event(
                    "insufficient_permissions",
                    api_key_id=str(current_api_key.id),
                    details={
                        "required_scopes": list(required_scopes),
                        "api_key_scopes": current_api_key.scopes,
                    },
                )
                raise AuthorizationError(
                    f"Missing required permissions: {', '.join(required_scopes)}"
                )

            return current_api_key

        else:
            raise AuthenticationError("Authentication required")

    return scope_dependency


def require_role(*allowed_roles: str):
    """
    Dependency factory for requiring specific user roles.

    Args:
        *allowed_roles: Allowed user roles

    Returns:
        Dependency function that validates user role
    """

    def role_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """Validate that the authenticated user has an allowed role."""

        if current_user.role not in allowed_roles:
            SecurityAuditor.log_security_event(
                "insufficient_role",
                user_id=str(current_user.id),
                details={
                    "required_roles": list(allowed_roles),
                    "user_role": current_user.role,
                },
            )
            raise AuthorizationError(
                f"Role '{current_user.role}' not authorized. "
                f"Required: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_dependency


async def log_audit_event(
    event_type: str,
    session: AsyncSession,
    user_id: str | None = None,
    api_key_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    details: dict | None = None,
    success: bool | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """
    Log an audit event to the database.

    Args:
        event_type: Type of event being logged
        session: Database session
        user_id: User ID if applicable
        api_key_id: API key ID if applicable
        ip_address: Client IP address
        user_agent: Client user agent
        endpoint: API endpoint accessed
        method: HTTP method
        details: Additional event details
        success: Whether the operation was successful
        error_message: Error message if applicable
        duration_ms: Request duration in milliseconds
    """
    try:
        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            api_key_id=api_key_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            details=details,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
        )

        session.add(audit_log)
        await session.commit()

    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        # Don't raise exception to avoid breaking the main request
