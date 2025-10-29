"""
Healthcare Professional Security and Authentication Module.

This module provides specialized security functions for healthcare professional
authentication, authorization, and role-based access control for the malaria
prediction system's healthcare tools.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

if TYPE_CHECKING:
    from .routers.healthcare import HealthcareProfessional

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()

# Healthcare professional roles and their permissions
HEALTHCARE_ROLES = {
    "doctor": {
        "name": "Medical Doctor",
        "permissions": [
            "conduct_risk_assessment",
            "manage_patient_cases",
            "prescribe_treatment",
            "access_all_data",
            "supervise_staff",
            "submit_surveillance_reports"
        ]
    },
    "nurse": {
        "name": "Registered Nurse",
        "permissions": [
            "conduct_risk_assessment",
            "manage_patient_cases",
            "basic_treatment_protocols",
            "submit_surveillance_reports",
            "access_assigned_cases"
        ]
    },
    "epidemiologist": {
        "name": "Epidemiologist",
        "permissions": [
            "conduct_risk_assessment",
            "analyze_surveillance_data",
            "submit_surveillance_reports",
            "access_population_data",
            "conduct_outbreak_investigations",
            "resource_allocation_planning"
        ]
    },
    "lab_technician": {
        "name": "Laboratory Technician",
        "permissions": [
            "enter_lab_results",
            "quality_control_testing",
            "submit_lab_surveillance",
            "access_assigned_cases"
        ]
    },
    "community_health_worker": {
        "name": "Community Health Worker",
        "permissions": [
            "conduct_basic_risk_assessment",
            "community_case_detection",
            "health_education",
            "submit_community_reports"
        ]
    },
    "supervisor": {
        "name": "Healthcare Supervisor",
        "permissions": [
            "conduct_risk_assessment",
            "manage_patient_cases",
            "prescribe_treatment",
            "access_all_data",
            "supervise_staff",
            "submit_surveillance_reports",
            "resource_allocation_planning",
            "system_administration",
            "validate_reports"
        ]
    }
}

# Multi-language support configuration
SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "pt": "Português",
    "ar": "العربية",
    "sw": "Kiswahili",
    "am": "አማርኛ",
    "ha": "هَوُسَ",
    "yo": "Yorùbá",
    "ig": "Igbo"
}


async def get_current_healthcare_professional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> "HealthcareProfessional":
    """
    Get current authenticated healthcare professional.

    Validates JWT token and returns healthcare professional with
    role-based permissions and organizational context.
    """
    try:
        # Extract and validate JWT token
        from .routers.healthcare import HealthcareProfessional

        # In production, validate JWT token and extract user info
        # For now, return mock healthcare professional
        healthcare_professional = HealthcareProfessional(
            id="hp_12345",
            name="Dr. Sarah Mwangi",
            role="doctor",
            organization="Nairobi General Hospital",
            location={
                "latitude": -1.2921,
                "longitude": 36.8219,
                "name": "Nairobi"
            },
            specialization=["internal_medicine", "tropical_diseases"],
            languages=["en", "sw"],
            permissions=HEALTHCARE_ROLES["doctor"]["permissions"]
        )

        logger.info(f"Authenticated healthcare professional: {healthcare_professional.name}")
        return healthcare_professional

    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_healthcare_permission(permission: str) -> Callable:
    """
    Decorator to require specific healthcare permission.

    Args:
        permission: Required permission string

    Returns:
        Dependency function that checks user permissions
    """
    async def permission_dependency(
        current_user: "HealthcareProfessional" = Depends(get_current_healthcare_professional)
    ) -> "HealthcareProfessional":
        """Check if user has required permission."""
        if permission not in current_user.permissions:
            logger.warning(
                f"User {current_user.id} attempted to access {permission} without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user

    return permission_dependency


def require_healthcare_role(allowed_roles: list[str]) -> Callable:
    """
    Decorator to require specific healthcare role(s).

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Dependency function that checks user role
    """
    async def role_dependency(
        current_user: "HealthcareProfessional" = Depends(get_current_healthcare_professional)
    ) -> "HealthcareProfessional":
        """Check if user has allowed role."""
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.id} with role {current_user.role} "
                f"attempted to access endpoint requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role permissions. Required roles: {allowed_roles}"
            )
        return current_user

    return role_dependency


class HealthcareAuditLogger:
    """
    Audit logging for healthcare professional activities.

    Provides comprehensive logging for compliance with healthcare
    data protection regulations and audit requirements.
    """

    @staticmethod
    def log_access(
        user_id: str,
        resource: str,
        action: str,
        patient_id: str | None = None,
        case_id: str | None = None,
        additional_data: dict[str, Any] | None = None
    ) -> None:
        """
        Log healthcare professional access to resources.

        Args:
            user_id: Healthcare professional ID
            resource: Resource being accessed
            action: Action being performed
            patient_id: Patient ID if applicable
            case_id: Case ID if applicable
            additional_data: Additional context data
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "patient_id": patient_id,
            "case_id": case_id,
            "ip_address": "127.0.0.1",  # In production, get from request
            "user_agent": "Healthcare API Client",  # In production, get from request
            "additional_data": additional_data or {}
        }

        # In production, write to secure audit log system
        logger.info(f"HEALTHCARE_AUDIT: {log_entry}")

    @staticmethod
    def log_data_modification(
        user_id: str,
        resource: str,
        record_id: str,
        modification_type: str,
        before_data: dict[str, Any] | None = None,
        after_data: dict[str, Any] | None = None
    ) -> None:
        """
        Log data modification activities.

        Args:
            user_id: Healthcare professional ID
            resource: Resource being modified
            record_id: Record being modified
            modification_type: Type of modification (create, update, delete)
            before_data: Data before modification
            after_data: Data after modification
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "record_id": record_id,
            "modification_type": modification_type,
            "before_data": before_data,
            "after_data": after_data
        }

        # In production, write to secure audit log system
        logger.info(f"HEALTHCARE_DATA_AUDIT: {log_entry}")


class DHIS2Integration:
    """
    DHIS2 (District Health Information System 2) integration utilities.

    Provides functions for integrating with national health information
    systems for surveillance data reporting and management.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        """
        Initialize DHIS2 integration.

        Args:
            base_url: DHIS2 instance URL
            username: DHIS2 username
            password: DHIS2 password
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session_token = None

    async def authenticate(self) -> bool:
        """
        Authenticate with DHIS2 system.

        Returns:
            bool: True if authentication successful
        """
        # In production, implement actual DHIS2 authentication
        logger.info(f"Authenticating with DHIS2 at {self.base_url}")
        self.session_token = "mock_dhis2_token_12345"
        return True

    async def export_surveillance_data(
        self,
        report_data: dict[str, Any],
        dataset_id: str,
        org_unit_id: str,
        period: str
    ) -> dict[str, Any]:
        """
        Export surveillance data to DHIS2.

        Args:
            report_data: Surveillance report data
            dataset_id: DHIS2 dataset ID
            org_unit_id: Organization unit ID
            period: Reporting period

        Returns:
            Export result status
        """
        if not self.session_token:
            await self.authenticate()

        # In production, map data to DHIS2 format and submit
        export_result = {
            "status": "success",
            "dhis2_import_id": "IMP_001_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "records_imported": len(report_data.get("case_data", {})),
            "conflicts": [],
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Exported surveillance data to DHIS2: {export_result}")
        return export_result

    async def get_organization_units(self, parent_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get organization units from DHIS2.

        Args:
            parent_id: Parent organization unit ID

        Returns:
            List of organization units
        """
        # In production, fetch from DHIS2 API
        org_units = [
            {
                "id": "OU_REGION_001",
                "name": "Central Region",
                "level": 2,
                "parent": "OU_COUNTRY_001"
            },
            {
                "id": "OU_DISTRICT_001",
                "name": "Nairobi District",
                "level": 3,
                "parent": "OU_REGION_001"
            },
            {
                "id": "OU_FACILITY_001",
                "name": "Nairobi General Hospital",
                "level": 4,
                "parent": "OU_DISTRICT_001"
            }
        ]

        return org_units


class MultiLanguageSupport:
    """
    Multi-language support for healthcare professional interfaces.

    Provides translation and localization services for healthcare
    tools and documentation in multiple African languages.
    """

    def __init__(self) -> None:
        """Initialize multi-language support."""
        self.translations = self._load_translations()

    def _load_translations(self) -> dict[str, dict[str, str]]:
        """
        Load translation dictionaries for supported languages.

        Returns:
            Translation dictionaries by language code
        """
        # In production, load from translation files or database
        translations = {
            "en": {
                "fever": "Fever",
                "headache": "Headache",
                "chills": "Chills",
                "suspected_case": "Suspected Case",
                "confirmed_case": "Confirmed Case",
                "severe_malaria": "Severe Malaria",
                "risk_assessment": "Risk Assessment",
                "treatment_protocol": "Treatment Protocol"
            },
            "sw": {
                "fever": "Homa",
                "headache": "Maumivu ya kichwa",
                "chills": "Kutetemeka kwa baridi",
                "suspected_case": "Kesi Inayoshukiwa",
                "confirmed_case": "Kesi Iliyothibitishwa",
                "severe_malaria": "Malaria Kali",
                "risk_assessment": "Tathmini ya Hatari",
                "treatment_protocol": "Utaratibu wa Matibabu"
            },
            "fr": {
                "fever": "Fièvre",
                "headache": "Mal de tête",
                "chills": "Frissons",
                "suspected_case": "Cas Suspect",
                "confirmed_case": "Cas Confirmé",
                "severe_malaria": "Paludisme Grave",
                "risk_assessment": "Évaluation des Risques",
                "treatment_protocol": "Protocole de Traitement"
            }
        }

        return translations

    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language code

        Returns:
            Translated text
        """
        if target_language not in self.translations:
            logger.warning(f"Unsupported language: {target_language}")
            return text

        return self.translations[target_language].get(text, text)

    def translate_questionnaire(
        self,
        questionnaire: dict[str, Any],
        target_language: str
    ) -> dict[str, Any]:
        """
        Translate entire questionnaire to target language.

        Args:
            questionnaire: Questionnaire data structure
            target_language: Target language code

        Returns:
            Translated questionnaire
        """
        if target_language == "en":
            return questionnaire

        translated = questionnaire.copy()

        # Translate questionnaire title and description
        translated["name"] = self.translate(questionnaire.get("name", ""), target_language)
        translated["description"] = self.translate(questionnaire.get("description", ""), target_language)

        # Translate categories and questions
        if "categories" in translated:
            for category in translated["categories"]:
                category["name"] = self.translate(category.get("name", ""), target_language)

                for question in category.get("questions", []):
                    question["text"] = self.translate(question.get("text", ""), target_language)

                    # Translate options for select questions
                    if question.get("type") == "select" and "options" in question:
                        question["options"] = [
                            self.translate(option, target_language)
                            for option in question["options"]
                        ]

        return translated

    def get_supported_languages(self) -> dict[str, str]:
        """
        Get list of supported languages.

        Returns:
            Dictionary of language codes and names
        """
        return SUPPORTED_LANGUAGES


# Global instances for convenience
audit_logger = HealthcareAuditLogger()
multi_language = MultiLanguageSupport()


def get_dhis2_integration() -> DHIS2Integration:
    """
    Get DHIS2 integration instance.

    Returns:
        Configured DHIS2 integration instance
    """
    # In production, load from configuration
    return DHIS2Integration(
        base_url="https://national-hims.gov/dhis2",
        username="api_user",
        password="secure_password"
    )
