"""Tests for malaria prediction data models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
    RiskLevel,
)


class TestEnvironmentalFactors:
    """Tests for EnvironmentalFactors model."""

    def test_valid_environmental_factors(self):
        """Test creating valid environmental factors."""
        factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            ndvi=0.6,
            evi=0.5,
            elevation=800.0,
            slope=15.0,
            population_density=250.0,
        )

        assert factors.mean_temperature == 25.0
        assert factors.monthly_rainfall == 150.0
        assert factors.relative_humidity == 75.0
        assert factors.ndvi == 0.6
        assert factors.elevation == 800.0

    def test_temperature_range_validation(self):
        """Test temperature range validation."""
        # Valid temperature range
        factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        assert factors.max_temperature == 30.0

        # Invalid: max < min temperature
        with pytest.raises(
            ValidationError, match="Max temperature must be >= min temperature"
        ):
            EnvironmentalFactors(
                mean_temperature=25.0,
                min_temperature=30.0,
                max_temperature=20.0,  # Invalid
                monthly_rainfall=150.0,
                relative_humidity=75.0,
                elevation=800.0,
            )

    def test_field_constraints(self):
        """Test field constraint validation."""
        # Temperature out of range
        with pytest.raises(ValidationError):
            EnvironmentalFactors(
                mean_temperature=60.0,  # Too high
                min_temperature=20.0,
                max_temperature=30.0,
                monthly_rainfall=150.0,
                relative_humidity=75.0,
                elevation=800.0,
            )

        # Negative rainfall
        with pytest.raises(ValidationError):
            EnvironmentalFactors(
                mean_temperature=25.0,
                min_temperature=20.0,
                max_temperature=30.0,
                monthly_rainfall=-50.0,  # Invalid
                relative_humidity=75.0,
                elevation=800.0,
            )

        # Humidity over 100%
        with pytest.raises(ValidationError):
            EnvironmentalFactors(
                mean_temperature=25.0,
                min_temperature=20.0,
                max_temperature=30.0,
                monthly_rainfall=150.0,
                relative_humidity=150.0,  # Invalid
                elevation=800.0,
            )

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
            # ndvi, evi, slope, population_density are None
        )

        assert factors.ndvi is None
        assert factors.evi is None
        assert factors.slope is None
        assert factors.population_density is None


class TestGeographicLocation:
    """Tests for GeographicLocation model."""

    def test_valid_location(self):
        """Test creating valid geographic location."""
        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi, Kenya",
            country_code="KE",
            admin_level="county",
        )

        assert location.latitude == -1.2921
        assert location.longitude == 36.8219
        assert location.area_name == "Nairobi, Kenya"
        assert location.country_code == "KE"

    def test_coordinate_constraints(self):
        """Test latitude/longitude constraints."""
        # Valid coordinates
        location = GeographicLocation(
            latitude=0.0, longitude=0.0, area_name="Test Area", country_code="XX"
        )
        assert location.latitude == 0.0

        # Invalid latitude
        with pytest.raises(ValidationError):
            GeographicLocation(
                latitude=95.0,  # Too high
                longitude=0.0,
                area_name="Test Area",
                country_code="XX",
            )

        # Invalid longitude
        with pytest.raises(ValidationError):
            GeographicLocation(
                latitude=0.0,
                longitude=-200.0,  # Too low
                area_name="Test Area",
                country_code="XX",
            )

    def test_string_constraints(self):
        """Test string field constraints."""
        # Empty area name should fail
        with pytest.raises(ValidationError):
            GeographicLocation(
                latitude=0.0,
                longitude=0.0,
                area_name="",  # Too short
                country_code="XX",
            )

        # Short country code should fail
        with pytest.raises(ValidationError):
            GeographicLocation(
                latitude=0.0,
                longitude=0.0,
                area_name="Test Area",
                country_code="X",  # Too short
            )


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_valid_risk_assessment(self):
        """Test creating valid risk assessment."""
        assessment = RiskAssessment(
            risk_score=0.75,
            risk_level=RiskLevel.HIGH,
            confidence=0.85,
            temperature_factor=0.9,
            rainfall_factor=0.8,
            humidity_factor=0.7,
            vegetation_factor=0.6,
            elevation_factor=0.8,
        )

        assert assessment.risk_score == 0.75
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.confidence == 0.85
        assert isinstance(assessment.assessment_date, datetime)

    def test_score_constraints(self):
        """Test that all scores are constrained to 0.0-1.0."""
        # Valid scores at boundaries
        assessment = RiskAssessment(
            risk_score=0.0,
            risk_level=RiskLevel.LOW,
            confidence=1.0,
            temperature_factor=0.0,
            rainfall_factor=1.0,
            humidity_factor=0.5,
            vegetation_factor=0.5,
            elevation_factor=0.5,
        )
        assert assessment.risk_score == 0.0
        assert assessment.confidence == 1.0

        # Invalid risk score
        with pytest.raises(ValidationError):
            RiskAssessment(
                risk_score=1.5,  # Too high
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                temperature_factor=0.5,
                rainfall_factor=0.5,
                humidity_factor=0.5,
                vegetation_factor=0.5,
                elevation_factor=0.5,
            )

    def test_default_values(self):
        """Test default values are set correctly."""
        assessment = RiskAssessment(
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.8,
            temperature_factor=0.5,
            rainfall_factor=0.5,
            humidity_factor=0.5,
            vegetation_factor=0.5,
            elevation_factor=0.5,
        )

        assert isinstance(assessment.assessment_date, datetime)
        assert assessment.model_version == "1.0.0"


class TestMalariaPrediction:
    """Tests for MalariaPrediction model."""

    def test_valid_prediction(self):
        """Test creating complete malaria prediction."""
        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi, Kenya",
            country_code="KE",
        )

        env_factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )

        risk_assessment = RiskAssessment(
            risk_score=0.75,
            risk_level=RiskLevel.HIGH,
            confidence=0.85,
            temperature_factor=0.9,
            rainfall_factor=0.8,
            humidity_factor=0.7,
            vegetation_factor=0.6,
            elevation_factor=0.8,
        )

        prediction = MalariaPrediction(
            location=location,
            environmental_data=env_factors,
            risk_assessment=risk_assessment,
            prediction_date=date(2024, 1, 15),
            time_horizon_days=30,
            data_sources=["ERA5", "CHIRPS"],
        )

        assert prediction.location.area_name == "Nairobi, Kenya"
        assert prediction.environmental_data.mean_temperature == 25.0
        assert prediction.risk_assessment.risk_level == RiskLevel.HIGH
        assert prediction.prediction_date == date(2024, 1, 15)
        assert prediction.time_horizon_days == 30
        assert "ERA5" in prediction.data_sources

    def test_time_horizon_constraints(self):
        """Test time horizon validation."""
        location = GeographicLocation(
            latitude=0.0, longitude=0.0, area_name="Test", country_code="XX"
        )
        env_factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        risk_assessment = RiskAssessment(
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.8,
            temperature_factor=0.5,
            rainfall_factor=0.5,
            humidity_factor=0.5,
            vegetation_factor=0.5,
            elevation_factor=0.5,
        )

        # Valid time horizon
        prediction = MalariaPrediction(
            location=location,
            environmental_data=env_factors,
            risk_assessment=risk_assessment,
            prediction_date=date.today(),
            time_horizon_days=30,
        )
        assert prediction.time_horizon_days == 30

        # Invalid time horizon
        with pytest.raises(ValidationError):
            MalariaPrediction(
                location=location,
                environmental_data=env_factors,
                risk_assessment=risk_assessment,
                prediction_date=date.today(),
                time_horizon_days=400,  # Too long
            )

    def test_default_values(self):
        """Test default values are set correctly."""
        location = GeographicLocation(
            latitude=0.0, longitude=0.0, area_name="Test", country_code="XX"
        )
        env_factors = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        risk_assessment = RiskAssessment(
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.8,
            temperature_factor=0.5,
            rainfall_factor=0.5,
            humidity_factor=0.5,
            vegetation_factor=0.5,
            elevation_factor=0.5,
        )

        prediction = MalariaPrediction(
            location=location,
            environmental_data=env_factors,
            risk_assessment=risk_assessment,
            prediction_date=date.today(),
            time_horizon_days=30,  # Required field
        )

        assert isinstance(prediction.created_at, datetime)
        assert prediction.data_sources == []
