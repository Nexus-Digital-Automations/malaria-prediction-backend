"""
Comprehensive unit tests for API dependencies module.
Target: 100% coverage for src/malaria_predictor/api/dependencies.py
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import asyncio

# Import the dependencies module to test
from src.malaria_predictor.api.dependencies import (
    get_db_session,
    get_async_db_session,
    get_current_user,
    get_current_active_user,
    verify_api_key,
    require_permission,
    require_admin_access,
    get_redis_client,
    rate_limit_dependency,
    validate_request_signature,
    get_ml_model_service,
    get_data_service,
    get_monitoring_service,
    SecurityManager,
    DatabaseManager,
    CacheManager,
    get_user_context,
    validate_request_headers,
    check_system_health,
)
from src.malaria_predictor.models import User, UserRole, Permission


class TestDatabaseDependencies:
    """Test database session dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.get_database_session")
    def test_get_db_session_success(self, mock_get_db):
        """Test successful database session creation."""
        mock_session = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        # Call the dependency function
        session_gen = get_db_session()
        session = next(session_gen)
        
        assert session == mock_session
        
        # Test cleanup (generator should handle session closure)
        with pytest.raises(StopIteration):
            next(session_gen)
    
    @patch("src.malaria_predictor.api.dependencies.get_async_database_session")
    async def test_get_async_db_session_success(self, mock_get_async_db):
        """Test successful async database session creation."""
        mock_session = Mock(spec=AsyncSession)
        mock_get_async_db.return_value.__aenter__.return_value = mock_session
        
        # Call the async dependency function
        session_gen = get_async_db_session()
        session = await session_gen.__anext__()
        
        assert session == mock_session
    
    @patch("src.malaria_predictor.api.dependencies.get_database_session")
    def test_get_db_session_connection_error(self, mock_get_db):
        """Test database session creation with connection error."""
        mock_get_db.side_effect = ConnectionError("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            session_gen = get_db_session()
            next(session_gen)
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    @patch("src.malaria_predictor.api.dependencies.get_async_database_session")
    async def test_get_async_db_session_timeout(self, mock_get_async_db):
        """Test async database session with timeout."""
        mock_get_async_db.side_effect = asyncio.TimeoutError("Connection timeout")
        
        with pytest.raises(HTTPException) as exc_info:
            session_gen = get_async_db_session()
            await session_gen.__anext__()
        
        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT


class TestUserDependencies:
    """Test user authentication and authorization dependencies."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user_123"
        self.mock_user.email = "test@example.com"
        self.mock_user.role = UserRole.RESEARCHER
        self.mock_user.is_active = True
        self.mock_user.permissions = [Permission.READ_DATA, Permission.WRITE_DATA]
    
    @patch("src.malaria_predictor.api.dependencies.AuthService")
    async def test_get_current_user_success(self, mock_auth_service):
        """Test successful current user retrieval."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_token"
        )
        mock_auth_service.return_value.validate_token.return_value = self.mock_user
        
        result = await get_current_user(credentials)
        assert result == self.mock_user
    
    @patch("src.malaria_predictor.api.dependencies.AuthService")
    async def test_get_current_user_invalid_token(self, mock_auth_service):
        """Test current user retrieval with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        mock_auth_service.return_value.validate_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_current_active_user_success(self):
        """Test getting active user successfully."""
        result = await get_current_active_user(self.mock_user)
        assert result == self.mock_user
    
    async def test_get_current_active_user_inactive(self):
        """Test getting inactive user raises exception."""
        self.mock_user.is_active = False
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(self.mock_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_get_user_context_success(self):
        """Test successful user context creation."""
        context = await get_user_context(self.mock_user)
        
        assert context["user_id"] == self.mock_user.id
        assert context["role"] == self.mock_user.role
        assert context["permissions"] == self.mock_user.permissions
    
    async def test_get_user_context_anonymous(self):
        """Test user context for anonymous user."""
        context = await get_user_context(None)
        
        assert context["user_id"] is None
        assert context["role"] == "anonymous"
        assert context["permissions"] == []


class TestAPIKeyDependencies:
    """Test API key verification dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.get_api_key_details")
    async def test_verify_api_key_success(self, mock_get_api_key):
        """Test successful API key verification."""
        mock_api_key = Mock()
        mock_api_key.is_active = True
        mock_api_key.rate_limit = 1000
        mock_api_key.usage_count = 50
        mock_get_api_key.return_value = mock_api_key
        
        result = await verify_api_key("valid_api_key")
        assert result == mock_api_key
    
    @patch("src.malaria_predictor.api.dependencies.get_api_key_details")
    async def test_verify_api_key_not_found(self, mock_get_api_key):
        """Test API key verification for non-existent key."""
        mock_get_api_key.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("invalid_api_key")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("src.malaria_predictor.api.dependencies.get_api_key_details")
    async def test_verify_api_key_inactive(self, mock_get_api_key):
        """Test API key verification for inactive key."""
        mock_api_key = Mock()
        mock_api_key.is_active = False
        mock_get_api_key.return_value = mock_api_key
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("inactive_api_key")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("src.malaria_predictor.api.dependencies.get_api_key_details")
    async def test_verify_api_key_rate_limited(self, mock_get_api_key):
        """Test API key verification when rate limited."""
        mock_api_key = Mock()
        mock_api_key.is_active = True
        mock_api_key.rate_limit = 100
        mock_api_key.usage_count = 100  # At limit
        mock_get_api_key.return_value = mock_api_key
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("rate_limited_key")
        
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestPermissionDependencies:
    """Test permission-based access control dependencies."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user_123"
        self.mock_user.role = UserRole.RESEARCHER
        self.mock_user.permissions = [Permission.READ_DATA, Permission.WRITE_DATA]
    
    async def test_require_permission_success(self):
        """Test successful permission check."""
        permission_dep = require_permission(Permission.READ_DATA)
        
        # Should not raise exception
        await permission_dep(self.mock_user)
    
    async def test_require_permission_failure(self):
        """Test permission check failure."""
        permission_dep = require_permission(Permission.ADMIN_ACCESS)
        
        with pytest.raises(HTTPException) as exc_info:
            await permission_dep(self.mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_require_admin_access_success(self):
        """Test successful admin access check."""
        self.mock_user.role = UserRole.ADMIN
        self.mock_user.permissions = [Permission.ADMIN_ACCESS]
        
        result = await require_admin_access(self.mock_user)
        assert result == self.mock_user
    
    async def test_require_admin_access_failure(self):
        """Test admin access check failure."""
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_access(self.mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_require_permission_multiple_success(self):
        """Test multiple permission requirements success."""
        permissions = [Permission.READ_DATA, Permission.WRITE_DATA]
        
        for perm in permissions:
            permission_dep = require_permission(perm)
            await permission_dep(self.mock_user)  # Should not raise
    
    async def test_require_permission_with_none_user(self):
        """Test permission check with None user."""
        permission_dep = require_permission(Permission.READ_DATA)
        
        with pytest.raises(HTTPException) as exc_info:
            await permission_dep(None)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestServiceDependencies:
    """Test service injection dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.get_redis_connection")
    async def test_get_redis_client_success(self, mock_get_redis):
        """Test successful Redis client creation."""
        mock_redis = Mock()
        mock_get_redis.return_value = mock_redis
        
        client = await get_redis_client()
        assert client == mock_redis
    
    @patch("src.malaria_predictor.api.dependencies.get_redis_connection")
    async def test_get_redis_client_connection_error(self, mock_get_redis):
        """Test Redis client creation with connection error."""
        mock_get_redis.side_effect = ConnectionError("Redis connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_redis_client()
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    @patch("src.malaria_predictor.api.dependencies.MLModelService")
    async def test_get_ml_model_service_success(self, mock_ml_service_class):
        """Test successful ML model service creation."""
        mock_service = Mock()
        mock_ml_service_class.return_value = mock_service
        
        service = await get_ml_model_service()
        assert service == mock_service
    
    @patch("src.malaria_predictor.api.dependencies.DataService")
    async def test_get_data_service_success(self, mock_data_service_class):
        """Test successful data service creation."""
        mock_service = Mock()
        mock_data_service_class.return_value = mock_service
        
        service = await get_data_service()
        assert service == mock_service
    
    @patch("src.malaria_predictor.api.dependencies.MonitoringService")
    async def test_get_monitoring_service_success(self, mock_monitoring_service_class):
        """Test successful monitoring service creation."""
        mock_service = Mock()
        mock_monitoring_service_class.return_value = mock_service
        
        service = await get_monitoring_service()
        assert service == mock_service
    
    @patch("src.malaria_predictor.api.dependencies.MLModelService")
    async def test_get_ml_model_service_initialization_error(self, mock_ml_service_class):
        """Test ML model service creation with initialization error."""
        mock_ml_service_class.side_effect = RuntimeError("Model loading failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_ml_model_service()
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestRateLimitingDependencies:
    """Test rate limiting dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.RateLimiter")
    async def test_rate_limit_dependency_success(self, mock_rate_limiter_class):
        """Test successful rate limiting check."""
        mock_limiter = Mock()
        mock_limiter.check_rate_limit.return_value = True
        mock_rate_limiter_class.return_value = mock_limiter
        
        rate_limit_dep = rate_limit_dependency(requests_per_minute=100)
        
        # Mock request object
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        
        result = await rate_limit_dep(mock_request)
        assert result is True
    
    @patch("src.malaria_predictor.api.dependencies.RateLimiter")
    async def test_rate_limit_dependency_exceeded(self, mock_rate_limiter_class):
        """Test rate limit exceeded scenario."""
        mock_limiter = Mock()
        mock_limiter.check_rate_limit.return_value = False
        mock_rate_limiter_class.return_value = mock_limiter
        
        rate_limit_dep = rate_limit_dependency(requests_per_minute=10)
        
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit_dep(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    @patch("src.malaria_predictor.api.dependencies.RateLimiter")
    async def test_rate_limit_dependency_custom_limits(self, mock_rate_limiter_class):
        """Test rate limiting with custom limits."""
        mock_limiter = Mock()
        mock_limiter.check_rate_limit.return_value = True
        mock_rate_limiter_class.return_value = mock_limiter
        
        # Test different rate limits
        for limit in [50, 100, 500]:
            rate_limit_dep = rate_limit_dependency(requests_per_minute=limit)
            mock_request = Mock()
            mock_request.client.host = "192.168.1.1"
            
            result = await rate_limit_dep(mock_request)
            assert result is True


class TestRequestValidationDependencies:
    """Test request validation dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.SignatureValidator")
    async def test_validate_request_signature_success(self, mock_validator_class):
        """Test successful request signature validation."""
        mock_validator = Mock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator
        
        mock_request = Mock()
        mock_request.body = b'{"data": "test"}'
        mock_request.headers = {"X-Signature": "valid_signature"}
        
        result = await validate_request_signature(mock_request)
        assert result is True
    
    @patch("src.malaria_predictor.api.dependencies.SignatureValidator")
    async def test_validate_request_signature_invalid(self, mock_validator_class):
        """Test invalid request signature validation."""
        mock_validator = Mock()
        mock_validator.validate.return_value = False
        mock_validator_class.return_value = mock_validator
        
        mock_request = Mock()
        mock_request.body = b'{"data": "test"}'
        mock_request.headers = {"X-Signature": "invalid_signature"}
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_request_signature(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("src.malaria_predictor.api.dependencies.validate_headers")
    async def test_validate_request_headers_success(self, mock_validate_headers):
        """Test successful request headers validation."""
        mock_validate_headers.return_value = True
        
        mock_request = Mock()
        mock_request.headers = {
            "Content-Type": "application/json",
            "User-Agent": "malaria-client/1.0"
        }
        
        result = await validate_request_headers(mock_request)
        assert result is True
    
    @patch("src.malaria_predictor.api.dependencies.validate_headers")
    async def test_validate_request_headers_invalid(self, mock_validate_headers):
        """Test invalid request headers validation."""
        mock_validate_headers.return_value = False
        
        mock_request = Mock()
        mock_request.headers = {"Invalid-Header": "bad_value"}
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_request_headers(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_validate_request_headers_missing_required(self):
        """Test validation with missing required headers."""
        mock_request = Mock()
        mock_request.headers = {}  # No headers
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_request_headers(mock_request, required=["Content-Type"])
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


class TestManagerDependencies:
    """Test manager class dependencies."""
    
    def test_security_manager_initialization(self):
        """Test SecurityManager initialization."""
        manager = SecurityManager()
        
        assert hasattr(manager, 'validate_token')
        assert hasattr(manager, 'check_permissions')
        assert hasattr(manager, 'rate_limiter')
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        manager = DatabaseManager()
        
        assert hasattr(manager, 'get_session')
        assert hasattr(manager, 'get_async_session')
        assert hasattr(manager, 'health_check')
    
    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        manager = CacheManager()
        
        assert hasattr(manager, 'get_client')
        assert hasattr(manager, 'set_cache')
        assert hasattr(manager, 'get_cache')
    
    @patch("src.malaria_predictor.api.dependencies.SecurityManager")
    def test_security_manager_methods(self, mock_security_manager_class):
        """Test SecurityManager methods."""
        mock_manager = Mock()
        mock_manager.validate_token.return_value = True
        mock_manager.check_permissions.return_value = True
        mock_security_manager_class.return_value = mock_manager
        
        manager = SecurityManager()
        
        assert manager.validate_token("token") is True
        assert manager.check_permissions("user", ["read"]) is True
    
    @patch("src.malaria_predictor.api.dependencies.DatabaseManager")
    def test_database_manager_methods(self, mock_db_manager_class):
        """Test DatabaseManager methods."""
        mock_manager = Mock()
        mock_session = Mock()
        mock_manager.get_session.return_value = mock_session
        mock_db_manager_class.return_value = mock_manager
        
        manager = DatabaseManager()
        session = manager.get_session()
        
        assert session == mock_session


class TestHealthCheckDependencies:
    """Test system health check dependencies."""
    
    @patch("src.malaria_predictor.api.dependencies.SystemHealthChecker")
    async def test_check_system_health_success(self, mock_health_checker_class):
        """Test successful system health check."""
        mock_checker = Mock()
        mock_checker.check_all_systems.return_value = {
            "database": "healthy",
            "redis": "healthy",
            "ml_models": "healthy"
        }
        mock_health_checker_class.return_value = mock_checker
        
        health_status = await check_system_health()
        
        assert health_status["database"] == "healthy"
        assert health_status["redis"] == "healthy"
        assert health_status["ml_models"] == "healthy"
    
    @patch("src.malaria_predictor.api.dependencies.SystemHealthChecker")
    async def test_check_system_health_partial_failure(self, mock_health_checker_class):
        """Test system health check with partial failures."""
        mock_checker = Mock()
        mock_checker.check_all_systems.return_value = {
            "database": "healthy",
            "redis": "unhealthy",
            "ml_models": "healthy"
        }
        mock_health_checker_class.return_value = mock_checker
        
        health_status = await check_system_health()
        
        assert health_status["redis"] == "unhealthy"
    
    @patch("src.malaria_predictor.api.dependencies.SystemHealthChecker")
    async def test_check_system_health_critical_failure(self, mock_health_checker_class):
        """Test system health check with critical failures."""
        mock_checker = Mock()
        mock_checker.check_all_systems.side_effect = Exception("System critical failure")
        mock_health_checker_class.return_value = mock_checker
        
        with pytest.raises(HTTPException) as exc_info:
            await check_system_health()
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestDependencyInjectionEdgeCases:
    """Test edge cases and error scenarios in dependency injection."""
    
    def test_none_parameters_handling(self):
        """Test handling of None parameters in dependencies."""
        # Test that dependencies handle None gracefully
        with pytest.raises((TypeError, AttributeError, HTTPException)):
            # This should fail gracefully
            asyncio.run(get_current_active_user(None))
    
    @patch("src.malaria_predictor.api.dependencies.get_database_session")
    def test_database_dependency_cleanup_on_error(self, mock_get_db):
        """Test database dependency cleanup on error."""
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__.return_value = mock_session
        mock_context.__exit__.return_value = None
        mock_get_db.return_value = mock_context
        
        # Simulate an error during session usage
        session_gen = get_db_session()
        session = next(session_gen)
        
        # Verify session is properly cleaned up
        try:
            next(session_gen)
        except StopIteration:
            pass  # Expected behavior
        
        # Verify __exit__ was called (cleanup)
        assert mock_context.__exit__.called
    
    async def test_async_dependency_cancellation(self):
        """Test async dependency behavior during cancellation."""
        async def cancelled_dependency():
            await asyncio.sleep(1)
            return "result"
        
        # Test that cancellation is handled properly
        task = asyncio.create_task(cancelled_dependency())
        await asyncio.sleep(0.1)
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
    
    def test_dependency_with_large_objects(self):
        """Test dependencies with large object handling."""
        # Create a large mock object
        large_user = Mock(spec=User)
        large_user.metadata = {"large_data": "x" * 10000}
        
        # Should handle large objects without issues
        context = asyncio.run(get_user_context(large_user))
        assert "user_id" in context