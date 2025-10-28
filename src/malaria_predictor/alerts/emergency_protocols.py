"""Emergency response protocols for critical malaria alerts.

Handles emergency escalation procedures, health authority notifications,
and automated response protocols for critical malaria risk situations.
"""

import logging
from datetime import datetime
from typing import Any

import aiohttp
from pydantic import BaseModel

from ..config import settings
from ..database.models import Alert
from .notification_service import NotificationRequest, notification_service

logger = logging.getLogger(__name__)


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    name: str
    role: str  # health_officer, epidemiologist, emergency_coordinator
    email: str
    phone: str
    organization: str
    priority_level: int = 1  # 1=highest, 5=lowest
    notification_methods: list[str] = ["email", "sms"]


class HealthAuthorityAPI(BaseModel):
    """Health authority API configuration."""

    name: str
    api_endpoint: str
    api_key: str
    format: str = "json"  # json, xml, fhir
    timeout_seconds: int = 30
    retry_attempts: int = 3
    verify_ssl: bool = True


class EmergencyProtocol(BaseModel):
    """Emergency response protocol configuration."""

    protocol_id: str
    name: str
    description: str
    trigger_conditions: dict  # Risk level, geographic area, etc.
    escalation_levels: list[dict]  # Different escalation stages
    response_actions: list[str]  # Automated actions to take
    contact_hierarchy: list[EmergencyContact]
    health_authorities: list[HealthAuthorityAPI]

    # Protocol settings
    auto_escalation_minutes: int = 60  # Time before auto-escalation
    max_escalation_level: int = 3
    require_human_approval: bool = True
    cooldown_period_hours: int = 24


class EmergencyResponseProtocolManager:
    """Manages emergency response protocols for critical malaria alerts.

    Provides functionality for:
    - Emergency protocol definition and management
    - Automated escalation procedures
    - Health authority notification integration
    - Response tracking and documentation
    - Emergency contact management
    """

    def __init__(self) -> None:
        """Initialize the emergency response protocol manager."""
        self.settings = settings

        # Load emergency protocols from configuration
        self.protocols = self._load_emergency_protocols()

        # Statistics tracking
        self.stats = {
            "emergency_alerts_processed": 0,
            "escalations_triggered": 0,
            "health_authorities_notified": 0,
            "emergency_contacts_reached": 0,
            "protocol_executions": 0,
            "avg_response_time_minutes": 0.0
        }

        # Active escalations tracking
        self.active_escalations: dict[str, Any] = {}

    async def process_emergency_alert(self, alert: Alert) -> dict:
        """Process an emergency alert and execute appropriate protocols.

        Args:
            alert: Emergency alert to process

        Returns:
            Dictionary with execution results
        """
        start_time = datetime.now()

        try:
            # Determine applicable protocols
            applicable_protocols = self._get_applicable_protocols(alert)

            if not applicable_protocols:
                logger.warning(f"No emergency protocols found for alert {alert.id}")
                return {"executed_protocols": [], "success": False}

            execution_results = []

            for protocol in applicable_protocols:
                result = await self._execute_emergency_protocol(alert, protocol)
                execution_results.append(result)

            # Update statistics
            self.stats["emergency_alerts_processed"] += 1
            self.stats["protocol_executions"] += len(execution_results)

            processing_time = (datetime.now() - start_time).total_seconds() / 60
            self._update_avg_response_time(processing_time)

            logger.info(
                f"Processed emergency alert {alert.id} with "
                f"{len(execution_results)} protocols in {processing_time:.2f} minutes"
            )

            return {
                "alert_id": alert.id,
                "executed_protocols": execution_results,
                "processing_time_minutes": processing_time,
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to process emergency alert {alert.id}: {e}")
            return {
                "alert_id": alert.id,
                "executed_protocols": [],
                "error": str(e),
                "success": False
            }

    async def escalate_alert(self, alert: Alert, escalation_level: int = 1) -> bool:
        """Escalate an alert to the next level.

        Args:
            alert: Alert to escalate
            escalation_level: Target escalation level

        Returns:
            True if escalation successful, False otherwise
        """
        try:
            protocols = self._get_applicable_protocols(alert)

            for protocol in protocols:
                if escalation_level <= protocol.max_escalation_level:
                    # Record escalation
                    escalation_key = f"{alert.id}_{protocol.protocol_id}"
                    self.active_escalations[escalation_key] = {
                        "alert_id": alert.id,
                        "protocol_id": protocol.protocol_id,
                        "escalation_level": escalation_level,
                        "escalated_at": datetime.now(),
                        "status": "active"
                    }

                    # Execute escalation actions
                    escalation_actions = protocol.escalation_levels[escalation_level - 1]
                    await self._execute_escalation_actions(alert, protocol, escalation_actions)

                    self.stats["escalations_triggered"] += 1

                    logger.info(
                        f"Escalated alert {alert.id} to level {escalation_level} "
                        f"for protocol {protocol.protocol_id}"
                    )

                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to escalate alert {alert.id}: {e}")
            return False

    async def notify_health_authorities(
        self,
        alert: Alert,
        protocol: EmergencyProtocol
    ) -> list[dict]:
        """Notify health authorities about an emergency alert.

        Args:
            alert: Emergency alert
            protocol: Emergency protocol

        Returns:
            List of notification results
        """
        results = []

        for authority in protocol.health_authorities:
            try:
                # Prepare notification data
                notification_data = {
                    "alert_id": alert.id,
                    "risk_level": alert.risk_level,
                    "location": {
                        "latitude": alert.latitude,
                        "longitude": alert.longitude,
                        "area": alert.area_name
                    },
                    "timestamp": alert.created_at.isoformat(),
                    "message": alert.message,
                    "protocol_id": protocol.protocol_id
                }

                result = await self._send_authority_notification(authority, notification_data)
                results.append(result)

                if result["success"]:
                    self.stats["health_authorities_notified"] += 1

            except Exception as e:
                logger.error(f"Failed to notify authority {authority.name}: {e}")
                results.append({
                    "authority": authority.name,
                    "success": False,
                    "error": str(e)
                })

        return results

    async def contact_emergency_personnel(
        self,
        alert: Alert,
        protocol: EmergencyProtocol,
        escalation_level: int = 1
    ) -> list[dict]:
        """Contact emergency personnel according to protocol.

        Args:
            alert: Emergency alert
            protocol: Emergency protocol
            escalation_level: Current escalation level

        Returns:
            List of contact results
        """
        results = []

        # Filter contacts by escalation level
        applicable_contacts = [
            contact for contact in protocol.contact_hierarchy
            if contact.priority_level <= escalation_level
        ]

        for contact in applicable_contacts:
            try:
                # Send notifications via configured methods
                for method in contact.notification_methods:
                    notification_request = NotificationRequest(
                        recipient_id=contact.email,
                        message=f"EMERGENCY ALERT: {alert.message}",
                        channel=method,
                        priority="emergency",
                        metadata={
                            "alert_id": alert.id,
                            "contact_name": contact.name,
                            "contact_role": contact.role,
                            "escalation_level": escalation_level
                        }
                    )

                    result = await notification_service.send_notification(notification_request)
                    results.append({
                        "contact": contact.name,
                        "method": method,
                        "success": result.success,
                        "details": result.details
                    })

                    if result.success:
                        self.stats["emergency_contacts_reached"] += 1

            except Exception as e:
                logger.error(f"Failed to contact {contact.name}: {e}")
                results.append({
                    "contact": contact.name,
                    "method": "unknown",
                    "success": False,
                    "error": str(e)
                })

        return results

    def _load_emergency_protocols(self) -> list[EmergencyProtocol]:
        """Load emergency protocols from configuration.

        Returns:
            List of emergency protocols
        """
        # Default emergency protocols for malaria alerts
        protocols = [
            EmergencyProtocol(
                protocol_id="malaria_outbreak",
                name="Malaria Outbreak Response",
                description="Response protocol for potential malaria outbreaks",
                trigger_conditions={
                    "risk_level": {"min": 0.8},
                    "affected_population": {"min": 1000}
                },
                escalation_levels=[
                    {"level": 1, "actions": ["notify_local_health"], "time_limit": 30},
                    {"level": 2, "actions": ["notify_regional_health", "deploy_resources"], "time_limit": 60},
                    {"level": 3, "actions": ["notify_national_health", "emergency_response"], "time_limit": 120}
                ],
                response_actions=[
                    "immediate_assessment",
                    "vector_control",
                    "case_investigation",
                    "preventive_measures"
                ],
                contact_hierarchy=[
                    EmergencyContact(
                        name="Local Health Officer",
                        role="health_officer",
                        email="health.officer@example.com",
                        phone="+1234567890",
                        organization="Local Health Department",
                        priority_level=1
                    )
                ],
                health_authorities=[
                    HealthAuthorityAPI(
                        name="National Health Authority",
                        api_endpoint="https://health.gov/api/alerts",
                        api_key="demo_key"
                    )
                ]
            )
        ]

        return protocols

    def _get_applicable_protocols(self, alert: Alert) -> list[EmergencyProtocol]:
        """Get protocols applicable to the given alert.

        Args:
            alert: Alert to check

        Returns:
            List of applicable protocols
        """
        applicable = []

        for protocol in self.protocols:
            if self._matches_trigger_conditions(alert, protocol.trigger_conditions):
                applicable.append(protocol)

        return applicable

    def _matches_trigger_conditions(self, alert: Alert, conditions: dict) -> bool:
        """Check if alert matches protocol trigger conditions.

        Args:
            alert: Alert to check
            conditions: Trigger conditions to evaluate

        Returns:
            True if conditions are met
        """
        # Check risk level condition
        if "risk_level" in conditions:
            risk_condition = conditions["risk_level"]
            if "min" in risk_condition and alert.risk_level < risk_condition["min"]:
                return False
            if "max" in risk_condition and alert.risk_level > risk_condition["max"]:
                return False

        # Additional condition checks can be added here

        return True

    async def _execute_emergency_protocol(self, alert: Alert, protocol: EmergencyProtocol) -> dict:
        """Execute a single emergency protocol.

        Args:
            alert: Emergency alert
            protocol: Protocol to execute

        Returns:
            Execution result
        """
        try:
            execution_start = datetime.now()

            # Notify health authorities
            authority_results = await self.notify_health_authorities(alert, protocol)

            # Contact emergency personnel
            contact_results = await self.contact_emergency_personnel(alert, protocol)

            execution_time = (datetime.now() - execution_start).total_seconds()

            return {
                "protocol_id": protocol.protocol_id,
                "protocol_name": protocol.name,
                "authority_notifications": authority_results,
                "personnel_contacts": contact_results,
                "execution_time_seconds": execution_time,
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to execute protocol {protocol.protocol_id}: {e}")
            return {
                "protocol_id": protocol.protocol_id,
                "protocol_name": protocol.name,
                "error": str(e),
                "success": False
            }

    async def _execute_escalation_actions(
        self,
        alert: Alert,
        protocol: EmergencyProtocol,
        escalation_actions: dict
    ) -> None:
        """Execute actions for a specific escalation level.

        Args:
            alert: Emergency alert
            protocol: Emergency protocol
            escalation_actions: Actions to execute
        """
        actions = escalation_actions.get("actions", [])

        for action in actions:
            try:
                if action == "notify_local_health":
                    await self.notify_health_authorities(alert, protocol)
                elif action == "notify_regional_health":
                    # Extended notification logic
                    pass
                elif action == "notify_national_health":
                    # National level notification logic
                    pass
                elif action == "deploy_resources":
                    # Resource deployment logic
                    pass
                elif action == "emergency_response":
                    # Full emergency response activation
                    pass

            except Exception as e:
                logger.error(f"Failed to execute escalation action {action}: {e}")

    async def _send_authority_notification(
        self,
        authority: HealthAuthorityAPI,
        notification_data: dict
    ) -> dict:
        """Send notification to a health authority.

        Args:
            authority: Health authority configuration
            notification_data: Data to send

        Returns:
            Notification result
        """
        try:
            timeout = aiohttp.ClientTimeout(total=authority.timeout_seconds)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Authorization": f"Bearer {authority.api_key}",
                    "Content-Type": "application/json"
                }

                async with session.post(
                    authority.api_endpoint,
                    json=notification_data,
                    headers=headers,
                    ssl=authority.verify_ssl
                ) as response:
                    if response.status == 200:
                        return {
                            "authority": authority.name,
                            "success": True,
                            "status_code": response.status
                        }
                    else:
                        return {
                            "authority": authority.name,
                            "success": False,
                            "status_code": response.status,
                            "error": await response.text()
                        }

        except Exception as e:
            return {
                "authority": authority.name,
                "success": False,
                "error": str(e)
            }

    def _update_avg_response_time(self, processing_time: float) -> None:
        """Update average response time statistics.

        Args:
            processing_time: Processing time in minutes
        """
        current_avg = self.stats["avg_response_time_minutes"]
        processed_count = self.stats["emergency_alerts_processed"]

        if processed_count == 1:
            self.stats["avg_response_time_minutes"] = processing_time
        else:
            # Calculate running average
            self.stats["avg_response_time_minutes"] = (
                (current_avg * (processed_count - 1) + processing_time) / processed_count
            )


# Global instance
emergency_protocol_manager = EmergencyResponseProtocolManager()
