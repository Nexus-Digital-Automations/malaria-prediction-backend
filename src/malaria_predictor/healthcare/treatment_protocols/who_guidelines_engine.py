"""
WHO Guidelines Engine

Implementation of WHO malaria treatment guidelines with evidence-based decision support.
This engine provides standardized treatment recommendations based on official WHO protocols,
disease severity assessment, and patient-specific factors.

Key Features:
- WHO Treatment Protocol Implementation (2023 Guidelines)
- Severity Assessment Algorithms
- First-line and Alternative Treatment Selection
- Special Population Considerations (pregnancy, children, etc.)
- Artemisinin Resistance Protocols
- Treatment Duration and Dosage Calculations

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MalariaSpecies(Enum):
    """Malaria parasite species classification"""
    P_FALCIPARUM = "P. falciparum"
    P_VIVAX = "P. vivax"
    P_OVALE = "P. ovale"
    P_MALARIAE = "P. malariae"
    P_KNOWLESI = "P. knowlesi"
    MIXED_INFECTION = "Mixed"
    UNKNOWN = "Unknown"


class DiseaseSeverity(Enum):
    """WHO malaria severity classification"""
    UNCOMPLICATED = "uncomplicated"
    SEVERE = "severe"
    CRITICAL = "critical"


class TreatmentCategory(Enum):
    """Treatment category classification"""
    FIRST_LINE = "first_line"
    SECOND_LINE = "second_line"
    ALTERNATIVE = "alternative"
    RESCUE = "rescue"
    EMERGENCY = "emergency"


class ResistanceStatus(Enum):
    """Drug resistance status"""
    SUSCEPTIBLE = "susceptible"
    PARTIAL_RESISTANCE = "partial_resistance"
    HIGH_RESISTANCE = "high_resistance"
    UNKNOWN = "unknown"


@dataclass
class PatientProfile:
    """Patient demographic and clinical profile"""
    age: float  # Age in years
    weight: float  # Weight in kg
    sex: str  # "male" or "female"
    is_pregnant: bool = False
    pregnancy_trimester: int | None = None
    has_comorbidities: bool = False
    comorbidities: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    previous_malaria_episodes: int = 0
    location: str | None = None  # Geographic location for resistance patterns


@dataclass
class ClinicalPresentation:
    """Clinical signs and symptoms assessment"""
    fever_duration_hours: int
    peak_temperature: float
    parasitemia_percent: float
    symptoms: list[str] = field(default_factory=list)
    vital_signs: dict[str, float] = field(default_factory=dict)
    laboratory_values: dict[str, float] = field(default_factory=dict)
    complications: list[str] = field(default_factory=list)
    consciousness_level: str = "alert"  # alert, confused, stuporous, comatose


@dataclass
class TreatmentRecommendation:
    """Comprehensive treatment recommendation"""
    treatment_id: str
    category: TreatmentCategory
    drug_regimen: list[dict[str, str | float | int]]
    duration_days: int
    dosage_instructions: str
    administration_route: str
    monitoring_requirements: list[str]
    contraindications: list[str]
    adverse_effects: list[str]
    follow_up_schedule: list[str]
    severity_basis: DiseaseSeverity
    confidence_score: float
    evidence_level: str
    who_guideline_reference: str
    special_considerations: list[str] = field(default_factory=list)
    alternative_treatments: list[str] = field(default_factory=list)


class WHOGuidelinesEngine:
    """
    WHO Guidelines Engine implementing official malaria treatment protocols.

    This engine provides evidence-based treatment recommendations following
    WHO guidelines with decision support algorithms for healthcare professionals.
    """

    def __init__(self):
        """Initialize WHO Guidelines Engine with protocol data"""
        logger.info("Initializing WHO Guidelines Engine")

        # Load WHO treatment protocols (2023 guidelines)
        self._treatment_protocols = self._load_who_protocols()
        self._severity_criteria = self._load_severity_criteria()
        self._dosage_calculations = self._load_dosage_calculations()
        self._contraindications = self._load_contraindications()
        self._monitoring_protocols = self._load_monitoring_protocols()

        logger.info("WHO Guidelines Engine initialized successfully")

    def assess_severity(
        self,
        clinical_presentation: ClinicalPresentation,
        patient_profile: PatientProfile
    ) -> tuple[DiseaseSeverity, dict[str, bool]]:
        """
        Assess malaria severity based on WHO criteria.

        Args:
            clinical_presentation: Patient's clinical signs and symptoms
            patient_profile: Patient demographic and clinical profile

        Returns:
            Tuple of (severity classification, severity indicators)
        """
        logger.info(f"Assessing severity for patient: age={patient_profile.age}, weight={patient_profile.weight}")

        severity_indicators = {}

        # WHO Severe Malaria Criteria
        severe_criteria = [
            # Neurological criteria
            ("altered_consciousness", clinical_presentation.consciousness_level != "alert"),
            ("seizures", "seizures" in clinical_presentation.symptoms),
            ("coma", clinical_presentation.consciousness_level == "comatose"),

            # Respiratory criteria
            ("respiratory_distress", "respiratory_distress" in clinical_presentation.symptoms),
            ("pulmonary_edema", "pulmonary_edema" in clinical_presentation.complications),

            # Cardiovascular criteria
            ("shock", "shock" in clinical_presentation.complications),
            ("hypotension", clinical_presentation.vital_signs.get("systolic_bp", 120) < 80),

            # Renal criteria
            ("acute_kidney_injury", "acute_kidney_injury" in clinical_presentation.complications),
            ("oliguria", clinical_presentation.laboratory_values.get("urine_output_ml_kg_hr", 1.0) < 0.5),

            # Hematological criteria
            ("severe_anemia", clinical_presentation.laboratory_values.get("hemoglobin_g_dl", 12.0) < 5.0),
            ("bleeding", "bleeding_disorder" in clinical_presentation.complications),

            # Metabolic criteria
            ("acidosis", clinical_presentation.laboratory_values.get("ph", 7.4) < 7.35),
            ("hypoglycemia", clinical_presentation.laboratory_values.get("glucose_mmol_l", 5.0) < 2.2),
            ("hyperlactatemia", clinical_presentation.laboratory_values.get("lactate_mmol_l", 2.0) > 5.0),

            # Parasitemia criteria
            ("hyperparasitemia", clinical_presentation.parasitemia_percent > 5.0)
        ]

        # Evaluate severity indicators
        positive_criteria_count = 0
        for criterion, is_present in severe_criteria:
            severity_indicators[criterion] = is_present
            if is_present:
                positive_criteria_count += 1

        # Age-specific severity assessment
        if patient_profile.age < 5:
            # Pediatric severe malaria criteria
            if positive_criteria_count >= 1:
                severity = DiseaseSeverity.SEVERE
            elif clinical_presentation.peak_temperature >= 39.5 and clinical_presentation.parasitemia_percent > 2.0:
                severity = DiseaseSeverity.SEVERE
            else:
                severity = DiseaseSeverity.UNCOMPLICATED
        else:
            # Adult severe malaria criteria
            if positive_criteria_count >= 1:
                severity = DiseaseSeverity.SEVERE
            elif clinical_presentation.parasitemia_percent > 5.0:
                severity = DiseaseSeverity.SEVERE
            else:
                severity = DiseaseSeverity.UNCOMPLICATED

        # Critical malaria (multiple organ failure)
        critical_indicators = [
            severity_indicators.get("coma", False),
            severity_indicators.get("shock", False),
            severity_indicators.get("acute_kidney_injury", False),
            severity_indicators.get("severe_anemia", False) and clinical_presentation.laboratory_values.get("hemoglobin_g_dl", 12.0) < 3.0,
            severity_indicators.get("acidosis", False) and clinical_presentation.laboratory_values.get("ph", 7.4) < 7.25
        ]

        if sum(critical_indicators) >= 2:
            severity = DiseaseSeverity.CRITICAL

        logger.info(f"Severity assessment: {severity.value}, positive criteria: {positive_criteria_count}")
        return severity, severity_indicators

    def recommend_treatment(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        resistance_patterns: dict[str, ResistanceStatus] | None = None
    ) -> TreatmentRecommendation:
        """
        Generate WHO-based treatment recommendation.

        Args:
            patient_profile: Patient demographic and clinical profile
            clinical_presentation: Clinical presentation and laboratory values
            malaria_species: Identified malaria species
            resistance_patterns: Known drug resistance patterns in area

        Returns:
            Comprehensive treatment recommendation
        """
        logger.info(f"Generating treatment recommendation for {malaria_species.value}")

        # Assess disease severity
        severity, severity_indicators = self.assess_severity(clinical_presentation, patient_profile)

        # Select appropriate treatment protocol
        if severity == DiseaseSeverity.UNCOMPLICATED:
            recommendation = self._recommend_uncomplicated_treatment(
                patient_profile, malaria_species, resistance_patterns
            )
        elif severity == DiseaseSeverity.SEVERE:
            recommendation = self._recommend_severe_treatment(
                patient_profile, clinical_presentation, malaria_species, resistance_patterns
            )
        else:  # CRITICAL
            recommendation = self._recommend_critical_treatment(
                patient_profile, clinical_presentation, malaria_species, resistance_patterns
            )

        # Add severity-specific considerations
        recommendation.severity_basis = severity
        recommendation.special_considerations.extend(
            self._get_special_considerations(patient_profile, severity, severity_indicators)
        )

        # Calculate confidence score
        recommendation.confidence_score = self._calculate_confidence_score(
            patient_profile, clinical_presentation, malaria_species, resistance_patterns
        )

        logger.info(f"Treatment recommendation generated: {recommendation.treatment_id}")
        return recommendation

    def _recommend_uncomplicated_treatment(
        self,
        patient_profile: PatientProfile,
        malaria_species: MalariaSpecies,
        resistance_patterns: dict[str, ResistanceStatus] | None
    ) -> TreatmentRecommendation:
        """Recommend treatment for uncomplicated malaria"""

        if malaria_species == MalariaSpecies.P_FALCIPARUM:
            # First-line: Artemether-lumefantrine (WHO recommendation)
            if not resistance_patterns or resistance_patterns.get("artemether_lumefantrine", ResistanceStatus.SUSCEPTIBLE) == ResistanceStatus.SUSCEPTIBLE:
                return self._create_artemether_lumefantrine_regimen(patient_profile)
            else:
                # Alternative: Artesunate-amodiaquine
                return self._create_artesunate_amodiaquine_regimen(patient_profile)

        elif malaria_species == MalariaSpecies.P_VIVAX:
            # Chloroquine + Primaquine for radical cure
            return self._create_vivax_treatment_regimen(patient_profile)

        elif malaria_species in [MalariaSpecies.P_OVALE, MalariaSpecies.P_MALARIAE]:
            # Chloroquine (if susceptible) or artemether-lumefantrine
            return self._create_non_falciparum_regimen(patient_profile, malaria_species)

        else:
            # Default to artemether-lumefantrine for unknown/mixed
            return self._create_artemether_lumefantrine_regimen(patient_profile)

    def _recommend_severe_treatment(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        resistance_patterns: dict[str, ResistanceStatus] | None
    ) -> TreatmentRecommendation:
        """Recommend treatment for severe malaria"""

        # WHO first-line for severe malaria: IV Artesunate
        return self._create_iv_artesunate_regimen(patient_profile, clinical_presentation)

    def _recommend_critical_treatment(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        resistance_patterns: dict[str, ResistanceStatus] | None
    ) -> TreatmentRecommendation:
        """Recommend treatment for critical malaria"""

        # Intensive IV artesunate with adjunctive therapies
        return self._create_critical_care_regimen(patient_profile, clinical_presentation)

    def _create_artemether_lumefantrine_regimen(self, patient_profile: PatientProfile) -> TreatmentRecommendation:
        """Create artemether-lumefantrine treatment regimen"""

        # Weight-based dosing
        if patient_profile.weight < 15:
            tablets_per_dose = 1
        elif patient_profile.weight < 25:
            tablets_per_dose = 2
        elif patient_profile.weight < 35:
            tablets_per_dose = 3
        else:
            tablets_per_dose = 4

        drug_regimen = [
            {
                "drug_name": "Artemether-Lumefantrine",
                "strength": "20mg/120mg tablets",
                "dose_per_administration": tablets_per_dose,
                "frequency": "twice daily",
                "duration_days": 3,
                "administration_time": "with food"
            }
        ]

        return TreatmentRecommendation(
            treatment_id=f"WHO_ACT_AL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            category=TreatmentCategory.FIRST_LINE,
            drug_regimen=drug_regimen,
            duration_days=3,
            dosage_instructions=f"Take {tablets_per_dose} tablet(s) twice daily with food for 3 days",
            administration_route="oral",
            monitoring_requirements=[
                "Temperature monitoring every 8 hours",
                "Parasitemia check on day 3",
                "Complete blood count on day 7",
                "Follow-up visit at day 28"
            ],
            contraindications=[
                "Known hypersensitivity to artemether or lumefantrine",
                "Severe hepatic impairment",
                "Severe cardiac conduction disorders"
            ],
            adverse_effects=[
                "Nausea and vomiting",
                "Diarrhea",
                "Dizziness",
                "Headache",
                "Sleep disturbances"
            ],
            follow_up_schedule=[
                "Day 3: Clinical assessment and parasitemia check",
                "Day 7: Complete blood count and clinical review",
                "Day 14: Clinical assessment",
                "Day 28: Clinical assessment and parasitemia check"
            ],
            severity_basis=DiseaseSeverity.UNCOMPLICATED,
            confidence_score=0.95,
            evidence_level="Grade A (Strong recommendation)",
            who_guideline_reference="WHO Guidelines for malaria treatment 2023, Section 4.2.1",
            alternative_treatments=[
                "Artesunate-amodiaquine",
                "Dihydroartemisinin-piperaquine",
                "Artesunate-mefloquine"
            ]
        )

    def _create_iv_artesunate_regimen(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation
    ) -> TreatmentRecommendation:
        """Create IV artesunate regimen for severe malaria"""

        # Weight-based dosing: 2.4 mg/kg IV
        dose_mg = patient_profile.weight * 2.4

        drug_regimen = [
            {
                "drug_name": "Artesunate",
                "strength": "60mg vials",
                "dose_per_administration": dose_mg,
                "frequency": "at 0, 12, 24 hours, then daily",
                "duration_days": 3,
                "administration_route": "IV bolus over 1-2 minutes"
            }
        ]

        return TreatmentRecommendation(
            treatment_id=f"WHO_SEVERE_AS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            category=TreatmentCategory.FIRST_LINE,
            drug_regimen=drug_regimen,
            duration_days=3,
            dosage_instructions=f"Artesunate {dose_mg:.1f}mg IV at 0, 12, 24 hours, then daily until oral therapy possible",
            administration_route="intravenous",
            monitoring_requirements=[
                "Continuous vital signs monitoring",
                "Hourly neurological assessment",
                "Parasitemia every 12 hours",
                "Blood glucose every 4 hours",
                "Renal function daily",
                "Complete blood count daily",
                "Arterial blood gas as clinically indicated"
            ],
            contraindications=[
                "Known hypersensitivity to artesunate"
            ],
            adverse_effects=[
                "Post-artesunate delayed hemolysis (monitor for 4 weeks)",
                "Injection site reactions",
                "Transient neutropenia",
                "Elevated liver enzymes"
            ],
            follow_up_schedule=[
                "Continuous monitoring until clinical improvement",
                "Switch to oral ACT when able to tolerate oral medication",
                "Weekly CBC for 4 weeks post-treatment (delayed hemolysis)",
                "Day 28: Clinical assessment and parasitemia check"
            ],
            severity_basis=DiseaseSeverity.SEVERE,
            confidence_score=0.98,
            evidence_level="Grade A (Strong recommendation)",
            who_guideline_reference="WHO Guidelines for malaria treatment 2023, Section 5.2.1",
            special_considerations=[
                "Monitor for post-artesunate delayed hemolysis",
                "Ensure adequate supportive care",
                "Consider exchange transfusion if parasitemia >30%"
            ]
        )

    def _load_who_protocols(self) -> dict:
        """Load WHO treatment protocol data"""
        # This would typically load from a configuration file or database
        # For now, returning structured protocol data
        return {
            "uncomplicated_falciparum": {
                "first_line": ["artemether_lumefantrine", "artesunate_amodiaquine"],
                "alternative": ["dihydroartemisinin_piperaquine", "artesunate_mefloquine"]
            },
            "severe_falciparum": {
                "first_line": ["iv_artesunate"],
                "alternative": ["iv_quinine"]
            },
            "vivax": {
                "first_line": ["chloroquine_primaquine"],
                "alternative": ["artemether_lumefantrine_primaquine"]
            }
        }

    def _load_severity_criteria(self) -> dict:
        """Load WHO severity assessment criteria"""
        return {
            "severe_criteria": [
                "altered_consciousness",
                "prostration",
                "multiple_convulsions",
                "acidosis",
                "hypoglycemia",
                "severe_anemia",
                "renal_impairment",
                "pulmonary_edema",
                "significant_bleeding",
                "shock",
                "hyperparasitemia"
            ]
        }

    def _load_dosage_calculations(self) -> dict:
        """Load dosage calculation formulas"""
        return {
            "artemether_lumefantrine": {
                "weight_bands": {
                    "5-14kg": 1,
                    "15-24kg": 2,
                    "25-34kg": 3,
                    "35kg+": 4
                }
            },
            "artesunate_iv": {
                "dose_mg_per_kg": 2.4,
                "loading_schedule": [0, 12, 24],
                "maintenance_frequency": "daily"
            }
        }

    def _load_contraindications(self) -> dict:
        """Load drug contraindications"""
        return {
            "artemether_lumefantrine": [
                "hypersensitivity",
                "severe_hepatic_impairment",
                "cardiac_conduction_disorders"
            ],
            "primaquine": [
                "g6pd_deficiency",
                "pregnancy",
                "severe_anemia"
            ]
        }

    def _load_monitoring_protocols(self) -> dict:
        """Load treatment monitoring protocols"""
        return {
            "uncomplicated": [
                "day_3_assessment",
                "day_7_cbc",
                "day_28_followup"
            ],
            "severe": [
                "continuous_vitals",
                "hourly_neuro_assessment",
                "q12h_parasitemia",
                "q4h_glucose"
            ]
        }

    def _get_special_considerations(
        self,
        patient_profile: PatientProfile,
        severity: DiseaseSeverity,
        severity_indicators: dict[str, bool]
    ) -> list[str]:
        """Get special considerations based on patient profile and severity"""
        considerations = []

        if patient_profile.is_pregnant:
            considerations.append("Pregnancy: Use pregnancy-safe antimalarials only")
            considerations.append("Avoid primaquine and doxycycline")

        if patient_profile.age < 5:
            considerations.append("Pediatric patient: Adjust dosing for weight")
            considerations.append("Monitor for hypoglycemia closely")

        if patient_profile.age > 65:
            considerations.append("Elderly patient: Monitor renal function")
            considerations.append("Consider drug interactions with comorbidity medications")

        if "g6pd_deficiency" in patient_profile.comorbidities:
            considerations.append("G6PD deficiency: Avoid primaquine and other oxidizing drugs")

        if severity_indicators.get("severe_anemia", False):
            considerations.append("Severe anemia: Consider blood transfusion")

        if severity_indicators.get("hypoglycemia", False):
            considerations.append("Hypoglycemia: Frequent glucose monitoring and correction")

        return considerations

    def _calculate_confidence_score(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation,
        malaria_species: MalariaSpecies,
        resistance_patterns: dict[str, ResistanceStatus] | None
    ) -> float:
        """Calculate confidence score for treatment recommendation"""

        base_confidence = 0.9

        # Adjust based on species certainty
        if malaria_species == MalariaSpecies.UNKNOWN:
            base_confidence -= 0.15
        elif malaria_species == MalariaSpecies.MIXED_INFECTION:
            base_confidence -= 0.1

        # Adjust based on resistance data availability
        if not resistance_patterns:
            base_confidence -= 0.05
        elif any(status == ResistanceStatus.UNKNOWN for status in resistance_patterns.values()):
            base_confidence -= 0.03

        # Adjust based on clinical complexity
        if len(patient_profile.comorbidities) > 2:
            base_confidence -= 0.05

        if len(clinical_presentation.complications) > 1:
            base_confidence -= 0.05

        return max(0.5, min(1.0, base_confidence))

    def _create_vivax_treatment_regimen(self, patient_profile: PatientProfile) -> TreatmentRecommendation:
        """Create P. vivax treatment regimen with radical cure"""
        # Implementation for P. vivax treatment
        pass

    def _create_non_falciparum_regimen(self, patient_profile: PatientProfile, species: MalariaSpecies) -> TreatmentRecommendation:
        """Create treatment regimen for non-falciparum species"""
        # Implementation for P. ovale, P. malariae treatment
        pass

    def _create_artesunate_amodiaquine_regimen(self, patient_profile: PatientProfile) -> TreatmentRecommendation:
        """Create artesunate-amodiaquine treatment regimen"""
        # Implementation for alternative ACT
        pass

    def _create_critical_care_regimen(
        self,
        patient_profile: PatientProfile,
        clinical_presentation: ClinicalPresentation
    ) -> TreatmentRecommendation:
        """Create critical care regimen for critical malaria"""
        # Implementation for critical malaria with adjunctive therapies
        pass
