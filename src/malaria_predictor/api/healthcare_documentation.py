"""
Healthcare Professional Documentation Tools and Resources.

This module provides comprehensive documentation generation, reporting,
and knowledge management tools for healthcare professionals using the
malaria prediction system.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .healthcare_security import get_current_healthcare_professional, multi_language

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentationRequest(BaseModel):
    """Request for generating professional documentation."""

    document_type: str = Field(..., description="Type of document to generate")
    case_ids: list[str] = Field(default_factory=list, description="Associated case IDs")
    template_id: str | None = Field(None, description="Documentation template ID")
    language: str = Field("en", description="Output language")
    format: str = Field("pdf", description="Output format (pdf, docx, html)")
    include_charts: bool = Field(True, description="Include data visualizations")
    include_recommendations: bool = Field(True, description="Include clinical recommendations")


class ClinicalReport(BaseModel):
    """Clinical report model."""

    report_id: str = Field(..., description="Unique report ID")
    report_type: str = Field(..., description="Report type")
    healthcare_professional_id: str = Field(..., description="Generating professional")
    generated_at: datetime = Field(default_factory=datetime.now)
    title: str = Field(..., description="Report title")
    summary: str = Field(..., description="Executive summary")
    sections: list[dict[str, Any]] = Field(..., description="Report sections")
    recommendations: list[str] = Field(default_factory=list, description="Clinical recommendations")
    data_sources: list[str] = Field(default_factory=list, description="Data sources used")
    quality_indicators: dict[str, float] = Field(default_factory=dict, description="Report quality metrics")


class KnowledgeResource(BaseModel):
    """Knowledge management resource."""

    resource_id: str = Field(..., description="Resource identifier")
    title: str = Field(..., description="Resource title")
    category: str = Field(..., description="Resource category")
    description: str = Field(..., description="Resource description")
    content_type: str = Field(..., description="Content type (guideline, protocol, reference)")
    content_url: str | None = Field(None, description="External content URL")
    embedded_content: str | None = Field(None, description="Embedded content")
    tags: list[str] = Field(default_factory=list, description="Resource tags")
    evidence_level: str = Field(..., description="Evidence strength level")
    last_updated: datetime = Field(default_factory=datetime.now)
    source_organization: str = Field(..., description="Publishing organization")
    languages_available: list[str] = Field(default_factory=list, description="Available languages")


class ProfessionalNote(BaseModel):
    """Professional clinical note."""

    note_id: str = Field(..., description="Note identifier")
    case_id: str = Field(..., description="Associated case ID")
    healthcare_professional_id: str = Field(..., description="Author ID")
    note_type: str = Field(..., description="Note type (assessment, treatment, follow-up)")
    content: str = Field(..., description="Note content")
    structured_data: dict[str, Any] = Field(default_factory=dict, description="Structured clinical data")
    created_at: datetime = Field(default_factory=datetime.now)
    is_confidential: bool = Field(False, description="Confidentiality flag")
    signed_by: str | None = Field(None, description="Digital signature")


# ==========================================
# Documentation Generation Endpoints
# ==========================================

@router.post("/documentation/generate", response_model=ClinicalReport)
async def generate_professional_documentation(
    request: DocumentationRequest,
    current_user = Depends(get_current_healthcare_professional)
):
    """
    Generate professional documentation and reports.

    Creates comprehensive clinical reports, case summaries,
    surveillance reports, and other professional documentation.
    """
    logger.info(f"Generating {request.document_type} documentation for user {current_user.id}")

    # Generate report based on type
    if request.document_type == "case_summary":
        report = _generate_case_summary_report(request, current_user)
    elif request.document_type == "surveillance_analysis":
        report = _generate_surveillance_analysis_report(request, current_user)
    elif request.document_type == "treatment_outcome":
        report = _generate_treatment_outcome_report(request, current_user)
    elif request.document_type == "risk_assessment_summary":
        report = _generate_risk_assessment_summary(request, current_user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document type: {request.document_type}"
        )

    # Translate if needed
    if request.language != "en":
        report = _translate_report(report, request.language)

    logger.info(f"Generated report {report.report_id} successfully")
    return report


@router.get("/documentation/templates")
async def get_documentation_templates(
    category: str | None = None,
    language: str = "en",
    current_user = Depends(get_current_healthcare_professional)
):
    """
    Get available documentation templates.

    Returns standardized templates for various types of
    professional documentation and reporting.
    """
    templates = {
        "case_summary": {
            "name": "Patient Case Summary",
            "description": "Comprehensive patient case documentation",
            "sections": [
                "patient_demographics",
                "clinical_presentation",
                "diagnostic_findings",
                "treatment_plan",
                "outcomes",
                "follow_up_plan"
            ],
            "required_data": ["case_id", "patient_id"],
            "estimated_generation_time": "2-3 minutes"
        },
        "surveillance_analysis": {
            "name": "Surveillance Data Analysis",
            "description": "Epidemiological surveillance analysis report",
            "sections": [
                "surveillance_period",
                "case_trends",
                "geographic_distribution",
                "risk_factors",
                "intervention_effectiveness",
                "recommendations"
            ],
            "required_data": ["surveillance_reports", "case_data"],
            "estimated_generation_time": "5-7 minutes"
        },
        "treatment_outcome": {
            "name": "Treatment Outcome Report",
            "description": "Clinical treatment effectiveness analysis",
            "sections": [
                "treatment_protocols_used",
                "patient_outcomes",
                "adverse_events",
                "efficacy_analysis",
                "protocol_adherence",
                "recommendations"
            ],
            "required_data": ["treatment_records", "follow_up_data"],
            "estimated_generation_time": "3-4 minutes"
        },
        "risk_assessment_summary": {
            "name": "Risk Assessment Summary",
            "description": "Population and individual risk assessment overview",
            "sections": [
                "risk_methodology",
                "environmental_factors",
                "clinical_risk_factors",
                "risk_stratification",
                "intervention_recommendations",
                "monitoring_plan"
            ],
            "required_data": ["risk_assessments", "environmental_data"],
            "estimated_generation_time": "4-5 minutes"
        }
    }

    if category and category in templates:
        return {category: templates[category]}

    return templates


# ==========================================
# Knowledge Management Endpoints
# ==========================================

@router.get("/knowledge/resources", response_model=list[KnowledgeResource])
async def get_knowledge_resources(
    category: str | None = None,
    tags: list[str] | None = None,
    language: str = "en",
    evidence_level: str | None = None,
    current_user = Depends(get_current_healthcare_professional)
):
    """
    Get knowledge management resources.

    Returns clinical guidelines, treatment protocols, research
    references, and other professional knowledge resources.
    """
    logger.info(f"Fetching knowledge resources for user {current_user.id}")

    # Mock knowledge resources - in production, fetch from knowledge base
    resources = [
        KnowledgeResource(
            resource_id="who_malaria_guidelines_2023",
            title="WHO Guidelines for Malaria Treatment 2023",
            category="clinical_guidelines",
            description="Comprehensive WHO guidelines for malaria diagnosis and treatment",
            content_type="guideline",
            content_url="https://www.who.int/publications/i/item/guidelines-for-malaria",
            tags=["malaria", "treatment", "diagnosis", "WHO"],
            evidence_level="Grade A",
            source_organization="World Health Organization",
            languages_available=["en", "fr", "es", "ar"]
        ),
        KnowledgeResource(
            resource_id="antimalarial_resistance_2023",
            title="Antimalarial Drug Resistance Surveillance",
            category="surveillance_guidance",
            description="Guidelines for monitoring and reporting antimalarial drug resistance",
            content_type="protocol",
            embedded_content="""
            # Antimalarial Drug Resistance Surveillance Protocol

            ## Objectives
            - Monitor trends in antimalarial drug efficacy
            - Detect emerging resistance patterns
            - Guide treatment policy updates

            ## Methods
            1. In vivo efficacy studies
            2. Molecular markers analysis
            3. Ex vivo susceptibility testing

            ## Reporting
            - Monthly resistance monitoring reports
            - Annual resistance trend analysis
            - Immediate alert for treatment failures >10%
            """,
            tags=["drug_resistance", "surveillance", "monitoring"],
            evidence_level="Grade B",
            source_organization="WHO Global Malaria Programme",
            languages_available=["en", "fr"]
        ),
        KnowledgeResource(
            resource_id="pediatric_malaria_2023",
            title="Pediatric Malaria Management Guidelines",
            category="clinical_guidelines",
            description="Specialized guidelines for malaria management in children under 5",
            content_type="guideline",
            embedded_content="""
            # Pediatric Malaria Management

            ## Age-Specific Considerations
            - Under 6 months: Limited antimalarial options
            - 6-24 months: Higher risk of severe malaria
            - 2-5 years: Standard pediatric protocols

            ## Dosing Guidelines
            - Weight-based dosing mandatory
            - Artesunate: 3mg/kg IV for severe malaria
            - Artemether-lumefantrine: 20mg/120mg per tablet

            ## Warning Signs
            - Inability to feed/drink
            - Persistent vomiting
            - Convulsions
            - Lethargy or unconsciousness
            """,
            tags=["pediatric", "children", "dosing", "severe_malaria"],
            evidence_level="Grade A",
            source_organization="WHO/UNICEF",
            languages_available=["en", "fr", "es", "sw"]
        )
    ]

    # Filter resources based on criteria
    filtered_resources = resources

    if category:
        filtered_resources = [r for r in filtered_resources if r.category == category]

    if tags:
        filtered_resources = [
            r for r in filtered_resources
            if any(tag in r.tags for tag in tags)
        ]

    if evidence_level:
        filtered_resources = [r for r in filtered_resources if r.evidence_level == evidence_level]

    if language != "en":
        filtered_resources = [
            r for r in filtered_resources
            if language in r.languages_available
        ]

    logger.info(f"Returning {len(filtered_resources)} knowledge resources")
    return filtered_resources


@router.get("/knowledge/search")
async def search_knowledge_base(
    query: str,
    category: str | None = None,
    language: str = "en",
    limit: int = 10,
    current_user = Depends(get_current_healthcare_professional)
):
    """
    Search the knowledge base.

    Performs full-text search across clinical guidelines,
    protocols, and professional resources.
    """
    logger.info(f"Searching knowledge base for query: {query}")

    # Mock search results - in production, use full-text search
    search_results = {
        "query": query,
        "total_results": 15,
        "search_time_ms": 45,
        "results": [
            {
                "resource_id": "who_malaria_guidelines_2023",
                "title": "WHO Guidelines for Malaria Treatment 2023",
                "relevance_score": 0.95,
                "snippet": "...treatment of uncomplicated malaria should be based on rapid diagnostic tests or microscopy...",
                "highlight_terms": ["malaria", "treatment", "diagnosis"]
            },
            {
                "resource_id": "antimalarial_resistance_2023",
                "title": "Antimalarial Drug Resistance Surveillance",
                "relevance_score": 0.87,
                "snippet": "...monitoring antimalarial drug efficacy is crucial for maintaining effective treatment...",
                "highlight_terms": ["antimalarial", "resistance", "efficacy"]
            }
        ],
        "suggestions": [
            "malaria treatment protocols",
            "antimalarial drug dosing",
            "severe malaria management"
        ]
    }

    return search_results


# ==========================================
# Clinical Notes and Documentation
# ==========================================

@router.post("/notes", response_model=ProfessionalNote)
async def create_clinical_note(
    case_id: str,
    note_type: str,
    content: str,
    structured_data: dict[str, Any] = None,
    is_confidential: bool = False,
    current_user = Depends(get_current_healthcare_professional)
):
    """
    Create a professional clinical note.

    Allows healthcare professionals to document clinical
    observations, assessments, and treatment decisions.
    """
    if structured_data is None:
        structured_data = {}
    logger.info(f"Creating clinical note for case {case_id} by user {current_user.id}")

    note = ProfessionalNote(
        note_id=f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        case_id=case_id,
        healthcare_professional_id=current_user.id,
        note_type=note_type,
        content=content,
        structured_data=structured_data,
        is_confidential=is_confidential,
        signed_by=current_user.id  # Digital signature
    )

    # In production, save to secure database with audit trail
    logger.info(f"Clinical note {note.note_id} created successfully")
    return note


@router.get("/notes/{case_id}", response_model=list[ProfessionalNote])
async def get_case_notes(
    case_id: str,
    note_type: str | None = None,
    current_user = Depends(get_current_healthcare_professional)
):
    """Get all clinical notes for a case."""
    logger.info(f"Retrieving notes for case {case_id}")

    # Mock notes - in production, fetch from database with access control
    notes = [
        ProfessionalNote(
            note_id="note_20231218_143000",
            case_id=case_id,
            healthcare_professional_id=current_user.id,
            note_type="assessment",
            content="Patient presents with fever (38.5°C), headache, and chills. Rapid diagnostic test positive for P. falciparum. No signs of severe malaria.",
            structured_data={
                "vital_signs": {
                    "temperature": 38.5,
                    "blood_pressure": "120/80",
                    "heart_rate": 88
                },
                "lab_results": {
                    "rdt_result": "positive",
                    "parasite_species": "P. falciparum"
                }
            },
            created_at=datetime.now() - timedelta(hours=2)
        )
    ]

    if note_type:
        notes = [n for n in notes if n.note_type == note_type]

    return notes


# ==========================================
# Helper Functions for Documentation
# ==========================================

def _generate_case_summary_report(request: DocumentationRequest, current_user) -> ClinicalReport:
    """Generate a comprehensive case summary report."""

    return ClinicalReport(
        report_id=f"case_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        report_type="case_summary",
        healthcare_professional_id=current_user.id,
        title="Patient Case Summary Report",
        summary="Comprehensive overview of patient case including clinical presentation, diagnostic findings, treatment plan, and outcomes.",
        sections=[
            {
                "title": "Patient Demographics",
                "content": "Patient ID: P12345, Age: 34, Gender: Female, Location: Nairobi District"
            },
            {
                "title": "Clinical Presentation",
                "content": "Patient presented with 3-day history of fever, headache, and chills. No previous malaria episodes."
            },
            {
                "title": "Diagnostic Findings",
                "content": "RDT positive for P. falciparum. Microscopy confirmed with parasitemia of 15,000/µL."
            },
            {
                "title": "Treatment Plan",
                "content": "Artemether-lumefantrine 20mg/120mg, 4 tablets twice daily for 3 days."
            },
            {
                "title": "Clinical Outcomes",
                "content": "Patient recovered fully. Day 3 follow-up showed negative RDT and resolved symptoms."
            }
        ],
        recommendations=[
            "Complete full course of antimalarial treatment",
            "Return for follow-up if symptoms recur",
            "Use bed nets for prevention"
        ],
        data_sources=["clinical_examination", "laboratory_results", "treatment_records"],
        quality_indicators={
            "completeness": 0.95,
            "accuracy": 0.98,
            "timeliness": 0.92
        }
    )


def _generate_surveillance_analysis_report(request: DocumentationRequest, current_user) -> ClinicalReport:
    """Generate surveillance data analysis report."""

    return ClinicalReport(
        report_id=f"surveillance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        report_type="surveillance_analysis",
        healthcare_professional_id=current_user.id,
        title="Malaria Surveillance Analysis Report",
        summary="Epidemiological analysis of malaria surveillance data for the reporting period.",
        sections=[
            {
                "title": "Surveillance Period Overview",
                "content": "Analysis covers surveillance data from January 1 - December 31, 2023"
            },
            {
                "title": "Case Trends",
                "content": "Total cases: 1,245. Peak transmission observed in April-May (wet season)."
            },
            {
                "title": "Geographic Distribution",
                "content": "Highest incidence in rural areas (8.5 cases/1000). Urban areas: 2.1 cases/1000."
            },
            {
                "title": "Risk Factor Analysis",
                "content": "Key risk factors: proximity to water bodies, lack of bed net use, recent travel."
            }
        ],
        recommendations=[
            "Intensify vector control during peak season",
            "Improve bed net distribution in high-risk areas",
            "Strengthen case management in rural facilities"
        ],
        data_sources=["surveillance_reports", "case_investigations", "environmental_data"],
        quality_indicators={
            "data_completeness": 0.89,
            "reporting_timeliness": 0.76,
            "geographic_coverage": 0.94
        }
    )


def _generate_treatment_outcome_report(request: DocumentationRequest, current_user) -> ClinicalReport:
    """Generate treatment outcome analysis report."""

    return ClinicalReport(
        report_id=f"treatment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        report_type="treatment_outcome",
        healthcare_professional_id=current_user.id,
        title="Treatment Outcome Analysis Report",
        summary="Analysis of treatment effectiveness and clinical outcomes for managed cases.",
        sections=[
            {
                "title": "Treatment Protocols Used",
                "content": "Artemether-lumefantrine (78%), Artesunate + Doxycycline (15%), Other (7%)"
            },
            {
                "title": "Clinical Outcomes",
                "content": "Complete cure rate: 96.2%. Treatment failure rate: 1.8%. Lost to follow-up: 2.0%"
            },
            {
                "title": "Adverse Events",
                "content": "Mild GI symptoms (12%), Dizziness (5%), No severe adverse events reported"
            }
        ],
        recommendations=[
            "Continue current first-line treatment protocols",
            "Improve follow-up mechanisms to reduce loss to follow-up",
            "Monitor for emerging drug resistance"
        ],
        data_sources=["treatment_records", "follow_up_data", "lab_results"],
        quality_indicators={
            "outcome_ascertainment": 0.91,
            "follow_up_completeness": 0.85,
            "data_accuracy": 0.97
        }
    )


def _generate_risk_assessment_summary(request: DocumentationRequest, current_user) -> ClinicalReport:
    """Generate risk assessment summary report."""

    return ClinicalReport(
        report_id=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        report_type="risk_assessment_summary",
        healthcare_professional_id=current_user.id,
        title="Malaria Risk Assessment Summary",
        summary="Comprehensive risk assessment analysis for population and individual cases.",
        sections=[
            {
                "title": "Risk Assessment Methodology",
                "content": "Combined clinical and environmental risk factors using validated scoring algorithms."
            },
            {
                "title": "Environmental Risk Factors",
                "content": "High transmission season (April-June), elevated temperatures, above-average rainfall."
            },
            {
                "title": "Population Risk Stratification",
                "content": "High risk: 23%, Medium risk: 45%, Low risk: 32%"
            }
        ],
        recommendations=[
            "Focus interventions on high-risk populations",
            "Strengthen early warning systems",
            "Improve environmental surveillance"
        ],
        data_sources=["risk_assessments", "environmental_data", "population_surveys"],
        quality_indicators={
            "risk_model_accuracy": 0.88,
            "environmental_data_quality": 0.92,
            "population_coverage": 0.87
        }
    )


def _translate_report(report: ClinicalReport, target_language: str) -> ClinicalReport:
    """Translate report to target language."""
    # In production, use professional translation services
    translated_report = report.copy()

    # Translate title and summary
    translated_report.title = multi_language.translate(report.title, target_language)
    translated_report.summary = multi_language.translate(report.summary, target_language)

    # Translate sections
    for section in translated_report.sections:
        section["title"] = multi_language.translate(section["title"], target_language)
        # Note: Content translation would require more sophisticated NLP
        # For now, keep original content with language note
        section["original_language"] = "en"

    # Translate recommendations
    translated_report.recommendations = [
        multi_language.translate(rec, target_language)
        for rec in report.recommendations
    ]

    return translated_report
