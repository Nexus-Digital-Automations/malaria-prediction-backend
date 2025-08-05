"""Database package for malaria prediction system.

This package contains database models, connection management,
and data access layers for persistent storage of environmental
and prediction data.
"""

from .models import (
    Base,
    ERA5DataPoint,
    LocationTimeSeries,
    MalariaRiskIndex,
    ProcessedClimateData,
)
from .security_models import (
    APIKey,
    AuditLog,
    IPAllowlist,
    RateLimitLog,
    RefreshToken,
    SecuritySettings,
    User,
)
from .session import get_session, init_database

__all__ = [
    "Base",
    "ERA5DataPoint",
    "ProcessedClimateData",
    "LocationTimeSeries",
    "MalariaRiskIndex",
    "User",
    "APIKey",
    "RefreshToken",
    "AuditLog",
    "SecuritySettings",
    "IPAllowlist",
    "RateLimitLog",
    "get_session",
    "init_database",
]
