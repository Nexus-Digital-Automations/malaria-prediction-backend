"""
Dependency Injection for FastAPI Application.

This module provides dependency injection functions for managing model instances,
prediction services, and other shared resources in the FastAPI application.
"""

import asyncio
import logging
from datetime import datetime

import torch
from fastapi import HTTPException, status

from ..ml import MalariaEnsembleModel, MalariaLSTM, MalariaTransformer
from ..services.unified_data_harmonizer import UnifiedDataHarmonizer
from .models import ModelType

logger = logging.getLogger(__name__)

# Import auth functions
try:
    from .auth import get_current_user

    # Create optional user dependency
    async def get_current_user_optional(*args, **kwargs):
        """Optional user authentication - returns None if not authenticated."""
        try:
            return await get_current_user(*args, **kwargs)
        except Exception:
            return None

except ImportError:
    # Fallback if auth module not available
    async def get_current_user(*args, **kwargs):
        """Placeholder authentication function."""
        return None

    async def get_current_user_optional(*args, **kwargs):
        """Placeholder optional authentication function."""
        return None


class ModelManager:
    """
    Manages ML model instances and their lifecycle.

    Handles loading, caching, and health monitoring of LSTM, Transformer,
    and Ensemble models for malaria prediction.
    """

    def __init__(self):
        self.models = {}
        self.model_health = {}
        self.last_health_check = None
        self._lock = asyncio.Lock()

    async def load_model(
        self, model_type: ModelType, model_path: str | None = None
    ) -> None:
        """Load a specific model type."""
        async with self._lock:
            if model_type in self.models:
                logger.info(f"Model {model_type} already loaded")
                return

            try:
                logger.info(f"Loading model: {model_type}")

                if model_type == ModelType.LSTM:
                    model = self._load_lstm_model(model_path)
                elif model_type == ModelType.TRANSFORMER:
                    model = self._load_transformer_model(model_path)
                elif model_type == ModelType.ENSEMBLE:
                    model = self._load_ensemble_model(model_path)
                else:
                    raise ValueError(f"Unknown model type: {model_type}")

                # Set to evaluation mode
                model.eval()

                self.models[model_type] = model
                self.model_health[model_type] = {
                    "status": "healthy",
                    "last_used": datetime.now(),
                    "load_time": datetime.now(),
                    "prediction_count": 0,
                    "error_count": 0,
                }

                logger.info(f"Successfully loaded model: {model_type}")

            except Exception as e:
                logger.error(f"Failed to load model {model_type}: {e}")
                self.model_health[model_type] = {
                    "status": "error",
                    "error": str(e),
                    "last_error": datetime.now(),
                }
                raise

    def _load_lstm_model(self, model_path: str | None) -> MalariaLSTM:
        """Load LSTM model from checkpoint or create new instance.

        Security: Uses weights_only=False to load config dict. Only load trusted checkpoints.
        """
        if model_path:
            # SECURITY: weights_only=False required for config dict loading
            # ONLY load checkpoints from trusted sources (MLflow, verified storage)
            checkpoint = torch.load(
                model_path, map_location="cpu", weights_only=False  # noqa: S614
            )
            model = MalariaLSTM(**checkpoint.get("config", {}))
            model.load_state_dict(checkpoint["model_state_dict"])
            return model
        else:
            # Create default model (for development/testing)
            return MalariaLSTM()

    def _load_transformer_model(self, model_path: str | None) -> MalariaTransformer:
        """Load Transformer model from checkpoint or create new instance.

        Security: Uses weights_only=False to load config dict. Only load trusted checkpoints.
        """
        if model_path:
            # SECURITY: weights_only=False required for config dict loading
            # ONLY load checkpoints from trusted sources (MLflow, verified storage)
            checkpoint = torch.load(
                model_path, map_location="cpu", weights_only=False  # noqa: S614
            )
            model = MalariaTransformer(**checkpoint.get("config", {}))
            model.load_state_dict(checkpoint["model_state_dict"])
            return model
        else:
            # Create default model (for development/testing)
            return MalariaTransformer()

    def _load_ensemble_model(self, model_path: str | None) -> MalariaEnsembleModel:
        """Load Ensemble model from checkpoint or create new instance.

        Security: Uses weights_only=False to load config dict. Only load trusted checkpoints.
        """
        if model_path:
            # SECURITY: weights_only=False required for config dict loading
            # ONLY load checkpoints from trusted sources (MLflow, verified storage)
            checkpoint = torch.load(
                model_path, map_location="cpu", weights_only=False  # noqa: S614
            )
            lstm_config = checkpoint.get("lstm_config", {})
            transformer_config = checkpoint.get("transformer_config", {})
            model = MalariaEnsembleModel(lstm_config, transformer_config)
            model.load_state_dict(checkpoint["model_state_dict"])
            return model
        else:
            # Create default model (for development/testing)
            lstm_config = {}
            transformer_config = {}
            return MalariaEnsembleModel(lstm_config, transformer_config)

    async def get_model(self, model_type: ModelType):
        """Get a model instance, loading if necessary."""
        if model_type not in self.models:
            await self.load_model(model_type)

        if model_type not in self.models:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model {model_type} is not available",
            )

        # Update usage statistics
        self.model_health[model_type]["last_used"] = datetime.now()
        self.model_health[model_type]["prediction_count"] += 1

        return self.models[model_type]

    async def health_check(self) -> dict:
        """Perform health check on all loaded models."""
        self.last_health_check = datetime.now()
        health_status = {}

        for model_type, model in self.models.items():
            try:
                # Simple forward pass to check model health
                dummy_input = self._create_dummy_input()
                with torch.no_grad():
                    _ = model(dummy_input)

                health_status[model_type.value] = {
                    **self.model_health[model_type],
                    "status": "healthy",
                }

            except Exception as e:
                logger.error(f"Health check failed for {model_type}: {e}")
                health_status[model_type.value] = {
                    **self.model_health[model_type],
                    "status": "unhealthy",
                    "error": str(e),
                }

        return health_status

    def _create_dummy_input(self) -> dict:
        """Create dummy input for model health checks."""
        batch_size = 1
        seq_len = 10
        return {
            "climate": torch.randn(batch_size, seq_len, 12),
            "vegetation": torch.randn(batch_size, seq_len, 4),
            "population": torch.randn(batch_size, seq_len, 6),
            "historical": torch.randn(batch_size, seq_len, 4),
        }

    async def cleanup(self):
        """Cleanup resources."""
        async with self._lock:
            self.models.clear()
            self.model_health.clear()
            logger.info("Model manager cleanup complete")


class PredictionService:
    """
    High-level prediction service that orchestrates data harmonization and model inference.

    Combines data harmonization, feature extraction, and model prediction
    into a unified service for malaria risk prediction.
    """

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.data_harmonizer = None
        self._initialize_harmonizer()

    def _initialize_harmonizer(self):
        """Initialize the data harmonization service."""
        try:
            import os

            if not os.getenv("TESTING", "false").lower() == "true":
                self.data_harmonizer = UnifiedDataHarmonizer()
                logger.info("Data harmonizer initialized successfully")
            else:
                logger.info(
                    "Skipping data harmonizer initialization in testing environment"
                )
                self.data_harmonizer = None
        except Exception as e:
            logger.error(f"Failed to initialize data harmonizer: {e}")
            # Continue without harmonizer for basic functionality
            self.data_harmonizer = None

    async def predict_single(
        self,
        latitude: float,
        longitude: float,
        target_date,
        model_type: ModelType,
        prediction_horizon: int = 30,
    ) -> dict:
        """Make prediction for a single location."""
        try:
            # Get model
            model = await self.model_manager.get_model(model_type)

            # Get harmonized data (if available)
            if self.data_harmonizer:
                region_bounds = (
                    longitude - 0.1,
                    latitude - 0.1,  # west, south
                    longitude + 0.1,
                    latitude + 0.1,  # east, north
                )

                harmonized_data = await self.data_harmonizer.get_harmonized_features(
                    region_bounds=region_bounds,
                    target_date=target_date,
                    lookback_days=90,
                )

                # Convert to model input format
                model_input = self._prepare_model_input(harmonized_data.data)
            else:
                # Use dummy data for development/testing
                model_input = self._create_dummy_input()

            # Make prediction
            with torch.no_grad():
                predictions = model(model_input)

            # Extract results
            risk_score = float(
                predictions["risk_mean"][0, 0]
            )  # First location, first day
            uncertainty = None

            if "risk_variance" in predictions:
                uncertainty = float(torch.sqrt(predictions["risk_variance"][0, 0]))

            return {
                "risk_score": risk_score,
                "uncertainty": uncertainty,
                "model_type": model_type.value,
                "prediction_horizon": prediction_horizon,
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Update error count
            if model_type in self.model_manager.model_health:
                self.model_manager.model_health[model_type]["error_count"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prediction failed: {str(e)}",
            ) from e

    def _prepare_model_input(self, harmonized_data: dict) -> dict:
        """Convert harmonized data to model input format."""
        # This is a simplified conversion - in practice, would need proper feature engineering
        batch_size = 1
        seq_len = 10  # Use last 10 days

        model_input = {}

        # Extract climate features
        if "era5" in harmonized_data and "chirps" in harmonized_data:
            climate_features = torch.randn(batch_size, seq_len, 12)  # Placeholder
            model_input["climate"] = climate_features

        # Extract vegetation features
        if "modis" in harmonized_data:
            vegetation_features = torch.randn(batch_size, seq_len, 4)  # Placeholder
            model_input["vegetation"] = vegetation_features

        # Extract population features
        if "worldpop" in harmonized_data:
            population_features = torch.randn(batch_size, seq_len, 6)  # Placeholder
            model_input["population"] = population_features

        # Extract historical features
        if "map" in harmonized_data:
            historical_features = torch.randn(batch_size, seq_len, 4)  # Placeholder
            model_input["historical"] = historical_features

        # Fill in missing modalities with dummy data
        for key in ["climate", "vegetation", "population", "historical"]:
            if key not in model_input:
                if key == "climate":
                    model_input[key] = torch.randn(batch_size, seq_len, 12)
                elif key == "vegetation":
                    model_input[key] = torch.randn(batch_size, seq_len, 4)
                elif key == "population":
                    model_input[key] = torch.randn(batch_size, seq_len, 6)
                elif key == "historical":
                    model_input[key] = torch.randn(batch_size, seq_len, 4)

        return model_input

    def _create_dummy_input(self) -> dict:
        """Create dummy input for testing."""
        batch_size = 1
        seq_len = 10
        return {
            "climate": torch.randn(batch_size, seq_len, 12),
            "vegetation": torch.randn(batch_size, seq_len, 4),
            "population": torch.randn(batch_size, seq_len, 6),
            "historical": torch.randn(batch_size, seq_len, 4),
        }


# Global instances
_model_manager: ModelManager | None = None
_prediction_service: PredictionService | None = None


async def get_model_manager() -> ModelManager:
    """Dependency injection for model manager."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
        # Load default models only in non-testing environments
        try:
            import os

            if not os.getenv("TESTING", "false").lower() == "true":
                await _model_manager.load_model(ModelType.ENSEMBLE)
                logger.info("Default ensemble model loaded")
            else:
                logger.info("Skipping model loading in testing environment")
        except Exception as e:
            logger.warning(f"Failed to load default model: {e}")
    return _model_manager


async def get_prediction_service() -> PredictionService:
    """Dependency injection for prediction service."""
    global _prediction_service
    if _prediction_service is None:
        model_manager = await get_model_manager()
        _prediction_service = PredictionService(model_manager)
    return _prediction_service


async def cleanup_dependencies():
    """Cleanup all dependencies."""
    global _model_manager, _prediction_service
    if _model_manager:
        await _model_manager.cleanup()
        _model_manager = None
    _prediction_service = None
