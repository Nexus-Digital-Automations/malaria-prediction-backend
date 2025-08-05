"""
Locust Load Testing Suite for Malaria Prediction API.

This module implements comprehensive load testing scenarios with realistic
user behavior patterns for the malaria prediction service.
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any

import gevent
from locust import HttpUser, TaskSet, between, events, task
from locust.env import Environment

from .locust_config import (
    USER_PROFILES,
    LoadTestSettings,
    TestDataGenerator,
    UserBehaviorProfile,
)
from .performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global configuration
settings = LoadTestSettings()
test_data = TestDataGenerator(settings)
performance_monitor = PerformanceMonitor(settings)


class AuthenticatedHttpUser(HttpUser):
    """Base HTTP user with authentication capabilities."""

    abstract = True
    auth_token: str | None = None

    def on_start(self):
        """Called when user starts - authenticate and setup."""
        self.authenticate()
        performance_monitor.on_user_start()

    def on_stop(self):
        """Called when user stops - cleanup."""
        performance_monitor.on_user_stop()

    def authenticate(self) -> bool:
        """Authenticate user and get access token."""
        try:
            response = self.client.post(
                "/auth/login",
                json={
                    "username": settings.test_username,
                    "password": settings.test_password,
                },
                timeout=settings.api_timeout,
                name="auth_login",
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.client.headers.update(
                    {"Authorization": f"Bearer {self.auth_token}"}
                )
                logger.info("User authenticated successfully")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def make_authenticated_request(self, method: str, url: str, **kwargs) -> Any:
        """Make authenticated request with error handling."""
        if not self.auth_token:
            self.authenticate()

        return getattr(self.client, method.lower())(url, **kwargs)


class SinglePredictionTasks(TaskSet):
    """Task set for single location predictions."""

    @task
    def predict_single_location(self):
        """Test single location prediction endpoint."""
        location = test_data.get_random_location()
        target_date = (datetime.now() + timedelta(days=random.randint(1, 30))).date()

        payload = {
            "location": location,
            "target_date": target_date.isoformat(),
            "model_type": random.choice(["lstm", "transformer", "ensemble"]),
            "prediction_horizon": random.choice([1, 7, 14, 30]),
        }

        start_time = time.time()

        response = self.user.make_authenticated_request(
            "POST",
            "/predict/single",
            json=payload,
            timeout=settings.api_timeout,
            name="predict_single",
        )

        response_time = (time.time() - start_time) * 1000

        # Record performance metrics
        performance_monitor.record_request(
            "predict_single",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            assert "risk_score" in data
            assert "risk_level" in data
            assert 0.0 <= data["risk_score"] <= 1.0
        else:
            logger.warning(f"Single prediction failed: {response.status_code}")


class BatchPredictionTasks(TaskSet):
    """Task set for batch prediction operations."""

    @task
    def predict_batch_locations(self):
        """Test batch location prediction endpoint."""
        # Generate 5-20 locations for batch processing
        num_locations = random.randint(5, 20)
        locations = [test_data.get_random_location() for _ in range(num_locations)]
        target_date = (datetime.now() + timedelta(days=random.randint(1, 30))).date()

        payload = {
            "locations": locations,
            "target_date": target_date.isoformat(),
            "model_type": random.choice(["lstm", "transformer", "ensemble"]),
            "prediction_horizon": random.choice([1, 7, 14, 30]),
        }

        start_time = time.time()

        response = self.user.make_authenticated_request(
            "POST",
            "/predict/batch",
            json=payload,
            timeout=settings.api_timeout * 2,  # Longer timeout for batch
            name="predict_batch",
        )

        response_time = (time.time() - start_time) * 1000

        performance_monitor.record_request(
            "predict_batch",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

        if response.status_code == 200:
            data = response.json()
            assert "predictions" in data
            assert "total_locations" in data
            assert data["total_locations"] == num_locations
        else:
            logger.warning(f"Batch prediction failed: {response.status_code}")


class SpatialPredictionTasks(TaskSet):
    """Task set for spatial grid prediction operations."""

    @task
    def predict_spatial_grid(self):
        """Test spatial grid prediction endpoint."""
        bounds = test_data.get_spatial_bounds()
        target_date = (datetime.now() + timedelta(days=random.randint(1, 30))).date()

        # Use different resolutions to test various grid sizes
        resolution = random.choice([0.1, 0.2, 0.5, 1.0])

        payload = {
            "bounds": bounds,
            "resolution": resolution,
            "target_date": target_date.isoformat(),
            "model_type": random.choice(["lstm", "transformer", "ensemble"]),
            "prediction_horizon": random.choice([1, 7, 14, 30]),
        }

        start_time = time.time()

        response = self.user.make_authenticated_request(
            "POST",
            "/predict/spatial",
            json=payload,
            timeout=settings.api_timeout * 3,  # Longer timeout for spatial
            name="predict_spatial",
        )

        response_time = (time.time() - start_time) * 1000

        performance_monitor.record_request(
            "predict_spatial",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

        if response.status_code == 200:
            data = response.json()
            assert "grid_info" in data
            assert "predictions" in data
            assert "metadata" in data
        else:
            logger.warning(f"Spatial prediction failed: {response.status_code}")


class TimeSeriesPredictionTasks(TaskSet):
    """Task set for time series prediction operations."""

    @task
    def predict_time_series(self):
        """Test time series prediction endpoint."""
        location = test_data.get_random_location()
        date_range = test_data.get_random_date_range()

        payload = {
            "location": location,
            "start_date": date_range["start_date"],
            "end_date": date_range["end_date"],
            "model_type": random.choice(["lstm", "transformer", "ensemble"]),
        }

        start_time = time.time()

        response = self.user.make_authenticated_request(
            "POST",
            "/predict/time-series",
            json=payload,
            timeout=settings.api_timeout * 2,  # Longer timeout for time series
            name="predict_time_series",
        )

        response_time = (time.time() - start_time) * 1000

        performance_monitor.record_request(
            "predict_time_series",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

        if response.status_code == 200:
            data = response.json()
            assert "time_series" in data
            assert "summary_statistics" in data
            assert len(data["time_series"]) > 0
        else:
            logger.warning(f"Time series prediction failed: {response.status_code}")


class HealthCheckTasks(TaskSet):
    """Task set for health check and monitoring operations."""

    @task(10)
    def health_check(self):
        """Test basic health check endpoint."""
        start_time = time.time()

        response = self.user.client.get(
            "/health", timeout=settings.api_timeout, name="health_check"
        )

        response_time = (time.time() - start_time) * 1000

        performance_monitor.record_request(
            "health_check",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

    @task(5)
    def model_health(self):
        """Test model health endpoint."""
        start_time = time.time()

        response = self.user.client.get(
            "/health/models", timeout=settings.api_timeout, name="health_models"
        )

        response_time = (time.time() - start_time) * 1000

        performance_monitor.record_request(
            "health_models",
            response_time,
            response.status_code == 200,
            len(response.content) if response.content else 0,
        )

    @task(2)
    def api_info(self):
        """Test API info endpoints."""
        for endpoint in ["/", "/info"]:
            start_time = time.time()

            response = self.user.client.get(
                endpoint,
                timeout=settings.api_timeout,
                name=f"api_info_{endpoint.replace('/', 'root' if endpoint == '/' else 'info')}",
            )

            response_time = (time.time() - start_time) * 1000

            performance_monitor.record_request(
                f"api_info_{endpoint.replace('/', 'root' if endpoint == '/' else 'info')}",
                response_time,
                response.status_code == 200,
                len(response.content) if response.content else 0,
            )


# Dynamic user classes based on behavior profiles
def create_user_class(profile: UserBehaviorProfile) -> type:
    """Dynamically create user class based on behavior profile."""

    class DynamicUser(AuthenticatedHttpUser):
        wait_time = between(profile.wait_time_min, profile.wait_time_max)
        weight = profile.weight

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.profile = profile

        tasks = {}

        # Add tasks based on profile weights
        if "single_prediction" in profile.tasks:
            tasks[SinglePredictionTasks] = profile.tasks["single_prediction"]

        if "batch_analysis" in profile.tasks:
            tasks[BatchPredictionTasks] = profile.tasks["batch_analysis"]

        if "spatial_grid_analysis" in profile.tasks:
            tasks[SpatialPredictionTasks] = profile.tasks["spatial_grid_analysis"]

        if "time_series_analysis" in profile.tasks:
            tasks[TimeSeriesPredictionTasks] = profile.tasks["time_series_analysis"]

        if "health_check" in profile.tasks or "api_info" in profile.tasks:
            health_weight = profile.tasks.get("health_check", 0) + profile.tasks.get(
                "api_info", 0
            )
            tasks[HealthCheckTasks] = health_weight

    DynamicUser.__name__ = f"{profile.name.title()}User"
    return DynamicUser


# Create user classes from profiles
ResearchAnalystUser = create_user_class(USER_PROFILES[0])
DashboardUser = create_user_class(USER_PROFILES[1])
BulkProcessorUser = create_user_class(USER_PROFILES[2])
ApiExplorerUser = create_user_class(USER_PROFILES[3])


# Event handlers for performance monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Handle request completion events."""
    success = exception is None
    performance_monitor.record_request(name, response_time, success, response_length)


@events.test_start.add_listener
def on_test_start(environment: Environment, **kwargs):
    """Handle test start event."""
    logger.info("🚀 Starting load test...")
    performance_monitor.start_monitoring()


@events.test_stop.add_listener
def on_test_stop(environment: Environment, **kwargs):
    """Handle test stop event."""
    logger.info("🛑 Load test completed")
    performance_monitor.stop_monitoring()
    performance_monitor.generate_report()


@events.init.add_listener
def on_locust_init(environment: Environment, **kwargs):
    """Initialize performance monitoring when Locust starts."""
    if not isinstance(environment.runner, gevent.spawn):
        # Initialize monitoring systems
        performance_monitor.initialize()
        logger.info("Performance monitoring initialized")
