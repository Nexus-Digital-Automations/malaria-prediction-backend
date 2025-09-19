"""
Healthcare Analytics Module

Comprehensive analytics and reporting system for healthcare management
with treatment outcome analysis, resource utilization metrics, and
management dashboards for malaria healthcare systems.

Components:
- Healthcare Analytics: Core analytics engine
- Treatment Outcome Analyzer: Clinical outcome analysis
- Resource Utilization Analyzer: Resource efficiency metrics
- Cost Effectiveness Analyzer: Economic analysis
- Management Dashboard: Executive reporting interface

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

from .healthcare_analytics import HealthcareAnalytics
from .treatment_outcome_analyzer import TreatmentOutcomeAnalyzer
from .resource_utilization_analyzer import ResourceUtilizationAnalyzer
from .cost_effectiveness_analyzer import CostEffectivenessAnalyzer
from .management_dashboard import ManagementDashboard

__all__ = [
    'HealthcareAnalytics',
    'TreatmentOutcomeAnalyzer',
    'ResourceUtilizationAnalyzer',
    'CostEffectivenessAnalyzer',
    'ManagementDashboard'
]