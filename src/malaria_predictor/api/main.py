"""
FastAPI Main Application for Malaria Prediction Service.

This module provides the main FastAPI application with comprehensive endpoints
for malaria risk prediction, health monitoring, and model management.
"""

import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .dependencies import get_model_manager, get_prediction_service
from .middleware import (
    AuditLoggingMiddleware,
    InputValidationMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from .routers import (
    alerts,
    analytics,
    auth,
    health,
    healthcare,
    notifications,
    operations,
    prediction,
    reports,
)

logger = logging.getLogger(__name__)

# Global state for model management
model_manager = None
prediction_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for startup and shutdown."""
    global model_manager, prediction_service

    # Startup
    logger.info("🚀 Starting Enhanced Malaria Prediction API...")

    try:
        # Initialize model manager and prediction service
        model_manager = await get_model_manager()
        prediction_service = await get_prediction_service()

        # Initialize enhanced WebSocket alert system
        from .alerts.websocket_manager import websocket_manager

        logger.info("🔌 Initializing enhanced WebSocket alert system...")
        await websocket_manager.initialize()
        logger.info("✅ Enhanced WebSocket alert system initialized")

        # Store in app state
        app.state.model_manager = model_manager
        app.state.prediction_service = prediction_service
        app.state.websocket_manager = websocket_manager

        logger.info("✅ Enhanced Malaria Prediction API started successfully")
        logger.info("🎯 Real-time alert system ready with features:")
        logger.info("   • Low-latency broadcasting (<100ms)")
        logger.info("   • Rate limiting and abuse protection")
        logger.info("   • Offline message queuing")
        logger.info("   • Health monitoring and diagnostics")
        logger.info("   • Multi-client subscription management")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start Enhanced API: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down Enhanced Malaria Prediction API...")

        # Cleanup WebSocket manager
        try:
            from .alerts.websocket_manager import websocket_manager
            await websocket_manager.stop_background_tasks()
            logger.info("✅ WebSocket alert system shutdown complete")
        except Exception as e:
            logger.warning(f"⚠️ Error during WebSocket cleanup: {e}")

        if model_manager:
            await model_manager.cleanup()

        logger.info("✅ Enhanced Malaria Prediction API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Malaria Prediction API",
    description="""
    A comprehensive API for real-time malaria risk prediction using environmental data.

    ## Features

    * **Real-time Predictions**: Get malaria risk predictions for specific locations and dates
    * **Multiple Models**: LSTM, Transformer, and Ensemble model support
    * **Uncertainty Quantification**: Confidence estimates for all predictions
    * **Batch Processing**: Process multiple locations simultaneously
    * **Health Monitoring**: Comprehensive health checks and metrics
    * **Rate Limiting**: Built-in protection against abuse

    ## Data Sources

    The API integrates data from multiple environmental sources:
    - **ERA5**: Climate data (temperature, humidity, precipitation)
    - **CHIRPS**: High-resolution precipitation data
    - **MODIS**: Vegetation indices (NDVI, EVI)
    - **WorldPop**: Population density and demographics
    - **MAP**: Historical malaria risk maps

    ## Model Architecture

    - **LSTM**: Temporal sequence modeling for time-series patterns
    - **Transformer**: Spatial-temporal attention for complex dependencies
    - **Ensemble**: Hybrid approach combining both architectures
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Middleware configuration - Order matters!
# Add security middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://malaria-predictor.com",
    ],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add enhanced security middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    SecurityHeadersMiddleware, environment="development"
)  # Change to "production" in prod
app.add_middleware(
    InputValidationMiddleware, max_content_length=10 * 1024 * 1024
)  # 10MB
app.add_middleware(AuditLoggingMiddleware, log_sensitive_data=False)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 calls per minute

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
app.include_router(healthcare.router, prefix="/healthcare", tags=["Healthcare Professional Tools"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(operations.router, tags=["Operations"])
app.include_router(notifications.router, prefix="/notifications", tags=["Push Notifications"])
app.include_router(reports.router, prefix="/api/v1", tags=["Custom Reports"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time(),
                "path": str(request.url.path),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time(),
                "path": str(request.url.path),
            }
        },
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Malaria Prediction API",
        "version": "1.0.0",
        "description": "Real-time malaria risk prediction using environmental data",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "prediction": "/predict",
            "analytics": "/analytics",
            "operations": "/operations/dashboard",
            "metrics": "/health/metrics",
        },
        "models": {
            "lstm": "Time-series LSTM model for temporal patterns",
            "transformer": "Transformer model for spatial-temporal attention",
            "ensemble": "Hybrid ensemble combining LSTM and Transformer",
        },
    }


@app.get("/info", tags=["Root"])
async def api_info():
    """Detailed API information and capabilities."""
    return {
        "api": {
            "name": "Malaria Prediction API",
            "version": "1.0.0",
            "documentation": "/docs",
        },
        "data_sources": {
            "era5": "Climate data from Copernicus Climate Data Store",
            "chirps": "High-resolution precipitation data",
            "modis": "Vegetation indices from NASA Earth Data",
            "worldpop": "Population density and demographics",
            "map": "Historical malaria risk maps",
        },
        "models": {
            "lstm": {
                "type": "LSTM Neural Network",
                "description": "Temporal sequence modeling for time-series patterns",
                "features": ["Climate", "Vegetation", "Population", "Historical Risk"],
                "prediction_horizon": "30 days",
                "uncertainty": True,
            },
            "transformer": {
                "type": "Transformer with Spatial-Temporal Attention",
                "description": "Complex pattern recognition with attention mechanisms",
                "features": ["Climate", "Vegetation", "Population", "Historical Risk"],
                "prediction_horizon": "30 days",
                "uncertainty": True,
            },
            "ensemble": {
                "type": "Hybrid Ensemble Model",
                "description": "Combines LSTM and Transformer predictions",
                "features": ["Climate", "Vegetation", "Population", "Historical Risk"],
                "prediction_horizon": "30 days",
                "uncertainty": True,
                "fusion_methods": ["Attention", "MLP", "Weighted"],
            },
        },
        "endpoints": {
            "prediction": {
                "single": "POST /predict/single - Single location prediction",
                "batch": "POST /predict/batch - Multiple location predictions",
                "time_series": "POST /predict/time-series - Historical predictions",
            },
            "analytics": {
                "accuracy": "GET /analytics/prediction-accuracy - Model performance metrics",
                "trends": "GET /analytics/environmental-trends - Environmental trend analysis",
                "patterns": "GET /analytics/outbreak-patterns - Outbreak pattern recognition",
                "exploration": "GET /analytics/data-exploration - Interactive data exploration",
                "reports": "POST /analytics/custom-report - Custom report generation",
                "dashboard": "GET /analytics/dashboard-config - Dashboard configurations",
            },
            "health": {
                "status": "GET /health - API health status",
                "models": "GET /health/models - Model health and metrics",
                "metrics": "GET /health/metrics - Detailed system metrics",
            },
            "operations": {
                "dashboard": "GET /operations/dashboard - Production operations dashboard",
                "summary": "GET /operations/summary - System health summary",
                "alerts": "GET /operations/alerts - Active alerts",
                "metrics": "GET /operations/metrics/prometheus - Prometheus metrics",
            },
        },
        "features": {
            "real_time": "Real-time predictions with sub-second response times",
            "batch_processing": "Process multiple locations simultaneously",
            "uncertainty": "Confidence estimates for all predictions",
            "caching": "Intelligent caching for improved performance",
            "rate_limiting": "Built-in protection against abuse",
            "monitoring": "Comprehensive health checks and metrics",
            "operations_dashboard": "Production-grade operations dashboard with real-time monitoring",
            "alerting": "Automated alerting with escalation and runbook integration",
            "analytics_dashboard": "Comprehensive analytics dashboard with advanced data visualization",
            "trend_analysis": "Environmental and epidemiological trend analysis",
            "pattern_recognition": "Outbreak pattern recognition and seasonal analysis",
            "custom_reporting": "Flexible custom report generation with multiple export formats",
        },
    }


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
