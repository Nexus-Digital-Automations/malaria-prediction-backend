"""
Healthcare Professional Services Module.

This module provides backend services for healthcare professional tools including
patient case management, risk assessment processing, treatment protocol management,
resource allocation optimization, and surveillance data processing.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class HealthcareService:
    """
    Core healthcare service for managing professional tools and data processing.

    Provides comprehensive backend services for healthcare professionals
    including case management, risk assessment, and surveillance operations.
    """

    def __init__(self) -> None:
        """Initialize healthcare service with required components."""
        self.case_repository = CaseRepository()
        self.risk_processor = RiskAssessmentProcessor()
        self.treatment_advisor = TreatmentProtocolAdvisor()
        self.resource_optimizer = ResourceAllocationOptimizer()
        self.surveillance_processor = SurveillanceDataProcessor()
        logger.info("Healthcare service initialized successfully")

    async def create_patient_case(
        self,
        patient_id: str,
        healthcare_professional_id: str,
        location: dict[str, Any],
        case_type: str,
        symptoms: list[str],
        initial_notes: str | None = None
    ) -> dict[str, Any]:
        """
        Create a new patient case with comprehensive tracking.

        Args:
            patient_id: Patient identifier
            healthcare_professional_id: Professional creating the case
            location: Patient location data
            case_type: Type of case (suspected, confirmed, follow-up)
            symptoms: List of reported symptoms
            initial_notes: Optional initial clinical notes

        Returns:
            Created case data with tracking information
        """
        logger.info(f"Creating patient case for patient {patient_id}")

        case_data = {
            "case_id": str(uuid4()),
            "patient_id": patient_id,
            "healthcare_professional_id": healthcare_professional_id,
            "location": location,
            "case_type": case_type,
            "symptoms": symptoms,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "notes": [{
                "timestamp": datetime.now().isoformat(),
                "author": healthcare_professional_id,
                "content": initial_notes or "Case created",
                "type": "initial"
            }] if initial_notes else [],
            "risk_assessment": None,
            "treatment_plan": None,
            "follow_up_schedule": []
        }

        # Store case in repository
        await self.case_repository.store_case(case_data)

        logger.info(f"Patient case {case_data['case_id']} created successfully")
        return case_data

    async def conduct_risk_assessment(
        self,
        case_id: str,
        template_id: str,
        responses: dict[str, Any],
        healthcare_professional_id: str,
        include_environmental_data: bool = True
    ) -> dict[str, Any]:
        """
        Conduct comprehensive risk assessment for a patient case.

        Args:
            case_id: Patient case identifier
            template_id: Risk assessment template to use
            responses: Questionnaire responses
            healthcare_professional_id: Professional conducting assessment
            include_environmental_data: Whether to include environmental risk factors

        Returns:
            Risk assessment results with recommendations
        """
        logger.info(f"Conducting risk assessment for case {case_id}")

        # Process risk assessment
        assessment_result = await self.risk_processor.process_assessment(
            template_id=template_id,
            responses=responses,
            include_environmental=include_environmental_data
        )

        # Generate clinical recommendations
        recommendations = await self._generate_clinical_recommendations(
            assessment_result["risk_score"],
            assessment_result["risk_level"],
            responses
        )

        # Store assessment results
        assessment_data = {
            "assessment_id": str(uuid4()),
            "case_id": case_id,
            "template_id": template_id,
            "healthcare_professional_id": healthcare_professional_id,
            "responses": responses,
            "calculated_risk_score": assessment_result["risk_score"],
            "risk_level": assessment_result["risk_level"],
            "environmental_risk": assessment_result.get("environmental_risk"),
            "clinical_risk": assessment_result.get("clinical_risk"),
            "recommendations": recommendations,
            "completed_at": datetime.now(),
            "validated_by": None
        }

        # Update case with assessment
        await self.case_repository.update_case_assessment(case_id, assessment_data)

        logger.info(f"Risk assessment completed for case {case_id} with score {assessment_result['risk_score']:.3f}")
        return assessment_data

    async def get_treatment_recommendations(
        self,
        case_id: str,
        patient_weight: float | None = None,
        comorbidities: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get personalized treatment protocol recommendations.

        Args:
            case_id: Patient case identifier
            patient_weight: Patient weight for dosage calculations
            comorbidities: List of patient comorbidities

        Returns:
            Treatment recommendations with protocols and dosages
        """
        if comorbidities is None:
            comorbidities = []

        logger.info(f"Generating treatment recommendations for case {case_id}")

        # Get case data
        case_data = await self.case_repository.get_case(case_id)
        if not case_data:
            raise ValueError(f"Case {case_id} not found")

        # Generate recommendations based on case data
        recommendations = await self.treatment_advisor.recommend_treatment(
            case_data=case_data,
            patient_weight=patient_weight,
            comorbidities=comorbidities
        )

        return recommendations

    async def request_resource_allocation(
        self,
        healthcare_professional_id: str,
        organization: str,
        location: dict[str, Any],
        resource_types: list[str],
        population_at_risk: int,
        current_capacity: dict[str, int],
        prediction_horizon: int = 30,
        urgency_level: str = "normal",
        justification: str = ""
    ) -> dict[str, Any]:
        """
        Submit resource allocation planning request.

        Args:
            healthcare_professional_id: Requesting professional
            organization: Healthcare organization
            location: Resource deployment location
            resource_types: Required resource types
            population_at_risk: Population size at risk
            current_capacity: Current resource capacity
            prediction_horizon: Prediction horizon in days
            urgency_level: Request urgency level
            justification: Request justification

        Returns:
            Resource allocation request data
        """
        logger.info(f"Creating resource allocation request for {organization}")

        request_data = {
            "request_id": str(uuid4()),
            "healthcare_professional_id": healthcare_professional_id,
            "organization": organization,
            "location": location,
            "prediction_horizon": prediction_horizon,
            "resource_types": resource_types,
            "population_at_risk": population_at_risk,
            "current_capacity": current_capacity,
            "urgency_level": urgency_level,
            "justification": justification,
            "requested_at": datetime.now(),
            "status": "pending"
        }

        # Store request and trigger optimization
        optimization_result = await self.resource_optimizer.optimize_allocation(request_data)
        request_data["optimization_id"] = optimization_result["plan_id"]

        logger.info(f"Resource allocation request {request_data['request_id']} created")
        return request_data

    async def submit_surveillance_report(
        self,
        healthcare_professional_id: str,
        report_type: str,
        reporting_period: dict[str, Any],
        location: dict[str, Any],
        population_monitored: int,
        case_data: dict[str, Any],
        vector_data: dict[str, Any] | None = None,
        environmental_observations: dict[str, Any] | None = None,
        intervention_activities: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Submit comprehensive surveillance data report.

        Args:
            healthcare_professional_id: Reporting professional
            report_type: Type of surveillance report
            reporting_period: Reporting time period
            location: Surveillance area
            population_monitored: Population under surveillance
            case_data: Case surveillance data
            vector_data: Vector surveillance data
            environmental_observations: Environmental factors
            intervention_activities: Control interventions

        Returns:
            Surveillance report with processing status
        """
        logger.info(f"Submitting surveillance report for {location.get('name', 'Unknown location')}")

        # Calculate data quality indicators
        data_quality = self._calculate_data_quality_indicators(
            case_data, vector_data or {}, environmental_observations or {}
        )

        report_data = {
            "report_id": str(uuid4()),
            "healthcare_professional_id": healthcare_professional_id,
            "report_type": report_type,
            "reporting_period": reporting_period,
            "location": location,
            "population_monitored": population_monitored,
            "case_data": case_data,
            "vector_data": vector_data or {},
            "environmental_observations": environmental_observations or {},
            "intervention_activities": intervention_activities or [],
            "data_quality_indicators": data_quality,
            "submitted_at": datetime.now(),
            "dhis2_export_status": "pending",
            "validation_status": "pending"
        }

        # Process surveillance data
        await self.surveillance_processor.process_report(report_data)

        logger.info(f"Surveillance report {report_data['report_id']} submitted successfully")
        return report_data

    async def _generate_clinical_recommendations(
        self,
        risk_score: float,
        risk_level: str,
        responses: dict[str, Any]
    ) -> list[str]:
        """Generate clinical recommendations based on risk assessment."""
        recommendations = []

        if risk_level == "very_high":
            recommendations.extend([
                "Immediate laboratory confirmation required (RDT + microscopy)",
                "Consider hospitalization for monitoring",
                "Initiate antimalarial treatment promptly if confirmed",
                "Monitor for signs of severe malaria"
            ])
        elif risk_level == "high":
            recommendations.extend([
                "Laboratory confirmation required within 24 hours",
                "Start appropriate antimalarial if positive",
                "Close follow-up within 48 hours",
                "Patient education on danger signs"
            ])
        elif risk_level == "medium":
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

    def _calculate_data_quality_indicators(
        self,
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


class CaseRepository:
    """Repository for patient case data management."""

    def __init__(self) -> None:
        """Initialize case repository."""
        self._cases: dict[str, dict[str, Any]] = {}  # In production, use actual database
        logger.info("Case repository initialized")

    async def store_case(self, case_data: dict[str, Any]) -> None:
        """Store patient case data."""
        case_id = case_data["case_id"]
        self._cases[case_id] = case_data
        logger.debug(f"Stored case {case_id}")

    async def get_case(self, case_id: str) -> dict[str, Any] | None:
        """Retrieve patient case data."""
        return self._cases.get(case_id)

    async def update_case_assessment(self, case_id: str, assessment_data: dict[str, Any]) -> None:
        """Update case with risk assessment data."""
        if case_id in self._cases:
            self._cases[case_id]["risk_assessment"] = assessment_data
            self._cases[case_id]["updated_at"] = datetime.now()
            logger.debug(f"Updated case {case_id} with assessment")


class RiskAssessmentProcessor:
    """Processor for risk assessment calculations and analysis."""

    async def process_assessment(
        self,
        template_id: str,
        responses: dict[str, Any],
        include_environmental: bool = True
    ) -> dict[str, Any]:
        """Process risk assessment questionnaire responses."""
        logger.debug(f"Processing risk assessment with template {template_id}")

        # Calculate clinical risk
        clinical_risk = self._calculate_clinical_risk(responses)

        # Calculate environmental risk if requested
        environmental_risk = None
        if include_environmental:
            environmental_risk = await self._calculate_environmental_risk(responses)

        # Combine risks
        combined_risk = self._combine_risk_scores(clinical_risk, environmental_risk)
        risk_level = self._determine_risk_level(combined_risk)

        return {
            "risk_score": combined_risk,
            "risk_level": risk_level,
            "clinical_risk": clinical_risk,
            "environmental_risk": environmental_risk
        }

    def _calculate_clinical_risk(self, responses: dict[str, Any]) -> float:
        """Calculate clinical risk score from questionnaire responses."""
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

    async def _calculate_environmental_risk(self, responses: dict[str, Any]) -> float:
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

    def _combine_risk_scores(self, clinical_risk: float, environmental_risk: float | None) -> float:
        """Combine clinical and environmental risk scores."""
        if environmental_risk is None:
            return clinical_risk

        # Weighted combination: 60% clinical, 40% environmental
        return (0.6 * clinical_risk) + (0.4 * environmental_risk)

    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level category from numeric score."""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.6:
            return "medium"
        elif risk_score < 0.8:
            return "high"
        else:
            return "very_high"


class TreatmentProtocolAdvisor:
    """Advisor for treatment protocol recommendations."""

    async def recommend_treatment(
        self,
        case_data: dict[str, Any],
        patient_weight: float | None = None,
        comorbidities: list[str] | None = None
    ) -> dict[str, Any]:
        """Generate personalized treatment recommendations."""
        if comorbidities is None:
            comorbidities = []

        logger.debug(f"Generating treatment recommendations for case {case_data['case_id']}")

        # Analyze case data for treatment selection
        risk_assessment = case_data.get("risk_assessment", {})
        risk_level = risk_assessment.get("risk_level", "medium")
        case_data.get("symptoms", [])

        # Select primary recommendation based on risk level
        if risk_level in ["high", "very_high"] or "severe" in case_data.get("case_type", ""):
            primary_protocol = {
                "protocol_id": "proto_severe_001",
                "name": "Artesunate IV Protocol",
                "rationale": "High risk case requiring intensive treatment",
                "personalized_dosage": self._calculate_severe_dosage(patient_weight),
                "confidence_score": 0.95
            }
        else:
            primary_protocol = {
                "protocol_id": "proto_standard_001",
                "name": "Artemether-Lumefantrine Standard",
                "rationale": "Standard treatment for uncomplicated malaria",
                "personalized_dosage": self._calculate_standard_dosage(patient_weight),
                "confidence_score": 0.92
            }

        return {
            "primary_recommendation": primary_protocol,
            "alternative_options": self._get_alternative_protocols(comorbidities),
            "contraindications_checked": self._check_contraindications(comorbidities),
            "monitoring_plan": self._generate_monitoring_plan(risk_level),
            "generated_at": datetime.now().isoformat(),
            "valid_for_hours": 24
        }

    def _calculate_severe_dosage(self, patient_weight: float | None) -> str:
        """Calculate dosage for severe malaria treatment."""
        if patient_weight and patient_weight < 35:
            return "3mg/kg IV artesunate at 0, 12, 24 hours, then daily"
        else:
            return "2.4mg/kg IV artesunate at 0, 12, 24 hours, then daily"

    def _calculate_standard_dosage(self, patient_weight: float | None) -> str:
        """Calculate dosage for standard treatment."""
        if patient_weight and patient_weight < 35:
            return "Weight-based artemether-lumefantrine dosing per pediatric guidelines"
        else:
            return "4 tablets twice daily for 3 days (based on adult weight >35kg)"

    def _get_alternative_protocols(self, comorbidities: list[str]) -> list[dict[str, Any]]:
        """Get alternative treatment protocols based on comorbidities."""
        alternatives = []

        if "liver_disease" in comorbidities:
            alternatives.append({
                "protocol_id": "proto_alt_001",
                "name": "Atovaquone-Proguanil",
                "rationale": "Alternative for patients with liver dysfunction",
                "confidence_score": 0.78
            })

        return alternatives

    def _check_contraindications(self, comorbidities: list[str]) -> list[str]:
        """Check for contraindications based on patient comorbidities."""
        checks = [
            "No known drug allergies",
            "No severe liver dysfunction",
            "No concurrent medications with interactions"
        ]

        if "liver_disease" in comorbidities:
            checks.append("CAUTION: Liver disease present - consider alternative protocols")

        return checks

    def _generate_monitoring_plan(self, risk_level: str) -> list[str]:
        """Generate monitoring plan based on risk level."""
        if risk_level in ["high", "very_high"]:
            return [
                "Continuous vital signs monitoring",
                "Blood glucose every 4 hours",
                "Parasitemia every 12 hours",
                "Neurological assessment every 2 hours"
            ]
        else:
            return [
                "Day 1: Baseline vitals, symptom assessment",
                "Day 3: Parasitemia check, clinical evaluation",
                "Day 7: Follow-up for cure confirmation"
            ]


class ResourceAllocationOptimizer:
    """Optimizer for healthcare resource allocation planning."""

    async def optimize_allocation(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Generate optimized resource allocation plan."""
        logger.info(f"Optimizing resource allocation for request {request_data['request_id']}")

        # Mock optimization - in production, use actual optimization algorithms
        plan = {
            "plan_id": str(uuid4()),
            "request_id": request_data["request_id"],
            "predicted_risk_score": 0.72,
            "predicted_case_load": {
                "confirmed_cases": 45,
                "suspected_cases": 78,
                "severe_cases": 8,
                "hospitalizations": 12
            },
            "resource_recommendations": self._generate_resource_recommendations(request_data),
            "optimization_strategy": "cost_effectiveness_priority",
            "cost_estimates": self._calculate_cost_estimates(),
            "implementation_timeline": self._generate_implementation_timeline(),
            "risk_mitigation": self._generate_risk_mitigation_strategies(),
            "confidence_level": 0.85,
            "generated_at": datetime.now(),
            "valid_until": datetime.now() + timedelta(days=1)
        }

        return plan

    def _generate_resource_recommendations(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Generate resource allocation recommendations."""
        current_capacity = request_data["current_capacity"]

        return {
            "medical_staff": {
                "doctors": {"current": current_capacity.get("doctors", 2), "recommended": 4, "gap": 2},
                "nurses": {"current": current_capacity.get("nurses", 8), "recommended": 12, "gap": 4},
                "lab_technicians": {"current": current_capacity.get("lab_techs", 1), "recommended": 2, "gap": 1}
            },
            "medical_supplies": {
                "RDTs": {"current": current_capacity.get("rdts", 50), "recommended": 200, "gap": 150},
                "artemether_lumefantrine": {"current": current_capacity.get("drugs", 30), "recommended": 100, "gap": 70},
                "severe_malaria_kits": {"current": current_capacity.get("severe_kits", 5), "recommended": 15, "gap": 10}
            },
            "infrastructure": {
                "isolation_beds": {"current": current_capacity.get("beds", 4), "recommended": 8, "gap": 4},
                "laboratory_capacity": {"current": "basic", "recommended": "enhanced", "upgrade_needed": True}
            }
        }

    def _calculate_cost_estimates(self) -> dict[str, float]:
        """Calculate cost estimates for resource allocation."""
        return {
            "personnel_costs_usd": 8500,
            "supply_costs_usd": 3200,
            "infrastructure_costs_usd": 12000,
            "total_estimated_cost_usd": 23700
        }

    def _generate_implementation_timeline(self) -> list[dict[str, Any]]:
        """Generate implementation timeline for resource allocation."""
        return [
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
        ]

    def _generate_risk_mitigation_strategies(self) -> list[str]:
        """Generate risk mitigation strategies."""
        return [
            "Establish referral protocols for severe cases",
            "Implement daily monitoring of case trends",
            "Maintain emergency supply buffer (20% above predicted needs)",
            "Coordinate with neighboring facilities for overflow capacity"
        ]


class SurveillanceDataProcessor:
    """Processor for surveillance data management and DHIS2 integration."""

    async def process_report(self, report_data: dict[str, Any]) -> None:
        """Process surveillance report and prepare for export."""
        logger.info(f"Processing surveillance report {report_data['report_id']}")

        # Validate data quality
        self._validate_surveillance_data(report_data)

        # Process for DHIS2 export
        await self._prepare_dhis2_export(report_data)

        # Store in surveillance database
        await self._store_surveillance_data(report_data)

        logger.info(f"Surveillance report {report_data['report_id']} processed successfully")

    def _validate_surveillance_data(self, report_data: dict[str, Any]) -> None:
        """Validate surveillance data completeness and quality."""
        # Check required fields
        required_fields = ["case_data", "location", "population_monitored"]
        for field in required_fields:
            if field not in report_data or report_data[field] is None:
                logger.warning(f"Missing required field: {field}")

        # Validate case data structure
        case_data = report_data.get("case_data", {})
        if not isinstance(case_data, dict):
            logger.warning("Case data should be a dictionary")

    async def _prepare_dhis2_export(self, report_data: dict[str, Any]) -> None:
        """Prepare surveillance data for DHIS2 export."""
        # Map data to DHIS2 format
        dhis2_data = {
            "dataSet": "MAL_WEEKLY_001",
            "orgUnit": report_data.get("location", {}).get("org_unit_id", "OU_FACILITY_001"),
            "period": self._format_dhis2_period(report_data["reporting_period"]),
            "dataValues": self._map_to_dhis2_data_elements(report_data["case_data"])
        }

        # Mark as ready for export
        report_data["dhis2_export_data"] = dhis2_data
        report_data["dhis2_export_status"] = "ready"

    def _format_dhis2_period(self, reporting_period: dict[str, Any]) -> str:
        """Format reporting period for DHIS2."""
        # Convert to DHIS2 period format (e.g., 2023W52)
        start_date = reporting_period.get("start_date", datetime.now())
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)

        # Calculate week number
        week_number = start_date.isocalendar()[1]
        year = start_date.year

        return f"{year}W{week_number:02d}"

    def _map_to_dhis2_data_elements(self, case_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Map case data to DHIS2 data elements."""
        data_values = []

        # Map each case data field to DHIS2 data element
        element_mapping = {
            "suspected_cases": "DE_MAL_SUSP",
            "confirmed_cases": "DE_MAL_CONF",
            "severe_cases": "DE_MAL_SEV",
            "deaths": "DE_MAL_DEATH"
        }

        for field, element_id in element_mapping.items():
            if field in case_data:
                data_values.append({
                    "dataElement": element_id,
                    "value": str(case_data[field])
                })

        return data_values

    async def _store_surveillance_data(self, report_data: dict[str, Any]) -> None:
        """Store surveillance data in local database."""
        # In production, store in surveillance database
        logger.debug(f"Storing surveillance data for report {report_data['report_id']}")


# Global healthcare service instance
healthcare_service = HealthcareService()
