"""
End-to-End Tests Package for Malaria Prediction Backend.

This package contains comprehensive end-to-end tests that validate complete
workflows from data ingestion to prediction delivery.
"""

# E2E test configuration
E2E_TEST_TIMEOUT = 300  # 5 minutes for complete workflows
E2E_TEST_DATA_SIZE = 100  # Smaller datasets for faster E2E tests

# Test scenarios
SCENARIOS = {
    "single_prediction": {
        "description": "Complete single location prediction workflow",
        "timeout": 60,
        "includes": ["data_fetch", "processing", "model_inference", "response"],
    },
    "batch_prediction": {
        "description": "Batch prediction workflow for multiple locations",
        "timeout": 180,
        "includes": [
            "data_fetch",
            "batch_processing",
            "parallel_inference",
            "aggregation",
        ],
    },
    "time_series_prediction": {
        "description": "Time series prediction workflow",
        "timeout": 120,
        "includes": [
            "historical_data",
            "temporal_processing",
            "sequence_inference",
            "forecasting",
        ],
    },
    "spatial_grid_prediction": {
        "description": "Spatial grid prediction workflow",
        "timeout": 240,
        "includes": [
            "grid_generation",
            "spatial_processing",
            "distributed_inference",
            "mapping",
        ],
    },
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "single_prediction_time": 2.0,  # seconds
    "batch_prediction_throughput": 10,  # predictions per second
    "memory_usage_mb": 1024,  # MB
    "database_query_time": 0.5,  # seconds
    "cache_hit_ratio": 0.8,  # 80%
}
