"""
Test Fixtures Package for Malaria Prediction Backend Tests.

This package contains test data fixtures, factory functions,
and utilities for creating realistic test datasets.
"""

from pathlib import Path

# Test fixture directories
FIXTURES_DIR = Path(__file__).parent
DATA_FIXTURES_DIR = FIXTURES_DIR / "data"
MODEL_FIXTURES_DIR = FIXTURES_DIR / "models"
OUTPUT_FIXTURES_DIR = FIXTURES_DIR / "outputs"

# Create directories if they don't exist
DATA_FIXTURES_DIR.mkdir(exist_ok=True)
MODEL_FIXTURES_DIR.mkdir(exist_ok=True)
OUTPUT_FIXTURES_DIR.mkdir(exist_ok=True)

# Test data categories
DATA_CATEGORIES = {
    "environmental": {
        "era5": "ERA5 climate data fixtures",
        "chirps": "CHIRPS precipitation data fixtures",
        "modis": "MODIS vegetation and temperature fixtures",
        "worldpop": "WorldPop population data fixtures",
        "map": "Malaria Atlas Project data fixtures",
    },
    "models": {
        "lstm": "LSTM model fixtures and weights",
        "transformer": "Transformer model fixtures and weights",
        "ensemble": "Ensemble model fixtures and configurations",
    },
    "predictions": {
        "single": "Single location prediction fixtures",
        "batch": "Batch prediction fixtures",
        "time_series": "Time series prediction fixtures",
        "spatial": "Spatial grid prediction fixtures",
    },
}

# Test locations with known characteristics
TEST_LOCATIONS = {
    "nairobi": {
        "name": "Nairobi, Kenya",
        "latitude": -1.286389,
        "longitude": 36.817222,
        "characteristics": "High altitude, urban, moderate malaria risk",
        "expected_risk_range": (0.3, 0.7),
    },
    "lagos": {
        "name": "Lagos, Nigeria",
        "latitude": 6.5244,
        "longitude": 3.3792,
        "characteristics": "Coastal, urban, high malaria risk",
        "expected_risk_range": (0.6, 0.9),
    },
    "kinshasa": {
        "name": "Kinshasa, DRC",
        "latitude": -4.4419,
        "longitude": 15.2663,
        "characteristics": "Tropical, urban, very high malaria risk",
        "expected_risk_range": (0.7, 0.95),
    },
    "cape_town": {
        "name": "Cape Town, South Africa",
        "latitude": -33.9249,
        "longitude": 18.4241,
        "characteristics": "Mediterranean climate, low malaria risk",
        "expected_risk_range": (0.05, 0.25),
    },
    "addis_ababa": {
        "name": "Addis Ababa, Ethiopia",
        "latitude": 9.005401,
        "longitude": 38.763611,
        "characteristics": "High altitude, moderate climate, low-moderate risk",
        "expected_risk_range": (0.2, 0.5),
    },
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "single_prediction_time": 2.0,  # seconds
    "batch_prediction_throughput": 10,  # predictions per second
    "database_query_time": 0.5,  # seconds
    "cache_hit_ratio": 0.8,  # minimum 80%
    "memory_usage_mb": 1024,  # MB
    "model_inference_time": 0.1,  # seconds
}
