"""Malaria Prediction System.

AI-powered malaria outbreak prediction using LSTM and Transformers
with environmental data from multiple African data sources.
"""

__version__ = "0.1.0"
__author__ = "Malaria Prediction Team"

from .config import Settings
from .models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
    RiskLevel,
)

__all__ = [
    "Settings",
    "__version__",
    "__author__",
    "EnvironmentalFactors",
    "GeographicLocation",
    "RiskAssessment",
    "RiskLevel",
    "MalariaPrediction",
]
