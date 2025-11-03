"""
Patient-Specific Recommender

Advanced patient-specific treatment recommendation system that integrates
patient demographics, clinical factors, drug resistance patterns, and
local treatment protocols to provide personalized malaria treatment recommendations.

Key Features:
- Personalized treatment algorithms
- Contraindication checking
- Drug interaction analysis
- Pregnancy and pediatric considerations
- Comorbidity adjustments
- Local protocol integration
- Real-time safety alerts

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .drug_resistance_analyzer import DrugResistanceAnalyzer
from .who_guidelines_engine import (
    ClinicalPresentation,
    DiseaseSeverity,
    MalariaSpecies,
    PatientProfile,
    TreatmentCategory,
    TreatmentRecommendation,
)

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Patient risk category classification"""
    LOW_RISK = "low_risk"
    MODERATE_RISK = "moderate_risk"
    HIGH_RISK = "high_risk"
    CRITICAL_RISK = "critical_risk"


class ContraindicationSeverity(Enum):
    """Contraindication severity levels"""
    ABSOLUTE = "absolute"  # Never use
    RELATIVE = "relative"  # Use with caution
    MONITORING = "monitoring"  # Requires enhanced monitoring
    CAUTION = "caution"  # Special considerations needed


@dataclass
class Contraindication:
    """Drug contraindication information"""
    drug_name: str
    contraindication_type: str
    severity: ContraindicationSeverity
    reason: str
    clinical_evidence: str
    alternative_suggestions: list[str] = field(default_factory=list)
    monitoring_requirements: list[str] = field(default_factory=list)


@dataclass
class DrugInteraction:
    """Drug-drug interaction information"""
    primary_drug: str
    interacting_drug: str
    interaction_type: str  # "major", "moderate", "minor"
    mechanism: str
    clinical_significance: str
    management_strategy: str
    severity_score: float


@dataclass
class PersonalizedRecommendation:
    """Personalized treatment recommendation"""
    patient_id: str | None
    recommendation_id: str
    primary_treatment: TreatmentRecommendation
    alternative_treatments: list[TreatmentRecommendation]
    contraindications: list[Contraindication]
    drug_interactions: list[DrugInteraction]
    risk_assessment: dict[str, Any]
    personalization_factors: dict[str, Any]
    monitoring_plan: dict[str, Any]
    safety_alerts: list[str]
    confidence_score: float
    generated_at: datetime
    valid_until: datetime
    prescriber_notes: str = ""


class PatientSpecificRecommender:
    """
    Patient-Specific Treatment Recommender for malaria.

    This system provides personalized treatment recommendations by integrating
    patient-specific factors, resistance patterns, contraindications, and
    local treatment protocols.
    """

    def __init__(
        self,
        who_guidelines_engine: Any,
        resistance_analyzer: DrugResistanceAnalyzer,
        local_protocols_db: str | None = None
    ) -> None:
        """
        Initialize Patient-Specific Recommender.

        Args:
            who_guidelines_engine: WHO Guidelines Engine instance
            resistance_analyzer: Drug Resistance Analyzer instance
            local_protocols_db: Optional local treatment protocols database
        """
        logger.info("Initializing Patient-Specific Recommender")

        self.who_engine = who_guidelines_engine
        self.resistance_analyzer = resistance_analyzer
        self.local_protocols_db = local_protocols_db

        # Load patient-specific databases
        self._contraindications_db = self._load_contraindications_database()
        self._drug_interactions_db = self._load_drug_interactions_database()
        self._pregnancy_safety_db = self._load_pregnancy_safety_database()
        self._pediatric_protocols = self._load_pediatric_protocols()
        self._comorbidity_adjustments = self._load_comorbidity_adjustments()

        logger.info("Patient-Specific Recommender initialized successfully")

    def generate_personalized_recommendation(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        location: str | None = None,
        local_protocols: dict | None = None
    ) -> PersonalizedRecommendation:
        """
        Generate comprehensive personalized treatment recommendation.

        Args:
            patient_profile: Patient demographic and clinical profile
            clinical_presentation: Clinical presentation and laboratory values
            malaria_species: Identified malaria species
            location: Patient location for resistance patterns
            local_protocols: Optional local treatment protocols

        Returns:
            Personalized treatment recommendation with safety considerations
        """
        logger.info(f"Generating personalized recommendation for patient: age={patient_profile.age}")

        # Step 1: Get base WHO recommendation
        base_recommendation = self.who_engine.recommend_treatment(
            patient_profile=patient_profile,
            clinical_presentation=clinical_presentation,
            malaria_species=malaria_species
        )

        # Step 2: Assess patient risk factors
        risk_assessment = self._assess_patient_risk(patient_profile, clinical_presentation)

        # Step 3: Check contraindications
        contraindications = self._check_contraindications(
            patient_profile, base_recommendation.drug_regimen
        )

        # Step 4: Check drug interactions
        drug_interactions = self._check_drug_interactions(
            patient_profile.current_medications,
            base_recommendation.drug_regimen
        )

        # Step 5: Get resistance patterns for location
        resistance_patterns = {}
        if location:
            resistance_patterns = self.resistance_analyzer.analyze_resistance_patterns(
                location=location,
                time_window_days=90,
                drugs_of_interest=[drug["drug_name"] for drug in base_recommendation.drug_regimen]
            )

        # Step 6: Apply personalization algorithms
        personalized_primary = self._personalize_treatment(
            base_recommendation=base_recommendation,
            patient_profile=patient_profile,
            contraindications=contraindications,
            drug_interactions=drug_interactions,
            resistance_patterns=resistance_patterns,
            risk_assessment=risk_assessment
        )

        # Step 7: Generate alternative treatments
        alternative_treatments = self._generate_alternatives(
            patient_profile=patient_profile,
            clinical_presentation=clinical_presentation,
            malaria_species=malaria_species,
            contraindications=contraindications,
            primary_treatment=personalized_primary
        )

        # Step 8: Create monitoring plan
        monitoring_plan = self._create_monitoring_plan(
            patient_profile=patient_profile,
            treatment=personalized_primary,
            risk_assessment=risk_assessment,
            contraindications=contraindications
        )

        # Step 9: Generate safety alerts
        safety_alerts = self._generate_safety_alerts(
            patient_profile=patient_profile,
            treatment=personalized_primary,
            contraindications=contraindications,
            drug_interactions=drug_interactions
        )

        # Step 10: Calculate personalization confidence
        confidence_score = self._calculate_personalization_confidence(
            patient_profile=patient_profile,
            contraindications=contraindications,
            resistance_patterns=resistance_patterns,
            local_protocols=local_protocols
        )

        # Create personalized recommendation
        recommendation = PersonalizedRecommendation(
            patient_id=getattr(patient_profile, 'patient_id', None),
            recommendation_id=f"PERS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            primary_treatment=personalized_primary,
            alternative_treatments=alternative_treatments,
            contraindications=contraindications,
            drug_interactions=drug_interactions,
            risk_assessment=risk_assessment,
            personalization_factors=self._extract_personalization_factors(patient_profile),
            monitoring_plan=monitoring_plan,
            safety_alerts=safety_alerts,
            confidence_score=confidence_score,
            generated_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=24),
            prescriber_notes=self._generate_prescriber_notes(
                patient_profile, contraindications, drug_interactions
            )
        )

        logger.info(f"Personalized recommendation generated: {recommendation.recommendation_id}")
        return recommendation

    def _assess_patient_risk(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation
    ) -> dict[str, Any]:
        """Assess patient-specific risk factors"""

        risk_factors: dict[str, Any] = {}

        # Age-based risk assessment
        if patient_profile.age < 5:
            risk_factors["pediatric_high_risk"] = True
            risk_factors["risk_score"] = 0.8
        elif patient_profile.age > 65:
            risk_factors["elderly_high_risk"] = True
            risk_factors["risk_score"] = 0.7
        else:
            risk_factors["risk_score"] = 0.3

        # Pregnancy risk
        if patient_profile.is_pregnant:
            risk_factors["pregnancy_risk"] = True
            risk_factors["pregnancy_trimester"] = patient_profile.pregnancy_trimester
            risk_factors["risk_score"] += 0.4

        # Comorbidity risk
        if patient_profile.has_comorbidities:
            risk_factors["comorbidity_risk"] = True
            risk_factors["comorbidities"] = patient_profile.comorbidities
            risk_factors["risk_score"] += len(patient_profile.comorbidities) * 0.1

        # Clinical severity risk
        if clinical_presentation.parasitemia_percent > 5.0:
            risk_factors["high_parasitemia"] = True
            risk_factors["risk_score"] += 0.3

        # Previous malaria episodes
        if patient_profile.previous_malaria_episodes > 3:
            risk_factors["recurrent_malaria"] = True
            risk_factors["risk_score"] += 0.2

        # Categorize overall risk
        total_risk = min(risk_factors["risk_score"], 1.0)
        if total_risk < 0.3:
            risk_factors["category"] = RiskCategory.LOW_RISK
        elif total_risk < 0.6:
            risk_factors["category"] = RiskCategory.MODERATE_RISK
        elif total_risk < 0.8:
            risk_factors["category"] = RiskCategory.HIGH_RISK
        else:
            risk_factors["category"] = RiskCategory.CRITICAL_RISK

        return risk_factors

    def _check_contraindications(
        self,
        patient_profile: PatientProfile,
        drug_regimen: list[dict]
    ) -> list[Contraindication]:
        """Check for drug contraindications based on patient profile"""

        contraindications = []

        for drug in drug_regimen:
            drug_name = drug["drug_name"].lower()

            # Pregnancy contraindications
            if patient_profile.is_pregnant:
                if "doxycycline" in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="pregnancy",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason="Teratogenic effects, dental staining in fetus",
                        clinical_evidence="Category D - Positive evidence of human fetal risk",
                        alternative_suggestions=["artemether-lumefantrine", "artesunate-amodiaquine"]
                    ))

                if "primaquine" in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="pregnancy",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason="Risk of hemolytic anemia in G6PD-deficient fetus",
                        clinical_evidence="Category C - Animal studies show adverse effects",
                        alternative_suggestions=["postpone radical cure until after delivery"]
                    ))

            # Age-based contraindications
            if patient_profile.age < 8:
                if "doxycycline" in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="pediatric_age",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason="Dental staining and bone growth inhibition",
                        clinical_evidence="Not recommended in children under 8 years",
                        alternative_suggestions=["artemether-lumefantrine", "artesunate-amodiaquine"]
                    ))

            # Allergy contraindications
            for allergy in patient_profile.allergies:
                if allergy.lower() in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="allergy",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason=f"Known hypersensitivity to {allergy}",
                        clinical_evidence="Patient-reported allergy history",
                        alternative_suggestions=self._get_alternative_drugs(drug_name)
                    ))

            # Comorbidity contraindications
            for comorbidity in patient_profile.comorbidities:
                if comorbidity == "g6pd_deficiency" and "primaquine" in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="genetic_disorder",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason="Risk of severe hemolytic anemia",
                        clinical_evidence="Well-established contraindication in G6PD deficiency",
                        alternative_suggestions=["use alternative radical cure regimen"]
                    ))

                if comorbidity == "severe_renal_impairment" and "mefloquine" in drug_name:
                    contraindications.append(Contraindication(
                        drug_name=drug["drug_name"],
                        contraindication_type="renal_impairment",
                        severity=ContraindicationSeverity.RELATIVE,
                        reason="Reduced clearance, risk of accumulation",
                        clinical_evidence="Dose adjustment required in renal impairment",
                        monitoring_requirements=["monitor renal function", "adjust dose"]
                    ))

        return contraindications

    def _check_drug_interactions(
        self,
        current_medications: list[str],
        drug_regimen: list[dict]
    ) -> list[DrugInteraction]:
        """Check for drug-drug interactions"""

        interactions = []

        for drug in drug_regimen:
            drug_name = drug["drug_name"].lower()

            for medication in current_medications:
                medication_lower = medication.lower()

                # Check for major interactions
                if "warfarin" in medication_lower and "artemether" in drug_name:
                    interactions.append(DrugInteraction(
                        primary_drug=drug["drug_name"],
                        interacting_drug=medication,
                        interaction_type="major",
                        mechanism="CYP3A4 induction by artemether",
                        clinical_significance="Decreased warfarin efficacy, increased bleeding risk",
                        management_strategy="Monitor INR closely, adjust warfarin dose",
                        severity_score=0.8
                    ))

                if "phenytoin" in medication_lower and "mefloquine" in drug_name:
                    interactions.append(DrugInteraction(
                        primary_drug=drug["drug_name"],
                        interacting_drug=medication,
                        interaction_type="major",
                        mechanism="Additive CNS effects",
                        clinical_significance="Increased risk of seizures",
                        management_strategy="Avoid combination, use alternative antimalarial",
                        severity_score=0.9
                    ))

                # Check for moderate interactions
                if "rifampin" in medication_lower and "artemether" in drug_name:
                    interactions.append(DrugInteraction(
                        primary_drug=drug["drug_name"],
                        interacting_drug=medication,
                        interaction_type="moderate",
                        mechanism="CYP3A4 induction by rifampin",
                        clinical_significance="Reduced artemether levels",
                        management_strategy="Consider dose adjustment or alternative treatment",
                        severity_score=0.6
                    ))

        return interactions

    def _personalize_treatment(
        self,
        base_recommendation: TreatmentRecommendation,
        patient_profile: PatientProfile,
        contraindications: list[Contraindication],
        drug_interactions: list[DrugInteraction],
        resistance_patterns: dict,
        risk_assessment: dict
    ) -> TreatmentRecommendation:
        """Apply personalization algorithms to base recommendation"""

        # Start with base recommendation
        personalized = base_recommendation

        # Check for absolute contraindications - need alternative drug
        absolute_contraindications = [
            c for c in contraindications
            if c.severity == ContraindicationSeverity.ABSOLUTE
        ]

        if absolute_contraindications:
            # Find alternative drug regimen
            personalized = self._find_alternative_regimen(
                patient_profile, base_recommendation, absolute_contraindications
            )

        # Adjust dosing for special populations
        personalized = self._adjust_dosing_for_population(personalized, patient_profile)

        # Adjust for resistance patterns
        personalized = self._adjust_for_resistance(personalized, resistance_patterns)

        # Add enhanced monitoring for high-risk patients
        if risk_assessment["category"] in [RiskCategory.HIGH_RISK, RiskCategory.CRITICAL_RISK]:
            personalized.monitoring_requirements.extend([
                "Enhanced clinical monitoring every 12 hours",
                "Daily laboratory monitoring",
                "Consider inpatient management"
            ])

        # Add interaction management
        for interaction in drug_interactions:
            if interaction.interaction_type == "major":
                personalized.special_considerations.append(
                    f"MAJOR INTERACTION: {interaction.clinical_significance} - {interaction.management_strategy}"
                )

        return personalized

    def _generate_alternatives(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        contraindications: list[Contraindication],
        primary_treatment: TreatmentRecommendation
    ) -> list[TreatmentRecommendation]:
        """Generate alternative treatment options"""

        alternatives = []

        # Get list of alternative drugs
        contraindicated_drugs = [c.drug_name.lower() for c in contraindications]

        # Standard alternatives based on species and severity
        if malaria_species == MalariaSpecies.P_FALCIPARUM:
            alternative_drugs = [
                "artesunate-amodiaquine",
                "dihydroartemisinin-piperaquine",
                "artemether-lumefantrine",
                "artesunate-mefloquine"
            ]
        else:
            alternative_drugs = [
                "chloroquine",
                "artemether-lumefantrine",
                "artesunate-amodiaquine"
            ]

        # Filter out contraindicated drugs and primary treatment
        primary_drug = str(primary_treatment.drug_regimen[0]["drug_name"]).lower()
        safe_alternatives = [
            drug for drug in alternative_drugs
            if drug not in contraindicated_drugs and drug != primary_drug
        ]

        # Generate alternative recommendations
        for drug in safe_alternatives[:3]:  # Limit to top 3 alternatives
            alt_recommendation = self._create_alternative_recommendation(
                drug, patient_profile, clinical_presentation
            )
            alternatives.append(alt_recommendation)

        return alternatives

    def _create_monitoring_plan(
        self,
        patient_profile: PatientProfile,
        treatment: TreatmentRecommendation,
        risk_assessment: dict,
        contraindications: list[Contraindication]
    ) -> dict[str, Any]:
        """Create personalized monitoring plan"""

        monitoring_plan: dict[str, Any] = {
            "baseline_assessments": [
                "Complete blood count",
                "Basic metabolic panel",
                "Liver function tests",
                "Parasitemia assessment"
            ],
            "routine_monitoring": [
                "Temperature every 8 hours",
                "Clinical assessment daily",
                "Parasitemia on day 3 and 28"
            ],
            "safety_monitoring": [],
            "follow_up_schedule": [
                {"day": 3, "assessment": "Clinical and parasitemia check"},
                {"day": 7, "assessment": "Complete blood count"},
                {"day": 14, "assessment": "Clinical assessment"},
                {"day": 28, "assessment": "Final follow-up and parasitemia"}
            ]
        }

        # Add risk-based monitoring
        if risk_assessment["category"] == RiskCategory.HIGH_RISK:
            monitoring_plan["routine_monitoring"].extend([
                "Vital signs every 4 hours",
                "Daily laboratory monitoring"
            ])

        # Add drug-specific monitoring
        for drug in treatment.drug_regimen:
            if "artesunate" in str(drug["drug_name"]).lower():
                monitoring_plan["safety_monitoring"].append(
                    "Monitor for post-artesunate delayed hemolysis (weekly CBC for 4 weeks)"
                )

        # Add contraindication-specific monitoring
        for contraindication in contraindications:
            if contraindication.severity == ContraindicationSeverity.MONITORING:
                monitoring_plan["safety_monitoring"].extend(
                    contraindication.monitoring_requirements
                )

        return monitoring_plan

    def _generate_safety_alerts(
        self,
        patient_profile: PatientProfile,
        treatment: TreatmentRecommendation,
        contraindications: list[Contraindication],
        drug_interactions: list[DrugInteraction]
    ) -> list[str]:
        """Generate safety alerts for the treatment"""

        alerts = []

        # Contraindication alerts
        for contraindication in contraindications:
            if contraindication.severity == ContraindicationSeverity.ABSOLUTE:
                alerts.append(
                    f"ABSOLUTE CONTRAINDICATION: {contraindication.reason} - "
                    f"Alternative treatment required"
                )

        # Drug interaction alerts
        major_interactions = [i for i in drug_interactions if i.interaction_type == "major"]
        for interaction in major_interactions:
            alerts.append(
                f"MAJOR DRUG INTERACTION: {interaction.clinical_significance} - "
                f"{interaction.management_strategy}"
            )

        # Population-specific alerts
        if patient_profile.is_pregnant:
            alerts.append("PREGNANCY: Ensure only pregnancy-safe antimalarials are used")

        if patient_profile.age < 5:
            alerts.append("PEDIATRIC: Weight-based dosing required, enhanced monitoring needed")

        # G6PD deficiency alert
        if "g6pd_deficiency" in patient_profile.comorbidities:
            alerts.append("G6PD DEFICIENCY: Avoid primaquine and other oxidizing drugs")

        return alerts

    def _calculate_personalization_confidence(
        self,
        patient_profile: PatientProfile,
        contraindications: list[Contraindication],
        resistance_patterns: dict,
        local_protocols: dict | None
    ) -> float:
        """Calculate confidence score for personalized recommendation"""

        base_confidence = 0.9

        # Reduce confidence for missing information
        if not patient_profile.allergies:
            base_confidence -= 0.05

        if not patient_profile.current_medications:
            base_confidence -= 0.05

        # Reduce confidence for contraindications
        if contraindications:
            base_confidence -= len(contraindications) * 0.1

        # Reduce confidence for lack of resistance data
        if not resistance_patterns:
            base_confidence -= 0.1

        return max(0.5, min(1.0, base_confidence))

    def _extract_personalization_factors(self, patient_profile: PatientProfile) -> dict[str, Any]:
        """Extract factors used for personalization"""

        return {
            "age": patient_profile.age,
            "weight": patient_profile.weight,
            "pregnancy_status": patient_profile.is_pregnant,
            "comorbidities": patient_profile.comorbidities,
            "allergies": patient_profile.allergies,
            "current_medications": patient_profile.current_medications,
            "previous_malaria_episodes": patient_profile.previous_malaria_episodes,
            "location": patient_profile.location
        }

    def _generate_prescriber_notes(
        self,
        patient_profile: PatientProfile,
        contraindications: list[Contraindication],
        drug_interactions: list[DrugInteraction]
    ) -> str:
        """Generate notes for prescribing healthcare professional"""

        notes = []

        # Patient-specific considerations
        if patient_profile.is_pregnant:
            notes.append(f"Pregnant patient (trimester {patient_profile.pregnancy_trimester})")

        if patient_profile.age < 5:
            notes.append(f"Pediatric patient ({patient_profile.age} years, {patient_profile.weight}kg)")

        # Contraindications summary
        if contraindications:
            absolute_contraindications = [
                c for c in contraindications
                if c.severity == ContraindicationSeverity.ABSOLUTE
            ]
            if absolute_contraindications:
                notes.append(f"Absolute contraindications: {len(absolute_contraindications)} identified")

        # Interaction summary
        if drug_interactions:
            major_interactions = [i for i in drug_interactions if i.interaction_type == "major"]
            if major_interactions:
                notes.append(f"Major drug interactions: {len(major_interactions)} identified")

        return "; ".join(notes) if notes else "Standard treatment protocol applicable"

    # Helper methods
    def _load_contraindications_database(self) -> dict:
        """Load contraindications database"""
        logger.info("Loading contraindications database")
        return {}

    def _load_drug_interactions_database(self) -> dict:
        """Load drug interactions database"""
        logger.info("Loading drug interactions database")
        return {}

    def _load_pregnancy_safety_database(self) -> dict:
        """Load pregnancy safety database"""
        logger.info("Loading pregnancy safety database")
        return {}

    def _load_pediatric_protocols(self) -> dict:
        """Load pediatric treatment protocols"""
        logger.info("Loading pediatric protocols")
        return {}

    def _load_comorbidity_adjustments(self) -> dict:
        """Load comorbidity adjustment protocols"""
        logger.info("Loading comorbidity adjustments")
        return {}

    def _get_alternative_drugs(self, drug_name: str) -> list[str]:
        """Get alternative drugs for a contraindicated drug"""
        return ["artemether-lumefantrine", "artesunate-amodiaquine"]

    def _find_alternative_regimen(
        self,
        patient_profile: PatientProfile,
        base_recommendation: TreatmentRecommendation,
        contraindications: list[Contraindication]
    ) -> TreatmentRecommendation:
        """Find alternative regimen when contraindications exist"""
        # This would implement alternative drug selection logic
        return base_recommendation

    def _adjust_dosing_for_population(
        self,
        recommendation: TreatmentRecommendation,
        patient_profile: PatientProfile
    ) -> TreatmentRecommendation:
        """Adjust dosing for special populations"""
        # This would implement population-specific dosing adjustments
        return recommendation

    def _adjust_for_resistance(
        self,
        recommendation: TreatmentRecommendation,
        resistance_patterns: dict
    ) -> TreatmentRecommendation:
        """Adjust recommendation based on resistance patterns"""
        # This would implement resistance-based adjustments
        return recommendation

    def _create_alternative_recommendation(
        self,
        drug: str,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation
    ) -> TreatmentRecommendation:
        """Create alternative treatment recommendation"""
        # This would create alternative recommendation
        # For now, return a simplified version
        return TreatmentRecommendation(
            treatment_id=f"ALT_{drug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            category=TreatmentCategory.ALTERNATIVE,
            drug_regimen=[{"drug_name": drug}],
            duration_days=3,
            dosage_instructions=f"Alternative treatment with {drug}",
            administration_route="oral",
            monitoring_requirements=[],
            contraindications=[],
            adverse_effects=[],
            follow_up_schedule=[],
            severity_basis=DiseaseSeverity.UNCOMPLICATED,
            confidence_score=0.8,
            evidence_level="Grade B",
            who_guideline_reference="WHO Guidelines alternative treatments"
        )
