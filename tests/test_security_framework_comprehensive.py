"""
Comprehensive tests for the security framework components.

Tests cover:
- Token management with encryption and validation
- Error handling and classification
- Retry strategies with circuit breakers
- Security audit logging with HIPAA compliance
- Integration testing of all components
"""

import asyncio
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from src.malaria_predictor.security import (
    AuditEventType,
    AuditRiskLevel,
    CircuitBreakerConfig,
    ComplianceFramework,
    DetailedError,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    RetryExecutor,
    RetryStrategy,
    SecurityAuditLogger,
    TokenManager,
    create_security_framework,
)


class TestTokenManager:
    """Test cases for TokenManager with secure storage and validation."""

    @pytest.fixture
    async def token_manager(self):
        """Create TokenManager instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield TokenManager(
                secret_key="test-secret-key-for-jwt-signing-and-encryption",
                storage_path=Path(temp_dir) / "tokens",
                access_token_expire_minutes=1,  # Short expiry for testing
                refresh_token_expire_days=1,
            )

    @pytest.mark.asyncio
    async def test_token_creation_and_validation(self, token_manager):
        """Test creating and validating JWT tokens."""
        user_id = "test_user_123"
        scopes = {"read:predictions", "write:predictions"}

        # Create tokens
        token_data = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes,
            client_id="test_client"
        )

        assert token_data.user_id == user_id
        assert token_data.scopes == scopes
        assert token_data.access_token is not None
        assert token_data.refresh_token is not None

        # Validate access token
        payload = await token_manager.validate_token(
            token_data.access_token,
            required_scopes={"read:predictions"}
        )

        assert payload["sub"] == user_id
        assert "read:predictions" in payload["scopes"]
        assert payload["type"] == "access"

    @pytest.mark.asyncio
    async def test_token_refresh(self, token_manager):
        """Test token refresh functionality."""
        user_id = "test_user_456"
        scopes = {"read:data"}

        # Create initial tokens
        original_tokens = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes
        )

        # Refresh tokens
        new_tokens = await token_manager.refresh_token(
            original_tokens.refresh_token
        )

        assert new_tokens.user_id == user_id
        assert new_tokens.scopes == scopes
        assert new_tokens.access_token != original_tokens.access_token

        # Original access token should still be valid until it expires
        await token_manager.validate_token(original_tokens.access_token)

    @pytest.mark.asyncio
    async def test_token_expiration(self, token_manager):
        """Test token expiration handling."""
        user_id = "test_user_789"
        scopes = {"read:test"}

        # Create tokens with very short expiry
        token_data = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes
        )

        # Wait for token to expire
        await asyncio.sleep(65)  # Wait longer than 1 minute expiry

        # Validation should fail
        with pytest.raises(Exception):  # TokenExpiredError
            await token_manager.validate_token(token_data.access_token)

    @pytest.mark.asyncio
    async def test_token_revocation(self, token_manager):
        """Test token revocation functionality."""
        user_id = "test_user_revoke"
        scopes = {"read:test"}

        # Create tokens
        token_data = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes
        )

        # Revoke token
        revoked = await token_manager.revoke_token(
            token_data.session_id,
            user_id,
            reason="test_revocation"
        )

        assert revoked is True

        # Token should be removed from storage
        stored_token = await token_manager.storage.retrieve_token(token_data.session_id)
        assert stored_token is None

    @pytest.mark.asyncio
    async def test_secure_storage_encryption(self, token_manager):
        """Test secure token storage with encryption."""
        user_id = "encryption_test_user"
        scopes = {"read:encrypted"}

        # Create and store token
        token_data = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes
        )

        # Verify token is stored and retrievable
        stored_token = await token_manager.storage.retrieve_token(token_data.session_id)
        assert stored_token is not None
        assert stored_token.user_id == user_id
        assert stored_token.scopes == scopes

        # Verify storage files exist
        assert token_manager.storage.tokens_file.exists()

    @pytest.mark.asyncio
    async def test_security_audit_events(self, token_manager):
        """Test that security events are properly logged."""
        user_id = "audit_test_user"
        scopes = {"read:audit"}

        # Create tokens (should generate audit events)
        await token_manager.create_tokens(user_id=user_id, scopes=scopes)

        # Check that audit events were generated
        assert len(token_manager.audit_events) > 0

        # Find token creation event
        creation_events = [
            event for event in token_manager.audit_events
            if event.event_type == "token_created"
        ]
        assert len(creation_events) > 0

        creation_event = creation_events[0]
        assert creation_event.user_id == user_id
        assert creation_event.outcome == "success"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, token_manager):
        """Test rate limiting functionality."""
        user_id = "rate_limit_test"
        scopes = {"read:test"}

        # Create tokens
        token_data = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes
        )

        # Simulate rapid token validation requests
        for _ in range(token_manager.max_requests_per_window + 10):
            try:
                await token_manager.validate_token(token_data.access_token)
            except Exception:
                # Rate limit should eventually be triggered
                break

        # Check that rate limiting events were logged
        rate_limit_events = [
            event for event in token_manager.audit_events
            if event.event_type == "rate_limit_exceeded"
        ]

        # Should have at least one rate limit event
        assert len(rate_limit_events) > 0


class TestErrorHandler:
    """Test cases for ErrorHandler with classification and recovery."""

    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        return ErrorHandler(enable_metrics=True)

    @pytest.mark.asyncio
    async def test_error_classification(self, error_handler):
        """Test error classification based on exception types."""
        # Test network error classification
        network_error = ConnectionError("Connection refused")
        detailed_error = await error_handler.handle_error(network_error)

        assert detailed_error.category == ErrorCategory.CONNECTION
        assert detailed_error.retry_eligible is True
        assert "Connection refused" in detailed_error.message

    @pytest.mark.asyncio
    async def test_custom_error_classification(self, error_handler):
        """Test custom error with specific classification."""
        # Create a detailed error directly
        custom_error = DetailedError(
            message="Custom business logic error",
            category=ErrorCategory.BUSINESS_RULE,
            severity=ErrorSeverity.HIGH,
            retry_eligible=False,
        )

        assert custom_error.category == ErrorCategory.BUSINESS_RULE
        assert custom_error.severity == ErrorSeverity.HIGH
        assert custom_error.retry_eligible is False

    @pytest.mark.asyncio
    async def test_error_metrics_collection(self, error_handler):
        """Test error metrics collection and reporting."""
        # Generate several errors
        errors = [
            ConnectionError("Network error 1"),
            ValueError("Validation error 1"),
            TimeoutError("Timeout error 1"),
            ConnectionError("Network error 2"),
        ]

        for error in errors:
            await error_handler.handle_error(error)

        # Check metrics
        assert len(error_handler.error_history) == 4
        assert len(error_handler.error_metrics) > 0

        # Generate metrics report
        report = error_handler.get_error_metrics_report(hours=1)
        assert report["summary"]["total_errors"] == 4
        assert "category_breakdown" in report
        assert "recommendations" in report

    @pytest.mark.asyncio
    async def test_error_recovery_strategies(self, error_handler):
        """Test error recovery strategy execution."""
        # Create error that should trigger recovery
        network_error = ConnectionError("Connection timeout")
        detailed_error = await error_handler.handle_error(
            network_error,
            attempt_recovery=True
        )

        # Check that recovery was attempted
        assert detailed_error.metadata.get("recovery_attempted") is True
        assert "recovery_result" in detailed_error.metadata

    @pytest.mark.asyncio
    async def test_security_error_handling(self, error_handler):
        """Test handling of security-related errors."""
        # Simulate security violation
        security_error = PermissionError("Unauthorized access attempt")
        detailed_error = await error_handler.handle_error(security_error)

        # Should be classified as high-risk security event
        assert detailed_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        assert detailed_error.retry_eligible is False


class TestRetryExecutor:
    """Test cases for RetryExecutor with circuit breakers."""

    @pytest.fixture
    def retry_executor(self):
        """Create RetryExecutor instance for testing."""
        return RetryExecutor()

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self, retry_executor):
        """Test successful execution without retry."""
        async def successful_func():
            return "success"

        result = await retry_executor.execute_with_retry(successful_func)

        assert result.success is True
        assert result.attempts == 1
        assert result.result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self, retry_executor):
        """Test retry logic with eventual success."""
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        config = RetryConfig(max_attempts=5, base_delay=0.1)
        result = await retry_executor.execute_with_retry(
            failing_then_success,
            config=config
        )

        assert result.success is True
        assert result.attempts == 3
        assert result.result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_persistent_failure(self, retry_executor):
        """Test retry logic with persistent failure."""
        async def always_failing():
            raise ValueError("Persistent error")

        config = RetryConfig(max_attempts=3, base_delay=0.1)
        result = await retry_executor.execute_with_retry(
            always_failing,
            config=config
        )

        assert result.success is False
        assert result.attempts == 3
        assert "Persistent error" in result.last_error

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, retry_executor):
        """Test circuit breaker pattern."""
        # Add circuit breaker
        cb_config = CircuitBreakerConfig(failure_threshold=2, timeout=1.0)
        retry_executor.add_circuit_breaker("test_service", cb_config)

        failure_count = 0

        async def intermittent_failure():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:  # Fail first 5 times
                raise ConnectionError("Service unavailable")
            return "success"

        # First few calls should fail and trigger circuit breaker
        for _ in range(3):
            result = await retry_executor.execute_with_retry(
                intermittent_failure,
                circuit_breaker_name="test_service"
            )
            assert result.success is False

        # Circuit should now be open
        cb_status = await retry_executor.get_circuit_breaker_status("test_service")
        assert cb_status["state"] in ["open", "half_open"]

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, retry_executor):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False  # Disable jitter for predictable testing
        )

        # Test delay calculation
        from src.malaria_predictor.security.retry_strategies import BackoffCalculator

        delay1 = BackoffCalculator.calculate_delay(1, config)
        delay2 = BackoffCalculator.calculate_delay(2, config)
        delay3 = BackoffCalculator.calculate_delay(3, config)

        assert delay1 == 1.0  # Base delay
        assert delay2 == 2.0  # Base * multiplier^1
        assert delay3 == 4.0  # Base * multiplier^2

    @pytest.mark.asyncio
    async def test_request_deduplication(self, retry_executor):
        """Test request deduplication for idempotent operations."""
        call_count = 0

        async def tracked_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate work
            return f"result_{call_count}"

        # Execute same idempotent operation concurrently
        config = RetryConfig(idempotency_key="test_operation_123")

        tasks = [
            retry_executor.execute_with_retry(tracked_function, config=config)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # Function should only be called once due to deduplication
        assert call_count == 1

        # All results should be the same
        for result in results:
            assert result.success is True


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger with HIPAA compliance."""

    @pytest.fixture
    async def audit_logger(self):
        """Create SecurityAuditLogger instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SecurityAuditLogger(
                storage_path=Path(temp_dir),
                encryption_key=Fernet.generate_key(),
                application_name="test_app",
                environment="test"
            )

    @pytest.mark.asyncio
    async def test_basic_event_logging(self, audit_logger):
        """Test basic audit event logging."""
        event_id = await audit_logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            description="User logged in successfully",
            user_id="test_user",
            outcome="success",
            client_ip="192.168.1.100"
        )

        assert event_id is not None
        assert len(audit_logger.recent_events) == 1

        event = audit_logger.recent_events[0]
        assert event.event_type == AuditEventType.LOGIN_SUCCESS
        assert event.user_id == "test_user"
        assert event.outcome == "success"

    @pytest.mark.asyncio
    async def test_phi_event_logging(self, audit_logger):
        """Test PHI-related event logging for HIPAA compliance."""
        event_id = await audit_logger.log_event(
            event_type=AuditEventType.PHI_ACCESSED,
            description="Patient health information accessed",
            user_id="doctor_123",
            resource_type="patient_record",
            resource_id="patient_456",
            phi_involved=True,
            risk_level=AuditRiskLevel.MEDIUM,
            compliance_frameworks=[ComplianceFramework.HIPAA]
        )

        assert event_id is not None

        event = audit_logger.recent_events[0]
        assert event.phi_involved is True
        assert ComplianceFramework.HIPAA in event.compliance_frameworks
        assert event.risk_level == AuditRiskLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_security_alert_logging(self, audit_logger):
        """Test security alert event logging."""
        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description="Suspicious login attempt detected",
            risk_level=AuditRiskLevel.HIGH,
            client_ip="suspicious.ip.address",
            additional_data={
                "failed_attempts": 5,
                "time_window": "5_minutes"
            }
        )

        event = audit_logger.recent_events[0]
        assert event.event_type == AuditEventType.SECURITY_ALERT
        assert event.risk_level == AuditRiskLevel.HIGH
        assert event.additional_data["failed_attempts"] == 5

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, audit_logger):
        """Test security anomaly detection."""
        if not audit_logger.anomaly_detector:
            pytest.skip("Anomaly detection disabled")

        # Generate multiple failed login events to trigger anomaly
        for i in range(15):
            await audit_logger.log_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                description=f"Failed login attempt {i}",
                user_id=f"user_{i % 3}",  # Concentrate failures on few users
                client_ip="192.168.1.100"
            )

        # Should have triggered anomaly detection
        security_alerts = [
            event for event in audit_logger.recent_events
            if event.event_type == AuditEventType.SECURITY_ALERT
        ]

        assert len(security_alerts) > 0

    @pytest.mark.asyncio
    async def test_compliance_report_generation(self, audit_logger):
        """Test HIPAA compliance report generation."""
        # Generate various events
        events_data = [
            (AuditEventType.PHI_ACCESSED, "PHI access 1", True),
            (AuditEventType.PHI_MODIFIED, "PHI modification", True),
            (AuditEventType.DATA_ACCESS, "Regular data access", False),
            (AuditEventType.USER_CREATED, "New user created", False),
        ]

        for event_type, description, phi_involved in events_data:
            await audit_logger.log_event(
                event_type=event_type,
                description=description,
                user_id="test_user",
                phi_involved=phi_involved,
                compliance_frameworks=[ComplianceFramework.HIPAA]
            )

        # Generate HIPAA compliance report
        start_date = datetime.now(UTC) - timedelta(hours=1)
        end_date = datetime.now(UTC)

        report = await audit_logger.generate_compliance_report(
            framework=ComplianceFramework.HIPAA,
            start_date=start_date,
            end_date=end_date
        )

        assert report["framework"] == "HIPAA"
        assert report["summary"]["total_events"] == 4
        assert report["summary"]["phi_related_events"] == 2
        assert "compliance_requirements" in report
        assert "violations" in report
        assert "recommendations" in report

    @pytest.mark.asyncio
    async def test_encrypted_storage(self, audit_logger):
        """Test encrypted audit log storage."""
        await audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            description="Test encrypted storage",
            user_id="encryption_test"
        )

        # Check that log files are created
        log_files = list(audit_logger.storage_path.glob("audit_log_*.log"))
        assert len(log_files) > 0

        # Verify files contain encrypted data (not readable as plain text)
        with open(log_files[0], "rb") as f:
            content = f.read()

        # Should not contain plain text
        assert b"encryption_test" not in content
        assert b"DATA_ACCESS" not in content

    @pytest.mark.asyncio
    async def test_event_retrieval_and_filtering(self, audit_logger):
        """Test event retrieval with filtering."""
        # Create events with different characteristics
        await audit_logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            description="Login 1",
            user_id="user1",
            risk_level=AuditRiskLevel.LOW
        )

        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description="Alert 1",
            user_id="user2",
            risk_level=AuditRiskLevel.HIGH
        )

        await audit_logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            description="Login 2",
            user_id="user1",
            risk_level=AuditRiskLevel.LOW
        )

        # Test filtering by user
        user1_events = await audit_logger.get_events(user_id="user1")
        assert len(user1_events) == 2
        assert all(event.user_id == "user1" for event in user1_events)

        # Test filtering by event type
        login_events = await audit_logger.get_events(
            event_types=[AuditEventType.LOGIN_SUCCESS]
        )
        assert len(login_events) == 2
        assert all(event.event_type == AuditEventType.LOGIN_SUCCESS for event in login_events)

        # Test filtering by risk level
        high_risk_events = await audit_logger.get_events(
            risk_level=AuditRiskLevel.HIGH
        )
        assert len(high_risk_events) == 1
        assert high_risk_events[0].event_type == AuditEventType.SECURITY_ALERT


class TestSecurityFrameworkIntegration:
    """Integration tests for the complete security framework."""

    @pytest.fixture
    async def security_framework(self):
        """Create complete security framework for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            token_manager, error_handler, retry_executor, audit_logger = create_security_framework(
                storage_path=temp_dir,
                secret_key="integration-test-secret-key",
                application_name="test_malaria_predictor",
                environment="test"
            )
            yield {
                "token_manager": token_manager,
                "error_handler": error_handler,
                "retry_executor": retry_executor,
                "audit_logger": audit_logger,
            }

    @pytest.mark.asyncio
    async def test_end_to_end_security_workflow(self, security_framework):
        """Test complete end-to-end security workflow."""
        token_manager = security_framework["token_manager"]
        error_handler = security_framework["error_handler"]
        retry_executor = security_framework["retry_executor"]
        audit_logger = security_framework["audit_logger"]

        # Step 1: Create user session with tokens
        user_id = "integration_test_user"
        scopes = {"read:predictions", "write:predictions", "access:phi"}

        tokens = await token_manager.create_tokens(
            user_id=user_id,
            scopes=scopes,
            client_id="integration_test_client"
        )

        assert tokens.access_token is not None

        # Step 2: Log security event for session creation
        session_event_id = await audit_logger.log_event(
            event_type=AuditEventType.SESSION_CREATED,
            description="User session created for integration test",
            user_id=user_id,
            session_id=tokens.session_id,
        )

        assert session_event_id is not None

        # Step 3: Simulate API operation with error handling and retry
        operation_call_count = 0

        async def simulated_api_operation():
            nonlocal operation_call_count
            operation_call_count += 1

            # Fail first two attempts, succeed on third
            if operation_call_count < 3:
                raise ConnectionError("Simulated API failure")

            # Log successful PHI access
            await audit_logger.log_event(
                event_type=AuditEventType.PHI_ACCESSED,
                description="Patient prediction data accessed",
                user_id=user_id,
                session_id=tokens.session_id,
                resource_type="prediction",
                resource_id="patient_123_prediction",
                phi_involved=True,
                risk_level=AuditRiskLevel.MEDIUM
            )

            return {"prediction": "low_risk", "confidence": 0.85}

        # Execute with retry logic
        retry_config = RetryConfig(max_attempts=5, base_delay=0.1)
        result = await retry_executor.execute_with_retry(
            simulated_api_operation,
            config=retry_config
        )

        assert result.success is True
        assert result.attempts == 3
        assert result.result["prediction"] == "low_risk"

        # Step 4: Handle authentication error
        try:
            # Simulate invalid token
            await token_manager.validate_token("invalid.token.here")
        except Exception as e:
            detailed_error = await error_handler.handle_error(e)
            assert detailed_error.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.TOKEN]

        # Step 5: Generate security metrics
        security_metrics = audit_logger.get_security_metrics()
        assert security_metrics.total_events > 0

        # Step 6: Generate compliance report
        start_date = datetime.now(UTC) - timedelta(hours=1)
        end_date = datetime.now(UTC)

        hipaa_report = await audit_logger.generate_compliance_report(
            framework=ComplianceFramework.HIPAA,
            start_date=start_date,
            end_date=end_date
        )

        assert hipaa_report["framework"] == "HIPAA"
        assert hipaa_report["summary"]["phi_related_events"] >= 1

        # Step 7: Clean up - revoke tokens
        revoked = await token_manager.revoke_token(
            tokens.session_id,
            user_id,
            reason="integration_test_cleanup"
        )

        assert revoked is True

        # Step 8: Log session termination
        await audit_logger.log_event(
            event_type=AuditEventType.SESSION_TERMINATED,
            description="User session terminated",
            user_id=user_id,
            session_id=tokens.session_id,
            outcome="success"
        )

    @pytest.mark.asyncio
    async def test_security_framework_under_load(self, security_framework):
        """Test security framework performance under concurrent load."""
        audit_logger = security_framework["audit_logger"]
        token_manager = security_framework["token_manager"]

        # Create multiple concurrent token operations
        async def create_and_validate_token(user_id: str):
            tokens = await token_manager.create_tokens(
                user_id=user_id,
                scopes={"read:test"}
            )

            # Validate the token
            payload = await token_manager.validate_token(tokens.access_token)
            assert payload["sub"] == user_id

            # Log an event
            await audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                description=f"Concurrent test for {user_id}",
                user_id=user_id
            )

            return tokens

        # Execute concurrent operations
        tasks = [
            create_and_validate_token(f"load_test_user_{i}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10

        # Check that all events were logged
        assert len(audit_logger.recent_events) >= 20  # At least token creation + data access events

    @pytest.mark.asyncio
    async def test_hipaa_compliance_validation(self, security_framework):
        """Test comprehensive HIPAA compliance validation."""
        audit_logger = security_framework["audit_logger"]
        token_manager = security_framework["token_manager"]

        # Create user with PHI access
        user_id = "hipaa_compliance_user"
        tokens = await token_manager.create_tokens(
            user_id=user_id,
            scopes={"access:phi", "read:predictions"}
        )

        # Simulate comprehensive PHI workflow
        phi_operations = [
            (AuditEventType.PHI_ACCESSED, "Patient record accessed"),
            (AuditEventType.PHI_MODIFIED, "Patient data updated"),
            (AuditEventType.PHI_DISCLOSED, "Data shared with authorized physician"),
        ]

        for event_type, description in phi_operations:
            await audit_logger.log_event(
                event_type=event_type,
                description=description,
                user_id=user_id,
                session_id=tokens.session_id,
                resource_type="patient_record",
                resource_id="patient_hipaa_test",
                phi_involved=True,
                compliance_frameworks=[ComplianceFramework.HIPAA],
                additional_data={
                    "access_purpose": "treatment",
                    "minimum_necessary": True,
                    "authorization_present": True
                }
            )

        # Generate HIPAA compliance report
        start_date = datetime.now(UTC) - timedelta(hours=1)
        end_date = datetime.now(UTC)

        report = await audit_logger.generate_compliance_report(
            framework=ComplianceFramework.HIPAA,
            start_date=start_date,
            end_date=end_date
        )

        # Validate HIPAA compliance requirements
        compliance_reqs = report["compliance_requirements"]
        assert compliance_reqs["audit_trail_complete"] is True
        assert compliance_reqs["user_identification"] is True
        assert compliance_reqs["timestamp_accuracy"] is True
        assert compliance_reqs["data_integrity"] is True
        assert compliance_reqs["encryption_status"] is True

        # Check for violations
        violations = report["violations"]
        # Should have no critical violations in this test
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        assert len(critical_violations) == 0


if __name__ == "__main__":
    # Run tests with asyncio support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
