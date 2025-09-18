"""
Comprehensive unit tests for core data models.

Tests all Pydantic models for validation, serialization, and edge cases
to achieve high coverage for the models module.
"""

from datetime import UTC, date, datetime
from typing import Any

import pytest

from src.malaria_predictor.models import (
    BatchPredictionRequest,
    EnvironmentalFactors,
    GeographicLocation,
    HealthStatus,
    MalariaRisk,
    ModelInfo,
    PredictionRequest,
    RiskLevel,
    User,
    UserRole,
)


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_risk_level_values(self):
        """Test all risk level values are available."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"

    def test_risk_level_comparison(self):
        """Test risk level string comparison."""
        assert RiskLevel.LOW in ["low", "medium", "high", "critical"]
        assert str(RiskLevel.HIGH) == "high"


class TestEnvironmentalFactors:
    """Test EnvironmentalFactors model."""

    @pytest.fixture
    def valid_env_factors(self) -> dict[str, Any]:
        """Valid environmental factors data."""
        return {
            "temperature": 25.5,
            "rainfall": 120.0,
            "humidity": 75.0,
            "ndvi": 0.6,
            "elevation": 1200.0,
            "wind_speed": 8.5,
            "solar_radiation": 250.0,
            "air_pressure": 1013.25
        }

    def test_valid_environmental_factors(self, valid_env_factors):
        """Test creating valid environmental factors."""
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.temperature == 25.5
        assert factors.rainfall == 120.0
        assert factors.humidity == 75.0
        assert factors.ndvi == 0.6
        assert factors.elevation == 1200.0
        assert factors.wind_speed == 8.5
        assert factors.solar_radiation == 250.0
        assert factors.air_pressure == 1013.25

    def test_temperature_validation(self, valid_env_factors):
        """Test temperature validation ranges."""
        # Valid temperature
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.temperature == 25.5

        # Edge case temperatures
        valid_env_factors["temperature"] = -10.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.temperature == -10.0

        valid_env_factors["temperature"] = 50.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.temperature == 50.0

    def test_rainfall_validation(self, valid_env_factors):
        """Test rainfall validation."""
        # Zero rainfall should be valid
        valid_env_factors["rainfall"] = 0.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.rainfall == 0.0

        # High rainfall
        valid_env_factors["rainfall"] = 500.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.rainfall == 500.0

    def test_humidity_validation(self, valid_env_factors):
        """Test humidity validation."""
        # Test 0% humidity
        valid_env_factors["humidity"] = 0.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.humidity == 0.0

        # Test 100% humidity
        valid_env_factors["humidity"] = 100.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.humidity == 100.0

    def test_ndvi_validation(self, valid_env_factors):
        """Test NDVI validation."""
        # Test negative NDVI (water/urban)
        valid_env_factors["ndvi"] = -0.1
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.ndvi == -0.1

        # Test maximum NDVI (dense vegetation)
        valid_env_factors["ndvi"] = 1.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.ndvi == 1.0


class TestGeographicLocation:
    """Test GeographicLocation model."""

    def test_valid_location(self):
        """Test creating valid geographic location."""
        location = GeographicLocation(
            latitude=-1.2921,  # Nairobi coordinates
            longitude=36.8219,
            country="Kenya",
            region="Nairobi County"
        )
        assert location.latitude == -1.2921
        assert location.longitude == 36.8219
        assert location.country == "Kenya"
        assert location.region == "Nairobi County"

    def test_latitude_bounds(self):
        """Test latitude validation bounds."""
        # Valid latitudes
        location = GeographicLocation(latitude=-90.0, longitude=0.0, country="Test", region="Test")
        assert location.latitude == -90.0

        location = GeographicLocation(latitude=90.0, longitude=0.0, country="Test", region="Test")
        assert location.latitude == 90.0

        location = GeographicLocation(latitude=0.0, longitude=0.0, country="Test", region="Test")
        assert location.latitude == 0.0

    def test_longitude_bounds(self):
        """Test longitude validation bounds."""
        # Valid longitudes
        location = GeographicLocation(latitude=0.0, longitude=-180.0, country="Test", region="Test")
        assert location.longitude == -180.0

        location = GeographicLocation(latitude=0.0, longitude=180.0, country="Test", region="Test")
        assert location.longitude == 180.0

        location = GeographicLocation(latitude=0.0, longitude=0.0, country="Test", region="Test")
        assert location.longitude == 0.0

    def test_string_fields(self):
        """Test string field validation."""
        location = GeographicLocation(
            latitude=0.0,
            longitude=0.0,
            country="Democratic Republic of the Congo",
            region="Kinshasa Province"
        )
        assert location.country == "Democratic Republic of the Congo"
        assert location.region == "Kinshasa Province"


class TestMalariaRisk:
    """Test MalariaRisk model."""

    @pytest.fixture
    def valid_risk_data(self) -> dict[str, Any]:
        """Valid malaria risk data."""
        return {
            "risk_level": RiskLevel.HIGH,
            "risk_score": 0.75,
            "confidence": 0.85,
            "prediction_date": date(2024, 6, 15),
            "location": {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "country": "Kenya",
                "region": "Nairobi County"
            },
            "environmental_factors": {
                "temperature": 25.5,
                "rainfall": 120.0,
                "humidity": 75.0,
                "ndvi": 0.6,
                "elevation": 1200.0,
                "wind_speed": 8.5,
                "solar_radiation": 250.0,
                "air_pressure": 1013.25
            },
            "model_version": "v1.2.0"
        }

    def test_valid_malaria_risk(self, valid_risk_data):
        """Test creating valid malaria risk assessment."""
        risk = MalariaRisk(**valid_risk_data)
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.risk_score == 0.75
        assert risk.confidence == 0.85
        assert risk.prediction_date == date(2024, 6, 15)
        assert risk.model_version == "v1.2.0"
        assert isinstance(risk.location, GeographicLocation)
        assert isinstance(risk.environmental_factors, EnvironmentalFactors)

    def test_risk_score_bounds(self, valid_risk_data):
        """Test risk score validation."""
        # Minimum risk score
        valid_risk_data["risk_score"] = 0.0
        risk = MalariaRisk(**valid_risk_data)
        assert risk.risk_score == 0.0

        # Maximum risk score
        valid_risk_data["risk_score"] = 1.0
        risk = MalariaRisk(**valid_risk_data)
        assert risk.risk_score == 1.0

    def test_confidence_bounds(self, valid_risk_data):
        """Test confidence validation."""
        # Minimum confidence
        valid_risk_data["confidence"] = 0.0
        risk = MalariaRisk(**valid_risk_data)
        assert risk.confidence == 0.0

        # Maximum confidence
        valid_risk_data["confidence"] = 1.0
        risk = MalariaRisk(**valid_risk_data)
        assert risk.confidence == 1.0


class TestPredictionRequest:
    """Test PredictionRequest model."""

    @pytest.fixture
    def valid_request(self) -> dict[str, Any]:
        """Valid prediction request data."""
        return {
            "location": {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "country": "Kenya",
                "region": "Nairobi County"
            },
            "prediction_date": date(2024, 6, 15),
            "model_type": "ensemble",
            "include_confidence": True,
            "include_factors": True
        }

    def test_valid_prediction_request(self, valid_request):
        """Test creating valid prediction request."""
        request = PredictionRequest(**valid_request)
        assert isinstance(request.location, GeographicLocation)
        assert request.prediction_date == date(2024, 6, 15)
        assert request.model_type == "ensemble"
        assert request.include_confidence is True
        assert request.include_factors is True

    def test_optional_fields(self, valid_request):
        """Test optional fields in prediction request."""
        # Remove optional fields
        del valid_request["model_type"]
        del valid_request["include_confidence"]
        del valid_request["include_factors"]

        request = PredictionRequest(**valid_request)
        assert request.model_type == "ensemble"  # Default value
        assert request.include_confidence is False  # Default value
        assert request.include_factors is False  # Default value


class TestUserRole:
    """Test UserRole enum."""

    def test_user_role_values(self):
        """Test all user role values."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.RESEARCHER == "researcher"
        assert UserRole.HEALTHCARE_PROVIDER == "healthcare_provider"
        assert UserRole.PUBLIC_HEALTH_OFFICIAL == "public_health_official"
        assert UserRole.VIEWER == "viewer"


class TestUser:
    """Test User model."""

    @pytest.fixture
    def valid_user_data(self) -> dict[str, Any]:
        """Valid user data."""
        return {
            "id": "user_123",
            "username": "test_user",
            "email": "test@example.com",
            "role": UserRole.RESEARCHER,
            "is_active": True,
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            "organization": "Test University",
            "country": "Kenya"
        }

    def test_valid_user(self, valid_user_data):
        """Test creating valid user."""
        user = User(**valid_user_data)
        assert user.id == "user_123"
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.role == UserRole.RESEARCHER
        assert user.is_active is True
        assert user.organization == "Test University"
        assert user.country == "Kenya"

    def test_optional_fields(self, valid_user_data):
        """Test optional user fields."""
        # Remove optional fields
        del valid_user_data["organization"]
        del valid_user_data["country"]

        user = User(**valid_user_data)
        assert user.organization is None
        assert user.country is None


class TestHealthStatus:
    """Test HealthStatus model."""

    def test_valid_health_status(self):
        """Test creating valid health status."""
        status = HealthStatus(
            status="healthy",
            timestamp=datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC),
            version="1.0.0",
            uptime=3600.0
        )
        assert status.status == "healthy"
        assert status.version == "1.0.0"
        assert status.uptime == 3600.0

    def test_optional_fields(self):
        """Test optional health status fields."""
        status = HealthStatus(
            status="healthy",
            timestamp=datetime.now(UTC),
            version="1.0.0"
        )
        assert status.status == "healthy"
        assert status.version == "1.0.0"
        assert status.uptime is None


class TestBatchPredictionRequest:
    """Test BatchPredictionRequest model."""

    def test_valid_batch_request(self):
        """Test creating valid batch prediction request."""
        locations = [
            {
                "latitude": -1.2921,
                "longitude": 36.8219,
                "country": "Kenya",
                "region": "Nairobi County"
            },
            {
                "latitude": -6.7924,
                "longitude": 39.2083,
                "country": "Tanzania",
                "region": "Dar es Salaam"
            }
        ]

        request = BatchPredictionRequest(
            locations=locations,
            prediction_date=date(2024, 6, 15),
            model_type="lstm"
        )

        assert len(request.locations) == 2
        assert all(isinstance(loc, GeographicLocation) for loc in request.locations)
        assert request.prediction_date == date(2024, 6, 15)
        assert request.model_type == "lstm"


class TestModelInfo:
    """Test ModelInfo model."""

    def test_valid_model_info(self):
        """Test creating valid model info."""
        info = ModelInfo(
            name="LSTM Malaria Predictor",
            version="v2.1.0",
            description="Long Short-Term Memory model for malaria outbreak prediction",
            accuracy=0.87,
            last_trained=datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC),
            features=[
                "temperature",
                "rainfall",
                "humidity",
                "ndvi",
                "elevation"
            ]
        )

        assert info.name == "LSTM Malaria Predictor"
        assert info.version == "v2.1.0"
        assert info.accuracy == 0.87
        assert len(info.features) == 5
        assert "temperature" in info.features
        assert "rainfall" in info.features


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_environmental_factors_json_round_trip(self):
        """Test EnvironmentalFactors JSON serialization."""
        original = EnvironmentalFactors(
            temperature=25.5,
            rainfall=120.0,
            humidity=75.0,
            ndvi=0.6,
            elevation=1200.0,
            wind_speed=8.5,
            solar_radiation=250.0,
            air_pressure=1013.25
        )

        # Serialize to JSON
        json_data = original.model_dump()

        # Deserialize from JSON
        restored = EnvironmentalFactors(**json_data)

        assert restored.temperature == original.temperature
        assert restored.rainfall == original.rainfall
        assert restored.humidity == original.humidity
        assert restored.ndvi == original.ndvi

    def test_malaria_risk_json_round_trip(self):
        """Test MalariaRisk JSON serialization."""
        original = MalariaRisk(
            risk_level=RiskLevel.HIGH,
            risk_score=0.75,
            confidence=0.85,
            prediction_date=date(2024, 6, 15),
            location=GeographicLocation(
                latitude=-1.2921,
                longitude=36.8219,
                country="Kenya",
                region="Nairobi County"
            ),
            environmental_factors=EnvironmentalFactors(
                temperature=25.5,
                rainfall=120.0,
                humidity=75.0,
                ndvi=0.6,
                elevation=1200.0,
                wind_speed=8.5,
                solar_radiation=250.0,
                air_pressure=1013.25
            ),
            model_version="v1.2.0"
        )

        # Serialize to JSON
        json_data = original.model_dump()

        # Deserialize from JSON
        restored = MalariaRisk(**json_data)

        assert restored.risk_level == original.risk_level
        assert restored.risk_score == original.risk_score
        assert restored.confidence == original.confidence
        assert restored.location.latitude == original.location.latitude
        assert restored.environmental_factors.temperature == original.environmental_factors.temperature
