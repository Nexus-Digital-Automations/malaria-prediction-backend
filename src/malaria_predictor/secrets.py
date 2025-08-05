"""
Secrets management for the malaria prediction system.

This module provides secure handling of sensitive configuration data including
Docker secrets, Kubernetes secrets, and environment variables with fallback
mechanisms and validation.
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secure secrets management with multiple backend support.

    Supports Docker secrets, Kubernetes secrets, environment variables,
    and file-based secrets with proper fallback mechanisms.
    """

    def __init__(self, secrets_dir: str | Path = "/run/secrets"):
        """
        Initialize the secrets manager.

        Args:
            secrets_dir: Directory where Docker/Kubernetes secrets are mounted
        """
        self.secrets_dir = Path(secrets_dir)
        self._secrets_cache: dict[str, str] = {}

    def get_secret(
        self,
        secret_name: str,
        env_var_name: str | None = None,
        default: str | None = None,
        required: bool = True,
    ) -> str | None:
        """
        Get a secret value with fallback mechanism.

        Priority order:
        1. Docker/Kubernetes secret file
        2. Environment variable (if env_var_name provided)
        3. Default value (if provided)
        4. Raise error if required=True and not found

        Args:
            secret_name: Name of the secret (file name in secrets directory)
            env_var_name: Environment variable name as fallback
            default: Default value if secret not found
            required: Whether the secret is required

        Returns:
            Secret value or None if not found and not required

        Raises:
            ValueError: If required secret is not found
        """
        # Check cache first
        cache_key = f"{secret_name}:{env_var_name or ''}"
        if cache_key in self._secrets_cache:
            return self._secrets_cache[cache_key]

        secret_value = None

        # 1. Try Docker/Kubernetes secret file
        secret_file = self.secrets_dir / secret_name
        if secret_file.exists() and secret_file.is_file():
            try:
                secret_value = secret_file.read_text().strip()
                logger.debug(f"Loaded secret '{secret_name}' from file")
            except Exception as e:
                logger.warning(f"Failed to read secret file '{secret_file}': {e}")

        # 2. Try environment variable fallback
        if secret_value is None and env_var_name:
            secret_value = os.getenv(env_var_name)
            if secret_value:
                logger.debug(
                    f"Loaded secret '{secret_name}' from environment variable '{env_var_name}'"
                )

        # 3. Use default value
        if secret_value is None and default is not None:
            secret_value = default
            logger.debug(f"Using default value for secret '{secret_name}'")

        # 4. Check if required
        if secret_value is None and required:
            sources = [f"secret file '{secret_file}'"]
            if env_var_name:
                sources.append(f"environment variable '{env_var_name}'")
            raise ValueError(
                f"Required secret '{secret_name}' not found in {', '.join(sources)}"
            )

        # Cache the result
        if secret_value is not None:
            self._secrets_cache[cache_key] = secret_value

        return secret_value

    def get_database_url(
        self,
        base_url: str,
        password_secret: str = "db_password",
        password_env_var: str = "DATABASE_PASSWORD",
    ) -> str:
        """
        Construct database URL with password from secrets.

        Args:
            base_url: Base database URL with placeholder for password
            password_secret: Name of the password secret file
            password_env_var: Environment variable name for password fallback

        Returns:
            Complete database URL with password
        """
        password = self.get_secret(
            password_secret, env_var_name=password_env_var, required=True
        )

        # Replace password placeholder in URL
        if "REPLACE_WITH_DB_PASSWORD" in base_url:
            return base_url.replace("REPLACE_WITH_DB_PASSWORD", password)
        elif ":password@" in base_url:
            return base_url.replace(":password@", f":{password}@")
        else:
            # Assume URL format needs password injection
            parts = base_url.split("://")
            if len(parts) == 2:
                protocol, rest = parts
                if "@" in rest:
                    # URL already has user info
                    user_info, host_db = rest.split("@", 1)
                    if ":" not in user_info:
                        # Add password to existing user
                        return f"{protocol}://{user_info}:{password}@{host_db}"
                    else:
                        # Replace existing password
                        user, _ = user_info.split(":", 1)
                        return f"{protocol}://{user}:{password}@{host_db}"

        logger.warning(f"Unable to inject password into database URL: {base_url}")
        return base_url

    def get_redis_url(
        self,
        base_url: str,
        password_secret: str = "redis_password",
        password_env_var: str = "REDIS_PASSWORD",
    ) -> str:
        """
        Construct Redis URL with password from secrets.

        Args:
            base_url: Base Redis URL
            password_secret: Name of the password secret file
            password_env_var: Environment variable name for password fallback

        Returns:
            Complete Redis URL with password
        """
        password = self.get_secret(
            password_secret, env_var_name=password_env_var, required=False
        )

        if not password:
            return base_url

        # Inject password into Redis URL
        if "://" in base_url:
            protocol, rest = base_url.split("://", 1)
            return f"{protocol}://:{password}@{rest}"

        return base_url

    def get_api_key(
        self,
        service_name: str,
        secret_name: str | None = None,
        env_var_name: str | None = None,
        required: bool = True,
    ) -> str | None:
        """
        Get API key for external service.

        Args:
            service_name: Name of the service (e.g., 'era5', 'modis')
            secret_name: Name of the secret file (defaults to f"{service_name}_api_key")
            env_var_name: Environment variable name (defaults to f"{service_name.upper()}_API_KEY")
            required: Whether the API key is required

        Returns:
            API key or None if not found and not required
        """
        if secret_name is None:
            secret_name = f"{service_name}_api_key"
        if env_var_name is None:
            env_var_name = f"{service_name.upper()}_API_KEY"

        return self.get_secret(
            secret_name=secret_name, env_var_name=env_var_name, required=required
        )

    def validate_secrets(
        self, required_secrets: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        """
        Validate that all required secrets are available.

        Args:
            required_secrets: Dictionary mapping secret names to their configuration
                             Format: {
                                 "secret_name": {
                                     "env_var": "ENV_VAR_NAME",
                                     "required": True,
                                     "description": "What this secret is for"
                                 }
                             }

        Returns:
            Dictionary of validation results

        Raises:
            ValueError: If any required secrets are missing
        """
        validation_results = {}
        missing_secrets = []

        for secret_name, config in required_secrets.items():
            env_var = config.get("env_var")
            required = config.get("required", True)
            description = config.get("description", "")

            try:
                value = self.get_secret(
                    secret_name=secret_name, env_var_name=env_var, required=required
                )

                if value:
                    validation_results[secret_name] = "✓ Available"
                else:
                    validation_results[secret_name] = "⚠ Not set (optional)"

            except ValueError:
                validation_results[secret_name] = "✗ Missing (required)"
                missing_secrets.append(f"{secret_name} ({description})")

        if missing_secrets:
            raise ValueError(
                f"Missing required secrets: {', '.join(missing_secrets)}. "
                "Ensure they are provided via Docker secrets, Kubernetes secrets, "
                "or environment variables."
            )

        return validation_results

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._secrets_cache.clear()
        logger.debug("Secrets cache cleared")

    def get_secret_status(self) -> dict[str, Any]:
        """
        Get status information about secrets management.

        Returns:
            Dictionary with secrets manager status
        """
        return {
            "secrets_directory": str(self.secrets_dir),
            "secrets_directory_exists": self.secrets_dir.exists(),
            "secrets_directory_readable": self.secrets_dir.exists()
            and os.access(self.secrets_dir, os.R_OK),
            "cached_secrets_count": len(self._secrets_cache),
            "available_secret_files": [
                f.name
                for f in self.secrets_dir.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ]
            if self.secrets_dir.exists()
            else [],
        }


class KubernetesSecretsManager(SecretsManager):
    """
    Kubernetes-specific secrets manager with ConfigMap support.
    """

    def __init__(
        self,
        secrets_dir: str | Path = "/var/secrets",
        configmaps_dir: str | Path = "/var/configmaps",
    ):
        """
        Initialize Kubernetes secrets manager.

        Args:
            secrets_dir: Directory where Kubernetes secrets are mounted
            configmaps_dir: Directory where Kubernetes ConfigMaps are mounted
        """
        super().__init__(secrets_dir)
        self.configmaps_dir = Path(configmaps_dir)

    def get_config_value(
        self,
        config_name: str,
        env_var_name: str | None = None,
        default: str | None = None,
        required: bool = False,
    ) -> str | None:
        """
        Get configuration value from ConfigMap or environment variable.

        Args:
            config_name: Name of the config key (file name in configmaps directory)
            env_var_name: Environment variable name as fallback
            default: Default value if config not found
            required: Whether the config is required

        Returns:
            Configuration value or None if not found and not required
        """
        config_value = None

        # Try ConfigMap file first
        config_file = self.configmaps_dir / config_name
        if config_file.exists() and config_file.is_file():
            try:
                config_value = config_file.read_text().strip()
                logger.debug(f"Loaded config '{config_name}' from ConfigMap")
            except Exception as e:
                logger.warning(f"Failed to read ConfigMap file '{config_file}': {e}")

        # Fallback to environment variable
        if config_value is None and env_var_name:
            config_value = os.getenv(env_var_name)
            if config_value:
                logger.debug(
                    f"Loaded config '{config_name}' from environment variable '{env_var_name}'"
                )

        # Use default value
        if config_value is None and default is not None:
            config_value = default
            logger.debug(f"Using default value for config '{config_name}'")

        # Check if required
        if config_value is None and required:
            sources = [f"ConfigMap file '{config_file}'"]
            if env_var_name:
                sources.append(f"environment variable '{env_var_name}'")
            raise ValueError(
                f"Required config '{config_name}' not found in {', '.join(sources)}"
            )

        return config_value


# Global secrets manager instance
_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager:
    """
    Get the global secrets manager instance.

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        # Detect environment and create appropriate manager
        if Path("/var/secrets").exists() or Path("/var/configmaps").exists():
            # Kubernetes environment
            _secrets_manager = KubernetesSecretsManager()
        else:
            # Docker or local environment
            _secrets_manager = SecretsManager()

    return _secrets_manager


def load_secret_from_file_or_env(
    secret_name: str,
    env_var_name: str | None = None,
    default: str | None = None,
    required: bool = True,
) -> str | None:
    """
    Convenience function to load a secret.

    Args:
        secret_name: Name of the secret file
        env_var_name: Environment variable name as fallback
        default: Default value if not found
        required: Whether the secret is required

    Returns:
        Secret value or None if not found and not required
    """
    manager = get_secrets_manager()
    return manager.get_secret(
        secret_name=secret_name,
        env_var_name=env_var_name,
        default=default,
        required=required,
    )


def validate_production_secrets() -> dict[str, str]:
    """
    Validate all required secrets for production deployment.

    Returns:
        Dictionary of validation results
    """
    required_secrets = {
        "api_secret_key": {
            "env_var": "SECRET_KEY",
            "required": True,
            "description": "API secret key for JWT tokens and encryption",
        },
        "db_password": {
            "env_var": "DATABASE_PASSWORD",
            "required": True,
            "description": "Database password for PostgreSQL/TimescaleDB",
        },
        "redis_password": {
            "env_var": "REDIS_PASSWORD",
            "required": False,
            "description": "Redis password (optional)",
        },
        "era5_api_key": {
            "env_var": "ERA5_API_KEY",
            "required": True,
            "description": "ERA5 Climate Data API key",
        },
        "modis_api_key": {
            "env_var": "MODIS_API_KEY",
            "required": True,
            "description": "MODIS/NASA EarthData API key",
        },
    }

    manager = get_secrets_manager()
    return manager.validate_secrets(required_secrets)
