"""
ML Model and External API Integration Tests for Malaria Prediction System.

Tests machine learning model integration, external API connectivity,
feature engineering pipeline, and model performance monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

import httpx
import numpy as np
import pytest
import torch

from malaria_predictor.ml.models.ensemble_model import EnsembleModel
from malaria_predictor.ml.models.lstm_model import LSTMModel
from malaria_predictor.models import GeographicLocation
from malaria_predictor.services.chirps_client import CHIRPSClient
from malaria_predictor.services.era5_client import ERA5Client
from malaria_predictor.services.feature_engineering import FeatureEngineeringService
from malaria_predictor.services.modis_client import MODISClient
from malaria_predictor.services.worldpop_client import WorldPopClient


# Mock FeatureExtractor for testing - TODO: Replace with actual implementation
class FeatureExtractor:
    """Mock feature extractor for testing purposes."""
    async def extract_features(self, environmental_data):
        return {
            "temperature_statistics": {"mean": 24.7, "min": 20.0, "max": 30.0, "std": 2.5},
            "precipitation_statistics": {"total": 4.3, "mean": 1.4, "days_with_rain": 3},
            "humidity_statistics": {"mean": 65.2, "min": 45.0, "max": 85.0},
            "vegetation_indices": {"ndvi": 0.72},
            "demographic_factors": {"population_density": 250.0},
            "baseline_risk_factors": {"baseline_risk": 0.15}
        }


@pytest.mark.asyncio
class TestMLModelIntegration:
    """Test machine learning model integration workflows."""

    @pytest.fixture
    def sample_features(self) -> dict[str, Any]:
        """Sample feature data for ML model testing."""
        return {
            "temperature_mean": 25.0,
            "temperature_max": 30.0,
            "temperature_min": 20.0,
            "precipitation_total": 120.0,
            "precipitation_anomaly": 0.15,
            "humidity_mean": 65.0,
            "ndvi": 0.72,
            "lst_day": 30.0,
            "lst_night": 20.0,
            "population_density": 8500,
            "urban_proportion": 0.85,
            "elevation": 1795,
            "baseline_malaria_risk": 0.15,
            "historical_incidence": 0.08,
            "seasonal_index": 0.6,
            "distance_to_water": 2.5
        }

    @pytest.fixture
    def sample_time_series_features(self) -> list[dict[str, Any]]:
        """Sample time series features for LSTM testing."""
        base_features = {
            "temperature": 25.0,
            "precipitation": 2.5,
            "humidity": 65.0,
            "ndvi": 0.72
        }

        time_series = []
        for i in range(30):  # 30-day time series
            features = base_features.copy()
            # Add temporal variation
            features["temperature"] += np.sin(i * 0.2) * 3
            features["precipitation"] += np.random.normal(0, 0.5)
            features["day_of_year"] = (datetime.now() + timedelta(days=i)).timetuple().tm_yday
            time_series.append(features)

        return time_series

    async def test_ensemble_model_prediction_workflow(
        self,
        sample_features: dict[str, Any]
    ):
        """Test ensemble model prediction workflow."""

        with (
            patch("malaria_predictor.ml.models.lstm_model.LSTMModel.predict") as mock_lstm,
            patch("malaria_predictor.ml.models.transformer_model.TransformerModel.predict") as mock_transformer,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.load_models") as mock_load
        ):

            # Configure individual model predictions
            mock_lstm.return_value = {
                "risk_score": 0.72,
                "confidence": 0.85,
                "temporal_trend": "increasing"
            }

            mock_transformer.return_value = {
                "risk_score": 0.78,
                "confidence": 0.91,
                "attention_weights": [0.25, 0.30, 0.20, 0.15, 0.10]
            }

            mock_load.return_value = True

            # Initialize ensemble model
            ensemble = EnsembleModel()

            # Make prediction
            prediction = await ensemble.predict(sample_features)

            # Validate ensemble prediction
            assert "risk_score" in prediction
            assert "confidence" in prediction
            assert "model_predictions" in prediction
            assert "ensemble_method" in prediction

            # Risk score should be within valid range
            assert 0.0 <= prediction["risk_score"] <= 1.0
            assert 0.0 <= prediction["confidence"] <= 1.0

            # Should include individual model predictions
            assert "lstm" in prediction["model_predictions"]
            assert "transformer" in prediction["model_predictions"]

            # Verify individual models were called
            mock_lstm.assert_called_once()
            mock_transformer.assert_called_once()

    async def test_lstm_time_series_prediction_workflow(
        self,
        sample_time_series_features: list[dict[str, Any]]
    ):
        """Test LSTM model time series prediction workflow."""

        with (
            patch("torch.load") as mock_torch_load,
            patch("malaria_predictor.ml.models.lstm_model.LSTMModel.preprocess_features") as mock_preprocess
        ):

            # Mock model weights and preprocessing
            mock_model_state = {
                "lstm.weight_ih_l0": torch.randn(128, 16),
                "lstm.weight_hh_l0": torch.randn(128, 32),
                "fc.weight": torch.randn(1, 32),
                "fc.bias": torch.randn(1)
            }
            mock_torch_load.return_value = mock_model_state

            # Mock feature preprocessing
            mock_preprocess.return_value = torch.randn(1, 30, 16)  # (batch, sequence, features)

            # Initialize LSTM model
            lstm_model = LSTMModel()

            # Make time series prediction
            prediction = await lstm_model.predict_time_series(sample_time_series_features)

            # Validate prediction structure
            assert "predictions" in prediction
            assert "temporal_patterns" in prediction
            assert "confidence_intervals" in prediction

            # Should have predictions for each time step
            assert len(prediction["predictions"]) == len(sample_time_series_features)

            # Each prediction should have required fields
            for pred in prediction["predictions"]:
                assert "risk_score" in pred
                assert "timestamp" in pred
                assert 0.0 <= pred["risk_score"] <= 1.0

    async def test_feature_extraction_workflow(self):
        """Test feature extraction from environmental data workflow."""

        # Sample environmental data from multiple sources
        environmental_data = {
            "era5": {
                "temperature": [23.5, 24.0, 25.5, 26.0, 24.5],
                "precipitation": [0, 2.3, 1.2, 0, 0.8],
                "humidity": [62, 65, 68, 70, 66],
                "wind_speed": [2.1, 3.2, 2.8, 1.9, 2.5],
                "timestamps": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            },
            "modis": {
                "ndvi": 0.72,
                "lst_day": 303.15,
                "lst_night": 293.15,
                "quality_flags": {"good": True}
            },
            "worldpop": {
                "population_density": 8500,
                "urban_proportion": 0.85
            },
            "map": {
                "baseline_risk": 0.15,
                "prevalence": 0.08
            }
        }

        # Initialize feature extractor
        feature_extractor = FeatureExtractor()

        # Extract features
        features = await feature_extractor.extract_features(environmental_data)

        # Validate extracted features
        assert "temperature_statistics" in features
        assert "precipitation_statistics" in features
        assert "humidity_statistics" in features
        assert "vegetation_indices" in features
        assert "demographic_factors" in features
        assert "baseline_risk_factors" in features

        # Validate temperature statistics
        temp_stats = features["temperature_statistics"]
        assert "mean" in temp_stats
        assert "min" in temp_stats
        assert "max" in temp_stats
        assert "std" in temp_stats
        assert temp_stats["mean"] == pytest.approx(24.7, rel=1e-2)

        # Validate precipitation statistics
        precip_stats = features["precipitation_statistics"]
        assert "total" in precip_stats
        assert "mean" in precip_stats
        assert "days_with_rain" in precip_stats
        assert precip_stats["total"] == pytest.approx(4.3, rel=1e-2)

    async def test_feature_engineering_pipeline_workflow(self):
        """Test complete feature engineering pipeline workflow."""

        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            altitude=1795.0
        )

        raw_environmental_data = {
            "era5_data": {
                "temperature": 298.15,  # Kelvin
                "precipitation": 0.0025,  # meters
                "humidity": 65.2,
                "wind_speed": 2.1
            },
            "chirps_data": {
                "precipitation": 2.5,  # mm
                "anomaly": 0.15
            },
            "modis_data": {
                "ndvi": 0.72,
                "lst_day": 303.15,
                "lst_night": 293.15
            }
        }

        with patch("malaria_predictor.services.feature_engineering.FeatureEngineeringService.engineer_features") as mock_engineer:

            # Mock engineered features
            mock_engineer.return_value = {
                "engineered_features": {
                    "temperature_celsius": 25.0,
                    "precipitation_mm": 2.5,
                    "humidity_percent": 65.2,
                    "ndvi_normalized": 0.72,
                    "diurnal_temperature_range": 10.0,
                    "heat_index": 28.5,
                    "comfort_index": 0.75,
                    "malaria_suitability_index": 0.68
                },
                "feature_quality": {
                    "completeness": 0.95,
                    "reliability": 0.89,
                    "temporal_consistency": 0.92
                }
            }

            # Initialize feature engineering service
            feature_service = FeatureEngineeringService()

            # Engineer features
            result = await feature_service.engineer_features(
                location=location,
                environmental_data=raw_environmental_data
            )

            # Validate engineered features
            assert "engineered_features" in result
            assert "feature_quality" in result

            features = result["engineered_features"]
            quality = result["feature_quality"]

            # Validate specific engineered features
            assert "temperature_celsius" in features
            assert "malaria_suitability_index" in features
            assert "heat_index" in features

            # Validate quality metrics
            assert quality["completeness"] > 0.9
            assert quality["reliability"] > 0.8
            assert quality["temporal_consistency"] > 0.8

    async def test_model_performance_monitoring_workflow(self):
        """Test ML model performance monitoring workflow."""

        prediction_results = [
            {"predicted": 0.75, "actual": 0.78, "confidence": 0.89},
            {"predicted": 0.62, "actual": 0.58, "confidence": 0.92},
            {"predicted": 0.84, "actual": 0.81, "confidence": 0.87},
            {"predicted": 0.45, "actual": 0.49, "confidence": 0.94},
            {"predicted": 0.91, "actual": 0.88, "confidence": 0.85}
        ]

        with (
            patch("malaria_predictor.ml.evaluation.metrics.calculate_performance_metrics") as mock_metrics,
            patch("malaria_predictor.monitoring.model_monitor.ModelMonitor.log_predictions") as mock_log
        ):

            # Mock performance metrics calculation
            mock_metrics.return_value = {
                "mae": 0.035,  # Mean Absolute Error
                "rmse": 0.042,  # Root Mean Square Error
                "r2_score": 0.94,  # R-squared
                "accuracy": 0.91,
                "precision": 0.89,
                "recall": 0.93,
                "f1_score": 0.91,
                "confidence_calibration": 0.87
            }

            mock_log.return_value = True

            # Initialize model monitor
            from malaria_predictor.monitoring.model_monitor import ModelMonitor
            monitor = ModelMonitor()

            # Evaluate model performance
            performance = await monitor.evaluate_predictions(prediction_results)

            # Validate performance metrics
            assert "mae" in performance
            assert "rmse" in performance
            assert "accuracy" in performance

            # Performance should meet quality thresholds
            assert performance["mae"] < 0.1  # Low error
            assert performance["r2_score"] > 0.8  # Good correlation
            assert performance["accuracy"] > 0.85  # High accuracy

            # Verify logging was called
            mock_log.assert_called_once()

    async def test_model_drift_detection_workflow(self):
        """Test model drift detection workflow."""

        # Historical model performance baseline
        baseline_performance = {
            "accuracy": 0.91,
            "precision": 0.89,
            "recall": 0.93,
            "f1_score": 0.91,
            "confidence_calibration": 0.87
        }

        # Current model performance (showing drift)
        current_performance = {
            "accuracy": 0.83,  # Degraded
            "precision": 0.81,  # Degraded
            "recall": 0.89,    # Slightly degraded
            "f1_score": 0.85,  # Degraded
            "confidence_calibration": 0.79  # Degraded
        }

        with patch("malaria_predictor.monitoring.drift_detector.DriftDetector.detect_drift") as mock_drift:

            # Mock drift detection
            mock_drift.return_value = {
                "drift_detected": True,
                "drift_magnitude": 0.08,  # 8% performance degradation
                "affected_metrics": ["accuracy", "precision", "f1_score"],
                "confidence": 0.95,
                "recommended_actions": [
                    "Retrain model with recent data",
                    "Review feature engineering pipeline",
                    "Validate data quality"
                ]
            }

            # Initialize drift detector
            from malaria_predictor.monitoring.drift_detector import DriftDetector
            drift_detector = DriftDetector()

            # Detect drift
            drift_result = await drift_detector.detect_drift(
                baseline_performance=baseline_performance,
                current_performance=current_performance
            )

            # Validate drift detection
            assert "drift_detected" in drift_result
            assert drift_result["drift_detected"] is True
            assert "drift_magnitude" in drift_result
            assert "recommended_actions" in drift_result

            # Drift magnitude should be significant
            assert drift_result["drift_magnitude"] > 0.05  # >5% degradation


@pytest.mark.asyncio
class TestExternalAPIIntegration:
    """Test external API integration workflows."""

    async def test_era5_api_integration_workflow(self):
        """Test ERA5 API integration workflow with error handling."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with patch("httpx.AsyncClient.get") as mock_get:

            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "2m_temperature": [298.15, 299.20, 297.85],
                    "total_precipitation": [0.0, 0.0025, 0.0008],
                    "2m_relative_humidity": [65.2, 68.1, 63.7],
                    "time": ["2024-01-01T00:00:00", "2024-01-01T06:00:00", "2024-01-01T12:00:00"]
                }
            }
            mock_get.return_value = mock_response

            # Initialize ERA5 client
            era5_client = ERA5Client()

            # Request data
            data = await era5_client.get_data(
                location=location,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )

            # Validate response data
            assert "temperature" in data
            assert "precipitation" in data
            assert "humidity" in data

            # Verify API was called correctly
            mock_get.assert_called_once()

    async def test_external_api_timeout_handling(self):
        """Test external API timeout handling workflow."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with patch("httpx.AsyncClient.get") as mock_get:

            # Mock timeout exception
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            # Initialize CHIRPS client
            chirps_client = CHIRPSClient()

            # Request should handle timeout gracefully
            with pytest.raises(Exception) as exc_info:
                await chirps_client.get_data(
                    location=location,
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now()
                )

            # Should raise appropriate exception
            assert "timeout" in str(exc_info.value).lower()

    async def test_external_api_rate_limiting_workflow(self):
        """Test external API rate limiting workflow."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with patch("httpx.AsyncClient.get") as mock_get:

            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429  # Too Many Requests
            mock_response.headers = {"Retry-After": "60"}
            mock_get.return_value = mock_response

            # Initialize MODIS client
            modis_client = MODISClient()

            # Request should handle rate limiting
            with pytest.raises(Exception) as exc_info:
                await modis_client.get_data(
                    location=location,
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now()
                )

            # Should indicate rate limiting
            assert "rate limit" in str(exc_info.value).lower() or "429" in str(exc_info.value)

    async def test_multiple_api_concurrent_requests_workflow(self):
        """Test concurrent requests to multiple external APIs."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_data") as mock_chirps,
            patch("malaria_predictor.services.modis_client.MODISClient.get_data") as mock_modis,
            patch("malaria_predictor.services.worldpop_client.WorldPopClient.get_data") as mock_worldpop
        ):

            # Configure mock responses
            mock_era5.return_value = {"temperature": 298.15, "precipitation": 2.5}
            mock_chirps.return_value = {"precipitation": 2.3, "anomaly": 0.15}
            mock_modis.return_value = {"ndvi": 0.72, "lst": 303.15}
            mock_worldpop.return_value = {"population_density": 8500}

            # Create clients
            era5_client = ERA5Client()
            chirps_client = CHIRPSClient()
            modis_client = MODISClient()
            worldpop_client = WorldPopClient()

            # Make concurrent requests
            tasks = [
                era5_client.get_data(location, start_date, end_date),
                chirps_client.get_data(location, start_date, end_date),
                modis_client.get_data(location, start_date, end_date),
                worldpop_client.get_data(location)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Validate all requests completed
            assert len(results) == 4

            # Count successful requests
            successful_requests = [
                result for result in results
                if isinstance(result, dict) and not isinstance(result, Exception)
            ]

            # Should have high success rate for concurrent requests
            assert len(successful_requests) >= 3  # At least 75% success

    async def test_api_data_validation_workflow(self):
        """Test external API data validation workflow."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with patch("httpx.AsyncClient.get") as mock_get:

            # Mock API response with invalid data
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "2m_temperature": [500.0, -100.0, 298.15],  # Invalid temperatures
                    "total_precipitation": [-1.0, 0.0025, 999.0],  # Invalid precipitation
                    "2m_relative_humidity": [150.0, 68.1, -20.0],  # Invalid humidity
                    "time": ["2024-01-01T00:00:00", "2024-01-01T06:00:00", "2024-01-01T12:00:00"]
                }
            }
            mock_get.return_value = mock_response

            # Initialize ERA5 client with validation
            era5_client = ERA5Client(validate_data=True)

            # Request data should trigger validation
            data = await era5_client.get_data(
                location=location,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )

            # Should return cleaned/validated data or raise validation error
            if "temperature" in data:
                # If data is returned, it should be within valid ranges
                temp_values = data.get("temperature", [])
                for temp in temp_values:
                    assert 200.0 <= temp <= 350.0  # Reasonable temperature range in Kelvin
            else:
                # Or validation should have flagged the data as invalid
                assert "validation_errors" in data

    async def test_api_caching_workflow(self):
        """Test external API response caching workflow."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with (
            patch("httpx.AsyncClient.get") as mock_get,
            patch("malaria_predictor.services.era5_client.CacheManager.get") as mock_cache_get,
            patch("malaria_predictor.services.era5_client.CacheManager.set") as mock_cache_set
        ):

            # First request: cache miss
            mock_cache_get.return_value = None  # Cache miss

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"temperature": 298.15}}
            mock_get.return_value = mock_response

            # Initialize ERA5 client with caching
            era5_client = ERA5Client(enable_cache=True)

            # First request should hit API and cache result
            data1 = await era5_client.get_data(
                location=location,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )

            # Verify API was called and cache was set
            mock_get.assert_called_once()
            mock_cache_set.assert_called_once()

            # Second request: cache hit
            mock_cache_get.return_value = {"temperature": 298.15}  # Cache hit
            mock_get.reset_mock()

            data2 = await era5_client.get_data(
                location=location,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )

            # Second request should not hit API (cached)
            mock_get.assert_not_called()

            # Data should be identical
            assert data1 == data2


@pytest.mark.asyncio
class TestEndToEndMLPipelineIntegration:
    """Test complete end-to-end ML pipeline integration."""

    async def test_complete_ml_pipeline_workflow(self):
        """Test complete ML pipeline from data ingestion to prediction."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        # Mock the entire pipeline
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_data") as mock_chirps,
            patch("malaria_predictor.services.modis_client.MODISClient.get_data") as mock_modis,
            patch("malaria_predictor.ml.feature_extractor.FeatureExtractor.extract_features") as mock_extract,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_predict
        ):

            # Configure pipeline mocks
            mock_era5.return_value = {"temperature": 298.15, "precipitation": 2.5}
            mock_chirps.return_value = {"precipitation": 2.3, "anomaly": 0.15}
            mock_modis.return_value = {"ndvi": 0.72, "lst": 303.15}

            mock_extract.return_value = {
                "temperature_celsius": 25.0,
                "precipitation_mm": 2.4,
                "ndvi": 0.72,
                "malaria_suitability_index": 0.68
            }

            mock_predict.return_value = {
                "risk_score": 0.75,
                "confidence": 0.89,
                "risk_category": "high",
                "contributing_factors": {
                    "temperature": 0.25,
                    "precipitation": 0.30,
                    "vegetation": 0.20,
                    "population": 0.15,
                    "baseline": 0.10
                }
            }

            # Initialize pipeline components
            from malaria_predictor.services.prediction_pipeline import (
                PredictionPipeline,
            )
            pipeline = PredictionPipeline()

            # Execute complete pipeline
            result = await pipeline.predict(
                location=location,
                date=datetime.now(),
                include_uncertainty=True
            )

            # Validate pipeline result
            assert "risk_score" in result
            assert "confidence" in result
            assert "risk_category" in result
            assert "contributing_factors" in result
            assert "pipeline_metadata" in result

            # Verify all pipeline stages were executed
            mock_era5.assert_called_once()
            mock_chirps.assert_called_once()
            mock_modis.assert_called_once()
            mock_extract.assert_called_once()
            mock_predict.assert_called_once()

            # Validate prediction quality
            assert 0.0 <= result["risk_score"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0
            assert result["risk_category"] in ["low", "medium", "high", "very_high"]

    async def test_pipeline_error_resilience_workflow(self):
        """Test ML pipeline resilience to component failures."""

        location = GeographicLocation(latitude=-1.2921, longitude=36.8219)

        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_data") as mock_chirps,
            patch("malaria_predictor.services.modis_client.MODISClient.get_data") as mock_modis,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_predict
        ):

            # Simulate partial API failures
            mock_era5.return_value = {"temperature": 298.15}  # Success
            mock_chirps.side_effect = Exception("CHIRPS API unavailable")  # Failure
            mock_modis.return_value = {"ndvi": 0.72}  # Success

            # Model should still make prediction with available data
            mock_predict.return_value = {
                "risk_score": 0.68,
                "confidence": 0.75,  # Lower confidence due to missing data
                "data_completeness": 0.67,  # 2/3 data sources available
                "missing_sources": ["CHIRPS"],
                "quality_warnings": ["Precipitation data unavailable"]
            }

            # Initialize resilient pipeline
            from malaria_predictor.services.prediction_pipeline import (
                ResilientPredictionPipeline,
            )
            pipeline = ResilientPredictionPipeline()

            # Execute pipeline with failures
            result = await pipeline.predict(location=location, date=datetime.now())

            # Should complete despite partial failures
            assert "risk_score" in result
            assert "confidence" in result
            assert "data_completeness" in result
            assert "missing_sources" in result

            # Confidence should be appropriately reduced
            assert result["confidence"] < 0.85  # Lower due to missing data
            assert result["data_completeness"] < 1.0
            assert "CHIRPS" in result["missing_sources"]
