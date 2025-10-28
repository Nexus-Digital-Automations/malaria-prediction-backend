"""
Feature Engineering and Quality Management for Malaria Prediction.

This module provides feature engineering capabilities that transform harmonized
environmental data into malaria-relevant ML features, along with comprehensive
quality assessment and validation frameworks.
"""

import logging
from datetime import datetime
from typing import Any

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Creates malaria-relevant features from harmonized multi-source data.
    Generates derived features that combine environmental variables in ways
    relevant to malaria transmission dynamics and vector ecology.
    """

    def __init__(self, feature_schema: dict[str, str] | None = None) -> None:
        self.schema = feature_schema or self._get_default_schema()
        self.scalers: dict[str, Any] = {}

    def _get_default_schema(self) -> dict[str, str]:
        """Get default feature schema."""
        return {
            # Climate features (ERA5)
            "era5_temp_mean": "Daily mean temperature (°C)",
            "era5_temp_max": "Daily maximum temperature (°C)",
            "era5_temp_min": "Daily minimum temperature (°C)",
            "era5_temp_range": "Diurnal temperature range (°C)",
            "era5_humid_relative": "Relative humidity (%)",
            "era5_temp_suitability": "Temperature suitability index (0-1)",
            # Precipitation features (CHIRPS)
            "chirps_precip_daily": "Daily precipitation (mm)",
            "chirps_precip_7d": "7-day accumulated precipitation (mm)",
            "chirps_precip_30d": "30-day accumulated precipitation (mm)",
            "chirps_dry_spell_days": "Consecutive dry days count",
            "chirps_wet_spell_intensity": "Average wet spell intensity",
            "chirps_seasonal_anomaly": "Precipitation anomaly vs seasonal normal",
            # Vegetation features (MODIS)
            "modis_ndvi_current": "Current NDVI value (-1 to 1)",
            "modis_evi_current": "Current EVI value (-1 to 1)",
            "modis_ndvi_trend_30d": "30-day NDVI trend slope",
            "modis_vegetation_stress": "Vegetation stress indicator (0-1)",
            "modis_greenness_peak": "Days since peak greenness",
            "modis_phenology_stage": "Vegetation phenology stage (0-4)",
            # Malaria risk features (MAP)
            "map_pr_baseline": "Baseline parasite rate (%)",
            "map_incidence_risk": "Clinical incidence risk (cases/1000)",
            "map_transmission_intensity": "Transmission intensity category (0-3)",
            "map_vector_suitability": "Vector habitat suitability (0-1)",
            "map_intervention_coverage": "Intervention coverage score (0-1)",
            # Population features (WorldPop)
            "worldpop_density": "Population density (people/km²)",
            "worldpop_children_u5": "Children under 5 density (people/km²)",
            "worldpop_density_log": "Log-transformed population density",
            "worldpop_urban_rural": "Urban/rural classification (0-1)",
            "worldpop_accessibility": "Travel time to cities (hours)",
            # Derived interaction features
            "breeding_habitat_index": "Combined water+temperature breeding suitability",
            "transmission_risk_composite": "Multi-factor transmission risk score",
            "population_at_risk": "Population density × malaria risk",
            "climate_stress_index": "Combined temperature+precipitation stress",
            "vector_activity_potential": "Temperature+humidity vector activity score",
        }

    def generate_ml_features(
        self, harmonized_data: dict[str, Any], target_date: datetime
    ) -> dict[str, np.ndarray]:
        """
        Generate complete ML feature vector from harmonized data.
        Args:
            harmonized_data: Dictionary of harmonized data arrays by source
            target_date: Target date for prediction
        Returns:
            Dictionary of feature arrays ready for ML models
        """
        features = {}

        # Extract basic features with standardized names
        features.update(self._extract_basic_features(harmonized_data))

        # Calculate derived interaction features
        features.update(self._calculate_derived_features(features))

        # Calculate temporal aggregation features
        features.update(self._calculate_temporal_features(harmonized_data, target_date))

        # Calculate quality and uncertainty features
        features.update(self._calculate_quality_features(harmonized_data))

        return self._validate_and_normalize(features)

    def _extract_basic_features(
        self, harmonized_data: dict[str, Any]
    ) -> dict[str, np.ndarray]:
        """Extract basic features from each data source."""
        features = {}

        # ERA5 climate features
        if "era5" in harmonized_data:
            era5_data = harmonized_data["era5"]["data"]
            if era5_data.ndim == 3:  # Time series data
                features["era5_temp_mean"] = np.mean(era5_data, axis=0)
                features["era5_temp_max"] = np.max(era5_data, axis=0)
                features["era5_temp_min"] = np.min(era5_data, axis=0)
                features["era5_temp_range"] = (
                    features["era5_temp_max"] - features["era5_temp_min"]
                )
            else:  # Single time slice
                features["era5_temp_mean"] = era5_data

        # CHIRPS precipitation features
        if "chirps" in harmonized_data:
            chirps_data = harmonized_data["chirps"]["data"]
            if chirps_data.ndim == 3:
                features["chirps_precip_daily"] = np.mean(chirps_data, axis=0)
                features["chirps_precip_7d"] = (
                    np.sum(chirps_data[-7:], axis=0)
                    if chirps_data.shape[0] >= 7
                    else np.sum(chirps_data, axis=0)
                )
                features["chirps_precip_30d"] = (
                    np.sum(chirps_data[-30:], axis=0)
                    if chirps_data.shape[0] >= 30
                    else np.sum(chirps_data, axis=0)
                )
                features["chirps_dry_spell_days"] = self._calculate_dry_spell_length(
                    chirps_data
                )
            else:
                features["chirps_precip_daily"] = chirps_data

        # MODIS vegetation features
        if "modis" in harmonized_data:
            modis_data = harmonized_data["modis"]["data"]
            if modis_data.ndim == 3:
                features["modis_ndvi_current"] = modis_data[-1]  # Most recent
                features["modis_ndvi_trend_30d"] = self._calculate_trend(modis_data)
                features["modis_vegetation_stress"] = self._calculate_vegetation_stress(
                    modis_data
                )
            else:
                features["modis_ndvi_current"] = modis_data

        # MAP malaria risk features
        if "map" in harmonized_data:
            map_data = harmonized_data["map"]["data"]
            features["map_pr_baseline"] = map_data

        # WorldPop population features
        if "worldpop" in harmonized_data:
            pop_data = harmonized_data["worldpop"]["data"]
            features["worldpop_density"] = pop_data
            features["worldpop_density_log"] = np.log1p(pop_data)  # Log transform

        return features

    def _calculate_derived_features(
        self, basic_features: dict[str, np.ndarray]
    ) -> dict[str, np.ndarray]:
        """Calculate derived cross-source features."""
        derived = {}

        # Temperature suitability for malaria transmission
        if "era5_temp_mean" in basic_features:
            derived["era5_temp_suitability"] = self._temperature_suitability_curve(
                basic_features["era5_temp_mean"]
            )

        # Breeding habitat index
        if all(
            k in basic_features
            for k in ["era5_temp_mean", "chirps_precip_7d", "modis_ndvi_current"]
        ):
            derived["breeding_habitat_index"] = self._calculate_breeding_habitat(
                basic_features["era5_temp_mean"],
                basic_features["chirps_precip_7d"],
                basic_features["modis_ndvi_current"],
            )

        # Population at risk
        if "worldpop_density" in basic_features and "map_pr_baseline" in basic_features:
            derived["population_at_risk"] = (
                basic_features["worldpop_density"]
                * basic_features["map_pr_baseline"]
                / 100
            )

        # Climate stress index
        if all(k in basic_features for k in ["era5_temp_mean", "chirps_precip_30d"]):
            derived["climate_stress_index"] = self._calculate_climate_stress(
                basic_features["era5_temp_mean"],
                basic_features["chirps_precip_30d"],
                basic_features.get(
                    "modis_vegetation_stress",
                    np.zeros_like(basic_features["era5_temp_mean"]),
                ),
            )

        # Vector activity potential
        if "era5_temp_mean" in basic_features:
            derived["vector_activity_potential"] = self._calculate_vector_activity(
                basic_features["era5_temp_mean"],
                basic_features.get(
                    "era5_humid_relative",
                    np.full_like(basic_features["era5_temp_mean"], 60),
                ),
            )

        return derived

    def _temperature_suitability_curve(self, temperature: np.ndarray) -> np.ndarray:
        """Calculate temperature suitability for malaria transmission."""
        # Optimal range: 25-30°C, based on vector biology
        optimal_min, optimal_max = 25, 30
        threshold_min, threshold_max = 15, 40

        suitability = np.zeros_like(temperature, dtype=np.float32)

        # Linear increase from threshold to optimal
        mask1 = (temperature >= threshold_min) & (temperature < optimal_min)
        suitability[mask1] = (temperature[mask1] - threshold_min) / (
            optimal_min - threshold_min
        )

        # Optimal range
        mask2 = (temperature >= optimal_min) & (temperature <= optimal_max)
        suitability[mask2] = 1.0

        # Linear decrease from optimal to threshold
        mask3 = (temperature > optimal_max) & (temperature <= threshold_max)
        suitability[mask3] = 1.0 - (temperature[mask3] - optimal_max) / (
            threshold_max - optimal_max
        )

        return np.clip(suitability, 0, 1)

    def _calculate_breeding_habitat(
        self, temperature: np.ndarray, precipitation: np.ndarray, ndvi: np.ndarray
    ) -> np.ndarray:
        """Calculate breeding habitat suitability index."""
        # Combine temperature suitability, water availability, and vegetation cover
        temp_suitability = self._temperature_suitability_curve(temperature)

        # Water availability (precipitation with saturation)
        water_suitability = np.tanh(precipitation / 50.0)  # Saturates at ~50mm

        # Vegetation cover (moderate levels optimal for mosquito habitat)
        veg_suitability = 4 * ndvi * (1 - ndvi)  # Quadratic with peak at NDVI=0.5
        veg_suitability = np.clip(veg_suitability, 0, 1)

        # Combine with weights based on ecological importance
        breeding_index = (
            0.4 * temp_suitability + 0.4 * water_suitability + 0.2 * veg_suitability
        )

        return np.clip(breeding_index, 0, 1)

    def _calculate_climate_stress(
        self, temperature: np.ndarray, precipitation: np.ndarray, veg_stress: np.ndarray
    ) -> np.ndarray:
        """Calculate composite climate stress index."""
        # Temperature stress (deviation from optimal)
        temp_stress = np.abs(temperature - 27.5) / 15.0  # Normalized by range
        temp_stress = np.clip(temp_stress, 0, 1)

        # Drought stress (low precipitation)
        drought_stress = np.exp(-precipitation / 25.0)  # Exponential decay

        # Combine stresses
        climate_stress = 0.4 * temp_stress + 0.4 * drought_stress + 0.2 * veg_stress

        return np.clip(climate_stress, 0, 1)

    def _calculate_vector_activity(
        self, temperature: np.ndarray, humidity: np.ndarray
    ) -> np.ndarray:
        """Calculate vector activity potential."""
        # Temperature component (bell curve around 27°C)
        temp_component = np.exp(-((temperature - 27) ** 2) / (2 * 5**2))

        # Humidity component (sigmoid with threshold at 60%)
        humidity_component = 1 / (1 + np.exp(-(humidity - 60) / 10))

        # Combine components
        vector_activity = temp_component * humidity_component

        return np.clip(vector_activity, 0, 1)

    def _calculate_dry_spell_length(self, precip_data: np.ndarray) -> np.ndarray:
        """Calculate consecutive dry days (precipitation < 1mm)."""
        if precip_data.ndim != 3:
            return np.zeros(precip_data.shape, dtype=np.float32)

        # Threshold for dry day
        dry_threshold = 1.0  # mm

        # Find dry days
        dry_days = precip_data < dry_threshold

        # Calculate consecutive dry periods for each pixel
        dry_spell_length = np.zeros(precip_data.shape[1:], dtype=np.float32)

        for i in range(precip_data.shape[1]):
            for j in range(precip_data.shape[2]):
                pixel_dry = dry_days[:, i, j]

                # Find consecutive dry periods
                consecutive = 0
                max_consecutive = 0

                for is_dry in pixel_dry:
                    if is_dry:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 0

                dry_spell_length[i, j] = max_consecutive

        return dry_spell_length

    def _calculate_trend(self, data: np.ndarray) -> np.ndarray:
        """Calculate temporal trend slope."""
        if data.ndim != 3:
            return np.zeros(data.shape, dtype=np.float32)

        time_steps = np.arange(data.shape[0])
        trend_slope = np.zeros(data.shape[1:], dtype=np.float32)

        for i in range(data.shape[1]):
            for j in range(data.shape[2]):
                pixel_values = data[:, i, j]

                # Skip if all NaN
                if np.all(np.isnan(pixel_values)):
                    trend_slope[i, j] = np.nan
                    continue

                # Calculate linear trend
                valid_mask = ~np.isnan(pixel_values)
                if np.sum(valid_mask) > 2:
                    slope, _ = np.polyfit(
                        time_steps[valid_mask], pixel_values[valid_mask], 1
                    )
                    trend_slope[i, j] = slope
                else:
                    trend_slope[i, j] = 0

        return trend_slope

    def _calculate_vegetation_stress(self, ndvi_data: np.ndarray) -> np.ndarray:
        """Calculate vegetation stress indicator."""
        if ndvi_data.ndim != 3:
            return np.zeros(ndvi_data.shape, dtype=np.float32)

        # Calculate relative decline from maximum
        max_ndvi = np.nanmax(ndvi_data, axis=0)
        current_ndvi = ndvi_data[-1]  # Most recent

        # Avoid division by zero
        stress = np.zeros_like(current_ndvi)
        valid_mask = max_ndvi > 0.1  # Only calculate for vegetated areas

        stress[valid_mask] = 1 - (current_ndvi[valid_mask] / max_ndvi[valid_mask])
        stress = np.clip(stress, 0, 1)

        return stress

    def _calculate_temporal_features(
        self, harmonized_data: dict[str, Any], target_date: datetime
    ) -> dict[str, np.ndarray]:
        """Calculate temporal aggregation features."""
        temporal_features = {}

        # Seasonal index based on target date
        day_of_year = target_date.timetuple().tm_yday
        seasonal_index = 0.5 + 0.5 * np.sin(2 * np.pi * (day_of_year - 120) / 365)

        # Add as constant feature across all pixels
        if harmonized_data:
            sample_shape = list(harmonized_data.values())[0]["data"].shape[-2:]
            temporal_features["seasonal_malaria_index"] = np.full(
                sample_shape, seasonal_index, dtype=np.float32
            )

        return temporal_features

    def _calculate_quality_features(
        self, harmonized_data: dict[str, Any]
    ) -> dict[str, np.ndarray]:
        """Calculate data quality and availability features."""
        quality_features = {}

        if harmonized_data:
            sample_shape = list(harmonized_data.values())[0]["data"].shape[-2:]

            # Data source availability
            source_count = len(harmonized_data)
            quality_features["data_source_count"] = np.full(
                sample_shape, source_count, dtype=np.float32
            )

            # Overall quality score (placeholder - could be more sophisticated)
            quality_features["overall_quality_score"] = np.full(
                sample_shape, 0.8, dtype=np.float32
            )

        return quality_features

    def _validate_and_normalize(
        self, features: dict[str, np.ndarray]
    ) -> dict[str, np.ndarray]:
        """Validate and normalize feature arrays."""
        validated_features = {}

        for name, array in features.items():
            # Check for valid data
            if array is None:
                logger.warning(f"Feature {name} is None, skipping")
                continue

            # Ensure float32 dtype
            if array.dtype != np.float32:
                array = array.astype(np.float32)

            # Handle infinite values
            array = np.where(np.isinf(array), np.nan, array)

            # Store validated feature
            validated_features[name] = array

        return validated_features


class QualityManager:
    """
    Manages data quality assessment and validation across multiple sources.
    Provides comprehensive quality scoring, cross-source validation,
    and consistency checks for harmonized environmental data.
    """

    def __init__(self) -> None:
        self.quality_thresholds = {
            "era5": {
                "temperature_range": (-50, 60),  # Celsius
                "confidence_threshold": 0.8,
            },
            "chirps": {
                "precipitation_max": 500,  # mm/day
                "negative_threshold": -0.1,
            },
            "modis": {
                "ndvi_range": (-0.2, 1.0),
                "quality_flags": ["good_quality", "marginal_quality"],
            },
            "map": {
                "pr_range": (0, 100),  # Percentage
                "uncertainty_threshold": 0.3,
            },
            "worldpop": {
                "density_max": 50000,  # people/km²
                "negative_threshold": 0,
            },
        }

    def assess_harmonized_quality(
        self, harmonized_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Assess overall quality of harmonized data.
        Args:
            harmonized_data: Dictionary of harmonized data by source
        Returns:
            Quality assessment with scores and flags
        """
        quality_assessment = {
            "overall_quality": 1.0,
            "source_quality": {},
            "consistency_checks": {},
            "data_completeness": {},
            "processing_flags": [],
        }

        # Assess each source individually
        for source_name, source_data in harmonized_data.items():
            source_quality = self._assess_source_quality(source_name, source_data)
            quality_assessment["source_quality"][source_name] = source_quality
            quality_assessment["overall_quality"] *= source_quality["score"]

        # Cross-source consistency checks
        if len(harmonized_data) > 1:
            consistency = self._validate_cross_source_consistency(harmonized_data)
            quality_assessment["consistency_checks"] = consistency

            if not consistency["overall_consistency"]:
                quality_assessment["overall_quality"] *= 0.8  # Penalize inconsistency

        # Data completeness assessment
        completeness = self._assess_data_completeness(harmonized_data)
        quality_assessment["data_completeness"] = completeness
        quality_assessment["overall_quality"] *= completeness["overall_completeness"]

        # Overall quality categorization
        if quality_assessment["overall_quality"] > 0.8:
            quality_assessment["quality_category"] = "high"
        elif quality_assessment["overall_quality"] > 0.6:
            quality_assessment["quality_category"] = "medium"
        else:
            quality_assessment["quality_category"] = "low"
            quality_assessment["processing_flags"].append("low_overall_quality")

        return quality_assessment

    def _assess_source_quality(
        self, source_name: str, source_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess quality of individual data source."""
        if source_name not in self.quality_thresholds:
            return {"score": 0.8, "flags": ["unknown_source"], "details": {}}

        thresholds = self.quality_thresholds[source_name]
        data_array = source_data.get("data")

        if data_array is None:
            return {"score": 0.0, "flags": ["no_data"], "details": {}}

        quality_score = 1.0
        flags = []
        details = {}

        # Check for valid data range
        if source_name == "era5" and "temperature_range" in thresholds:
            temp_range = thresholds["temperature_range"]
            invalid_temp = np.sum(
                (data_array < temp_range[0]) | (data_array > temp_range[1])
            )
            total_pixels = data_array.size

            if invalid_temp > 0:
                invalid_ratio = invalid_temp / total_pixels
                quality_score *= 1 - invalid_ratio
                flags.append("temperature_out_of_range")
                details["invalid_temperature_ratio"] = invalid_ratio

        elif source_name == "chirps" and "precipitation_max" in thresholds:
            max_precip = thresholds["precipitation_max"]
            invalid_precip = np.sum(data_array > max_precip)
            negative_precip = np.sum(data_array < 0)
            total_pixels = data_array.size

            if invalid_precip > 0:
                invalid_ratio = invalid_precip / total_pixels
                quality_score *= 1 - invalid_ratio
                flags.append("precipitation_too_high")
                details["extreme_precipitation_ratio"] = invalid_ratio

            if negative_precip > 0:
                negative_ratio = negative_precip / total_pixels
                quality_score *= 1 - negative_ratio
                flags.append("negative_precipitation")
                details["negative_precipitation_ratio"] = negative_ratio

        elif source_name == "modis" and "ndvi_range" in thresholds:
            ndvi_range = thresholds["ndvi_range"]
            invalid_ndvi = np.sum(
                (data_array < ndvi_range[0]) | (data_array > ndvi_range[1])
            )
            total_pixels = data_array.size

            if invalid_ndvi > 0:
                invalid_ratio = invalid_ndvi / total_pixels
                quality_score *= 1 - invalid_ratio
                flags.append("ndvi_out_of_range")
                details["invalid_ndvi_ratio"] = invalid_ratio

        # Check for missing data
        if np.isnan(data_array).any():
            nan_ratio = np.sum(np.isnan(data_array)) / data_array.size
            quality_score *= 1 - nan_ratio

            if nan_ratio > 0.1:
                flags.append("high_missing_data")
            details["missing_data_ratio"] = nan_ratio

        return {"score": max(quality_score, 0.0), "flags": flags, "details": details}

    def _validate_cross_source_consistency(
        self, harmonized_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate consistency across data sources."""
        consistency_checks = []

        # Extract data arrays for correlation analysis
        data_arrays = {}
        for source_name, source_data in harmonized_data.items():
            data_arrays[source_name] = source_data.get("data")

        # Climate-vegetation consistency
        if "era5" in data_arrays and "modis" in data_arrays:
            era5_data = data_arrays["era5"]
            modis_data = data_arrays["modis"]

            # Flatten arrays for correlation
            era5_flat = era5_data.flatten()
            modis_flat = modis_data.flatten()

            # Remove NaN values
            valid_mask = ~(np.isnan(era5_flat) | np.isnan(modis_flat))

            if np.sum(valid_mask) > 100:  # Need sufficient data points
                temp_ndvi_corr = np.corrcoef(
                    era5_flat[valid_mask], modis_flat[valid_mask]
                )[0, 1]

                consistency_checks.append(
                    {
                        "check": "temperature_vegetation_correlation",
                        "value": temp_ndvi_corr,
                        "expected_range": (0.2, 0.8),
                        "passed": 0.2 <= temp_ndvi_corr <= 0.8,
                    }
                )

        # Precipitation-vegetation consistency
        if "chirps" in data_arrays and "modis" in data_arrays:
            chirps_data = data_arrays["chirps"]
            modis_data = data_arrays["modis"]

            chirps_flat = chirps_data.flatten()
            modis_flat = modis_data.flatten()

            valid_mask = ~(np.isnan(chirps_flat) | np.isnan(modis_flat))

            if np.sum(valid_mask) > 100:
                precip_ndvi_corr = np.corrcoef(
                    chirps_flat[valid_mask], modis_flat[valid_mask]
                )[0, 1]

                consistency_checks.append(
                    {
                        "check": "precipitation_vegetation_correlation",
                        "value": precip_ndvi_corr,
                        "expected_range": (0.1, 0.7),
                        "passed": 0.1 <= precip_ndvi_corr <= 0.7,
                    }
                )

        # Population-risk relationship (if available)
        if "worldpop" in data_arrays and "map" in data_arrays:
            pop_data = data_arrays["worldpop"]
            map_data = data_arrays["map"]

            pop_flat = pop_data.flatten()
            map_flat = map_data.flatten()

            valid_mask = ~(np.isnan(pop_flat) | np.isnan(map_flat))

            if np.sum(valid_mask) > 100:
                pop_risk_corr = np.corrcoef(pop_flat[valid_mask], map_flat[valid_mask])[
                    0, 1
                ]

                consistency_checks.append(
                    {
                        "check": "population_risk_relationship",
                        "value": pop_risk_corr,
                        "expected_range": (-0.3, 0.5),
                        "passed": -0.3 <= pop_risk_corr <= 0.5,
                    }
                )

        return {
            "overall_consistency": all(
                check.get("passed", False) for check in consistency_checks
            ),
            "checks": consistency_checks,
            "num_checks": len(consistency_checks),
        }

    def _assess_data_completeness(
        self, harmonized_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess data completeness across sources."""
        completeness = {}
        overall_completeness = 1.0

        for source_name, source_data in harmonized_data.items():
            data_array = source_data.get("data")

            if data_array is None:
                completeness[source_name] = 0.0
                overall_completeness = 0.0
            else:
                # Calculate completeness as ratio of non-NaN values
                valid_pixels = np.sum(~np.isnan(data_array))
                total_pixels = data_array.size
                source_completeness = (
                    valid_pixels / total_pixels if total_pixels > 0 else 0.0
                )

                completeness[source_name] = source_completeness
                overall_completeness = min(overall_completeness, source_completeness)

        return {
            "source_completeness": completeness,
            "overall_completeness": overall_completeness,
            "complete_sources": sum(1 for c in completeness.values() if c > 0.8),
            "total_sources": len(completeness),
        }
