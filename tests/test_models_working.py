"""
Working unit tests for existing data models.

Tests the actual Pydantic models in the codebase for validation,
serialization, and edge cases.
"""

from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from src.malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
    RiskLevel,
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

    def test_serialization(self, valid_env_factors):
        """Test JSON serialization and deserialization."""
        original = EnvironmentalFactors(**valid_env_factors)

        # Serialize to JSON
        json_data = original.model_dump()

        # Deserialize from JSON
        restored = EnvironmentalFactors(**json_data)

        assert restored.temperature == original.temperature
        assert restored.rainfall == original.rainfall
        assert restored.humidity == original.humidity
        assert restored.ndvi == original.ndvi


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

    def test_serialization(self):
        """Test JSON serialization."""
        original = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            country="Kenya",
            region="Nairobi County"
        )

        json_data = original.model_dump()
        restored = GeographicLocation(**json_data)

        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude
        assert restored.country == original.country
        assert restored.region == original.region


class TestRiskAssessment:
    """Test RiskAssessment model."""

    @pytest.fixture
    def valid_risk_data(self) -> dict[str, Any]:
        """Valid risk assessment data."""
        return {
            "risk_level": RiskLevel.HIGH,
            "risk_score": 0.75,
            "confidence": 0.85,
            "location": GeographicLocation(
                latitude=-1.2921,
                longitude=36.8219,
                country="Kenya",
                region="Nairobi County"
            ),
            "environmental_factors": EnvironmentalFactors(
                temperature=25.5,
                rainfall=120.0,
                humidity=75.0,
                ndvi=0.6,
                elevation=1200.0,
                wind_speed=8.5,
                solar_radiation=250.0,
                air_pressure=1013.25
            )
        }

    def test_valid_risk_assessment(self, valid_risk_data):
        """Test creating valid risk assessment."""
        risk = RiskAssessment(**valid_risk_data)
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.risk_score == 0.75
        assert risk.confidence == 0.85
        assert isinstance(risk.location, GeographicLocation)
        assert isinstance(risk.environmental_factors, EnvironmentalFactors)

    def test_risk_score_bounds(self, valid_risk_data):
        """Test risk score validation."""
        # Minimum risk score
        valid_risk_data["risk_score"] = 0.0
        risk = RiskAssessment(**valid_risk_data)
        assert risk.risk_score == 0.0

        # Maximum risk score
        valid_risk_data["risk_score"] = 1.0
        risk = RiskAssessment(**valid_risk_data)
        assert risk.risk_score == 1.0

    def test_confidence_bounds(self, valid_risk_data):
        """Test confidence validation."""
        # Minimum confidence
        valid_risk_data["confidence"] = 0.0
        risk = RiskAssessment(**valid_risk_data)
        assert risk.confidence == 0.0

        # Maximum confidence
        valid_risk_data["confidence"] = 1.0
        risk = RiskAssessment(**valid_risk_data)
        assert risk.confidence == 1.0

    def test_serialization(self, valid_risk_data):
        """Test complete serialization."""
        original = RiskAssessment(**valid_risk_data)

        json_data = original.model_dump()
        restored = RiskAssessment(**json_data)

        assert restored.risk_level == original.risk_level
        assert restored.risk_score == original.risk_score
        assert restored.confidence == original.confidence
        assert restored.location.latitude == original.location.latitude
        assert restored.environmental_factors.temperature == original.environmental_factors.temperature


class TestMalariaPrediction:
    """Test MalariaPrediction model."""

    @pytest.fixture
    def valid_prediction_data(self) -> dict[str, Any]:
        """Valid malaria prediction data."""
        return {
            "prediction_id": "pred_123",
            "location": GeographicLocation(
                latitude=-1.2921,
                longitude=36.8219,
                country="Kenya",
                region="Nairobi County"
            ),
            "prediction_date": date(2024, 6, 15),
            "risk_assessment": RiskAssessment(
                risk_level=RiskLevel.HIGH,
                risk_score=0.75,
                confidence=0.85,
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
                )
            )
        }

    def test_valid_prediction(self, valid_prediction_data):
        """Test creating valid malaria prediction."""
        prediction = MalariaPrediction(**valid_prediction_data)
        assert prediction.prediction_id == "pred_123"
        assert prediction.prediction_date == date(2024, 6, 15)
        assert isinstance(prediction.location, GeographicLocation)
        assert isinstance(prediction.risk_assessment, RiskAssessment)

    def test_prediction_serialization(self, valid_prediction_data):
        """Test prediction serialization."""
        original = MalariaPrediction(**valid_prediction_data)

        json_data = original.model_dump()
        restored = MalariaPrediction(**json_data)

        assert restored.prediction_id == original.prediction_id
        assert restored.prediction_date == original.prediction_date
        assert restored.location.latitude == original.location.latitude
        assert restored.risk_assessment.risk_level == original.risk_assessment.risk_level


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_extreme_coordinates(self):
        """Test extreme coordinate values."""
        # North Pole
        location = GeographicLocation(latitude=90.0, longitude=0.0, country="Arctic", region="North Pole")
        assert location.latitude == 90.0

        # South Pole
        location = GeographicLocation(latitude=-90.0, longitude=0.0, country="Antarctica", region="South Pole")
        assert location.latitude == -90.0

        # International Date Line
        location = GeographicLocation(latitude=0.0, longitude=180.0, country="Pacific", region="International Date Line")
        assert location.longitude == 180.0

    def test_extreme_environmental_conditions(self):
        """Test extreme environmental conditions."""
        # Desert conditions
        desert_factors = EnvironmentalFactors(
            temperature=45.0,
            rainfall=0.0,
            humidity=10.0,
            ndvi=0.05,
            elevation=400.0,
            wind_speed=15.0,
            solar_radiation=400.0,
            air_pressure=1000.0
        )
        assert desert_factors.temperature == 45.0
        assert desert_factors.rainfall == 0.0
        assert desert_factors.humidity == 10.0

        # Mountain conditions
        mountain_factors = EnvironmentalFactors(
            temperature=5.0,
            rainfall=200.0,
            humidity=90.0,
            ndvi=0.8,
            elevation=3000.0,
            wind_speed=25.0,
            solar_radiation=300.0,
            air_pressure=700.0
        )
        assert mountain_factors.elevation == 3000.0
        assert mountain_factors.air_pressure == 700.0

    def test_risk_level_consistency(self):
        """Test risk level and score consistency."""
        # Low risk should have low score
        low_risk = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_score=0.1,
            confidence=0.9,
            location=GeographicLocation(latitude=0.0, longitude=0.0, country="Test", region="Test"),
            environmental_factors=EnvironmentalFactors(
                temperature=20.0, rainfall=50.0, humidity=60.0, ndvi=0.3,
                elevation=500.0, wind_speed=5.0, solar_radiation=200.0, air_pressure=1013.0
            )
        )
        assert low_risk.risk_level == RiskLevel.LOW
        assert low_risk.risk_score == 0.1

        # Critical risk should have high score
        critical_risk = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            risk_score=0.95,
            confidence=0.85,
            location=GeographicLocation(latitude=0.0, longitude=0.0, country="Test", region="Test"),
            environmental_factors=EnvironmentalFactors(
                temperature=30.0, rainfall=150.0, humidity=85.0, ndvi=0.7,
                elevation=100.0, wind_speed=3.0, solar_radiation=350.0, air_pressure=1010.0
            )
        )
        assert critical_risk.risk_level == RiskLevel.CRITICAL
        assert critical_risk.risk_score == 0.95

    def test_model_validation_errors(self):
        """Test that invalid data raises validation errors."""
        with pytest.raises(ValidationError):  # Should raise validation error
            # Invalid risk score (> 1.0)
            RiskAssessment(
                risk_level=RiskLevel.HIGH,
                risk_score=1.5,  # Invalid: > 1.0
                confidence=0.85,
                location=GeographicLocation(latitude=0.0, longitude=0.0, country="Test", region="Test"),
                environmental_factors=EnvironmentalFactors(
                    temperature=25.0, rainfall=100.0, humidity=70.0, ndvi=0.5,
                    elevation=1000.0, wind_speed=10.0, solar_radiation=250.0, air_pressure=1013.0
                )
            )


class TestModelFieldValidation:
    """Test field-level validation and constraints."""

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Test that missing required fields raise validation errors
        with pytest.raises(ValidationError):
            EnvironmentalFactors()  # Missing all required fields

        with pytest.raises(ValidationError):
            GeographicLocation(latitude=0.0)  # Missing longitude, country, region

    def test_optional_fields(self):
        """Test optional fields behavior."""
        # Create minimal valid objects to test optional fields
        location = GeographicLocation(
            latitude=0.0,
            longitude=0.0,
            country="Test",
            region="Test"
        )
        assert location.latitude == 0.0
        assert location.longitude == 0.0
        assert location.country == "Test"
        assert location.region == "Test"

    def test_field_types(self):
        """Test field type validation."""
        # Test that incorrect types are rejected
        with pytest.raises(ValidationError):
            GeographicLocation(
                latitude="not_a_number",  # Should be float
                longitude=0.0,
                country="Test",
                region="Test"
            )
