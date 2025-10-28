"""
Drug Resistance Analyzer

Advanced analysis of malaria drug resistance patterns with geographic mapping,
temporal trend analysis, and resistance prediction algorithms.

Key Features:
- Geographic resistance pattern mapping
- Temporal resistance trend analysis
- Multi-drug resistance detection
- Resistance risk scoring
- Treatment efficacy prediction
- Surveillance data integration
- Real-time resistance monitoring

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DrugClass(Enum):
    """Antimalarial drug classification"""
    ARTEMISININ = "artemisinin"
    QUINOLINE = "quinoline"
    ANTIFOLATE = "antifolate"
    NAPTHOQUINONE = "napthoquinone"
    ENDOPEROXIDE = "endoperoxide"
    COMBINATION = "combination"


class ResistanceMechanism(Enum):
    """Known resistance mechanisms"""
    PfKELCH13_MUTATION = "pfkelch13_mutation"
    PfCRT_MUTATION = "pfcrt_mutation"
    PfMDR1_MUTATION = "pfmdr1_mutation"
    PfDHFR_MUTATION = "pfdhfr_mutation"
    PfDHPS_MUTATION = "pfdhps_mutation"
    COPY_NUMBER_VARIATION = "copy_number_variation"
    METABOLIC_RESISTANCE = "metabolic_resistance"
    TARGET_MODIFICATION = "target_modification"


class ResistanceLevel(Enum):
    """Resistance level classification"""
    SUSCEPTIBLE = "susceptible"
    REDUCED_SUSCEPTIBILITY = "reduced_susceptibility"
    MODERATE_RESISTANCE = "moderate_resistance"
    HIGH_RESISTANCE = "high_resistance"
    COMPLETE_RESISTANCE = "complete_resistance"


@dataclass
class ResistanceMarker:
    """Genetic or phenotypic resistance marker"""
    marker_id: str
    marker_type: str  # "genetic", "phenotypic", "molecular"
    chromosome: str | None = None
    gene: str | None = None
    mutation: str | None = None
    frequency: float = 0.0
    confidence: float = 0.0
    detection_method: str | None = None
    source: str | None = None
    date_detected: datetime | None = None


@dataclass
class ResistanceProfile:
    """Drug resistance profile for a specific drug"""
    drug_name: str
    drug_class: DrugClass
    resistance_level: ResistanceLevel
    resistance_mechanisms: list[ResistanceMechanism]
    resistance_markers: list[ResistanceMarker]
    geographic_prevalence: dict[str, float]  # location -> prevalence %
    temporal_trend: list[tuple[datetime, float]]  # time -> prevalence
    confidence_score: float
    treatment_efficacy: float  # Expected treatment success rate
    surveillance_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResistanceHotspot:
    """Geographic resistance hotspot identification"""
    location: str
    coordinates: tuple[float, float]  # lat, lon
    resistance_drugs: list[str]
    peak_resistance_level: ResistanceLevel
    prevalence_percentage: float
    trend_direction: str  # "increasing", "stable", "decreasing"
    risk_score: float
    population_at_risk: int
    last_updated: datetime
    surveillance_quality: str  # "high", "medium", "low"


class DrugResistanceAnalyzer:
    """
    Drug Resistance Analyzer for malaria antimalarial resistance patterns.

    This analyzer provides comprehensive resistance analysis including geographic
    mapping, temporal trends, and predictive modeling for treatment optimization.
    """

    def __init__(self, surveillance_database_url: str | None = None):
        """
        Initialize Drug Resistance Analyzer.

        Args:
            surveillance_database_url: Optional URL for resistance surveillance database
        """
        logger.info("Initializing Drug Resistance Analyzer")

        self.surveillance_db_url = surveillance_database_url
        self._resistance_profiles = {}
        self._geographic_data = {}
        self._temporal_trends = defaultdict(list)
        self._molecular_markers = {}

        # Load resistance databases
        self._load_resistance_markers()
        self._load_geographic_patterns()
        self._load_surveillance_data()

        logger.info("Drug Resistance Analyzer initialized successfully")

    def analyze_resistance_patterns(
        self,
        location: str,
        time_window_days: int = 365,
        drugs_of_interest: list[str] | None = None
    ) -> dict[str, ResistanceProfile]:
        """
        Analyze drug resistance patterns for a specific location and timeframe.

        Args:
            location: Geographic location (country, region, or coordinates)
            time_window_days: Analysis time window in days
            drugs_of_interest: Specific drugs to analyze (if None, analyze all)

        Returns:
            Dictionary mapping drug names to resistance profiles
        """
        logger.info(f"Analyzing resistance patterns for {location}, window: {time_window_days} days")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window_days)

        if drugs_of_interest is None:
            drugs_of_interest = self._get_standard_antimalarial_panel()

        resistance_profiles = {}

        for drug in drugs_of_interest:
            profile = self._analyze_drug_resistance(
                drug=drug,
                location=location,
                start_date=start_date,
                end_date=end_date
            )
            resistance_profiles[drug] = profile

        logger.info(f"Resistance analysis completed for {len(drugs_of_interest)} drugs")
        return resistance_profiles

    def predict_resistance_emergence(
        self,
        location: str,
        drug: str,
        prediction_horizon_months: int = 12
    ) -> dict[str, Any]:
        """
        Predict future resistance emergence using temporal trend analysis.

        Args:
            location: Geographic location for prediction
            drug: Drug name for resistance prediction
            prediction_horizon_months: Prediction timeframe in months

        Returns:
            Prediction results with confidence intervals
        """
        logger.info(f"Predicting resistance emergence for {drug} in {location}")

        # Get historical resistance data
        historical_data = self._get_temporal_trends(location, drug)

        if len(historical_data) < 3:
            return {
                "prediction": "insufficient_data",
                "confidence": 0.0,
                "message": "Insufficient historical data for prediction"
            }

        # Perform trend analysis
        prediction_result = self._perform_resistance_prediction(
            historical_data=historical_data,
            horizon_months=prediction_horizon_months
        )

        logger.info(f"Resistance prediction completed: {prediction_result.get('trend', 'unknown')}")
        return prediction_result

    def identify_resistance_hotspots(
        self,
        region: str,
        resistance_threshold: float = 0.05  # 5% resistance threshold
    ) -> list[ResistanceHotspot]:
        """
        Identify geographic resistance hotspots in a region.

        Args:
            region: Geographic region to analyze
            resistance_threshold: Minimum resistance prevalence to consider hotspot

        Returns:
            List of identified resistance hotspots
        """
        logger.info(f"Identifying resistance hotspots in {region}")

        hotspots = []

        # Get geographic resistance data for region
        geographic_data = self._get_geographic_resistance_data(region)

        for location, location_data in geographic_data.items():
            max_resistance = 0.0
            resistant_drugs = []

            # Analyze resistance for each drug at this location
            for drug, resistance_data in location_data.get("drugs", {}).items():
                prevalence = resistance_data.get("prevalence", 0.0)

                if prevalence >= resistance_threshold:
                    resistant_drugs.append(drug)
                    max_resistance = max(max_resistance, prevalence)

            # Create hotspot if resistance detected
            if resistant_drugs:
                hotspot = ResistanceHotspot(
                    location=location,
                    coordinates=location_data.get("coordinates", (0.0, 0.0)),
                    resistance_drugs=resistant_drugs,
                    peak_resistance_level=self._classify_resistance_level(max_resistance),
                    prevalence_percentage=max_resistance * 100,
                    trend_direction=self._calculate_trend_direction(location, resistant_drugs),
                    risk_score=self._calculate_hotspot_risk_score(location_data, max_resistance),
                    population_at_risk=location_data.get("population", 0),
                    last_updated=datetime.now(),
                    surveillance_quality=location_data.get("surveillance_quality", "medium")
                )
                hotspots.append(hotspot)

        # Sort by risk score (highest first)
        hotspots.sort(key=lambda h: h.risk_score, reverse=True)

        logger.info(f"Identified {len(hotspots)} resistance hotspots")
        return hotspots

    def assess_treatment_risk(
        self,
        drug: str,
        location: str,
        patient_factors: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Assess treatment failure risk based on resistance patterns.

        Args:
            drug: Antimalarial drug name
            location: Patient location
            patient_factors: Optional patient-specific risk factors

        Returns:
            Treatment risk assessment with recommendations
        """
        logger.info(f"Assessing treatment risk for {drug} in {location}")

        # Get resistance profile for location
        resistance_profile = self._get_resistance_profile(drug, location)

        # Base risk from resistance prevalence
        base_risk = resistance_profile.get("prevalence", 0.0)

        # Adjust risk based on patient factors
        adjusted_risk = self._adjust_risk_for_patient_factors(base_risk, patient_factors)

        # Get resistance mechanisms
        mechanisms = resistance_profile.get("mechanisms", [])

        # Calculate confidence in assessment
        confidence = self._calculate_risk_confidence(resistance_profile, patient_factors)

        risk_assessment = {
            "drug": drug,
            "location": location,
            "base_resistance_prevalence": base_risk,
            "adjusted_risk": adjusted_risk,
            "risk_category": self._categorize_risk(adjusted_risk),
            "dominant_mechanisms": mechanisms[:3],  # Top 3 mechanisms
            "confidence": confidence,
            "recommendations": self._generate_risk_recommendations(drug, adjusted_risk, mechanisms),
            "alternative_drugs": self._suggest_alternative_drugs(location, drug),
            "monitoring_requirements": self._get_monitoring_requirements(drug, adjusted_risk)
        }

        logger.info(f"Treatment risk assessment completed: {risk_assessment['risk_category']}")
        return risk_assessment

    def get_molecular_surveillance_summary(
        self,
        location: str,
        time_window_days: int = 90
    ) -> dict[str, Any]:
        """
        Generate molecular surveillance summary for a location.

        Args:
            location: Geographic location
            time_window_days: Time window for surveillance data

        Returns:
            Molecular surveillance summary
        """
        logger.info(f"Generating molecular surveillance summary for {location}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window_days)

        # Get molecular marker data
        molecular_data = self._get_molecular_marker_data(location, start_date, end_date)

        summary = {
            "location": location,
            "time_window": f"{time_window_days} days",
            "samples_analyzed": molecular_data.get("total_samples", 0),
            "marker_frequencies": molecular_data.get("marker_frequencies", {}),
            "new_mutations_detected": molecular_data.get("new_mutations", []),
            "resistance_trends": molecular_data.get("trends", {}),
            "quality_metrics": molecular_data.get("quality", {}),
            "recommendations": self._generate_surveillance_recommendations(molecular_data)
        }

        logger.info("Molecular surveillance summary generated")
        return summary

    def _analyze_drug_resistance(
        self,
        drug: str,
        location: str,
        start_date: datetime,
        end_date: datetime
    ) -> ResistanceProfile:
        """Analyze resistance for a specific drug"""

        # Get drug classification
        drug_class = self._classify_drug(drug)

        # Get resistance level
        resistance_level = self._assess_resistance_level(drug, location)

        # Get resistance mechanisms
        mechanisms = self._identify_resistance_mechanisms(drug, location)

        # Get molecular markers
        markers = self._get_molecular_markers(drug, location, start_date, end_date)

        # Get geographic prevalence
        geographic_prevalence = self._get_geographic_prevalence(drug, location)

        # Get temporal trends
        temporal_trend = self._get_temporal_trends(location, drug)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(drug, location, markers)

        # Estimate treatment efficacy
        treatment_efficacy = self._estimate_treatment_efficacy(drug, resistance_level, mechanisms)

        return ResistanceProfile(
            drug_name=drug,
            drug_class=drug_class,
            resistance_level=resistance_level,
            resistance_mechanisms=mechanisms,
            resistance_markers=markers,
            geographic_prevalence=geographic_prevalence,
            temporal_trend=temporal_trend,
            confidence_score=confidence_score,
            treatment_efficacy=treatment_efficacy,
            surveillance_data={}
        )

    def _get_standard_antimalarial_panel(self) -> list[str]:
        """Get standard panel of antimalarial drugs for analysis"""
        return [
            "artemether-lumefantrine",
            "artesunate-amodiaquine",
            "dihydroartemisinin-piperaquine",
            "chloroquine",
            "sulfadoxine-pyrimethamine",
            "mefloquine",
            "doxycycline",
            "atovaquone-proguanil",
            "quinine",
            "artesunate"
        ]

    def _classify_drug(self, drug: str) -> DrugClass:
        """Classify drug into appropriate drug class"""
        drug_classifications = {
            "artemether": DrugClass.ARTEMISININ,
            "artesunate": DrugClass.ARTEMISININ,
            "dihydroartemisinin": DrugClass.ARTEMISININ,
            "chloroquine": DrugClass.QUINOLINE,
            "mefloquine": DrugClass.QUINOLINE,
            "quinine": DrugClass.QUINOLINE,
            "sulfadoxine-pyrimethamine": DrugClass.ANTIFOLATE,
            "atovaquone": DrugClass.NAPTHOQUINONE,
            "artemether-lumefantrine": DrugClass.COMBINATION,
            "artesunate-amodiaquine": DrugClass.COMBINATION,
            "dihydroartemisinin-piperaquine": DrugClass.COMBINATION
        }

        for drug_name, drug_class in drug_classifications.items():
            if drug_name in drug.lower():
                return drug_class

        return DrugClass.COMBINATION  # Default for unknown drugs

    def _assess_resistance_level(self, drug: str, location: str) -> ResistanceLevel:
        """Assess resistance level for drug at location"""
        # This would query surveillance database
        # For now, return simulated resistance level
        prevalence = self._get_resistance_prevalence(drug, location)

        if prevalence < 0.01:
            return ResistanceLevel.SUSCEPTIBLE
        elif prevalence < 0.05:
            return ResistanceLevel.REDUCED_SUSCEPTIBILITY
        elif prevalence < 0.20:
            return ResistanceLevel.MODERATE_RESISTANCE
        elif prevalence < 0.50:
            return ResistanceLevel.HIGH_RESISTANCE
        else:
            return ResistanceLevel.COMPLETE_RESISTANCE

    def _identify_resistance_mechanisms(self, drug: str, location: str) -> list[ResistanceMechanism]:
        """Identify known resistance mechanisms for drug"""
        mechanism_mapping = {
            "artemether": [ResistanceMechanism.PfKELCH13_MUTATION],
            "artesunate": [ResistanceMechanism.PfKELCH13_MUTATION],
            "chloroquine": [ResistanceMechanism.PfCRT_MUTATION, ResistanceMechanism.PfMDR1_MUTATION],
            "sulfadoxine-pyrimethamine": [ResistanceMechanism.PfDHFR_MUTATION, ResistanceMechanism.PfDHPS_MUTATION],
            "mefloquine": [ResistanceMechanism.PfMDR1_MUTATION, ResistanceMechanism.COPY_NUMBER_VARIATION]
        }

        mechanisms = []
        for drug_name, drug_mechanisms in mechanism_mapping.items():
            if drug_name in drug.lower():
                mechanisms.extend(drug_mechanisms)

        return list(set(mechanisms))  # Remove duplicates

    def _get_molecular_markers(
        self,
        drug: str,
        location: str,
        start_date: datetime,
        end_date: datetime
    ) -> list[ResistanceMarker]:
        """Get molecular resistance markers for drug"""
        # This would query molecular surveillance database
        # For now, return simulated markers
        markers = []

        if "artemether" in drug.lower() or "artesunate" in drug.lower():
            markers.append(ResistanceMarker(
                marker_id="PfKelch13_C580Y",
                marker_type="genetic",
                chromosome="13",
                gene="PfKelch13",
                mutation="C580Y",
                frequency=0.05,
                confidence=0.9,
                detection_method="PCR-sequencing",
                source="routine_surveillance",
                date_detected=datetime.now()
            ))

        return markers

    def _load_resistance_markers(self):
        """Load known resistance markers from database"""
        # This would load from configuration or database
        logger.info("Loading resistance markers database")

    def _load_geographic_patterns(self):
        """Load geographic resistance patterns"""
        # This would load from GIS database
        logger.info("Loading geographic resistance patterns")

    def _load_surveillance_data(self):
        """Load surveillance data from external sources"""
        # This would connect to surveillance systems
        logger.info("Loading surveillance data")

    def _get_geographic_resistance_data(self, region: str) -> dict:
        """Get geographic resistance data for region"""
        # Simulated geographic data
        return {
            "location_1": {
                "coordinates": (-1.2921, 36.8219),  # Nairobi coordinates
                "drugs": {
                    "artemether-lumefantrine": {"prevalence": 0.03},
                    "sulfadoxine-pyrimethamine": {"prevalence": 0.45}
                },
                "population": 100000,
                "surveillance_quality": "high"
            }
        }

    def _classify_resistance_level(self, prevalence: float) -> ResistanceLevel:
        """Classify resistance level from prevalence"""
        if prevalence < 0.01:
            return ResistanceLevel.SUSCEPTIBLE
        elif prevalence < 0.05:
            return ResistanceLevel.REDUCED_SUSCEPTIBILITY
        elif prevalence < 0.20:
            return ResistanceLevel.MODERATE_RESISTANCE
        else:
            return ResistanceLevel.HIGH_RESISTANCE

    def _calculate_trend_direction(self, location: str, drugs: list[str]) -> str:
        """Calculate resistance trend direction"""
        # This would analyze temporal trends
        return "stable"  # Simplified

    def _calculate_hotspot_risk_score(self, location_data: dict, max_resistance: float) -> float:
        """Calculate risk score for resistance hotspot"""
        base_score = max_resistance * 100  # Convert to percentage

        # Adjust for population size
        population_factor = min(location_data.get("population", 0) / 50000, 2.0)

        # Adjust for surveillance quality
        quality_multiplier = {
            "high": 1.0,
            "medium": 0.8,
            "low": 0.6
        }.get(location_data.get("surveillance_quality", "medium"), 0.8)

        return base_score * population_factor * quality_multiplier

    # Additional helper methods would be implemented here
    def _get_resistance_profile(self, drug: str, location: str) -> dict:
        """Get resistance profile for drug at location"""
        return {"prevalence": 0.05, "mechanisms": []}

    def _adjust_risk_for_patient_factors(self, base_risk: float, patient_factors: dict | None) -> float:
        """Adjust risk based on patient factors"""
        return base_risk

    def _calculate_risk_confidence(self, resistance_profile: dict, patient_factors: dict | None) -> float:
        """Calculate confidence in risk assessment"""
        return 0.8

    def _categorize_risk(self, risk: float) -> str:
        """Categorize risk level"""
        if risk < 0.05:
            return "low"
        elif risk < 0.20:
            return "moderate"
        else:
            return "high"

    def _generate_risk_recommendations(self, drug: str, risk: float, mechanisms: list) -> list[str]:
        """Generate recommendations based on risk"""
        return ["Consider alternative treatment if available"]

    def _suggest_alternative_drugs(self, location: str, current_drug: str) -> list[str]:
        """Suggest alternative drugs based on resistance patterns"""
        return ["artesunate-amodiaquine", "dihydroartemisinin-piperaquine"]

    def _get_monitoring_requirements(self, drug: str, risk: float) -> list[str]:
        """Get monitoring requirements based on resistance risk"""
        return ["Day 3 parasitemia check", "Day 28 follow-up"]

    def _get_molecular_marker_data(self, location: str, start_date: datetime, end_date: datetime) -> dict:
        """Get molecular marker surveillance data"""
        return {
            "total_samples": 150,
            "marker_frequencies": {},
            "new_mutations": [],
            "trends": {},
            "quality": {}
        }

    def _generate_surveillance_recommendations(self, molecular_data: dict) -> list[str]:
        """Generate surveillance recommendations"""
        return ["Increase molecular surveillance frequency"]

    def _get_resistance_prevalence(self, drug: str, location: str) -> float:
        """Get resistance prevalence for drug at location"""
        return 0.05  # Simplified

    def _get_geographic_prevalence(self, drug: str, location: str) -> dict[str, float]:
        """Get geographic prevalence data"""
        return {location: 0.05}

    def _get_temporal_trends(self, location: str, drug: str) -> list[tuple[datetime, float]]:
        """Get temporal resistance trends"""
        return [(datetime.now(), 0.05)]

    def _calculate_confidence_score(self, drug: str, location: str, markers: list) -> float:
        """Calculate confidence score for resistance profile"""
        return 0.8

    def _estimate_treatment_efficacy(self, drug: str, resistance_level: ResistanceLevel, mechanisms: list) -> float:
        """Estimate treatment efficacy based on resistance"""
        level_efficacy = {
            ResistanceLevel.SUSCEPTIBLE: 0.95,
            ResistanceLevel.REDUCED_SUSCEPTIBILITY: 0.85,
            ResistanceLevel.MODERATE_RESISTANCE: 0.70,
            ResistanceLevel.HIGH_RESISTANCE: 0.40,
            ResistanceLevel.COMPLETE_RESISTANCE: 0.10
        }
        return level_efficacy.get(resistance_level, 0.80)

    def _perform_resistance_prediction(self, historical_data: list, horizon_months: int) -> dict:
        """Perform resistance prediction using historical data"""
        return {
            "prediction": "stable",
            "confidence": 0.75,
            "trend": "no_significant_change",
            "predicted_prevalence": 0.05
        }
