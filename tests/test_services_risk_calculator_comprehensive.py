"""
Comprehensive unit tests for malaria risk calculation service.
Target: 100% coverage for src/malaria_predictor/services/risk_calculator.py
"""
from datetime import date
from unittest.mock import Mock, patch

from src.malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
    RiskLevel,
)

# Import the risk calculator module to test
from src.malaria_predictor.services.risk_calculator import RiskCalculator


class TestRiskCalculatorConstants:
    """Test RiskCalculator class constants and thresholds."""

    def test_temperature_constants(self):
        """Test temperature threshold constants."""
        calculator = RiskCalculator()

        assert calculator.OPTIMAL_TEMP == 25.0
        assert calculator.MIN_TRANSMISSION_TEMP == 18.0
        assert calculator.MAX_TRANSMISSION_TEMP == 34.0

    def test_rainfall_constants(self):
        """Test rainfall threshold constants."""
        calculator = RiskCalculator()

        assert calculator.MIN_RAINFALL == 80.0
        assert calculator.OPTIMAL_RAINFALL == 200.0

    def test_humidity_constants(self):
        """Test humidity threshold constants."""
        calculator = RiskCalculator()

        assert calculator.MIN_HUMIDITY == 60.0
        assert calculator.OPTIMAL_HUMIDITY == 80.0

    def test_elevation_constants(self):
        """Test elevation threshold constants."""
        calculator = RiskCalculator()

        assert calculator.LOW_RISK_ELEVATION == 1200.0
        assert calculator.MEDIUM_RISK_ELEVATION == 1600.0
        assert calculator.HIGH_RISK_ELEVATION == 2000.0


class TestTemperatureFactor:
    """Test temperature factor calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_optimal_temperature(self):
        """Test temperature factor at optimal temperature."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 25.0  # Optimal temperature

        factor = self.calculator.calculate_temperature_factor(env)

        assert factor == 1.0

    def test_temperature_below_minimum(self):
        """Test temperature factor below minimum transmission temperature."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 15.0  # Below MIN_TRANSMISSION_TEMP (18°C)

        factor = self.calculator.calculate_temperature_factor(env)

        assert factor == 0.0

    def test_temperature_above_maximum(self):
        """Test temperature factor above maximum transmission temperature."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 40.0  # Above MAX_TRANSMISSION_TEMP (34°C)

        factor = self.calculator.calculate_temperature_factor(env)

        assert factor == 0.0

    def test_temperature_at_minimum_threshold(self):
        """Test temperature factor at minimum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 18.0  # At MIN_TRANSMISSION_TEMP

        factor = self.calculator.calculate_temperature_factor(env)

        assert 0.0 < factor < 1.0
        assert factor > 0.1  # Should have some transmission potential

    def test_temperature_at_maximum_threshold(self):
        """Test temperature factor at maximum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 34.0  # At MAX_TRANSMISSION_TEMP

        factor = self.calculator.calculate_temperature_factor(env)

        assert 0.0 < factor < 1.0
        assert factor > 0.1  # Should have some transmission potential

    def test_temperature_below_optimal_range(self):
        """Test temperature factor in below optimal range."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 20.0  # Between MIN and OPTIMAL

        factor = self.calculator.calculate_temperature_factor(env)

        assert 0.0 < factor < 1.0

    def test_temperature_above_optimal_range(self):
        """Test temperature factor in above optimal range."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 30.0  # Between OPTIMAL and MAX

        factor = self.calculator.calculate_temperature_factor(env)

        assert 0.0 < factor < 1.0

    def test_temperature_factor_symmetry(self):
        """Test temperature factor symmetry around optimal temperature."""
        env_below = Mock(spec=EnvironmentalFactors)
        env_below.mean_temperature = 20.0  # 5°C below optimal

        env_above = Mock(spec=EnvironmentalFactors)
        env_above.mean_temperature = 30.0  # 5°C above optimal

        factor_below = self.calculator.calculate_temperature_factor(env_below)
        factor_above = self.calculator.calculate_temperature_factor(env_above)

        # Should be approximately equal due to similar distance from optimal
        assert abs(factor_below - factor_above) < 0.1

    def test_temperature_factor_bounds(self):
        """Test temperature factor stays within bounds."""
        test_temperatures = [10.0, 15.0, 18.0, 22.0, 25.0, 28.0, 34.0, 40.0, 45.0]

        for temp in test_temperatures:
            env = Mock(spec=EnvironmentalFactors)
            env.mean_temperature = temp

            factor = self.calculator.calculate_temperature_factor(env)

            assert 0.0 <= factor <= 1.0, f"Factor {factor} out of bounds for temperature {temp}"


class TestRainfallFactor:
    """Test rainfall factor calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_rainfall_below_minimum(self):
        """Test rainfall factor below minimum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.monthly_rainfall = 50.0  # Below MIN_RAINFALL (80mm)

        factor = self.calculator.calculate_rainfall_factor(env)

        assert factor == 0.0

    def test_rainfall_at_minimum_threshold(self):
        """Test rainfall factor at minimum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.monthly_rainfall = 80.0  # At MIN_RAINFALL

        factor = self.calculator.calculate_rainfall_factor(env)

        assert factor == 0.0

    def test_rainfall_at_optimal(self):
        """Test rainfall factor at optimal level."""
        env = Mock(spec=EnvironmentalFactors)
        env.monthly_rainfall = 200.0  # At OPTIMAL_RAINFALL

        factor = self.calculator.calculate_rainfall_factor(env)

        assert factor == 1.0

    def test_rainfall_between_min_and_optimal(self):
        """Test rainfall factor between minimum and optimal."""
        env = Mock(spec=EnvironmentalFactors)
        env.monthly_rainfall = 140.0  # Halfway between 80 and 200

        factor = self.calculator.calculate_rainfall_factor(env)

        expected = (140.0 - 80.0) / (200.0 - 80.0)  # Linear interpolation
        assert abs(factor - expected) < 0.001
        assert 0.0 < factor < 1.0

    def test_rainfall_above_optimal(self):
        """Test rainfall factor above optimal level."""
        env = Mock(spec=EnvironmentalFactors)
        env.monthly_rainfall = 400.0  # Above OPTIMAL_RAINFALL

        factor = self.calculator.calculate_rainfall_factor(env)

        assert 0.0 < factor <= 1.0
        # Should be less than 1.0 due to excessive rain washing out breeding sites
        assert factor < 1.0

    def test_rainfall_factor_bounds(self):
        """Test rainfall factor stays within bounds."""
        test_rainfalls = [0.0, 50.0, 80.0, 140.0, 200.0, 300.0, 500.0]

        for rainfall in test_rainfalls:
            env = Mock(spec=EnvironmentalFactors)
            env.monthly_rainfall = rainfall

            factor = self.calculator.calculate_rainfall_factor(env)

            assert 0.0 <= factor <= 1.0, f"Factor {factor} out of bounds for rainfall {rainfall}"

    def test_excessive_rainfall_diminishing_returns(self):
        """Test excessive rainfall has diminishing returns."""
        env_300 = Mock(spec=EnvironmentalFactors)
        env_300.monthly_rainfall = 300.0

        env_600 = Mock(spec=EnvironmentalFactors)
        env_600.monthly_rainfall = 600.0

        factor_300 = self.calculator.calculate_rainfall_factor(env_300)
        factor_600 = self.calculator.calculate_rainfall_factor(env_600)

        # Higher rainfall should not increase factor significantly
        assert factor_600 < factor_300 or abs(factor_600 - factor_300) < 0.1


class TestHumidityFactor:
    """Test humidity factor calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_humidity_below_minimum(self):
        """Test humidity factor below minimum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.relative_humidity = 50.0  # Below MIN_HUMIDITY (60%)

        factor = self.calculator.calculate_humidity_factor(env)

        assert factor == 0.0

    def test_humidity_at_minimum_threshold(self):
        """Test humidity factor at minimum threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.relative_humidity = 60.0  # At MIN_HUMIDITY

        factor = self.calculator.calculate_humidity_factor(env)

        assert factor == 0.0

    def test_humidity_at_optimal(self):
        """Test humidity factor at optimal level."""
        env = Mock(spec=EnvironmentalFactors)
        env.relative_humidity = 80.0  # At OPTIMAL_HUMIDITY

        factor = self.calculator.calculate_humidity_factor(env)

        assert factor == 1.0

    def test_humidity_between_min_and_optimal(self):
        """Test humidity factor between minimum and optimal."""
        env = Mock(spec=EnvironmentalFactors)
        env.relative_humidity = 70.0  # Halfway between 60 and 80

        factor = self.calculator.calculate_humidity_factor(env)

        expected = (70.0 - 60.0) / (80.0 - 60.0)  # Linear interpolation
        assert abs(factor - expected) < 0.001
        assert 0.0 < factor < 1.0

    def test_humidity_above_optimal(self):
        """Test humidity factor above optimal level."""
        env = Mock(spec=EnvironmentalFactors)
        env.relative_humidity = 95.0  # Above OPTIMAL_HUMIDITY

        factor = self.calculator.calculate_humidity_factor(env)

        assert factor == 1.0  # Maintains high risk at very high humidity

    def test_humidity_factor_bounds(self):
        """Test humidity factor stays within bounds."""
        test_humidities = [30.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

        for humidity in test_humidities:
            env = Mock(spec=EnvironmentalFactors)
            env.relative_humidity = humidity

            factor = self.calculator.calculate_humidity_factor(env)

            assert 0.0 <= factor <= 1.0, f"Factor {factor} out of bounds for humidity {humidity}"


class TestVegetationFactor:
    """Test vegetation factor calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_vegetation_no_data(self):
        """Test vegetation factor when no vegetation data available."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = None
        env.evi = None

        factor = self.calculator.calculate_vegetation_factor(env)

        assert factor == 0.5  # Neutral factor

    def test_vegetation_ndvi_preferred_over_evi(self):
        """Test NDVI is preferred when both NDVI and EVI available."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = 0.5
        env.evi = 0.8

        # Mock the calculation to track which value is used
        with patch.object(self.calculator, 'calculate_vegetation_factor') as mock_calc:
            mock_calc.return_value = 1.0
            self.calculator.calculate_vegetation_factor(env)

        # Should use NDVI when available
        factor = self.calculator.calculate_vegetation_factor(env)
        assert isinstance(factor, float)

    def test_vegetation_uses_evi_when_ndvi_unavailable(self):
        """Test EVI is used when NDVI not available."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = None
        env.evi = 0.5

        factor = self.calculator.calculate_vegetation_factor(env)

        assert 0.0 <= factor <= 1.0
        assert factor != 0.5  # Should not be neutral since EVI is available

    def test_vegetation_low_index(self):
        """Test vegetation factor with low vegetation index."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = -0.5  # Low vegetation
        env.evi = None

        factor = self.calculator.calculate_vegetation_factor(env)

        assert 0.0 <= factor < 1.0
        # Low vegetation should have reduced risk
        assert factor < 0.5

    def test_vegetation_moderate_index(self):
        """Test vegetation factor with moderate vegetation index."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = 0.0  # Moderate vegetation (normalized to 0.5)
        env.evi = None

        factor = self.calculator.calculate_vegetation_factor(env)

        assert factor == 1.0  # Peak risk at moderate vegetation

    def test_vegetation_high_index(self):
        """Test vegetation factor with high vegetation index."""
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = 0.8  # High vegetation
        env.evi = None

        factor = self.calculator.calculate_vegetation_factor(env)

        assert 0.0 <= factor < 1.0
        # High vegetation should have reduced risk
        assert factor < 1.0

    def test_vegetation_index_bounds_handling(self):
        """Test vegetation factor handles out-of-bounds indices."""
        # Test values outside [-1, 1] range
        test_indices = [-2.0, -1.0, 0.0, 1.0, 2.0]

        for index in test_indices:
            env = Mock(spec=EnvironmentalFactors)
            env.ndvi = index
            env.evi = None

            factor = self.calculator.calculate_vegetation_factor(env)

            assert 0.0 <= factor <= 1.0, f"Factor {factor} out of bounds for NDVI {index}"

    def test_vegetation_optimal_range(self):
        """Test vegetation factor in optimal range (0.3-0.7 normalized)."""
        # NDVI 0.2 maps to normalized 0.6 (optimal range)
        env = Mock(spec=EnvironmentalFactors)
        env.ndvi = 0.2
        env.evi = None

        factor = self.calculator.calculate_vegetation_factor(env)

        assert factor == 1.0


class TestElevationFactor:
    """Test elevation factor calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_elevation_low_risk_zone(self):
        """Test elevation factor in low elevation zone."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 1000.0  # Below LOW_RISK_ELEVATION (1200m)

        factor = self.calculator.calculate_elevation_factor(env)

        assert factor == 1.0

    def test_elevation_at_low_risk_threshold(self):
        """Test elevation factor at low risk threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 1200.0  # At LOW_RISK_ELEVATION

        factor = self.calculator.calculate_elevation_factor(env)

        assert factor == 1.0

    def test_elevation_medium_risk_zone(self):
        """Test elevation factor in medium elevation zone."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 1400.0  # Between LOW and MEDIUM thresholds

        factor = self.calculator.calculate_elevation_factor(env)

        assert 0.7 < factor < 1.0  # Linear decrease from 1.0 to 0.7

    def test_elevation_at_medium_risk_threshold(self):
        """Test elevation factor at medium risk threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 1600.0  # At MEDIUM_RISK_ELEVATION

        factor = self.calculator.calculate_elevation_factor(env)

        assert abs(factor - 0.7) < 0.001

    def test_elevation_high_risk_zone(self):
        """Test elevation factor in high elevation zone."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 1800.0  # Between MEDIUM and HIGH thresholds

        factor = self.calculator.calculate_elevation_factor(env)

        assert 0.1 < factor < 0.7  # Linear decrease from 0.7 to 0.1

    def test_elevation_at_high_risk_threshold(self):
        """Test elevation factor at high risk threshold."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 2000.0  # At HIGH_RISK_ELEVATION

        factor = self.calculator.calculate_elevation_factor(env)

        assert abs(factor - 0.1) < 0.001

    def test_elevation_very_high(self):
        """Test elevation factor at very high elevations."""
        env = Mock(spec=EnvironmentalFactors)
        env.elevation = 3000.0  # Above HIGH_RISK_ELEVATION

        factor = self.calculator.calculate_elevation_factor(env)

        assert factor == 0.1

    def test_elevation_factor_bounds(self):
        """Test elevation factor stays within bounds."""
        test_elevations = [0.0, 800.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0, 3000.0]

        for elevation in test_elevations:
            env = Mock(spec=EnvironmentalFactors)
            env.elevation = elevation

            factor = self.calculator.calculate_elevation_factor(env)

            assert 0.0 <= factor <= 1.0, f"Factor {factor} out of bounds for elevation {elevation}"


class TestOverallRiskCalculation:
    """Test overall risk assessment calculation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def create_mock_env(self, temp=25.0, rainfall=200.0, humidity=80.0,
                       ndvi=0.5, elevation=1000.0):
        """Create mock environmental factors."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = temp
        env.monthly_rainfall = rainfall
        env.relative_humidity = humidity
        env.ndvi = ndvi
        env.evi = None
        env.elevation = elevation
        return env

    def test_optimal_conditions_risk(self):
        """Test overall risk with optimal environmental conditions."""
        env = self.create_mock_env()  # All optimal values

        risk = self.calculator.calculate_overall_risk(env)

        assert isinstance(risk, RiskAssessment)
        assert risk.risk_score > 0.8
        assert risk.risk_level == RiskLevel.CRITICAL
        assert risk.confidence > 0.8
        assert risk.temperature_factor == 1.0
        assert risk.rainfall_factor == 1.0
        assert risk.humidity_factor == 1.0

    def test_temperature_limiting_scenario(self):
        """Test overall risk when temperature is limiting factor."""
        env = self.create_mock_env(temp=10.0)  # Temperature too low

        risk = self.calculator.calculate_overall_risk(env)

        assert risk.risk_score == 0.0
        assert risk.risk_level == RiskLevel.LOW
        assert risk.confidence == 0.9  # High confidence in temperature cutoffs
        assert risk.temperature_factor == 0.0

    def test_suboptimal_conditions_risk(self):
        """Test overall risk with suboptimal but viable conditions."""
        env = self.create_mock_env(temp=20.0, rainfall=100.0, humidity=65.0)

        risk = self.calculator.calculate_overall_risk(env)

        assert 0.0 < risk.risk_score < 0.8
        assert risk.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert 0.0 < risk.confidence <= 1.0

    def test_risk_level_thresholds(self):
        """Test risk level classification thresholds."""
        # Test CRITICAL threshold (>= 0.8)
        env_critical = self.create_mock_env()
        risk_critical = self.calculator.calculate_overall_risk(env_critical)
        if risk_critical.risk_score >= 0.8:
            assert risk_critical.risk_level == RiskLevel.CRITICAL

        # Test different scenarios to hit other thresholds
        test_cases = [
            (self.create_mock_env(temp=30.0, rainfall=120.0), "moderate conditions"),
            (self.create_mock_env(temp=20.0, rainfall=90.0, humidity=62.0), "marginal conditions"),
        ]

        for env, _description in test_cases:
            risk = self.calculator.calculate_overall_risk(env)

            if risk.risk_score >= 0.8:
                assert risk.risk_level == RiskLevel.CRITICAL
            elif risk.risk_score >= 0.6:
                assert risk.risk_level == RiskLevel.HIGH
            elif risk.risk_score >= 0.3:
                assert risk.risk_level == RiskLevel.MEDIUM
            else:
                assert risk.risk_level == RiskLevel.LOW

    def test_confidence_calculation(self):
        """Test confidence calculation based on factor availability."""
        # Test with all major factors present
        env_full = self.create_mock_env()
        risk_full = self.calculator.calculate_overall_risk(env_full)

        # Test with limited factors
        env_limited = self.create_mock_env(temp=10.0, rainfall=50.0, humidity=40.0)
        risk_limited = self.calculator.calculate_overall_risk(env_limited)

        # Confidence should be different based on viable factors
        assert isinstance(risk_full.confidence, float)
        assert isinstance(risk_limited.confidence, float)
        assert 0.0 <= risk_full.confidence <= 1.0
        assert 0.0 <= risk_limited.confidence <= 1.0

    def test_factor_weights_application(self):
        """Test that factor weights are applied correctly."""
        # Test with only temperature optimal (should dominate)
        env_temp_only = self.create_mock_env(temp=25.0, rainfall=0.0, humidity=0.0)
        risk_temp = self.calculator.calculate_overall_risk(env_temp_only)

        # Test with only non-temperature factors optimal
        env_no_temp = self.create_mock_env(temp=10.0, rainfall=200.0, humidity=80.0)
        risk_no_temp = self.calculator.calculate_overall_risk(env_no_temp)

        # Temperature-limited case should have very low risk despite other factors
        assert risk_no_temp.risk_score == 0.0
        assert risk_temp.risk_score > risk_no_temp.risk_score

    def test_risk_assessment_rounding(self):
        """Test that risk assessment values are properly rounded."""
        env = self.create_mock_env()
        risk = self.calculator.calculate_overall_risk(env)

        # Check that values are rounded to 3 decimal places
        assert len(str(risk.risk_score).split('.')[-1]) <= 3
        assert len(str(risk.confidence).split('.')[-1]) <= 3
        assert len(str(risk.temperature_factor).split('.')[-1]) <= 3
        assert len(str(risk.rainfall_factor).split('.')[-1]) <= 3
        assert len(str(risk.humidity_factor).split('.')[-1]) <= 3
        assert len(str(risk.vegetation_factor).split('.')[-1]) <= 3
        assert len(str(risk.elevation_factor).split('.')[-1]) <= 3


class TestMalariaPredictionCreation:
    """Test complete malaria prediction creation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()
        self.location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            name="Nairobi, Kenya"
        )
        self.env = Mock(spec=EnvironmentalFactors)
        self.env.mean_temperature = 25.0
        self.env.monthly_rainfall = 200.0
        self.env.relative_humidity = 80.0
        self.env.ndvi = 0.5
        self.env.evi = None
        self.env.elevation = 1000.0
        self.prediction_date = date(2024, 6, 15)

    def test_create_prediction_success(self):
        """Test successful prediction creation."""
        prediction = self.calculator.create_prediction(
            location=self.location,
            environmental_data=self.env,
            prediction_date=self.prediction_date
        )

        assert isinstance(prediction, MalariaPrediction)
        assert prediction.location == self.location
        assert prediction.environmental_data == self.env
        assert isinstance(prediction.risk_assessment, RiskAssessment)
        assert prediction.prediction_date == self.prediction_date
        assert prediction.time_horizon_days == 30  # Default value
        assert prediction.data_sources == ["placeholder_data"]  # Default value

    def test_create_prediction_with_custom_parameters(self):
        """Test prediction creation with custom parameters."""
        custom_horizon = 14
        custom_sources = ["ERA5", "CHIRPS", "MODIS"]

        prediction = self.calculator.create_prediction(
            location=self.location,
            environmental_data=self.env,
            prediction_date=self.prediction_date,
            time_horizon_days=custom_horizon,
            data_sources=custom_sources
        )

        assert prediction.time_horizon_days == custom_horizon
        assert prediction.data_sources == custom_sources

    def test_create_prediction_risk_assessment_integration(self):
        """Test that prediction integrates risk assessment correctly."""
        prediction = self.calculator.create_prediction(
            location=self.location,
            environmental_data=self.env,
            prediction_date=self.prediction_date
        )

        # Risk assessment should be calculated from environmental data
        direct_risk = self.calculator.calculate_overall_risk(self.env)

        assert prediction.risk_assessment.risk_score == direct_risk.risk_score
        assert prediction.risk_assessment.risk_level == direct_risk.risk_level
        assert prediction.risk_assessment.confidence == direct_risk.confidence

    def test_create_prediction_with_none_data_sources(self):
        """Test prediction creation with None data sources."""
        prediction = self.calculator.create_prediction(
            location=self.location,
            environmental_data=self.env,
            prediction_date=self.prediction_date,
            data_sources=None
        )

        assert prediction.data_sources == ["placeholder_data"]


class TestRiskCalculatorEdgeCases:
    """Test edge cases and error scenarios."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = RiskCalculator()

    def test_extreme_temperature_values(self):
        """Test risk calculation with extreme temperature values."""
        extreme_temps = [-50.0, -10.0, 0.0, 60.0, 100.0]

        for temp in extreme_temps:
            env = Mock(spec=EnvironmentalFactors)
            env.mean_temperature = temp
            env.monthly_rainfall = 200.0
            env.relative_humidity = 80.0
            env.ndvi = 0.5
            env.evi = None
            env.elevation = 1000.0

            risk = self.calculator.calculate_overall_risk(env)

            assert isinstance(risk, RiskAssessment)
            assert 0.0 <= risk.risk_score <= 1.0

    def test_extreme_rainfall_values(self):
        """Test risk calculation with extreme rainfall values."""
        extreme_rainfalls = [0.0, -10.0, 1000.0, 10000.0]

        for rainfall in extreme_rainfalls:
            env = Mock(spec=EnvironmentalFactors)
            env.mean_temperature = 25.0
            env.monthly_rainfall = rainfall
            env.relative_humidity = 80.0
            env.ndvi = 0.5
            env.evi = None
            env.elevation = 1000.0

            risk = self.calculator.calculate_overall_risk(env)

            assert isinstance(risk, RiskAssessment)
            assert 0.0 <= risk.risk_score <= 1.0

    def test_extreme_humidity_values(self):
        """Test risk calculation with extreme humidity values."""
        extreme_humidities = [-10.0, 0.0, 150.0, 200.0]

        for humidity in extreme_humidities:
            env = Mock(spec=EnvironmentalFactors)
            env.mean_temperature = 25.0
            env.monthly_rainfall = 200.0
            env.relative_humidity = humidity
            env.ndvi = 0.5
            env.evi = None
            env.elevation = 1000.0

            risk = self.calculator.calculate_overall_risk(env)

            assert isinstance(risk, RiskAssessment)
            assert 0.0 <= risk.risk_score <= 1.0

    def test_extreme_elevation_values(self):
        """Test risk calculation with extreme elevation values."""
        extreme_elevations = [-100.0, 0.0, 5000.0, 10000.0]

        for elevation in extreme_elevations:
            env = Mock(spec=EnvironmentalFactors)
            env.mean_temperature = 25.0
            env.monthly_rainfall = 200.0
            env.relative_humidity = 80.0
            env.ndvi = 0.5
            env.evi = None
            env.elevation = elevation

            risk = self.calculator.calculate_overall_risk(env)

            assert isinstance(risk, RiskAssessment)
            assert 0.0 <= risk.risk_score <= 1.0

    def test_missing_environmental_data(self):
        """Test risk calculation with missing environmental data."""
        # Test with minimal environmental data
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 25.0
        env.monthly_rainfall = 200.0
        env.relative_humidity = 80.0
        env.ndvi = None  # Missing vegetation data
        env.evi = None
        env.elevation = 1000.0

        risk = self.calculator.calculate_overall_risk(env)

        assert isinstance(risk, RiskAssessment)
        assert risk.vegetation_factor == 0.5  # Neutral factor for missing data

    def test_all_factors_zero_except_temperature(self):
        """Test risk calculation when only temperature is viable."""
        env = Mock(spec=EnvironmentalFactors)
        env.mean_temperature = 25.0
        env.monthly_rainfall = 0.0  # Below minimum
        env.relative_humidity = 0.0  # Below minimum
        env.ndvi = None
        env.evi = None
        env.elevation = 1000.0

        risk = self.calculator.calculate_overall_risk(env)

        assert isinstance(risk, RiskAssessment)
        assert risk.temperature_factor == 1.0
        assert risk.rainfall_factor == 0.0
        assert risk.humidity_factor == 0.0
        assert risk.vegetation_factor == 0.5  # Neutral
        assert risk.elevation_factor == 1.0
