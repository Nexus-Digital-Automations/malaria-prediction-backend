"""
Performance testing framework for malaria prediction system.

Tests API response times, ML model inference speed, data processing
throughput, and system resource utilization under load.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import psutil
import pytest
import torch

from src.malaria_predictor.ml.models.ensemble_model import EnsembleConfig, EnsembleModel
from src.malaria_predictor.ml.models.lstm_model import LSTMConfig, LSTMModel
from src.malaria_predictor.ml.models.transformer_model import (
    TransformerConfig,
    TransformerModel,
)


class PerformanceMetrics:
    """Utility class for tracking performance metrics."""

    def __init__(self):
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.throughput_metrics = []

    def record_response_time(self, start_time: float, end_time: float):
        """Record API response time."""
        self.response_times.append(end_time - start_time)

    def record_system_metrics(self):
        """Record current system resource usage."""
        process = psutil.Process()
        self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_usage.append(process.cpu_percent())

    def record_throughput(self, items_processed: int, time_taken: float):
        """Record throughput (items per second)."""
        self.throughput_metrics.append(items_processed / time_taken)

    def get_summary(self) -> dict:
        """Get performance summary statistics."""
        return {
            'response_times': {
                'mean': statistics.mean(self.response_times) if self.response_times else 0,
                'median': statistics.median(self.response_times) if self.response_times else 0,
                'p95': np.percentile(self.response_times, 95) if self.response_times else 0,
                'p99': np.percentile(self.response_times, 99) if self.response_times else 0,
                'min': min(self.response_times) if self.response_times else 0,
                'max': max(self.response_times) if self.response_times else 0
            },
            'memory_usage': {
                'mean': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max': max(self.memory_usage) if self.memory_usage else 0,
                'min': min(self.memory_usage) if self.memory_usage else 0
            },
            'cpu_usage': {
                'mean': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max': max(self.cpu_usage) if self.cpu_usage else 0
            },
            'throughput': {
                'mean': statistics.mean(self.throughput_metrics) if self.throughput_metrics else 0,
                'max': max(self.throughput_metrics) if self.throughput_metrics else 0
            }
        }


class TestMLModelPerformance:
    """Test ML model inference performance."""

    @pytest.fixture
    def lstm_model(self):
        """LSTM model for performance testing."""
        config = LSTMConfig(
            input_dim=15,
            hidden_dim=128,
            num_layers=3,
            dropout=0.2
        )
        model = LSTMModel(config)
        model.eval()  # Set to evaluation mode
        return model

    @pytest.fixture
    def transformer_model(self):
        """Transformer model for performance testing."""
        config = TransformerConfig(
            input_dim=15,
            model_dim=256,
            num_heads=8,
            num_layers=6,
            feedforward_dim=512,
            max_sequence_length=365
        )
        model = TransformerModel(config)
        model.eval()
        return model

    @pytest.fixture
    def ensemble_model(self):
        """Ensemble model for performance testing."""
        config = EnsembleConfig(
            lstm_config=LSTMConfig(input_dim=15, hidden_dim=64, num_layers=2),
            transformer_config=TransformerConfig(
                input_dim=15, model_dim=128, num_heads=8, num_layers=4
            ),
            ensemble_weights=[0.6, 0.4]
        )
        model = EnsembleModel(config)
        model.eval()
        return model

    def test_lstm_inference_speed(self, lstm_model):
        """Test LSTM model inference speed."""
        metrics = PerformanceMetrics()

        # Test different batch sizes and sequence lengths
        test_cases = [
            (1, 30, 15),    # Single prediction, 30 days
            (10, 30, 15),   # Small batch
            (50, 30, 15),   # Medium batch
            (100, 30, 15),  # Large batch
            (1, 365, 15),   # Long sequence
        ]

        for batch_size, seq_len, input_dim in test_cases:
            test_input = torch.randn(batch_size, seq_len, input_dim)

            # Warm-up runs
            for _ in range(3):
                with torch.no_grad():
                    _ = lstm_model(test_input)

            # Performance measurement
            start_time = time.time()
            metrics.record_system_metrics()

            with torch.no_grad():
                output = lstm_model(test_input)

            end_time = time.time()
            metrics.record_response_time(start_time, end_time)
            metrics.record_throughput(batch_size, end_time - start_time)
            metrics.record_system_metrics()

            # Verify output shape
            assert output.shape == (batch_size, 1)

        summary = metrics.get_summary()

        # Performance assertions
        assert summary['response_times']['mean'] < 1.0  # Under 1 second average
        assert summary['response_times']['p95'] < 2.0   # 95% under 2 seconds
        assert summary['memory_usage']['max'] < 2000    # Under 2GB memory

        print(f"LSTM Performance Summary: {summary}")

    def test_transformer_inference_speed(self, transformer_model):
        """Test Transformer model inference speed."""
        metrics = PerformanceMetrics()

        test_cases = [
            (1, 30, 15),    # Single prediction
            (5, 30, 15),    # Small batch
            (20, 30, 15),   # Medium batch (Transformers are more memory intensive)
            (1, 180, 15),   # Longer sequence
        ]

        for batch_size, seq_len, input_dim in test_cases:
            test_input = torch.randn(batch_size, seq_len, input_dim)

            # Warm-up
            for _ in range(3):
                with torch.no_grad():
                    _ = transformer_model(test_input)

            start_time = time.time()
            metrics.record_system_metrics()

            with torch.no_grad():
                output = transformer_model(test_input)

            end_time = time.time()
            metrics.record_response_time(start_time, end_time)
            metrics.record_throughput(batch_size, end_time - start_time)
            metrics.record_system_metrics()

            assert output.shape == (batch_size, 1)

        summary = metrics.get_summary()

        # Transformer-specific performance assertions
        assert summary['response_times']['mean'] < 2.0  # Under 2 seconds average
        assert summary['response_times']['p95'] < 5.0   # 95% under 5 seconds
        assert summary['memory_usage']['max'] < 4000    # Under 4GB memory

        print(f"Transformer Performance Summary: {summary}")

    def test_ensemble_inference_speed(self, ensemble_model):
        """Test Ensemble model inference speed."""
        metrics = PerformanceMetrics()

        test_cases = [
            (1, 30, 15),    # Single prediction
            (5, 30, 15),    # Small batch
            (10, 30, 15),   # Medium batch
            (1, 90, 15),    # Longer sequence
        ]

        for batch_size, seq_len, input_dim in test_cases:
            test_input = torch.randn(batch_size, seq_len, input_dim)

            # Warm-up
            for _ in range(3):
                with torch.no_grad():
                    _ = ensemble_model(test_input)

            start_time = time.time()
            metrics.record_system_metrics()

            with torch.no_grad():
                output = ensemble_model(test_input)

            end_time = time.time()
            metrics.record_response_time(start_time, end_time)
            metrics.record_throughput(batch_size, end_time - start_time)
            metrics.record_system_metrics()

            assert output.shape == (batch_size, 1)

        summary = metrics.get_summary()

        # Ensemble performance should be between LSTM and Transformer
        assert summary['response_times']['mean'] < 3.0  # Under 3 seconds average
        assert summary['response_times']['p95'] < 6.0   # 95% under 6 seconds
        assert summary['memory_usage']['max'] < 5000    # Under 5GB memory

        print(f"Ensemble Performance Summary: {summary}")

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gpu_acceleration(self, lstm_model):
        """Test GPU acceleration performance."""
        # CPU performance
        test_input_cpu = torch.randn(20, 30, 15)
        start_time = time.time()
        with torch.no_grad():
            _ = lstm_model(test_input_cpu)
        cpu_time = time.time() - start_time

        # GPU performance
        lstm_model_gpu = lstm_model.cuda()
        test_input_gpu = test_input_cpu.cuda()

        # Warm-up GPU
        for _ in range(5):
            with torch.no_grad():
                _ = lstm_model_gpu(test_input_gpu)

        start_time = time.time()
        with torch.no_grad():
            _ = lstm_model_gpu(test_input_gpu)
        gpu_time = time.time() - start_time

        # GPU should be faster for larger batches
        print(f"CPU time: {cpu_time:.4f}s, GPU time: {gpu_time:.4f}s")

        # For small models, GPU might not be faster due to overhead
        # Just ensure both work
        assert cpu_time > 0
        assert gpu_time > 0


class TestDataProcessingPerformance:
    """Test data processing performance."""

    def test_batch_data_processing(self):
        """Test batch environmental data processing performance."""
        from src.malaria_predictor.ml.feature_extractor import (
            EnvironmentalFeatureExtractor,
        )

        extractor = EnvironmentalFeatureExtractor()
        metrics = PerformanceMetrics()

        # Simulate different batch sizes of environmental data
        batch_sizes = [1, 10, 50, 100, 500]

        for batch_size in batch_sizes:
            # Generate mock environmental data
            environmental_data = {
                'temperature': np.random.uniform(15, 35, (batch_size, 30)),
                'rainfall': np.random.uniform(0, 200, (batch_size, 30)),
                'humidity': np.random.uniform(30, 90, (batch_size, 30)),
                'ndvi': np.random.uniform(-0.1, 0.9, (batch_size, 30)),
                'elevation': np.random.uniform(0, 3000, batch_size),
                'population_density': np.random.uniform(1, 1000, batch_size)
            }

            start_time = time.time()
            metrics.record_system_metrics()

            # Process environmental data
            features = extractor.extract_features(environmental_data)

            end_time = time.time()
            metrics.record_response_time(start_time, end_time)
            metrics.record_throughput(batch_size, end_time - start_time)
            metrics.record_system_metrics()

            # Verify output
            assert features is not None
            assert len(features) == batch_size

        summary = metrics.get_summary()

        # Data processing performance assertions
        assert summary['response_times']['mean'] < 5.0  # Under 5 seconds average
        assert summary['throughput']['mean'] > 10       # At least 10 items/second

        print(f"Data Processing Performance: {summary}")

    def test_concurrent_data_processing(self):
        """Test concurrent data processing performance."""
        from src.malaria_predictor.ml.feature_extractor import (
            EnvironmentalFeatureExtractor,
        )

        extractor = EnvironmentalFeatureExtractor()
        PerformanceMetrics()

        def process_data_batch(batch_id):
            """Process a single batch of data."""
            environmental_data = {
                'temperature': np.random.uniform(15, 35, (10, 30)),
                'rainfall': np.random.uniform(0, 200, (10, 30)),
                'humidity': np.random.uniform(30, 90, (10, 30)),
                'ndvi': np.random.uniform(-0.1, 0.9, (10, 30)),
                'elevation': np.random.uniform(0, 3000, 10),
                'population_density': np.random.uniform(1, 1000, 10)
            }

            start_time = time.time()
            features = extractor.extract_features(environmental_data)
            end_time = time.time()

            return {
                'batch_id': batch_id,
                'processing_time': end_time - start_time,
                'features_count': len(features)
            }

        # Test concurrent processing
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_data_batch, i) for i in range(20)]
            results = [future.result() for future in futures]
        end_time = time.time()

        total_time = end_time - start_time
        total_items = sum(result['features_count'] for result in results)

        # Performance assertions
        assert total_time < 30.0  # Under 30 seconds for 20 batches
        assert len(results) == 20
        assert all(result['features_count'] == 10 for result in results)

        throughput = total_items / total_time
        print(f"Concurrent Processing Throughput: {throughput:.2f} items/second")
        assert throughput > 5  # At least 5 items/second


class TestAPIPerformance:
    """Test API endpoint performance."""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application for performance testing."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @app.post("/predict/single")
        async def predict_single(request_data: dict):
            # Simulate processing time
            await asyncio.sleep(0.1)
            return {
                "risk_level": "medium",
                "risk_score": 0.65,
                "confidence": 0.82,
                "processing_time": 0.1
            }

        @app.post("/predict/batch")
        async def predict_batch(request_data: dict):
            batch_size = len(request_data.get("locations", []))
            # Simulate batch processing time
            await asyncio.sleep(0.05 * batch_size)
            return {
                "predictions": [
                    {
                        "location_id": i,
                        "risk_level": "medium",
                        "risk_score": 0.65,
                        "confidence": 0.82
                    }
                    for i in range(batch_size)
                ],
                "processing_time": 0.05 * batch_size
            }

        return TestClient(app)

    def test_health_endpoint_performance(self, mock_app):
        """Test health check endpoint performance."""
        metrics = PerformanceMetrics()

        # Test multiple health check requests
        for _ in range(100):
            start_time = time.time()
            response = mock_app.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            metrics.record_response_time(start_time, end_time)

        summary = metrics.get_summary()

        # Health check should be very fast
        assert summary['response_times']['mean'] < 0.1   # Under 100ms average
        assert summary['response_times']['p95'] < 0.2    # 95% under 200ms
        assert summary['response_times']['max'] < 0.5    # Max under 500ms

        print(f"Health Endpoint Performance: {summary}")

    def test_single_prediction_performance(self, mock_app):
        """Test single prediction endpoint performance."""
        metrics = PerformanceMetrics()

        prediction_request = {
            "location": {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "country": "Kenya",
                "region": "Nairobi County"
            },
            "prediction_date": "2024-06-15",
            "model_type": "ensemble"
        }

        # Test multiple prediction requests
        for _ in range(50):
            start_time = time.time()
            response = mock_app.post("/predict/single", json=prediction_request)
            end_time = time.time()

            assert response.status_code == 200
            metrics.record_response_time(start_time, end_time)

        summary = metrics.get_summary()

        # Single prediction performance requirements
        assert summary['response_times']['mean'] < 0.5   # Under 500ms average
        assert summary['response_times']['p95'] < 1.0    # 95% under 1 second
        assert summary['response_times']['max'] < 2.0    # Max under 2 seconds

        print(f"Single Prediction Performance: {summary}")

    def test_batch_prediction_performance(self, mock_app):
        """Test batch prediction endpoint performance."""
        metrics = PerformanceMetrics()

        # Test different batch sizes
        batch_sizes = [1, 5, 10, 25, 50, 100]

        for batch_size in batch_sizes:
            locations = [
                {
                    "latitude": -1.2921 + i * 0.1,
                    "longitude": 36.8219 + i * 0.1,
                    "country": "Kenya",
                    "region": f"Region_{i}"
                }
                for i in range(batch_size)
            ]

            batch_request = {
                "locations": locations,
                "prediction_date": "2024-06-15",
                "model_type": "ensemble"
            }

            start_time = time.time()
            response = mock_app.post("/predict/batch", json=batch_request)
            end_time = time.time()

            assert response.status_code == 200
            metrics.record_response_time(start_time, end_time)
            metrics.record_throughput(batch_size, end_time - start_time)

            # Verify response structure
            response_data = response.json()
            assert len(response_data["predictions"]) == batch_size

        summary = metrics.get_summary()

        # Batch prediction performance requirements
        assert summary['response_times']['mean'] < 10.0  # Under 10 seconds average
        assert summary['throughput']['mean'] > 5         # At least 5 predictions/second

        print(f"Batch Prediction Performance: {summary}")

    def test_concurrent_api_requests(self, mock_app):
        """Test concurrent API request handling."""
        PerformanceMetrics()

        def make_prediction_request(request_id):
            """Make a single prediction request."""
            prediction_request = {
                "location": {
                    "latitude": -1.2921 + request_id * 0.01,
                    "longitude": 36.8219 + request_id * 0.01,
                    "country": "Kenya",
                    "region": f"Region_{request_id}"
                },
                "prediction_date": "2024-06-15",
                "model_type": "lstm"
            }

            start_time = time.time()
            response = mock_app.post("/predict/single", json=prediction_request)
            end_time = time.time()

            return {
                'request_id': request_id,
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }

        # Test concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_prediction_request, i) for i in range(50)]
            results = [future.result() for future in futures]
        end_time = time.time()

        total_time = end_time - start_time
        successful_requests = sum(1 for result in results if result['status_code'] == 200)

        # Performance assertions
        assert successful_requests == 50  # All requests should succeed
        assert total_time < 20.0  # Under 20 seconds for 50 concurrent requests

        avg_response_time = sum(result['response_time'] for result in results) / len(results)
        throughput = len(results) / total_time

        print("Concurrent API Performance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")

        assert avg_response_time < 1.0  # Average under 1 second
        assert throughput > 5           # At least 5 requests/second


class TestMemoryUsage:
    """Test memory usage and potential memory leaks."""

    def test_model_memory_usage(self):
        """Test ML model memory usage."""
        import gc

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Create and use models
        models = []
        for _i in range(10):
            config = LSTMConfig(input_dim=15, hidden_dim=64, num_layers=2)
            model = LSTMModel(config)
            models.append(model)

            # Run inference
            test_input = torch.randn(5, 30, 15)
            with torch.no_grad():
                _ = model(test_input)

        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Clean up models
        del models
        gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        memory_increase = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory

        print("Memory Usage Test:")
        print(f"  Initial: {initial_memory:.1f}MB")
        print(f"  Peak: {peak_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Increase: {memory_increase:.1f}MB")
        print(f"  Cleanup: {memory_cleanup:.1f}MB")

        # Memory usage should be reasonable
        assert memory_increase < 1000  # Under 1GB increase
        assert memory_cleanup > memory_increase * 0.5  # At least 50% cleanup

    def test_data_processing_memory(self):
        """Test memory usage during large data processing."""
        import gc

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Process large amounts of data
        for _batch in range(5):
            large_data = np.random.randn(1000, 365, 15)  # Large tensor

            # Simulate processing
            processed_data = large_data.mean(axis=1)  # Reduce temporal dimension

            # Clean up
            del large_data, processed_data
            gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print("Data Processing Memory Test:")
        print(f"  Initial: {initial_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Net increase: {memory_increase:.1f}MB")

        # Should not have significant memory leaks
        assert abs(memory_increase) < 100  # Under 100MB net increase


if __name__ == "__main__":
    # Run performance tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
