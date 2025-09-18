"""
Test Data Factory for Malaria Prediction Backend.

This module provides factories for creating realistic test data
across all environmental data sources and prediction scenarios.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from malaria_predictor.models import Location


class EnvironmentalDataFactory:
    """Factory for creating realistic environmental data fixtures."""

    @staticmethod
    def create_era5_data(
        location: Location,
        start_date: datetime,
        end_date: datetime,
        temporal_resolution: str = "6H",
        add_noise: bool = True,
    ) -> dict[str, Any]:
        """Create realistic ERA5 climate data."""

        # Generate time series
        date_range = pd.date_range(start_date, end_date, freq=temporal_resolution)
        n_points = len(date_range)

        # Base climate values based on location (rough approximation)
        base_temp = 20 + (abs(location.latitude) * -0.5) + 5  # Celsius
        base_precip = 2.0 if abs(location.latitude) < 10 else 1.0  # mm/day
        base_humidity = 70 if abs(location.latitude) < 20 else 60  # %
        base_wind = 5 + random.uniform(-2, 2)  # m/s

        # Create seasonal and diurnal patterns
        temperatures = []
        precipitation = []
        humidity = []
        wind_speed = []

        for _i, timestamp in enumerate(date_range):
            # Seasonal component (annual cycle)
            seasonal_temp = 3 * np.sin(2 * np.pi * timestamp.dayofyear / 365.25)

            # Diurnal component (daily cycle)
            diurnal_temp = 2 * np.sin(2 * np.pi * timestamp.hour / 24)

            # Temperature with patterns
            temp = base_temp + seasonal_temp + diurnal_temp
            if add_noise:
                temp += random.gauss(0, 1.5)  # Add realistic noise
            temperatures.append(round(temp, 2))

            # Precipitation (clustered, realistic patterns)
            if random.random() < 0.3:  # 30% chance of precipitation
                precip = random.lognormvariate(np.log(base_precip), 0.8)
            else:
                precip = 0.0
            precipitation.append(round(precip, 2))

            # Humidity (anti-correlated with temperature)
            humid = base_humidity - (temp - base_temp) * 2
            if add_noise:
                humid += random.gauss(0, 5)
            humidity.append(max(0, min(100, round(humid, 1))))

            # Wind speed (varies with weather patterns)
            wind = base_wind + random.gauss(0, 2)
            wind_speed.append(max(0, round(wind, 1)))

        return {
            "data": {
                "2m_temperature": temperatures,
                "total_precipitation": precipitation,
                "2m_relative_humidity": humidity,
                "10m_wind_speed": wind_speed,
                "time": [ts.isoformat() for ts in date_range],
                "latitude": [location.latitude] * n_points,
                "longitude": [location.longitude] * n_points,
            },
            "metadata": {
                "source": "ERA5",
                "location": location.dict(),
                "temporal_resolution": temporal_resolution,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "variables": [
                    "2m_temperature",
                    "total_precipitation",
                    "2m_relative_humidity",
                    "10m_wind_speed",
                ],
                "units": {
                    "2m_temperature": "Celsius",
                    "total_precipitation": "mm",
                    "2m_relative_humidity": "%",
                    "10m_wind_speed": "m/s",
                },
            },
        }

    @staticmethod
    def create_chirps_data(
        location: Location,
        start_date: datetime,
        end_date: datetime,
        add_seasonal_patterns: bool = True,
    ) -> dict[str, Any]:
        """Create realistic CHIRPS precipitation data."""

        # Generate daily data
        date_range = pd.date_range(start_date.date(), end_date.date(), freq="D")

        # Base precipitation based on latitude (rough climate zones)
        if abs(location.latitude) < 10:  # Tropical
            base_precip = 4.0
            wet_season_months = [4, 5, 6, 7, 8, 9]  # April-September
        elif abs(location.latitude) < 23:  # Subtropical
            base_precip = 2.5
            wet_season_months = [11, 12, 1, 2, 3]  # Nov-Mar (Southern Hemisphere)
        else:  # Temperate
            base_precip = 1.5
            wet_season_months = [6, 7, 8]  # Jun-Aug

        precipitation_data = []

        for date in date_range:
            # Seasonal modulation
            if add_seasonal_patterns:
                if date.month in wet_season_months:
                    seasonal_factor = 2.0
                else:
                    seasonal_factor = 0.5
            else:
                seasonal_factor = 1.0

            # Precipitation occurrence (realistic clustering)
            if random.random() < 0.25 * seasonal_factor:  # Chance of rain
                # Log-normal distribution for precipitation amounts
                precip = random.lognormvariate(
                    np.log(base_precip * seasonal_factor), 0.8
                )
                precipitation_data.append(round(precip, 1))
            else:
                precipitation_data.append(0.0)

        return {
            "data": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "precipitation": precip,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
                for date, precip in zip(date_range, precipitation_data, strict=False)
            ],
            "metadata": {
                "source": "CHIRPS v2.0",
                "location": location.dict(),
                "resolution": "0.05 degrees",
                "units": "mm/day",
                "date_range": {
                    "start": start_date.date().isoformat(),
                    "end": end_date.date().isoformat(),
                },
                "total_precipitation": sum(precipitation_data),
                "rainy_days": sum(1 for p in precipitation_data if p > 0),
            },
        }

    @staticmethod
    def create_modis_data(
        location: Location,
        start_date: datetime,
        end_date: datetime,
        composite_period: int = 16,  # 16-day composites
    ) -> dict[str, Any]:
        """Create realistic MODIS vegetation and temperature data."""

        # Generate 16-day composite dates
        current_date = start_date
        composite_dates = []
        while current_date <= end_date:
            composite_dates.append(current_date)
            current_date += timedelta(days=composite_period)

        # Base values based on location characteristics
        if abs(location.latitude) < 10:  # Tropical
            base_ndvi = 0.7
            base_evi = 0.6
            base_lst_day = 305  # Kelvin (~32°C)
            base_lst_night = 295  # Kelvin (~22°C)
        elif abs(location.latitude) < 23:  # Subtropical
            base_ndvi = 0.5
            base_evi = 0.4
            base_lst_day = 300  # Kelvin (~27°C)
            base_lst_night = 285  # Kelvin (~12°C)
        else:  # Temperate
            base_ndvi = 0.4
            base_evi = 0.3
            base_lst_day = 295  # Kelvin (~22°C)
            base_lst_night = 280  # Kelvin (~7°C)

        modis_results = []

        for _i, date in enumerate(composite_dates):
            # Seasonal vegetation patterns
            seasonal_ndvi = 0.2 * np.sin(2 * np.pi * date.dayofyear / 365.25)
            seasonal_evi = 0.15 * np.sin(2 * np.pi * date.dayofyear / 365.25)

            # Add some noise and ensure valid ranges
            ndvi = max(0, min(1, base_ndvi + seasonal_ndvi + random.gauss(0, 0.05)))
            evi = max(0, min(1, base_evi + seasonal_evi + random.gauss(0, 0.04)))

            # Temperature with seasonal variation
            seasonal_temp = 10 * np.sin(2 * np.pi * date.dayofyear / 365.25)
            lst_day = base_lst_day + seasonal_temp + random.gauss(0, 2)
            lst_night = base_lst_night + seasonal_temp + random.gauss(0, 1.5)

            modis_results.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "pixel_reliability": (
                        "Good" if random.random() > 0.1 else "Marginal"
                    ),
                    "ndvi": round(ndvi, 4),
                    "evi": round(evi, 4),
                    "lst_day": round(lst_day, 1),
                    "lst_night": round(lst_night, 1),
                    "qa_quality_flag": (
                        "Good quality"
                        if random.random() > 0.15
                        else "Acceptable quality"
                    ),
                }
            )

        return {
            "results": modis_results,
            "metadata": {
                "source": "MODIS",
                "product": "MOD13Q1/MOD11A2",
                "version": "061",
                "pixel_size": "250m",
                "location": location.dict(),
                "composite_period": f"{composite_period} days",
                "date_range": {
                    "start": start_date.date().isoformat(),
                    "end": end_date.date().isoformat(),
                },
            },
        }

    @staticmethod
    def create_worldpop_data(
        location: Location,
        year: int = 2023,
        add_demographic_details: bool = True,
    ) -> dict[str, Any]:
        """Create realistic WorldPop population data."""

        # Base population density based on location characteristics
        # This is a very rough approximation for testing
        if (
            location.latitude == -1.286389 and location.longitude == 36.817222
        ):  # Nairobi
            base_density = 4500
            urban_fraction = 0.85
        elif location.latitude == 6.5244 and location.longitude == 3.3792:  # Lagos
            base_density = 6500
            urban_fraction = 0.90
        elif abs(location.latitude) < 10:  # Tropical regions (often more populated)
            base_density = random.uniform(200, 1000)
            urban_fraction = random.uniform(0.3, 0.7)
        else:  # Other regions
            base_density = random.uniform(50, 500)
            urban_fraction = random.uniform(0.2, 0.6)

        # Add some spatial variation
        density_variation = random.uniform(0.8, 1.2)
        population_density = base_density * density_variation

        # Estimate total population for a 1km grid cell
        total_population = int(population_density)

        # Age structure (realistic distribution)
        age_structure = {
            "0-1": int(total_population * 0.04),
            "1-5": int(total_population * 0.12),
            "5-15": int(total_population * 0.22),
            "15-65": int(total_population * 0.58),
            "65+": int(total_population * 0.04),
        }

        # Urban/rural split
        urban_population = int(total_population * urban_fraction)
        rural_population = total_population - urban_population

        result = {
            "data": {
                "population_density": round(population_density, 2),
                "total_population": total_population,
                "urban_rural": {
                    "urban": urban_population,
                    "rural": rural_population,
                },
            },
            "metadata": {
                "source": "WorldPop",
                "year": year,
                "resolution": "100m",
                "dataset": f"ppp_{year}_1km_Aggregated",
                "location": location.dict(),
                "urban_fraction": round(urban_fraction, 3),
            },
        }

        if add_demographic_details:
            result["data"]["age_structure"] = age_structure
            result["data"]["dependency_ratio"] = round(
                (age_structure["0-1"] + age_structure["1-5"] + age_structure["65+"])
                / age_structure["15-65"],
                3,
            )

        return result

    @staticmethod
    def create_map_data(
        location: Location,
        year: int = 2023,
        include_interventions: bool = True,
    ) -> dict[str, Any]:
        """Create realistic Malaria Atlas Project data."""

        # Base malaria risk based on location (rough climate-based estimate)
        if abs(location.latitude) < 10:  # Tropical belt
            base_incidence = random.uniform(0.15, 0.35)
            base_parasite_rate = base_incidence * 0.7
            environmental_suitability = random.uniform(0.6, 0.85)
        elif abs(location.latitude) < 23:  # Subtropical
            base_incidence = random.uniform(0.05, 0.20)
            base_parasite_rate = base_incidence * 0.65
            environmental_suitability = random.uniform(0.4, 0.70)
        else:  # Temperate (low malaria risk)
            base_incidence = random.uniform(0.001, 0.05)
            base_parasite_rate = base_incidence * 0.5
            environmental_suitability = random.uniform(0.1, 0.40)

        result = {
            "data": {
                "malaria_incidence": round(base_incidence, 4),
                "parasite_rate": round(base_parasite_rate, 4),
                "environmental_suitability": round(environmental_suitability, 3),
                "transmission_intensity": (
                    "high"
                    if base_incidence > 0.2
                    else "moderate" if base_incidence > 0.1 else "low"
                ),
            },
            "metadata": {
                "source": "MAP Global Database",
                "country": "Unknown",  # Would need geocoding
                "year": year,
                "location": location.dict(),
                "data_type": "modeled_estimates",
                "last_updated": datetime.now().isoformat(),
            },
        }

        if include_interventions:
            # Intervention coverage (higher coverage often correlates with lower incidence)
            coverage_factor = (
                1.2 - base_incidence
            )  # Higher incidence = potentially lower coverage

            result["data"]["intervention_coverage"] = {
                "itn_coverage": max(
                    0.2, min(0.9, random.uniform(0.4, 0.8) * coverage_factor)
                ),
                "irs_coverage": max(
                    0.1, min(0.7, random.uniform(0.2, 0.6) * coverage_factor)
                ),
                "act_coverage": max(
                    0.3, min(0.95, random.uniform(0.5, 0.9) * coverage_factor)
                ),
                "rdt_coverage": max(
                    0.2, min(0.8, random.uniform(0.3, 0.7) * coverage_factor)
                ),
            }

            # Round intervention coverage values
            for key, value in result["data"]["intervention_coverage"].items():
                result["data"]["intervention_coverage"][key] = round(value, 3)

        return result


class PredictionDataFactory:
    """Factory for creating prediction-related test data."""

    @staticmethod
    def create_feature_matrix(
        n_timesteps: int = 30,
        n_features: int = 8,
        add_patterns: bool = True,
        normalize: bool = True,
    ) -> np.ndarray:
        """Create realistic feature matrix for ML models."""

        # Feature names for reference
        feature_names = [
            "temperature",
            "precipitation",
            "humidity",
            "wind_speed",
            "ndvi",
            "evi",
            "population_density",
            "elevation",
        ]

        # Base values and ranges for each feature
        feature_config = {
            "temperature": {"base": 25, "range": 10, "seasonal": True},
            "precipitation": {"base": 5, "range": 15, "seasonal": True},
            "humidity": {"base": 65, "range": 20, "seasonal": False},
            "wind_speed": {"base": 8, "range": 5, "seasonal": False},
            "ndvi": {"base": 0.6, "range": 0.3, "seasonal": True},
            "evi": {"base": 0.5, "range": 0.3, "seasonal": True},
            "population_density": {"base": 500, "range": 1000, "seasonal": False},
            "elevation": {"base": 1200, "range": 800, "seasonal": False},
        }

        features = np.zeros((n_timesteps, n_features))

        for i, feature_name in enumerate(feature_names[:n_features]):
            config = feature_config[feature_name]
            base_values = np.full(n_timesteps, config["base"])

            if add_patterns and config["seasonal"]:
                # Add seasonal pattern
                seasonal_pattern = np.sin(2 * np.pi * np.arange(n_timesteps) / 365) * (
                    config["range"] / 4
                )
                base_values += seasonal_pattern

            # Add random variation
            noise = np.random.normal(0, config["range"] / 10, n_timesteps)
            features[:, i] = base_values + noise

            # Ensure realistic ranges
            if feature_name == "ndvi" or feature_name == "evi":
                features[:, i] = np.clip(features[:, i], 0, 1)
            elif feature_name == "humidity":
                features[:, i] = np.clip(features[:, i], 0, 100)
            elif (
                feature_name == "precipitation"
                or feature_name == "population_density"
                or feature_name == "elevation"
            ):
                features[:, i] = np.clip(features[:, i], 0, None)  # Non-negative

        if normalize:
            # Simple min-max normalization per feature
            for i in range(n_features):
                feature_min = features[:, i].min()
                feature_max = features[:, i].max()
                if feature_max > feature_min:
                    features[:, i] = (features[:, i] - feature_min) / (
                        feature_max - feature_min
                    )

        return features.astype(np.float32)

    @staticmethod
    def create_prediction_response(
        risk_level: str = "medium",
        model_type: str = "ensemble",
        include_uncertainty: bool = True,
        include_explanations: bool = True,
    ) -> dict[str, Any]:
        """Create realistic prediction response."""

        # Risk level mapping
        risk_mappings = {
            "low": {"score": 0.25, "range": (0.1, 0.4)},
            "medium": {"score": 0.55, "range": (0.4, 0.7)},
            "high": {"score": 0.80, "range": (0.7, 0.95)},
        }

        risk_config = risk_mappings.get(risk_level, risk_mappings["medium"])
        risk_score = random.uniform(*risk_config["range"])

        # Confidence based on model type and risk level
        base_confidence = 0.85 if model_type == "ensemble" else 0.80
        confidence = base_confidence + random.uniform(-0.1, 0.05)

        # Class probabilities (low, medium, high)
        if risk_level == "low":
            class_probs = [
                0.6 + random.uniform(-0.1, 0.1),
                0.3 + random.uniform(-0.05, 0.05),
                0.1 + random.uniform(-0.05, 0.05),
            ]
        elif risk_level == "medium":
            class_probs = [
                0.2 + random.uniform(-0.05, 0.05),
                0.6 + random.uniform(-0.1, 0.1),
                0.2 + random.uniform(-0.05, 0.05),
            ]
        else:  # high
            class_probs = [
                0.1 + random.uniform(-0.05, 0.05),
                0.2 + random.uniform(-0.05, 0.05),
                0.7 + random.uniform(-0.1, 0.1),
            ]

        # Normalize probabilities
        total = sum(class_probs)
        class_probs = [p / total for p in class_probs]

        response = {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "confidence": round(confidence, 4),
            "predictions": {
                "low_risk": round(class_probs[0], 4),
                "medium_risk": round(class_probs[1], 4),
                "high_risk": round(class_probs[2], 4),
            },
            "model_metadata": {
                "model_type": model_type,
                "model_version": "v1.0.0",
                "inference_time_ms": random.randint(20, 80),
                "prediction_date": datetime.now().isoformat(),
            },
        }

        if include_uncertainty:
            uncertainty = max(0.05, (1 - confidence) * 1.2)
            response["uncertainty"] = {
                "standard_deviation": round(uncertainty, 4),
                "lower_bound": round(max(0, risk_score - 1.96 * uncertainty), 4),
                "upper_bound": round(min(1, risk_score + 1.96 * uncertainty), 4),
            }

        if include_explanations:
            # Contributing factors (should sum to 1.0)
            factors = {
                "temperature": random.uniform(0.15, 0.25),
                "precipitation": random.uniform(0.15, 0.25),
                "humidity": random.uniform(0.10, 0.20),
                "vegetation": random.uniform(0.15, 0.25),
                "population": random.uniform(0.05, 0.15),
                "historical": random.uniform(0.10, 0.20),
            }

            # Normalize factors
            total_factors = sum(factors.values())
            factors = {k: round(v / total_factors, 3) for k, v in factors.items()}

            response["contributing_factors"] = factors

        return response

    @staticmethod
    def create_batch_prediction_response(
        locations: list[Location],
        base_risk_level: str = "medium",
        add_spatial_correlation: bool = True,
    ) -> dict[str, Any]:
        """Create realistic batch prediction response."""

        predictions = []

        for i, location in enumerate(locations):
            # Add spatial correlation - nearby locations have similar risk
            if add_spatial_correlation and i > 0:
                # Adjust risk based on distance to previous location
                prev_location = locations[i - 1]
                distance = np.sqrt(
                    (location.latitude - prev_location.latitude) ** 2
                    + (location.longitude - prev_location.longitude) ** 2
                )

                # Closer locations have more similar risk
                max(0.2, 1 - distance / 10)  # Adjust based on distance

                if distance < 1.0:  # Very close locations
                    risk_level = base_risk_level  # Same risk level
                else:
                    # Randomly vary risk level for distant locations
                    risk_levels = ["low", "medium", "high"]
                    risk_level = random.choice(risk_levels)
            else:
                risk_level = base_risk_level

            prediction = PredictionDataFactory.create_prediction_response(
                risk_level=risk_level,
                model_type="ensemble",
                include_uncertainty=True,
                include_explanations=True,
            )
            prediction["location"] = location.dict()
            predictions.append(prediction)

        # Calculate batch summary statistics
        risk_scores = [p["risk_score"] for p in predictions]

        summary = {
            "total_locations": len(predictions),
            "mean_risk_score": round(np.mean(risk_scores), 4),
            "std_risk_score": round(np.std(risk_scores), 4),
            "min_risk_score": round(min(risk_scores), 4),
            "max_risk_score": round(max(risk_scores), 4),
            "high_risk_locations": sum(
                1 for p in predictions if p["risk_level"] == "high"
            ),
            "medium_risk_locations": sum(
                1 for p in predictions if p["risk_level"] == "medium"
            ),
            "low_risk_locations": sum(
                1 for p in predictions if p["risk_level"] == "low"
            ),
        }

        return {
            "predictions": predictions,
            "summary": summary,
            "batch_metadata": {
                "processing_time_ms": random.randint(100, 500),
                "parallel_processing": True,
                "batch_size": len(predictions),
                "timestamp": datetime.now().isoformat(),
            },
        }


class DatabaseTestDataFactory:
    """Factory for creating database test data."""

    @staticmethod
    def create_environmental_records(
        locations: list[Location],
        start_date: datetime,
        end_date: datetime,
        sources: list[str] = None,
    ) -> list[dict[str, Any]]:
        """Create environmental data records for database testing."""

        if sources is None:
            sources = ["era5", "chirps", "modis"]
        records = []
        date_range = pd.date_range(start_date, end_date, freq="D")

        for location in locations:
            for date in date_range:
                for source in sources:
                    if source == "era5":
                        # Daily ERA5-like record
                        record = {
                            "location": location.dict(),
                            "timestamp": date.to_pydatetime(),
                            "temperature": random.uniform(20, 30),
                            "precipitation": random.uniform(0, 20),
                            "humidity": random.uniform(50, 80),
                            "wind_speed": random.uniform(5, 15),
                            "data_source": "era5",
                        }
                    elif source == "chirps":
                        # Daily CHIRPS-like record
                        record = {
                            "location": location.dict(),
                            "timestamp": date.to_pydatetime(),
                            "precipitation": random.uniform(0, 25),
                            "data_source": "chirps",
                        }
                    elif source == "modis":
                        # 16-day MODIS-like record (only every 16 days)
                        if date.day % 16 == 1:
                            record = {
                                "location": location.dict(),
                                "timestamp": date.to_pydatetime(),
                                "ndvi": random.uniform(0.2, 0.8),
                                "evi": random.uniform(0.1, 0.7),
                                "lst_day": random.uniform(295, 315),  # Kelvin
                                "lst_night": random.uniform(280, 300),  # Kelvin
                                "data_source": "modis",
                            }
                        else:
                            continue

                    if "record" in locals():
                        records.append(record)

        return records

    @staticmethod
    def create_malaria_incidence_records(
        locations: list[Location],
        start_date: datetime,
        end_date: datetime,
        frequency: str = "M",  # Monthly
    ) -> list[dict[str, Any]]:
        """Create malaria incidence records for database testing."""

        records = []
        date_range = pd.date_range(start_date, end_date, freq=frequency)

        for location in locations:
            # Base incidence rate for location
            base_incidence = random.uniform(0.05, 0.25)

            for date in date_range:
                # Seasonal variation
                seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)
                incidence_rate = base_incidence * seasonal_factor

                # Population at risk (varies by location)
                population_at_risk = random.randint(10000, 100000)
                cases_reported = int(incidence_rate * population_at_risk)

                record = {
                    "location": location.dict(),
                    "date": date.date(),
                    "incidence_rate": round(incidence_rate, 4),
                    "parasite_rate": round(incidence_rate * 0.7, 4),
                    "mortality_rate": round(incidence_rate * 0.02, 4),
                    "age_group": "all",
                    "population_at_risk": population_at_risk,
                    "cases_reported": cases_reported,
                    "data_source": "national_surveillance",
                }
                records.append(record)

        return records


def save_test_fixtures(fixtures_dir: Path = None) -> None:
    """Save generated test fixtures to files."""

    if fixtures_dir is None:
        fixtures_dir = Path(__file__).parent / "data"

    fixtures_dir.mkdir(exist_ok=True)

    # Test locations
    from ..fixtures import TEST_LOCATIONS

    locations = [
        Location(
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            name=loc_data["name"],
        )
        for loc_data in TEST_LOCATIONS.values()
    ]

    # Date range for test data
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    # Generate and save environmental data fixtures
    env_factory = EnvironmentalDataFactory()

    for i, location in enumerate(locations):
        location_dir = fixtures_dir / f"location_{i + 1}"
        location_dir.mkdir(exist_ok=True)

        # ERA5 data
        era5_data = env_factory.create_era5_data(location, start_date, end_date)
        with open(location_dir / "era5_data.json", "w") as f:
            json.dump(era5_data, f, indent=2)

        # CHIRPS data
        chirps_data = env_factory.create_chirps_data(location, start_date, end_date)
        with open(location_dir / "chirps_data.json", "w") as f:
            json.dump(chirps_data, f, indent=2)

        # MODIS data
        modis_data = env_factory.create_modis_data(location, start_date, end_date)
        with open(location_dir / "modis_data.json", "w") as f:
            json.dump(modis_data, f, indent=2)

        # WorldPop data
        worldpop_data = env_factory.create_worldpop_data(location)
        with open(location_dir / "worldpop_data.json", "w") as f:
            json.dump(worldpop_data, f, indent=2)

        # MAP data
        map_data = env_factory.create_map_data(location)
        with open(location_dir / "map_data.json", "w") as f:
            json.dump(map_data, f, indent=2)

    # Generate and save prediction fixtures
    pred_factory = PredictionDataFactory()

    # Feature matrices
    feature_dir = fixtures_dir / "features"
    feature_dir.mkdir(exist_ok=True)

    for size in ["small", "medium", "large"]:
        if size == "small":
            n_timesteps, n_features = 10, 5
        elif size == "medium":
            n_timesteps, n_features = 30, 8
        else:  # large
            n_timesteps, n_features = 90, 12

        features = pred_factory.create_feature_matrix(n_timesteps, n_features)
        np.save(feature_dir / f"features_{size}.npy", features)

    # Prediction responses
    pred_dir = fixtures_dir / "predictions"
    pred_dir.mkdir(exist_ok=True)

    for risk_level in ["low", "medium", "high"]:
        prediction = pred_factory.create_prediction_response(risk_level=risk_level)
        with open(pred_dir / f"prediction_{risk_level}_risk.json", "w") as f:
            json.dump(prediction, f, indent=2)

    # Batch prediction response
    batch_response = pred_factory.create_batch_prediction_response(
        locations[:3], base_risk_level="medium"
    )
    with open(pred_dir / "batch_prediction_response.json", "w") as f:
        json.dump(batch_response, f, indent=2)

    print(f"Test fixtures saved to {fixtures_dir}")


if __name__ == "__main__":
    # Generate and save test fixtures
    save_test_fixtures()
