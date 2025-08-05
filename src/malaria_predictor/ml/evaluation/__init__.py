"""
Model Evaluation Module for Malaria Prediction.

This module provides comprehensive evaluation metrics and tools for assessing
malaria prediction model performance, including epidemiological metrics,
uncertainty calibration, and temporal consistency.
"""

from .metrics import ModelEvaluationMetrics

__all__ = ["ModelEvaluationMetrics"]
