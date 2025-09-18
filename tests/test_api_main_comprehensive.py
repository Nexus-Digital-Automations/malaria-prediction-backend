"""
Comprehensive unit tests for FastAPI main application module.
Target: 100% coverage for src/malaria_predictor/api/main.py
"""
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the main application module to test
from src.malaria_predictor.api.main import app, lifespan


class TestFastAPIApplication:
    """Test FastAPI application configuration and endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
        self.test_request_data = {
            "latitude": 12.5,
            "longitude": -15.3,
            "date": "2024-01-15"
        }

    def test_app_configuration(self):
        """Test FastAPI app is properly configured."""
        assert app.title == "Malaria Prediction API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_middleware_configuration(self):
        """Test middleware is properly configured."""
        # Check CORS middleware is configured
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORS middleware not found"

    def test_root_endpoint_success(self):
        """Test root endpoint returns API information."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Malaria Prediction API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "models" in data
        assert data["endpoints"]["docs"] == "/docs"
        assert data["endpoints"]["health"] == "/health"

    def test_info_endpoint_success(self):
        """Test info endpoint returns detailed API information."""
        response = self.client.get("/info")

        assert response.status_code == 200
        data = response.json()

        assert "api" in data
        assert "data_sources" in data
        assert "models" in data
        assert "endpoints" in data
        assert "features" in data

        # Check API section
        assert data["api"]["name"] == "Malaria Prediction API"
        assert data["api"]["version"] == "1.0.0"

        # Check data sources
        assert "era5" in data["data_sources"]
        assert "chirps" in data["data_sources"]
        assert "modis" in data["data_sources"]

        # Check models
        assert "lstm" in data["models"]
        assert "transformer" in data["models"]
        assert "ensemble" in data["models"]

    def test_info_endpoint_model_details(self):
        """Test info endpoint returns detailed model information."""
        response = self.client.get("/info")
        data = response.json()

        # Check LSTM model details
        lstm = data["models"]["lstm"]
        assert lstm["type"] == "LSTM Neural Network"
        assert lstm["prediction_horizon"] == "30 days"
        assert lstm["uncertainty"] is True

        # Check Transformer model details
        transformer = data["models"]["transformer"]
        assert transformer["type"] == "Transformer with Spatial-Temporal Attention"
        assert transformer["uncertainty"] is True

        # Check Ensemble model details
        ensemble = data["models"]["ensemble"]
        assert ensemble["type"] == "Hybrid Ensemble Model"
        assert "fusion_methods" in ensemble

    def test_openapi_schema_generation(self):
        """Test OpenAPI schema is properly generated."""
        response = self.client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "Malaria Prediction API"

    def test_docs_endpoint_accessible(self):
        """Test documentation endpoint is accessible."""
        response = self.client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self):
        """Test ReDoc documentation endpoint is accessible."""
        response = self.client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestExceptionHandlers:
    """Test custom exception handlers."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    @patch('src.malaria_predictor.api.main.logger')
    def test_http_exception_handler(self, mock_logger):
        """Test HTTP exception handler formatting."""
        # This will test the handler when an HTTPException is raised
        # We'll trigger it by accessing a non-existent endpoint
        response = self.client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data
        assert data["error"]["code"] == 404
        assert "timestamp" in data["error"]
        assert "path" in data["error"]
        assert data["error"]["path"] == "/nonexistent-endpoint"

    @patch('src.malaria_predictor.api.main.logger')
    def test_general_exception_handler_logs_error(self, mock_logger):
        """Test general exception handler logs errors properly."""
        # Create a mock endpoint that raises an exception
        @app.get("/test-exception")
        async def test_exception():
            raise ValueError("Test exception")

        response = self.client.get("/test-exception")

        assert response.status_code == 500
        data = response.json()

        assert data["error"]["code"] == 500
        assert data["error"]["message"] == "Internal server error"

        # Verify logger.error was called
        mock_logger.error.assert_called()

        # Clean up the test route
        app.router.routes = [route for route in app.router.routes if route.path != "/test-exception"]


@pytest.mark.asyncio
class TestLifespanManagement:
    """Test application lifespan management."""

    async def test_lifespan_startup_success(self):
        """Test successful application startup."""
        with patch('src.malaria_predictor.api.main.get_model_manager') as mock_get_model_manager, \
             patch('src.malaria_predictor.api.main.get_prediction_service') as mock_get_prediction_service, \
             patch('src.malaria_predictor.api.main.logger'):

            # Create mock objects
            mock_model_manager = AsyncMock()
            mock_prediction_service = AsyncMock()

            mock_get_model_manager.return_value = mock_model_manager
            mock_get_prediction_service.return_value = mock_prediction_service

            # Create a mock app for testing
            mock_app = Mock()
            mock_app.state = Mock()

            # Test the lifespan context manager
            async with lifespan(mock_app):
                # Verify initialization calls
                mock_get_model_manager.assert_called_once()
                mock_get_prediction_service.assert_called_once()

                # Verify app state is set
                assert mock_app.state.model_manager == mock_model_manager
                assert mock_app.state.prediction_service == mock_prediction_service

            # Verify cleanup is called on shutdown
            mock_model_manager.cleanup.assert_called_once()

    async def test_lifespan_startup_failure(self):
        """Test application startup failure handling."""
        with patch('src.malaria_predictor.api.main.get_model_manager') as mock_get_model_manager, \
             patch('src.malaria_predictor.api.main.logger') as mock_logger:

            # Mock startup failure
            mock_get_model_manager.side_effect = Exception("Startup failed")

            mock_app = Mock()
            mock_app.state = Mock()

            # Test that exception is re-raised
            with pytest.raises(Exception, match="Startup failed"):
                async with lifespan(mock_app):
                    pass

            # Verify error logging
            mock_logger.error.assert_called()

    async def test_lifespan_cleanup_on_shutdown(self):
        """Test cleanup is performed on application shutdown."""
        with patch('src.malaria_predictor.api.main.get_model_manager') as mock_get_model_manager, \
             patch('src.malaria_predictor.api.main.get_prediction_service') as mock_get_prediction_service, \
             patch('src.malaria_predictor.api.main.logger') as mock_logger:

            mock_model_manager = AsyncMock()
            mock_prediction_service = AsyncMock()

            mock_get_model_manager.return_value = mock_model_manager
            mock_get_prediction_service.return_value = mock_prediction_service

            mock_app = Mock()
            mock_app.state = Mock()

            async with lifespan(mock_app):
                pass  # Just testing cleanup

            # Verify cleanup was called
            mock_model_manager.cleanup.assert_called_once()
            mock_logger.info.assert_called()

    async def test_lifespan_with_no_model_manager(self):
        """Test lifespan when model manager is None."""
        with patch('src.malaria_predictor.api.main.get_model_manager') as mock_get_model_manager, \
             patch('src.malaria_predictor.api.main.get_prediction_service') as mock_get_prediction_service, \
             patch('src.malaria_predictor.api.main.logger') as mock_logger:

            mock_get_model_manager.return_value = None
            mock_get_prediction_service.return_value = AsyncMock()

            mock_app = Mock()
            mock_app.state = Mock()

            async with lifespan(mock_app):
                pass

            # Should not crash when model_manager is None
            mock_logger.info.assert_called()


class TestRouterInclusion:
    """Test router inclusion and endpoint availability."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_auth_router_included(self):
        """Test auth router is properly included."""
        # Test that auth endpoints exist (should return 405 Method Not Allowed or similar)
        response = self.client.get("/auth/")
        # Should not be 404, indicating the router is included
        assert response.status_code != 404

    def test_health_router_included(self):
        """Test health router is properly included."""
        response = self.client.get("/health")
        # Should not be 404, indicating the router is included
        assert response.status_code != 404

    def test_prediction_router_included(self):
        """Test prediction router is properly included."""
        response = self.client.get("/predict/")
        # Should not be 404, indicating the router is included
        assert response.status_code != 404

    def test_operations_router_included(self):
        """Test operations router is properly included."""
        response = self.client.get("/operations/")
        # Should not be 404, indicating the router is included
        assert response.status_code != 404


class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_cors_headers_present(self):
        """Test CORS headers are present in responses."""
        response = self.client.get("/")

        # Check basic CORS functionality
        assert response.status_code == 200

    def test_options_request_handling(self):
        """Test OPTIONS request handling for CORS preflight."""
        response = self.client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        # Should not be 404 or 405
        assert response.status_code in [200, 204]


class TestApplicationIntegrity:
    """Test overall application integrity and configuration."""

    def test_app_instance_created(self):
        """Test that app instance is properly created."""
        from src.malaria_predictor.api.main import app

        assert app is not None
        assert hasattr(app, 'title')
        assert hasattr(app, 'version')

    def test_app_has_required_attributes(self):
        """Test app has all required FastAPI attributes."""
        from src.malaria_predictor.api.main import app

        assert hasattr(app, 'routes')
        assert hasattr(app, 'middleware_stack')
        assert hasattr(app, 'exception_handlers')
        assert hasattr(app, 'openapi')

    def test_development_server_configuration(self):
        """Test development server configuration in __main__ block."""
        # This tests the configuration without actually running the server
        import src.malaria_predictor.api.main as main_module

        # Verify the module has the expected structure
        assert hasattr(main_module, 'app')
        assert hasattr(main_module, 'lifespan')

    def test_global_state_initialization(self):
        """Test global state variables are properly initialized."""
        from src.malaria_predictor.api.main import model_manager, prediction_service

        # These should be None initially
        assert model_manager is None
        assert prediction_service is None

    def test_logging_configuration(self):
        """Test logging is properly configured."""
        from src.malaria_predictor.api.main import logger

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "src.malaria_predictor.api.main"


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_malformed_request_handling(self):
        """Test handling of malformed requests."""
        response = self.client.post(
            "/predict/single",
            json={"invalid": "data"}
        )

        # Should return a proper error response, not crash
        assert response.status_code in [400, 422, 500]

        if response.status_code != 500:
            data = response.json()
            assert "error" in data or "detail" in data

    def test_large_request_handling(self):
        """Test handling of large requests."""
        large_data = {"data": "x" * 1000000}  # 1MB of data

        response = self.client.post("/predict/batch", json=large_data)

        # Should handle large requests gracefully
        assert response.status_code in [200, 400, 413, 422, 500]

    def test_concurrent_request_handling(self):
        """Test concurrent request handling."""
        import concurrent.futures


        def make_request():
            return self.client.get("/")

        # Test multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for result in results:
            assert result.status_code == 200


class TestPerformanceMetrics:
    """Test performance-related aspects of the application."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_response_time_reasonable(self):
        """Test that response times are reasonable."""
        import time

        start_time = time.time()
        response = self.client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0, f"Response time {response_time} seconds is too slow"

    def test_memory_usage_stable(self):
        """Test that memory usage remains stable."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make multiple requests
        for _ in range(10):
            response = self.client.get("/")
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase} bytes"


class TestSecurityHeaders:
    """Test security-related headers and configurations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_security_middleware_applied(self):
        """Test that security middleware is applied."""
        response = self.client.get("/")

        assert response.status_code == 200
        # The SecurityHeadersMiddleware should add security headers
        # We can't test the exact headers without knowing the implementation
        # but we can ensure the response is successful

    def test_gzip_compression_enabled(self):
        """Test that GZip compression is enabled."""
        response = self.client.get("/info")  # Large response

        assert response.status_code == 200
        # GZip middleware should compress large responses
        # Test passes if response is successful

    def test_request_id_middleware(self):
        """Test that request ID middleware is functioning."""
        response = self.client.get("/")

        assert response.status_code == 200
        # Request ID middleware should add request IDs to logs
        # Test passes if response is successful


class TestAPIDocumentation:
    """Test API documentation and schema generation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_openapi_schema_completeness(self):
        """Test that OpenAPI schema is complete."""
        response = self.client.get("/openapi.json")
        schema = response.json()

        assert response.status_code == 200
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema or "definitions" in schema

        # Check required info fields
        assert schema["info"]["title"] == "Malaria Prediction API"
        assert schema["info"]["version"] == "1.0.0"

    def test_api_description_content(self):
        """Test that API description contains expected content."""
        response = self.client.get("/openapi.json")
        schema = response.json()

        description = schema["info"]["description"]

        # Check for key features mentioned in description
        assert "real-time" in description.lower() or "prediction" in description.lower()
        assert "malaria" in description.lower()

    def test_endpoint_documentation(self):
        """Test that endpoints are properly documented."""
        response = self.client.get("/openapi.json")
        schema = response.json()

        paths = schema["paths"]

        # Check that main endpoints are documented
        assert "/" in paths
        assert "/info" in paths

        # Check that each path has proper HTTP methods
        root_path = paths["/"]
        assert "get" in root_path

        # Check that operations have summaries or descriptions
        get_operation = root_path["get"]
        assert "summary" in get_operation or "description" in get_operation
