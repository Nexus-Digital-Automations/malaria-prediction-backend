"""
Performance Testing and Optimization Package.

This package provides comprehensive performance testing, optimization,
and monitoring capabilities for the Malaria Prediction API.

Components:
- Load testing with Locust
- Database optimization and indexing
- Redis caching strategies
- Real-time performance monitoring
- CI/CD integration for automated testing
"""

from .cache_optimization import CacheOptimizer, get_cache_optimizer
from .database_optimization import DatabaseOptimizer
from .locust_config import USER_PROFILES, LoadTestSettings
from .monitoring_dashboard import (
    PerformanceMonitoringDashboard,
    get_monitoring_dashboard,
)
from .performance_monitor import PerformanceMonitor

__all__ = [
    "CacheOptimizer",
    "get_cache_optimizer",
    "DatabaseOptimizer",
    "LoadTestSettings",
    "USER_PROFILES",
    "PerformanceMonitoringDashboard",
    "get_monitoring_dashboard",
    "PerformanceMonitor",
]

__version__ = "1.0.0"
