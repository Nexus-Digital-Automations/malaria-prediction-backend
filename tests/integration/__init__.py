"""
Integration Tests Package for Malaria Prediction Backend.

This package contains comprehensive integration tests that validate the system
components working together, including database, cache, external APIs, and ML models.
"""

# Integration test configuration
INTEGRATION_TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
INTEGRATION_TEST_REDIS_URL = "redis://localhost:6380/0"

# Test data paths
TEST_DATA_DIR = "tests/fixtures/data"
TEST_MODEL_DIR = "tests/fixtures/models"
TEST_OUTPUT_DIR = "tests/output"

# External API mock endpoints
MOCK_ERA5_ENDPOINT = "http://localhost:9001/era5"
MOCK_CHIRPS_ENDPOINT = "http://localhost:9002/chirps"
MOCK_MODIS_ENDPOINT = "http://localhost:9003/modis"
MOCK_WORLDPOP_ENDPOINT = "http://localhost:9004/worldpop"
MOCK_MAP_ENDPOINT = "http://localhost:9005/map"
