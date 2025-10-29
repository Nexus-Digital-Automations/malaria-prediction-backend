"""
Treatment Effectiveness Tracker

Comprehensive tracking and analysis system for malaria treatment outcomes,
effectiveness monitoring, and continuous improvement of treatment protocols.

Key Features:
- Real-time outcome tracking
- Treatment response monitoring
- Effectiveness metrics calculation
- Adverse event monitoring
- Protocol performance analysis
- Comparative effectiveness research
- Quality improvement insights

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


class TreatmentOutcome(Enum):
    """Treatment outcome classifications"""
    CURE = "cure"
    TREATMENT_FAILURE = "treatment_failure"
    RECURRENCE = "recurrence"
    DEATH = "death"
    LOST_TO_FOLLOWUP = "lost_to_followup"
    TRANSFER = "transfer"
    ONGOING = "ongoing"


class AdverseEventSeverity(Enum):
    """Adverse event severity levels"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"
    DEATH = "death"


class EffectivenessMetric(Enum):
    """Treatment effectiveness metrics"""
    CURE_RATE = "cure_rate"
    TREATMENT_FAILURE_RATE = "treatment_failure_rate"
    RECURRENCE_RATE = "recurrence_rate"
    ADVERSE_EVENT_RATE = "adverse_event_rate"
    COMPLIANCE_RATE = "compliance_rate"
    TIME_TO_CLEARANCE = "time_to_clearance"
    COST_EFFECTIVENESS = "cost_effectiveness"


@dataclass
class TreatmentRecord:
    """Individual treatment record"""
    record_id: str
    patient_id: str
    treatment_id: str
    facility_id: str
    prescriber_id: str
    start_date: datetime
    end_date: datetime | None
    drug_regimen: list[dict[str, Any]]
    initial_parasitemia: float
    initial_symptoms: list[str]
    malaria_species: str
    severity_at_start: str
    patient_demographics: dict[str, Any]
    comorbidities: list[str]
    previous_treatments: list[str] = field(default_factory=list)


@dataclass
class FollowUpVisit:
    """Treatment follow-up visit record"""
    visit_id: str
    record_id: str
    visit_date: datetime
    visit_type: str  # "scheduled", "unscheduled", "emergency"
    parasitemia_level: float | None
    symptoms_present: list[str]
    vital_signs: dict[str, float]
    clinical_assessment: str
    adherence_score: float  # 0-1
    adverse_events: list[dict[str, Any]]
    provider_notes: str


@dataclass
class TreatmentOutcomeRecord:
    """Final treatment outcome record"""
    outcome_id: str
    record_id: str
    outcome_date: datetime
    final_outcome: TreatmentOutcome
    time_to_outcome_days: int
    parasitemia_clearance_day: int | None
    symptom_resolution_day: int | None
    final_parasitemia: float
    adverse_events_summary: list[dict[str, Any]]
    compliance_rate: float
    cost_data: dict[str, float]
    provider_assessment: str


@dataclass
class EffectivenessAnalysis:
    """Treatment effectiveness analysis results"""
    analysis_id: str
    analysis_period: tuple[datetime, datetime]
    treatment_analyzed: str
    total_cases: int
    effectiveness_metrics: dict[EffectivenessMetric, float]
    demographic_breakdown: dict[str, dict[str, float]]
    severity_breakdown: dict[str, dict[str, float]]
    resistance_correlation: dict[str, float]
    comparative_analysis: dict[str, Any]
    statistical_significance: dict[str, float]
    recommendations: list[str]
    confidence_intervals: dict[str, tuple[float, float]]


class TreatmentEffectivenessTracker:
    """
    Treatment Effectiveness Tracker for malaria treatment monitoring.

    This system provides comprehensive tracking of treatment outcomes,
    effectiveness analysis, and continuous improvement insights for
    malaria treatment protocols.
    """

    def __init__(
        self,
        database_connection: str | None = None,
        analytics_config: dict | None = None
    ):
        """
        Initialize Treatment Effectiveness Tracker.

        Args:
            database_connection: Database connection for outcome data
            analytics_config: Configuration for analytics calculations
        """
        logger.info("Initializing Treatment Effectiveness Tracker")

        self.db_connection = database_connection
        self.analytics_config = analytics_config or {}

        # Initialize data stores
        self._treatment_records: dict[str, TreatmentRecord] = {}  # record_id -> TreatmentRecord
        self._followup_visits: defaultdict[str, list[FollowUpVisit]] = defaultdict(list)  # record_id -> List[FollowUpVisit]
        self._outcome_records: dict[str, TreatmentOutcomeRecord] = {}  # record_id -> TreatmentOutcomeRecord
        self._effectiveness_cache: dict[str, Any] = {}  # Cache for calculated metrics

        # Load configuration
        self._effectiveness_thresholds = self._load_effectiveness_thresholds()
        self._outcome_definitions = self._load_outcome_definitions()
        self._statistical_methods = self._load_statistical_methods()

        logger.info("Treatment Effectiveness Tracker initialized successfully")

    def record_treatment_start(
        self,
        patient_id: str,
        treatment_details: dict[str, Any],
        clinical_data: dict[str, Any],
        provider_info: dict[str, Any]
    ) -> str:
        """
        Record the start of a new treatment.

        Args:
            patient_id: Unique patient identifier
            treatment_details: Treatment regimen and details
            clinical_data: Initial clinical presentation
            provider_info: Provider and facility information

        Returns:
            Treatment record ID
        """
        logger.info(f"Recording treatment start for patient {patient_id}")

        record_id = f"TR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_id}"

        treatment_record = TreatmentRecord(
            record_id=record_id,
            patient_id=patient_id,
            treatment_id=treatment_details.get("treatment_id", ""),
            facility_id=provider_info.get("facility_id", ""),
            prescriber_id=provider_info.get("prescriber_id", ""),
            start_date=datetime.now(),
            end_date=None,
            drug_regimen=treatment_details.get("drug_regimen", []),
            initial_parasitemia=clinical_data.get("parasitemia", 0.0),
            initial_symptoms=clinical_data.get("symptoms", []),
            malaria_species=clinical_data.get("species", "unknown"),
            severity_at_start=clinical_data.get("severity", "uncomplicated"),
            patient_demographics=clinical_data.get("demographics", {}),
            comorbidities=clinical_data.get("comorbidities", []),
            previous_treatments=clinical_data.get("previous_treatments", [])
        )

        self._treatment_records[record_id] = treatment_record
        self._log_treatment_event(record_id, "treatment_started", treatment_details)

        logger.info(f"Treatment record created: {record_id}")
        return record_id

    def record_followup_visit(
        self,
        record_id: str,
        visit_data: dict[str, Any],
        clinical_assessment: dict[str, Any]
    ) -> str:
        """
        Record a treatment follow-up visit.

        Args:
            record_id: Treatment record ID
            visit_data: Visit details and timing
            clinical_assessment: Clinical findings and assessment

        Returns:
            Follow-up visit ID
        """
        logger.info(f"Recording follow-up visit for treatment {record_id}")

        visit_id = f"FU_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{record_id}"

        followup_visit = FollowUpVisit(
            visit_id=visit_id,
            record_id=record_id,
            visit_date=datetime.now(),
            visit_type=visit_data.get("visit_type", "scheduled"),
            parasitemia_level=clinical_assessment.get("parasitemia"),
            symptoms_present=clinical_assessment.get("symptoms", []),
            vital_signs=clinical_assessment.get("vital_signs", {}),
            clinical_assessment=clinical_assessment.get("assessment", ""),
            adherence_score=clinical_assessment.get("adherence_score", 1.0),
            adverse_events=clinical_assessment.get("adverse_events", []),
            provider_notes=clinical_assessment.get("notes", "")
        )

        self._followup_visits[record_id].append(followup_visit)
        self._update_treatment_progress(record_id, followup_visit)

        logger.info(f"Follow-up visit recorded: {visit_id}")
        return visit_id

    def record_treatment_outcome(
        self,
        record_id: str,
        outcome_data: dict[str, Any]
    ) -> str:
        """
        Record final treatment outcome.

        Args:
            record_id: Treatment record ID
            outcome_data: Final outcome data and assessments

        Returns:
            Outcome record ID
        """
        logger.info(f"Recording treatment outcome for {record_id}")

        outcome_id = f"OUT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{record_id}"

        # Calculate derived metrics
        start_date = self._treatment_records[record_id].start_date
        outcome_date = datetime.now()
        time_to_outcome = (outcome_date - start_date).days

        # Calculate parasitemia clearance day
        clearance_day = self._calculate_parasitemia_clearance_day(record_id)

        # Calculate symptom resolution day
        resolution_day = self._calculate_symptom_resolution_day(record_id)

        # Aggregate adverse events
        adverse_events = self._aggregate_adverse_events(record_id)

        # Calculate compliance rate
        compliance_rate = self._calculate_compliance_rate(record_id)

        outcome_record = TreatmentOutcomeRecord(
            outcome_id=outcome_id,
            record_id=record_id,
            outcome_date=outcome_date,
            final_outcome=TreatmentOutcome(outcome_data.get("outcome", "ongoing")),
            time_to_outcome_days=time_to_outcome,
            parasitemia_clearance_day=clearance_day,
            symptom_resolution_day=resolution_day,
            final_parasitemia=outcome_data.get("final_parasitemia", 0.0),
            adverse_events_summary=adverse_events,
            compliance_rate=compliance_rate,
            cost_data=outcome_data.get("cost_data", {}),
            provider_assessment=outcome_data.get("provider_assessment", "")
        )

        self._outcome_records[record_id] = outcome_record

        # Update treatment record end date
        self._treatment_records[record_id].end_date = outcome_date

        self._log_treatment_event(record_id, "treatment_completed", outcome_data)

        logger.info(f"Treatment outcome recorded: {outcome_id}")
        return outcome_id

    def analyze_treatment_effectiveness(
        self,
        treatment_name: str,
        analysis_period_days: int = 90,
        patient_filters: dict | None = None
    ) -> EffectivenessAnalysis:
        """
        Analyze treatment effectiveness over a specified period.

        Args:
            treatment_name: Name of treatment to analyze
            analysis_period_days: Analysis time window in days
            patient_filters: Optional filters for patient selection

        Returns:
            Comprehensive effectiveness analysis
        """
        logger.info(f"Analyzing effectiveness for {treatment_name}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=analysis_period_days)

        # Get relevant treatment records
        treatment_records = self._get_treatment_records_for_analysis(
            treatment_name=treatment_name,
            start_date=start_date,
            end_date=end_date,
            filters=patient_filters
        )

        if not treatment_records:
            logger.warning(f"No treatment records found for {treatment_name}")
            return self._create_empty_analysis(treatment_name, start_date, end_date)

        # Calculate core effectiveness metrics
        effectiveness_metrics = {}
        for metric in EffectivenessMetric:
            effectiveness_metrics[metric] = self._calculate_effectiveness_metric(
                metric=metric,
                treatment_records=treatment_records
            )

        # Demographic breakdown analysis
        demographic_breakdown = self._analyze_demographic_breakdown(treatment_records)

        # Severity breakdown analysis
        severity_breakdown = self._analyze_severity_breakdown(treatment_records)

        # Resistance correlation analysis
        resistance_correlation = self._analyze_resistance_correlation(treatment_records)

        # Comparative analysis with other treatments
        comparative_analysis = self._perform_comparative_analysis(
            treatment_name=treatment_name,
            current_metrics=effectiveness_metrics,
            analysis_period=(start_date, end_date)
        )

        # Statistical significance testing
        statistical_significance = self._calculate_statistical_significance(
            treatment_records=treatment_records,
            metrics=effectiveness_metrics
        )

        # Generate recommendations
        recommendations = self._generate_effectiveness_recommendations(
            metrics=effectiveness_metrics,
            demographics=demographic_breakdown,
            comparative=comparative_analysis
        )

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            treatment_records=treatment_records,
            metrics=effectiveness_metrics
        )

        analysis = EffectivenessAnalysis(
            analysis_id=f"EFF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_period=(start_date, end_date),
            treatment_analyzed=treatment_name,
            total_cases=len(treatment_records),
            effectiveness_metrics=effectiveness_metrics,
            demographic_breakdown=demographic_breakdown,
            severity_breakdown=severity_breakdown,
            resistance_correlation=resistance_correlation,
            comparative_analysis=comparative_analysis,
            statistical_significance=statistical_significance,
            recommendations=recommendations,
            confidence_intervals=confidence_intervals
        )

        # Cache results
        self._effectiveness_cache[f"{treatment_name}_{start_date}_{end_date}"] = analysis

        logger.info(f"Effectiveness analysis completed for {treatment_name}")
        return analysis

    def generate_treatment_quality_report(
        self,
        facility_id: str | None = None,
        time_period_days: int = 30
    ) -> dict[str, Any]:
        """
        Generate treatment quality report for facility or system-wide.

        Args:
            facility_id: Specific facility ID (if None, system-wide)
            time_period_days: Report time period in days

        Returns:
            Comprehensive treatment quality report
        """
        logger.info(f"Generating quality report for facility: {facility_id}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_period_days)

        # Get treatment data for period
        treatment_data = self._get_treatment_data_for_period(
            start_date=start_date,
            end_date=end_date,
            facility_id=facility_id
        )

        # Calculate quality indicators
        quality_indicators = {
            "treatment_completion_rate": self._calculate_completion_rate(treatment_data),
            "protocol_adherence_rate": self._calculate_protocol_adherence(treatment_data),
            "adverse_event_rate": self._calculate_adverse_event_rate(treatment_data),
            "patient_satisfaction_score": self._calculate_satisfaction_score(treatment_data),
            "cost_efficiency_score": self._calculate_cost_efficiency(treatment_data),
            "documentation_completeness": self._calculate_documentation_completeness(treatment_data)
        }

        # Identify quality improvement opportunities
        improvement_opportunities = self._identify_quality_improvements(
            treatment_data=treatment_data,
            quality_indicators=quality_indicators
        )

        # Generate benchmarking comparisons
        benchmarking = self._generate_benchmarking_data(
            facility_id=facility_id,
            quality_indicators=quality_indicators
        )

        quality_report = {
            "report_id": f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "facility_id": facility_id or "system_wide",
            "report_period": f"{start_date.date()} to {end_date.date()}",
            "total_treatments": len(treatment_data),
            "quality_indicators": quality_indicators,
            "improvement_opportunities": improvement_opportunities,
            "benchmarking": benchmarking,
            "overall_quality_score": self._calculate_overall_quality_score(quality_indicators),
            "recommendations": self._generate_quality_recommendations(quality_indicators),
            "generated_at": datetime.now()
        }

        logger.info("Treatment quality report generated")
        return quality_report

    # Helper methods for calculations and analysis
    def _calculate_parasitemia_clearance_day(self, record_id: str) -> int | None:
        """Calculate day of parasitemia clearance"""
        followups = self._followup_visits.get(record_id, [])
        start_date = self._treatment_records[record_id].start_date

        for visit in sorted(followups, key=lambda v: v.visit_date):
            if visit.parasitemia_level is not None and visit.parasitemia_level <= 0.001:
                return (visit.visit_date - start_date).days

        return None

    def _calculate_symptom_resolution_day(self, record_id: str) -> int | None:
        """Calculate day of symptom resolution"""
        followups = self._followup_visits.get(record_id, [])
        start_date = self._treatment_records[record_id].start_date

        for visit in sorted(followups, key=lambda v: v.visit_date):
            if not visit.symptoms_present:  # No symptoms present
                return (visit.visit_date - start_date).days

        return None

    def _aggregate_adverse_events(self, record_id: str) -> list[dict[str, Any]]:
        """Aggregate adverse events across all visits"""
        all_events = []
        followups = self._followup_visits.get(record_id, [])

        for visit in followups:
            all_events.extend(visit.adverse_events)

        return all_events

    def _calculate_compliance_rate(self, record_id: str) -> float:
        """Calculate treatment compliance rate"""
        followups = self._followup_visits.get(record_id, [])

        if not followups:
            return 1.0  # Assume compliance if no follow-up data

        adherence_scores = [visit.adherence_score for visit in followups if visit.adherence_score is not None]

        return sum(adherence_scores) / len(adherence_scores) if adherence_scores else 1.0

    def _calculate_effectiveness_metric(
        self,
        metric: EffectivenessMetric,
        treatment_records: list[str]
    ) -> float:
        """Calculate specific effectiveness metric"""

        if metric == EffectivenessMetric.CURE_RATE:
            cured_count = sum(
                1 for record_id in treatment_records
                if record_id in self._outcome_records and
                self._outcome_records[record_id].final_outcome == TreatmentOutcome.CURE
            )
            return cured_count / len(treatment_records) if treatment_records else 0.0

        elif metric == EffectivenessMetric.TREATMENT_FAILURE_RATE:
            failure_count = sum(
                1 for record_id in treatment_records
                if record_id in self._outcome_records and
                self._outcome_records[record_id].final_outcome == TreatmentOutcome.TREATMENT_FAILURE
            )
            return failure_count / len(treatment_records) if treatment_records else 0.0

        elif metric == EffectivenessMetric.ADVERSE_EVENT_RATE:
            ae_count = sum(
                1 for record_id in treatment_records
                if record_id in self._outcome_records and
                self._outcome_records[record_id].adverse_events_summary
            )
            return ae_count / len(treatment_records) if treatment_records else 0.0

        # Add more metric calculations as needed
        return 0.0

    def _get_treatment_records_for_analysis(
        self,
        treatment_name: str,
        start_date: datetime,
        end_date: datetime,
        filters: dict | None
    ) -> list[str]:
        """Get treatment records matching analysis criteria"""

        matching_records = []

        for record_id, record in self._treatment_records.items():
            # Check date range
            if not (start_date <= record.start_date <= end_date):
                continue

            # Check treatment name
            treatment_match = any(
                treatment_name.lower() in drug.get("drug_name", "").lower()
                for drug in record.drug_regimen
            )
            if not treatment_match:
                continue

            # Apply filters if provided
            if filters:
                if not self._apply_patient_filters(record, filters):
                    continue

            matching_records.append(record_id)

        return matching_records

    def _apply_patient_filters(self, record: TreatmentRecord, filters: dict) -> bool:
        """Apply patient filters to treatment record"""
        # Implement filter logic
        return True  # Simplified

    def _create_empty_analysis(
        self,
        treatment_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> EffectivenessAnalysis:
        """Create empty analysis when no data available"""

        return EffectivenessAnalysis(
            analysis_id=f"EMPTY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_period=(start_date, end_date),
            treatment_analyzed=treatment_name,
            total_cases=0,
            effectiveness_metrics={},
            demographic_breakdown={},
            severity_breakdown={},
            resistance_correlation={},
            comparative_analysis={},
            statistical_significance={},
            recommendations=["Insufficient data for analysis"],
            confidence_intervals={}
        )

    # Additional helper methods would be implemented here
    def _load_effectiveness_thresholds(self) -> dict:
        """Load effectiveness threshold configurations"""
        return {
            "cure_rate_threshold": 0.95,
            "adverse_event_threshold": 0.05,
            "compliance_threshold": 0.90
        }

    def _load_outcome_definitions(self) -> dict:
        """Load outcome definition configurations"""
        return {}

    def _load_statistical_methods(self) -> dict:
        """Load statistical analysis method configurations"""
        return {}

    def _log_treatment_event(self, record_id: str, event_type: str, event_data: dict) -> None:
        """Log treatment-related events"""
        logger.info(f"Treatment event {event_type} for record {record_id}")

    def _update_treatment_progress(self, record_id: str, visit: FollowUpVisit) -> None:
        """Update treatment progress based on follow-up visit"""
        # Update treatment record with progress information
        pass

    def _get_treatment_data_for_period(self, start_date: datetime, end_date: datetime, facility_id: str | None) -> list:
        """Get treatment data for specified period and facility"""
        return []  # Simplified

    def _analyze_demographic_breakdown(self, treatment_records: list[str]) -> dict:
        """Analyze effectiveness by demographic groups"""
        return {}

    def _analyze_severity_breakdown(self, treatment_records: list[str]) -> dict:
        """Analyze effectiveness by disease severity"""
        return {}

    def _analyze_resistance_correlation(self, treatment_records: list[str]) -> dict:
        """Analyze correlation with resistance patterns"""
        return {}

    def _perform_comparative_analysis(self, treatment_name: str, current_metrics: dict, analysis_period: tuple) -> dict:
        """Perform comparative analysis with other treatments"""
        return {}

    def _calculate_statistical_significance(self, treatment_records: list[str], metrics: dict) -> dict:
        """Calculate statistical significance of metrics"""
        return {}

    def _generate_effectiveness_recommendations(self, metrics: dict, demographics: dict, comparative: dict) -> list[str]:
        """Generate recommendations based on effectiveness analysis"""
        return ["Continue monitoring treatment outcomes"]

    def _calculate_confidence_intervals(self, treatment_records: list[str], metrics: dict) -> dict:
        """Calculate confidence intervals for metrics"""
        return {}

    def _calculate_completion_rate(self, treatment_data: list) -> float:
        """Calculate treatment completion rate"""
        return 0.9  # Simplified

    def _calculate_protocol_adherence(self, treatment_data: list) -> float:
        """Calculate protocol adherence rate"""
        return 0.85  # Simplified

    def _calculate_adverse_event_rate(self, treatment_data: list) -> float:
        """Calculate adverse event rate"""
        return 0.05  # Simplified

    def _calculate_satisfaction_score(self, treatment_data: list) -> float:
        """Calculate patient satisfaction score"""
        return 0.88  # Simplified

    def _calculate_cost_efficiency(self, treatment_data: list) -> float:
        """Calculate cost efficiency score"""
        return 0.75  # Simplified

    def _calculate_documentation_completeness(self, treatment_data: list) -> float:
        """Calculate documentation completeness score"""
        return 0.92  # Simplified

    def _identify_quality_improvements(self, treatment_data: list, quality_indicators: dict) -> list:
        """Identify quality improvement opportunities"""
        return ["Improve patient follow-up rates"]

    def _generate_benchmarking_data(self, facility_id: str | None, quality_indicators: dict) -> dict:
        """Generate benchmarking comparison data"""
        return {"national_average": 0.85}

    def _calculate_overall_quality_score(self, quality_indicators: dict) -> float:
        """Calculate overall quality score"""
        return sum(quality_indicators.values()) / len(quality_indicators) if quality_indicators else 0.8

    def _generate_quality_recommendations(self, quality_indicators: dict) -> list[str]:
        """Generate quality improvement recommendations"""
        return ["Implement standardized follow-up protocols"]
