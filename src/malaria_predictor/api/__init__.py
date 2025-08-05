"""
API Package for Malaria Prediction Service.

This package provides FastAPI-based REST endpoints for real-time malaria risk prediction,
including model inference, health checks, and monitoring capabilities.
"""

from .main import app

__all__ = ["app"]
