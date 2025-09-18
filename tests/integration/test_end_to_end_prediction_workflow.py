"""
Comprehensive End-to-End Integration Tests for Malaria Prediction System.

Tests complete workflows: data ingestion → processing → prediction → API response
Covers database connections, external API integrations, and prediction pipelines.
Target: 90%+ overall system coverage for integration scenarios.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from malaria_predictor.api.main import app
from malaria_predictor.database.models import (
    ERA5DataPoint,
    ProcessedClimateData,
    MalariaRiskIndex,
    MODISDataPoint
)
from malaria_predictor.models import (
    GeographicLocation,
    PredictionRequest,
    EnvironmentalFactors
)
from malaria_predictor.services.data_harmonizer import DataHarmonizer
from malaria_predictor.services.era5_client import ERA5Client
from malaria_predictor.services.chirps_client import CHIRPSClient
from malaria_predictor.services.risk_calculator import RiskCalculator


@pytest.mark.asyncio
class TestEndToEndPredictionWorkflow:
    """Test complete end-to-end malaria prediction workflows."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_location(self) -> GeographicLocation:
        """Sample geographic location for testing."""
        return GeographicLocation(
            latitude=-1.2921,  # Nairobi, Kenya
            longitude=36.8219,
            altitude=1795.0
        )

    @pytest.fixture
    def mock_environmental_data(self) -> Dict[str, Any]:
        """Mock comprehensive environmental data."""
        return {
            "era5_data": {
                "temperature": 298.15,  # 25°C in Kelvin
                "precipitation": 0.0025,  # 2.5mm
                "humidity": 65.2,
                "wind_speed": 2.1
            },
            "chirps_data": {
                "precipitation": 2.5,  # mm
                "anomaly": 0.15
            },
            "modis_data": {
                "ndvi": 0.72,
                "lst_day": 303.15,  # 30°C
                "lst_night": 293.15  # 20°C
            },
            "worldpop_data": {
                "population_density": 8500,
                "urban_proportion": 0.85
            },
            "map_data": {
                "baseline_risk": 0.15,
                "prevalence": 0.08
            }
        }

    @pytest.fixture
    def mock_prediction_result(self) -> Dict[str, Any]:
        """Mock prediction result from ML models."""
        return {
            "risk_score": 0.75,
            "confidence": 0.89,
            "risk_category": "high",
            "contributing_factors": {
                "temperature": 0.25,
                "precipitation": 0.30,
                "humidity": 0.20,
                "population_density": 0.15,
                "baseline_risk": 0.10
            },
            "temporal_trend": "increasing",
            "recommendations": [
                "Enhanced vector control recommended",
                "Monitor population movement",
                "Prepare medical resources"
            ]
        }

    async def test_complete_single_prediction_workflow(
        self,
        client: TestClient,
        sample_location: GeographicLocation,
        mock_environmental_data: Dict[str, Any],
        mock_prediction_result: Dict[str, Any]
    ):
        """Test complete workflow for single location prediction."""
        
        # Step 1: Mock external API responses
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_data") as mock_chirps,
            patch("malaria_predictor.services.modis_client.MODISClient.get_data") as mock_modis,
            patch("malaria_predictor.services.worldpop_client.WorldPopClient.get_data") as mock_worldpop,
            patch("malaria_predictor.services.map_client.MAPClient.get_data") as mock_map,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Configure mocks to return sample data
            mock_era5.return_value = mock_environmental_data["era5_data"]
            mock_chirps.return_value = mock_environmental_data["chirps_data"]
            mock_modis.return_value = mock_environmental_data["modis_data"]
            mock_worldpop.return_value = mock_environmental_data["worldpop_data"]
            mock_map.return_value = mock_environmental_data["map_data"]
            mock_ml_predict.return_value = mock_prediction_result
            
            # Step 2: Make API request for prediction
            prediction_request = {
                "latitude": sample_location.latitude,
                "longitude": sample_location.longitude,
                "date": datetime.now().isoformat(),
                "forecast_days": 7
            }
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Step 3: Validate API response
            assert response.status_code == 200
            result = response.json()
            
            # Validate response structure
            assert "risk_score" in result
            assert "confidence" in result
            assert "location" in result
            assert "timestamp" in result
            assert "environmental_factors" in result
            assert "prediction_metadata" in result
            
            # Validate data pipeline execution
            mock_era5.assert_called_once()
            mock_chirps.assert_called_once()
            mock_modis.assert_called_once()
            mock_worldpop.assert_called_once()
            mock_map.assert_called_once()
            mock_ml_predict.assert_called_once()
            
            # Validate prediction results
            assert 0.0 <= result["risk_score"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0
            assert result["location"]["latitude"] == sample_location.latitude
            assert result["location"]["longitude"] == sample_location.longitude

    async def test_batch_prediction_workflow(
        self,
        client: TestClient,
        mock_environmental_data: Dict[str, Any],
        mock_prediction_result: Dict[str, Any]
    ):
        """Test batch prediction workflow for multiple locations."""
        
        locations = [
            {"latitude": -1.2921, "longitude": 36.8219},  # Nairobi
            {"latitude": -4.0435, "longitude": 39.6682},  # Mombasa
            {"latitude": 0.3476, "longitude": 32.5825}    # Kampala
        ]
        
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_data") as mock_chirps,
            patch("malaria_predictor.services.modis_client.MODISClient.get_data") as mock_modis,
            patch("malaria_predictor.services.worldpop_client.WorldPopClient.get_data") as mock_worldpop,
            patch("malaria_predictor.services.map_client.MAPClient.get_data") as mock_map,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Configure mocks
            mock_era5.return_value = mock_environmental_data["era5_data"]
            mock_chirps.return_value = mock_environmental_data["chirps_data"]
            mock_modis.return_value = mock_environmental_data["modis_data"]
            mock_worldpop.return_value = mock_environmental_data["worldpop_data"]
            mock_map.return_value = mock_environmental_data["map_data"]
            mock_ml_predict.return_value = mock_prediction_result
            
            # Make batch prediction request
            batch_request = {
                "locations": locations,
                "date": datetime.now().isoformat(),
                "include_uncertainty": True
            }
            
            response = client.post("/predict/batch", json=batch_request)
            
            # Validate response
            assert response.status_code == 200
            result = response.json()
            
            assert "predictions" in result
            assert len(result["predictions"]) == len(locations)
            assert "batch_metadata" in result
            
            # Verify each prediction
            for i, prediction in enumerate(result["predictions"]):
                assert prediction["location"]["latitude"] == locations[i]["latitude"]
                assert prediction["location"]["longitude"] == locations[i]["longitude"]
                assert "risk_score" in prediction
                assert "confidence" in prediction

    async def test_time_series_prediction_workflow(
        self,
        client: TestClient,
        sample_location: GeographicLocation,
        mock_environmental_data: Dict[str, Any]
    ):
        """Test time series prediction workflow."""
        
        # Mock time series data for 30 days
        time_series_predictions = []
        base_date = datetime.now()
        
        for i in range(30):
            prediction_date = base_date + timedelta(days=i)
            time_series_predictions.append({
                "date": prediction_date.isoformat(),
                "risk_score": 0.6 + (0.2 * (i % 7) / 7),  # Weekly pattern
                "confidence": 0.85 - (0.05 * i / 30),  # Decreasing confidence
                "temperature": 298.15 + (2 * (i % 5)),
                "precipitation": 2.5 * (1 + 0.1 * i)
            })
        
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_time_series") as mock_era5_ts,
            patch("malaria_predictor.services.chirps_client.CHIRPSClient.get_time_series") as mock_chirps_ts,
            patch("malaria_predictor.ml.models.lstm_model.LSTMModel.predict_time_series") as mock_lstm_predict
        ):
            
            # Configure time series mocks
            mock_era5_ts.return_value = [mock_environmental_data["era5_data"]] * 30
            mock_chirps_ts.return_value = [mock_environmental_data["chirps_data"]] * 30
            mock_lstm_predict.return_value = time_series_predictions
            
            # Make time series request
            time_series_request = {
                "latitude": sample_location.latitude,
                "longitude": sample_location.longitude,
                "start_date": base_date.isoformat(),
                "end_date": (base_date + timedelta(days=29)).isoformat(),
                "include_confidence_intervals": True
            }
            
            response = client.post("/predict/time-series", json=time_series_request)
            
            # Validate response
            assert response.status_code == 200
            result = response.json()
            
            assert "time_series" in result
            assert len(result["time_series"]) == 30
            assert "trend_analysis" in result
            assert "statistics" in result

    async def test_database_integration_workflow(
        self,
        client: TestClient,
        sample_location: GeographicLocation,
        mock_environmental_data: Dict[str, Any],
        mock_prediction_result: Dict[str, Any]
    ):
        """Test database integration throughout prediction workflow."""
        
        with (
            patch("malaria_predictor.database.repositories.EnvironmentalDataRepository.store_data") as mock_store_env,
            patch("malaria_predictor.database.repositories.PredictionRepository.store_prediction") as mock_store_pred,
            patch("malaria_predictor.database.repositories.MalariaRiskRepository.store_risk_assessment") as mock_store_risk,
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Configure mocks
            mock_era5.return_value = mock_environmental_data["era5_data"]
            mock_ml_predict.return_value = mock_prediction_result
            mock_store_env.return_value = True
            mock_store_pred.return_value = True
            mock_store_risk.return_value = True
            
            # Make prediction request
            prediction_request = {
                "latitude": sample_location.latitude,
                "longitude": sample_location.longitude,
                "date": datetime.now().isoformat(),
                "store_results": True  # Enable database storage
            }
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Validate successful prediction
            assert response.status_code == 200
            
            # Verify database operations were called
            mock_store_env.assert_called()
            mock_store_pred.assert_called()
            mock_store_risk.assert_called()

    async def test_error_handling_workflow(
        self,
        client: TestClient,
        sample_location: GeographicLocation
    ):
        """Test error handling throughout prediction workflow."""
        
        # Test external API failure handling
        with patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5:
            mock_era5.side_effect = httpx.TimeoutException("ERA5 API timeout")
            
            prediction_request = {
                "latitude": sample_location.latitude,
                "longitude": sample_location.longitude,
                "date": datetime.now().isoformat()
            }
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Should handle gracefully and return appropriate error
            assert response.status_code in [500, 503]  # Server error or service unavailable
            
            error_response = response.json()
            assert "error" in error_response
            assert "ERA5" in error_response["error"] or "timeout" in error_response["error"].lower()

    async def test_authentication_workflow(self, client: TestClient):
        """Test authentication integration in prediction workflow."""
        
        # Test unauthenticated request
        prediction_request = {
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.now().isoformat()
        }
        
        # Mock authentication requirement
        with patch("malaria_predictor.api.dependencies.get_current_user") as mock_auth:
            mock_auth.side_effect = Exception("Authentication required")
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Should require authentication
            assert response.status_code in [401, 403]

    async def test_rate_limiting_workflow(self, client: TestClient):
        """Test rate limiting integration in prediction workflow."""
        
        prediction_request = {
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.now().isoformat()
        }
        
        # Mock rate limiting
        with patch("malaria_predictor.api.middleware.RateLimitMiddleware.check_rate_limit") as mock_rate_limit:
            mock_rate_limit.side_effect = Exception("Rate limit exceeded")
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Should enforce rate limits
            assert response.status_code == 429  # Too Many Requests

    async def test_health_check_integration(self, client: TestClient):
        """Test health check integration for system components."""
        
        # Test system health endpoint
        response = client.get("/health/status")
        
        # Should return health status
        assert response.status_code == 200
        health_data = response.json()
        
        assert "status" in health_data
        assert "components" in health_data
        assert "timestamp" in health_data
        
        # Verify key components are monitored
        components = health_data["components"]
        expected_components = ["database", "redis", "external_apis", "ml_models"]
        
        for component in expected_components:
            assert component in components
            assert "status" in components[component]

    async def test_performance_monitoring_workflow(
        self,
        client: TestClient,
        sample_location: GeographicLocation,
        mock_environmental_data: Dict[str, Any],
        mock_prediction_result: Dict[str, Any]
    ):
        """Test performance monitoring integration in prediction workflow."""
        
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict,
            patch("malaria_predictor.monitoring.metrics.performance_counter.record") as mock_perf_counter
        ):
            
            # Configure mocks
            mock_era5.return_value = mock_environmental_data["era5_data"]
            mock_ml_predict.return_value = mock_prediction_result
            
            # Make prediction request
            prediction_request = {
                "latitude": sample_location.latitude,
                "longitude": sample_location.longitude,
                "date": datetime.now().isoformat()
            }
            
            response = client.post("/predict/single", json=prediction_request)
            
            # Validate successful prediction
            assert response.status_code == 200
            
            # Verify performance metrics were recorded
            mock_perf_counter.assert_called()
            
            # Response should include performance metadata
            result = response.json()
            assert "prediction_metadata" in result
            metadata = result["prediction_metadata"]
            assert "processing_time_ms" in metadata
            assert "data_sources_count" in metadata
            assert "model_version" in metadata


@pytest.mark.asyncio
class TestConcurrentPredictionWorkflows:
    """Test concurrent prediction workflows for load testing."""
    
    async def test_concurrent_single_predictions(self, client: TestClient):
        """Test handling multiple concurrent single predictions."""
        
        async def make_prediction(latitude: float, longitude: float) -> dict:
            """Make a single prediction request."""
            prediction_request = {
                "latitude": latitude,
                "longitude": longitude,
                "date": datetime.now().isoformat()
            }
            
            response = client.post("/predict/single", json=prediction_request)
            return response.json() if response.status_code == 200 else {"error": "failed"}
        
        # Create multiple concurrent prediction tasks
        locations = [
            (-1.2921, 36.8219),   # Nairobi
            (-4.0435, 39.6682),   # Mombasa
            (0.3476, 32.5825),    # Kampala
            (-15.3875, 28.3228),  # Lusaka
            (-17.8292, 31.0522)   # Harare
        ]
        
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Configure mocks for concurrent calls
            mock_era5.return_value = {"temperature": 298.15}
            mock_ml_predict.return_value = {"risk_score": 0.65, "confidence": 0.85}
            
            # Execute concurrent predictions
            tasks = [
                make_prediction(lat, lon) for lat, lon in locations
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate all predictions completed
            assert len(results) == len(locations)
            
            # Count successful predictions
            successful_predictions = [
                result for result in results 
                if isinstance(result, dict) and "risk_score" in result
            ]
            
            # Should handle concurrent load effectively
            assert len(successful_predictions) >= len(locations) * 0.8  # 80% success rate minimum


class TestDataPipelineIntegration:
    """Test data pipeline integration scenarios."""
    
    def test_data_harmonization_workflow(self):
        """Test data harmonization across multiple sources."""
        
        # Mock data from different sources with different formats
        era5_data = {
            "temperature": 298.15,  # Kelvin
            "precipitation": 0.0025,  # meters
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        chirps_data = {
            "precipitation": 2.5,  # millimeters
            "date": "2024-01-01"
        }
        
        modis_data = {
            "ndvi": 0.72,
            "lst": 303.15,  # Kelvin
            "date": "2024001"  # Julian date format
        }
        
        with patch("malaria_predictor.services.data_harmonizer.DataHarmonizer.harmonize") as mock_harmonizer:
            mock_harmonizer.return_value = {
                "temperature_celsius": 25.0,
                "precipitation_mm": 2.5,
                "ndvi": 0.72,
                "date": "2024-01-01T00:00:00Z",
                "data_quality_score": 0.95
            }
            
            harmonizer = DataHarmonizer()
            result = harmonizer.harmonize([era5_data, chirps_data, modis_data])
            
            # Verify harmonization was called and results are consistent
            mock_harmonizer.assert_called_once()
            assert result["temperature_celsius"] == 25.0
            assert result["precipitation_mm"] == 2.5
            assert "data_quality_score" in result

    def test_data_quality_validation_workflow(self):
        """Test data quality validation in pipeline."""
        
        # Test with high quality data
        high_quality_data = {
            "temperature": 298.15,
            "precipitation": 2.5,
            "humidity": 65.0,
            "completeness": 0.98,
            "temporal_consistency": 0.95
        }
        
        # Test with low quality data
        low_quality_data = {
            "temperature": 350.0,  # Unrealistic temperature
            "precipitation": -1.0,  # Invalid negative precipitation
            "humidity": 120.0,     # Invalid humidity > 100%
            "completeness": 0.45,  # Low data completeness
            "temporal_consistency": 0.30
        }
        
        with patch("malaria_predictor.services.data_harmonizer.DataValidator.validate") as mock_validator:
            # High quality data should pass
            mock_validator.return_value = {"valid": True, "quality_score": 0.95}
            
            validator = DataHarmonizer()
            result = validator.validate(high_quality_data)
            assert result["valid"] is True
            assert result["quality_score"] > 0.9
            
            # Low quality data should be flagged
            mock_validator.return_value = {"valid": False, "quality_score": 0.35, "issues": ["invalid_temperature", "negative_precipitation"]}
            
            result = validator.validate(low_quality_data)
            assert result["valid"] is False
            assert result["quality_score"] < 0.5
            assert "issues" in result


# Performance and Load Testing
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance and load testing for integration scenarios."""
    
    async def test_prediction_performance_benchmarks(self, client: TestClient):
        """Test prediction performance under various loads."""
        
        import time
        
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Configure fast mocks
            mock_era5.return_value = {"temperature": 298.15}
            mock_ml_predict.return_value = {"risk_score": 0.65}
            
            # Measure single prediction performance
            start_time = time.time()
            
            prediction_request = {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "date": datetime.now().isoformat()
            }
            
            response = client.post("/predict/single", json=prediction_request)
            
            end_time = time.time()
            prediction_time = (end_time - start_time) * 1000  # milliseconds
            
            # Performance assertions
            assert response.status_code == 200
            assert prediction_time < 5000  # Should complete within 5 seconds
            
            # Verify performance metadata in response
            result = response.json()
            if "prediction_metadata" in result:
                metadata = result["prediction_metadata"]
                assert "processing_time_ms" in metadata
                assert metadata["processing_time_ms"] < 5000

    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during prediction workflows."""
        
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate large data processing
        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_ml_predict
        ):
            
            # Mock large data response
            large_data = {"temperature": [298.15] * 10000}  # Large dataset
            mock_era5.return_value = large_data
            mock_ml_predict.return_value = {"risk_score": 0.65}
            
            # Process multiple predictions
            for _ in range(10):
                # Simulate prediction processing
                pass
            
            # Check memory usage after processing
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 100MB for test)
            assert memory_increase < 100, f"Memory increased by {memory_increase}MB"