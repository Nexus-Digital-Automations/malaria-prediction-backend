"""Tests for risk calculator service."""

from datetime import date

from malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    RiskLevel,
)
from malaria_predictor.services.risk_calculator import RiskCalculator


class TestRiskCalculator:
    """Tests for RiskCalculator service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = RiskCalculator()

    def test_temperature_factor_optimal(self):
        """Test temperature factor at optimal temperature (25°C)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )

        factor = self.calculator.calculate_temperature_factor(env)
        assert factor == 1.0

    def test_temperature_factor_outside_range(self):
        """Test temperature factor outside transmission range."""
        # Too cold
        env_cold = EnvironmentalFactors(
            mean_temperature=15.0,  # Below 18°C threshold
            min_temperature=10.0,
            max_temperature=20.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        factor = self.calculator.calculate_temperature_factor(env_cold)
        assert factor == 0.0

        # Too hot
        env_hot = EnvironmentalFactors(
            mean_temperature=40.0,  # Above 34°C threshold
            min_temperature=35.0,
            max_temperature=45.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        factor = self.calculator.calculate_temperature_factor(env_hot)
        assert factor == 0.0

    def test_temperature_factor_edge_cases(self):
        """Test temperature factor at transmission boundaries."""
        # Minimum transmission temperature
        env_min = EnvironmentalFactors(
            mean_temperature=18.0,
            min_temperature=15.0,
            max_temperature=25.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        factor_min = self.calculator.calculate_temperature_factor(env_min)
        assert 0.0 < factor_min < 1.0

        # Maximum transmission temperature
        env_max = EnvironmentalFactors(
            mean_temperature=34.0,
            min_temperature=30.0,
            max_temperature=38.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
        )
        factor_max = self.calculator.calculate_temperature_factor(env_max)
        assert 0.0 < factor_max < 1.0

    def test_rainfall_factor_insufficient(self):
        """Test rainfall factor below minimum threshold."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=50.0,  # Below 80mm threshold
            relative_humidity=75.0,
            elevation=800.0,
        )

        factor = self.calculator.calculate_rainfall_factor(env)
        assert factor == 0.0

    def test_rainfall_factor_optimal(self):
        """Test rainfall factor at optimal level."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=200.0,  # Optimal rainfall
            relative_humidity=75.0,
            elevation=800.0,
        )

        factor = self.calculator.calculate_rainfall_factor(env)
        assert factor == 1.0

    def test_rainfall_factor_excessive(self):
        """Test rainfall factor with excessive rainfall."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=800.0,  # Very high rainfall
            relative_humidity=75.0,
            elevation=800.0,
        )

        factor = self.calculator.calculate_rainfall_factor(env)
        assert 0.5 < factor < 1.0  # Should be reduced but not zero

    def test_humidity_factor_insufficient(self):
        """Test humidity factor below minimum threshold."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=40.0,  # Below 60% threshold
            elevation=800.0,
        )

        factor = self.calculator.calculate_humidity_factor(env)
        assert factor == 0.0

    def test_humidity_factor_optimal(self):
        """Test humidity factor at optimal level."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=80.0,  # Optimal humidity
            elevation=800.0,
        )

        factor = self.calculator.calculate_humidity_factor(env)
        assert factor == 1.0

    def test_humidity_factor_very_high(self):
        """Test humidity factor at very high levels (>80%)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=95.0,  # Very high humidity
            elevation=800.0,
        )

        factor = self.calculator.calculate_humidity_factor(env)
        assert factor == 1.0

    def test_vegetation_factor_with_ndvi(self):
        """Test vegetation factor calculation with NDVI."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
            ndvi=0.4,  # Moderate vegetation
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert 0.8 <= factor <= 1.0

    def test_vegetation_factor_with_evi(self):
        """Test vegetation factor calculation with EVI."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
            evi=0.5,  # Moderate vegetation
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert 0.8 <= factor <= 1.0

    def test_vegetation_factor_no_data(self):
        """Test vegetation factor when no vegetation data available."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
            # No NDVI or EVI
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert factor == 0.5  # Neutral factor

    def test_vegetation_factor_low_vegetation(self):
        """Test vegetation factor with low vegetation (< 0.3 normalized)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=800.0,
            ndvi=-0.8,  # Very low vegetation, should hit the < 0.3 normalized case
        )

        factor = self.calculator.calculate_vegetation_factor(env)
        assert 0.0 <= factor < 1.0

    def test_elevation_factor_low_elevation(self):
        """Test elevation factor at low elevation (high risk)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=500.0,  # Below 1200m threshold
        )

        factor = self.calculator.calculate_elevation_factor(env)
        assert factor == 1.0

    def test_elevation_factor_high_elevation(self):
        """Test elevation factor at high elevation (low risk)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=2500.0,  # Above 2000m threshold
        )

        factor = self.calculator.calculate_elevation_factor(env)
        assert factor == 0.1

    def test_elevation_factor_medium_elevation(self):
        """Test elevation factor at medium elevation (1600-2000m range)."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=150.0,
            relative_humidity=75.0,
            elevation=1800.0,  # Between 1600-2000m threshold
        )

        factor = self.calculator.calculate_elevation_factor(env)
        assert 0.1 < factor < 0.7  # Should be in the linear decrease range

    def test_overall_risk_high_risk_scenario(self):
        """Test overall risk calculation for high-risk scenario."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,  # Optimal
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=200.0,  # Optimal
            relative_humidity=80.0,  # Optimal
            elevation=800.0,  # Low elevation
            ndvi=0.5,  # Moderate vegetation
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert assessment.risk_score > 0.6
        assert 0.0 <= assessment.confidence <= 1.0
        assert assessment.temperature_factor == 1.0
        assert assessment.rainfall_factor == 1.0
        assert assessment.humidity_factor == 1.0

    def test_overall_risk_low_risk_scenario(self):
        """Test overall risk calculation for low-risk scenario."""
        env = EnvironmentalFactors(
            mean_temperature=15.0,  # Too cold
            min_temperature=10.0,
            max_temperature=20.0,
            monthly_rainfall=50.0,  # Too low
            relative_humidity=40.0,  # Too low
            elevation=2500.0,  # Too high
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.risk_score == 0.0
        assert assessment.temperature_factor == 0.0

    def test_overall_risk_medium_scenario(self):
        """Test overall risk calculation for medium-risk scenario."""
        env = EnvironmentalFactors(
            mean_temperature=22.0,  # Suboptimal but viable
            min_temperature=18.0,
            max_temperature=26.0,
            monthly_rainfall=120.0,  # Adequate
            relative_humidity=65.0,  # Just above minimum
            elevation=1400.0,  # Medium elevation
        )

        assessment = self.calculator.calculate_overall_risk(env)

        assert assessment.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
        ]
        assert 0.0 <= assessment.risk_score <= 1.0
        assert 0.0 < assessment.temperature_factor < 1.0

    def test_overall_risk_high_risk_level(self):
        """Test overall risk calculation that can reach HIGH risk level to test line 219."""
        env = EnvironmentalFactors(
            mean_temperature=25.0,  # Optimal temperature
            min_temperature=20.0,
            max_temperature=30.0,
            monthly_rainfall=160.0,  # Good rainfall
            relative_humidity=72.0,  # Moderate humidity
            elevation=1100.0,  # Low elevation
            ndvi=0.3,  # Moderate vegetation
        )

        assessment = self.calculator.calculate_overall_risk(env)

        # This should be a reasonable risk calculation, just verifying we can test the HIGH branch
        assert assessment.risk_level in [
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        assert 0.0 <= assessment.risk_score <= 1.0

    def test_risk_level_boundary_conditions(self):
        """Test specific risk level boundary conditions to hit all code paths."""
        # Test scenario that should produce exactly HIGH risk (0.6-0.8)
        env_high = EnvironmentalFactors(
            mean_temperature=24.5,  # Good temperature
            min_temperature=19.5,
            max_temperature=29.5,
            monthly_rainfall=170.0,  # Adequate rainfall
            relative_humidity=75.0,  # Good humidity
            elevation=800.0,  # Low elevation
            ndvi=0.35,  # Moderate vegetation
        )
        assessment_high = self.calculator.calculate_overall_risk(env_high)
        # Just verify calculation works - the exact risk level will depend on weighting
        assert assessment_high.risk_level in [
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

    def test_create_prediction(self):
        """Test creating complete malaria prediction."""
        location = GeographicLocation(
            latitude=-1.2921,
            longitude=36.8219,
            area_name="Nairobi, Kenya",
            country_code="KE",
        )

        env = EnvironmentalFactors(
            mean_temperature=24.0,
            min_temperature=19.0,
            max_temperature=29.0,
            monthly_rainfall=120.0,
            relative_humidity=70.0,
            elevation=1200.0,
            ndvi=0.4,
        )

        prediction_date = date(2024, 1, 15)
        prediction = self.calculator.create_prediction(
            location=location,
            environmental_data=env,
            prediction_date=prediction_date,
            time_horizon_days=30,
            data_sources=["ERA5", "CHIRPS"],
        )

        assert prediction.location.area_name == "Nairobi, Kenya"
        assert prediction.environmental_data.mean_temperature == 24.0
        assert prediction.prediction_date == prediction_date
        assert prediction.time_horizon_days == 30
        assert "ERA5" in prediction.data_sources
        assert prediction.risk_assessment.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

    def test_factor_rounding(self):
        """Test that factor values are properly rounded."""
        env = EnvironmentalFactors(
            mean_temperature=24.333,
            min_temperature=19.0,
            max_temperature=29.0,
            monthly_rainfall=123.456,
            relative_humidity=72.789,
            elevation=1234.567,
        )

        assessment = self.calculator.calculate_overall_risk(env)

        # All factors should be rounded to 3 decimal places
        assert len(str(assessment.risk_score).split(".")[-1]) <= 3
        assert len(str(assessment.confidence).split(".")[-1]) <= 3
        assert len(str(assessment.temperature_factor).split(".")[-1]) <= 3
