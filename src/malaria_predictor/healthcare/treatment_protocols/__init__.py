"""
Treatment Protocols Module

WHO-based treatment protocol recommendation engine with decision support algorithms,
drug resistance pattern analysis, and patient-specific treatment recommendations.

This module implements evidence-based malaria treatment protocols following WHO guidelines
with advanced decision support capabilities for healthcare professionals.

Components:
- WHO Guidelines Engine: Implementation of official WHO treatment protocols
- Treatment Protocol Engine: Core decision support system
- Drug Resistance Analyzer: Pattern analysis and resistance mapping
- Patient-Specific Recommender: Personalized treatment recommendations
- Treatment Effectiveness Tracker: Outcome monitoring and feedback systems

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

from .drug_resistance_analyzer import DrugResistanceAnalyzer
from .patient_specific_recommender import PatientSpecificRecommender
from .treatment_effectiveness_tracker import TreatmentEffectivenessTracker
from .treatment_protocol_engine import TreatmentProtocolEngine
from .who_guidelines_engine import WHOGuidelinesEngine

__all__ = [
    'WHOGuidelinesEngine',
    'TreatmentProtocolEngine',
    'DrugResistanceAnalyzer',
    'PatientSpecificRecommender',
    'TreatmentEffectivenessTracker'
]
