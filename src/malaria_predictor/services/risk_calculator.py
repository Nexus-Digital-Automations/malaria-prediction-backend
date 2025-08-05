"""Risk calculation service for malaria outbreak prediction.

This service implements the core business logic for calculating malaria outbreak
risk based on environmental factors. The calculations are based on published
research on environmental determinants of malaria transmission.

Key thresholds based on research:
- Temperature: Optimal transmission ~25°C, window 18-34°C
- Rainfall: 80mm+ monthly needed for sustained transmission
- Humidity: 60%+ needed for mosquito survival
- Elevation: Higher risk decreases with altitude (varies by region)
"""

import math
from datetime import date

from ..models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
    RiskLevel,
)


class RiskCalculator:
    """Service for calculating malaria outbreak risk from environmental data."""

    # Research-based thresholds for malaria transmission
    OPTIMAL_TEMP = 25.0  # °C - optimal temperature for transmission
    MIN_TRANSMISSION_TEMP = 18.0  # °C - minimum for parasite development
    MAX_TRANSMISSION_TEMP = 34.0  # °C - maximum before transmission inhibited

    MIN_RAINFALL = 80.0  # mm/month - minimum for sustained transmission
    OPTIMAL_RAINFALL = 200.0  # mm/month - optimal rainfall amount

    MIN_HUMIDITY = 60.0  # % - minimum for mosquito survival
    OPTIMAL_HUMIDITY = 80.0  # % - optimal humidity level

    # Elevation thresholds (East African highlands)
    LOW_RISK_ELEVATION = 1200.0  # m - below this = stable transmission
    MEDIUM_RISK_ELEVATION = 1600.0  # m - above this = seasonal/epidemic risk
    HIGH_RISK_ELEVATION = 2000.0  # m - above this = minimal risk

    def calculate_temperature_factor(self, env: EnvironmentalFactors) -> float:
        """Calculate temperature contribution to malaria risk.

        Uses research showing optimal transmission around 25°C with
        transmission window between 18-34°C.
        """
        temp = env.mean_temperature

        # No transmission outside the viable range
        if temp < self.MIN_TRANSMISSION_TEMP or temp > self.MAX_TRANSMISSION_TEMP:
            return 0.0

        # Calculate distance from optimal temperature
        temp_deviation = abs(temp - self.OPTIMAL_TEMP)

        # Use Gaussian-like curve with peak at optimal temperature
        if temp_deviation == 0:
            return 1.0

        # Normalize based on distance from transmission limits
        if temp < self.OPTIMAL_TEMP:
            # Below optimal - scale to lower bound
            range_size = self.OPTIMAL_TEMP - self.MIN_TRANSMISSION_TEMP
            normalized_dev = temp_deviation / range_size
        else:
            # Above optimal - scale to upper bound
            range_size = self.MAX_TRANSMISSION_TEMP - self.OPTIMAL_TEMP
            normalized_dev = temp_deviation / range_size

        # Apply exponential decay from optimal point
        factor = math.exp(-2 * normalized_dev)
        return max(0.0, min(1.0, factor))

    def calculate_rainfall_factor(self, env: EnvironmentalFactors) -> float:
        """Calculate rainfall contribution to malaria risk.

        Based on research showing 80mm+ monthly rainfall needed,
        with optimal around 200mm/month.
        """
        rainfall = env.monthly_rainfall

        # No transmission below minimum threshold
        if rainfall < self.MIN_RAINFALL:
            return 0.0

        # Linear increase from minimum to optimal
        if rainfall <= self.OPTIMAL_RAINFALL:
            factor = (rainfall - self.MIN_RAINFALL) / (
                self.OPTIMAL_RAINFALL - self.MIN_RAINFALL
            )
        else:
            # Diminishing returns above optimal (excessive rain can wash out breeding sites)
            excess = rainfall - self.OPTIMAL_RAINFALL
            # Asymptotic approach to 1.0 with decreasing marginal benefit
            factor = 1.0 - 0.3 * (excess / (excess + 300))

        return max(0.0, min(1.0, factor))

    def calculate_humidity_factor(self, env: EnvironmentalFactors) -> float:
        """Calculate humidity contribution to malaria risk.

        Based on research showing 60%+ relative humidity needed
        for mosquito survival.
        """
        humidity = env.relative_humidity

        # No transmission below minimum threshold
        if humidity < self.MIN_HUMIDITY:
            return 0.0

        # Linear increase from minimum to optimal
        if humidity <= self.OPTIMAL_HUMIDITY:
            factor = (humidity - self.MIN_HUMIDITY) / (
                self.OPTIMAL_HUMIDITY - self.MIN_HUMIDITY
            )
        else:
            # Maintain high risk at very high humidity
            factor = 1.0

        return max(0.0, min(1.0, factor))

    def calculate_vegetation_factor(self, env: EnvironmentalFactors) -> float:
        """Calculate vegetation contribution to malaria risk.

        Uses NDVI/EVI as proxies for mosquito habitat availability.
        Moderate vegetation (0.3-0.7) is typically highest risk.
        """
        # Use NDVI if available, otherwise EVI, otherwise neutral
        vegetation_index = env.ndvi if env.ndvi is not None else env.evi

        if vegetation_index is None:
            return 0.5  # Neutral factor when vegetation data unavailable

        # Ensure valid range
        vegetation_index = max(-1.0, min(1.0, vegetation_index))

        # Convert to 0-1 range
        normalized_vi = (vegetation_index + 1.0) / 2.0

        # Peak risk at moderate vegetation (0.3-0.7 normalized range)
        if normalized_vi < 0.3:
            # Low vegetation - limited habitat
            factor = normalized_vi / 0.3
        elif normalized_vi <= 0.7:
            # Moderate vegetation - optimal habitat
            factor = 1.0
        else:
            # High vegetation - may reduce access to water/breeding sites
            factor = 1.0 - 0.3 * ((normalized_vi - 0.7) / 0.3)

        return max(0.0, min(1.0, factor))

    def calculate_elevation_factor(self, env: EnvironmentalFactors) -> float:
        """Calculate elevation contribution to malaria risk.

        Based on East African highland thresholds where transmission
        decreases with altitude due to temperature limitations.
        """
        elevation = env.elevation

        # High risk at low elevations
        if elevation <= self.LOW_RISK_ELEVATION:
            return 1.0
        # Medium risk in mid-elevation zones
        elif elevation <= self.MEDIUM_RISK_ELEVATION:
            # Linear decrease from 1.0 to 0.7
            range_size = self.MEDIUM_RISK_ELEVATION - self.LOW_RISK_ELEVATION
            position = (elevation - self.LOW_RISK_ELEVATION) / range_size
            factor = 1.0 - 0.3 * position
        # Low risk at high elevations
        elif elevation <= self.HIGH_RISK_ELEVATION:
            # Linear decrease from 0.7 to 0.1
            range_size = self.HIGH_RISK_ELEVATION - self.MEDIUM_RISK_ELEVATION
            position = (elevation - self.MEDIUM_RISK_ELEVATION) / range_size
            factor = 0.7 - 0.6 * position
        else:
            # Very low risk above 2000m
            factor = 0.1

        return max(0.0, min(1.0, factor))

    def calculate_overall_risk(self, env: EnvironmentalFactors) -> RiskAssessment:
        """Calculate overall malaria risk from environmental factors."""

        # Calculate individual factor contributions
        temp_factor = self.calculate_temperature_factor(env)
        rainfall_factor = self.calculate_rainfall_factor(env)
        humidity_factor = self.calculate_humidity_factor(env)
        vegetation_factor = self.calculate_vegetation_factor(env)
        elevation_factor = self.calculate_elevation_factor(env)

        # Weight factors based on research importance
        # Temperature is most critical (multiplicative), others are additive
        if temp_factor == 0.0:
            # No transmission possible without suitable temperature
            overall_score = 0.0
            confidence = 0.9  # High confidence in temperature cutoffs
        else:
            # Weighted combination of factors
            weighted_score = (
                temp_factor * 0.4  # Temperature: 40% weight
                + rainfall_factor * 0.25  # Rainfall: 25% weight
                + humidity_factor * 0.15  # Humidity: 15% weight
                + vegetation_factor * 0.1  # Vegetation: 10% weight
                + elevation_factor * 0.1  # Elevation: 10% weight
            )

            # Apply temperature multiplier for temperature-limited scenarios
            overall_score = weighted_score * temp_factor

            # Confidence based on data availability and factor alignment
            confidence_factors = [
                f for f in [temp_factor, rainfall_factor, humidity_factor] if f > 0
            ]
            confidence = min(0.95, 0.6 + 0.1 * len(confidence_factors))

        # Determine categorical risk level
        if overall_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return RiskAssessment(
            risk_score=round(overall_score, 3),
            risk_level=risk_level,
            confidence=round(confidence, 3),
            temperature_factor=round(temp_factor, 3),
            rainfall_factor=round(rainfall_factor, 3),
            humidity_factor=round(humidity_factor, 3),
            vegetation_factor=round(vegetation_factor, 3),
            elevation_factor=round(elevation_factor, 3),
        )

    def create_prediction(
        self,
        location: GeographicLocation,
        environmental_data: EnvironmentalFactors,
        prediction_date: date,
        time_horizon_days: int = 30,
        data_sources: list[str] | None = None,
    ) -> MalariaPrediction:
        """Create a complete malaria prediction for a location."""

        risk_assessment = self.calculate_overall_risk(environmental_data)

        return MalariaPrediction(
            location=location,
            environmental_data=environmental_data,
            risk_assessment=risk_assessment,
            prediction_date=prediction_date,
            time_horizon_days=time_horizon_days,
            data_sources=data_sources or ["placeholder_data"],
        )
