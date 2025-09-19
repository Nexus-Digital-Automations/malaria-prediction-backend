"""
Outbreak Detection Service

Advanced algorithms for detecting malaria outbreaks using statistical
and machine learning methods. Provides real-time anomaly detection
and early warning capabilities.

Author: AI Agent - Outbreak Pattern Recognition Specialist
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog
from geojson_pydantic import Point
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ..models import (
    OutbreakEvent,
    OutbreakMetrics,
    OutbreakSeverity,
    OutbreakStatus,
    SurveillanceData,
    TransmissionType,
)

logger = structlog.get_logger(__name__)


class OutbreakDetector:
    """
    Advanced outbreak detection service with anomaly detection and ML models.

    Implements multiple detection algorithms for identifying malaria outbreaks
    including statistical thresholds, time-series anomalies, and spatial clustering.
    """

    def __init__(self):
        """Initialize outbreak detector with configuration."""
        self.logger = logger.bind(service="outbreak_detector")

        # Detection algorithm configuration
        self.detection_methods = {
            "statistical_threshold": self._detect_statistical_threshold,
            "isolation_forest": self._detect_isolation_forest,
            "dbscan_clustering": self._detect_spatial_clustering,
            "epidemic_algorithm": self._detect_epidemic_algorithm,
            "seasonal_decomposition": self._detect_seasonal_anomaly
        }

        # Alert thresholds
        self.thresholds = {
            "case_increase_percent": 50.0,  # 50% increase threshold
            "test_positivity_rate": 0.15,   # 15% positivity rate
            "case_density_per_km2": 10.0,   # Cases per km²
            "doubling_time_days": 7.0,      # Case doubling time
            "statistical_significance": 0.05  # p-value threshold
        }

        # Model instances
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()

        self.logger.info("Outbreak detector initialized", thresholds=self.thresholds)

    async def detect_outbreaks(
        self,
        surveillance_data: list[SurveillanceData],
        method: str = "ensemble",
        confidence_threshold: float = 0.7
    ) -> list[OutbreakEvent]:
        """
        Detect outbreaks from surveillance data using specified method.

        Args:
            surveillance_data: List of surveillance data points
            method: Detection method ("ensemble" or specific method name)
            confidence_threshold: Minimum confidence for outbreak detection

        Returns:
            List of detected outbreak events
        """
        operation_id = f"detect_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(
            "Starting outbreak detection",
            operation_id=operation_id,
            data_points=len(surveillance_data),
            method=method,
            threshold=confidence_threshold
        )

        try:
            # Convert surveillance data to DataFrame for analysis
            df = self._prepare_surveillance_dataframe(surveillance_data)

            if df.empty:
                self.logger.warning("No surveillance data available for analysis")
                return []

            # Apply detection method(s)
            if method == "ensemble":
                detections = await self._ensemble_detection(df)
            elif method in self.detection_methods:
                detections = await self.detection_methods[method](df)
            else:
                raise ValueError(f"Unknown detection method: {method}")

            # Filter by confidence threshold
            valid_detections = [
                detection for detection in detections
                if detection.confidence_level >= confidence_threshold
            ]

            # Create outbreak events from detections
            outbreak_events = await self._create_outbreak_events(
                valid_detections,
                surveillance_data
            )

            self.logger.info(
                "Outbreak detection completed",
                operation_id=operation_id,
                total_detections=len(detections),
                valid_detections=len(valid_detections),
                outbreak_events=len(outbreak_events)
            )

            return outbreak_events

        except Exception as e:
            self.logger.error(
                "Outbreak detection failed",
                operation_id=operation_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def _ensemble_detection(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Run ensemble detection using multiple methods.

        Args:
            df: Prepared surveillance DataFrame

        Returns:
            List of detection results with confidence scores
        """
        self.logger.debug("Running ensemble detection")

        # Run all detection methods
        detection_results = []
        method_weights = {
            "statistical_threshold": 0.25,
            "isolation_forest": 0.20,
            "dbscan_clustering": 0.20,
            "epidemic_algorithm": 0.20,
            "seasonal_decomposition": 0.15
        }

        for method_name, weight in method_weights.items():
            try:
                results = await self.detection_methods[method_name](df)
                for result in results:
                    result["method"] = method_name
                    result["weight"] = weight
                    detection_results.append(result)
            except Exception as e:
                self.logger.warning(
                    f"Detection method {method_name} failed",
                    error=str(e)
                )

        # Combine and weight results
        combined_detections = self._combine_detection_results(detection_results)

        return combined_detections

    async def _detect_statistical_threshold(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Detect outbreaks using statistical threshold analysis.

        Args:
            df: Surveillance DataFrame

        Returns:
            List of detected anomalies
        """
        self.logger.debug("Running statistical threshold detection")

        detections = []

        # Group by location for analysis
        for location, group in df.groupby(['latitude', 'longitude']):
            if len(group) < 3:  # Need minimum data points
                continue

            # Calculate baseline statistics (last 30 days)
            baseline_period = group.tail(30)
            if len(baseline_period) < 3:
                continue

            # Calculate metrics
            baseline_mean = baseline_period['confirmed_cases'].mean()
            baseline_std = baseline_period['confirmed_cases'].std()
            current_cases = group['confirmed_cases'].iloc[-1]

            # Statistical significance test
            if baseline_std > 0:
                z_score = (current_cases - baseline_mean) / baseline_std
                p_value = 1 - stats.norm.cdf(abs(z_score))

                # Check thresholds
                case_increase = ((current_cases - baseline_mean) / max(baseline_mean, 1)) * 100
                positivity_rate = group['test_positivity_rate'].iloc[-1]

                if (p_value < self.thresholds["statistical_significance"] and
                    case_increase > self.thresholds["case_increase_percent"]):

                    detection = {
                        "location": Point(coordinates=[location[1], location[0]]),
                        "detection_date": group['reported_at'].iloc[-1],
                        "severity_score": min(abs(z_score) / 5.0, 1.0),
                        "confidence_level": 1 - p_value,
                        "metrics": {
                            "z_score": z_score,
                            "p_value": p_value,
                            "case_increase_percent": case_increase,
                            "baseline_mean": baseline_mean,
                            "current_cases": current_cases,
                            "positivity_rate": positivity_rate
                        }
                    }

                    detections.append(detection)

        self.logger.debug(f"Statistical threshold detection found {len(detections)} anomalies")
        return detections

    async def _detect_isolation_forest(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Detect outbreaks using Isolation Forest anomaly detection.

        Args:
            df: Surveillance DataFrame

        Returns:
            List of detected anomalies
        """
        self.logger.debug("Running Isolation Forest detection")

        if len(df) < 10:  # Need minimum samples
            return []

        # Prepare features for anomaly detection
        features = [
            'confirmed_cases', 'suspected_cases', 'test_positivity_rate',
            'vector_density', 'temperature_avg', 'rainfall_mm', 'humidity_avg'
        ]

        # Select available features and handle missing values
        available_features = [f for f in features if f in df.columns]
        feature_data = df[available_features].fillna(0)

        if feature_data.empty:
            return []

        # Scale features
        scaled_features = self.scaler.fit_transform(feature_data)

        # Fit Isolation Forest
        outliers = self.isolation_forest.fit_predict(scaled_features)
        scores = self.isolation_forest.score_samples(scaled_features)

        detections = []
        for idx, (is_outlier, score) in enumerate(zip(outliers, scores, strict=False)):
            if is_outlier == -1:  # Anomaly detected
                row = df.iloc[idx]

                detection = {
                    "location": Point(coordinates=[row['longitude'], row['latitude']]),
                    "detection_date": row['reported_at'],
                    "severity_score": min(abs(score) * 2, 1.0),
                    "confidence_level": min(abs(score) * 1.5, 1.0),
                    "metrics": {
                        "isolation_score": score,
                        "confirmed_cases": row['confirmed_cases'],
                        "feature_values": {f: row[f] for f in available_features}
                    }
                }

                detections.append(detection)

        self.logger.debug(f"Isolation Forest detection found {len(detections)} anomalies")
        return detections

    async def _detect_spatial_clustering(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Detect outbreak clusters using DBSCAN spatial clustering.

        Args:
            df: Surveillance DataFrame

        Returns:
            List of detected clusters
        """
        self.logger.debug("Running DBSCAN spatial clustering")

        if len(df) < 5:  # Need minimum points
            return []

        # Prepare spatial coordinates with case weights
        coordinates = df[['latitude', 'longitude']].values
        weights = df['confirmed_cases'].values

        # Apply DBSCAN clustering
        dbscan = DBSCAN(eps=0.01, min_samples=3)  # ~1km at equator
        clusters = dbscan.fit_predict(coordinates, sample_weight=weights)

        detections = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Skip noise points
                continue

            cluster_points = df[clusters == cluster_id]
            if len(cluster_points) < 3:
                continue

            # Calculate cluster statistics
            total_cases = cluster_points['confirmed_cases'].sum()
            centroid_lat = cluster_points['latitude'].mean()
            centroid_lon = cluster_points['longitude'].mean()
            cluster_density = total_cases / len(cluster_points)

            # Check if cluster exceeds density threshold
            if cluster_density > self.thresholds["case_density_per_km2"]:
                detection = {
                    "location": Point(coordinates=[centroid_lon, centroid_lat]),
                    "detection_date": cluster_points['reported_at'].max(),
                    "severity_score": min(cluster_density / 50.0, 1.0),
                    "confidence_level": min(len(cluster_points) / 10.0, 1.0),
                    "metrics": {
                        "cluster_size": len(cluster_points),
                        "total_cases": total_cases,
                        "case_density": cluster_density,
                        "cluster_id": cluster_id
                    }
                }

                detections.append(detection)

        self.logger.debug(f"Spatial clustering found {len(detections)} clusters")
        return detections

    async def _detect_epidemic_algorithm(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Detect outbreaks using epidemic curve analysis.

        Args:
            df: Surveillance DataFrame

        Returns:
            List of detected epidemic signals
        """
        self.logger.debug("Running epidemic algorithm detection")

        detections = []

        # Group by location for time series analysis
        for location, group in df.groupby(['latitude', 'longitude']):
            if len(group) < 7:  # Need at least a week of data
                continue

            # Sort by date
            group = group.sort_values('reported_at')

            # Calculate doubling time
            doubling_time = self._calculate_doubling_time(group['confirmed_cases'])

            if doubling_time and doubling_time < self.thresholds["doubling_time_days"]:
                # Calculate growth rate
                recent_cases = group['confirmed_cases'].tail(3).mean()
                baseline_cases = group['confirmed_cases'].head(3).mean()
                growth_rate = (recent_cases - baseline_cases) / max(baseline_cases, 1)

                detection = {
                    "location": Point(coordinates=[location[1], location[0]]),
                    "detection_date": group['reported_at'].iloc[-1],
                    "severity_score": min(growth_rate, 1.0),
                    "confidence_level": max(1 - (doubling_time / 14.0), 0.1),
                    "metrics": {
                        "doubling_time_days": doubling_time,
                        "growth_rate": growth_rate,
                        "recent_cases": recent_cases,
                        "baseline_cases": baseline_cases
                    }
                }

                detections.append(detection)

        self.logger.debug(f"Epidemic algorithm found {len(detections)} signals")
        return detections

    async def _detect_seasonal_anomaly(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Detect seasonal anomalies using decomposition analysis.

        Args:
            df: Surveillance DataFrame

        Returns:
            List of detected seasonal anomalies
        """
        self.logger.debug("Running seasonal anomaly detection")

        detections = []

        # Group by location for seasonal analysis
        for location, group in df.groupby(['latitude', 'longitude']):
            if len(group) < 52:  # Need at least a year of weekly data
                continue

            # Calculate seasonal baseline
            group = group.sort_values('reported_at')
            cases = group['confirmed_cases'].values

            # Simple seasonal decomposition
            seasonal_mean = self._calculate_seasonal_baseline(cases)
            current_cases = cases[-1]

            # Check for anomaly
            if current_cases > seasonal_mean * 2:  # 2x seasonal average
                seasonal_excess = (current_cases - seasonal_mean) / seasonal_mean

                detection = {
                    "location": Point(coordinates=[location[1], location[0]]),
                    "detection_date": group['reported_at'].iloc[-1],
                    "severity_score": min(seasonal_excess / 3.0, 1.0),
                    "confidence_level": min(seasonal_excess / 2.0, 1.0),
                    "metrics": {
                        "seasonal_baseline": seasonal_mean,
                        "current_cases": current_cases,
                        "seasonal_excess": seasonal_excess
                    }
                }

                detections.append(detection)

        self.logger.debug(f"Seasonal anomaly detection found {len(detections)} anomalies")
        return detections

    def _prepare_surveillance_dataframe(self, data: list[SurveillanceData]) -> pd.DataFrame:
        """Convert surveillance data to DataFrame for analysis."""
        records = []

        for item in data:
            record = {
                "surveillance_id": item.surveillance_id,
                "reported_at": item.reported_at,
                "latitude": item.location.coordinates[1],
                "longitude": item.location.coordinates[0],
                "confirmed_cases": item.confirmed_cases,
                "suspected_cases": item.suspected_cases,
                "severe_cases": item.severe_cases,
                "deaths": item.deaths,
                "test_positivity_rate": item.test_positivity_rate,
                "vector_density": item.vector_density,
                "temperature_avg": item.temperature_avg,
                "rainfall_mm": item.rainfall_mm,
                "humidity_avg": item.humidity_avg,
                "population_monitored": item.population_monitored
            }
            records.append(record)

        return pd.DataFrame(records)

    def _combine_detection_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Combine results from multiple detection methods."""
        # Group detections by location and time proximity
        combined = {}

        for result in results:
            location = result["location"]
            detection_date = result["detection_date"]

            # Create key based on location (rounded) and date
            lat = round(location.coordinates[1], 3)
            lon = round(location.coordinates[0], 3)
            date_key = detection_date.strftime("%Y%m%d")
            key = f"{lat}_{lon}_{date_key}"

            if key not in combined:
                combined[key] = {
                    "location": location,
                    "detection_date": detection_date,
                    "methods": [],
                    "total_weight": 0,
                    "weighted_severity": 0,
                    "weighted_confidence": 0
                }

            # Add method result
            weight = result.get("weight", 0.2)
            combined[key]["methods"].append(result)
            combined[key]["total_weight"] += weight
            combined[key]["weighted_severity"] += result["severity_score"] * weight
            combined[key]["weighted_confidence"] += result["confidence_level"] * weight

        # Calculate final scores
        final_detections = []
        for detection in combined.values():
            if detection["total_weight"] > 0:
                detection["severity_score"] = detection["weighted_severity"] / detection["total_weight"]
                detection["confidence_level"] = detection["weighted_confidence"] / detection["total_weight"]

                # Boost confidence for multiple method agreement
                method_count = len(detection["methods"])
                detection["confidence_level"] = min(
                    detection["confidence_level"] * (1 + 0.1 * method_count),
                    1.0
                )

                final_detections.append(detection)

        return final_detections

    async def _create_outbreak_events(
        self,
        detections: list[dict[str, Any]],
        surveillance_data: list[SurveillanceData]
    ) -> list[OutbreakEvent]:
        """Create OutbreakEvent objects from detections."""
        outbreak_events = []

        for idx, detection in enumerate(detections):
            try:
                # Determine severity based on score
                severity = self._score_to_severity(detection["severity_score"])

                # Generate outbreak ID
                outbreak_id = f"outbreak_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{idx}"

                # Find related surveillance data
                location = detection["location"]
                related_data = [
                    data for data in surveillance_data
                    if (abs(data.location.coordinates[1] - location.coordinates[1]) < 0.01 and
                        abs(data.location.coordinates[0] - location.coordinates[0]) < 0.01)
                ]

                # Calculate basic metrics
                total_cases = sum(data.confirmed_cases for data in related_data)
                total_population = sum(data.population_monitored for data in related_data)

                outbreak_event = OutbreakEvent(
                    outbreak_id=outbreak_id,
                    event_name=f"Detected Outbreak {idx + 1}",
                    location=location,
                    detection_date=detection["detection_date"],
                    onset_date=detection["detection_date"] - timedelta(days=7),  # Estimate
                    severity=severity,
                    status=OutbreakStatus.SUSPECTED,
                    transmission_type=TransmissionType.EPIDEMIC,
                    total_cases=total_cases,
                    population_at_risk=total_population,
                    source_organization="Automated Detection System",
                    confidence_level=detection["confidence_level"],
                    data_quality_score=0.8,  # Default for automated detection
                    created_by="outbreak_detector_service"
                )

                outbreak_events.append(outbreak_event)

            except Exception as e:
                self.logger.error(
                    "Failed to create outbreak event",
                    detection_index=idx,
                    error=str(e)
                )

        return outbreak_events

    def _score_to_severity(self, score: float) -> OutbreakSeverity:
        """Convert severity score to OutbreakSeverity enum."""
        if score >= 0.9:
            return OutbreakSeverity.EMERGENCY
        elif score >= 0.7:
            return OutbreakSeverity.CRITICAL
        elif score >= 0.5:
            return OutbreakSeverity.HIGH
        elif score >= 0.3:
            return OutbreakSeverity.MODERATE
        else:
            return OutbreakSeverity.LOW

    def _calculate_doubling_time(self, cases: pd.Series) -> float | None:
        """Calculate case doubling time in days."""
        if len(cases) < 3:
            return None

        # Find periods where cases double
        for i in range(len(cases) - 1):
            for j in range(i + 1, len(cases)):
                if cases.iloc[j] >= cases.iloc[i] * 2:
                    return float(j - i)

        return None

    def _calculate_seasonal_baseline(self, cases: np.ndarray) -> float:
        """Calculate seasonal baseline for anomaly detection."""
        if len(cases) < 52:
            return np.mean(cases)

        # Simple seasonal decomposition - calculate same week average
        current_week = len(cases) % 52
        seasonal_values = []

        for year_start in range(0, len(cases) - 52, 52):
            week_idx = year_start + current_week
            if week_idx < len(cases):
                seasonal_values.append(cases[week_idx])

        return np.mean(seasonal_values) if seasonal_values else np.mean(cases)

    async def calculate_outbreak_metrics(self, outbreak: OutbreakEvent) -> OutbreakMetrics:
        """Calculate comprehensive metrics for an outbreak."""
        try:
            metrics_id = f"metrics_{outbreak.outbreak_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Calculate basic epidemiological metrics
            attack_rate = 0.0
            if outbreak.population_at_risk > 0:
                attack_rate = outbreak.total_cases / outbreak.population_at_risk

            case_fatality_rate = 0.0
            if outbreak.total_cases > 0:
                case_fatality_rate = outbreak.deaths / outbreak.total_cases

            incidence_rate = (outbreak.total_cases / max(outbreak.population_at_risk, 1)) * 100000

            # Calculate severity index
            severity_components = {
                'attack_rate': min(attack_rate * 10, 1.0),
                'case_fatality_rate': case_fatality_rate,
                'total_cases': min(outbreak.total_cases / 1000, 1.0),
                'confidence': outbreak.confidence_level
            }

            severity_index = sum(severity_components.values()) / len(severity_components)

            metrics = OutbreakMetrics(
                metrics_id=metrics_id,
                outbreak_id=outbreak.outbreak_id,
                attack_rate=attack_rate,
                case_fatality_rate=case_fatality_rate,
                incidence_rate=incidence_rate,
                severity_index=severity_index,
                impact_score=min(outbreak.total_cases / 100, 1.0),
                urgency_level=int(outbreak.severity_score() * 5) + 1,
                spatial_extent_km2=100.0,  # Default estimate
                affected_communities=1,
                growth_rate=0.0,  # Would need time series data
                epidemic_phase="detection",
                confidence_score=outbreak.confidence_level,
                data_quality=outbreak.data_quality_score
            )

            self.logger.info(
                "Outbreak metrics calculated",
                outbreak_id=outbreak.outbreak_id,
                severity_index=severity_index,
                urgency_level=metrics.urgency_level
            )

            return metrics

        except Exception as e:
            self.logger.error(
                "Failed to calculate outbreak metrics",
                outbreak_id=outbreak.outbreak_id,
                error=str(e)
            )
            raise
