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

import schedule
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class ERA5RequestConfig(BaseModel):
    """Configuration for ERA5 data requests."""

    model_config = ConfigDict(frozen=True)

    product_type: str = Field(default="reanalysis", description="ERA5 product type")
    format_type: str = Field(default="netcdf", description="Output format")
    variables: list[str] = Field(
        default=["2m_temperature", "2m_dewpoint_temperature", "total_precipitation"],
        description="ERA5 variables to download",
    )
    pressure_levels: list[str] | None = Field(
        default=None, description="Pressure levels if needed"
    )

    # Geographic bounds (Africa focus)
    area: list[float] = Field(
        default=[40, -20, -35, 55],  # North, West, South, East
        description="Geographic area bounds [N, W, S, E]",
    )

    # Temporal configuration
    years: list[str] = Field(..., description="Years to download")
    months: list[str] = Field(..., description="Months to download")
    days: list[str] = Field(..., description="Days to download")
    times: list[str] = Field(
        default=["00:00", "06:00", "12:00", "18:00"], description="Times to download"
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

    def __init__(self, settings: Settings | None = None):
        """Initialize ERA5 client with configuration.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.download_directory = Path(self.settings.data.directory) / "era5"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Initialize CDS API client (lazy loading)
        self._cds_client = None

        logger.info(
            f"ERA5 client initialized with download directory: {self.download_directory}"
        )

    @property
    def cds_client(self):
        """Lazy-loaded CDS API client."""
        if self._cds_client is None:
            try:
                import cdsapi

                self._cds_client = cdsapi.Client()
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

    def download_temperature_data(
        self, start_date: date, end_date: date, area_bounds: list[float] | None = None
    ) -> ERA5DownloadResult:
        """Download ERA5 temperature data for specified period and area.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            area_bounds: Geographic bounds [N, W, S, E], defaults to Africa

        Returns:
            Download result with file path and metadata
        """
        logger.info(f"Starting ERA5 temperature download: {start_date} to {end_date}")

        download_start = datetime.now()

        # Build request configuration
        config = self._build_request_config(start_date, end_date, area_bounds)

        # Generate output filename
        output_file = self._generate_filename(start_date, end_date, "temperature")

        try:
            # Submit download request to CDS
            request_id = self._submit_cds_request("temperature", config, output_file)

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

    def _build_request_config(
        self, start_date: date, end_date: date, area_bounds: list[float] | None
    ) -> ERA5RequestConfig:
        """Build CDS request configuration from parameters."""

        # Generate date ranges
        years = [str(year) for year in range(start_date.year, end_date.year + 1)]
        months = [
            f"{month:02d}" for month in range(start_date.month, end_date.month + 1)
        ]
        days = [f"{day:02d}" for day in range(start_date.day, end_date.day + 1)]

        return ERA5RequestConfig(
            years=years,
            months=months,
            days=days,
            area=area_bounds or [40, -20, -35, 55],  # Default to Africa bounds
            variables=[
                "2m_temperature",
                "maximum_2m_temperature_since_previous_post_processing",
                "minimum_2m_temperature_since_previous_post_processing",
            ],
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
        """Validate downloaded ERA5 file for quality and completeness.

        Args:
            file_path: Path to the NetCDF file to validate

        Returns:
            Dict with validation results including success status and details
        """
        validation_result = {
            "file_exists": False,
            "file_size_valid": False,
            "data_accessible": False,
            "variables_present": False,
            "temporal_coverage_valid": False,
            "spatial_bounds_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "variables_found": [],
            "temporal_range": {},
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
                import xarray as xr

                with xr.open_dataset(file_path) as ds:
                    validation_result["data_accessible"] = True

                    # Check for required temperature variables
                    expected_vars = ["t2m", "mx2t", "mn2t"]  # ERA5 variable names
                    found_vars = [var for var in expected_vars if var in ds.data_vars]
                    validation_result["variables_found"] = found_vars
                    validation_result["variables_present"] = len(found_vars) >= 1

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

                    # Validate spatial bounds (should cover part of Africa)
                    if "latitude" in ds.coords and "longitude" in ds.coords:
                        lat_range = [float(ds.latitude.min()), float(ds.latitude.max())]
                        lon_range = [
                            float(ds.longitude.min()),
                            float(ds.longitude.max()),
                        ]

                        # Check if bounds overlap with Africa region
                        africa_bounds = {"lat": [-35, 40], "lon": [-20, 55]}
                        lat_overlap = (
                            lat_range[0] <= africa_bounds["lat"][1]
                            and lat_range[1] >= africa_bounds["lat"][0]
                        )
                        lon_overlap = (
                            lon_range[0] <= africa_bounds["lon"][1]
                            and lon_range[1] >= africa_bounds["lon"][0]
                        )

                        validation_result["spatial_bounds_valid"] = (
                            lat_overlap and lon_overlap
                        )

            except ImportError:
                validation_result["error_message"] = (
                    "xarray not available for data validation"
                )
            except Exception as e:
                validation_result["error_message"] = f"Data validation error: {e}"

        except Exception as e:
            validation_result["error_message"] = f"File validation error: {e}"

        # Overall validation success
        overall_valid = all(
            [
                validation_result["file_exists"],
                validation_result["file_size_valid"],
                validation_result["data_accessible"],
                validation_result["variables_present"],
                validation_result["temporal_coverage_valid"],
                validation_result["spatial_bounds_valid"],
            ]
        )

        validation_result["success"] = overall_valid

        if overall_valid:
            logger.info(f"File validation successful: {file_path.name}")
        else:
            logger.warning(
                f"File validation failed: {file_path.name} - {validation_result['error_message']}"
            )

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

    def download_and_validate_temperature_data(
        self,
        start_date: date,
        end_date: date,
        area_bounds: list[float] | None = None,
        max_retries: int = 3,
    ) -> ERA5DownloadResult:
        """Download temperature data with built-in validation and retry logic.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            area_bounds: Geographic bounds [N, W, S, E], defaults to Africa
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Download result with validation information
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt + 1} of {max_retries}")

                # Download data
                result = self.download_temperature_data(
                    start_date, end_date, area_bounds
                )

                if result.success:
                    # Validate downloaded file
                    validation_result = self.validate_downloaded_file(result.file_path)

                    if validation_result["success"]:
                        logger.info("Download and validation completed successfully")
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

    async def get_climate_data(self, *args, **kwargs):
        """Alias for download_temperature_data for backward compatibility with tests."""
        return self.download_temperature_data(*args, **kwargs)
