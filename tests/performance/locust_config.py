"""
Locust Configuration for Malaria Prediction API Load Testing.

This module provides comprehensive configuration settings for load testing
the malaria prediction API with realistic user behavior patterns.
"""

from dataclasses import dataclass

from pydantic import BaseSettings


class LoadTestSettings(BaseSettings):
    """Configuration settings for load testing environment."""

    # Target API settings
    api_host: str = "http://localhost:8000"
    api_timeout: float = 30.0

    # Authentication settings
    test_username: str = "test_user"
    test_password: str = "test_password"
    auth_endpoint: str = "/auth/login"

    # Load test parameters
    min_wait: int = 1000  # ms
    max_wait: int = 5000  # ms
    spawn_rate: int = 10  # users per second

    # Performance targets
    target_p95_response_time: float = 2000  # ms
    target_throughput: int = 100  # requests per second
    max_error_rate: float = 0.01  # 1%

    # Test data bounds
    test_bounds_south: float = -10.0
    test_bounds_north: float = 10.0
    test_bounds_west: float = -10.0
    test_bounds_east: float = 10.0

    # Database connection for monitoring
    database_url: str | None = None
    redis_url: str | None = None

    class Config:
        env_prefix = "LOAD_TEST_"
        case_sensitive = False


@dataclass
class UserBehaviorProfile:
    """Defines realistic user behavior patterns for load testing."""

    name: str
    weight: int  # Relative frequency of this behavior
    tasks: dict[str, int]  # Task name -> weight mapping
    wait_time_min: int  # ms
    wait_time_max: int  # ms
    description: str


# Realistic user behavior profiles based on typical API usage patterns
USER_PROFILES = [
    UserBehaviorProfile(
        name="research_analyst",
        weight=40,
        tasks={
            "single_prediction": 50,
            "time_series_analysis": 30,
            "spatial_grid_analysis": 15,
            "batch_analysis": 5,
        },
        wait_time_min=2000,
        wait_time_max=8000,
        description="Researchers analyzing specific locations and patterns",
    ),
    UserBehaviorProfile(
        name="dashboard_user",
        weight=35,
        tasks={"single_prediction": 70, "health_check": 20, "batch_analysis": 10},
        wait_time_min=1000,
        wait_time_max=3000,
        description="Dashboard users making frequent quick queries",
    ),
    UserBehaviorProfile(
        name="bulk_processor",
        weight=15,
        tasks={
            "batch_analysis": 60,
            "spatial_grid_analysis": 30,
            "single_prediction": 10,
        },
        wait_time_min=5000,
        wait_time_max=15000,
        description="Automated systems processing large datasets",
    ),
    UserBehaviorProfile(
        name="api_explorer",
        weight=10,
        tasks={
            "health_check": 30,
            "single_prediction": 25,
            "api_info": 20,
            "time_series_analysis": 15,
            "spatial_grid_analysis": 10,
        },
        wait_time_min=500,
        wait_time_max=2000,
        description="New users exploring API capabilities",
    ),
]


# Realistic test data generators
class TestDataGenerator:
    """Generates realistic test data for load testing scenarios."""

    def __init__(self, settings: LoadTestSettings):
        self.settings = settings
        self.locations = self._generate_test_locations()
        self.date_ranges = self._generate_date_ranges()

    def _generate_test_locations(self) -> list[dict[str, float]]:
        """Generate realistic geographic locations for testing."""
        import random

        locations = []

        # Add major African cities (realistic malaria prediction targets)
        major_cities = [
            {"latitude": -1.2921, "longitude": 36.8219},  # Nairobi, Kenya
            {"latitude": 6.5244, "longitude": 3.3792},  # Lagos, Nigeria
            {"latitude": -26.2041, "longitude": 28.0473},  # Johannesburg, SA
            {"latitude": 9.0579, "longitude": 7.4951},  # Abuja, Nigeria
            {"latitude": -15.3875, "longitude": 28.3228},  # Lusaka, Zambia
            {"latitude": 5.6037, "longitude": -0.1870},  # Accra, Ghana
            {"latitude": -17.8312, "longitude": 31.0472},  # Harare, Zimbabwe
            {"latitude": 15.5007, "longitude": 32.5599},  # Khartoum, Sudan
        ]
        locations.extend(major_cities)

        # Add random rural locations (also realistic for malaria risk)
        for _ in range(50):
            lat = random.uniform(
                self.settings.test_bounds_south, self.settings.test_bounds_north
            )
            lon = random.uniform(
                self.settings.test_bounds_west, self.settings.test_bounds_east
            )
            locations.append({"latitude": lat, "longitude": lon})

        return locations

    def _generate_date_ranges(self) -> list[dict[str, str]]:
        """Generate realistic date ranges for time series testing."""
        import random
        from datetime import datetime, timedelta

        date_ranges = []
        base_date = datetime.now()

        # Common analysis periods
        periods = [
            7,  # Weekly analysis
            30,  # Monthly analysis
            90,  # Quarterly analysis
            180,  # Semi-annual analysis
        ]

        for period in periods:
            for _ in range(5):  # 5 ranges per period
                start_offset = random.randint(0, 365)
                start_date = base_date - timedelta(days=start_offset)
                end_date = start_date + timedelta(days=period)

                date_ranges.append(
                    {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    }
                )

        return date_ranges

    def get_random_location(self) -> dict[str, float]:
        """Get a random test location."""
        import random

        return random.choice(self.locations)

    def get_random_date_range(self) -> dict[str, str]:
        """Get a random date range for time series testing."""
        import random

        return random.choice(self.date_ranges)

    def get_spatial_bounds(self) -> dict[str, float]:
        """Get realistic spatial bounds for grid testing."""
        import random

        # Generate smaller bounds for realistic grid testing
        center_lat = random.uniform(-20, 20)  # Focus on African region
        center_lon = random.uniform(-20, 50)

        # Create 2-5 degree bounds (reasonable for malaria analysis)
        size = random.uniform(1.0, 3.0)

        return {
            "south": center_lat - size,
            "north": center_lat + size,
            "west": center_lon - size,
            "east": center_lon + size,
        }


# Performance monitoring configuration
PERFORMANCE_METRICS = {
    "response_time_percentiles": [50, 75, 90, 95, 99],
    "error_rate_threshold": 0.01,  # 1%
    "throughput_target": 100,  # RPS
    "memory_threshold_mb": 1024,  # 1GB
    "cpu_threshold_percent": 80,  # 80%
    "database_connection_threshold": 50,
    "redis_memory_threshold_mb": 512,
}

# Load test scenarios configuration
LOAD_TEST_SCENARIOS = {
    "smoke_test": {
        "users": 5,
        "spawn_rate": 1,
        "duration": "2m",
        "description": "Basic functionality verification",
    },
    "load_test": {
        "users": 50,
        "spawn_rate": 10,
        "duration": "10m",
        "description": "Normal load conditions",
    },
    "stress_test": {
        "users": 200,
        "spawn_rate": 20,
        "duration": "15m",
        "description": "High load stress testing",
    },
    "spike_test": {
        "users": 500,
        "spawn_rate": 50,
        "duration": "5m",
        "description": "Sudden traffic spike simulation",
    },
    "endurance_test": {
        "users": 100,
        "spawn_rate": 10,
        "duration": "60m",
        "description": "Long-duration stability testing",
    },
}
