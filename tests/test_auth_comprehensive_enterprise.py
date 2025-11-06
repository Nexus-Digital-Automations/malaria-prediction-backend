"""
Enterprise-Grade Comprehensive Authentication & Security Test Suite.

This module provides exhaustive testing coverage for all authentication and
security features including password hashing, token management, API keys,
session handling, and security edge cases.

Target Coverage: 90%+ for authentication/security modules
"""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from jose import jwt

from malaria_predictor.api.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    SecurityConfig,
    Token,
    TokenData,
    UserCreate,
    create_access_token,
    create_api_key_token,
    create_refresh_token,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
    verify_token,
)
from malaria_predictor.database.security_models import APIKey, RefreshToken, User


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_unique_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "SecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2, "Hashes should differ due to salt"
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_handles_special_characters(self):
        """Test password hashing with special characters."""
        special_passwords = [
            "p@$$w0rd!#%^&*()",
            "パスワード123",  # Japanese characters
            "🔒🔑password123",  # Emojis
            "pass word with spaces",
            "pass\nword\twith\rwhitespace",
        ]

        for pwd in special_passwords:
            hashed = hash_password(pwd)
            assert verify_password(pwd, hashed), f"Failed for password: {pwd}"

    def test_hash_password_minimum_length(self):
        """Test password hashing with various lengths."""
        # Very short password (should still hash successfully)
        short_pwd = "a"
        hashed = hash_password(short_pwd)
        assert verify_password(short_pwd, hashed)

        # Very long password
        long_pwd = "a" * 1000
        hashed = hash_password(long_pwd)
        assert verify_password(long_pwd, hashed)

    def test_hash_password_performance(self):
        """Test that password hashing is reasonably fast."""
        password = "TestPassword123!"
        start = time.time()
        hash_password(password)
        duration = time.time() - start

        # Bcrypt should complete in reasonable time (< 1 second)
        assert duration < 1.0, f"Hashing took {duration}s, too slow!"


class TestTokenManagement:
    """Test JWT token creation and validation."""

    def test_create_access_token_basic(self):
        """Test basic access token creation."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test access token with custom expiration."""
        user_id = str(uuid4())
        custom_expiry = timedelta(minutes=60)
        token = create_access_token(data={"sub": user_id}, expires_delta=custom_expiry)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], UTC)

        time_diff = (exp_time - iat_time).total_seconds() / 60
        assert 59 <= time_diff <= 61, "Expiry should be ~60 minutes"

    def test_create_access_token_with_scopes(self):
        """Test access token with permission scopes."""
        user_id = str(uuid4())
        scopes = ["read:predictions", "write:predictions"]
        token = create_access_token(data={"sub": user_id, "scopes": scopes})

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["scopes"] == scopes

    def test_create_refresh_token_basic(self):
        """Test refresh token creation."""
        user_id = str(uuid4())
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

        # Verify expiration is ~7 days
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], UTC)
        time_diff_days = (exp_time - iat_time).days

        assert time_diff_days == REFRESH_TOKEN_EXPIRE_DAYS

    def test_create_api_key_token_basic(self):
        """Test API key token creation."""
        api_key_id = str(uuid4())
        scopes = ["read:health", "read:predictions"]
        token = create_api_key_token(api_key_id, scopes)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == api_key_id
        assert payload["type"] == "api_key"
        assert payload["scopes"] == scopes

    def test_create_api_key_token_with_expiration(self):
        """Test API key token with custom expiration."""
        api_key_id = str(uuid4())
        scopes = ["read:predictions"]
        expires_at = datetime.now(UTC) + timedelta(days=30)

        token = create_api_key_token(api_key_id, scopes, expires_at)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_exp = datetime.fromtimestamp(payload["exp"], UTC)

        # Allow 1 second tolerance
        time_diff = abs((token_exp - expires_at).total_seconds())
        assert time_diff < 2, "Expiration should match provided time"

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id, "scopes": ["read:health"]})

        token_data = verify_token(token)

        assert token_data is not None
        assert token_data.sub == user_id
        assert token_data.type == "access"
        assert "read:health" in token_data.scopes

    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        user_id = str(uuid4())
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": user_id}, expires_delta=timedelta(seconds=-10)
        )

        token_data = verify_token(token)
        assert token_data is None, "Expired token should return None"

    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        # Tamper with token
        tampered_token = token[:-10] + "tampered123"

        token_data = verify_token(tampered_token)
        assert token_data is None, "Tampered token should return None"

    def test_verify_token_malformed(self):
        """Test verifying malformed tokens."""
        malformed_tokens = [
            "not.a.token",
            "invalid",
            "",
            "a" * 1000,
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ]

        for token in malformed_tokens:
            result = verify_token(token)
            assert result is None, f"Malformed token should return None: {token}"

    def test_verify_token_missing_required_fields(self):
        """Test token verification with missing required fields."""
        # Manually create token without required fields
        incomplete_payload = {"sub": str(uuid4())}  # Missing type, exp, iat

        token = jwt.encode(incomplete_payload, SECRET_KEY, algorithm=ALGORITHM)

        result = verify_token(token)
        assert result is None, "Token with missing fields should return None"

    def test_token_data_model_validation(self):
        """Test TokenData model validation."""
        now = datetime.now(UTC)
        exp = int((now + timedelta(minutes=30)).timestamp())
        iat = int(now.timestamp())

        token_data = TokenData(
            sub=str(uuid4()), type="access", exp=exp, iat=iat, scopes=["read:health"]
        )

        assert token_data.sub
        assert token_data.type == "access"
        assert token_data.exp == exp
        assert token_data.scopes == ["read:health"]


class TestAPIKeyGeneration:
    """Test API key generation and hashing."""

    def test_generate_api_key_format(self):
        """Test that generated API keys have correct format."""
        api_key = generate_api_key()

        assert isinstance(api_key, str)
        assert api_key.startswith("mp_"), "API key should have 'mp_' prefix"
        assert len(api_key) == 67, "API key should be 67 characters (mp_ + 64 chars)"
        # Check format: prefix + alphanumeric
        assert api_key[3:].isalnum(), "API key body should contain only alphanumeric chars"

    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        keys = [generate_api_key() for _ in range(100)]

        assert len(keys) == len(set(keys)), "All generated keys should be unique"

    def test_generate_api_key_entropy(self):
        """Test that API keys have high entropy."""
        key = generate_api_key()

        # Count unique characters
        unique_chars = len(set(key))

        # Should have reasonable character diversity (at least 20 unique chars in 64)
        assert unique_chars >= 20, f"Low entropy: only {unique_chars} unique characters"

    def test_hash_api_key_consistency(self):
        """Test that same API key produces same hash."""
        api_key = generate_api_key()
        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)

        assert hash1 == hash2, "Same API key should produce same hash"

    def test_hash_api_key_different_keys(self):
        """Test that different API keys produce different hashes."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2, "Different keys should produce different hashes"


class TestDataEncryption:
    """Test sensitive data encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption and decryption roundtrip."""
        original = "sensitive-data-12345"
        encrypted = encrypt_sensitive_data(original)
        decrypted = decrypt_sensitive_data(encrypted)

        assert decrypted == original
        assert encrypted != original, "Encrypted data should differ from original"

    def test_encrypt_decrypt_special_characters(self):
        """Test encryption with special characters."""
        test_data = [
            "p@$$w0rd!#%^&*()",
            "データ保護123",  # Japanese
            "🔒🔑secure",  # Emojis
            "multi\nline\tdata",
        ]

        for data in test_data:
            encrypted = encrypt_sensitive_data(data)
            decrypted = decrypt_sensitive_data(encrypted)
            assert decrypted == data, f"Failed roundtrip for: {data}"

    def test_encrypted_data_format(self):
        """Test that encrypted data is properly encoded."""
        original = "test-data"
        encrypted = encrypt_sensitive_data(original)

        assert isinstance(encrypted, str)
        assert len(encrypted) > len(original), "Encrypted should be longer"
        assert encrypted != original


class TestSecurityConfiguration:
    """Test security configuration and utilities."""

    def test_security_scopes_defined(self):
        """Test that all security scopes are properly defined."""
        scopes = SecurityConfig.SCOPES

        assert isinstance(scopes, dict)
        assert len(scopes) > 0

        # Verify expected scopes exist
        expected_scopes = [
            "read:health",
            "read:predictions",
            "write:predictions",
            "read:admin",
            "write:admin",
        ]

        for scope in expected_scopes:
            assert scope in scopes, f"Missing scope: {scope}"
            assert isinstance(scopes[scope], str), f"Scope description missing: {scope}"

    def test_role_scopes_defined(self):
        """Test that role-based scopes are properly configured."""
        role_scopes = SecurityConfig.ROLE_SCOPES

        assert isinstance(role_scopes, dict)
        assert "admin" in role_scopes
        assert "researcher" in role_scopes
        assert "user" in role_scopes
        assert "readonly" in role_scopes

    def test_admin_role_has_all_scopes(self):
        """Test that admin role has all available scopes."""
        admin_scopes = SecurityConfig.ROLE_SCOPES["admin"]
        all_scopes = SecurityConfig.SCOPES.keys()

        assert set(admin_scopes) == set(all_scopes), "Admin should have all scopes"

    def test_readonly_role_has_no_write_scopes(self):
        """Test that readonly role has no write permissions."""
        readonly_scopes = SecurityConfig.ROLE_SCOPES["readonly"]

        write_scopes = [scope for scope in readonly_scopes if "write:" in scope]

        assert len(write_scopes) == 0, "Readonly should have no write scopes"

    def test_user_role_has_basic_scopes(self):
        """Test that user role has appropriate basic scopes."""
        user_scopes = SecurityConfig.ROLE_SCOPES["user"]

        assert "read:health" in user_scopes
        assert "read:predictions" in user_scopes
        assert "write:predictions" in user_scopes
        assert "write:admin" not in user_scopes


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_user_create_model_valid(self):
        """Test valid UserCreate model."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            organization="Test Org",
            role="user",
        )

        assert user_data.username == "testuser"
        assert user_data.email == "test@example.com"
        assert user_data.role == "user"

    def test_user_create_model_email_validation(self):
        """Test email validation in UserCreate."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",  # Space
            "user@.com",
        ]

        for email in invalid_emails:
            with pytest.raises(Exception):  # Pydantic validation error
                UserCreate(
                    username="testuser",
                    email=email,
                    password="SecurePass123!",
                )

    def test_user_create_model_username_length(self):
        """Test username length validation."""
        # Too short
        with pytest.raises(Exception):
            UserCreate(
                username="ab",  # < 3 chars
                email="test@example.com",
                password="SecurePass123!",
            )

        # Too long
        with pytest.raises(Exception):
            UserCreate(
                username="a" * 51,  # > 50 chars
                email="test@example.com",
                password="SecurePass123!",
            )

    def test_user_create_model_password_length(self):
        """Test password length validation."""
        # Too short
        with pytest.raises(Exception):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short",  # < 8 chars
            )

        # Too long
        with pytest.raises(Exception):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="a" * 129,  # > 128 chars
            )

    def test_api_key_create_model_valid(self):
        """Test valid APIKeyCreate model."""
        from malaria_predictor.api.security import APIKeyCreate

        api_key_data = APIKeyCreate(
            name="Test API Key",
            description="For testing",
            scopes=["read:predictions"],
            rate_limit=500,
            allowed_ips=["192.168.1.1"],
        )

        assert api_key_data.name == "Test API Key"
        assert api_key_data.rate_limit == 500
        assert "read:predictions" in api_key_data.scopes

    def test_api_key_create_model_rate_limit_bounds(self):
        """Test rate limit validation."""
        from malaria_predictor.api.security import APIKeyCreate

        # Too low
        with pytest.raises(Exception):
            APIKeyCreate(name="Test", rate_limit=0)

        # Too high
        with pytest.raises(Exception):
            APIKeyCreate(name="Test", rate_limit=10001)

        # Valid boundaries
        APIKeyCreate(name="Test", rate_limit=1)  # Minimum
        APIKeyCreate(name="Test", rate_limit=10000)  # Maximum

    def test_token_model_defaults(self):
        """Test Token model with defaults."""
        token = Token(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=1800,
        )

        assert token.token_type == "bearer", "Default token_type should be bearer"
        assert token.access_token == "test_access_token"
        assert token.expires_in == 1800


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def test_token_expiration_boundary(self):
        """Test token expiration at exact boundary."""
        user_id = str(uuid4())
        # Create token that expires in 1 second
        token = create_access_token(
            data={"sub": user_id}, expires_delta=timedelta(seconds=1)
        )

        # Verify immediately - should be valid
        token_data = verify_token(token)
        assert token_data is not None

        # Wait for expiration
        time.sleep(2)

        # Verify after expiration - should be invalid
        token_data = verify_token(token)
        assert token_data is None

    def test_empty_scopes_handling(self):
        """Test handling of empty scopes."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id, "scopes": []})

        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.scopes == []

    def test_unicode_in_token_data(self):
        """Test Unicode characters in token data."""
        user_id = "user-日本語-🔒"
        token = create_access_token(data={"sub": user_id})

        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.sub == user_id

    def test_concurrent_token_generation(self):
        """Test concurrent token generation for race conditions."""
        import concurrent.futures

        def create_token():
            user_id = str(uuid4())
            return create_access_token(data={"sub": user_id})

        # Create 50 tokens concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            tokens = list(executor.map(lambda _: create_token(), range(50)))

        # All tokens should be valid and unique
        assert len(tokens) == 50
        assert len(set(tokens)) == 50, "All tokens should be unique"

        # Verify all tokens
        for token in tokens:
            token_data = verify_token(token)
            assert token_data is not None


# Mark for performance testing
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmarks for authentication operations."""

    def test_password_hashing_throughput(self):
        """Benchmark password hashing throughput."""
        password = "TestPassword123!"
        iterations = 10

        start = time.time()
        for _ in range(iterations):
            hash_password(password)
        duration = time.time() - start

        avg_time = duration / iterations
        print(f"\nPassword hashing: {avg_time:.3f}s per operation")

        # Should complete 10 hashes in under 5 seconds
        assert duration < 5.0, f"Performance degraded: {duration}s for {iterations} hashes"

    def test_token_verification_throughput(self):
        """Benchmark token verification throughput."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            verify_token(token)
        duration = time.time() - start

        avg_time = duration / iterations
        print(f"\nToken verification: {avg_time*1000:.2f}ms per operation")

        # Should verify 1000 tokens in under 1 second
        assert duration < 1.0, f"Performance degraded: {duration}s for {iterations} verifications"

    def test_api_key_generation_throughput(self):
        """Benchmark API key generation throughput."""
        iterations = 1000

        start = time.time()
        for _ in range(iterations):
            generate_api_key()
        duration = time.time() - start

        avg_time = duration / iterations
        print(f"\nAPI key generation: {avg_time*1000:.2f}ms per operation")

        # Should generate 1000 keys in under 1 second
        assert duration < 1.0, f"Performance degraded: {duration}s for {iterations} generations"
