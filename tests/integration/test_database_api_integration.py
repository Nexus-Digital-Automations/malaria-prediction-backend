"""
Database and API Integration Tests for Malaria Prediction System.

Tests database operations, API endpoints, authentication, and data persistence
throughout the complete prediction and data management workflows.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from malaria_predictor.api.main import app
from malaria_predictor.database.repositories import (
    EnvironmentalDataRepository,
    MalariaRiskRepository,
    PredictionRepository,
    UserRepository,
)
from malaria_predictor.database.security_models import APIKey
from malaria_predictor.models import (
    EnvironmentalData,
    User,
    UserRole,
    UserSession,
)


@pytest.mark.asyncio
class TestDatabaseIntegrationWorkflows:
    """Test database integration throughout prediction workflows."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create test user for authentication testing."""
        user_repo = UserRepository(db_session)

        user_data = {
            "email": "test.researcher@example.com",
            "username": "test_researcher",
            "full_name": "Test Researcher",
            "role": UserRole.RESEARCHER,
            "organization": "Test University",
            "is_active": True
        }

        user = await user_repo.create_user(user_data)
        await db_session.commit()
        return user

    @pytest.fixture
    async def test_api_key(self, db_session: AsyncSession, test_user: User) -> str:
        """Create test API key for authentication."""
        api_key_data = {
            "user_id": test_user.id,
            "name": "test_api_key",
            "key_hash": "test_hash_value",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "permissions": ["read", "predict"],
            "is_active": True
        }

        api_key = APIKey(**api_key_data)
        db_session.add(api_key)
        await db_session.commit()

        return "test_api_key_value"

    async def test_environmental_data_storage_workflow(
        self,
        db_session: AsyncSession,
        client: TestClient
    ):
        """Test environmental data storage and retrieval workflow."""

        env_repo = EnvironmentalDataRepository(db_session)

        # Sample environmental data for multiple sources
        era5_data = {
            "source": "ERA5",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow(),
            "temperature": 298.15,
            "precipitation": 2.5,
            "humidity": 65.2,
            "wind_speed": 3.1
        }

        chirps_data = {
            "source": "CHIRPS",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow(),
            "precipitation": 2.3,
            "precipitation_anomaly": 0.15
        }

        modis_data = {
            "source": "MODIS",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow(),
            "ndvi": 0.72,
            "lst_day": 303.15,
            "lst_night": 293.15
        }

        # Store environmental data
        era5_record = await env_repo.store_data(era5_data)
        chirps_record = await env_repo.store_data(chirps_data)
        modis_record = await env_repo.store_data(modis_data)

        await db_session.commit()

        # Verify data was stored correctly
        assert era5_record.id is not None
        assert chirps_record.id is not None
        assert modis_record.id is not None

        # Test data retrieval by location and date range
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)

        retrieved_data = await env_repo.get_data_by_location_and_date(
            latitude=-1.2921,
            longitude=36.8219,
            start_date=start_date,
            end_date=end_date
        )

        # Should retrieve all three records
        assert len(retrieved_data) == 3

        # Verify data sources are represented
        sources = {record.source for record in retrieved_data}
        assert "ERA5" in sources
        assert "CHIRPS" in sources
        assert "MODIS" in sources

    async def test_prediction_storage_and_retrieval_workflow(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test prediction storage and retrieval workflow."""

        pred_repo = PredictionRepository(db_session)

        # Sample prediction data
        prediction_data = {
            "user_id": test_user.id,
            "latitude": -1.2921,
            "longitude": 36.8219,
            "prediction_date": datetime.utcnow(),
            "risk_score": 0.75,
            "confidence": 0.89,
            "risk_category": "high",
            "model_version": "ensemble_v1.2",
            "environmental_factors": {
                "temperature": 25.0,
                "precipitation": 2.5,
                "humidity": 65.2,
                "ndvi": 0.72
            },
            "contributing_factors": {
                "temperature": 0.25,
                "precipitation": 0.30,
                "humidity": 0.20,
                "vegetation": 0.15,
                "baseline": 0.10
            }
        }

        # Store prediction
        prediction_record = await pred_repo.store_prediction(prediction_data)
        await db_session.commit()

        # Verify prediction was stored
        assert prediction_record.id is not None
        assert prediction_record.risk_score == 0.75
        assert prediction_record.confidence == 0.89
        assert prediction_record.user_id == test_user.id

        # Test prediction retrieval by user
        user_predictions = await pred_repo.get_predictions_by_user(test_user.id)
        assert len(user_predictions) >= 1
        assert user_predictions[0].id == prediction_record.id

        # Test prediction retrieval by location
        location_predictions = await pred_repo.get_predictions_by_location(
            latitude=-1.2921,
            longitude=36.8219,
            days_back=1
        )
        assert len(location_predictions) >= 1
        assert location_predictions[0].id == prediction_record.id

    async def test_risk_assessment_workflow(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test malaria risk assessment storage and analysis workflow."""

        risk_repo = MalariaRiskRepository(db_session)

        # Sample risk assessment data
        risk_data = {
            "user_id": test_user.id,
            "location_name": "Nairobi, Kenya",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "assessment_date": datetime.utcnow(),
            "population_at_risk": 850000,
            "risk_level": "high",
            "risk_score": 0.75,
            "confidence_interval": [0.68, 0.82],
            "environmental_risk_factors": {
                "temperature_risk": 0.80,
                "precipitation_risk": 0.70,
                "humidity_risk": 0.65,
                "vegetation_risk": 0.85
            },
            "demographic_factors": {
                "population_density": 8500,
                "urban_proportion": 0.85,
                "vulnerable_population": 0.25
            },
            "interventions_recommended": [
                "Enhanced vector control",
                "Community health education",
                "Improved case management"
            ]
        }

        # Store risk assessment
        risk_record = await risk_repo.store_risk_assessment(risk_data)
        await db_session.commit()

        # Verify risk assessment was stored
        assert risk_record.id is not None
        assert risk_record.risk_score == 0.75
        assert risk_record.location_name == "Nairobi, Kenya"
        assert risk_record.population_at_risk == 850000

        # Test risk assessment retrieval
        location_risks = await risk_repo.get_risk_assessments_by_location(
            latitude=-1.2921,
            longitude=36.8219
        )
        assert len(location_risks) >= 1
        assert location_risks[0].id == risk_record.id

    async def test_user_session_management_workflow(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test user session management workflow."""

        user_repo = UserRepository(db_session)

        # Create user session
        session_data = {
            "user_id": test_user.id,
            "session_token": "test_session_token_12345",
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "ip_address": "192.168.1.100",
            "user_agent": "Test Client/1.0",
            "is_active": True
        }

        session = UserSession(**session_data)
        db_session.add(session)
        await db_session.commit()

        # Verify session was created
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.is_active is True

        # Test session validation
        valid_session = await user_repo.validate_session("test_session_token_12345")
        assert valid_session is not None
        assert valid_session.user_id == test_user.id

        # Test session expiry
        expired_session_data = {
            "user_id": test_user.id,
            "session_token": "expired_session_token",
            "expires_at": datetime.utcnow() - timedelta(hours=1),  # Expired
            "ip_address": "192.168.1.100",
            "user_agent": "Test Client/1.0",
            "is_active": True
        }

        expired_session = UserSession(**expired_session_data)
        db_session.add(expired_session)
        await db_session.commit()

        # Expired session should not validate
        invalid_session = await user_repo.validate_session("expired_session_token")
        assert invalid_session is None

    async def test_concurrent_database_operations(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test concurrent database operations for thread safety."""

        env_repo = EnvironmentalDataRepository(db_session)

        async def store_environmental_data(index: int) -> EnvironmentalData:
            """Store environmental data concurrently."""
            data = {
                "source": "ERA5",
                "latitude": -1.2921 + (index * 0.01),  # Slight variation
                "longitude": 36.8219 + (index * 0.01),
                "date": datetime.utcnow(),
                "temperature": 298.15 + index,
                "precipitation": 2.5 + (index * 0.1),
                "humidity": 65.0 + index
            }

            return await env_repo.store_data(data)

        # Execute concurrent database operations
        tasks = [store_environmental_data(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        await db_session.commit()

        # Verify all operations completed successfully
        successful_operations = [
            result for result in results
            if isinstance(result, EnvironmentalData)
        ]

        assert len(successful_operations) == 10

        # Verify data integrity
        for i, record in enumerate(successful_operations):
            assert record.id is not None
            assert record.temperature == 298.15 + i

    async def test_data_archival_workflow(self, db_session: AsyncSession):
        """Test data archival and cleanup workflow."""

        env_repo = EnvironmentalDataRepository(db_session)

        # Create old environmental data (older than retention period)
        old_data = {
            "source": "ERA5",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow() - timedelta(days=400),  # Very old data
            "temperature": 298.15,
            "precipitation": 2.5,
            "humidity": 65.0
        }

        old_record = await env_repo.store_data(old_data)
        await db_session.commit()

        # Create recent data
        recent_data = {
            "source": "ERA5",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow() - timedelta(days=30),
            "temperature": 299.15,
            "precipitation": 3.0,
            "humidity": 70.0
        }

        recent_record = await env_repo.store_data(recent_data)
        await db_session.commit()

        # Test archival query (data older than 365 days)
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        archival_candidates = await env_repo.get_data_for_archival(cutoff_date)

        # Should identify old data for archival
        old_record_ids = [record.id for record in archival_candidates]
        assert old_record.id in old_record_ids
        assert recent_record.id not in old_record_ids


@pytest.mark.asyncio
class TestAPIEndpointIntegration:
    """Test API endpoint integration with database operations."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    async def test_health_endpoint_database_integration(self, client: TestClient):
        """Test health endpoint database connectivity check."""

        with patch("malaria_predictor.database.session.get_database_session") as mock_db:
            # Mock successful database connection
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value.scalar.return_value = 1

            response = client.get("/health/status")

            assert response.status_code == 200
            health_data = response.json()

            assert "components" in health_data
            assert "database" in health_data["components"]
            assert health_data["components"]["database"]["status"] == "healthy"

    async def test_prediction_endpoint_with_database_storage(
        self,
        client: TestClient
    ):
        """Test prediction endpoint with database storage enabled."""

        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.ml.models.ensemble_model.EnsembleModel.predict") as mock_predict,
            patch("malaria_predictor.database.repositories.PredictionRepository.store_prediction") as mock_store
        ):

            # Configure mocks
            mock_era5.return_value = {"temperature": 298.15, "precipitation": 2.5}
            mock_predict.return_value = {"risk_score": 0.75, "confidence": 0.89}
            mock_store.return_value = Mock(id=12345)

            # Make prediction request with storage enabled
            prediction_request = {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "date": datetime.now().isoformat(),
                "store_results": True
            }

            response = client.post("/predict/single", json=prediction_request)

            assert response.status_code == 200
            result = response.json()

            # Verify prediction was stored in database
            mock_store.assert_called_once()

            # Response should include storage confirmation
            assert "prediction_id" in result
            assert result["prediction_id"] == 12345

    async def test_user_authentication_api_workflow(self, client: TestClient):
        """Test user authentication API workflow."""

        with (
            patch("malaria_predictor.api.auth.AuthService.authenticate_user") as mock_auth,
            patch("malaria_predictor.api.auth.JWTTokenService.create_access_token") as mock_token
        ):

            # Configure authentication mocks
            mock_user = Mock()
            mock_user.id = 123
            mock_user.email = "test@example.com"
            mock_user.is_active = True

            mock_auth.return_value = mock_user
            mock_token.return_value = "jwt_token_12345"

            # Test login endpoint
            login_request = {
                "username": "test@example.com",
                "password": "test_password"
            }

            response = client.post("/auth/login", json=login_request)

            assert response.status_code == 200
            auth_result = response.json()

            assert "access_token" in auth_result
            assert "token_type" in auth_result
            assert auth_result["access_token"] == "jwt_token_12345"

            # Verify authentication was called
            mock_auth.assert_called_once_with("test@example.com", "test_password")

    async def test_api_rate_limiting_integration(self, client: TestClient):
        """Test API rate limiting with database tracking."""

        with (
            patch("malaria_predictor.api.middleware.RateLimitMiddleware.check_rate_limit") as mock_rate_limit,
            patch("malaria_predictor.database.repositories.APIUsageRepository.record_request") as mock_usage
        ):

            # First request should succeed
            mock_rate_limit.return_value = True
            mock_usage.return_value = True

            response = client.get("/health/status")
            assert response.status_code == 200

            # Verify usage was recorded
            mock_usage.assert_called_once()

            # Subsequent request should be rate limited
            mock_rate_limit.return_value = False

            response = client.get("/health/status")
            assert response.status_code == 429  # Too Many Requests

    async def test_error_logging_integration(self, client: TestClient):
        """Test error logging integration with database."""

        with (
            patch("malaria_predictor.services.era5_client.ERA5Client.get_data") as mock_era5,
            patch("malaria_predictor.monitoring.logger.ErrorLogger.log_error") as mock_error_log
        ):

            # Simulate API error
            mock_era5.side_effect = Exception("ERA5 API connection failed")

            prediction_request = {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "date": datetime.now().isoformat()
            }

            response = client.post("/predict/single", json=prediction_request)

            # Should handle error gracefully
            assert response.status_code in [500, 503]

            # Verify error was logged
            mock_error_log.assert_called()


class TestDataConsistencyIntegration:
    """Test data consistency across database operations."""

    async def test_transaction_rollback_workflow(self, db_session: AsyncSession):
        """Test transaction rollback maintains data consistency."""

        env_repo = EnvironmentalDataRepository(db_session)

        # Store valid environmental data
        valid_data = {
            "source": "ERA5",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "date": datetime.utcnow(),
            "temperature": 298.15,
            "precipitation": 2.5
        }

        valid_record = await env_repo.store_data(valid_data)

        # Attempt to store invalid data in same transaction
        try:
            invalid_data = {
                "source": "ERA5",
                "latitude": None,  # Invalid latitude
                "longitude": 36.8219,
                "date": datetime.utcnow(),
                "temperature": 298.15
            }

            await env_repo.store_data(invalid_data)
            await db_session.commit()

        except Exception:
            # Transaction should rollback
            await db_session.rollback()

        # Verify valid record was not committed due to rollback
        result = await db_session.execute(
            select(EnvironmentalData).where(EnvironmentalData.id == valid_record.id)
        )
        record = result.scalar_one_or_none()

        # Record should not exist due to rollback
        assert record is None

    async def test_foreign_key_constraint_integrity(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test foreign key constraints maintain referential integrity."""

        pred_repo = PredictionRepository(db_session)

        # Attempt to create prediction with invalid user_id
        invalid_prediction_data = {
            "user_id": 99999,  # Non-existent user
            "latitude": -1.2921,
            "longitude": 36.8219,
            "prediction_date": datetime.utcnow(),
            "risk_score": 0.75,
            "confidence": 0.89
        }

        # This should fail due to foreign key constraint
        with pytest.raises(IntegrityError):
            await pred_repo.store_prediction(invalid_prediction_data)
            await db_session.commit()

        # Valid prediction with existing user should succeed
        valid_prediction_data = {
            "user_id": test_user.id,
            "latitude": -1.2921,
            "longitude": 36.8219,
            "prediction_date": datetime.utcnow(),
            "risk_score": 0.75,
            "confidence": 0.89
        }

        valid_record = await pred_repo.store_prediction(valid_prediction_data)
        await db_session.commit()

        assert valid_record.id is not None
        assert valid_record.user_id == test_user.id
