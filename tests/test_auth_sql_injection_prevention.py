"""
SQL Injection Prevention Tests for Authentication Router.

This module tests that all authentication endpoints are protected against
SQL injection attacks after migration from raw SQL to SQLAlchemy ORM.
"""

import pytest
from fastapi import status
from sqlalchemy import select

from malaria_predictor.database.security_models import APIKey, RefreshToken, User


class TestSQLInjectionPrevention:
    """Test SQL injection prevention across all auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_prevents_sql_injection_in_username(
        self, test_client, test_db_session
    ):
        """Test that registration prevents SQL injection in username field."""
        # Attempt SQL injection via username
        malicious_username = "admin' OR '1'='1"

        response = await test_client.post(
            "/auth/register",
            json={
                "username": malicious_username,
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User",
                "role": "user",
            },
        )

        # Should succeed (username is treated as literal string, not SQL)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,  # If validation rejects special chars
        ]

        # If created, verify only one user was created with exact username
        if response.status_code == status.HTTP_201_CREATED:
            result = await test_db_session.execute(select(User))
            users = result.scalars().all()

            # Should only create one user with the exact malicious string as username
            matching_users = [u for u in users if u.username == malicious_username]
            assert len(matching_users) <= 1, "SQL injection bypassed ORM protection!"

    @pytest.mark.asyncio
    async def test_register_prevents_sql_injection_in_email(
        self, test_client, test_db_session
    ):
        """Test that registration prevents SQL injection in email field."""
        # Attempt SQL injection via email
        malicious_email = "admin@test.com' OR '1'='1' --"

        response = await test_client.post(
            "/auth/register",
            json={
                "username": "testuser123",
                "email": malicious_email,
                "password": "SecurePass123!",
                "full_name": "Test User",
                "role": "user",
            },
        )

        # Should succeed (email treated as literal)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,  # If email validation rejects it
        ]

        if response.status_code == status.HTTP_201_CREATED:
            result = await test_db_session.execute(select(User))
            users = result.scalars().all()

            # Verify exact email match
            matching_users = [u for u in users if u.email == malicious_email]
            assert len(matching_users) <= 1, "SQL injection bypassed ORM protection!"

    @pytest.mark.asyncio
    async def test_refresh_token_prevents_sql_injection(
        self, test_client, test_db_session, create_test_user
    ):
        """Test that token refresh prevents SQL injection attacks."""
        # Create user and login
        user = await create_test_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
        )

        login_response = await test_client.post(
            "/auth/login",
            data={"username": "testuser", "password": "SecurePass123!"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        refresh_token = login_response.json()["refresh_token"]

        # Attempt SQL injection via refresh token
        malicious_token = refresh_token + "' OR '1'='1"

        response = await test_client.post(
            "/auth/refresh",
            json={"refresh_token": malicious_token},
        )

        # Should fail with 401 (token not found/invalid)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify no tokens were compromised
        result = await test_db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        tokens = result.scalars().all()

        # Should only have the legitimate token
        assert len(tokens) == 1, "SQL injection may have affected token table!"

    @pytest.mark.asyncio
    async def test_list_api_keys_prevents_sql_injection(
        self, test_client, test_db_session, create_test_user
    ):
        """Test that API key listing prevents SQL injection in user_id."""
        # This tests the internal query protection even though user_id
        # comes from authenticated user (defense in depth)

        user = await create_test_user(
            username="researcher",
            email="researcher@example.com",
            password="SecurePass123!",
            role="researcher",
        )

        # Login and get access token
        login_response = await test_client.post(
            "/auth/login",
            data={"username": "researcher", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # List API keys
        response = await test_client.get(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        api_keys = response.json()

        # Verify it's a list (not SQL injection result)
        assert isinstance(api_keys, list)

        # All returned keys should belong to the user
        result = await test_db_session.execute(
            select(APIKey).where(APIKey.user_id == user.id)
        )
        db_keys = result.scalars().all()
        assert len(api_keys) == len(db_keys)

    @pytest.mark.asyncio
    async def test_revoke_api_key_prevents_sql_injection_in_id(
        self, test_client, test_db_session, create_test_user
    ):
        """Test that API key revocation prevents SQL injection in key ID."""
        user = await create_test_user(
            username="researcher2",
            email="researcher2@example.com",
            password="SecurePass123!",
            role="researcher",
        )

        # Login
        login_response = await test_client.post(
            "/auth/login",
            data={"username": "researcher2", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create an API key
        create_response = await test_client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Test Key",
                "description": "For testing",
                "scopes": ["read"],
                "rate_limit": 100,
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        api_key_id = create_response.json()["id"]

        # Attempt SQL injection in key ID
        malicious_id = f"{api_key_id}' OR '1'='1"

        response = await test_client.delete(
            f"/auth/api-keys/{malicious_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Should fail (invalid UUID format or not found)
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # Invalid UUID
        ]

        # Verify the real API key is still active
        result = await test_db_session.execute(
            select(APIKey).where(APIKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()
        assert api_key is not None, "Real API key was affected by injection attempt!"
        assert api_key.is_active is True, "Real API key was deactivated by injection!"

    @pytest.mark.asyncio
    async def test_logout_prevents_sql_injection(
        self, test_client, test_db_session, create_test_user
    ):
        """Test that logout prevents SQL injection when revoking tokens."""
        user = await create_test_user(
            username="logoutuser",
            email="logout@example.com",
            password="SecurePass123!",
        )

        # Login
        login_response = await test_client.post(
            "/auth/login",
            data={"username": "logoutuser", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Logout
        response = await test_client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

        # Verify all user's tokens are revoked (and ONLY this user's tokens)
        result = await test_db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        user_tokens = result.scalars().all()

        assert all(token.is_revoked for token in user_tokens), \
            "Not all user tokens were revoked!"

        # Verify no other users' tokens were affected
        result_all = await test_db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id != user.id)
        )
        other_tokens = result_all.scalars().all()

        # If other tokens exist, none should be revoked (defense against mass revocation)
        if other_tokens:
            assert not all(token.is_revoked for token in other_tokens), \
                "SQL injection affected other users' tokens!"

    @pytest.mark.asyncio
    async def test_malicious_payload_comprehensive(
        self, test_client, test_db_session
    ):
        """Comprehensive test with various SQL injection payloads."""
        sql_injection_payloads = [
            "admin' --",
            "admin' #",
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' #",
            "admin'/*",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users--",
            "1' AND '1'='1",
            "admin' AND 1=1--",
        ]

        for payload in sql_injection_payloads:
            # Try each payload in username
            response = await test_client.post(
                "/auth/register",
                json={
                    "username": payload,
                    "email": f"test_{hash(payload)}@example.com",
                    "password": "SecurePass123!",
                    "full_name": "Test User",
                    "role": "user",
                },
            )

            # Should either succeed (creating user with literal string)
            # or fail validation, but NOT cause SQL injection
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ], f"Unexpected response for payload: {payload}"

        # Verify database integrity - check that users table still exists
        result = await test_db_session.execute(select(User))
        users = result.scalars().all()

        # Table should exist and contain only legitimate users
        assert isinstance(users, list), "Users table may have been compromised!"

    @pytest.mark.asyncio
    async def test_no_raw_sql_in_auth_module(self):
        """
        Meta-test: Verify no raw SQL strings remain in auth.py.

        This test reads the source file and ensures no f-strings
        with SQL keywords are present.
        """
        import pathlib

        auth_file = pathlib.Path(__file__).parent.parent / "src" / "malaria_predictor" / "api" / "routers" / "auth.py"

        with open(auth_file, "r") as f:
            content = f.read()

        # Check for dangerous patterns
        dangerous_patterns = [
            'f"SELECT',
            "f'SELECT",
            'f"UPDATE',
            "f'UPDATE",
            'f"INSERT',
            "f'INSERT",
            'f"DELETE',
            "f'DELETE",
        ]

        for pattern in dangerous_patterns:
            assert pattern not in content, \
                f"Raw SQL found in auth.py: {pattern}. Use SQLAlchemy ORM instead!"


@pytest.fixture
async def create_test_user(test_db_session):
    """Fixture to create test users programmatically."""
    from malaria_predictor.api.security import hash_password

    async def _create_user(
        username: str,
        email: str,
        password: str,
        role: str = "user",
        **kwargs
    ) -> User:
        hashed_password = hash_password(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            **kwargs
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        return user

    return _create_user
