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
    - BackupOrchestrator: Manages backup operations
    - DataCorruptionDetector: Detects and handles data corruption
    - FailoverOrchestrator: Manages system failover
    - DisasterRecoveryTester: Tests DR procedures
    - DRMonitoringIntegration: Integrates with monitoring systems
    - DRScheduler: Schedules DR operations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backup_orchestrator import BackupOrchestrator
    from .data_corruption_detector import DataCorruptionDetector
    from .disaster_recovery_tester import DisasterRecoveryTester
    from .dr_monitoring_integration import DRMonitoringIntegration
    from .dr_scheduler import DRScheduler
    from .failover_orchestrator import FailoverOrchestrator

__all__ = [
    "BackupOrchestrator",
    "DataCorruptionDetector",
    "DisasterRecoveryTester",
    "DRMonitoringIntegration",
    "DRScheduler",
    "FailoverOrchestrator",
]
