"""
Authentication Router for Malaria Prediction API.

This module provides authentication endpoints including user registration,
login, logout, token refresh, and API key management.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.security_models import APIKey, RefreshToken, User
from ...database.session import get_session
from ..auth import authenticate_user, get_current_user, log_audit_event, require_role
from ..security import (
    APIKeyCreate,
    APIKeyResponse,
    SecurityAuditor,
    Token,
    UserCreate,
    UserResponse,
    create_access_token,
    create_refresh_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        session: Database session
        request: FastAPI request object

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If registration fails or user already exists
    """
    try:
        # Check if username or email already exists (using ORM to prevent SQL injection)
        existing_user_result = await session.execute(
            select(User.id).where(
                or_(
                    User.username == user_data.username,
                    User.email == user_data.email
                )
            )
        )
        existing_user = existing_user_result.scalar_one_or_none()

        if existing_user:
            SecurityAuditor.log_security_event(
                "registration_attempt_duplicate",
                ip_address=request.client.host if request.client else None,
                details={"username": user_data.username, "email": user_data.email},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered",
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            organization=user_data.organization,
            role=user_data.role,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Log successful registration
        SecurityAuditor.log_security_event(
            "user_registered",
            user_id=str(new_user.id),
            ip_address=request.client.host if request.client else None,
            details={
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role,
            },
        )

        return UserResponse.model_validate({
            'id': str(new_user.id),
            'username': new_user.username,
            'email': new_user.email,
            'full_name': new_user.full_name,
            'organization': new_user.organization,
            'role': new_user.role,
            'is_active': new_user.is_active,
            'created_at': new_user.created_at,
            'last_login': new_user.last_login,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from e


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> Token:
    """
    Authenticate user and return access/refresh tokens.

    Args:
        form_data: OAuth2 password form data (username/password)
        session: Database session
        request: FastAPI request object

    Returns:
        Token: Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = await authenticate_user(
        form_data.username, form_data.password, session, request
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "scopes": ["user"]})

    # Create refresh token
    refresh_token = create_refresh_token(str(user.id))

    # Store refresh token in database
    refresh_token_obj = RefreshToken(
        token_hash=hash_api_key(refresh_token),  # Reuse hash function
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    session.add(refresh_token_obj)
    await session.commit()

    # Log audit event
    await log_audit_event(
        "user_login",
        session,
        user_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        endpoint="/auth/login",
        method="POST",
        success=True,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token string
        session: Database session
        request: FastAPI request object

    Returns:
        Token: New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        # Verify refresh token
        token_data = verify_token(refresh_token)
        if not token_data or token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Check if refresh token exists in database and is not revoked (using ORM to prevent SQL injection)
        token_hash = hash_api_key(refresh_token)
        result = await session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False,  # noqa: E712
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            SecurityAuditor.log_security_event(
                "invalid_refresh_token_attempt",
                ip_address=request.client.host if request.client else None,
                details={"token_data": str(token_data.sub)},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired",
            )

        # Get user (using ORM to prevent SQL injection)
        user_result = await session.execute(
            select(User).where(
                and_(
                    User.id == stored_token.user_id,
                    User.is_active == True  # noqa: E712
                )
            )
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "scopes": ["user"]}
        )

        # Create new refresh token
        new_refresh_token = create_refresh_token(str(user.id))

        # Revoke old refresh token (using ORM to prevent SQL injection)
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == stored_token.id)
            .values(is_revoked=True)
        )

        # Store new refresh token
        new_refresh_token_obj = RefreshToken(
            token_hash=hash_api_key(new_refresh_token),
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        session.add(new_refresh_token_obj)
        await session.commit()

        # Log audit event
        await log_audit_event(
            "token_refreshed",
            session,
            user_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint="/auth/refresh",
            method="POST",
            success=True,
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        ) from e


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> dict[str, str]:
    """
    Logout user and revoke refresh tokens.

    Args:
        current_user: Currently authenticated user
        session: Database session
        request: FastAPI request object

    Returns:
        dict: Logout confirmation message
    """
    try:
        # Revoke all active refresh tokens for the user (using ORM to prevent SQL injection)
        await session.execute(
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == current_user.id,
                    RefreshToken.is_revoked == False  # noqa: E712
                )
            )
            .values(is_revoked=True)
        )
        await session.commit()

        # Log audit event
        await log_audit_event(
            "user_logout",
            session,
            user_id=str(current_user.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint="/auth/logout",
            method="POST",
            success=True,
        )

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """
    Get current user information.

    Args:
        current_user: Currently authenticated user

    Returns:
        UserResponse: Current user information
    """
    return UserResponse.model_validate({
        'id': str(current_user.id),
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'organization': current_user.organization,
        'role': current_user.role,
        'is_active': current_user.is_active,
        'created_at': current_user.created_at,
        'last_login': current_user.last_login,
    })


@router.post(
    "/api-keys", response_model=dict[str, str], status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: Annotated[User, Depends(require_role("admin", "researcher"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> dict[str, str]:
    """
    Create a new API key for the current user.

    Args:
        api_key_data: API key creation data
        current_user: Currently authenticated user
        session: Database session
        request: FastAPI request object

    Returns:
        dict: API key information including the key value (only shown once)

    Raises:
        HTTPException: If API key creation fails
    """
    try:
        # Generate API key
        api_key = generate_api_key()
        hashed_key = hash_api_key(api_key)

        # Create API key object
        new_api_key = APIKey(
            name=api_key_data.name,
            description=api_key_data.description,
            hashed_key=hashed_key,
            scopes=api_key_data.scopes,
            allowed_ips=api_key_data.allowed_ips,
            rate_limit=api_key_data.rate_limit,
            expires_at=api_key_data.expires_at,
            user_id=current_user.id,
        )

        session.add(new_api_key)
        await session.commit()
        await session.refresh(new_api_key)

        # Log audit event
        await log_audit_event(
            "api_key_created",
            session,
            user_id=str(current_user.id),
            api_key_id=str(new_api_key.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint="/auth/api-keys",
            method="POST",
            details={"api_key_name": new_api_key.name, "scopes": new_api_key.scopes},
            success=True,
        )

        return {
            "api_key": api_key,  # Only shown once
            "id": str(new_api_key.id),
            "name": new_api_key.name,  # type: ignore[dict-item]
            "message": "API key created successfully. Save it securely - it won't be shown again.",
        }

    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed",
        ) from e


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[APIKeyResponse]:
    """
    List all API keys for the current user.

    Args:
        current_user: Currently authenticated user
        session: Database session

    Returns:
        list[APIKeyResponse]: List of user's API keys (excluding key values)
    """
    try:
        # Get API keys using ORM to prevent SQL injection
        result = await session.execute(
            select(APIKey)
            .where(APIKey.user_id == current_user.id)
            .order_by(APIKey.created_at.desc())
        )
        api_keys = result.scalars().all()

        return [
            APIKeyResponse(
                id=str(api_key.id),
                name=api_key.name,  # type: ignore[arg-type]
                description=api_key.description,  # type: ignore[arg-type]
                scopes=api_key.scopes,  # type: ignore[arg-type]
                is_active=api_key.is_active,  # type: ignore[arg-type]
                created_at=api_key.created_at,  # type: ignore[arg-type]
                expires_at=api_key.expires_at,  # type: ignore[arg-type]
                last_used=api_key.last_used,  # type: ignore[arg-type]
                usage_count=api_key.usage_count,  # type: ignore[arg-type]
                rate_limit=api_key.rate_limit,  # type: ignore[arg-type]
                allowed_ips=api_key.allowed_ips,  # type: ignore[arg-type]
            )
            for api_key in api_keys
        ]

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys",
        ) from e


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> dict[str, str]:
    """
    Revoke (deactivate) an API key.

    Args:
        api_key_id: ID of the API key to revoke
        current_user: Currently authenticated user
        session: Database session
        request: FastAPI request object

    Returns:
        dict: Revocation confirmation message

    Raises:
        HTTPException: If API key not found or access denied
    """
    try:
        # Check if API key exists and belongs to current user (using ORM to prevent SQL injection)
        result = await session.execute(
            select(APIKey).where(
                and_(
                    APIKey.id == api_key_id,
                    APIKey.user_id == current_user.id
                )
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        # Deactivate API key (using ORM to prevent SQL injection)
        await session.execute(
            update(APIKey)
            .where(APIKey.id == api_key_id)
            .values(is_active=False)
        )
        await session.commit()

        # Log audit event
        await log_audit_event(
            "api_key_revoked",
            session,
            user_id=str(current_user.id),
            api_key_id=api_key_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint=f"/auth/api-keys/{api_key_id}",
            method="DELETE",
            details={"api_key_name": api_key.name},
            success=True,
        )

        return {"message": "API key revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed",
        ) from e
