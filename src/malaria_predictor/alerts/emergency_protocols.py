"""Emergency response protocols for critical malaria alerts.

Handles emergency escalation procedures, health authority notifications,
and automated response protocols for critical malaria risk situations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database.models import Alert, AlertConfiguration, NotificationDelivery
from ..database.session import get_database
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
    notification_methods: List[str] = ["email", "sms"]


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
    trigger_conditions: Dict  # Risk level, geographic area, etc.
    escalation_levels: List[Dict]  # Different escalation stages
    response_actions: List[str]  # Automated actions to take
    contact_hierarchy: List[EmergencyContact]
    health_authorities: List[HealthAuthorityAPI]
    
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
    
    def __init__(self):
        """Initialize the emergency response protocol manager."""
        self.settings = get_settings()
        
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
        self.active_escalations = {}
    
    async def process_emergency_alert(self, alert: Alert) -> Dict:
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
            escalation_key = f"alert_{alert.id}"
            
            # Check if alert is already being escalated
            if escalation_key in self.active_escalations:
                current_level = self.active_escalations[escalation_key]["level"]
                if escalation_level <= current_level:
                    logger.info(f"Alert {alert.id} already at escalation level {current_level}")
                    return True
            
            # Find applicable protocol
            protocol = self._get_primary_protocol_for_alert(alert)
            if not protocol:
                logger.error(f"No protocol found for alert {alert.id} escalation")
                return False
            
            # Execute escalation level
            if escalation_level <= len(protocol.escalation_levels):
                escalation_config = protocol.escalation_levels[escalation_level - 1]
                
                # Record escalation
                self.active_escalations[escalation_key] = {
                    "alert_id": alert.id,
                    "protocol_id": protocol.protocol_id,
                    "level": escalation_level,
                    "started_at": datetime.now(),
                    "config": escalation_config
                }
                
                # Update alert record
                alert.escalated_at = datetime.now()
                alert.escalation_level = escalation_level
                
                # Execute escalation actions
                await self._execute_escalation_level(alert, protocol, escalation_config)
                
                self.stats["escalations_triggered"] += 1
                
                logger.info(f"Escalated alert {alert.id} to level {escalation_level}")
                return True
            
            else:
                logger.error(f"Invalid escalation level {escalation_level} for protocol {protocol.protocol_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to escalate alert {alert.id}: {e}")
            return False
    
    async def notify_health_authorities(
        self,
        alert: Alert,
        protocol: EmergencyProtocol
    ) -> List[Dict]:
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
                result = await self._notify_health_authority(alert, authority)
                results.append({
                    "authority": authority.name,
                    "success": result["success"],
                    "message_id": result.get("message_id"),
                    "error": result.get("error")
                })
                
                if result["success"]:
                    self.stats["health_authorities_notified"] += 1
                
            except Exception as e:
                logger.error(f"Failed to notify health authority {authority.name}: {e}")
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
    ) -> List[Dict]:
        """Contact emergency personnel according to protocol.
        
        Args:
            alert: Emergency alert
            protocol: Emergency protocol
            escalation_level: Current escalation level
            
        Returns:
            List of contact results
        """
        results = []
        
        # Filter contacts by escalation level priority
        relevant_contacts = [
            contact for contact in protocol.contact_hierarchy
            if contact.priority_level <= escalation_level
        ]
        
        for contact in relevant_contacts:
            try:
                contact_results = await self._contact_emergency_person(alert, contact)
                results.extend(contact_results)
                
                successful_contacts = sum(1 for r in contact_results if r["success"])
                self.stats["emergency_contacts_reached"] += successful_contacts
                
            except Exception as e:
                logger.error(f"Failed to contact emergency person {contact.name}: {e}")
                results.append({
                    "contact": contact.name,
                    "method": "error",
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _load_emergency_protocols(self) -> List[EmergencyProtocol]:
        """Load emergency protocols from configuration.
        
        Returns:
            List of emergency protocols
        """
        try:
            # Default protocol for critical malaria alerts
            default_protocol = EmergencyProtocol(
                protocol_id="malaria_critical",
                name="Critical Malaria Risk Protocol",
                description="Emergency response for critical malaria risk alerts",
                trigger_conditions={
                    "risk_score": {"gte": 0.9},
                    "alert_level": "critical",
                    "prediction_confidence": {"gte": 0.8}
                },
                escalation_levels=[
                    {
                        "level": 1,
                        "name": "Initial Response",
                        "actions": ["notify_local_health_officer", "alert_emergency_contacts"],
                        "timeout_minutes": 30
                    },
                    {
                        "level": 2,
                        "name": "Regional Escalation",
                        "actions": ["notify_regional_health_authority", "activate_response_team"],
                        "timeout_minutes": 60
                    },
                    {
                        "level": 3,
                        "name": "National Emergency",
                        "actions": ["notify_national_health_ministry", "activate_emergency_response"],
                        "timeout_minutes": 120
                    }
                ],
                response_actions=[
                    "immediate_vector_control",
                    "emergency_case_management",
                    "community_mobilization",
                    "surveillance_enhancement"
                ],
                contact_hierarchy=[
                    EmergencyContact(
                        name="Local Health Officer",
                        role="health_officer",
                        email="health.officer@local.gov",
                        phone="+1234567890",
                        organization="Local Health Department",
                        priority_level=1,
                        notification_methods=["email", "sms"]
                    ),
                    EmergencyContact(
                        name="Regional Epidemiologist",
                        role="epidemiologist",
                        email="epidemiologist@region.gov",
                        phone="+1234567891",
                        organization="Regional Health Authority",
                        priority_level=2,
                        notification_methods=["email", "sms"]
                    ),
                    EmergencyContact(
                        name="Emergency Coordinator",
                        role="emergency_coordinator",
                        email="emergency@national.gov",
                        phone="+1234567892",
                        organization="National Health Ministry",
                        priority_level=3,
                        notification_methods=["email", "sms", "voice"]
                    )
                ],
                health_authorities=[
                    HealthAuthorityAPI(
                        name="WHO Disease Outbreak News",
                        api_endpoint="https://who.int/api/outbreak-notification",
                        api_key="who_api_key_placeholder",
                        format="json"
                    ),
                    HealthAuthorityAPI(
                        name="National Health Information System",
                        api_endpoint="https://nhis.gov/api/emergency-alerts",
                        api_key="nhis_api_key_placeholder",
                        format="fhir"
                    )
                ]
            )
            
            # Try to load additional protocols from settings
            protocols = [default_protocol]
            
            # Add protocol for outbreak detection
            outbreak_protocol = EmergencyProtocol(
                protocol_id="malaria_outbreak",
                name="Malaria Outbreak Detection Protocol",
                description="Response protocol for detected malaria outbreaks",
                trigger_conditions={
                    "alert_type": "outbreak_detection",
                    "risk_score": {"gte": 0.8},
                    "affected_population": {"gte": 1000}
                },
                escalation_levels=[
                    {
                        "level": 1,
                        "name": "Outbreak Confirmation",
                        "actions": ["verify_outbreak", "isolate_cases", "contact_tracing"],
                        "timeout_minutes": 60
                    },
                    {
                        "level": 2,
                        "name": "Containment Response",
                        "actions": ["mass_treatment", "vector_control", "public_health_measures"],
                        "timeout_minutes": 180
                    }
                ],
                response_actions=[
                    "rapid_diagnostic_testing",
                    "case_management_protocols",
                    "vector_surveillance",
                    "community_education"
                ],
                contact_hierarchy=default_protocol.contact_hierarchy,
                health_authorities=default_protocol.health_authorities
            )
            
            protocols.append(outbreak_protocol)
            
            logger.info(f"Loaded {len(protocols)} emergency protocols")
            return protocols
            
        except Exception as e:
            logger.error(f"Failed to load emergency protocols: {e}")
            return []
    
    def _get_applicable_protocols(self, alert: Alert) -> List[EmergencyProtocol]:
        """Get protocols applicable to an alert.
        
        Args:
            alert: Alert to check
            
        Returns:
            List of applicable protocols
        """
        applicable = []
        
        for protocol in self.protocols:
            if self._protocol_matches_alert(protocol, alert):
                applicable.append(protocol)
        
        return applicable
    
    def _protocol_matches_alert(self, protocol: EmergencyProtocol, alert: Alert) -> bool:
        """Check if a protocol matches an alert.
        
        Args:
            protocol: Protocol to check
            alert: Alert to match against
            
        Returns:
            True if protocol matches, False otherwise
        """
        conditions = protocol.trigger_conditions
        
        # Check risk score
        if "risk_score" in conditions and alert.risk_score:
            risk_condition = conditions["risk_score"]
            if isinstance(risk_condition, dict):
                if "gte" in risk_condition and alert.risk_score < risk_condition["gte"]:
                    return False
                if "lte" in risk_condition and alert.risk_score > risk_condition["lte"]:
                    return False
            elif alert.risk_score < risk_condition:
                return False
        
        # Check alert level
        if "alert_level" in conditions:
            if alert.alert_level != conditions["alert_level"]:
                return False
        
        # Check alert type
        if "alert_type" in conditions:
            if alert.alert_type != conditions["alert_type"]:
                return False
        
        # Check confidence score
        if "prediction_confidence" in conditions and alert.confidence_score:
            confidence_condition = conditions["prediction_confidence"]
            if isinstance(confidence_condition, dict):
                if "gte" in confidence_condition and alert.confidence_score < confidence_condition["gte"]:
                    return False
        
        return True
    
    def _get_primary_protocol_for_alert(self, alert: Alert) -> Optional[EmergencyProtocol]:
        """Get the primary protocol for an alert.
        
        Args:
            alert: Alert to get protocol for
            
        Returns:
            Primary emergency protocol or None
        """
        applicable = self._get_applicable_protocols(alert)
        
        if not applicable:
            return None
        
        # Return the first matching protocol (could be enhanced with priority)
        return applicable[0]
    
    async def _execute_emergency_protocol(
        self,
        alert: Alert,
        protocol: EmergencyProtocol
    ) -> Dict:
        """Execute an emergency protocol for an alert.
        
        Args:
            alert: Emergency alert
            protocol: Protocol to execute
            
        Returns:
            Execution result dictionary
        """
        try:
            execution_result = {
                "protocol_id": protocol.protocol_id,
                "protocol_name": protocol.name,
                "started_at": datetime.now(),
                "actions_completed": [],
                "notifications_sent": [],
                "escalation_level": 1,
                "success": True
            }
            
            # Start with level 1 escalation
            escalation_config = protocol.escalation_levels[0]
            
            # Execute escalation level
            await self._execute_escalation_level(alert, protocol, escalation_config)
            execution_result["actions_completed"].extend(escalation_config.get("actions", []))
            
            # Notify health authorities
            authority_results = await self.notify_health_authorities(alert, protocol)
            execution_result["notifications_sent"].extend(authority_results)
            
            # Contact emergency personnel
            contact_results = await self.contact_emergency_personnel(alert, protocol, 1)
            execution_result["notifications_sent"].extend(contact_results)
            
            # Schedule auto-escalation if configured
            if protocol.auto_escalation_minutes > 0:
                await self._schedule_auto_escalation(alert, protocol)
            
            execution_result["completed_at"] = datetime.now()
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Failed to execute emergency protocol {protocol.protocol_id}: {e}")
            return {
                "protocol_id": protocol.protocol_id,
                "protocol_name": protocol.name,
                "error": str(e),
                "success": False
            }
    
    async def _execute_escalation_level(
        self,
        alert: Alert,
        protocol: EmergencyProtocol,
        escalation_config: Dict
    ):
        """Execute actions for a specific escalation level.
        
        Args:
            alert: Alert being escalated
            protocol: Emergency protocol
            escalation_config: Configuration for this escalation level
        """
        actions = escalation_config.get("actions", [])
        
        for action in actions:
            try:
                await self._execute_response_action(alert, action)
                logger.info(f"Executed action '{action}' for alert {alert.id}")
                
            except Exception as e:
                logger.error(f"Failed to execute action '{action}' for alert {alert.id}: {e}")
    
    async def _execute_response_action(self, alert: Alert, action: str):
        """Execute a specific response action.
        
        Args:
            alert: Alert context
            action: Action to execute
        """
        # This would integrate with various systems based on the action
        # For now, we'll log the actions that would be taken
        
        action_mapping = {
            "notify_local_health_officer": "Send notification to local health officer",
            "alert_emergency_contacts": "Alert all emergency contacts",
            "notify_regional_health_authority": "Notify regional health authority",
            "activate_response_team": "Activate emergency response team",
            "notify_national_health_ministry": "Notify national health ministry",
            "activate_emergency_response": "Activate national emergency response",
            "immediate_vector_control": "Deploy vector control measures",
            "emergency_case_management": "Activate emergency case management",
            "community_mobilization": "Mobilize community response",
            "surveillance_enhancement": "Enhance surveillance activities",
            "verify_outbreak": "Verify outbreak status",
            "isolate_cases": "Implement case isolation protocols",
            "contact_tracing": "Initiate contact tracing",
            "mass_treatment": "Deploy mass treatment protocols",
            "vector_control": "Implement vector control measures",
            "public_health_measures": "Activate public health measures"
        }
        
        action_description = action_mapping.get(action, f"Execute action: {action}")
        
        logger.info(f"Emergency Action for Alert {alert.id}: {action_description}")
        
        # Here you would integrate with:
        # - Health information systems
        # - Emergency response platforms
        # - Vector control systems
        # - Case management systems
        # - Communication platforms
    
    async def _notify_health_authority(
        self,
        alert: Alert,
        authority: HealthAuthorityAPI
    ) -> Dict:
        """Notify a health authority about an emergency alert.
        
        Args:
            alert: Emergency alert
            authority: Health authority to notify
            
        Returns:
            Notification result
        """
        try:
            # Build notification payload
            payload = {
                "alert_id": alert.id,
                "alert_type": "malaria_emergency",
                "alert_level": alert.alert_level,
                "risk_score": alert.risk_score,
                "location": {
                    "latitude": alert.latitude,
                    "longitude": alert.longitude,
                    "name": alert.location_name,
                    "country": alert.country_code,
                    "region": alert.admin_region
                },
                "prediction_date": alert.prediction_date.isoformat() if alert.prediction_date else None,
                "confidence_score": alert.confidence_score,
                "alert_message": alert.alert_message,
                "timestamp": alert.created_at.isoformat(),
                "source_system": "malaria_prediction_system"
            }
            
            # Send notification via HTTP API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {authority.api_key}",
                "User-Agent": "MalariaAlertSystem/1.0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    authority.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=authority.timeout_seconds),
                    ssl=authority.verify_ssl
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        return {
                            "success": True,
                            "message_id": response_data.get("message_id"),
                            "authority": authority.name
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {await response.text()}",
                            "authority": authority.name
                        }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "authority": authority.name
            }
    
    async def _contact_emergency_person(
        self,
        alert: Alert,
        contact: EmergencyContact
    ) -> List[Dict]:
        """Contact an emergency person via configured methods.
        
        Args:
            alert: Emergency alert
            contact: Emergency contact
            
        Returns:
            List of contact attempt results
        """
        results = []
        
        for method in contact.notification_methods:
            try:
                if method == "email":
                    result = await self._send_emergency_email(alert, contact)
                elif method == "sms":
                    result = await self._send_emergency_sms(alert, contact)
                elif method == "voice":
                    result = await self._initiate_emergency_call(alert, contact)
                else:
                    result = {"success": False, "error": f"Unsupported method: {method}"}
                
                results.append({
                    "contact": contact.name,
                    "method": method,
                    "success": result["success"],
                    "message_id": result.get("message_id"),
                    "error": result.get("error")
                })
                
            except Exception as e:
                results.append({
                    "contact": contact.name,
                    "method": method,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _send_emergency_email(
        self,
        alert: Alert,
        contact: EmergencyContact
    ) -> Dict:
        """Send emergency email notification.
        
        Args:
            alert: Emergency alert
            contact: Emergency contact
            
        Returns:
            Send result
        """
        subject = f"EMERGENCY: Malaria Alert - {alert.alert_level.upper()} Risk"
        
        message = f"""
        EMERGENCY MALARIA ALERT
        
        Alert Level: {alert.alert_level.upper()}
        Risk Score: {alert.risk_score:.1%} 
        Location: {alert.location_name or 'Unknown'}
        Confidence: {alert.confidence_score:.1%}
        
        Alert Details:
        {alert.alert_message}
        
        Contact: {contact.name} ({contact.role})
        Organization: {contact.organization}
        
        Time: {alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}
        Alert ID: {alert.id}
        
        Please take immediate action according to emergency protocols.
        
        This is an automated emergency notification from the Malaria Prediction System.
        """
        
        request = NotificationRequest(
            alert_id=alert.id,
            channel="email",
            recipient=contact.email,
            recipient_type="emergency_contact",
            subject=subject,
            message=message,
            priority="urgent"
        )
        
        result = await notification_service.send_notification(request)
        
        return {
            "success": result.success,
            "message_id": result.provider_message_id,
            "error": result.error_message
        }
    
    async def _send_emergency_sms(
        self,
        alert: Alert,
        contact: EmergencyContact
    ) -> Dict:
        """Send emergency SMS notification.
        
        Args:
            alert: Emergency alert
            contact: Emergency contact
            
        Returns:
            Send result
        """
        location = alert.location_name or alert.admin_region or "Unknown"
        
        message = (
            f"EMERGENCY MALARIA ALERT: {alert.alert_level.upper()} risk ({alert.risk_score:.0%}) "
            f"detected in {location}. Immediate action required. "
            f"Contact: {contact.name}. Alert ID: {alert.id}. "
            f"Time: {alert.created_at.strftime('%m/%d %H:%M')}"
        )
        
        # SMS length limit
        if len(message) > 160:
            message = message[:157] + "..."
        
        request = NotificationRequest(
            alert_id=alert.id,
            channel="sms",
            recipient=contact.phone,
            recipient_type="emergency_contact",
            message=message,
            priority="urgent"
        )
        
        result = await notification_service.send_notification(request)
        
        return {
            "success": result.success,
            "message_id": result.provider_message_id,
            "error": result.error_message
        }
    
    async def _initiate_emergency_call(
        self,
        alert: Alert,
        contact: EmergencyContact
    ) -> Dict:
        """Initiate emergency voice call (placeholder).
        
        Args:
            alert: Emergency alert
            contact: Emergency contact
            
        Returns:
            Call initiation result
        """
        # This would integrate with voice calling services like Twilio Voice
        # For now, return a placeholder response
        
        logger.info(
            f"Emergency voice call would be initiated to {contact.name} "
            f"at {contact.phone} for alert {alert.id}"
        )
        
        return {
            "success": False,
            "error": "Voice calling not yet implemented"
        }
    
    async def _schedule_auto_escalation(
        self,
        alert: Alert,
        protocol: EmergencyProtocol
    ):
        """Schedule automatic escalation for an alert.
        
        Args:
            alert: Alert to escalate
            protocol: Emergency protocol
        """
        try:
            # Schedule escalation task
            delay_seconds = protocol.auto_escalation_minutes * 60
            
            asyncio.create_task(
                self._auto_escalate_after_delay(alert, protocol, delay_seconds)
            )
            
            logger.info(
                f"Scheduled auto-escalation for alert {alert.id} "
                f"in {protocol.auto_escalation_minutes} minutes"
            )
            
        except Exception as e:
            logger.error(f"Failed to schedule auto-escalation for alert {alert.id}: {e}")
    
    async def _auto_escalate_after_delay(
        self,
        alert: Alert,
        protocol: EmergencyProtocol,
        delay_seconds: int
    ):
        """Auto-escalate an alert after a delay.
        
        Args:
            alert: Alert to escalate
            protocol: Emergency protocol
            delay_seconds: Delay before escalation
        """
        try:
            await asyncio.sleep(delay_seconds)
            
            # Check if alert has been resolved or acknowledged
            db = next(get_database())
            try:
                current_alert = db.query(Alert).filter(Alert.id == alert.id).first()
                
                if (current_alert and 
                    not current_alert.acknowledged_at and 
                    not current_alert.resolved_at):
                    
                    # Escalate to next level
                    next_level = current_alert.escalation_level + 1
                    
                    if next_level <= protocol.max_escalation_level:
                        await self.escalate_alert(current_alert, next_level)
                        logger.info(f"Auto-escalated alert {alert.id} to level {next_level}")
                    else:
                        logger.warning(
                            f"Alert {alert.id} reached maximum escalation level "
                            f"{protocol.max_escalation_level}"
                        )
                else:
                    logger.info(f"Alert {alert.id} resolved, cancelling auto-escalation")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Auto-escalation failed for alert {alert.id}: {e}")
    
    def _update_avg_response_time(self, processing_time_minutes: float):
        """Update average response time statistic.
        
        Args:
            processing_time_minutes: Current processing time
        """
        current_avg = self.stats["avg_response_time_minutes"]
        processed_count = self.stats["emergency_alerts_processed"]
        
        if processed_count == 1:
            self.stats["avg_response_time_minutes"] = processing_time_minutes
        else:
            # Rolling average
            self.stats["avg_response_time_minutes"] = (
                (current_avg * (processed_count - 1) + processing_time_minutes) / processed_count
            )
    
    def get_stats(self) -> Dict:
        """Get emergency response statistics.
        
        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            "active_escalations": len(self.active_escalations),
            "loaded_protocols": len(self.protocols)
        }
    
    def get_active_escalations(self) -> Dict:
        """Get currently active escalations.
        
        Returns:
            Dictionary of active escalations
        """
        return self.active_escalations.copy()


# Global emergency protocol manager instance
emergency_protocols = EmergencyResponseProtocolManager()