"""
Enterprise-Grade Comprehensive Risk Calculator Test Suite.

Tests all malaria risk calculation logic including temperature, rainfall,
humidity, vegetation, and elevation factors. Covers edge cases, boundary
conditions, and integration scenarios.

Target Coverage: 90%+ for risk calculator module (critical business logic)
"""

import math
from datetime import date

import pytest

from malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    RiskLevel,
)
from malaria_predictor.services.risk_calculator import RiskCalculator


class TestTemperatureFactor:
    """Test temperature-based risk calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_optimal_temperature(self):
        """Test risk at optimal temperature (25°C)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_temperature_factor(env)
        assert factor == 1.0, "Optimal temperature should give maximum factor"

    def test_minimum_transmission_temperature_boundary(self):
        """Test risk at minimum transmission temperature (18°C)."""
        env = EnvironmentalFactors(
            mean_temperature=18.0,
            min_temperature=18.0-2.0,
            max_temperature=18.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_temperature_factor(env)
        assert factor > 0.0, "Minimum temp should still allow transmission"
        assert factor < 1.0, "Minimum temp should not be optimal"

    def test_below_minimum_temperature(self):
        """Test that temperatures below 18°C prevent transmission."""
        temps_below_min = [17.9, 15.0, 10.0, 5.0, 0.0, -5.0]

        for temp in temps_below_min:
            env = EnvironmentalFactors(
                mean_temperature=temp,
                min_temperature=temp - 2.0,
                max_temperature=temp + 2.0,
                monthly_rainfall=150.0,
                relative_humidity=70.0,
                elevation=500.0,
            )

            factor = self.calculator.calculate_temperature_factor(env)
            assert factor == 0.0, f"Temperature {temp}°C should prevent transmission"

    def test_maximum_transmission_temperature_boundary(self):
        """Test risk at maximum transmission temperature (34°C)."""
        env = EnvironmentalFactors(
            mean_temperature=34.0,
            min_temperature=34.0-2.0,
            max_temperature=34.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_temperature_factor(env)
        assert factor > 0.0, "Maximum temp should still allow transmission"
        assert factor < 1.0, "Maximum temp should not be optimal"

    def test_above_maximum_temperature(self):
        """Test that temperatures above 34°C prevent transmission."""
        temps_above_max = [34.1, 35.0, 40.0, 45.0]

        for temp in temps_above_max:
            env = EnvironmentalFactors(
                mean_temperature=temp,
                min_temperature=temp - 2.0,
                max_temperature=temp + 2.0,
                monthly_rainfall=150.0,
                relative_humidity=70.0,
                elevation=500.0,
            )

            factor = self.calculator.calculate_temperature_factor(env)
            assert factor == 0.0, f"Temperature {temp}°C should prevent transmission"

    def test_temperature_gaussian_decay(self):
        """Test that temperature factor follows Gaussian-like decay from optimal."""
        env_optimal = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_near_optimal = EnvironmentalFactors(
            mean_temperature=23.0,
            min_temperature=23.0-2.0,
            max_temperature=23.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_far_optimal = EnvironmentalFactors(
            mean_temperature=20.0,
            min_temperature=20.0-2.0,
            max_temperature=20.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor_optimal = self.calculator.calculate_temperature_factor(env_optimal)
        factor_near = self.calculator.calculate_temperature_factor(env_near_optimal)
        factor_far = self.calculator.calculate_temperature_factor(env_far_optimal)

        assert factor_optimal > factor_near > factor_far, \
            "Temperature factor should decay with distance from optimal"

    def test_temperature_symmetry(self):
        """Test that temperature decay is not perfectly symmetric due to different ranges."""
        env_below = EnvironmentalFactors(
            mean_temperature=22.0,
            min_temperature=22.0-2.0,
            max_temperature=22.0+2.0,  # 3°C below optimal
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_above = EnvironmentalFactors(
            mean_temperature=28.0,
            min_temperature=28.0-2.0,
            max_temperature=28.0+2.0,  # 3°C above optimal
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor_below = self.calculator.calculate_temperature_factor(env_below)
        factor_above = self.calculator.calculate_temperature_factor(env_above)

        # Factors should be similar but not identical due to range differences
        assert 0.5 < factor_below / factor_above < 2.0, \
            "Temperature factors should be comparable on both sides of optimal"


class TestRainfallFactor:
    """Test rainfall-based risk calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_optimal_rainfall(self):
        """Test risk at optimal rainfall (200mm/month)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=200.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_rainfall_factor(env)
        assert factor == 1.0, "Optimal rainfall should give maximum factor"

    def test_below_minimum_rainfall(self):
        """Test that rainfall below 80mm prevents sustained transmission."""
        rainfalls_below_min = [79.9, 70.0, 50.0, 20.0, 0.0]

        for rainfall in rainfalls_below_min:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=rainfall,
                relative_humidity=70.0,
                elevation=500.0,
            )

            factor = self.calculator.calculate_rainfall_factor(env)
            assert factor == 0.0, f"Rainfall {rainfall}mm should prevent transmission"

    def test_minimum_rainfall_boundary(self):
        """Test risk at minimum rainfall threshold (80mm)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=80.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_rainfall_factor(env)
        assert factor == 0.0, "Exactly at minimum should be zero (or very low)"

    def test_rainfall_linear_increase(self):
        """Test linear increase from minimum to optimal rainfall."""
        env_min = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=80.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_mid = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=140.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_optimal = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=200.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor_min = self.calculator.calculate_rainfall_factor(env_min)
        factor_mid = self.calculator.calculate_rainfall_factor(env_mid)
        factor_optimal = self.calculator.calculate_rainfall_factor(env_optimal)

        assert factor_min < factor_mid < factor_optimal, \
            "Rainfall factor should increase linearly from min to optimal"

    def test_excessive_rainfall_diminishing_returns(self):
        """Test diminishing returns above optimal rainfall."""
        env_optimal = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=200.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_high = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=400.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_extreme = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=800.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        factor_optimal = self.calculator.calculate_rainfall_factor(env_optimal)
        factor_high = self.calculator.calculate_rainfall_factor(env_high)
        factor_extreme = self.calculator.calculate_rainfall_factor(env_extreme)

        # Excessive rain should reduce risk slightly (washout effect)
        assert factor_optimal >= factor_high, \
            "Excessive rainfall should have diminishing returns"
        assert factor_high >= factor_extreme, \
            "Very excessive rainfall should reduce risk further"


class TestHumidityFactor:
    """Test humidity-based risk calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_optimal_humidity(self):
        """Test risk at optimal humidity (80%)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=80.0,
            elevation=500.0,
        )

        factor = self.calculator.calculate_humidity_factor(env)
        assert factor == 1.0, "Optimal humidity should give maximum factor"

    def test_below_minimum_humidity(self):
        """Test that humidity below 60% prevents mosquito survival."""
        humidities_below_min = [59.9, 50.0, 30.0, 10.0, 0.0]

        for humidity in humidities_below_min:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=150.0,
                relative_humidity=humidity,
                elevation=500.0,
            )

            factor = self.calculator.calculate_humidity_factor(env)
            assert factor == 0.0, f"Humidity {humidity}% should prevent survival"

    def test_humidity_linear_increase(self):
        """Test linear increase from minimum to optimal humidity."""
        env_min = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=60.0,
            elevation=500.0,
        )
        env_mid = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        env_optimal = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=80.0,
            elevation=500.0,
        )

        factor_min = self.calculator.calculate_humidity_factor(env_min)
        factor_mid = self.calculator.calculate_humidity_factor(env_mid)
        factor_optimal = self.calculator.calculate_humidity_factor(env_optimal)

        assert factor_min < factor_mid < factor_optimal, \
            "Humidity factor should increase linearly from min to optimal"

    def test_very_high_humidity(self):
        """Test that very high humidity (>80%) maintains high risk."""
        humidities_high = [85.0, 90.0, 95.0, 100.0]

        for humidity in humidities_high:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=150.0,
                relative_humidity=humidity,
                elevation=500.0,
            )

            factor = self.calculator.calculate_humidity_factor(env)
            assert factor == 1.0, f"Humidity {humidity}% should maintain maximum risk"


class TestVegetationFactor:
    """Test vegetation-based risk calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_optimal_vegetation_ndvi(self):
        """Test risk at optimal vegetation (NDVI 0.3-0.7 normalized)."""
        # NDVI range is -1 to 1, optimal 0.3-0.7 normalized = -0.4 to 0.4 raw
        optimal_ndvi_values = [-0.2, 0.0, 0.2, 0.4]

        for ndvi in optimal_ndvi_values:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=150.0,
                relative_humidity=70.0,
                elevation=500.0,
                ndvi=ndvi,
            )

            factor = self.calculator.calculate_vegetation_factor(env)
            assert factor == 1.0, f"NDVI {ndvi} should be optimal"

    def test_low_vegetation_limited_habitat(self):
        """Test that low vegetation reduces risk due to limited habitat."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
            ndvi=-0.8,  # Very low vegetation
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert factor < 0.5, "Very low vegetation should reduce risk significantly"

    def test_high_vegetation_reduced_access(self):
        """Test that very high vegetation reduces risk slightly."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
            ndvi=0.9,  # Very high vegetation
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert 0.5 <= factor < 1.0, "Very high vegetation should reduce risk slightly"

    def test_missing_vegetation_data(self):
        """Test neutral factor when vegetation data unavailable."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
            ndvi=None,
            evi=None,
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert factor == 0.5, "Missing vegetation data should give neutral factor"

    def test_evi_fallback(self):
        """Test that EVI is used when NDVI unavailable."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
            ndvi=None,
            evi=0.0,  # Moderate EVI
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert factor == 1.0, "EVI should be used as fallback for NDVI"


class TestElevationFactor:
    """Test elevation-based risk calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_low_elevation_high_risk(self):
        """Test high risk at low elevations (<1200m)."""
        low_elevations = [0.0, 500.0, 1000.0, 1200.0]

        for elev in low_elevations:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=150.0,
                relative_humidity=70.0,
                elevation=elev,
            )

            factor = self.calculator.calculate_elevation_factor(env)
            assert factor == 1.0, f"Elevation {elev}m should have maximum risk"

    def test_medium_elevation_gradual_decrease(self):
        """Test gradual risk decrease at medium elevations (1200-1600m)."""
        env_1200 = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=1200.0,
        )
        env_1400 = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=1400.0,
        )
        env_1600 = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=1600.0,
        )

        factor_1200 = self.calculator.calculate_elevation_factor(env_1200)
        factor_1400 = self.calculator.calculate_elevation_factor(env_1400)
        factor_1600 = self.calculator.calculate_elevation_factor(env_1600)

        assert factor_1200 > factor_1400 > factor_1600, \
            "Risk should decrease linearly in medium elevation range"

    def test_high_elevation_low_risk(self):
        """Test low risk at high elevations (1600-2000m)."""
        env_1800 = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=1800.0,
        )

        factor = self.calculator.calculate_elevation_factor(env_1800)
        assert 0.1 < factor < 0.7, "High elevation should have low to medium risk"

    def test_very_high_elevation_minimal_risk(self):
        """Test minimal risk at very high elevations (>2000m)."""
        very_high_elevations = [2000.0, 2500.0, 3000.0, 4000.0]

        for elev in very_high_elevations:
            env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
                monthly_rainfall=150.0,
                relative_humidity=70.0,
                elevation=elev,
            )

            factor = self.calculator.calculate_elevation_factor(env)
            assert factor == pytest.approx(0.1, abs=1e-9), f"Elevation {elev}m should have minimal risk"


class TestOverallRiskCalculation:
    """Test overall risk calculation integrating all factors."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_perfect_conditions_critical_risk(self):
        """Test that perfect conditions result in critical risk."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,  # Optimal
            monthly_rainfall=200.0,  # Optimal
            relative_humidity=80.0,  # Optimal
            elevation=500.0,  # Low elevation
            ndvi=0.0,  # Optimal vegetation
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_level == RiskLevel.CRITICAL
        assert assessment.risk_score >= 0.8
        assert assessment.confidence >= 0.8

    def test_no_temperature_no_transmission(self):
        """Test that unsuitable temperature prevents all transmission."""
        env = EnvironmentalFactors(
            mean_temperature=10.0,
            min_temperature=10.0-2.0,
            max_temperature=10.0+2.0,  # Too cold
            monthly_rainfall=200.0,  # Perfect
            relative_humidity=80.0,  # Perfect
            elevation=500.0,  # Perfect
            ndvi=0.0,  # Perfect
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_score == 0.0
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.temperature_factor == 0.0

    def test_mixed_conditions_medium_risk(self):
        """Test mixed conditions result in medium risk."""
        env = EnvironmentalFactors(
            mean_temperature=23.0,
            min_temperature=23.0-2.0,
            max_temperature=23.0+2.0,  # Good but not optimal
            monthly_rainfall=120.0,  # Moderate
            relative_humidity=68.0,  # Moderate
            elevation=1300.0,  # Medium elevation
            ndvi=-0.2,  # Moderate vegetation
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert 0.3 <= assessment.risk_score < 0.8

    def test_factor_weights(self):
        """Test that temperature has highest weight (40%)."""
        # Temperature weight should dominate the calculation
        env_good_temp = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,  # Optimal (40% weight)
            monthly_rainfall=90.0,  # Low (25% weight)
            relative_humidity=62.0,  # Low (15% weight)
            elevation=1800.0,  # High elevation (10% weight)
            ndvi=-0.8,  # Low vegetation (10% weight)
        )

        assessment = self.calculator.calculate_overall_risk(env_good_temp)

        # Despite poor other factors, good temperature should maintain moderate risk
        assert assessment.risk_score > 0.2, \
            "Good temperature should dominate despite poor other factors"

    def test_all_factors_present_in_assessment(self):
        """Test that all factor values are included in assessment."""
        env = EnvironmentalFactors(
            mean_temperature=24.0,
            min_temperature=24.0-2.0,
            max_temperature=24.0+2.0,
            monthly_rainfall=180.0,
            relative_humidity=75.0,
            elevation=800.0,
            ndvi=0.1,
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.temperature_factor > 0.0
        assert assessment.rainfall_factor > 0.0
        assert assessment.humidity_factor > 0.0
        assert assessment.vegetation_factor > 0.0
        assert assessment.elevation_factor > 0.0

    def test_confidence_score_range(self):
        """Test that confidence score is in valid range."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert 0.0 <= assessment.confidence <= 1.0, \
            "Confidence should be between 0 and 1"


class TestPredictionCreation:
    """Test complete prediction creation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_create_prediction_basic(self):
        """Test basic prediction creation."""
        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi, Kenya",
            country_code="KE",
        )
        env = EnvironmentalFactors(
            mean_temperature=22.0,
            min_temperature=22.0-2.0,
            max_temperature=22.0+2.0,
            monthly_rainfall=100.0,
            relative_humidity=65.0,
            elevation=1795.0,
        )
        prediction_date = date(2024, 3, 15)

        prediction = self.calculator.create_prediction(
            location=location,
            environmental_data=env,
            prediction_date=prediction_date,
        )

        assert prediction.location == location
        assert prediction.environmental_data == env
        assert prediction.prediction_date == prediction_date
        assert prediction.time_horizon_days == 30  # Default
        assert prediction.risk_assessment is not None

    def test_create_prediction_custom_horizon(self):
        """Test prediction with custom time horizon."""
        location = GeographicLocation(
            latitude=0.0,
            longitude=0.0,
            area_name="Test Location",
            country_code="XX",
        )
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        prediction_date = date(2024, 6, 1)

        prediction = self.calculator.create_prediction(
            location=location,
            environmental_data=env,
            prediction_date=prediction_date,
            time_horizon_days=90,
        )

        assert prediction.time_horizon_days == 90

    def test_create_prediction_with_data_sources(self):
        """Test prediction with specified data sources."""
        location = GeographicLocation(
            latitude=0.0,
            longitude=0.0,
            area_name="Test Location",
            country_code="XX",
        )
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=25.0-2.0,
            max_temperature=25.0+2.0,
            monthly_rainfall=150.0,
            relative_humidity=70.0,
            elevation=500.0,
        )
        prediction_date = date(2024, 6, 1)
        data_sources = ["ERA5", "CHIRPS", "MODIS"]

        prediction = self.calculator.create_prediction(
            location=location,
            environmental_data=env,
            prediction_date=prediction_date,
            data_sources=data_sources,
        )

        assert prediction.data_sources == data_sources


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_extreme_negative_values(self):
        """Test handling of extreme negative values within valid Pydantic ranges."""
        env = EnvironmentalFactors(
            mean_temperature=-10.0,  # Minimum valid per model (ge=-10.0)
            min_temperature=-20.0,  # Minimum valid per model (ge=-20.0)
            max_temperature=-5.0,  # Minimum valid per model (ge=-5.0)
            monthly_rainfall=0.0,  # Minimum valid (ge=0.0)
            relative_humidity=0.0,  # Minimum valid (ge=0.0)
            elevation=-500.0,  # Minimum valid per model (ge=-500.0, below sea level)
            ndvi=-1.0,  # Valid minimum
        )

        assessment = self.calculator.calculate_overall_risk(env)

        # Should handle gracefully without crashing
        assert assessment.risk_score == 0.0
        assert assessment.risk_level == RiskLevel.LOW

    def test_extreme_positive_values(self):
        """Test handling of extreme positive values within valid Pydantic ranges."""
        env = EnvironmentalFactors(
            mean_temperature=50.0,  # Maximum valid per model (le=50.0)
            min_temperature=45.0,  # Maximum valid per model (le=45.0)
            max_temperature=55.0,  # Maximum valid per model (le=55.0)
            monthly_rainfall=2000.0,  # Maximum valid (le=2000.0)
            relative_humidity=100.0,  # Maximum
            elevation=6000.0,  # Maximum valid per model (le=6000.0)
            ndvi=1.0,  # Valid maximum
        )

        assessment = self.calculator.calculate_overall_risk(env)

        # Temperature too high should prevent transmission
        assert assessment.risk_score == 0.0

    def test_all_zeros(self):
        """Test handling of all zero values."""
        env = EnvironmentalFactors(
            mean_temperature=0.0,
            min_temperature=0.0-2.0,
            max_temperature=0.0+2.0,
            monthly_rainfall=0.0,
            relative_humidity=0.0,
            elevation=0.0,
            ndvi=0.0,
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_score == 0.0
        assert assessment.risk_level == RiskLevel.LOW

    def test_rounding_precision(self):
        """Test that all values are properly rounded."""
        env = EnvironmentalFactors(
            mean_temperature=24.5678,
            min_temperature=24.5678-2.0,
            max_temperature=24.5678+2.0,
            monthly_rainfall=156.789,
            relative_humidity=73.456,
            elevation=567.89,
            ndvi=0.12345,
        )

        assessment = self.calculator.calculate_overall_risk(env)

        # Check that all factors are rounded to 3 decimal places
        assert len(str(assessment.risk_score).split('.')[-1]) <= 3
        assert len(str(assessment.confidence).split('.')[-1]) <= 3
        assert len(str(assessment.temperature_factor).split('.')[-1]) <= 3


@pytest.mark.parametrize(
    "temp,rainfall,humidity,expected_risk_level",
    [
        (25.0, 200.0, 80.0, RiskLevel.CRITICAL),  # Perfect conditions
        (18.0, 80.0, 60.0, RiskLevel.LOW),  # Minimal conditions
        (34.0, 400.0, 100.0, RiskLevel.LOW),  # Too hot
        (10.0, 300.0, 90.0, RiskLevel.LOW),  # Too cold
        (25.0, 50.0, 80.0, RiskLevel.HIGH),  # Optimal temp+humidity but low rainfall (score 0.700)
        (25.0, 200.0, 40.0, RiskLevel.CRITICAL),  # Optimal temp+rainfall but low humidity (score 0.800)
        (23.0, 150.0, 70.0, RiskLevel.MEDIUM),  # Good conditions
        (27.0, 250.0, 85.0, RiskLevel.MEDIUM),  # Very good conditions but not optimal temp (score 0.510)
    ],
)
class TestParameterizedRiskScenarios:
    """Parametrized tests for various risk scenarios."""

    def test_risk_scenarios(
        self, temp, rainfall, humidity, expected_risk_level
    ):
        """Test various environmental scenarios."""
        calculator = RiskCalculator()

        env = EnvironmentalFactors(
            mean_temperature=temp,
            min_temperature=temp - 2.0,
            max_temperature=temp + 2.0,
            monthly_rainfall=rainfall,
            relative_humidity=humidity,
            elevation=500.0,  # Low elevation baseline
        )

        assessment = calculator.calculate_overall_risk(env)

        assert assessment.risk_level == expected_risk_level, \
            f"Temp={temp}, Rain={rainfall}, Humidity={humidity} should be {expected_risk_level}"
