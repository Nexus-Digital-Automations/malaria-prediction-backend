"""
Disaster Recovery Module for Malaria Prediction Backend.

This module provides comprehensive disaster recovery capabilities including:
- Backup orchestration
- Data corruption detection
- Failover orchestration
- Disaster recovery testing
- DR monitoring integration
- DR scheduling

Components:
    - DisasterRecoveryOrchestrator: Manages backup operations
    - DataCorruptionMonitor: Detects and handles data corruption
    - FailoverOrchestrator: Manages system failover
    - DisasterRecoveryTester: Tests DR procedures
    - DRMonitoringService: Integrates with monitoring systems
    - DRScheduler: Schedules DR operations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backup_orchestrator import DisasterRecoveryOrchestrator
    from .data_corruption_detector import DataCorruptionMonitor
    from .disaster_recovery_tester import DisasterRecoveryTester
    from .dr_monitoring_integration import DRMonitoringService
    from .dr_scheduler import DRScheduler
    from .failover_orchestrator import FailoverOrchestrator

__all__ = [
    "DisasterRecoveryOrchestrator",
    "DataCorruptionMonitor",
    "DisasterRecoveryTester",
    "DRMonitoringService",
    "DRScheduler",
    "FailoverOrchestrator",
]
