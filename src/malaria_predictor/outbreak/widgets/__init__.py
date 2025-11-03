"""
Outbreak Analysis Widgets Module

Interactive widgets for outbreak analysis including alerts, summaries,
risk assessment, and forecasting components.

Author: AI Agent - Outbreak Pattern Recognition Specialist
"""

from .alerts import OutbreakAlert
from .assessment import RiskAssessment  # type: ignore[import-not-found]
from .dashboard import OutbreakTab  # type: ignore[import-not-found]
from .forecasting import OutbreakForecast  # type: ignore[import-not-found]
from .summaries import PatternSummary  # type: ignore[import-not-found]

__all__ = [
    "OutbreakAlert",
    "PatternSummary",
    "RiskAssessment",
    "OutbreakForecast",
    "OutbreakTab"
]
