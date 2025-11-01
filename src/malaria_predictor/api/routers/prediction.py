"""
Prediction Router for Malaria Risk Prediction API.

This module provides endpoints for malaria risk prediction including
single location predictions, batch processing, and time series analysis.
"""

import asyncio
import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..auth import require_scopes
from ..dependencies import PredictionService, get_prediction_service
from ...models import RiskLevel
from ..models import (
    BatchPredictionRequest,
    BatchPredictionResult,
    PredictionResult,
    SinglePredictionRequest,
    SpatialPredictionRequest,
    TimeSeriesPoint,
    TimeSeriesPredictionRequest,
    TimeSeriesPredictionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _calculate_risk_level(risk_score: float) -> RiskLevel:
    """Convert risk score to categorical risk level."""
    if risk_score < 0.25:
        return RiskLevel.LOW
    elif risk_score < 0.5:
        return RiskLevel.MEDIUM
    elif risk_score < 0.75:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH


@router.post("/single", response_model=PredictionResult)
async def predict_single_location(
    request: SinglePredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: Annotated[
        object, Depends(require_scopes("read:predictions", "write:predictions"))
    ] = None,
) -> PredictionResult:
    """
    Make malaria risk prediction for a single location.

    This endpoint provides real-time malaria risk prediction for a specific
    geographic location and target date using the selected model.

    Args:
        request: Single prediction request with location, date, and model parameters

    Returns:
        Prediction result with risk score, uncertainty, and metadata

    Raises:
        HTTPException: If prediction fails or invalid parameters provided
    """
    try:
        start_time = time.time()

        logger.info(
            f"Single prediction request: {request.location.latitude}, "
            f"{request.location.longitude} on {request.target_date} "
            f"using {request.model_type.value}"
        )

        # Make prediction
        prediction = await prediction_service.predict_single(
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            target_date=request.target_date,
            model_type=request.model_type,
            prediction_horizon=request.prediction_horizon.value,
        )

        # Calculate confidence interval if uncertainty is available
        confidence_interval = None
        if prediction["uncertainty"] is not None:
            risk_score = prediction["risk_score"]
            uncertainty = prediction["uncertainty"]
            confidence_interval = [
                max(0.0, risk_score - 1.96 * uncertainty),
                min(1.0, risk_score + 1.96 * uncertainty),
            ]

        # Create result
        result = PredictionResult(
            location=request.location,
            target_date=request.target_date,
            risk_score=prediction["risk_score"],
            risk_level=_calculate_risk_level(prediction["risk_score"]),
            uncertainty=prediction["uncertainty"],
            confidence_interval=confidence_interval,
            model_used=request.model_type,
            prediction_horizon=request.prediction_horizon.value,
            factors=None,  # Optional risk factors
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Single prediction completed in {processing_time:.2f}ms")

        return result

    except Exception as e:
        logger.error(f"Single prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        ) from e


@router.post("/batch", response_model=BatchPredictionResult)
async def predict_batch_locations(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: Annotated[
        object, Depends(require_scopes("read:predictions", "write:predictions"))
    ] = None,
) -> BatchPredictionResult:
    """
    Make malaria risk predictions for multiple locations.

    This endpoint processes multiple locations simultaneously for efficient
    batch prediction. Useful for analyzing risk across regions or for
    bulk analysis workflows.

    Args:
        request: Batch prediction request with multiple locations
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Batch prediction results with statistics and individual predictions

    Raises:
        HTTPException: If batch processing fails
    """
    try:
        start_time = time.time()
        total_locations = len(request.locations)

        logger.info(
            f"Batch prediction request: {total_locations} locations "
            f"on {request.target_date} using {request.model_type.value}"
        )

        # Process predictions concurrently
        tasks = []
        for location in request.locations:
            task = prediction_service.predict_single(
                latitude=location.latitude,
                longitude=location.longitude,
                target_date=request.target_date,
                model_type=request.model_type,
                prediction_horizon=request.prediction_horizon.value,
            )
            tasks.append((location, task))

        # Execute all predictions concurrently
        predictions = []
        successful_predictions = 0
        failed_predictions = 0

        # Use semaphore to limit concurrent predictions
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent predictions

        async def predict_with_semaphore(
            location: LocationPoint, prediction_task: Any
        ) -> tuple[PredictionResult | None, bool]:
            async with semaphore:
                try:
                    prediction = await prediction_task

                    # Calculate confidence interval
                    confidence_interval = None
                    if prediction["uncertainty"] is not None:
                        risk_score = prediction["risk_score"]
                        uncertainty = prediction["uncertainty"]
                        confidence_interval = [
                            max(0.0, risk_score - 1.96 * uncertainty),
                            min(1.0, risk_score + 1.96 * uncertainty),
                        ]

                    result = PredictionResult(
                        location=location,
                        target_date=request.target_date,
                        risk_score=prediction["risk_score"],
                        risk_level=_calculate_risk_level(prediction["risk_score"]),
                        uncertainty=prediction["uncertainty"],
                        confidence_interval=confidence_interval,
                        model_used=request.model_type,
                        prediction_horizon=request.prediction_horizon.value,
                        factors=None,  # Optional risk factors
                    )
                    return result, True

                except Exception as e:
                    logger.error(f"Prediction failed for location {location}: {e}")
                    return None, False

        # Execute all predictions
        results = await asyncio.gather(
            *[predict_with_semaphore(location, task) for location, task in tasks]
        )

        # Process results
        for result, success in results:
            if success and result:
                predictions.append(result)
                successful_predictions += 1
            else:
                failed_predictions += 1

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(
            f"Batch prediction completed: {successful_predictions} successful, "
            f"{failed_predictions} failed in {processing_time:.2f}ms"
        )

        return BatchPredictionResult(
            predictions=predictions,
            total_locations=total_locations,
            successful_predictions=successful_predictions,
            failed_predictions=failed_predictions,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}",
        ) from e


@router.post("/spatial")
async def predict_spatial_grid(
    request: SpatialPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: Annotated[
        object, Depends(require_scopes("read:predictions", "write:predictions"))
    ] = None,
) -> dict[str, Any]:
    """
    Make predictions across a spatial grid.

    This endpoint generates predictions for a regular grid of points within
    the specified geographic bounds, useful for creating risk maps and
    spatial visualizations.

    Args:
        request: Spatial prediction request with geographic bounds and resolution

    Returns:
        Grid predictions with spatial coordinates and risk values

    Raises:
        HTTPException: If spatial prediction fails or grid is too large
    """
    try:
        start_time = time.time()

        # Calculate grid dimensions
        lat_range = request.bounds["north"] - request.bounds["south"]
        lon_range = request.bounds["east"] - request.bounds["west"]

        lat_points = int(lat_range / request.resolution) + 1
        lon_points = int(lon_range / request.resolution) + 1
        total_points = lat_points * lon_points

        # Limit grid size to prevent resource exhaustion
        max_points = 10000  # Configurable limit
        if total_points > max_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grid too large: {total_points} points (max: {max_points}). "
                f"Increase resolution or reduce bounds.",
            )

        logger.info(
            f"Spatial prediction: {lat_points}x{lon_points} grid "
            f"({total_points} points) using {request.model_type.value}"
        )

        # Generate grid points
        grid_predictions = []
        lats = [
            request.bounds["south"] + i * request.resolution for i in range(lat_points)
        ]
        lons = [request.bounds["west"] + j * request.resolution for j in range(lon_points)]

        # Create prediction tasks
        tasks = []
        for lat in lats:
            for lon in lons:
                task = prediction_service.predict_single(
                    latitude=lat,
                    longitude=lon,
                    target_date=request.target_date,
                    model_type=request.model_type,
                    prediction_horizon=request.prediction_horizon.value,
                )
                tasks.append((lat, lon, task))

        # Process in batches to avoid overwhelming the system
        batch_size = 100
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]

            # Execute batch
            batch_results = await asyncio.gather(
                *[task for _, _, task in batch], return_exceptions=True
            )

            # Process batch results
            for j, (lat, lon, _) in enumerate(batch):
                result = batch_results[j]

                if isinstance(result, Exception):
                    logger.warning(f"Prediction failed for {lat}, {lon}: {result}")
                    continue

                grid_predictions.append(
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "risk_score": result["risk_score"],
                        "risk_level": _calculate_risk_level(result["risk_score"]).value,
                        "uncertainty": result["uncertainty"],
                    }
                )

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            f"Spatial prediction completed: {len(grid_predictions)} points "
            f"in {processing_time:.2f}ms"
        )

        return {
            "grid_info": {
                "bounds": request.bounds.model_dump(),
                "resolution": request.resolution,
                "dimensions": {"lat_points": lat_points, "lon_points": lon_points},
                "total_points": total_points,
                "successful_points": len(grid_predictions),
            },
            "predictions": grid_predictions,
            "metadata": {
                "target_date": request.target_date.isoformat(),
                "model_type": request.model_type.value,
                "prediction_horizon": request.prediction_horizon.value,
                "processing_time_ms": processing_time,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spatial prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial prediction failed: {str(e)}",
        ) from e


@router.post("/time-series", response_model=TimeSeriesPredictionResult)
async def predict_time_series(
    request: TimeSeriesPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: Annotated[
        object, Depends(require_scopes("read:predictions", "write:predictions"))
    ] = None,
) -> TimeSeriesPredictionResult:
    """
    Generate time series predictions for a location.

    This endpoint creates predictions across a range of dates for a single
    location, useful for temporal analysis and trend identification.

    Args:
        request: Time series prediction request with date range

    Returns:
        Time series with predictions for each date in the range

    Raises:
        HTTPException: If time series prediction fails or date range too large
    """
    try:
        start_time = time.time()

        # Calculate date range
        date_range = (request.end_date - request.start_date).days + 1

        # Limit time series length
        max_days = 365  # Configurable limit
        if date_range > max_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range too large: {date_range} days (max: {max_days})",
            )

        logger.info(
            f"Time series prediction: {request.location.latitude}, "
            f"{request.location.longitude} from {request.start_date} "
            f"to {request.end_date} ({date_range} days)"
        )

        # Generate predictions for each date
        time_series = []
        current_date = request.start_date

        while current_date <= request.end_date:
            try:
                prediction = await prediction_service.predict_single(
                    latitude=request.location.latitude,
                    longitude=request.location.longitude,
                    target_date=current_date,
                    model_type=request.model_type,
                    prediction_horizon=1,  # Single day prediction
                )

                time_series.append(
                    TimeSeriesPoint(
                        date=current_date,
                        risk_score=prediction["risk_score"],
                        risk_level=_calculate_risk_level(prediction["risk_score"]),
                        uncertainty=prediction["uncertainty"],
                    )
                )

            except Exception as e:
                logger.warning(f"Prediction failed for {current_date}: {e}")
                # Continue with next date

            current_date = current_date.replace(day=current_date.day + 1)

        # Calculate summary statistics
        risk_scores = [point.risk_score for point in time_series]
        uncertainties = [
            point.uncertainty for point in time_series if point.uncertainty is not None
        ]

        summary_statistics = {
            "total_points": len(time_series),
            "mean_risk": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            "min_risk": min(risk_scores) if risk_scores else 0,
            "max_risk": max(risk_scores) if risk_scores else 0,
            "mean_uncertainty": (
                sum(uncertainties) / len(uncertainties) if uncertainties else None
            ),
            "high_risk_days": sum(
                1
                for point in time_series
                if point.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
            ),
            "risk_trend": _calculate_trend(risk_scores) if len(risk_scores) > 1 else 0,
        }

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            f"Time series prediction completed: {len(time_series)} points "
            f"in {processing_time:.2f}ms"
        )

        return TimeSeriesPredictionResult(
            location=request.location,
            model_used=request.model_type,
            time_series=time_series,
            summary_statistics=summary_statistics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Time series prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Time series prediction failed: {str(e)}",
        ) from e


def _calculate_trend(values: list[float]) -> float:
    """Calculate linear trend slope for time series."""
    if len(values) < 2:
        return 0.0

    n = len(values)
    x = list(range(n))

    # Calculate linear regression slope
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    return numerator / denominator if denominator != 0 else 0.0
