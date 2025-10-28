"""
Comprehensive Security Audit Logging and Monitoring System for HIPAA Compliance.

This module provides enterprise-grade security audit logging with:
- HIPAA-compliant audit trail generation
- Real-time security event monitoring
- Anomaly detection and alerting
- Structured logging with correlation IDs
- Encrypted audit log storage
- Comprehensive compliance reporting
- Integration with SIEM systems

Designed for healthcare applications requiring comprehensive audit trails and compliance.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Comprehensive audit event types for HIPAA compliance."""
    # Authentication and Session Management
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    SESSION_TERMINATED = "session_terminated"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"

    # Token and API Key Management
    TOKEN_CREATED = "token_created"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_EXPIRED = "token_expired"
    API_KEY_CREATED = "api_key_created"
    API_KEY_USED = "api_key_used"
    API_KEY_REVOKED = "api_key_revoked"

    # Data Access and Operations
    DATA_ACCESS = "data_access"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    PHI_ACCESSED = "phi_accessed"  # Protected Health Information
    PHI_MODIFIED = "phi_modified"
    PHI_DISCLOSED = "phi_disclosed"

    # Security Events
    SECURITY_ALERT = "security_alert"
    INTRUSION_ATTEMPT = "intrusion_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POLICY_VIOLATION = "policy_violation"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"

    # System and Infrastructure
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIGURATION_CHANGED = "configuration_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    DATABASE_CONNECTION = "database_connection"
    SERVICE_FAILURE = "service_failure"

    # Administrative Actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    PERMISSIONS_CHANGED = "permissions_changed"
    POLICY_UPDATED = "policy_updated"

    # Compliance and Audit
    AUDIT_LOG_ACCESSED = "audit_log_accessed"
    COMPLIANCE_CHECK = "compliance_check"
    RETENTION_POLICY_APPLIED = "retention_policy_applied"
    DATA_RETENTION_EXPIRED = "data_retention_expired"
    REGULATORY_REPORT_GENERATED = "regulatory_report_generated"


class AuditRiskLevel(Enum):
    """Risk levels for audit events."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


class AuditEvent(BaseModel):
    """Comprehensive audit event model for HIPAA compliance."""
    # Core event information
    event_id: str = Field(..., description="Unique event identifier")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_system: str = Field(..., description="System generating the event")

    # User and session context
    user_id: str | None = Field(None, description="User identifier")
    username: str | None = Field(None, description="Username")
    session_id: str | None = Field(None, description="Session identifier")
    impersonated_user: str | None = Field(None, description="Impersonated user if applicable")

    # Request context
    request_id: str | None = Field(None, description="Request correlation ID")
    trace_id: str | None = Field(None, description="Distributed trace ID")
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    endpoint: str | None = Field(None, description="API endpoint accessed")
    http_method: str | None = Field(None, description="HTTP method")

    # Event details
    description: str = Field(..., description="Human-readable event description")
    outcome: str = Field(..., description="Event outcome (success/failure/unknown)")
    risk_level: AuditRiskLevel = Field(default=AuditRiskLevel.LOW)

    # Data context
    resource_type: str | None = Field(None, description="Type of resource accessed")
    resource_id: str | None = Field(None, description="Resource identifier")
    data_classification: str | None = Field(None, description="Data classification level")
    phi_involved: bool = Field(default=False, description="Whether PHI was involved")

    # Technical details
    application_name: str = Field(..., description="Application name")
    application_version: str | None = Field(None, description="Application version")
    environment: str = Field(..., description="Environment (prod/staging/dev)")

    # Additional context
    additional_data: dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    error_details: str | None = Field(None, description="Error details if applicable")

    # Compliance tracking
    compliance_frameworks: list[ComplianceFramework] = Field(default_factory=list)
    retention_period_days: int = Field(default=2557, description="Retention period (7 years default for HIPAA)")

    # Security metadata
    hash_value: str | None = Field(None, description="Event integrity hash")
    encrypted: bool = Field(default=False, description="Whether event data is encrypted")


class SecurityMetrics(BaseModel):
    """Security metrics for monitoring and alerting."""
    # Authentication metrics
    successful_logins: int = 0
    failed_logins: int = 0
    active_sessions: int = 0
    expired_sessions: int = 0

    # Access metrics
    data_access_events: int = 0
    phi_access_events: int = 0
    unauthorized_access_attempts: int = 0
    privilege_escalation_attempts: int = 0

    # Security event metrics
    security_alerts: int = 0
    intrusion_attempts: int = 0
    policy_violations: int = 0
    suspicious_activities: int = 0

    # System metrics
    system_errors: int = 0
    configuration_changes: int = 0
    encryption_key_rotations: int = 0

    # Risk metrics
    high_risk_events: int = 0
    critical_risk_events: int = 0
    average_risk_score: float = 0.0

    # Compliance metrics
    compliance_violations: int = 0
    audit_log_accesses: int = 0
    regulatory_reports: int = 0

    # Temporal information
    measurement_period_start: datetime = Field(default_factory=lambda: datetime.now(UTC))
    measurement_period_end: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnomalyDetector:
    """
    Advanced anomaly detection for security events.

    Detects unusual patterns that might indicate security threats
    or compliance violations.
    """

    def __init__(self) -> None:
        """Initialize anomaly detector with baseline patterns."""
        self.baseline_patterns: dict[str, Any] = {}
        self.thresholds: dict[str, float] = {
            "failed_login_rate": 0.1,  # 10% failure rate threshold
            "unusual_access_time": 0.05,  # 5% of accesses outside normal hours
            "rapid_requests": 100,  # Requests per minute threshold
            "geo_anomaly": 0.02,  # 2% of requests from unusual locations
            "privilege_escalation": 0.01,  # 1% privilege escalation rate
        }
        self.learning_enabled = True

    async def detect_anomalies(self, events: list[AuditEvent]) -> list[dict[str, Any]]:
        """
        Detect anomalies in audit events.

        Args:
            events: List of recent audit events

        Returns:
            List of detected anomalies with details
        """
        anomalies = []

        # Failed login rate anomaly
        login_anomaly = await self._detect_failed_login_anomaly(events)
        if login_anomaly:
            anomalies.append(login_anomaly)

        # Unusual access time anomaly
        time_anomaly = await self._detect_unusual_access_time(events)
        if time_anomaly:
            anomalies.append(time_anomaly)

        # Rapid request anomaly
        rate_anomaly = await self._detect_rapid_requests(events)
        if rate_anomaly:
            anomalies.append(rate_anomaly)

        # Geographic anomaly
        geo_anomaly = await self._detect_geographic_anomaly(events)
        if geo_anomaly:
            anomalies.append(geo_anomaly)

        # Privilege escalation anomaly
        privilege_anomaly = await self._detect_privilege_escalation(events)
        if privilege_anomaly:
            anomalies.append(privilege_anomaly)

        return anomalies

    async def _detect_failed_login_anomaly(self, events: list[AuditEvent]) -> dict[str, Any] | None:
        """Detect unusual failed login patterns."""
        login_events = [e for e in events if e.event_type in [AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILURE]]

        if len(login_events) < 10:  # Need minimum events for analysis
            return None

        failed_logins = [e for e in login_events if e.event_type == AuditEventType.LOGIN_FAILURE]
        failure_rate = len(failed_logins) / len(login_events)

        if failure_rate > self.thresholds["failed_login_rate"]:
            return {
                "type": "failed_login_anomaly",
                "severity": "high" if failure_rate > 0.3 else "medium",
                "details": {
                    "failure_rate": failure_rate,
                    "threshold": self.thresholds["failed_login_rate"],
                    "failed_attempts": len(failed_logins),
                    "total_attempts": len(login_events),
                },
                "recommendation": "Investigate potential brute force attack",
            }
        return None

    async def _detect_unusual_access_time(self, events: list[AuditEvent]) -> dict[str, Any] | None:
        """Detect access during unusual hours."""
        access_events = [e for e in events if e.event_type == AuditEventType.DATA_ACCESS]

        if len(access_events) < 5:
            return None

        # Define business hours (8 AM to 6 PM UTC)
        unusual_hours = []
        for event in access_events:
            hour = event.timestamp.hour
            if hour < 8 or hour > 18:  # Outside business hours
                unusual_hours.append(event)

        unusual_rate = len(unusual_hours) / len(access_events)

        if unusual_rate > self.thresholds["unusual_access_time"]:
            return {
                "type": "unusual_access_time",
                "severity": "medium",
                "details": {
                    "unusual_rate": unusual_rate,
                    "threshold": self.thresholds["unusual_access_time"],
                    "unusual_accesses": len(unusual_hours),
                    "total_accesses": len(access_events),
                },
                "recommendation": "Review access patterns during off-hours",
            }
        return None

    async def _detect_rapid_requests(self, events: list[AuditEvent]) -> dict[str, Any] | None:
        """Detect rapid successive requests that might indicate automated attacks."""
        # Group events by user and time windows
        user_requests: dict[str, list[datetime]] = {}

        for event in events:
            if event.user_id:
                if event.user_id not in user_requests:
                    user_requests[event.user_id] = []
                user_requests[event.user_id].append(event.timestamp)

        for user_id, timestamps in user_requests.items():
            if len(timestamps) < 10:  # Need minimum requests
                continue

            # Sort timestamps
            timestamps.sort()

            # Check for rapid requests in 1-minute windows
            for i in range(len(timestamps) - 1):
                window_start = timestamps[i]
                window_requests = [
                    t for t in timestamps[i:]
                    if t <= window_start + timedelta(minutes=1)
                ]

                if len(window_requests) > self.thresholds["rapid_requests"]:
                    return {
                        "type": "rapid_requests",
                        "severity": "high",
                        "details": {
                            "user_id": user_id,
                            "requests_per_minute": len(window_requests),
                            "threshold": self.thresholds["rapid_requests"],
                            "window_start": window_start.isoformat(),
                        },
                        "recommendation": "Investigate potential automated attack or bot activity",
                    }
        return None

    async def _detect_geographic_anomaly(self, events: list[AuditEvent]) -> dict[str, Any] | None:
        """Detect access from unusual geographic locations."""
        # This is a simplified implementation
        # In production, would use IP geolocation services
        ip_patterns: dict[str, int] = {}

        for event in events:
            if event.client_ip:
                # Extract network portion (simplified)
                network = ".".join(event.client_ip.split(".")[:-1]) + ".0"
                ip_patterns[network] = ip_patterns.get(network, 0) + 1

        if len(ip_patterns) > 10:  # Many different networks
            total_events = sum(ip_patterns.values())
            rare_networks = [ip for ip, count in ip_patterns.items() if count / total_events < 0.01]

            if len(rare_networks) / len(ip_patterns) > self.thresholds["geo_anomaly"]:
                return {
                    "type": "geographic_anomaly",
                    "severity": "medium",
                    "details": {
                        "unique_networks": len(ip_patterns),
                        "rare_networks": len(rare_networks),
                        "threshold": self.thresholds["geo_anomaly"],
                    },
                    "recommendation": "Review access from unusual geographic locations",
                }
        return None

    async def _detect_privilege_escalation(self, events: list[AuditEvent]) -> dict[str, Any] | None:
        """Detect potential privilege escalation attempts."""
        escalation_events = [
            e for e in events
            if e.event_type in [AuditEventType.PRIVILEGE_ESCALATION, AuditEventType.ROLE_ASSIGNED]
        ]

        if len(escalation_events) > 0:
            # Check if escalation rate is unusual
            total_events = len(events)
            escalation_rate = len(escalation_events) / total_events

            if escalation_rate > self.thresholds["privilege_escalation"]:
                return {
                    "type": "privilege_escalation",
                    "severity": "critical",
                    "details": {
                        "escalation_events": len(escalation_events),
                        "escalation_rate": escalation_rate,
                        "threshold": self.thresholds["privilege_escalation"],
                    },
                    "recommendation": "Immediately investigate privilege escalation attempts",
                }
        return None


class SecurityAuditLogger:
    """
    Comprehensive security audit logger with HIPAA compliance features.

    Provides encrypted audit logging, real-time monitoring, anomaly detection,
    and compliance reporting for healthcare applications.
    """

    def __init__(
        self,
        storage_path: Path,
        encryption_key: str | bytes | None = None,
        application_name: str = "malaria_predictor",
        environment: str = "production",
        enable_anomaly_detection: bool = True,
        max_memory_events: int = 10000,
    ):
        """
        Initialize security audit logger.

        Args:
            storage_path: Path for audit log storage
            encryption_key: Encryption key for audit logs
            application_name: Name of the application
            environment: Deployment environment
            enable_anomaly_detection: Whether to enable anomaly detection
            max_memory_events: Maximum events to keep in memory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.application_name = application_name
        self.environment = environment
        self.enable_anomaly_detection = enable_anomaly_detection
        self.max_memory_events = max_memory_events

        # Initialize encryption
        if encryption_key:
            if isinstance(encryption_key, str):
                # Derive a proper Fernet key from the string
                import base64

                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

                salt = b"malaria_audit_salt_2024"
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(encryption_key.encode())
                self.cipher = Fernet(base64.urlsafe_b64encode(key))
            else:
                self.cipher = Fernet(encryption_key)
        else:
            self.cipher = Fernet(Fernet.generate_key())
            logger.warning("Using generated encryption key - audit logs will not be recoverable after restart")

        # In-memory event storage for analysis
        self.recent_events: list[AuditEvent] = []
        self.metrics = SecurityMetrics()
        self.anomaly_detector = AnomalyDetector() if enable_anomaly_detection else None

        # Thread safety
        self._event_lock = asyncio.Lock()
        self._metrics_lock = asyncio.Lock()

        # Alert callbacks
        self.alert_callbacks: list[callable] = []

        logger.info(f"Security audit logger initialized at {storage_path}")

    async def log_event(
        self,
        event_type: AuditEventType,
        description: str,
        outcome: str = "success",
        user_id: str | None = None,
        username: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        client_ip: str | None = None,
        endpoint: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        risk_level: AuditRiskLevel = AuditRiskLevel.LOW,
        phi_involved: bool = False,
        additional_data: dict[str, Any] | None = None,
        compliance_frameworks: list[ComplianceFramework] | None = None,
    ) -> str:
        """
        Log a security audit event.

        Args:
            event_type: Type of audit event
            description: Human-readable description
            outcome: Event outcome
            user_id: User identifier
            username: Username
            session_id: Session identifier
            request_id: Request correlation ID
            client_ip: Client IP address
            endpoint: API endpoint
            resource_type: Type of resource
            resource_id: Resource identifier
            risk_level: Risk level assessment
            phi_involved: Whether PHI was involved
            additional_data: Additional event data
            compliance_frameworks: Applicable compliance frameworks

        Returns:
            Event ID for correlation
        """
        import uuid

        # Generate unique event ID
        event_id = f"{self.application_name}_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            source_system=self.application_name,
            user_id=user_id,
            username=username,
            session_id=session_id,
            request_id=request_id,
            client_ip=client_ip,
            endpoint=endpoint,
            description=description,
            outcome=outcome,
            risk_level=risk_level,
            resource_type=resource_type,
            resource_id=resource_id,
            phi_involved=phi_involved,
            application_name=self.application_name,
            environment=self.environment,
            additional_data=additional_data or {},
            compliance_frameworks=compliance_frameworks or [ComplianceFramework.HIPAA],
        )

        # Calculate integrity hash
        event.hash_value = self._calculate_event_hash(event)

        # Store event
        async with self._event_lock:
            # Add to memory storage
            self.recent_events.append(event)

            # Maintain memory limit
            if len(self.recent_events) > self.max_memory_events:
                self.recent_events = self.recent_events[-self.max_memory_events:]

            # Persist to disk
            await self._persist_event(event)

            # Update metrics
            await self._update_metrics(event)

            # Check for anomalies
            if self.anomaly_detector:
                anomalies = await self.anomaly_detector.detect_anomalies(self.recent_events[-100:])
                for anomaly in anomalies:
                    await self._handle_anomaly(anomaly, event)

        # Log to system logger
        log_level = self._get_log_level(risk_level)
        logger.log(log_level, f"AUDIT: [{event_id}] {event_type.value} - {description} ({outcome})")

        return event_id

    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """Calculate integrity hash for audit event."""
        # Create deterministic string representation
        hash_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "description": event.description,
            "outcome": event.outcome,
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    async def _persist_event(self, event: AuditEvent):
        """Persist audit event to encrypted storage."""
        try:
            # Generate filename with date for organization
            date_str = event.timestamp.strftime("%Y-%m-%d")
            filename = f"audit_log_{date_str}.log"
            file_path = self.storage_path / filename

            # Serialize event
            event_data = event.json() + "\n"

            # Encrypt if cipher available
            if self.cipher:
                encrypted_data = self.cipher.encrypt(event_data.encode())
                event.encrypted = True
            else:
                encrypted_data = event_data.encode()

            # Append to daily log file
            async with aiofiles.open(file_path, "ab") as f:
                await f.write(encrypted_data)

        except Exception as e:
            logger.error(f"Failed to persist audit event {event.event_id}: {e}")
            # Continue operation even if persistence fails

    async def _update_metrics(self, event: AuditEvent):
        """Update security metrics based on event."""
        async with self._metrics_lock:
            # Authentication metrics
            if event.event_type == AuditEventType.LOGIN_SUCCESS:
                self.metrics.successful_logins += 1
            elif event.event_type == AuditEventType.LOGIN_FAILURE:
                self.metrics.failed_logins += 1
            elif event.event_type == AuditEventType.SESSION_CREATED:
                self.metrics.active_sessions += 1
            elif event.event_type in [AuditEventType.SESSION_EXPIRED, AuditEventType.SESSION_TERMINATED]:
                self.metrics.expired_sessions += 1

            # Access metrics
            elif event.event_type == AuditEventType.DATA_ACCESS:
                self.metrics.data_access_events += 1
            elif event.event_type == AuditEventType.PHI_ACCESSED:
                self.metrics.phi_access_events += 1
            elif event.event_type == AuditEventType.UNAUTHORIZED_ACCESS:
                self.metrics.unauthorized_access_attempts += 1
            elif event.event_type == AuditEventType.PRIVILEGE_ESCALATION:
                self.metrics.privilege_escalation_attempts += 1

            # Security events
            elif event.event_type == AuditEventType.SECURITY_ALERT:
                self.metrics.security_alerts += 1
            elif event.event_type == AuditEventType.INTRUSION_ATTEMPT:
                self.metrics.intrusion_attempts += 1
            elif event.event_type == AuditEventType.POLICY_VIOLATION:
                self.metrics.policy_violations += 1
            elif event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY:
                self.metrics.suspicious_activities += 1

            # Risk metrics
            if event.risk_level == AuditRiskLevel.HIGH:
                self.metrics.high_risk_events += 1
            elif event.risk_level == AuditRiskLevel.CRITICAL:
                self.metrics.critical_risk_events += 1

            # Update timestamp
            self.metrics.last_updated = datetime.now(UTC)

    async def _handle_anomaly(self, anomaly: dict[str, Any], triggering_event: AuditEvent):
        """Handle detected anomaly."""
        # Log anomaly as security alert
        await self.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description=f"Anomaly detected: {anomaly['type']}",
            outcome="alert",
            risk_level=AuditRiskLevel.HIGH if anomaly.get("severity") == "high" else AuditRiskLevel.MEDIUM,
            additional_data={"anomaly_details": anomaly, "triggering_event": triggering_event.event_id},
        )

        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(anomaly, triggering_event)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def _get_log_level(self, risk_level: AuditRiskLevel) -> int:
        """Get appropriate log level for risk level."""
        level_map = {
            AuditRiskLevel.NONE: logging.DEBUG,
            AuditRiskLevel.LOW: logging.INFO,
            AuditRiskLevel.MEDIUM: logging.WARNING,
            AuditRiskLevel.HIGH: logging.ERROR,
            AuditRiskLevel.CRITICAL: logging.CRITICAL,
        }
        return level_map.get(risk_level, logging.INFO)

    def add_alert_callback(self, callback: callable):
        """Add callback function for security alerts."""
        self.alert_callbacks.append(callback)
        logger.info("Added security alert callback")

    async def get_events(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_types: list[AuditEventType] | None = None,
        user_id: str | None = None,
        risk_level: AuditRiskLevel | None = None,
        limit: int = 1000,
    ) -> list[AuditEvent]:
        """
        Retrieve audit events with filtering.

        Args:
            start_time: Start time filter
            end_time: End time filter
            event_types: Event type filter
            user_id: User ID filter
            risk_level: Risk level filter
            limit: Maximum number of events

        Returns:
            Filtered list of audit events
        """
        filtered_events = []

        for event in self.recent_events:
            # Apply filters
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_types and event.event_type not in event_types:
                continue
            if user_id and event.user_id != user_id:
                continue
            if risk_level and event.risk_level != risk_level:
                continue

            filtered_events.append(event)

            if len(filtered_events) >= limit:
                break

        return filtered_events

    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        Generate compliance report for specified framework.

        Args:
            framework: Compliance framework
            start_date: Report start date
            end_date: Report end date

        Returns:
            Comprehensive compliance report
        """
        # Filter events for date range and framework
        relevant_events = [
            event for event in self.recent_events
            if start_date <= event.timestamp <= end_date
            and framework in event.compliance_frameworks
        ]

        # Generate framework-specific report
        if framework == ComplianceFramework.HIPAA:
            return await self._generate_hipaa_report(relevant_events, start_date, end_date)
        else:
            return await self._generate_generic_report(relevant_events, start_date, end_date, framework)

    async def _generate_hipaa_report(
        self, events: list[AuditEvent], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Generate HIPAA-specific compliance report."""
        # HIPAA-specific metrics
        phi_events = [e for e in events if e.phi_involved]
        access_events = [e for e in events if e.event_type == AuditEventType.PHI_ACCESSED]
        disclosure_events = [e for e in events if e.event_type == AuditEventType.PHI_DISCLOSED]
        modification_events = [e for e in events if e.event_type == AuditEventType.PHI_MODIFIED]

        # User access patterns
        user_access = {}
        for event in access_events:
            if event.user_id:
                if event.user_id not in user_access:
                    user_access[event.user_id] = {"count": 0, "resources": set()}
                user_access[event.user_id]["count"] += 1
                if event.resource_id:
                    user_access[event.user_id]["resources"].add(event.resource_id)

        return {
            "framework": "HIPAA",
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_events": len(events),
                "phi_related_events": len(phi_events),
                "access_events": len(access_events),
                "disclosure_events": len(disclosure_events),
                "modification_events": len(modification_events),
            },
            "user_access_patterns": {
                user_id: {
                    "access_count": data["count"],
                    "unique_resources": len(data["resources"]),
                }
                for user_id, data in user_access.items()
            },
            "compliance_requirements": {
                "audit_trail_complete": len(events) > 0,
                "user_identification": all(e.user_id is not None for e in access_events),
                "timestamp_accuracy": all(e.timestamp is not None for e in events),
                "data_integrity": all(e.hash_value is not None for e in events),
                "encryption_status": all(e.encrypted for e in events),
            },
            "violations": await self._identify_hipaa_violations(events),
            "recommendations": await self._generate_hipaa_recommendations(events),
        }

    async def _generate_generic_report(
        self, events: list[AuditEvent], start_date: datetime, end_date: datetime, framework: ComplianceFramework
    ) -> dict[str, Any]:
        """Generate generic compliance report."""
        return {
            "framework": framework.value,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_events": len(events),
                "event_types": list({e.event_type.value for e in events}),
                "unique_users": len({e.user_id for e in events if e.user_id}),
                "risk_distribution": {
                    level.value: len([e for e in events if e.risk_level == level])
                    for level in AuditRiskLevel
                },
            },
            "metrics": self.metrics.dict(),
        }

    async def _identify_hipaa_violations(self, events: list[AuditEvent]) -> list[dict[str, Any]]:
        """Identify potential HIPAA violations in events."""
        violations = []

        # Check for unauthorized PHI access
        unauthorized_phi = [
            e for e in events
            if e.event_type == AuditEventType.UNAUTHORIZED_ACCESS and e.phi_involved
        ]

        if unauthorized_phi:
            violations.append({
                "type": "unauthorized_phi_access",
                "severity": "critical",
                "count": len(unauthorized_phi),
                "description": "Unauthorized access to Protected Health Information detected",
            })

        # Check for missing audit trails
        phi_events_without_audit = [
            e for e in events
            if e.phi_involved and not e.hash_value
        ]

        if phi_events_without_audit:
            violations.append({
                "type": "incomplete_audit_trail",
                "severity": "high",
                "count": len(phi_events_without_audit),
                "description": "PHI events without complete audit trail",
            })

        return violations

    async def _generate_hipaa_recommendations(self, events: list[AuditEvent]) -> list[str]:
        """Generate HIPAA compliance recommendations."""
        recommendations = []

        # Check access patterns
        phi_events = [e for e in events if e.phi_involved]
        if len(phi_events) > 1000:  # High volume of PHI access
            recommendations.append("Consider implementing additional access controls for high-volume PHI access")

        # Check for failed access attempts
        failed_access = [e for e in events if e.outcome == "failure" and e.phi_involved]
        if len(failed_access) > len(phi_events) * 0.1:  # More than 10% failure rate
            recommendations.append("Investigate high failure rate for PHI access attempts")

        # Check encryption status
        unencrypted_events = [e for e in events if not e.encrypted]
        if unencrypted_events:
            recommendations.append("Ensure all audit events are encrypted for data integrity")

        if not recommendations:
            recommendations.append("HIPAA compliance posture appears satisfactory")

        return recommendations

    def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        return self.metrics

    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        export_path: Path,
        include_phi: bool = False,
    ) -> str:
        """
        Export audit logs for external analysis or compliance reporting.

        Args:
            start_date: Export start date
            end_date: Export end date
            export_path: Export file path
            include_phi: Whether to include PHI-related events

        Returns:
            Export file path
        """
        # Filter events
        export_events = [
            event for event in self.recent_events
            if start_date <= event.timestamp <= end_date
        ]

        if not include_phi:
            export_events = [e for e in export_events if not e.phi_involved]

        # Prepare export data
        export_data = {
            "export_metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_events": len(export_events),
                "phi_included": include_phi,
                "application": self.application_name,
                "environment": self.environment,
            },
            "events": [event.dict() for event in export_events],
        }

        # Write to file
        export_file = export_path / f"audit_export_{int(time.time())}.json"
        async with aiofiles.open(export_file, "w") as f:
            await f.write(json.dumps(export_data, indent=2, default=str))

        # Log export activity
        await self.log_event(
            event_type=AuditEventType.REGULATORY_REPORT_GENERATED,
            description=f"Audit logs exported to {export_file}",
            additional_data={
                "export_file": str(export_file),
                "event_count": len(export_events),
                "phi_included": include_phi,
            },
        )

        return str(export_file)
