"""
Resource Allocation Module

Comprehensive resource allocation and optimization system for malaria healthcare management.
This module provides tools for inventory management, demand forecasting, staff scheduling,
and emergency resource mobilization.

Components:
- Resource Allocation Engine: Core optimization algorithms
- Inventory Manager: Real-time inventory tracking and management
- Demand Forecaster: Predictive analytics for resource demand
- Staff Scheduler: Multi-facility staff allocation and scheduling
- Emergency Resource Mobilizer: Emergency response resource coordination
- Budget Optimizer: Cost optimization and budget management

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

from .budget_optimizer import BudgetOptimizer
from .demand_forecaster import DemandForecaster
from .emergency_resource_mobilizer import EmergencyResourceMobilizer
from .inventory_manager import InventoryManager
from .resource_allocation_engine import ResourceAllocationEngine
from .staff_scheduler import StaffScheduler

__all__ = [
    'ResourceAllocationEngine',
    'InventoryManager',
    'DemandForecaster',
    'StaffScheduler',
    'EmergencyResourceMobilizer',
    'BudgetOptimizer'
]
