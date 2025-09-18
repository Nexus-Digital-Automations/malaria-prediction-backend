"""
Final comprehensive unit tests for actual data models.

Tests the real Pydantic models in the codebase based on their actual structure.
"""

from datetime import UTC, date, datetime
from typing import Any

import pytest

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
        assert RiskLevel.HIGH.value == "high"


class TestEnvironmentalFactors:
    """Test EnvironmentalFactors model with correct field names."""

    @pytest.fixture
    def valid_env_factors(self) -> dict[str, Any]:
        """Valid environmental factors data with correct field names."""
        return {
            "mean_temperature": 25.5,
            "min_temperature": 20.0,
            "max_temperature": 30.0,
            "monthly_rainfall": 120.0,
            "relative_humidity": 75.0,
            "ndvi": 0.6,
            "elevation": 1200.0,
            "population_density": 150.0
        }

    def test_valid_environmental_factors(self, valid_env_factors):
        """Test creating valid environmental factors."""
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.mean_temperature == 25.5
        assert factors.min_temperature == 20.0
        assert factors.max_temperature == 30.0
        assert factors.monthly_rainfall == 120.0
        assert factors.relative_humidity == 75.0
        assert factors.ndvi == 0.6
        assert factors.elevation == 1200.0
        assert factors.population_density == 150.0

    def test_temperature_validation(self, valid_env_factors):
        """Test temperature validation ranges."""
        # Valid temperatures
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.mean_temperature == 25.5

        # Test temperature bounds
        valid_env_factors["mean_temperature"] = -5.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.mean_temperature == -5.0

        valid_env_factors["mean_temperature"] = 45.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.mean_temperature == 45.0

    def test_temperature_range_validation(self):
        """Test that max_temperature >= min_temperature."""
        # Valid temperature range
        factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=100.0,
            relative_humidity=70.0,
            elevation=1000.0
        )
        assert factors.min_temperature <= factors.max_temperature

        # Invalid temperature range should raise error
        with pytest.raises(ValueError, match="Max temperature must be >= min temperature"):
            EnvironmentalFactors(
                mean_temperature=25.0,
                min_temperature=30.0,  # Higher than max
                max_temperature=25.0,
                monthly_rainfall=100.0,
                relative_humidity=70.0,
                elevation=1000.0
            )

    def test_rainfall_validation(self, valid_env_factors):
        """Test rainfall validation."""
        # Zero rainfall should be valid
        valid_env_factors["monthly_rainfall"] = 0.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.monthly_rainfall == 0.0

        # High rainfall
        valid_env_factors["monthly_rainfall"] = 500.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.monthly_rainfall == 500.0

    def test_humidity_validation(self, valid_env_factors):
        """Test humidity validation."""
        # Test 0% humidity
        valid_env_factors["relative_humidity"] = 0.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.relative_humidity == 0.0

        # Test 100% humidity
        valid_env_factors["relative_humidity"] = 100.0
        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.relative_humidity == 100.0

    def test_optional_fields(self, valid_env_factors):
        """Test optional fields like NDVI and population density."""
        # Remove optional fields
        del valid_env_factors["ndvi"]
        del valid_env_factors["population_density"]

        factors = EnvironmentalFactors(**valid_env_factors)
        assert factors.ndvi is None
        assert factors.population_density is None

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

        assert restored.mean_temperature == original.mean_temperature
        assert restored.monthly_rainfall == original.monthly_rainfall
        assert restored.relative_humidity == original.relative_humidity
        assert restored.ndvi == original.ndvi


class TestGeographicLocation:
    """Test GeographicLocation model with correct field names."""

    def test_valid_location(self):
        """Test creating valid geographic location."""
        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi County",
            country_code="KE",
            admin_level="County"
        )
        assert location.latitude == -1.2921
        assert location.longitude == 36.8219
        assert location.area_name == "Nairobi County"
        assert location.country_code == "KE"
        assert location.admin_level == "County"

    def test_latitude_bounds(self):
        """Test latitude validation bounds."""
        # Valid latitudes
        location = GeographicLocation(
            latitude=-90.0, longitude=0.0, area_name="South Pole", country_code="AQ"
        )
        assert location.latitude == -90.0

        location = GeographicLocation(
            latitude=90.0, longitude=0.0, area_name="North Pole", country_code="GL"
        )
        assert location.latitude == 90.0

    def test_longitude_bounds(self):
        """Test longitude validation bounds."""
        # Valid longitudes
        location = GeographicLocation(
            latitude=0.0, longitude=-180.0, area_name="Pacific", country_code="XX"
        )
        assert location.longitude == -180.0

        location = GeographicLocation(
            latitude=0.0, longitude=180.0, area_name="Pacific", country_code="XX"
        )
        assert location.longitude == 180.0

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Missing area_name should raise error
        with pytest.raises(Exception):
            GeographicLocation(
                latitude=0.0,
                longitude=0.0,
                country_code="KE"
                # Missing area_name
            )

        # Missing country_code should raise error
        with pytest.raises(Exception):
            GeographicLocation(
                latitude=0.0,
                longitude=0.0,
                area_name="Test Area"
                # Missing country_code
            )

    def test_optional_admin_level(self):
        """Test optional admin_level field."""
        location = GeographicLocation(
            latitude=0.0,
            longitude=0.0,
            area_name="Test Area",
            country_code="KE"
            # admin_level is optional
        )
        assert location.admin_level is None

    def test_serialization(self):
        """Test JSON serialization."""
        original = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi County",
            country_code="KE",
            admin_level="County"
        )

        json_data = original.model_dump()
        restored = GeographicLocation(**json_data)

        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude
        assert restored.area_name == original.area_name
        assert restored.country_code == original.country_code


class TestRiskAssessment:
    """Test RiskAssessment model with correct field structure."""

    @pytest.fixture
    def valid_risk_data(self) -> dict[str, Any]:
        """Valid risk assessment data."""
        return {
            "risk_score": 0.75,
            "risk_level": RiskLevel.HIGH,
            "confidence": 0.85,
            "temperature_factor": 0.8,
            "rainfall_factor": 0.7,
            "humidity_factor": 0.9,
            "vegetation_factor": 0.6,
            "elevation_factor": 0.5,
            "model_version": "2.0.0"
        }

    def test_valid_risk_assessment(self, valid_risk_data):
        """Test creating valid risk assessment."""
        risk = RiskAssessment(**valid_risk_data)
        assert risk.risk_score == 0.75
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.confidence == 0.85
        assert risk.temperature_factor == 0.8
        assert risk.rainfall_factor == 0.7
        assert risk.humidity_factor == 0.9
        assert risk.vegetation_factor == 0.6
        assert risk.elevation_factor == 0.5
        assert risk.model_version == "2.0.0"

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

    def test_factor_validation(self, valid_risk_data):
        """Test that all factors are in valid range [0, 1]."""
        factors = [
            "temperature_factor",
            "rainfall_factor",
            "humidity_factor",
            "vegetation_factor",
            "elevation_factor"
        ]

        for factor in factors:
            # Test minimum value
            valid_risk_data[factor] = 0.0
            risk = RiskAssessment(**valid_risk_data)
            assert getattr(risk, factor) == 0.0

            # Test maximum value
            valid_risk_data[factor] = 1.0
            risk = RiskAssessment(**valid_risk_data)
            assert getattr(risk, factor) == 1.0

    def test_default_values(self):
        """Test default values for optional fields."""
        minimal_risk = RiskAssessment(
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.8,
            temperature_factor=0.5,
            rainfall_factor=0.5,
            humidity_factor=0.5,
            vegetation_factor=0.5,
            elevation_factor=0.5
        )

        # Should have default assessment_date and model_version
        assert minimal_risk.assessment_date is not None
        assert minimal_risk.model_version == "1.0.0"  # Default version

    def test_assessment_date_auto_generation(self, valid_risk_data):
        """Test that assessment_date is automatically generated."""
        before_creation = datetime.now(UTC)
        risk = RiskAssessment(**valid_risk_data)
        after_creation = datetime.now(UTC)

        assert before_creation <= risk.assessment_date <= after_creation

    def test_serialization(self, valid_risk_data):
        """Test complete serialization."""
        original = RiskAssessment(**valid_risk_data)

        json_data = original.model_dump()
        restored = RiskAssessment(**json_data)

        assert restored.risk_score == original.risk_score
        assert restored.risk_level == original.risk_level
        assert restored.confidence == original.confidence
        assert restored.temperature_factor == original.temperature_factor


class TestMalariaPrediction:
    """Test MalariaPrediction model with complete structure."""

    @pytest.fixture
    def valid_prediction_data(self) -> dict[str, Any]:
        """Valid malaria prediction data."""
        return {
            "location": GeographicLocation(
                latitude=-1.2921,
                longitude=36.8219,
                area_name="Nairobi County",
                country_code="KE",
                admin_level="County"
            ),
            "environmental_data": EnvironmentalFactors(
                mean_temperature=25.5,
                min_temperature=20.0,
                max_temperature=30.0,
                monthly_rainfall=120.0,
                relative_humidity=75.0,
                ndvi=0.6,
                elevation=1200.0,
                population_density=150.0
            ),
            "risk_assessment": RiskAssessment(
                risk_score=0.75,
                risk_level=RiskLevel.HIGH,
                confidence=0.85,
                temperature_factor=0.8,
                rainfall_factor=0.7,
                humidity_factor=0.9,
                vegetation_factor=0.6,
                elevation_factor=0.5
            ),
            "prediction_date": date(2024, 6, 15),
            "time_horizon_days": 30,
            "data_sources": ["ERA5", "CHIRPS", "MODIS"]
        }

    def test_valid_prediction(self, valid_prediction_data):
        """Test creating valid malaria prediction."""
        prediction = MalariaPrediction(**valid_prediction_data)
        assert isinstance(prediction.location, GeographicLocation)
        assert isinstance(prediction.environmental_data, EnvironmentalFactors)
        assert isinstance(prediction.risk_assessment, RiskAssessment)
        assert prediction.prediction_date == date(2024, 6, 15)
        assert prediction.time_horizon_days == 30
        assert prediction.data_sources == ["ERA5", "CHIRPS", "MODIS"]

    def test_time_horizon_validation(self, valid_prediction_data):
        """Test time horizon validation."""
        # Minimum time horizon
        valid_prediction_data["time_horizon_days"] = 1
        prediction = MalariaPrediction(**valid_prediction_data)
        assert prediction.time_horizon_days == 1

        # Maximum time horizon
        valid_prediction_data["time_horizon_days"] = 365
        prediction = MalariaPrediction(**valid_prediction_data)
        assert prediction.time_horizon_days == 365

        # Invalid time horizon should raise error
        with pytest.raises(Exception):
            valid_prediction_data["time_horizon_days"] = 0  # Too low
            MalariaPrediction(**valid_prediction_data)

        with pytest.raises(Exception):
            valid_prediction_data["time_horizon_days"] = 400  # Too high
            MalariaPrediction(**valid_prediction_data)

    def test_default_values(self):
        """Test default values for optional fields."""
        minimal_prediction = MalariaPrediction(
            location=GeographicLocation(
                latitude=0.0,
                longitude=0.0,
                area_name="Test",
                country_code="XX"
            ),
            environmental_data=EnvironmentalFactors(
                mean_temperature=25.0,
                min_temperature=20.0,
                max_temperature=30.0,
                monthly_rainfall=100.0,
                relative_humidity=70.0,
                elevation=1000.0
            ),
            risk_assessment=RiskAssessment(
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.8,
                temperature_factor=0.5,
                rainfall_factor=0.5,
                humidity_factor=0.5,
                vegetation_factor=0.5,
                elevation_factor=0.5
            ),
            prediction_date=date(2024, 6, 15),
            time_horizon_days=30
        )

        # Should have default created_at and empty data_sources
        assert minimal_prediction.created_at is not None
        assert minimal_prediction.data_sources == []

    def test_created_at_auto_generation(self, valid_prediction_data):
        """Test that created_at is automatically generated."""
        before_creation = datetime.now(UTC)
        prediction = MalariaPrediction(**valid_prediction_data)
        after_creation = datetime.now(UTC)

        assert before_creation <= prediction.created_at <= after_creation

    def test_prediction_serialization(self, valid_prediction_data):
        """Test complete prediction serialization."""
        original = MalariaPrediction(**valid_prediction_data)

        json_data = original.model_dump()
        restored = MalariaPrediction(**json_data)

        assert restored.prediction_date == original.prediction_date
        assert restored.time_horizon_days == original.time_horizon_days
        assert restored.location.latitude == original.location.latitude
        assert restored.risk_assessment.risk_score == original.risk_assessment.risk_score


class TestModelIntegration:
    """Test integration between models."""

    def test_complete_prediction_workflow(self):
        """Test creating a complete prediction with all components."""
        # Create environmental data
        env_data = EnvironmentalFactors(
            mean_temperature=28.0,
            min_temperature=22.0,
            max_temperature=34.0,
            monthly_rainfall=180.0,
            relative_humidity=85.0,
            ndvi=0.7,
            elevation=800.0,
            population_density=200.0
        )

        # Create location
        location = GeographicLocation(
            latitude=-4.0435,  # Kisumu, Kenya
            longitude=39.6682,
            area_name="Kisumu County",
            country_code="KE",
            admin_level="County"
        )

        # Create risk assessment
        risk = RiskAssessment(
            risk_score=0.85,
            risk_level=RiskLevel.HIGH,
            confidence=0.90,
            temperature_factor=0.9,
            rainfall_factor=0.8,
            humidity_factor=0.95,
            vegetation_factor=0.8,
            elevation_factor=0.7,
            model_version="2.1.0"
        )

        # Create complete prediction
        prediction = MalariaPrediction(
            location=location,
            environmental_data=env_data,
            risk_assessment=risk,
            prediction_date=date(2024, 7, 1),
            time_horizon_days=14,
            data_sources=["ERA5", "CHIRPS", "MODIS", "WorldPop"]
        )

        # Verify the complete prediction
        assert prediction.risk_assessment.risk_level == RiskLevel.HIGH
        assert prediction.environmental_data.mean_temperature == 28.0
        assert prediction.location.area_name == "Kisumu County"
        assert len(prediction.data_sources) == 4

    def test_risk_level_score_consistency(self):
        """Test that risk levels are consistent with scores."""
        test_cases = [
            (RiskLevel.LOW, 0.15),
            (RiskLevel.MEDIUM, 0.45),
            (RiskLevel.HIGH, 0.75),
            (RiskLevel.CRITICAL, 0.95)
        ]

        for risk_level, risk_score in test_cases:
            risk = RiskAssessment(
                risk_score=risk_score,
                risk_level=risk_level,
                confidence=0.8,
                temperature_factor=0.5,
                rainfall_factor=0.5,
                humidity_factor=0.5,
                vegetation_factor=0.5,
                elevation_factor=0.5
            )

            assert risk.risk_level == risk_level
            assert risk.risk_score == risk_score
