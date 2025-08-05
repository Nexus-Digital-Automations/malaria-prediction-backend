"""
Configuration settings for the malaria prediction system.

This module provides comprehensive environment-specific configuration management
with validation, secrets support, and security features for the malaria prediction
backend application.
"""

import os
import secrets
from pathlib import Path
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    """Security-related configuration settings."""

    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT tokens and encryption",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="JWT token expiration time in hours",
    )
    password_min_length: int = Field(
        default=8, ge=6, le=128, description="Minimum password length"
    )
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS requests"
    )
    rate_limit_per_minute: int = Field(
        default=100, ge=1, le=10000, description="API rate limit per minute per client"
    )

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins format."""
        if not isinstance(v, list):
            raise ValueError("CORS origins must be a list")
        return v


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    url: PostgresDsn = Field(
        default="postgresql+asyncpg://user:password@localhost/malaria_prediction",
        description="PostgreSQL database URL with TimescaleDB",
    )
    echo: bool = Field(default=False, description="Echo SQL statements to logs")
    pool_size: int = Field(
        default=20, ge=1, le=100, description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=0, ge=0, le=50, description="Maximum pool overflow connections"
    )
    pool_timeout: int = Field(
        default=30, ge=1, le=300, description="Pool connection timeout in seconds"
    )
    pool_recycle: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Pool connection recycle time in seconds",
    )

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str | PostgresDsn) -> str:
        """Validate database URL format and requirements."""
        if isinstance(v, str):
            parsed = urlparse(v)
            if not parsed.hostname:
                raise ValueError("Database URL must include hostname")
            if not parsed.path or parsed.path == "/":
                raise ValueError("Database URL must include database name")
        return str(v)


class RedisSettings(BaseModel):
    """Redis configuration settings."""

    url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and job queues",
    )
    password: str | None = Field(
        default=None, description="Redis password (if required)"
    )
    max_connections: int = Field(
        default=50, ge=1, le=1000, description="Maximum Redis connection pool size"
    )
    socket_timeout: int = Field(
        default=5, ge=1, le=60, description="Redis socket timeout in seconds"
    )
    socket_connect_timeout: int = Field(
        default=5, ge=1, le=60, description="Redis socket connection timeout in seconds"
    )

    # Celery-specific Redis settings
    celery_broker_db: int = Field(
        default=1, ge=0, le=15, description="Redis database number for Celery broker"
    )
    celery_result_db: int = Field(
        default=2, ge=0, le=15, description="Redis database number for Celery results"
    )


class ExternalAPISettings(BaseModel):
    """External API configuration settings."""

    # ERA5 Climate Data API
    era5_api_key: str | None = Field(
        default=None, description="Copernicus Climate Data Store API key"
    )
    era5_api_url: HttpUrl = Field(
        default="https://cds.climate.copernicus.eu/api/v2",
        description="ERA5 API base URL",
    )

    # CHIRPS Precipitation Data API
    chirps_api_endpoint: HttpUrl = Field(
        default="https://data.chc.ucsb.edu/api/", description="CHIRPS data API endpoint"
    )

    # MODIS/NASA Earth Data API
    modis_api_key: str | None = Field(
        default=None, description="NASA EarthData API key"
    )
    modis_api_url: HttpUrl = Field(
        default="https://modis.gsfc.nasa.gov/data/", description="MODIS API base URL"
    )

    # WorldPop Population Data API
    worldpop_api_endpoint: HttpUrl = Field(
        default="https://hub.worldpop.org/", description="WorldPop API endpoint"
    )

    # Malaria Atlas Project API
    map_api_endpoint: HttpUrl = Field(
        default="https://malariaatlas.org/",
        description="Malaria Atlas Project API endpoint",
    )

    # API rate limiting
    max_requests_per_minute: int = Field(
        default=100, ge=1, le=10000, description="Maximum API requests per minute"
    )
    request_timeout: int = Field(
        default=30, ge=5, le=300, description="API request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed API requests",
    )
    retry_delay: int = Field(
        default=5, ge=1, le=60, description="Delay between retry attempts in seconds"
    )


class MLModelSettings(BaseModel):
    """Machine Learning model configuration settings."""

    storage_path: Path = Field(
        default=Path("./models"), description="Path to store trained models"
    )
    enable_cache: bool = Field(default=True, description="Enable model caching")
    cache_ttl: int = Field(
        default=3600, ge=60, le=86400, description="Model cache TTL in seconds"
    )
    max_memory_usage: int = Field(
        default=4096,
        ge=512,
        le=32768,
        description="Maximum memory usage for models in MB",
    )
    device: str = Field(
        default="auto", description="Device for model inference (auto, cpu, cuda)"
    )
    batch_size: int = Field(
        default=32, ge=1, le=1024, description="Default batch size for model inference"
    )

    @field_validator("storage_path")
    @classmethod
    def validate_storage_path(cls, v: str | Path) -> Path:
        """Validate and normalize storage path."""
        path = Path(v) if isinstance(v, str) else v
        return path.absolute()

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device specification."""
        valid_devices = ["auto", "cpu", "cuda", "mps"]
        if v not in valid_devices:
            raise ValueError(f"Device must be one of: {valid_devices}")
        return v


class DataSettings(BaseModel):
    """Data storage and processing configuration settings."""

    directory: Path = Field(
        default=Path("./data"), description="Path to store environmental data"
    )
    enable_cache: bool = Field(default=True, description="Enable data caching")
    cache_ttl: int = Field(
        default=1800, ge=60, le=86400, description="Data cache TTL in seconds"
    )
    max_file_size: int = Field(
        default=1073741824,  # 1GB
        ge=1048576,  # 1MB
        le=10737418240,  # 10GB
        description="Maximum file size for data files in bytes",
    )
    compression_enabled: bool = Field(
        default=True, description="Enable data compression"
    )
    backup_enabled: bool = Field(
        default=True, description="Enable automatic data backup"
    )
    retention_days: int = Field(
        default=90, ge=1, le=365, description="Data retention period in days"
    )

    @field_validator("directory")
    @classmethod
    def validate_directory(cls, v: str | Path) -> Path:
        """Validate and normalize data directory path."""
        path = Path(v) if isinstance(v, str) else v
        return path.absolute()


class MonitoringSettings(BaseModel):
    """Monitoring and observability configuration settings."""

    enable_metrics: bool = Field(
        default=True, description="Enable Prometheus metrics collection"
    )
    enable_tracing: bool = Field(
        default=False, description="Enable distributed tracing"
    )
    enable_profiling: bool = Field(
        default=False, description="Enable performance profiling"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json", description="Log format (json, structured, text)"
    )
    sentry_dsn: str | None = Field(
        default=None, description="Sentry DSN for error tracking"
    )
    metrics_port: int = Field(
        default=9090, ge=1024, le=65535, description="Port for metrics endpoint"
    )
    health_check_interval: int = Field(
        default=30, ge=5, le=300, description="Health check interval in seconds"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "structured", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()


class Settings(BaseSettings):
    """
    Main application configuration settings.

    Supports multiple environments (development, staging, production) with
    environment-specific overrides and secrets management integration.
    """

    # Application metadata
    app_name: str = Field(
        default="Malaria Prediction API", description="Application name"
    )
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    testing: bool = Field(default=False, description="Whether in testing mode")

    # API configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(
        default=8000, ge=1024, le=65535, description="API port number"
    )
    api_prefix: str = Field(default="/api/v1", description="API URL prefix")
    workers: int = Field(
        default=1, ge=1, le=32, description="Number of worker processes"
    )

    # Configuration sections
    security: SecuritySettings = Field(
        default_factory=SecuritySettings, description="Security configuration"
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings, description="Database configuration"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings, description="Redis configuration"
    )
    external_apis: ExternalAPISettings = Field(
        default_factory=ExternalAPISettings, description="External API configuration"
    )
    ml_models: MLModelSettings = Field(
        default_factory=MLModelSettings, description="ML model configuration"
    )
    data: DataSettings = Field(
        default_factory=DataSettings, description="Data storage configuration"
    )
    monitoring: MonitoringSettings = Field(
        default_factory=MonitoringSettings, description="Monitoring configuration"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_environments = ["development", "staging", "production", "testing"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v.lower()

    @model_validator(mode="after")
    def validate_environment_consistency(self) -> "Settings":
        """Validate configuration consistency based on environment."""
        # Production environment validations
        if self.environment == "production":
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
            if self.security.secret_key == "dev_secret_key_change_in_production":
                raise ValueError("Default secret key cannot be used in production")
            if "*" in self.security.cors_origins:
                raise ValueError("Wildcard CORS origins not allowed in production")

        # Development environment defaults
        elif self.environment == "development":
            if not self.debug:
                self.debug = True

        return self

    def get_database_url(self, sync: bool = False) -> str:
        """
        Get database URL with optional sync driver.

        Args:
            sync: If True, returns URL with psycopg2 driver for sync connections

        Returns:
            Database URL string
        """
        url = str(self.database.url)
        if sync:
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        return url

    def get_redis_url(self, db: int | None = None) -> str:
        """
        Get Redis URL with optional database number override.

        Args:
            db: Database number to use (overrides URL database)

        Returns:
            Redis URL string
        """
        url = str(self.redis.url)
        if db is not None:
            # Replace database number in URL
            parsed = urlparse(url)
            new_path = f"/{db}"
            url = url.replace(parsed.path, new_path)
        return url

    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL."""
        return self.get_redis_url(db=self.redis.celery_broker_db)

    def get_celery_result_backend_url(self) -> str:
        """Get Celery result backend URL."""
        return self.get_redis_url(db=self.redis.celery_result_db)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.testing or self.environment == "testing"


def load_settings() -> Settings:
    """
    Load configuration settings with environment-specific overrides.

    This function loads settings in the following order of precedence:
    1. Docker/Kubernetes secrets (for production)
    2. Environment variables
    3. Environment-specific .env file (e.g., .env.production)
    4. Generic .env file
    5. Default values

    Returns:
        Configured Settings instance
    """
    # Import here to avoid circular imports
    from .secrets import get_secrets_manager

    # Determine environment from ENV variable or default
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Initialize secrets manager for production environments
    if env == "production":
        secrets_manager = get_secrets_manager()

        # Load critical secrets and inject into environment
        try:
            # Secret key
            secret_key = secrets_manager.get_secret(
                "api_secret_key", env_var_name="SECRET_KEY", required=True
            )
            if secret_key and "SECRET_KEY" not in os.environ:
                os.environ["SECURITY__SECRET_KEY"] = secret_key

            # Database password
            db_password = secrets_manager.get_secret(
                "db_password", env_var_name="DATABASE_PASSWORD", required=True
            )
            if db_password and "DATABASE_PASSWORD" not in os.environ:
                # Update DATABASE_URL with the actual password
                base_url = os.getenv("DATABASE__URL", "")
                if base_url and "REPLACE_WITH_DB_PASSWORD" in base_url:
                    os.environ["DATABASE__URL"] = base_url.replace(
                        "REPLACE_WITH_DB_PASSWORD", db_password
                    )

            # Redis password (optional)
            redis_password = secrets_manager.get_secret(
                "redis_password", env_var_name="REDIS_PASSWORD", required=False
            )
            if redis_password and "REDIS_PASSWORD" not in os.environ:
                os.environ["REDIS__PASSWORD"] = redis_password

            # External API keys
            era5_key = secrets_manager.get_secret(
                "era5_api_key", env_var_name="ERA5_API_KEY", required=False
            )
            if era5_key and "ERA5_API_KEY" not in os.environ:
                os.environ["EXTERNAL_APIS__ERA5_API_KEY"] = era5_key

            modis_key = secrets_manager.get_secret(
                "modis_api_key", env_var_name="MODIS_API_KEY", required=False
            )
            if modis_key and "MODIS_API_KEY" not in os.environ:
                os.environ["EXTERNAL_APIS__MODIS_API_KEY"] = modis_key

        except Exception as e:
            # Log the error but don't fail completely
            # Let the validation handle missing secrets
            print(f"Warning: Failed to load some secrets: {e}")

    # Define environment-specific config file
    env_files = []

    # Add environment-specific file if it exists
    env_file = f".env.{env}"
    if os.path.exists(env_file):
        env_files.append(env_file)

    # Add generic .env file if it exists
    if os.path.exists(".env"):
        env_files.append(".env")

    # Create settings with environment-specific configuration
    settings = Settings(_env_file=env_files, environment=env)

    return settings


def validate_configuration(settings: Settings) -> list[str]:
    """
    Validate configuration and return list of warnings or errors.

    Args:
        settings: Settings instance to validate

    Returns:
        List of validation messages
    """
    warnings = []

    # Check for missing API keys in production
    if settings.is_production():
        if not settings.external_apis.era5_api_key:
            warnings.append("ERA5 API key not configured for production")
        if not settings.external_apis.modis_api_key:
            warnings.append("MODIS API key not configured for production")

    # Check storage paths exist
    if not settings.ml_models.storage_path.exists():
        warnings.append(
            f"Model storage path does not exist: {settings.ml_models.storage_path}"
        )

    if not settings.data.directory.exists():
        warnings.append(f"Data directory does not exist: {settings.data.directory}")

    # Check database connectivity (basic URL validation)
    try:
        parsed_db = urlparse(str(settings.database.url))
        if not parsed_db.hostname:
            warnings.append("Database hostname not specified")
    except Exception as e:
        warnings.append(f"Invalid database URL: {e}")

    # Check Redis connectivity (basic URL validation)
    try:
        parsed_redis = urlparse(str(settings.redis.url))
        if not parsed_redis.hostname:
            warnings.append("Redis hostname not specified")
    except Exception as e:
        warnings.append(f"Invalid Redis URL: {e}")

    return warnings


# Global settings instance
settings = load_settings()
