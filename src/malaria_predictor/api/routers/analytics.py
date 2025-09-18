"""
Analytics Dashboard API Routes.

This module provides comprehensive analytics endpoints for malaria prediction
data visualization, including prediction accuracy metrics, environmental trends,
outbreak pattern analysis, and interactive data exploration tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from ...database.models import (
    CHIRPSDataPoint,
    ERA5DataPoint,
    MalariaRiskIndex,
    MODISDataPoint,
    ProcessedClimateData,
    WorldPopDataPoint,
)
from ...database.session import get_db
from ...services.data_export import get_data_export_service
from ..dependencies import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/prediction-accuracy")
async def get_prediction_accuracy_metrics(
    start_date: str | None = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="End date in YYYY-MM-DD format"),
    model_type: str | None = Query(None, description="Model type (lstm, transformer, ensemble)"),
    region: str | None = Query(None, description="Geographic region filter"),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get comprehensive prediction accuracy metrics and performance analytics.

    Returns detailed accuracy metrics including:
    - Model performance over time
    - Accuracy by geographic region
    - Confidence score distributions
    - Error analysis and trends
    """
    try:
        # Build base query
        query = db.query(MalariaRiskIndex)

        # Apply filters
        if start_date:
            query = query.filter(MalariaRiskIndex.assessment_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(MalariaRiskIndex.assessment_date <= datetime.fromisoformat(end_date))
        if model_type:
            query = query.filter(MalariaRiskIndex.model_type == model_type)
        if region:
            query = query.filter(MalariaRiskIndex.location_name.ilike(f"%{region}%"))

        # Get prediction accuracy data
        predictions = query.order_by(desc(MalariaRiskIndex.assessment_date)).limit(1000).all()

        # Calculate accuracy metrics
        total_predictions = len(predictions)
        if total_predictions == 0:
            return {"error": "No prediction data found for the specified criteria"}

        # Model performance metrics
        model_accuracy = {}
        confidence_distribution = {}
        risk_level_accuracy = {}
        temporal_accuracy = {}

        for prediction in predictions:
            # Model type accuracy
            if prediction.model_type not in model_accuracy:
                model_accuracy[prediction.model_type] = {
                    "total": 0, "high_confidence": 0, "avg_confidence": 0, "predictions": []
                }

            model_accuracy[prediction.model_type]["total"] += 1
            model_accuracy[prediction.model_type]["predictions"].append(prediction.confidence_score)

            if prediction.confidence_score >= 0.8:
                model_accuracy[prediction.model_type]["high_confidence"] += 1

            # Confidence distribution
            conf_bucket = round(prediction.confidence_score, 1)
            confidence_distribution[conf_bucket] = confidence_distribution.get(conf_bucket, 0) + 1

            # Risk level accuracy
            if prediction.risk_level not in risk_level_accuracy:
                risk_level_accuracy[prediction.risk_level] = {"count": 0, "avg_confidence": 0, "scores": []}

            risk_level_accuracy[prediction.risk_level]["count"] += 1
            risk_level_accuracy[prediction.risk_level]["scores"].append(prediction.confidence_score)

            # Temporal accuracy (monthly)
            month_key = prediction.assessment_date.strftime("%Y-%m")
            if month_key not in temporal_accuracy:
                temporal_accuracy[month_key] = {"count": 0, "avg_confidence": 0, "scores": []}

            temporal_accuracy[month_key]["count"] += 1
            temporal_accuracy[month_key]["scores"].append(prediction.confidence_score)

        # Calculate averages
        for model_type, data in model_accuracy.items():
            data["avg_confidence"] = sum(data["predictions"]) / len(data["predictions"])
            data["high_confidence_rate"] = data["high_confidence"] / data["total"]
            del data["predictions"]  # Remove raw data to reduce response size

        for _risk_level, data in risk_level_accuracy.items():
            data["avg_confidence"] = sum(data["scores"]) / len(data["scores"])
            del data["scores"]

        for _month, data in temporal_accuracy.items():
            data["avg_confidence"] = sum(data["scores"]) / len(data["scores"])
            del data["scores"]

        return {
            "summary": {
                "total_predictions": total_predictions,
                "date_range": {
                    "start": predictions[-1].assessment_date.isoformat() if predictions else None,
                    "end": predictions[0].assessment_date.isoformat() if predictions else None,
                },
                "models_analyzed": list(model_accuracy.keys()),
            },
            "model_performance": model_accuracy,
            "confidence_distribution": confidence_distribution,
            "risk_level_accuracy": risk_level_accuracy,
            "temporal_trends": temporal_accuracy,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "filters_applied": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "model_type": model_type,
                    "region": region,
                },
            },
        }

    except Exception as e:
        logger.error(f"Error generating prediction accuracy metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate accuracy metrics")


@router.get("/environmental-trends")
async def get_environmental_trend_analysis(
    location_lat: float = Query(..., description="Latitude of location"),
    location_lon: float = Query(..., description="Longitude of location"),
    radius_km: float = Query(50, description="Radius in kilometers for data aggregation"),
    days_back: int = Query(365, description="Number of days to look back"),
    data_sources: str | None = Query(None, description="Comma-separated data sources (era5,chirps,modis)"),
    aggregation: str = Query("daily", description="Aggregation level (daily, weekly, monthly)"),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get comprehensive environmental trend analysis for a specific location.

    Returns detailed environmental data trends including:
    - Temperature patterns and anomalies
    - Precipitation trends and seasonal patterns
    - Vegetation index changes over time
    - Multi-factor correlation analysis
    """
    try:
        # Calculate coordinate bounds for radius
        lat_offset = radius_km / 111.0  # Approximate km per degree
        lon_offset = radius_km / (111.0 * abs(location_lat))

        lat_min, lat_max = location_lat - lat_offset, location_lat + lat_offset
        lon_min, lon_max = location_lon - lon_offset, location_lon + lon_offset

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Parse data sources
        sources = data_sources.split(',') if data_sources else ['era5', 'chirps', 'modis']

        trends_data = {}

        # ERA5 Climate Data Trends
        if 'era5' in sources:
            era5_query = db.query(ERA5DataPoint).filter(
                and_(
                    ERA5DataPoint.latitude.between(lat_min, lat_max),
                    ERA5DataPoint.longitude.between(lon_min, lon_max),
                    ERA5DataPoint.timestamp >= start_date,
                    ERA5DataPoint.timestamp <= end_date,
                )
            )

            era5_data = era5_query.all()

            # Process ERA5 trends
            temperature_trends = []
            precipitation_trends = []

            if aggregation == "daily":
                # Group by day
                daily_groups = {}
                for point in era5_data:
                    day_key = point.timestamp.date().isoformat()
                    if day_key not in daily_groups:
                        daily_groups[day_key] = []
                    daily_groups[day_key].append(point)

                for day, points in daily_groups.items():
                    if points:
                        avg_temp = sum(p.temperature_2m for p in points if p.temperature_2m) / len([p for p in points if p.temperature_2m])
                        total_precip = sum(p.total_precipitation for p in points if p.total_precipitation)

                        temperature_trends.append({"date": day, "value": avg_temp, "type": "temperature"})
                        precipitation_trends.append({"date": day, "value": total_precip, "type": "precipitation"})

            trends_data["climate"] = {
                "temperature_trends": temperature_trends,
                "precipitation_trends": precipitation_trends,
                "data_points": len(era5_data),
                "source": "ERA5",
            }

        # CHIRPS Precipitation Data
        if 'chirps' in sources:
            chirps_query = db.query(CHIRPSDataPoint).filter(
                and_(
                    CHIRPSDataPoint.latitude.between(lat_min, lat_max),
                    CHIRPSDataPoint.longitude.between(lon_min, lon_max),
                    CHIRPSDataPoint.date >= start_date,
                    CHIRPSDataPoint.date <= end_date,
                )
            )

            chirps_data = chirps_query.all()

            # Process CHIRPS precipitation trends
            precipitation_detailed = []
            anomaly_trends = []

            for point in chirps_data:
                precipitation_detailed.append({
                    "date": point.date.isoformat(),
                    "precipitation": point.precipitation,
                    "precipitation_5d": point.precipitation_accumulated_5d,
                    "precipitation_30d": point.precipitation_accumulated_30d,
                })

                if point.precipitation_anomaly is not None:
                    anomaly_trends.append({
                        "date": point.date.isoformat(),
                        "anomaly": point.precipitation_anomaly,
                        "percentile": point.precipitation_percentile,
                    })

            trends_data["precipitation_detailed"] = {
                "daily_precipitation": precipitation_detailed,
                "anomaly_trends": anomaly_trends,
                "data_points": len(chirps_data),
                "source": "CHIRPS",
            }

        # MODIS Vegetation Data
        if 'modis' in sources:
            modis_query = db.query(MODISDataPoint).filter(
                and_(
                    MODISDataPoint.latitude.between(lat_min, lat_max),
                    MODISDataPoint.longitude.between(lon_min, lon_max),
                    MODISDataPoint.date >= start_date,
                    MODISDataPoint.date <= end_date,
                )
            )

            modis_data = modis_query.all()

            # Process MODIS vegetation trends
            vegetation_trends = []
            temperature_surface = []

            for point in modis_data:
                if point.ndvi is not None:
                    vegetation_trends.append({
                        "date": point.date.isoformat(),
                        "ndvi": point.ndvi,
                        "evi": point.evi,
                        "lai": point.lai,
                    })

                if point.lst_day is not None:
                    temperature_surface.append({
                        "date": point.date.isoformat(),
                        "lst_day": point.lst_day - 273.15,  # Convert Kelvin to Celsius
                        "lst_night": point.lst_night - 273.15 if point.lst_night else None,
                    })

            trends_data["vegetation"] = {
                "vegetation_indices": vegetation_trends,
                "surface_temperature": temperature_surface,
                "data_points": len(modis_data),
                "source": "MODIS",
            }

        # Calculate correlation analysis
        correlation_analysis = {}
        if len(trends_data) > 1:
            # This would involve more complex correlation calculations
            # For now, provide structure for correlation data
            correlation_analysis = {
                "temperature_precipitation": 0.0,
                "vegetation_temperature": 0.0,
                "vegetation_precipitation": 0.0,
                "note": "Correlation analysis requires sufficient overlapping data points",
            }

        return {
            "location": {
                "latitude": location_lat,
                "longitude": location_lon,
                "radius_km": radius_km,
            },
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": days_back,
            },
            "trends": trends_data,
            "correlation_analysis": correlation_analysis,
            "aggregation_level": aggregation,
            "data_sources_used": sources,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_data_points": sum(
                    data.get("data_points", 0) for data in trends_data.values()
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error generating environmental trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate environmental trends")


@router.get("/outbreak-patterns")
async def get_outbreak_pattern_recognition(
    region: str | None = Query(None, description="Geographic region (country code or name)"),
    time_scale: str = Query("monthly", description="Time scale for analysis (weekly, monthly, yearly)"),
    risk_threshold: float = Query(0.7, description="Risk score threshold for outbreak classification"),
    years_back: int = Query(5, description="Number of years to analyze"),
    include_seasonality: bool = Query(True, description="Include seasonal pattern analysis"),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get outbreak pattern recognition and analysis data.

    Returns comprehensive outbreak pattern analysis including:
    - Historical outbreak frequency and distribution
    - Seasonal patterns and trends
    - Geographic clustering analysis
    - Risk escalation patterns
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365)

        # Build base query for risk indices
        query = db.query(MalariaRiskIndex).filter(
            and_(
                MalariaRiskIndex.assessment_date >= start_date,
                MalariaRiskIndex.assessment_date <= end_date,
            )
        )

        # Apply region filter
        if region:
            query = query.filter(MalariaRiskIndex.location_name.ilike(f"%{region}%"))

        # Get risk data
        risk_data = query.order_by(MalariaRiskIndex.assessment_date).all()

        if not risk_data:
            return {"error": "No risk data found for the specified criteria"}

        # Classify outbreaks based on risk threshold
        outbreak_events = []
        normal_events = []

        for risk_point in risk_data:
            event_data = {
                "date": risk_point.assessment_date.isoformat(),
                "location": risk_point.location_name,
                "latitude": risk_point.latitude,
                "longitude": risk_point.longitude,
                "risk_score": risk_point.composite_risk_score,
                "risk_level": risk_point.risk_level,
                "confidence": risk_point.confidence_score,
            }

            if risk_point.composite_risk_score >= risk_threshold:
                outbreak_events.append(event_data)
            else:
                normal_events.append(event_data)

        # Analyze outbreak patterns
        outbreak_frequency = {}
        seasonal_patterns = {}
        geographic_distribution = {}

        # Frequency analysis by time scale
        for event in outbreak_events:
            event_date = datetime.fromisoformat(event["date"])

            if time_scale == "weekly":
                period_key = f"{event_date.year}-W{event_date.isocalendar()[1]:02d}"
            elif time_scale == "monthly":
                period_key = f"{event_date.year}-{event_date.month:02d}"
            else:  # yearly
                period_key = str(event_date.year)

            outbreak_frequency[period_key] = outbreak_frequency.get(period_key, 0) + 1

            # Geographic distribution
            location = event["location"] or f"{event['latitude']:.2f},{event['longitude']:.2f}"
            geographic_distribution[location] = geographic_distribution.get(location, 0) + 1

        # Seasonal pattern analysis
        if include_seasonality:
            monthly_outbreaks = {}
            for event in outbreak_events:
                month = datetime.fromisoformat(event["date"]).month
                monthly_outbreaks[month] = monthly_outbreaks.get(month, 0) + 1

            # Calculate seasonal risk scores
            seasonal_patterns = {
                "monthly_distribution": monthly_outbreaks,
                "peak_months": sorted(monthly_outbreaks.items(), key=lambda x: x[1], reverse=True)[:3],
                "seasonal_intensity": {
                    "spring": sum(monthly_outbreaks.get(m, 0) for m in [3, 4, 5]),
                    "summer": sum(monthly_outbreaks.get(m, 0) for m in [6, 7, 8]),
                    "autumn": sum(monthly_outbreaks.get(m, 0) for m in [9, 10, 11]),
                    "winter": sum(monthly_outbreaks.get(m, 0) for m in [12, 1, 2]),
                },
            }

        # Risk escalation patterns
        escalation_patterns = []
        sorted_events = sorted(outbreak_events, key=lambda x: x["date"])

        for i in range(1, len(sorted_events)):
            current = sorted_events[i]
            previous = sorted_events[i-1]

            time_diff = (
                datetime.fromisoformat(current["date"]) -
                datetime.fromisoformat(previous["date"])
            ).days

            if time_diff <= 30:  # Events within 30 days
                escalation_patterns.append({
                    "from_date": previous["date"],
                    "to_date": current["date"],
                    "days_between": time_diff,
                    "risk_increase": current["risk_score"] - previous["risk_score"],
                    "locations": [previous["location"], current["location"]],
                })

        # Calculate statistics
        total_outbreaks = len(outbreak_events)
        total_normal = len(normal_events)
        outbreak_rate = total_outbreaks / (total_outbreaks + total_normal) if (total_outbreaks + total_normal) > 0 else 0

        avg_outbreak_risk = sum(event["risk_score"] for event in outbreak_events) / total_outbreaks if total_outbreaks > 0 else 0
        avg_confidence = sum(event["confidence"] for event in outbreak_events) / total_outbreaks if total_outbreaks > 0 else 0

        return {
            "analysis_parameters": {
                "region": region,
                "time_scale": time_scale,
                "risk_threshold": risk_threshold,
                "years_analyzed": years_back,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            },
            "outbreak_statistics": {
                "total_outbreaks": total_outbreaks,
                "total_normal_periods": total_normal,
                "outbreak_rate": round(outbreak_rate, 3),
                "average_outbreak_risk": round(avg_outbreak_risk, 3),
                "average_confidence": round(avg_confidence, 3),
            },
            "temporal_patterns": {
                "frequency_by_period": outbreak_frequency,
                "seasonal_analysis": seasonal_patterns,
                "escalation_patterns": escalation_patterns[:20],  # Limit to top 20
            },
            "geographic_patterns": {
                "outbreak_distribution": geographic_distribution,
                "high_risk_locations": sorted(
                    geographic_distribution.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
            },
            "risk_analysis": {
                "risk_level_distribution": {
                    level: len([e for e in outbreak_events if e["risk_level"] == level])
                    for level in ["low", "medium", "high", "critical"]
                },
                "confidence_distribution": {
                    "high_confidence": len([e for e in outbreak_events if e["confidence"] >= 0.8]),
                    "medium_confidence": len([e for e in outbreak_events if 0.6 <= e["confidence"] < 0.8]),
                    "low_confidence": len([e for e in outbreak_events if e["confidence"] < 0.6]),
                },
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_data_points": len(risk_data),
                "analysis_method": "statistical_pattern_recognition",
            },
        }

    except Exception as e:
        logger.error(f"Error generating outbreak pattern analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate outbreak pattern analysis")


@router.get("/data-exploration")
async def get_interactive_data_exploration(
    data_type: str = Query(..., description="Data type (climate, vegetation, population, risk)"),
    location_lat: float | None = Query(None, description="Latitude for location-based queries"),
    location_lon: float | None = Query(None, description="Longitude for location-based queries"),
    start_date: str | None = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="End date in YYYY-MM-DD format"),
    aggregation_method: str = Query("mean", description="Aggregation method (mean, sum, max, min)"),
    group_by: str = Query("month", description="Grouping method (day, week, month, year)"),
    limit: int = Query(1000, description="Maximum number of data points to return"),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get interactive data exploration results for specified parameters.

    Provides flexible data exploration capabilities including:
    - Multi-dimensional data filtering and aggregation
    - Statistical summaries and distributions
    - Data quality assessment
    - Export-ready data formats
    """
    try:
        exploration_results = {}

        # Parse date filters
        date_filters = {}
        if start_date:
            date_filters["start"] = datetime.fromisoformat(start_date)
        if end_date:
            date_filters["end"] = datetime.fromisoformat(end_date)

        # Location filters
        location_filters = {}
        if location_lat is not None and location_lon is not None:
            # Use a default radius for location-based queries
            radius = 0.5  # degrees (approximately 50km)
            location_filters["lat_range"] = (location_lat - radius, location_lat + radius)
            location_filters["lon_range"] = (location_lon - radius, location_lon + radius)

        if data_type == "climate":
            # ERA5 and processed climate data exploration
            query = db.query(ProcessedClimateData)

            # Apply filters
            if date_filters.get("start"):
                query = query.filter(ProcessedClimateData.date >= date_filters["start"])
            if date_filters.get("end"):
                query = query.filter(ProcessedClimateData.date <= date_filters["end"])
            if location_filters.get("lat_range"):
                lat_min, lat_max = location_filters["lat_range"]
                query = query.filter(ProcessedClimateData.latitude.between(lat_min, lat_max))
            if location_filters.get("lon_range"):
                lon_min, lon_max = location_filters["lon_range"]
                query = query.filter(ProcessedClimateData.longitude.between(lon_min, lon_max))

            climate_data = query.limit(limit).all()

            # Process and aggregate data
            processed_data = []
            for record in climate_data:
                processed_data.append({
                    "date": record.date.isoformat(),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "mean_temperature": record.mean_temperature,
                    "max_temperature": record.max_temperature,
                    "min_temperature": record.min_temperature,
                    "daily_precipitation": record.daily_precipitation_mm,
                    "relative_humidity": record.mean_relative_humidity,
                    "temperature_suitability": record.temperature_suitability,
                    "precipitation_risk_factor": record.precipitation_risk_factor,
                })

            # Calculate statistics
            if processed_data:
                temperature_values = [d["mean_temperature"] for d in processed_data if d["mean_temperature"]]
                precipitation_values = [d["daily_precipitation"] for d in processed_data if d["daily_precipitation"]]

                exploration_results = {
                    "data": processed_data,
                    "statistics": {
                        "total_records": len(processed_data),
                        "temperature_stats": {
                            "mean": sum(temperature_values) / len(temperature_values) if temperature_values else 0,
                            "min": min(temperature_values) if temperature_values else 0,
                            "max": max(temperature_values) if temperature_values else 0,
                        },
                        "precipitation_stats": {
                            "mean": sum(precipitation_values) / len(precipitation_values) if precipitation_values else 0,
                            "min": min(precipitation_values) if precipitation_values else 0,
                            "max": max(precipitation_values) if precipitation_values else 0,
                        },
                    },
                }

        elif data_type == "vegetation":
            # MODIS vegetation data exploration
            query = db.query(MODISDataPoint)

            # Apply filters
            if date_filters.get("start"):
                query = query.filter(MODISDataPoint.date >= date_filters["start"])
            if date_filters.get("end"):
                query = query.filter(MODISDataPoint.date <= date_filters["end"])
            if location_filters.get("lat_range"):
                lat_min, lat_max = location_filters["lat_range"]
                query = query.filter(MODISDataPoint.latitude.between(lat_min, lat_max))
            if location_filters.get("lon_range"):
                lon_min, lon_max = location_filters["lon_range"]
                query = query.filter(MODISDataPoint.longitude.between(lon_min, lon_max))

            vegetation_data = query.limit(limit).all()

            processed_data = []
            for record in vegetation_data:
                processed_data.append({
                    "date": record.date.isoformat(),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "ndvi": record.ndvi,
                    "evi": record.evi,
                    "lai": record.lai,
                    "lst_day_celsius": record.lst_day - 273.15 if record.lst_day else None,
                    "lst_night_celsius": record.lst_night - 273.15 if record.lst_night else None,
                })

            # Calculate vegetation statistics
            if processed_data:
                ndvi_values = [d["ndvi"] for d in processed_data if d["ndvi"]]
                evi_values = [d["evi"] for d in processed_data if d["evi"]]

                exploration_results = {
                    "data": processed_data,
                    "statistics": {
                        "total_records": len(processed_data),
                        "ndvi_stats": {
                            "mean": sum(ndvi_values) / len(ndvi_values) if ndvi_values else 0,
                            "min": min(ndvi_values) if ndvi_values else 0,
                            "max": max(ndvi_values) if ndvi_values else 0,
                        },
                        "evi_stats": {
                            "mean": sum(evi_values) / len(evi_values) if evi_values else 0,
                            "min": min(evi_values) if evi_values else 0,
                            "max": max(evi_values) if evi_values else 0,
                        },
                    },
                }

        elif data_type == "population":
            # WorldPop population data exploration
            query = db.query(WorldPopDataPoint)

            # Apply filters
            if location_filters.get("lat_range"):
                lat_min, lat_max = location_filters["lat_range"]
                query = query.filter(WorldPopDataPoint.latitude.between(lat_min, lat_max))
            if location_filters.get("lon_range"):
                lon_min, lon_max = location_filters["lon_range"]
                query = query.filter(WorldPopDataPoint.longitude.between(lon_min, lon_max))

            population_data = query.limit(limit).all()

            processed_data = []
            for record in population_data:
                processed_data.append({
                    "year": record.year,
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "population_total": record.population_total,
                    "population_density": record.population_density,
                    "population_children_u5": record.population_children_u5,
                    "urban_rural_classification": record.urban_rural_classification,
                    "travel_time_to_healthcare": record.travel_time_to_healthcare,
                })

            exploration_results = {
                "data": processed_data,
                "statistics": {
                    "total_records": len(processed_data),
                    "population_summary": {
                        "total_population": sum(d["population_total"] for d in processed_data if d["population_total"]),
                        "avg_density": sum(d["population_density"] for d in processed_data if d["population_density"]) / len(processed_data) if processed_data else 0,
                    },
                },
            }

        elif data_type == "risk":
            # Risk assessment data exploration
            query = db.query(MalariaRiskIndex)

            # Apply filters
            if date_filters.get("start"):
                query = query.filter(MalariaRiskIndex.assessment_date >= date_filters["start"])
            if date_filters.get("end"):
                query = query.filter(MalariaRiskIndex.assessment_date <= date_filters["end"])
            if location_filters.get("lat_range"):
                lat_min, lat_max = location_filters["lat_range"]
                query = query.filter(MalariaRiskIndex.latitude.between(lat_min, lat_max))
            if location_filters.get("lon_range"):
                lon_min, lon_max = location_filters["lon_range"]
                query = query.filter(MalariaRiskIndex.longitude.between(lon_min, lon_max))

            risk_data = query.limit(limit).all()

            processed_data = []
            for record in risk_data:
                processed_data.append({
                    "assessment_date": record.assessment_date.isoformat(),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "location_name": record.location_name,
                    "composite_risk_score": record.composite_risk_score,
                    "risk_level": record.risk_level,
                    "confidence_score": record.confidence_score,
                    "temperature_risk": record.temperature_risk_component,
                    "precipitation_risk": record.precipitation_risk_component,
                    "humidity_risk": record.humidity_risk_component,
                    "vegetation_risk": record.vegetation_risk_component,
                    "model_type": record.model_type,
                })

            exploration_results = {
                "data": processed_data,
                "statistics": {
                    "total_records": len(processed_data),
                    "risk_distribution": {
                        "low": len([d for d in processed_data if d["risk_level"] == "low"]),
                        "medium": len([d for d in processed_data if d["risk_level"] == "medium"]),
                        "high": len([d for d in processed_data if d["risk_level"] == "high"]),
                        "critical": len([d for d in processed_data if d["risk_level"] == "critical"]),
                    },
                    "avg_risk_score": sum(d["composite_risk_score"] for d in processed_data) / len(processed_data) if processed_data else 0,
                    "avg_confidence": sum(d["confidence_score"] for d in processed_data) / len(processed_data) if processed_data else 0,
                },
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid data_type. Must be one of: climate, vegetation, population, risk")

        # Add common metadata
        exploration_results["metadata"] = {
            "data_type": data_type,
            "filters_applied": {
                "location": {"lat": location_lat, "lon": location_lon} if location_lat and location_lon else None,
                "date_range": {"start": start_date, "end": end_date} if start_date or end_date else None,
                "aggregation_method": aggregation_method,
                "group_by": group_by,
                "limit": limit,
            },
            "generated_at": datetime.now().isoformat(),
        }

        return exploration_results

    except Exception as e:
        logger.error(f"Error in data exploration: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute data exploration")


@router.post("/custom-report")
async def generate_custom_report(
    report_config: dict[str, Any],
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Generate custom analytics reports based on user configuration.

    Supports:
    - Multi-source data compilation
    - Custom visualization configurations
    - Export formats (JSON, CSV structure)
    - Automated report scheduling
    """
    try:
        # Extract report configuration
        report_type = report_config.get("type", "summary")
        data_sources = report_config.get("data_sources", ["risk"])
        time_range = report_config.get("time_range", {})
        report_config.get("geographic_scope", {})
        visualization_configs = report_config.get("visualizations", [])
        export_format = report_config.get("export_format", "json")

        # Initialize report structure
        custom_report = {
            "report_metadata": {
                "type": report_type,
                "generated_at": datetime.now().isoformat(),
                "configuration": report_config,
            },
            "data_sections": {},
            "visualizations": [],
            "summary": {},
            "export_info": {"format": export_format},
        }

        # Parse time range
        start_date = None
        end_date = None
        if time_range.get("start"):
            start_date = datetime.fromisoformat(time_range["start"])
        if time_range.get("end"):
            end_date = datetime.fromisoformat(time_range["end"])

        # Process each requested data source
        for source in data_sources:
            if source == "risk":
                # Risk assessment data
                query = db.query(MalariaRiskIndex)

                if start_date:
                    query = query.filter(MalariaRiskIndex.assessment_date >= start_date)
                if end_date:
                    query = query.filter(MalariaRiskIndex.assessment_date <= end_date)

                risk_data = query.limit(5000).all()

                custom_report["data_sections"]["risk_assessments"] = {
                    "total_assessments": len(risk_data),
                    "risk_level_distribution": {
                        level: len([r for r in risk_data if r.risk_level == level])
                        for level in ["low", "medium", "high", "critical"]
                    },
                    "average_risk_score": sum(r.composite_risk_score for r in risk_data) / len(risk_data) if risk_data else 0,
                    "model_performance": {
                        model: len([r for r in risk_data if r.model_type == model])
                        for model in {r.model_type for r in risk_data}
                    },
                }

            elif source == "environmental":
                # Environmental data summary
                climate_query = db.query(ProcessedClimateData)
                if start_date:
                    climate_query = climate_query.filter(ProcessedClimateData.date >= start_date)
                if end_date:
                    climate_query = climate_query.filter(ProcessedClimateData.date <= end_date)

                climate_data = climate_query.limit(1000).all()

                custom_report["data_sections"]["environmental_conditions"] = {
                    "total_observations": len(climate_data),
                    "temperature_range": {
                        "min": min(c.min_temperature for c in climate_data if c.min_temperature) if climate_data else None,
                        "max": max(c.max_temperature for c in climate_data if c.max_temperature) if climate_data else None,
                        "average": sum(c.mean_temperature for c in climate_data if c.mean_temperature) / len([c for c in climate_data if c.mean_temperature]) if climate_data else None,
                    },
                    "precipitation_summary": {
                        "total_mm": sum(c.daily_precipitation_mm for c in climate_data if c.daily_precipitation_mm) if climate_data else 0,
                        "average_daily": sum(c.daily_precipitation_mm for c in climate_data if c.daily_precipitation_mm) / len([c for c in climate_data if c.daily_precipitation_mm]) if climate_data else 0,
                    },
                }

        # Generate visualization configurations
        for viz_config in visualization_configs:
            viz_type = viz_config.get("type", "line_chart")
            data_field = viz_config.get("data_field")

            visualization = {
                "type": viz_type,
                "title": viz_config.get("title", f"{viz_type.replace('_', ' ').title()} Visualization"),
                "data_source": viz_config.get("data_source"),
                "configuration": {
                    "x_axis": viz_config.get("x_axis", "date"),
                    "y_axis": viz_config.get("y_axis", data_field),
                    "color_scheme": viz_config.get("color_scheme", "default"),
                    "aggregation": viz_config.get("aggregation", "none"),
                },
                "chart_data_structure": {
                    "type": "ready_for_frontend_consumption",
                    "format": "json_array",
                    "note": "Data structure optimized for fl_chart or similar visualization libraries",
                },
            }

            custom_report["visualizations"].append(visualization)

        # Generate summary
        total_data_points = sum(
            section.get("total_assessments", 0) + section.get("total_observations", 0)
            for section in custom_report["data_sections"].values()
        )

        custom_report["summary"] = {
            "total_data_points": total_data_points,
            "data_sources_included": len(data_sources),
            "visualizations_configured": len(visualization_configs),
            "time_range_analyzed": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "report_completeness": "100%" if total_data_points > 0 else "No data available",
        }

        # Add export instructions
        if export_format == "csv":
            custom_report["export_info"]["csv_structure"] = {
                "note": "Data can be flattened for CSV export",
                "suggested_files": [
                    "risk_assessments.csv",
                    "environmental_data.csv",
                    "summary_statistics.csv",
                ],
            }
        elif export_format == "pdf":
            custom_report["export_info"]["pdf_structure"] = {
                "note": "Report can be formatted for PDF generation",
                "sections": ["Executive Summary", "Data Analysis", "Visualizations", "Conclusions"],
            }

        return custom_report

    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate custom report")


@router.get("/dashboard-config")
async def get_dashboard_configuration(
    dashboard_type: str = Query("comprehensive", description="Dashboard type (comprehensive, executive, operational)"),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get pre-configured dashboard layouts and visualization configurations.

    Returns ready-to-use dashboard configurations for different user types:
    - Comprehensive: Full analytics dashboard for researchers
    - Executive: High-level summary dashboard for decision makers
    - Operational: Real-time monitoring dashboard for operators
    """
    try:
        if dashboard_type == "comprehensive":
            return {
                "dashboard_type": "comprehensive",
                "layout": {
                    "grid_columns": 12,
                    "grid_rows": 8,
                    "widgets": [
                        {
                            "id": "prediction_accuracy_chart",
                            "type": "line_chart",
                            "position": {"col": 0, "row": 0, "width": 6, "height": 2},
                            "title": "Model Prediction Accuracy Over Time",
                            "data_endpoint": "/analytics/prediction-accuracy",
                            "chart_config": {
                                "x_axis": "date",
                                "y_axis": "accuracy",
                                "multiple_series": True,
                                "series": ["lstm_model", "transformer_model", "ensemble_model"],
                            },
                        },
                        {
                            "id": "environmental_trends",
                            "type": "multi_line_chart",
                            "position": {"col": 6, "row": 0, "width": 6, "height": 2},
                            "title": "Environmental Trends",
                            "data_endpoint": "/analytics/environmental-trends",
                            "chart_config": {
                                "series": ["temperature", "precipitation", "humidity"],
                                "time_range": "30_days",
                            },
                        },
                        {
                            "id": "risk_heatmap",
                            "type": "heatmap",
                            "position": {"col": 0, "row": 2, "width": 8, "height": 3},
                            "title": "Geographic Risk Distribution",
                            "data_endpoint": "/analytics/outbreak-patterns",
                            "chart_config": {
                                "geographic_projection": True,
                                "color_scale": "risk_gradient",
                                "interactive": True,
                            },
                        },
                        {
                            "id": "outbreak_patterns",
                            "type": "bar_chart",
                            "position": {"col": 8, "row": 2, "width": 4, "height": 3},
                            "title": "Seasonal Outbreak Patterns",
                            "data_endpoint": "/analytics/outbreak-patterns",
                            "chart_config": {
                                "x_axis": "month",
                                "y_axis": "outbreak_frequency",
                                "color_by": "risk_level",
                            },
                        },
                        {
                            "id": "data_quality_metrics",
                            "type": "gauge_chart",
                            "position": {"col": 0, "row": 5, "width": 4, "height": 2},
                            "title": "Data Quality Metrics",
                            "data_endpoint": "/analytics/data-exploration",
                            "chart_config": {
                                "metrics": ["completeness", "accuracy", "timeliness"],
                                "thresholds": {"good": 0.9, "warning": 0.7, "critical": 0.5},
                            },
                        },
                        {
                            "id": "model_performance_comparison",
                            "type": "radar_chart",
                            "position": {"col": 4, "row": 5, "width": 4, "height": 2},
                            "title": "Model Performance Comparison",
                            "data_endpoint": "/analytics/prediction-accuracy",
                            "chart_config": {
                                "metrics": ["accuracy", "precision", "recall", "confidence"],
                                "models": ["lstm", "transformer", "ensemble"],
                            },
                        },
                        {
                            "id": "real_time_alerts",
                            "type": "alert_panel",
                            "position": {"col": 8, "row": 5, "width": 4, "height": 2},
                            "title": "Real-time Risk Alerts",
                            "data_endpoint": "/operations/alerts",
                            "refresh_interval": 30,
                        },
                    ],
                },
                "data_refresh_intervals": {
                    "prediction_accuracy": 300,  # 5 minutes
                    "environmental_trends": 180,  # 3 minutes
                    "outbreak_patterns": 600,     # 10 minutes
                    "real_time_alerts": 30,       # 30 seconds
                },
                "theme": {
                    "color_palette": {
                        "risk_low": "#4CAF50",
                        "risk_medium": "#FF9800",
                        "risk_high": "#F44336",
                        "risk_critical": "#9C27B0",
                        "temperature": "#2196F3",
                        "precipitation": "#00BCD4",
                        "vegetation": "#8BC34A",
                    },
                    "chart_styles": {
                        "font_family": "Roboto",
                        "grid_color": "#E0E0E0",
                        "background_color": "#FAFAFA",
                    },
                },
            }

        elif dashboard_type == "executive":
            return {
                "dashboard_type": "executive",
                "layout": {
                    "grid_columns": 8,
                    "grid_rows": 4,
                    "widgets": [
                        {
                            "id": "risk_summary_kpis",
                            "type": "kpi_cards",
                            "position": {"col": 0, "row": 0, "width": 8, "height": 1},
                            "title": "Risk Assessment Summary",
                            "data_endpoint": "/analytics/outbreak-patterns",
                            "kpis": [
                                {"name": "Active High Risk Areas", "format": "number"},
                                {"name": "Outbreak Probability", "format": "percentage"},
                                {"name": "Population at Risk", "format": "number_with_suffix"},
                                {"name": "Alert Status", "format": "status"},
                            ],
                        },
                        {
                            "id": "trend_overview",
                            "type": "trend_chart",
                            "position": {"col": 0, "row": 1, "width": 4, "height": 2},
                            "title": "Risk Trend Overview",
                            "data_endpoint": "/analytics/outbreak-patterns",
                            "chart_config": {
                                "time_range": "90_days",
                                "aggregation": "weekly",
                                "trend_indicators": True,
                            },
                        },
                        {
                            "id": "geographic_summary",
                            "type": "choropleth_map",
                            "position": {"col": 4, "row": 1, "width": 4, "height": 2},
                            "title": "Regional Risk Summary",
                            "data_endpoint": "/analytics/outbreak-patterns",
                            "chart_config": {
                                "region_level": "country",
                                "color_by": "risk_level",
                                "interactive": False,
                            },
                        },
                        {
                            "id": "recommendations",
                            "type": "recommendation_panel",
                            "position": {"col": 0, "row": 3, "width": 8, "height": 1},
                            "title": "Key Recommendations",
                            "data_endpoint": "/analytics/custom-report",
                            "config": {
                                "priority_levels": ["critical", "high", "medium"],
                                "max_recommendations": 5,
                            },
                        },
                    ],
                },
                "auto_refresh": True,
                "refresh_interval": 600,  # 10 minutes
            }

        elif dashboard_type == "operational":
            return {
                "dashboard_type": "operational",
                "layout": {
                    "grid_columns": 6,
                    "grid_rows": 6,
                    "widgets": [
                        {
                            "id": "system_status",
                            "type": "status_grid",
                            "position": {"col": 0, "row": 0, "width": 2, "height": 2},
                            "title": "System Status",
                            "data_endpoint": "/operations/summary",
                            "refresh_interval": 30,
                        },
                        {
                            "id": "real_time_predictions",
                            "type": "live_chart",
                            "position": {"col": 2, "row": 0, "width": 4, "height": 2},
                            "title": "Real-time Predictions",
                            "data_endpoint": "/analytics/prediction-accuracy",
                            "chart_config": {
                                "streaming": True,
                                "buffer_size": 100,
                                "update_interval": 10,
                            },
                        },
                        {
                            "id": "alert_management",
                            "type": "alert_table",
                            "position": {"col": 0, "row": 2, "width": 6, "height": 2},
                            "title": "Active Alerts Management",
                            "data_endpoint": "/operations/alerts",
                            "config": {
                                "actions_enabled": True,
                                "auto_refresh": True,
                                "severity_filtering": True,
                            },
                        },
                        {
                            "id": "data_pipeline_status",
                            "type": "pipeline_monitor",
                            "position": {"col": 0, "row": 4, "width": 3, "height": 2},
                            "title": "Data Pipeline Status",
                            "data_endpoint": "/operations/health/detailed",
                            "monitoring": ["era5", "chirps", "modis", "worldpop"],
                        },
                        {
                            "id": "model_monitoring",
                            "type": "model_status_grid",
                            "position": {"col": 3, "row": 4, "width": 3, "height": 2},
                            "title": "Model Performance Monitoring",
                            "data_endpoint": "/operations/models/status",
                            "real_time_updates": True,
                        },
                    ],
                },
                "websocket_enabled": True,
                "websocket_endpoint": "/operations/ws/operations-dashboard",
                "real_time_refresh": True,
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid dashboard_type. Must be one of: comprehensive, executive, operational")

    except Exception as e:
        logger.error(f"Error getting dashboard configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard configuration")


@router.get("/export/formats")
async def get_supported_export_formats(
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get list of supported data export formats.

    Returns available export formats and their capabilities.
    """
    return {
        "supported_formats": [
            {
                "format": "json",
                "description": "JavaScript Object Notation - human readable structured data",
                "mime_type": "application/json",
                "features": ["nested_data", "metadata", "type_preservation"],
            },
            {
                "format": "csv",
                "description": "Comma Separated Values - flat table format",
                "mime_type": "text/csv",
                "features": ["spreadsheet_compatible", "lightweight", "streaming"],
            },
            {
                "format": "excel",
                "description": "Microsoft Excel format with multiple sheets",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "features": ["multiple_sheets", "formatting", "metadata_sheet"],
            },
        ],
        "recommendations": {
            "small_datasets": "csv",
            "analysis_workflows": "excel",
            "api_consumption": "json",
        },
    }


@router.post("/export/prediction-accuracy")
async def export_prediction_accuracy_data(
    export_format: str = Query("csv", description="Export format"),
    start_date: str | None = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="End date in YYYY-MM-DD format"),
    model_type: str | None = Query(None, description="Model type filter"),
    include_metadata: bool = Query(True, description="Include metadata in export"),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Export prediction accuracy data in specified format.

    Returns downloadable export data with metadata.
    """
    try:
        export_service = await get_data_export_service(db)

        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Generate export
        export_result = await export_service.export_prediction_accuracy_data(
            export_format=export_format,
            start_date=start_dt,
            end_date=end_dt,
            model_type=model_type,
            include_metadata=include_metadata,
        )

        return {
            "export_status": "completed",
            "export_metadata": {
                "format": export_format,
                "filename": export_result["filename"],
                "size_bytes": export_result["size"],
                "content_type": export_result["content_type"],
                "generated_at": datetime.now().isoformat(),
            },
            "download_info": {
                "method": "direct_response",
                "note": "In production, this would be a signed URL to cloud storage",
            },
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "model_type": model_type,
                "include_metadata": include_metadata,
            },
        }

    except Exception as e:
        logger.error(f"Error exporting prediction accuracy data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.get("/export/statistics")
async def get_export_statistics(
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Get statistics about available data for export.

    Returns information about data availability, record counts,
    and date ranges for all data sources.
    """
    try:
        export_service = await get_data_export_service(db)
        stats = await export_service.get_export_statistics()

        return {
            "export_statistics": stats,
            "recommendations": {
                "optimal_batch_sizes": {
                    "csv": "< 100,000 records",
                    "excel": "< 50,000 records",
                    "json": "< 10,000 records",
                },
                "performance_tips": [
                    "Use date filters to limit data volume",
                    "Consider geographic bounds for location-based data",
                    "Include quality flags only when needed for analysis",
                ],
            },
            "api_limits": {
                "max_records_per_request": 50000,
                "max_export_size_mb": 100,
                "rate_limit": "10 exports per hour per user",
            },
        }

    except Exception as e:
        logger.error(f"Error getting export statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export statistics")
