"""ERA5 Climate Data Ingestion Client.

This module provides a client for downloading ERA5 reanalysis data from the
Copernicus Climate Data Store (CDS). It handles authentication, data requests,
and provides a clean interface for retrieving temperature and climate data.

Dependencies:
- cdsapi: Copernicus Climate Data Store API client
- requests: HTTP client for API interactions
- pathlib: File system path handling

Assumptions:
- CDS API credentials are configured in ~/.cdsapirc or via environment
- Sufficient disk space available for downloaded data files
- Internet connectivity to Copernicus CDS servers
"""

import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import schedule
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class ERA5RequestConfig(BaseModel):
    """Configuration for ERA5 data requests following research best practices."""

    model_config = ConfigDict(frozen=True)

    product_type: str = Field(default="reanalysis", description="ERA5 product type")
    format_type: str = Field(default="netcdf", description="Output format")

    # Comprehensive variable sets based on research recommendations
    variables: list[str] = Field(
        default=[
            "2m_temperature",
            "total_precipitation",
            "2m_relative_humidity",
            "2m_dewpoint_temperature",
        ],
        description="ERA5 variables to download",
    )

    # Variable presets for different use cases
    variable_preset: str | None = Field(
        default=None,
        description="Preset variable group: 'malaria_core', 'malaria_extended', 'temperature_only', 'comprehensive'",
    )

    pressure_levels: list[str] | None = Field(
        default=None, description="Pressure levels if needed"
    )
    grid_resolution: str = Field(
        default="0.25/0.25", description="Spatial resolution in degrees"
    )

    # Geographic bounds with regional presets
    area: list[float] = Field(
        default=[40, -20, -35, 55],  # North, West, South, East
        description="Geographic area bounds [N, W, S, E]",
    )
    region_preset: str | None = Field(
        default=None,
        description="Regional preset: 'africa', 'west_africa', 'east_africa', 'southern_africa'",
    )

    # Enhanced temporal configuration
    years: list[str] = Field(..., description="Years to download")
    months: list[str] = Field(..., description="Months to download")
    days: list[str] = Field(..., description="Days to download")
    times: list[str] = Field(
        default=["00:00", "06:00", "12:00", "18:00"],
        description="Times to download (6-hourly recommended for efficiency)",
    )

    # Temporal aggregation options
    temporal_aggregation: str | None = Field(
        default=None,
        description="Temporal aggregation: 'hourly', 'daily', 'monthly', 'seasonal'",
    )


class ERA5DownloadResult(BaseModel):
    """Result of an ERA5 data download operation."""

    request_id: str = Field(description="CDS request identifier")
    file_path: Path = Field(description="Path to downloaded file")
    file_size_bytes: int = Field(description="Size of downloaded file")
    variables: list[str] = Field(description="Variables included in download")
    temporal_coverage: dict[str, str] = Field(description="Start and end dates")
    download_duration_seconds: float = Field(description="Time taken for download")
    success: bool = Field(description="Whether download completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )


class ERA5Client:
    """Client for downloading ERA5 climate data from Copernicus CDS."""

    # Variable presets based on research recommendations
    VARIABLE_PRESETS = {
        "malaria_core": [
            "2m_temperature",
            "total_precipitation",
            "2m_relative_humidity",
            "2m_dewpoint_temperature",
        ],
        "malaria_extended": [
            "2m_temperature",
            "maximum_2m_temperature_in_the_last_24_hours",
            "minimum_2m_temperature_in_the_last_24_hours",
            "total_precipitation",
            "2m_relative_humidity",
            "2m_dewpoint_temperature",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "surface_pressure",
        ],
        "temperature_only": [
            "2m_temperature",
            "maximum_2m_temperature_in_the_last_24_hours",
            "minimum_2m_temperature_in_the_last_24_hours",
        ],
        "comprehensive": [
            "2m_temperature",
            "maximum_2m_temperature_in_the_last_24_hours",
            "minimum_2m_temperature_in_the_last_24_hours",
            "2m_dewpoint_temperature",
            "total_precipitation",
            "large_scale_precipitation",
            "convective_precipitation",
            "2m_relative_humidity",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "surface_pressure",
            "mean_sea_level_pressure",
            "evaporation",
            "soil_temperature_level_1",
        ],
    }

    # Regional presets for malaria-endemic areas
    REGIONAL_PRESETS = {
        "africa": [40, -20, -35, 55],  # North, West, South, East
        "west_africa": [20, -20, 5, 20],
        "east_africa": [15, 30, -12, 52],
        "southern_africa": [0, 10, -35, 35],
    }

    # Quality thresholds for data validation
    QUALITY_THRESHOLDS = {
        "2m_temperature": {"min": 200, "max": 330},  # Kelvin
        "total_precipitation": {"min": 0, "max": 0.1},  # meters
        "2m_relative_humidity": {"min": 0, "max": 100},  # %
        "2m_dewpoint_temperature": {"min": 180, "max": 320},  # Kelvin
        "surface_pressure": {"min": 50000, "max": 110000},  # Pa
        "10m_u_component_of_wind": {"min": -100, "max": 100},  # m/s
        "10m_v_component_of_wind": {"min": -100, "max": 100},  # m/s
    }

    def __init__(
        self, settings: Settings | None = None, auth_method: str = "config_file"
    ):
        """Initialize ERA5 client with enhanced configuration.

        Args:
            settings: Application settings instance
            auth_method: Authentication method ('config_file', 'environment', 'explicit')
        """
        self.settings = settings or Settings()
        self.auth_method = auth_method
        self.download_directory = Path(self.settings.data.directory) / "era5"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for organization
        (self.download_directory / "raw").mkdir(exist_ok=True)
        (self.download_directory / "processed").mkdir(exist_ok=True)
        (self.download_directory / "cache").mkdir(exist_ok=True)

        # Initialize CDS API client (lazy loading)
        self._cds_client = None

        # Cache for request optimization
        self._request_cache: dict[str, Any] = {}

        logger.info(
            f"ERA5 client initialized with download directory: {self.download_directory}"
        )
        logger.info(f"Authentication method: {auth_method}")

    @property
    def cds_client(self):
        """Lazy-loaded CDS API client with multiple authentication methods."""
        if self._cds_client is None:
            try:
                import os
                from pathlib import Path

                import cdsapi

                # Initialize client based on authentication method
                if self.auth_method == "environment":
                    # Use environment variables
                    url = os.environ.get(
                        "CDS_URL", "https://cds.climate.copernicus.eu/api"
                    )
                    key = os.environ.get("CDS_KEY")
                    if not key:
                        raise ValueError("CDS_KEY environment variable not set")
                    self._cds_client = cdsapi.Client(url=url, key=key)
                    logger.info("CDS client initialized with environment variables")

                elif self.auth_method == "explicit":
                    # Explicit configuration (would need to be passed in)
                    raise NotImplementedError(
                        "Explicit authentication not yet implemented"
                    )

                else:  # config_file (default)
                    # Use ~/.cdsapirc configuration file
                    config_file = Path.home() / ".cdsapirc"
                    if not config_file.exists():
                        raise FileNotFoundError(
                            f"CDS API configuration file not found at {config_file}. "
                            "Please create it with your CDS API credentials."
                        )
                    self._cds_client = cdsapi.Client()
                    logger.info("CDS client initialized with configuration file")

                logger.info("CDS API client initialized successfully")

            except ImportError as e:
                raise ImportError(
                    "cdsapi package required for ERA5 data access. "
                    "Install with: pip install cdsapi"
                ) from e
            except Exception as e:
                logger.error(f"Failed to initialize CDS client: {e}")
                raise
        return self._cds_client

    def validate_credentials(self) -> bool:
        """Validate CDS API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Test credentials with a minimal request
            test_request = {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": "2m_temperature",
                "year": "2023",
                "month": "01",
                "day": "01",
                "time": "00:00",
                "area": [1, 1, 0, 2],  # Very small area
            }

            # This will validate credentials without actually downloading
            self.cds_client.retrieve("reanalysis-era5-single-levels", test_request)
            logger.info("CDS credentials validated successfully")
            return True

        except Exception as e:
            logger.error(f"CDS credential validation failed: {e}")
            return False

    def download_climate_data(
        self,
        start_date: date,
        end_date: date,
        variables: list[str] | None = None,
        variable_preset: str | None = None,
        area_bounds: list[float] | None = None,
        region_preset: str | None = None,
        data_type: str = "climate",
    ) -> ERA5DownloadResult:
        """Download comprehensive ERA5 climate data with enhanced options.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            variables: Specific variables to download
            variable_preset: Preset variable group ('malaria_core', 'malaria_extended', etc.)
            area_bounds: Geographic bounds [N, W, S, E]
            region_preset: Regional preset ('africa', 'west_africa', etc.)
            data_type: Data type identifier for filename

        Returns:
            Download result with file path and metadata
        """
        logger.info(f"Starting ERA5 {data_type} download: {start_date} to {end_date}")

        if variable_preset:
            logger.info(f"Using variable preset: {variable_preset}")
        if region_preset:
            logger.info(f"Using region preset: {region_preset}")

        download_start = datetime.now()

        # Build request configuration with enhanced options
        config = self._build_request_config(
            start_date=start_date,
            end_date=end_date,
            variables=variables,
            variable_preset=variable_preset,
            area_bounds=area_bounds,
            region_preset=region_preset,
        )

        # Generate output filename
        preset_suffix = f"_{variable_preset}" if variable_preset else ""
        region_suffix = f"_{region_preset}" if region_preset else ""
        output_file = self._generate_filename(
            start_date, end_date, f"{data_type}{preset_suffix}{region_suffix}"
        )

        try:
            # Submit download request to CDS
            request_id = self._submit_cds_request(data_type, config, output_file)

            # Calculate download metrics
            download_duration = (datetime.now() - download_start).total_seconds()
            file_size = output_file.stat().st_size if output_file.exists() else 0

            return ERA5DownloadResult(
                request_id=request_id,
                file_path=output_file,
                file_size_bytes=file_size,
                variables=config.variables,
                temporal_coverage={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                download_duration_seconds=download_duration,
                success=True,
                error_message=None,
            )

        except Exception as e:
            logger.error(f"ERA5 download failed: {e}")
            return ERA5DownloadResult(
                request_id="failed",
                file_path=Path(""),
                file_size_bytes=0,
                variables=[],
                temporal_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def download_temperature_data(
        self, start_date: date, end_date: date, area_bounds: list[float] | None = None
    ) -> ERA5DownloadResult:
        """Download ERA5 temperature data (backward compatibility method).

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            area_bounds: Geographic bounds [N, W, S, E], defaults to Africa

        Returns:
            Download result with file path and metadata
        """
        return self.download_climate_data(
            start_date=start_date,
            end_date=end_date,
            variable_preset="temperature_only",
            area_bounds=area_bounds,
            data_type="temperature",
        )

    def download_malaria_climate_data(
        self,
        start_date: date,
        end_date: date,
        region_preset: str = "africa",
        extended: bool = False,
    ) -> ERA5DownloadResult:
        """Download climate data optimized for malaria research.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            region_preset: Regional preset for malaria-endemic areas
            extended: Whether to use extended variable set

        Returns:
            Download result with file path and metadata
        """
        variable_preset = "malaria_extended" if extended else "malaria_core"

        return self.download_climate_data(
            start_date=start_date,
            end_date=end_date,
            variable_preset=variable_preset,
            region_preset=region_preset,
            data_type="malaria_climate",
        )

    def _build_request_config(
        self,
        start_date: date,
        end_date: date,
        variables: list[str] | None = None,
        area_bounds: list[float] | None = None,
        variable_preset: str | None = None,
        region_preset: str | None = None,
        **kwargs,
    ) -> ERA5RequestConfig:
        """Build comprehensive CDS request configuration from parameters."""

        # Generate date ranges
        years = [str(year) for year in range(start_date.year, end_date.year + 1)]
        months = [
            f"{month:02d}" for month in range(start_date.month, end_date.month + 1)
        ]
        days = [f"{day:02d}" for day in range(start_date.day, end_date.day + 1)]

        # Resolve variables from preset or use provided list
        if variable_preset:
            if variable_preset not in self.VARIABLE_PRESETS:
                raise ValueError(f"Unknown variable preset: {variable_preset}")
            resolved_variables = self.VARIABLE_PRESETS[variable_preset]
            logger.info(
                f"Using variable preset '{variable_preset}' with {len(resolved_variables)} variables"
            )
        elif variables:
            resolved_variables = variables
        else:
            resolved_variables = self.VARIABLE_PRESETS["malaria_core"]
            logger.info("Using default malaria_core variable preset")

        # Resolve area from preset or use provided bounds
        if region_preset:
            if region_preset not in self.REGIONAL_PRESETS:
                raise ValueError(f"Unknown region preset: {region_preset}")
            resolved_area = self.REGIONAL_PRESETS[region_preset]
            logger.info(f"Using region preset '{region_preset}': {resolved_area}")
        elif area_bounds:
            resolved_area = area_bounds
        else:
            resolved_area = self.REGIONAL_PRESETS["africa"]
            logger.info("Using default Africa region")

        return ERA5RequestConfig(
            years=years,
            months=months,
            days=days,
            area=resolved_area,
            variables=resolved_variables,
            variable_preset=variable_preset,
            region_preset=region_preset,
            **kwargs,
        )

    def _generate_filename(
        self, start_date: date, end_date: date, data_type: str
    ) -> Path:
        """Generate standardized filename for downloaded data."""
        date_str = f"{start_date.isoformat()}_{end_date.isoformat()}"
        filename = f"era5_{data_type}_{date_str}.nc"
        return self.download_directory / filename

    def _submit_cds_request(
        self, data_type: str, config: ERA5RequestConfig, output_file: Path
    ) -> str:
        """Submit request to CDS API and handle download."""

        # Build CDS API request
        request_params = {
            "product_type": config.product_type,
            "format": config.format_type,
            "variable": config.variables,
            "year": config.years,
            "month": config.months,
            "day": config.days,
            "time": config.times,
            "area": config.area,
        }

        logger.info(f"Submitting CDS request for {data_type}: {request_params}")

        # Submit request and download
        self.cds_client.retrieve(
            "reanalysis-era5-single-levels", request_params, str(output_file)
        )

        # Generate request ID (CDS doesn't provide one directly)
        request_id = f"era5_{data_type}_{datetime.now().isoformat()}"

        logger.info(f"CDS request completed successfully: {request_id}")
        return request_id

    def list_downloaded_files(self) -> list[Path]:
        """List all ERA5 files in download directory.

        Returns:
            List of paths to downloaded ERA5 files
        """
        return list(self.download_directory.glob("era5_*.nc"))

    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """Clean up old downloaded files.

        Args:
            days_to_keep: Number of days of files to retain

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for file_path in self.list_downloaded_files():
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old ERA5 file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old ERA5 files")
        return deleted_count

    def validate_downloaded_file(self, file_path: Path) -> dict[str, bool | str | int]:
        """Validate downloaded ERA5 file with comprehensive quality checks.

        Args:
            file_path: Path to the NetCDF file to validate

        Returns:
            Dict with validation results including success status and details
        """
        validation_result: dict[str, Any] = {
            "file_exists": False,
            "file_size_valid": False,
            "data_accessible": False,
            "variables_present": False,
            "temporal_coverage_valid": False,
            "spatial_bounds_valid": False,
            "physical_ranges_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "variables_found": [],
            "temporal_range": {},
            "quality_issues": [],
            "quality_score": 0,
        }

        try:
            # Check file existence
            if not file_path.exists():
                validation_result["error_message"] = "File does not exist"
                validation_result["success"] = False
                return validation_result

            validation_result["file_exists"] = True

            # Check file size (should be > 1MB for valid ERA5 data)
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            validation_result["file_size_valid"] = file_size_mb > 1.0

            # Try to open and validate NetCDF file
            try:
                import numpy as np
                import xarray as xr

                with xr.open_dataset(file_path) as ds:
                    validation_result["data_accessible"] = True

                    # Check for variables and their physical ranges
                    found_vars = list(ds.data_vars.keys())
                    validation_result["variables_found"] = found_vars
                    validation_result["variables_present"] = len(found_vars) >= 1

                    # Comprehensive physical range validation
                    range_issues = []
                    for var_name in found_vars:
                        if var_name in self.QUALITY_THRESHOLDS:
                            thresholds = self.QUALITY_THRESHOLDS[var_name]
                            data = ds[var_name]

                            # Check for values outside physical ranges
                            valid_data = data.where(~np.isnan(data))
                            too_low = (
                                (valid_data < thresholds["min"]).sum().item()
                                if valid_data.size > 0
                                else 0
                            )
                            too_high = (
                                (valid_data > thresholds["max"]).sum().item()
                                if valid_data.size > 0
                                else 0
                            )

                            if too_low > 0:
                                range_issues.append(
                                    f"{var_name}: {too_low} values below {thresholds['min']}"
                                )
                            if too_high > 0:
                                range_issues.append(
                                    f"{var_name}: {too_high} values above {thresholds['max']}"
                                )

                            # Check for excessive missing data
                            missing_ratio = np.isnan(data).sum().item() / data.size
                            if missing_ratio > 0.5:  # More than 50% missing
                                range_issues.append(
                                    f"{var_name}: {missing_ratio:.1%} missing data"
                                )

                    validation_result["quality_issues"] = range_issues
                    validation_result["physical_ranges_valid"] = len(range_issues) == 0

                    # Validate temporal coverage
                    if "time" in ds.coords:
                        time_values = ds.time.values
                        validation_result["temporal_range"] = {
                            "start": str(time_values[0]),
                            "end": str(time_values[-1]),
                            "count": len(time_values),
                        }
                        validation_result["temporal_coverage_valid"] = (
                            len(time_values) > 0
                        )

                        # Check for temporal gaps
                        if len(time_values) > 1:
                            time_diffs = np.diff(time_values)
                            expected_interval = time_diffs[0]
                            irregular_intervals = np.sum(
                                time_diffs != expected_interval
                            )
                            if irregular_intervals > 0:
                                validation_result["quality_issues"].append(
                                    f"Irregular time intervals: {irregular_intervals} gaps"
                                )

                    # Validate spatial bounds
                    if "latitude" in ds.coords and "longitude" in ds.coords:
                        lat_range = [float(ds.latitude.min()), float(ds.latitude.max())]
                        lon_range = [
                            float(ds.longitude.min()),
                            float(ds.longitude.max()),
                        ]

                        validation_result["spatial_bounds"] = {
                            "latitude_range": lat_range,
                            "longitude_range": lon_range,
                        }

                        # Check if bounds are reasonable
                        lat_valid = -90 <= lat_range[0] <= lat_range[1] <= 90
                        lon_valid = -180 <= lon_range[0] <= lon_range[1] <= 360
                        validation_result["spatial_bounds_valid"] = (
                            lat_valid and lon_valid
                        )

                        if not lat_valid:
                            validation_result["quality_issues"].append(
                                "Invalid latitude range"
                            )
                        if not lon_valid:
                            validation_result["quality_issues"].append(
                                "Invalid longitude range"
                            )

            except ImportError:
                validation_result["error_message"] = (
                    "xarray not available for data validation"
                )
            except Exception as e:
                validation_result["error_message"] = f"Data validation error: {e}"

        except Exception as e:
            validation_result["error_message"] = f"File validation error: {e}"

        # Calculate overall quality score
        quality_score = 100
        if not validation_result["file_exists"]:
            quality_score -= 50
        if not validation_result["file_size_valid"]:
            quality_score -= 20
        if not validation_result["data_accessible"]:
            quality_score -= 30
        if not validation_result["variables_present"]:
            quality_score -= 20
        if not validation_result["temporal_coverage_valid"]:
            quality_score -= 15
        if not validation_result["spatial_bounds_valid"]:
            quality_score -= 15
        if not validation_result["physical_ranges_valid"]:
            quality_score -= 20

        # Deduct points for quality issues
        quality_score -= len(validation_result["quality_issues"]) * 5

        validation_result["quality_score"] = max(0, quality_score)

        # Overall validation success
        overall_valid = all(
            [
                validation_result["file_exists"],
                validation_result["file_size_valid"],
                validation_result["data_accessible"],
                validation_result["variables_present"],
                validation_result["temporal_coverage_valid"],
                validation_result["spatial_bounds_valid"],
                validation_result["physical_ranges_valid"],
            ]
        )

        validation_result["success"] = overall_valid

        if overall_valid:
            logger.info(
                f"File validation successful: {file_path.name} (Quality: {quality_score}/100)"
            )
        else:
            logger.warning(
                f"File validation failed: {file_path.name} - Issues: {len(validation_result['quality_issues'])}"
            )
            for issue in validation_result["quality_issues"]:
                logger.warning(f"  - {issue}")

        return validation_result

    def setup_automated_updates(self) -> None:
        """Set up automated daily and monthly data downloads.

        Schedules:
        - Daily update at 06:00 UTC for recent data (last 7 days)
        - Monthly update on 1st day of month for previous month's complete data
        """
        logger.info("Setting up automated ERA5 data updates")

        # Schedule daily updates for recent data
        schedule.every().day.at("06:00").do(self._daily_update_job)

        # Schedule monthly updates for complete monthly data
        schedule.every().month.do(self._monthly_update_job)

        logger.info("Automated update schedule configured")

    def _daily_update_job(self) -> None:
        """Daily job to download recent ERA5 data."""
        try:
            logger.info("Starting daily ERA5 data update")

            # Download data for last 7 days (ERA5 has 3-5 day delay)
            end_date = date.today() - timedelta(days=5)
            start_date = end_date - timedelta(days=6)

            result = self.download_temperature_data(start_date, end_date)

            if result.success:
                # Validate downloaded file
                validation_result = self.validate_downloaded_file(result.file_path)

                if validation_result["success"]:
                    logger.info(
                        f"Daily update completed successfully: {result.file_path.name}"
                    )
                else:
                    logger.error(
                        f"Daily update validation failed: {validation_result['error_message']}"
                    )
            else:
                logger.error(f"Daily update download failed: {result.error_message}")

        except Exception as e:
            logger.error(f"Daily update job failed: {e}")

    def _monthly_update_job(self) -> None:
        """Monthly job to download complete monthly ERA5 data."""
        try:
            logger.info("Starting monthly ERA5 data update")

            # Download complete data for previous month
            today = date.today()
            if today.month == 1:
                prev_month = 12
                year = today.year - 1
            else:
                prev_month = today.month - 1
                year = today.year

            # First and last day of previous month
            start_date = date(year, prev_month, 1)
            if prev_month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, prev_month + 1, 1) - timedelta(days=1)

            result = self.download_temperature_data(start_date, end_date)

            if result.success:
                # Validate downloaded file
                validation_result = self.validate_downloaded_file(result.file_path)

                if validation_result["success"]:
                    logger.info(
                        f"Monthly update completed successfully: {result.file_path.name}"
                    )
                    # Clean up old files after successful monthly update
                    self.cleanup_old_files(days_to_keep=90)
                else:
                    logger.error(
                        f"Monthly update validation failed: {validation_result['error_message']}"
                    )
            else:
                logger.error(f"Monthly update download failed: {result.error_message}")

        except Exception as e:
            logger.error(f"Monthly update job failed: {e}")

    def run_scheduler(self, run_continuously: bool = True) -> None:
        """Run the automated update scheduler.

        Args:
            run_continuously: If True, runs continuously. If False, runs once.
        """
        if run_continuously:
            logger.info("Starting continuous ERA5 update scheduler")
            while True:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
        else:
            logger.info("Running scheduled updates once")
            schedule.run_pending()

    def download_and_validate_climate_data(
        self,
        start_date: date,
        end_date: date,
        variable_preset: str | None = None,
        region_preset: str | None = None,
        area_bounds: list[float] | None = None,
        max_retries: int = 3,
    ) -> ERA5DownloadResult:
        """Download climate data with comprehensive validation and retry logic.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            variable_preset: Variable preset to use
            region_preset: Regional preset to use
            area_bounds: Geographic bounds [N, W, S, E]
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Download result with validation information
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt + 1} of {max_retries}")

                # Download data
                result = self.download_climate_data(
                    start_date=start_date,
                    end_date=end_date,
                    variable_preset=variable_preset,
                    region_preset=region_preset,
                    area_bounds=area_bounds,
                )

                if result.success:
                    # Validate downloaded file
                    validation_result = self.validate_downloaded_file(result.file_path)

                    if validation_result["success"]:
                        logger.info(
                            f"Download and validation completed successfully (Quality: {validation_result['quality_score']}/100)"
                        )
                        return result
                    else:
                        # Delete invalid file and retry
                        if result.file_path.exists():
                            result.file_path.unlink()

                        last_error = (
                            f"Validation failed: {validation_result['error_message']}"
                        )
                        logger.warning(
                            f"Attempt {attempt + 1} validation failed, retrying..."
                        )
                else:
                    last_error = result.error_message
                    logger.warning(
                        f"Attempt {attempt + 1} download failed, retrying..."
                    )

                # Wait before retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = 2**attempt * 60  # 1min, 2min, 4min...
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed with exception: {e}")

                if attempt < max_retries - 1:
                    time.sleep(60)

        # All retries failed
        logger.error(
            f"All {max_retries} download attempts failed. Last error: {last_error}"
        )
        return ERA5DownloadResult(
            request_id="failed_all_retries",
            file_path=Path(""),
            file_size_bytes=0,
            variables=[],
            temporal_coverage={},
            download_duration_seconds=0,
            success=False,
            error_message=f"All {max_retries} attempts failed. Last error: {last_error}",
        )

    def download_and_validate_temperature_data(
        self,
        start_date: date,
        end_date: date,
        area_bounds: list[float] | None = None,
        max_retries: int = 3,
    ) -> ERA5DownloadResult:
        """Download temperature data with built-in validation and retry logic (backward compatibility).

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            area_bounds: Geographic bounds [N, W, S, E], defaults to Africa
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Download result with validation information
        """
        return self.download_and_validate_climate_data(
            start_date=start_date,
            end_date=end_date,
            variable_preset="temperature_only",
            area_bounds=area_bounds,
            max_retries=max_retries,
        )

    def aggregate_temporal_data(
        self,
        file_path: Path,
        aggregation_method: str = "daily",
        variables: list[str] | None = None,
    ) -> Path | None:
        """Aggregate ERA5 data temporally following research workflows.

        Args:
            file_path: Path to NetCDF file to aggregate
            aggregation_method: 'daily', 'monthly', or 'seasonal'
            variables: Variables to aggregate (all if None)

        Returns:
            Path to aggregated file or None if failed
        """
        try:
            import xarray as xr

            logger.info(
                f"Starting {aggregation_method} aggregation of {file_path.name}"
            )

            with xr.open_dataset(file_path) as ds:
                if variables:
                    # Select only specified variables
                    ds = ds[variables]

                aggregated_data = {}

                if aggregation_method == "daily":
                    # Daily aggregation with multiple statistics
                    for var in ds.data_vars:
                        if "precipitation" in var or "tp" in var:
                            # Sum precipitation
                            aggregated_data[f"{var}_total"] = (
                                ds[var].resample(time="1D").sum()
                            )
                        elif "temperature" in var or "t2m" in var or "d2m" in var:
                            # Mean temperature
                            aggregated_data[f"{var}_mean"] = (
                                ds[var].resample(time="1D").mean()
                            )
                            aggregated_data[f"{var}_max"] = (
                                ds[var].resample(time="1D").max()
                            )
                            aggregated_data[f"{var}_min"] = (
                                ds[var].resample(time="1D").min()
                            )
                        elif "humidity" in var or "r2" in var:
                            # Mean humidity
                            aggregated_data[f"{var}_mean"] = (
                                ds[var].resample(time="1D").mean()
                            )
                        else:
                            # Default to mean for other variables
                            aggregated_data[f"{var}_mean"] = (
                                ds[var].resample(time="1D").mean()
                            )

                elif aggregation_method == "monthly":
                    # Monthly aggregation
                    for var in ds.data_vars:
                        aggregated_data[f"{var}_mean"] = (
                            ds[var].resample(time="1M").mean()
                        )
                        aggregated_data[f"{var}_max"] = (
                            ds[var].resample(time="1M").max()
                        )
                        aggregated_data[f"{var}_min"] = (
                            ds[var].resample(time="1M").min()
                        )
                        aggregated_data[f"{var}_std"] = (
                            ds[var].resample(time="1M").std()
                        )

                        if "precipitation" in var or "tp" in var:
                            aggregated_data[f"{var}_total"] = (
                                ds[var].resample(time="1M").sum()
                            )

                elif aggregation_method == "seasonal":
                    # Seasonal aggregation
                    for var in ds.data_vars:
                        seasonal_means = ds[var].groupby("time.season").mean("time")
                        aggregated_data[f"{var}_seasonal"] = seasonal_means

                # Create aggregated dataset
                aggregated_ds = xr.Dataset(aggregated_data)

                # Preserve original attributes
                aggregated_ds.attrs = ds.attrs.copy()
                aggregated_ds.attrs["temporal_resolution"] = aggregation_method
                aggregated_ds.attrs["aggregation_date"] = datetime.now().isoformat()

                # Generate output filename
                output_file = (
                    self.download_directory
                    / "processed"
                    / f"{file_path.stem}_{aggregation_method}.nc"
                )

                # Save aggregated data
                aggregated_ds.to_netcdf(output_file, engine="netcdf4")

                logger.info(f"Temporal aggregation completed: {output_file.name}")
                return output_file

        except Exception as e:
            logger.error(f"Temporal aggregation failed: {e}")
            return None

    def extract_point_data(
        self, file_path: Path, latitude: float, longitude: float, buffer: float = 0.25
    ) -> dict | None:
        """Extract ERA5 data for a specific point location.

        Args:
            file_path: Path to NetCDF file
            latitude: Latitude of point
            longitude: Longitude of point
            buffer: Buffer around point in degrees

        Returns:
            Dictionary with extracted data or None if failed
        """
        try:
            import numpy as np
            import xarray as xr

            logger.info(f"Extracting point data for {latitude}, {longitude}")

            with xr.open_dataset(file_path) as ds:
                # Define extraction area
                lat_min = latitude - buffer
                lat_max = latitude + buffer
                lon_min = longitude - buffer
                lon_max = longitude + buffer

                # Extract data for the area
                subset = ds.sel(
                    latitude=slice(
                        lat_max, lat_min
                    ),  # Note: ERA5 latitudes are descending
                    longitude=slice(lon_min, lon_max),
                )

                # Calculate statistics for each variable
                extracted_data = {
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "buffer": buffer,
                    },
                    "temporal_range": {
                        "start": str(subset.time.min().values),
                        "end": str(subset.time.max().values),
                        "count": len(subset.time),
                    },
                    "variables": {},
                }

                for var_name in subset.data_vars:
                    data = subset[var_name]
                    valid_data = data.where(~np.isnan(data))

                    extracted_data["variables"][var_name] = {
                        "mean": (
                            float(valid_data.mean().values)
                            if valid_data.size > 0
                            else None
                        ),
                        "min": (
                            float(valid_data.min().values)
                            if valid_data.size > 0
                            else None
                        ),
                        "max": (
                            float(valid_data.max().values)
                            if valid_data.size > 0
                            else None
                        ),
                        "std": (
                            float(valid_data.std().values)
                            if valid_data.size > 0
                            else None
                        ),
                        "count": int((~np.isnan(data)).sum().values),
                    }

                    # Add time series data
                    if len(subset.time) > 0:
                        time_series = valid_data.mean(dim=["latitude", "longitude"])
                        extracted_data["variables"][var_name]["time_series"] = {
                            "times": [str(t) for t in subset.time.values],
                            "values": [
                                float(v) if not np.isnan(v) else None
                                for v in time_series.values
                            ],
                        }

                return extracted_data

        except Exception as e:
            logger.error(f"Point extraction failed: {e}")
            return None

    def get_variable_statistics(
        self, file_path: Path, variables: list[str] | None = None
    ) -> dict | None:
        """Get comprehensive statistics for ERA5 variables.

        Args:
            file_path: Path to NetCDF file
            variables: Variables to analyze (all if None)

        Returns:
            Dictionary with variable statistics or None if failed
        """
        try:
            import numpy as np
            import xarray as xr

            logger.info(f"Computing variable statistics for {file_path.name}")

            with xr.open_dataset(file_path) as ds:
                vars_to_analyze = variables or list(ds.data_vars.keys())

                statistics = {
                    "file_info": {
                        "filename": file_path.name,
                        "file_size_mb": round(
                            file_path.stat().st_size / (1024 * 1024), 2
                        ),
                        "variables_count": len(vars_to_analyze),
                    },
                    "spatial_coverage": {
                        "latitude_range": [
                            float(ds.latitude.min()),
                            float(ds.latitude.max()),
                        ],
                        "longitude_range": [
                            float(ds.longitude.min()),
                            float(ds.longitude.max()),
                        ],
                        "grid_points": {
                            "latitude": len(ds.latitude),
                            "longitude": len(ds.longitude),
                        },
                    },
                    "temporal_coverage": {
                        "start": str(ds.time.min().values),
                        "end": str(ds.time.max().values),
                        "count": len(ds.time),
                        "frequency": "hourly" if len(ds.time) > 1 else "single",
                    },
                    "variables": {},
                }

                for var_name in vars_to_analyze:
                    if var_name not in ds.data_vars:
                        continue

                    data = ds[var_name]
                    valid_data = data.where(~np.isnan(data))

                    var_stats = {
                        "units": data.attrs.get("units", "unknown"),
                        "long_name": data.attrs.get("long_name", var_name),
                        "data_coverage": {
                            "total_points": int(data.size),
                            "valid_points": int((~np.isnan(data)).sum().values),
                            "missing_percentage": float(
                                (np.isnan(data).sum() / data.size * 100).values
                            ),
                        },
                        "value_statistics": {
                            "mean": (
                                float(valid_data.mean().values)
                                if valid_data.size > 0
                                else None
                            ),
                            "median": (
                                float(valid_data.median().values)
                                if valid_data.size > 0
                                else None
                            ),
                            "min": (
                                float(valid_data.min().values)
                                if valid_data.size > 0
                                else None
                            ),
                            "max": (
                                float(valid_data.max().values)
                                if valid_data.size > 0
                                else None
                            ),
                            "std": (
                                float(valid_data.std().values)
                                if valid_data.size > 0
                                else None
                            ),
                        },
                    }

                    # Add quality assessment based on thresholds
                    if var_name in self.QUALITY_THRESHOLDS:
                        thresholds = self.QUALITY_THRESHOLDS[var_name]
                        out_of_range = (
                            (
                                (valid_data < thresholds["min"])
                                | (valid_data > thresholds["max"])
                            )
                            .sum()
                            .item()
                        )

                        var_stats["quality_assessment"] = {
                            "physical_range_valid": out_of_range == 0,
                            "out_of_range_count": out_of_range,
                            "expected_range": thresholds,
                        }

                    statistics["variables"][var_name] = var_stats

                return statistics

        except Exception as e:
            logger.error(f"Statistics computation failed: {e}")
            return None

    async def get_climate_data(self, *args, **kwargs):
        """Alias for download_climate_data for backward compatibility with tests."""
        return self.download_climate_data(*args, **kwargs)
