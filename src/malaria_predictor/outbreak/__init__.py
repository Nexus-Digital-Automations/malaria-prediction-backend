"""
Outbreak Pattern Recognition and Epidemiological Analysis Module

This module provides comprehensive outbreak detection, pattern recognition,
and epidemiological analysis capabilities for malaria surveillance systems.

Core Components:
- Data models for outbreak events, patterns, and metrics
- Pattern recognition algorithms and clustering analysis
- Epidemiological visualization and dashboard components
- Real-time surveillance and alert integration
- WHO-compliant reporting and analysis tools

Author: AI Agent - Outbreak Pattern Recognition Specialist
Version: 1.0.0
"""

from .models import (
    OutbreakEvent,
    EpidemiologicalPattern,
    CaseCluster,
    OutbreakMetrics,
    TransmissionPattern,
    SurveillanceData
)

from .services import (
    OutbreakDetector,
    PatternAnalyzer,
    ClusterAnalyzer,
    EpidemiologicalService,
    SurveillanceService
)

from .visualization import (
    OutbreakTimelineChart,
    EpidemicCurveChart,
    GeographicClusterMap,
    TransmissionPatternChart,
    SurveillanceDashboard
)

from .widgets import (
    OutbreakAlert,
    PatternSummary,
    RiskAssessment,
    OutbreakForecast,
    OutbreakTab
)

__all__ = [
    # Models
    "OutbreakEvent",
    "EpidemiologicalPattern",
    "CaseCluster",
    "OutbreakMetrics",
    "TransmissionPattern",
    "SurveillanceData",

    # Services
    "OutbreakDetector",
    "PatternAnalyzer",
    "ClusterAnalyzer",
    "EpidemiologicalService",
    "SurveillanceService",

    # Visualization
    "OutbreakTimelineChart",
    "EpidemicCurveChart",
    "GeographicClusterMap",
    "TransmissionPatternChart",
    "SurveillanceDashboard",

    # Widgets
    "OutbreakAlert",
    "PatternSummary",
    "RiskAssessment",
    "OutbreakForecast",
    "OutbreakTab"
]