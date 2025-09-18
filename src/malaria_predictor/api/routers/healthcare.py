"""
Healthcare Professional Tools Router for Malaria Prediction API.

This module provides specialized tools and endpoints for healthcare professionals
including risk assessment workflows, patient case management, treatment protocols,
resource allocation planning, and surveillance reporting features.
"""

import logging
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..healthcare_security import get_current_healthcare_professional
from ..models import LocationPoint, RiskLevel

logger = logging.getLogger(__name__)

router = APIRouter()

# ==========================================
# Healthcare Professional Data Models
# ==========================================

class HealthcareProfessional(BaseModel):
    """Healthcare professional user profile."""

    id: str = Field(..., description="Professional ID")
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="Professional role (doctor, nurse, epidemiologist, etc.)")
    organization: str = Field(..., description="Healthcare organization")
    location: LocationPoint = Field(..., description="Primary work location")
    specialization: list[str] = Field(default_factory=list, description="Medical specializations")
    languages: list[str] = Field(default_factory=list, description="Supported languages")
    permissions: list[str] = Field(default_factory=list, description="System permissions")


class PatientCase(BaseModel):
    """Patient case management model."""

    case_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique case ID")
    patient_id: str = Field(..., description="Patient identifier")
    healthcare_professional_id: str = Field(..., description="Assigned healthcare professional")
    location: LocationPoint = Field(..., description="Patient location")
    case_type: str = Field(..., description="Case type (suspected, confirmed, follow-up)")
    symptoms: list[str] = Field(default_factory=list, description="Reported symptoms")
    risk_factors: dict[str, Any] = Field(default_factory=dict, description="Risk factor assessment")
    diagnostic_results: dict[str, Any] = Field(default_factory=dict, description="Test results")
    treatment_plan: dict[str, Any] = Field(default_factory=dict, description="Treatment protocol")
    follow_up_schedule: list[dict[str, Any]] = Field(default_factory=list, description="Follow-up appointments")
    status: str = Field("active", description="Case status")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: list[dict[str, Any]] = Field(default_factory=list, description="Clinical notes")


class RiskAssessmentQuestionnaireTemplate(BaseModel):
    """Risk assessment questionnaire template."""

    template_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    version: str = Field("1.0", description="Template version")
    language: str = Field("en", description="Primary language")
    categories: list[dict[str, Any]] = Field(..., description="Question categories")
    scoring_rules: dict[str, Any] = Field(..., description="Risk scoring rules")
    created_by: str = Field(..., description="Creator ID")
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(True, description="Template active status")


class RiskAssessmentResponse(BaseModel):
    """Risk assessment questionnaire response."""

    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    template_id: str = Field(..., description="Template used")
    patient_case_id: str = Field(..., description="Associated patient case")
    healthcare_professional_id: str = Field(..., description="Conducting professional")
    responses: dict[str, Any] = Field(..., description="Question responses")
    calculated_risk_score: float = Field(..., ge=0, le=1, description="Calculated risk score")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    recommendations: list[str] = Field(default_factory=list, description="Clinical recommendations")
    environmental_risk: float | None = Field(None, description="Environmental risk component")
    clinical_risk: float | None = Field(None, description="Clinical risk component")
    completed_at: datetime = Field(default_factory=datetime.now)
    validated_by: str | None = Field(None, description="Validation by supervisor")


class TreatmentProtocol(BaseModel):
    """Treatment protocol recommendation."""

    protocol_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Protocol name")
    description: str = Field(..., description="Protocol description")
    indication: str = Field(..., description="Clinical indication")
    contraindications: list[str] = Field(default_factory=list, description="Contraindications")
    medications: list[dict[str, Any]] = Field(..., description="Medication details")
    dosages: dict[str, Any] = Field(..., description="Dosage information")
    duration: str = Field(..., description="Treatment duration")
    monitoring_requirements: list[str] = Field(default_factory=list, description="Monitoring needed")
    success_criteria: list[str] = Field(default_factory=list, description="Success indicators")
    evidence_level: str = Field(..., description="Evidence strength")
    guidelines_source: str = Field(..., description="Guidelines source (WHO, national, etc.)")
    last_updated: datetime = Field(default_factory=datetime.now)


class ResourceAllocationRequest(BaseModel):
    """Resource allocation planning request."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    healthcare_professional_id: str = Field(..., description="Requesting professional")
    organization: str = Field(..., description="Requesting organization")
    location: LocationPoint = Field(..., description="Resource deployment location")
    prediction_horizon: int = Field(30, ge=1, le=365, description="Prediction horizon in days")
    resource_types: list[str] = Field(..., description="Required resource types")
    population_at_risk: int = Field(..., ge=0, description="Population at risk")
    current_capacity: dict[str, int] = Field(..., description="Current resource capacity")
    requested_at: datetime = Field(default_factory=datetime.now)
    urgency_level: str = Field("normal", description="Request urgency")
    justification: str = Field(..., description="Request justification")


class ResourceAllocationPlan(BaseModel):
    """Resource allocation optimization plan."""

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(..., description="Original request ID")
    predicted_risk_score: float = Field(..., ge=0, le=1, description="Predicted area risk")
    predicted_case_load: dict[str, int] = Field(..., description="Predicted case numbers")
    resource_recommendations: dict[str, Any] = Field(..., description="Resource allocation recommendations")
    optimization_strategy: str = Field(..., description="Optimization approach used")
    cost_estimates: dict[str, float] = Field(default_factory=dict, description="Cost projections")
    implementation_timeline: list[dict[str, Any]] = Field(..., description="Implementation phases")
    risk_mitigation: list[str] = Field(default_factory=list, description="Risk mitigation strategies")
    confidence_level: float = Field(..., ge=0, le=1, description="Plan confidence")
    generated_at: datetime = Field(default_factory=datetime.now)
    valid_until: datetime = Field(..., description="Plan validity period")


class SurveillanceReport(BaseModel):
    """Surveillance data entry and reporting."""

    report_id: str = Field(default_factory=lambda: str(uuid4()))
    healthcare_professional_id: str = Field(..., description="Reporting professional")
    report_type: str = Field(..., description="Report type (weekly, outbreak, investigation)")
    reporting_period: dict[str, date] = Field(..., description="Reporting period")
    location: LocationPoint = Field(..., description="Surveillance area")
    population_monitored: int = Field(..., ge=0, description="Population under surveillance")
    case_data: dict[str, Any] = Field(..., description="Case surveillance data")
    vector_data: dict[str, Any] = Field(default_factory=dict, description="Vector surveillance data")
    environmental_observations: dict[str, Any] = Field(default_factory=dict, description="Environmental factors")
    intervention_activities: list[dict[str, Any]] = Field(default_factory=list, description="Control interventions")
    data_quality_indicators: dict[str, float] = Field(default_factory=dict, description="Data quality metrics")
    submitted_at: datetime = Field(default_factory=datetime.now)
    dhis2_export_status: str = Field("pending", description="DHIS2 export status")
    validation_status: str = Field("pending", description="Report validation status")


# ==========================================
# Risk Assessment Workflow Endpoints
# ==========================================

@router.get("/risk-assessment/templates", response_model=list[RiskAssessmentQuestionnaireTemplate])
async def get_risk_assessment_templates(
    language: str = "en",
    category: str | None = None,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get available risk assessment questionnaire templates.

    Returns questionnaire templates available to healthcare professionals
    for conducting malaria risk assessments.
    """
    logger.info(f"Fetching risk assessment templates for user {current_user.id}")

    # Mock templates - in production, these would be stored in database
    templates = [
        RiskAssessmentQuestionnaireTemplate(
            name="WHO Standard Malaria Risk Assessment",
            description="Standardized malaria risk assessment based on WHO guidelines",
            version="2.1",
            language=language,
            categories=[
                {
                    "name": "Clinical Symptoms",
                    "questions": [
                        {
                            "id": "fever",
                            "text": "Does the patient have fever (>37.5°C)?",
                            "type": "boolean",
                            "weight": 0.3,
                            "required": True
                        },
                        {
                            "id": "chills",
                            "text": "Does the patient experience chills?",
                            "type": "boolean",
                            "weight": 0.2,
                            "required": False
                        },
                        {
                            "id": "headache",
                            "text": "Does the patient have headache?",
                            "type": "boolean",
                            "weight": 0.15,
                            "required": False
                        }
                    ]
                },
                {
                    "name": "Travel History",
                    "questions": [
                        {
                            "id": "recent_travel",
                            "text": "Has the patient traveled to malaria-endemic areas in the last 30 days?",
                            "type": "boolean",
                            "weight": 0.4,
                            "required": True
                        },
                        {
                            "id": "travel_locations",
                            "text": "Specify travel locations",
                            "type": "text",
                            "weight": 0.2,
                            "required": False,
                            "conditional": {"depends_on": "recent_travel", "value": True}
                        }
                    ]
                },
                {
                    "name": "Environmental Factors",
                    "questions": [
                        {
                            "id": "residence_type",
                            "text": "Type of residence",
                            "type": "select",
                            "options": ["urban", "rural", "peri-urban"],
                            "weight": 0.25,
                            "required": True
                        },
                        {
                            "id": "water_sources",
                            "text": "Proximity to stagnant water sources",
                            "type": "select",
                            "options": ["none", "nearby", "immediate"],
                            "weight": 0.3,
                            "required": True
                        }
                    ]
                }
            ],
            scoring_rules={
                "risk_levels": {
                    "low": {"min": 0.0, "max": 0.3},
                    "medium": {"min": 0.3, "max": 0.6},
                    "high": {"min": 0.6, "max": 0.8},
                    "very_high": {"min": 0.8, "max": 1.0}
                },
                "environmental_weight": 0.4,
                "clinical_weight": 0.6
            },
            created_by=current_user.id
        ),
        RiskAssessmentQuestionnaireTemplate(
            name="Pediatric Malaria Risk Assessment",
            description="Specialized risk assessment for children under 5 years",
            version="1.3",
            language=language,
            categories=[
                {
                    "name": "Age and Development",
                    "questions": [
                        {
                            "id": "age_months",
                            "text": "Patient age in months",
                            "type": "number",
                            "min": 0,
                            "max": 60,
                            "weight": 0.4,
                            "required": True
                        },
                        {
                            "id": "vaccination_status",
                            "text": "Vaccination status up to date",
                            "type": "boolean",
                            "weight": 0.2,
                            "required": True
                        }
                    ]
                },
                {
                    "name": "Pediatric Symptoms",
                    "questions": [
                        {
                            "id": "feeding_issues",
                            "text": "Feeding difficulties or loss of appetite",
                            "type": "boolean",
                            "weight": 0.3,
                            "required": True
                        },
                        {
                            "id": "lethargy",
                            "text": "Unusual lethargy or drowsiness",
                            "type": "boolean",
                            "weight": 0.35,
                            "required": True
                        }
                    ]
                }
            ],
            scoring_rules={
                "risk_levels": {
                    "low": {"min": 0.0, "max": 0.25},
                    "medium": {"min": 0.25, "max": 0.5},
                    "high": {"min": 0.5, "max": 0.75},
                    "very_high": {"min": 0.75, "max": 1.0}
                },
                "age_weight": 0.5,
                "symptoms_weight": 0.5
            },
            created_by=current_user.id
        )
    ]

    # Filter by category if specified
    if category:
        templates = [t for t in templates if any(cat["name"].lower() == category.lower() for cat in t.categories)]

    logger.info(f"Returning {len(templates)} risk assessment templates")
    return templates


@router.post("/risk-assessment/conduct", response_model=RiskAssessmentResponse)
async def conduct_risk_assessment(
    template_id: str,
    patient_case_id: str,
    responses: dict[str, Any],
    include_environmental_data: bool = True,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Conduct a risk assessment using a questionnaire template.

    Processes questionnaire responses and calculates risk scores using
    both clinical and environmental factors.
    """
    logger.info(f"Conducting risk assessment for case {patient_case_id} by user {current_user.id}")

    try:
        # In production, fetch actual template and validate responses
        # For now, calculate mock risk score based on responses
        clinical_risk = _calculate_clinical_risk(responses)
        environmental_risk = None

        if include_environmental_data:
            # In production, integrate with environmental prediction API
            environmental_risk = _calculate_environmental_risk(responses)

        # Combine clinical and environmental risks
        combined_risk = _combine_risk_scores(clinical_risk, environmental_risk)
        risk_level = _determine_risk_level(combined_risk)

        # Generate recommendations based on risk assessment
        recommendations = _generate_risk_recommendations(
            combined_risk, risk_level, responses
        )

        assessment = RiskAssessmentResponse(
            template_id=template_id,
            patient_case_id=patient_case_id,
            healthcare_professional_id=current_user.id,
            responses=responses,
            calculated_risk_score=combined_risk,
            risk_level=risk_level,
            recommendations=recommendations,
            environmental_risk=environmental_risk,
            clinical_risk=clinical_risk
        )

        logger.info(f"Risk assessment completed with score {combined_risk:.3f} (level: {risk_level})")
        return assessment

    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment calculation failed: {str(e)}"
        ) from e


# ==========================================
# Patient Case Management Endpoints
# ==========================================

@router.post("/cases", response_model=PatientCase)
async def create_patient_case(
    patient_id: str,
    location: LocationPoint,
    case_type: str,
    symptoms: list[str] = None,
    initial_notes: str | None = None,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Create a new patient case for tracking and management.

    Initializes a patient case with basic information and assigns
    to the current healthcare professional.
    """
    if symptoms is None:
        symptoms = []
    logger.info(f"Creating patient case for patient {patient_id} by user {current_user.id}")

    case = PatientCase(
        patient_id=patient_id,
        healthcare_professional_id=current_user.id,
        location=location,
        case_type=case_type,
        symptoms=symptoms,
        notes=[{
            "timestamp": datetime.now().isoformat(),
            "author": current_user.id,
            "content": initial_notes or "Case created",
            "type": "initial"
        }] if initial_notes else []
    )

    # In production, save to database
    logger.info(f"Patient case {case.case_id} created successfully")
    return case


@router.get("/cases/{case_id}", response_model=PatientCase)
async def get_patient_case(
    case_id: str,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """Get detailed information for a specific patient case."""
    logger.info(f"Retrieving case {case_id} for user {current_user.id}")

    # In production, fetch from database and verify permissions
    # Mock case data for demonstration
    case = PatientCase(
        case_id=case_id,
        patient_id="P12345",
        healthcare_professional_id=current_user.id,
        location=LocationPoint(latitude=-1.2921, longitude=36.8219, name="Nairobi"),
        case_type="suspected",
        symptoms=["fever", "headache", "chills"],
        status="active"
    )

    return case


@router.put("/cases/{case_id}", response_model=PatientCase)
async def update_patient_case(
    case_id: str,
    update_data: dict[str, Any],
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """Update patient case information."""
    logger.info(f"Updating case {case_id} by user {current_user.id}")

    # In production, fetch existing case, validate permissions, and update
    # For now, return mock updated case
    updated_case = PatientCase(
        case_id=case_id,
        patient_id="P12345",
        healthcare_professional_id=current_user.id,
        location=LocationPoint(latitude=-1.2921, longitude=36.8219, name="Nairobi"),
        case_type=update_data.get("case_type", "suspected"),
        symptoms=update_data.get("symptoms", ["fever", "headache"]),
        status=update_data.get("status", "active"),
        updated_at=datetime.now()
    )

    return updated_case


# ==========================================
# Treatment Protocol Endpoints
# ==========================================

@router.get("/treatment-protocols", response_model=list[TreatmentProtocol])
async def get_treatment_protocols(
    indication: str | None = None,
    severity_level: str | None = None,
    patient_age_group: str | None = None,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get available treatment protocols based on clinical criteria.

    Returns evidence-based treatment protocols filtered by
    indication, severity, and patient demographics.
    """
    logger.info(f"Fetching treatment protocols for user {current_user.id}")

    # Mock protocols - in production, these would be from clinical database
    protocols = [
        TreatmentProtocol(
            name="Uncomplicated P. falciparum Treatment - Adult",
            description="WHO recommended treatment for uncomplicated P. falciparum malaria in adults",
            indication="uncomplicated_falciparum",
            contraindications=["known_artemisinin_resistance", "severe_liver_disease"],
            medications=[
                {
                    "name": "Artemether-Lumefantrine",
                    "active_ingredients": ["artemether", "lumefantrine"],
                    "formulation": "tablet",
                    "strength": "20mg/120mg"
                }
            ],
            dosages={
                "adult": "4 tablets twice daily for 3 days",
                "weight_based": "20mg/kg artemether + 120mg/kg lumefantrine total dose"
            },
            duration="3 days",
            monitoring_requirements=[
                "Temperature monitoring every 8 hours",
                "Parasitemia check on day 3",
                "Clinical assessment daily"
            ],
            success_criteria=[
                "Fever resolution within 48-72 hours",
                "Negative blood smear by day 3",
                "Complete symptom resolution"
            ],
            evidence_level="Grade A (Strong recommendation)",
            guidelines_source="WHO Malaria Treatment Guidelines 2023"
        ),
        TreatmentProtocol(
            name="Severe Malaria Treatment - ICU Protocol",
            description="Intensive care protocol for severe P. falciparum malaria",
            indication="severe_malaria",
            contraindications=[],
            medications=[
                {
                    "name": "Artesunate",
                    "active_ingredients": ["artesunate"],
                    "formulation": "injection",
                    "strength": "60mg/ml"
                }
            ],
            dosages={
                "adult": "2.4mg/kg IV at 0, 12, 24 hours, then daily",
                "pediatric": "3mg/kg IV at 0, 12, 24 hours, then daily"
            },
            duration="Minimum 3 days IV, then oral completion",
            monitoring_requirements=[
                "Continuous vital signs monitoring",
                "Blood glucose every 4 hours",
                "Parasitemia every 12 hours",
                "Neurological assessment every 2 hours"
            ],
            success_criteria=[
                "Parasitemia reduction >90% in 48 hours",
                "Consciousness improvement",
                "Hemodynamic stability"
            ],
            evidence_level="Grade A (Strong recommendation)",
            guidelines_source="WHO Severe Malaria Guidelines 2023"
        )
    ]

    # Filter protocols based on criteria
    if indication:
        protocols = [p for p in protocols if p.indication == indication]

    logger.info(f"Returning {len(protocols)} treatment protocols")
    return protocols


@router.get("/treatment-protocols/recommend")
async def recommend_treatment_protocol(
    case_id: str,
    patient_weight: float | None = None,
    comorbidities: list[str] = None,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get personalized treatment protocol recommendations for a patient case.

    Analyzes patient case data and provides tailored treatment
    recommendations with dosage calculations.
    """
    if comorbidities is None:
        comorbidities = []
    logger.info(f"Generating treatment recommendations for case {case_id}")

    # In production, fetch case data and analyze for recommendations
    recommendations = {
        "primary_recommendation": {
            "protocol_id": "proto_001",
            "name": "Artemether-Lumefantrine Standard",
            "rationale": "Patient presents with uncomplicated malaria, no contraindications",
            "personalized_dosage": "4 tablets twice daily for 3 days (based on adult weight >35kg)",
            "confidence_score": 0.92
        },
        "alternative_options": [
            {
                "protocol_id": "proto_002",
                "name": "Atovaquone-Proguanil",
                "rationale": "Alternative for travelers or artemisinin intolerance",
                "confidence_score": 0.78
            }
        ],
        "contraindications_checked": [
            "No known drug allergies",
            "No severe liver dysfunction",
            "No concurrent medications with interactions"
        ],
        "monitoring_plan": [
            "Day 1: Baseline vitals, symptom assessment",
            "Day 3: Parasitemia check, clinical evaluation",
            "Day 7: Follow-up for cure confirmation"
        ],
        "generated_at": datetime.now().isoformat(),
        "valid_for_hours": 24
    }

    return recommendations


# ==========================================
# Helper Functions
# ==========================================

def _calculate_clinical_risk(responses: dict[str, Any]) -> float:
    """Calculate clinical risk score from questionnaire responses."""
    # Mock calculation - in production, use validated scoring algorithms
    risk_score = 0.0

    # Fever adds significant risk
    if responses.get("fever", False):
        risk_score += 0.3

    # Travel history
    if responses.get("recent_travel", False):
        risk_score += 0.4

    # Additional symptoms
    if responses.get("chills", False):
        risk_score += 0.15
    if responses.get("headache", False):
        risk_score += 0.1

    return min(risk_score, 1.0)


def _calculate_environmental_risk(responses: dict[str, Any]) -> float:
    """Calculate environmental risk score based on location and season."""
    # Mock environmental risk - in production, integrate with prediction API
    base_risk = 0.4  # Baseline environmental risk for the region

    # Residence type adjustment
    residence = responses.get("residence_type", "urban")
    if residence == "rural":
        base_risk += 0.2
    elif residence == "peri-urban":
        base_risk += 0.1

    # Water sources proximity
    water_proximity = responses.get("water_sources", "none")
    if water_proximity == "immediate":
        base_risk += 0.3
    elif water_proximity == "nearby":
        base_risk += 0.15

    return min(base_risk, 1.0)


def _combine_risk_scores(clinical_risk: float, environmental_risk: float | None) -> float:
    """Combine clinical and environmental risk scores."""
    if environmental_risk is None:
        return clinical_risk

    # Weighted combination: 60% clinical, 40% environmental
    return (0.6 * clinical_risk) + (0.4 * environmental_risk)


def _determine_risk_level(risk_score: float) -> RiskLevel:
    """Determine risk level category from numeric score."""
    if risk_score < 0.3:
        return RiskLevel.LOW
    elif risk_score < 0.6:
        return RiskLevel.MEDIUM
    elif risk_score < 0.8:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH


def _generate_risk_recommendations(
    risk_score: float,
    risk_level: RiskLevel,
    responses: dict[str, Any]
) -> list[str]:
    """Generate clinical recommendations based on risk assessment."""
    recommendations = []

    if risk_level == RiskLevel.VERY_HIGH:
        recommendations.extend([
            "Immediate laboratory confirmation required (RDT + microscopy)",
            "Consider hospitalization for monitoring",
            "Initiate antimalarial treatment promptly if confirmed",
            "Monitor for signs of severe malaria"
        ])
    elif risk_level == RiskLevel.HIGH:
        recommendations.extend([
            "Laboratory confirmation required within 24 hours",
            "Start appropriate antimalarial if positive",
            "Close follow-up within 48 hours",
            "Patient education on danger signs"
        ])
    elif risk_level == RiskLevel.MEDIUM:
        recommendations.extend([
            "Laboratory testing recommended",
            "Symptomatic treatment while awaiting results",
            "Follow-up in 2-3 days if symptoms persist"
        ])
    else:  # LOW risk
        recommendations.extend([
            "Consider alternative diagnoses",
            "Symptomatic treatment",
            "Return if symptoms worsen or persist >48 hours"
        ])

    # Add specific recommendations based on responses
    if responses.get("recent_travel", False):
        recommendations.append("Obtain detailed travel history including prophylaxis use")

    if responses.get("age_months") and responses["age_months"] < 60:
        recommendations.append("Pediatric malaria protocols apply - consider age-specific risks")

    return recommendations


# ==========================================
# Resource Allocation Planning Endpoints
# ==========================================

@router.post("/resource-allocation/request", response_model=ResourceAllocationRequest)
async def create_resource_allocation_request(
    location: LocationPoint,
    resource_types: list[str],
    population_at_risk: int,
    current_capacity: dict[str, int],
    prediction_horizon: int = 30,
    urgency_level: str = "normal",
    justification: str = "",
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Submit a resource allocation planning request.

    Creates a request for optimized resource allocation based on
    predicted malaria risk and current capacity constraints.
    """
    logger.info(f"Creating resource allocation request for location {location.name} by user {current_user.id}")

    request = ResourceAllocationRequest(
        healthcare_professional_id=current_user.id,
        organization=current_user.organization,
        location=location,
        prediction_horizon=prediction_horizon,
        resource_types=resource_types,
        population_at_risk=population_at_risk,
        current_capacity=current_capacity,
        urgency_level=urgency_level,
        justification=justification
    )

    # In production, save to database and trigger optimization process
    logger.info(f"Resource allocation request {request.request_id} created successfully")
    return request


@router.get("/resource-allocation/plan/{request_id}", response_model=ResourceAllocationPlan)
async def get_resource_allocation_plan(
    request_id: str,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get optimized resource allocation plan for a request.

    Returns the generated resource allocation plan with
    recommendations, cost estimates, and implementation timeline.
    """
    logger.info(f"Retrieving resource allocation plan for request {request_id}")

    # Mock optimization results - in production, this would run actual optimization algorithms
    plan = ResourceAllocationPlan(
        request_id=request_id,
        predicted_risk_score=0.72,
        predicted_case_load={
            "confirmed_cases": 45,
            "suspected_cases": 78,
            "severe_cases": 8,
            "hospitalizations": 12
        },
        resource_recommendations={
            "medical_staff": {
                "doctors": {"current": 2, "recommended": 4, "gap": 2},
                "nurses": {"current": 8, "recommended": 12, "gap": 4},
                "lab_technicians": {"current": 1, "recommended": 2, "gap": 1}
            },
            "medical_supplies": {
                "RDTs": {"current": 50, "recommended": 200, "gap": 150},
                "artemether_lumefantrine": {"current": 30, "recommended": 100, "gap": 70},
                "severe_malaria_kits": {"current": 5, "recommended": 15, "gap": 10}
            },
            "infrastructure": {
                "isolation_beds": {"current": 4, "recommended": 8, "gap": 4},
                "laboratory_capacity": {"current": "basic", "recommended": "enhanced", "upgrade_needed": True}
            }
        },
        optimization_strategy="cost_effectiveness_priority",
        cost_estimates={
            "personnel_costs_usd": 8500,
            "supply_costs_usd": 3200,
            "infrastructure_costs_usd": 12000,
            "total_estimated_cost_usd": 23700
        },
        implementation_timeline=[
            {
                "phase": "immediate",
                "duration_days": 3,
                "actions": ["Deploy emergency medical supplies", "Request additional nursing staff"],
                "cost_usd": 3200
            },
            {
                "phase": "short_term",
                "duration_days": 14,
                "actions": ["Recruit temporary medical staff", "Set up additional isolation capacity"],
                "cost_usd": 12000
            },
            {
                "phase": "medium_term",
                "duration_days": 30,
                "actions": ["Implement laboratory enhancements", "Establish monitoring protocols"],
                "cost_usd": 8500
            }
        ],
        risk_mitigation=[
            "Establish referral protocols for severe cases",
            "Implement daily monitoring of case trends",
            "Maintain emergency supply buffer (20% above predicted needs)",
            "Coordinate with neighboring facilities for overflow capacity"
        ],
        confidence_level=0.85,
        valid_until=datetime.now().replace(hour=23, minute=59, second=59)
    )

    return plan


@router.get("/resource-allocation/optimization-models")
async def get_optimization_models(
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get available resource allocation optimization models and their capabilities.
    """
    models = {
        "cost_effectiveness_priority": {
            "name": "Cost-Effectiveness Priority",
            "description": "Optimizes resource allocation based on cost per case prevented",
            "strengths": ["Budget optimization", "Scalable solutions"],
            "use_cases": ["Limited budget scenarios", "Large population coverage"]
        },
        "clinical_outcome_priority": {
            "name": "Clinical Outcome Priority",
            "description": "Prioritizes resources for maximum clinical impact and case reduction",
            "strengths": ["Maximal health impact", "Evidence-based allocation"],
            "use_cases": ["Outbreak response", "High-risk populations"]
        },
        "equity_based_allocation": {
            "name": "Equity-Based Allocation",
            "description": "Ensures fair distribution of resources across vulnerable populations",
            "strengths": ["Social equity", "Inclusive healthcare"],
            "use_cases": ["Rural deployments", "Marginalized communities"]
        },
        "rapid_response_mode": {
            "name": "Rapid Response Mode",
            "description": "Emergency allocation for immediate outbreak containment",
            "strengths": ["Speed of deployment", "Outbreak containment"],
            "use_cases": ["Emergency response", "Outbreak situations"]
        }
    }

    return models


# ==========================================
# Surveillance Reporting Endpoints
# ==========================================

@router.post("/surveillance/reports", response_model=SurveillanceReport)
async def submit_surveillance_report(
    report_type: str,
    reporting_period: dict[str, date],
    location: LocationPoint,
    population_monitored: int,
    case_data: dict[str, Any],
    vector_data: dict[str, Any] = None,
    environmental_observations: dict[str, Any] = None,
    intervention_activities: list[dict[str, Any]] = None,
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Submit surveillance data report.

    Creates comprehensive surveillance report including case data,
    vector surveillance, environmental factors, and interventions.
    """
    if intervention_activities is None:
        intervention_activities = []
    if environmental_observations is None:
        environmental_observations = {}
    if vector_data is None:
        vector_data = {}
    logger.info(f"Submitting surveillance report for {location.name} by user {current_user.id}")

    # Calculate data quality indicators
    data_quality = _calculate_data_quality_indicators(
        case_data, vector_data, environmental_observations
    )

    report = SurveillanceReport(
        healthcare_professional_id=current_user.id,
        report_type=report_type,
        reporting_period=reporting_period,
        location=location,
        population_monitored=population_monitored,
        case_data=case_data,
        vector_data=vector_data,
        environmental_observations=environmental_observations,
        intervention_activities=intervention_activities,
        data_quality_indicators=data_quality
    )

    # In production, save to database and trigger DHIS2 export
    logger.info(f"Surveillance report {report.report_id} submitted successfully")
    return report


@router.get("/surveillance/templates")
async def get_surveillance_form_templates(
    report_type: str | None = None,
    language: str = "en",
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get surveillance reporting form templates.

    Returns standardized forms for different types of surveillance
    reporting (weekly, outbreak investigation, vector surveillance).
    """
    templates = {
        "weekly_surveillance": {
            "name": "Weekly Malaria Surveillance Report",
            "description": "Standard weekly surveillance data collection",
            "sections": {
                "basic_info": {
                    "title": "Basic Information",
                    "fields": [
                        {"name": "reporting_week", "type": "date_range", "required": True},
                        {"name": "catchment_population", "type": "number", "required": True},
                        {"name": "reporting_facilities", "type": "number", "required": True}
                    ]
                },
                "case_data": {
                    "title": "Case Data",
                    "fields": [
                        {"name": "suspected_cases", "type": "number", "required": True},
                        {"name": "confirmed_cases", "type": "number", "required": True},
                        {"name": "severe_cases", "type": "number", "required": True},
                        {"name": "deaths", "type": "number", "required": True},
                        {"name": "age_breakdown", "type": "nested_object", "required": False}
                    ]
                },
                "laboratory_data": {
                    "title": "Laboratory Testing",
                    "fields": [
                        {"name": "rdt_performed", "type": "number", "required": True},
                        {"name": "rdt_positive", "type": "number", "required": True},
                        {"name": "microscopy_performed", "type": "number", "required": False},
                        {"name": "microscopy_positive", "type": "number", "required": False}
                    ]
                }
            }
        },
        "outbreak_investigation": {
            "name": "Malaria Outbreak Investigation Form",
            "description": "Detailed outbreak investigation data collection",
            "sections": {
                "outbreak_description": {
                    "title": "Outbreak Description",
                    "fields": [
                        {"name": "outbreak_start_date", "type": "date", "required": True},
                        {"name": "index_case_description", "type": "text", "required": True},
                        {"name": "attack_rate", "type": "number", "required": False}
                    ]
                },
                "epidemiological_investigation": {
                    "title": "Epidemiological Investigation",
                    "fields": [
                        {"name": "case_definition", "type": "text", "required": True},
                        {"name": "line_listing", "type": "file_upload", "required": True},
                        {"name": "risk_factors_identified", "type": "multi_select", "required": True}
                    ]
                }
            }
        },
        "vector_surveillance": {
            "name": "Vector Surveillance Report",
            "description": "Mosquito surveillance and control monitoring",
            "sections": {
                "collection_data": {
                    "title": "Vector Collection Data",
                    "fields": [
                        {"name": "collection_method", "type": "select", "required": True},
                        {"name": "collection_sites", "type": "number", "required": True},
                        {"name": "mosquito_density", "type": "number", "required": False}
                    ]
                },
                "insecticide_resistance": {
                    "title": "Insecticide Resistance Testing",
                    "fields": [
                        {"name": "tested_insecticides", "type": "multi_select", "required": False},
                        {"name": "resistance_patterns", "type": "nested_object", "required": False}
                    ]
                }
            }
        }
    }

    if report_type and report_type in templates:
        return {report_type: templates[report_type]}

    return templates


@router.get("/surveillance/dhis2-integration")
async def get_dhis2_integration_status(
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get DHIS2 integration status and configuration.

    Returns current DHIS2 integration status, data element mappings,
    and export capabilities for surveillance data.
    """
    integration_status = {
        "status": "active",
        "last_sync": datetime.now().isoformat(),
        "configuration": {
            "dhis2_instance": "https://national-hims.gov/dhis2",
            "organization_unit": current_user.organization,
            "user_access_level": "data_entry",
            "supported_datasets": [
                {
                    "name": "Malaria Weekly Surveillance",
                    "dhis2_id": "MAL_WEEKLY_001",
                    "period_type": "weekly",
                    "auto_export": True
                },
                {
                    "name": "Malaria Case Investigation",
                    "dhis2_id": "MAL_INVEST_001",
                    "period_type": "event",
                    "auto_export": False
                }
            ]
        },
        "data_element_mappings": {
            "suspected_cases": "DE_MAL_SUSP",
            "confirmed_cases": "DE_MAL_CONF",
            "severe_cases": "DE_MAL_SEV",
            "deaths": "DE_MAL_DEATH",
            "rdt_performed": "DE_RDT_PERF",
            "rdt_positive": "DE_RDT_POS"
        },
        "export_queue": {
            "pending_reports": 3,
            "last_export_attempt": datetime.now().isoformat(),
            "export_errors": []
        }
    }

    return integration_status


# ==========================================
# Professional Dashboard Endpoints
# ==========================================

@router.get("/dashboard/overview")
async def get_professional_dashboard_overview(
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get comprehensive dashboard overview for healthcare professionals.

    Returns key metrics, alerts, recent activities, and actionable insights
    for healthcare professionals in their area of responsibility.
    """
    logger.info(f"Generating dashboard overview for user {current_user.id}")

    # Mock dashboard data - in production, aggregate from various sources
    dashboard = {
        "professional_info": {
            "name": current_user.name,
            "role": current_user.role,
            "organization": current_user.organization,
            "coverage_area": current_user.location.name,
            "last_login": datetime.now().isoformat()
        },
        "key_metrics": {
            "active_cases": 12,
            "new_cases_today": 3,
            "high_risk_assessments": 5,
            "pending_follow_ups": 8,
            "surveillance_reports_due": 2
        },
        "risk_summary": {
            "area_risk_level": "medium",
            "area_risk_score": 0.58,
            "risk_trend": "increasing",
            "environmental_factors": {
                "temperature": "optimal_for_transmission",
                "rainfall": "above_average",
                "vector_activity": "high"
            }
        },
        "alerts": [
            {
                "type": "outbreak_risk",
                "severity": "high",
                "message": "Increased case clustering detected in northern district",
                "action_required": "Conduct outbreak investigation",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "resource_shortage",
                "severity": "medium",
                "message": "RDT stock running low (3 days remaining)",
                "action_required": "Submit resupply request",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "recent_activities": [
            {
                "type": "risk_assessment",
                "description": "Completed risk assessment for patient P12345",
                "timestamp": datetime.now().isoformat(),
                "outcome": "high_risk"
            },
            {
                "type": "surveillance_report",
                "description": "Submitted weekly surveillance report",
                "timestamp": datetime.now().isoformat(),
                "status": "exported_to_dhis2"
            }
        ],
        "pending_tasks": [
            {
                "type": "case_follow_up",
                "description": "Follow-up required for patient P12340",
                "due_date": datetime.now().isoformat(),
                "priority": "high"
            },
            {
                "type": "surveillance_report",
                "description": "Weekly surveillance report due",
                "due_date": datetime.now().isoformat(),
                "priority": "medium"
            }
        ],
        "performance_metrics": {
            "cases_managed_this_month": 45,
            "average_case_resolution_days": 5.2,
            "surveillance_reporting_compliance": 0.95,
            "patient_satisfaction_score": 4.6
        }
    }

    return dashboard


@router.get("/dashboard/case-workload")
async def get_case_workload_summary(
    time_period: str = "week",
    current_user: HealthcareProfessional = Depends(get_current_healthcare_professional)
):
    """
    Get detailed case workload summary for specified time period.
    """
    workload = {
        "time_period": time_period,
        "case_statistics": {
            "total_active_cases": 15,
            "new_cases": 8,
            "resolved_cases": 12,
            "transferred_cases": 2
        },
        "case_breakdown_by_type": {
            "suspected": 8,
            "confirmed": 5,
            "severe": 2
        },
        "case_breakdown_by_risk": {
            "low": 3,
            "medium": 6,
            "high": 4,
            "very_high": 2
        },
        "geographic_distribution": [
            {"location": "District A", "cases": 8, "risk_level": "high"},
            {"location": "District B", "cases": 4, "risk_level": "medium"},
            {"location": "District C", "cases": 3, "risk_level": "low"}
        ],
        "treatment_outcomes": {
            "successful_treatment": 10,
            "treatment_failure": 1,
            "lost_to_follow_up": 1,
            "ongoing_treatment": 3
        }
    }

    return workload


# ==========================================
# Additional Helper Functions
# ==========================================

def _calculate_data_quality_indicators(
    case_data: dict[str, Any],
    vector_data: dict[str, Any],
    environmental_observations: dict[str, Any]
) -> dict[str, float]:
    """Calculate data quality indicators for surveillance reports."""
    indicators = {}

    # Case data completeness
    required_case_fields = ["suspected_cases", "confirmed_cases", "severe_cases"]
    completed_case_fields = sum(1 for field in required_case_fields if case_data.get(field) is not None)
    indicators["case_data_completeness"] = completed_case_fields / len(required_case_fields)

    # Vector data completeness (optional)
    if vector_data:
        required_vector_fields = ["collection_method", "collection_sites"]
        completed_vector_fields = sum(1 for field in required_vector_fields if vector_data.get(field) is not None)
        indicators["vector_data_completeness"] = completed_vector_fields / len(required_vector_fields)
    else:
        indicators["vector_data_completeness"] = 0.0

    # Environmental data completeness (optional)
    if environmental_observations:
        indicators["environmental_data_completeness"] = 1.0
    else:
        indicators["environmental_data_completeness"] = 0.0

    # Overall data quality score
    indicators["overall_quality_score"] = (
        indicators["case_data_completeness"] * 0.7 +
        indicators["vector_data_completeness"] * 0.2 +
        indicators["environmental_data_completeness"] * 0.1
    )

    return indicators


# Include documentation router as sub-router
try:
    from ..healthcare_documentation import router as documentation_router
    router.include_router(documentation_router, prefix="/documentation", tags=["Documentation"])
    logger.info("Healthcare documentation router included successfully")
except ImportError as e:
    logger.warning(f"Healthcare documentation router not available: {e}")
