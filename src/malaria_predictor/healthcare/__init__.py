"""
Healthcare Tools Module

Comprehensive healthcare professional tools for malaria prediction and treatment
including WHO-based treatment protocols, resource allocation optimization,
and clinical decision support systems.

This module provides:
- Treatment protocol recommendation engines
- Resource allocation planning and optimization
- Staff scheduling and coordination
- Inventory management and demand forecasting
- Clinical decision support algorithms
- Treatment effectiveness tracking
- Emergency response coordination

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

from .analytics import (
    CostEffectivenessAnalyzer,
    HealthcareAnalytics,
    ManagementDashboard,
    ResourceUtilizationAnalyzer,
    TreatmentOutcomeAnalyzer,
)
from .resource_allocation import (
    BudgetOptimizer,
    DemandForecaster,
    EmergencyResourceMobilizer,
    InventoryManager,
    ResourceAllocationEngine,
    StaffScheduler,
)
from .treatment_protocols import (
    DrugResistanceAnalyzer,
    PatientSpecificRecommender,
    TreatmentEffectivenessTracker,
    TreatmentProtocolEngine,
    WHOGuidelinesEngine,
)

__all__ = [
    # Treatment Protocols
    'TreatmentProtocolEngine',
    'WHOGuidelinesEngine',
    'DrugResistanceAnalyzer',
    'PatientSpecificRecommender',
    'TreatmentEffectivenessTracker',

    # Resource Allocation
    'ResourceAllocationEngine',
    'InventoryManager',
    'DemandForecaster',
    'StaffScheduler',
    'EmergencyResourceMobilizer',
    'BudgetOptimizer',

    # Analytics
    'HealthcareAnalytics',
    'TreatmentOutcomeAnalyzer',
    'ResourceUtilizationAnalyzer',
    'CostEffectivenessAnalyzer',
    'ManagementDashboard'
]

__version__ = "1.0.0"
__author__ = "Claude Healthcare Tools Agent"
__description__ = "Comprehensive healthcare professional tools for malaria prediction and treatment"
