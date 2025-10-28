"""CHIRPS Rainfall Data Ingestion Client.

This module provides a client for downloading CHIRPS (Climate Hazards Group
InfraRed Precipitation with Station data) rainfall data. It handles data
downloads, validation, and provides a clean interface for retrieving
precipitation data for malaria risk assessment.

Dependencies:
- requests: HTTP client for data downloads
- rasterio: GeoTIFF file reading and processing
- numpy: Array operations for data processing
- pathlib: File system path handling

Assumptions:
- No authentication required (open access data)
- Sufficient disk space for downloaded GeoTIFF files
- Internet connectivity to CHIRPS data servers
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import requests
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class CHIRPSRequestConfig(BaseModel):
    """Configuration for CHIRPS data requests."""

    model_config = ConfigDict(frozen=True)

    data_type: str = Field(default="daily", description="Data temporal resolution")
    format_type: str = Field(default="tif", description="Output format")

    # Geographic bounds (Africa focus)
    area_bounds: tuple[float, float, float, float] = Field(
        default=(-20.0, -35.0, 55.0, 40.0),  # West, South, East, North
        description="Geographic area bounds (W, S, E, N)",
    )

    # Temporal configuration
    start_date: date = Field(..., description="Start date for data download")
    end_date: date = Field(..., description="End date for data download")


class CHIRPSDownloadResult(BaseModel):
    """Result of a CHIRPS data download operation."""

    request_id: str = Field(description="Download request identifier")
    file_paths: list[Path] = Field(description="Paths to downloaded files")
    total_size_bytes: int = Field(description="Total size of downloaded files")
    temporal_coverage: dict[str, str] = Field(description="Start and end dates")
    download_duration_seconds: float = Field(description="Time taken for download")
    success: bool = Field(description="Whether download completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    files_processed: int = Field(default=0, description="Number of files processed")


class CHIRPSClient:
    """Client for downloading CHIRPS rainfall data."""

    BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize CHIRPS client with configuration.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.download_directory = Path(self.settings.data.directory) / "chirps"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "MalariaPredictorBackend/1.0 (CHIRPS Data Client)"}
        )

        # Thread pool for parallel downloads
        self.executor = ThreadPoolExecutor(max_workers=5)

        logger.info(
            f"CHIRPS client initialized with download directory: {self.download_directory}"
        )

    def download_rainfall_data(
        self,
        start_date: date,
        end_date: date,
        data_type: str = "daily",
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> CHIRPSDownloadResult:
        """Download CHIRPS rainfall data for specified period.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            data_type: Temporal resolution ("daily" or "monthly")
            area_bounds: Geographic bounds (W, S, E, N), defaults to Africa

        Returns:
            Download result with file paths and metadata
        """
        logger.info(f"Starting CHIRPS {data_type} download: {start_date} to {end_date}")

        download_start = datetime.now()
        downloaded_files = []
        total_size = 0

        try:
            # Generate list of dates/files to download
            if data_type == "daily":
                dates_to_download = self._generate_daily_dates(start_date, end_date)
            elif data_type == "monthly":
                dates_to_download = self._generate_monthly_dates(start_date, end_date)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            # Download files in parallel using ThreadPoolExecutor
            from concurrent.futures import as_completed

            futures = []
            for target_date in dates_to_download:
                future = self.executor.submit(
                    self._download_single_file, target_date, data_type
                )
                futures.append(future)

            # Wait for downloads to complete
            for future in as_completed(futures):
                try:
                    file_path, file_size = future.result()
                    if file_path:
                        downloaded_files.append(file_path)
                        total_size += file_size
                except Exception as e:
                    logger.error(f"Download task failed: {e}")

            download_duration = (datetime.now() - download_start).total_seconds()

            return CHIRPSDownloadResult(
                request_id=f"chirps_{data_type}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                temporal_coverage={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                files_processed=len(downloaded_files),
                error_message=None if downloaded_files else "No files downloaded",
            )

        except Exception as e:
            logger.error(f"CHIRPS download failed: {e}")
            return CHIRPSDownloadResult(
                request_id="failed",
                file_paths=[],
                total_size_bytes=0,
                temporal_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _generate_daily_dates(self, start_date: date, end_date: date) -> list[date]:
        """Generate list of dates for daily data download."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def _generate_monthly_dates(self, start_date: date, end_date: date) -> list[date]:
        """Generate list of dates for monthly data download."""
        dates = []
        current = date(start_date.year, start_date.month, 1)
        end_month = date(end_date.year, end_date.month, 1)

        while current <= end_month:
            dates.append(current)
            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return dates

    def _download_single_file(
        self, target_date: date, data_type: str
    ) -> tuple[Path | None, int]:
        """Download a single CHIRPS file.

        Returns:
            Tuple of (file_path, file_size) or (None, 0) if download failed
        """
        try:
            # Build URL based on data type
            if data_type == "daily":
                filename = f"chirps-v2.0.{target_date.year}.{target_date.month:02d}.{target_date.day:02d}.tif"
                url = f"{self.BASE_URL}/global_daily/tifs/p05/{target_date.year}/{filename}"
            else:  # monthly
                filename = f"chirps-v2.0.{target_date.year}.{target_date.month:02d}.tif"
                url = f"{self.BASE_URL}/global_monthly/tifs/{filename}"

            output_path = self.download_directory / filename

            # Skip if already downloaded
            if output_path.exists():
                logger.info(f"File already exists, skipping: {filename}")
                return output_path, output_path.stat().st_size

            # Download file
            logger.info(f"Downloading: {filename}")
            response = self.session.get(url, stream=True, timeout=300)
            response.raise_for_status()

            # Save to file
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = output_path.stat().st_size
            logger.info(
                f"Downloaded successfully: {filename} ({file_size / 1024 / 1024:.2f} MB)"
            )

            return output_path, file_size

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {target_date}: {e}")
            return None, 0
        except Exception as e:
            logger.error(f"Unexpected error downloading {target_date}: {e}")
            return None, 0

    def process_rainfall_data(
        self,
        file_path: Path,
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> np.ndarray | None:
        """Process CHIRPS GeoTIFF file and extract rainfall data.

        Args:
            file_path: Path to CHIRPS GeoTIFF file
            area_bounds: Geographic bounds (W, S, E, N) to extract

        Returns:
            Numpy array with rainfall data or None if processing failed
        """
        try:
            import rasterio
            from rasterio.windows import from_bounds

            bounds = area_bounds or (-20.0, -35.0, 55.0, 40.0)  # Default Africa bounds

            with rasterio.open(file_path) as src:
                # Get window for specified bounds
                window = from_bounds(
                    bounds[0], bounds[1], bounds[2], bounds[3], transform=src.transform
                )

                # Read data for the window
                rainfall_data = src.read(1, window=window)

                # Handle no-data values (CHIRPS uses -9999)
                rainfall_data = rainfall_data.astype(np.float32)
                rainfall_data[rainfall_data < 0] = np.nan

                # Get the transform and bounds for the subset
                window_transform = src.window_transform(window)

                return {
                    "data": rainfall_data,
                    "transform": window_transform,
                    "crs": src.crs,
                    "bounds": bounds,
                    "shape": rainfall_data.shape,
                }

        except ImportError:
            logger.error("rasterio package required for GeoTIFF processing")
            return None
        except Exception as e:
            logger.error(f"Failed to process rainfall data: {e}")
            return None

    def validate_rainfall_file(self, file_path: Path) -> dict[str, bool | str | float]:
        """Validate downloaded CHIRPS file.

        Args:
            file_path: Path to the CHIRPS file to validate

        Returns:
            Dict with validation results
        """
        validation_result: dict[str, Any] = {
            "file_exists": False,
            "file_size_valid": False,
            "data_accessible": False,
            "has_valid_data": False,
            "spatial_resolution_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "data_range": {},
        }

        try:
            # Check file existence
            if not file_path.exists():
                validation_result["error_message"] = "File does not exist"
                validation_result["success"] = False
                return validation_result

            validation_result["file_exists"] = True

            # Check file size (CHIRPS daily global is ~3-5 MB)
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            validation_result["file_size_valid"] = file_size_mb > 0.5

            # Try to open and validate GeoTIFF
            try:
                import rasterio

                with rasterio.open(file_path) as src:
                    validation_result["data_accessible"] = True

                    # Check data
                    data = src.read(1)
                    valid_data = data[data >= 0]  # Exclude no-data values

                    if len(valid_data) > 0:
                        validation_result["has_valid_data"] = True
                        validation_result["data_range"] = {
                            "min": float(valid_data.min()),
                            "max": float(valid_data.max()),
                            "mean": float(valid_data.mean()),
                        }

                    # Check spatial resolution (should be 0.05 degrees)
                    res = src.res
                    validation_result["spatial_resolution_valid"] = (
                        abs(res[0] - 0.05) < 0.001 and abs(res[1] - 0.05) < 0.001
                    )

            except ImportError:
                validation_result["error_message"] = (
                    "rasterio not available for validation"
                )
            except Exception as e:
                validation_result["error_message"] = f"Data validation error: {e}"

        except Exception as e:
            validation_result["error_message"] = f"File validation error: {e}"

        # Overall validation success
        validation_result["success"] = all(
            [
                validation_result["file_exists"],
                validation_result["file_size_valid"],
                validation_result["data_accessible"],
                validation_result["has_valid_data"],
                validation_result["spatial_resolution_valid"],
            ]
        )

        return validation_result

    def aggregate_to_monthly(self, daily_files: list[Path], output_path: Path) -> bool:
        """Aggregate daily CHIRPS files to monthly total.

        Args:
            daily_files: List of daily CHIRPS file paths
            output_path: Path for output monthly aggregate file

        Returns:
            True if successful, False otherwise
        """
        try:
            import rasterio

            monthly_sum = None
            profile = None
            valid_days = 0

            for file_path in sorted(daily_files):
                try:
                    with rasterio.open(file_path) as src:
                        data = src.read(1)

                        if monthly_sum is None:
                            monthly_sum = np.zeros_like(data, dtype=np.float32)
                            profile = src.profile.copy()
                            profile.update(dtype=rasterio.float32)

                        # Add daily rainfall (handling no-data)
                        valid_mask = data >= 0
                        monthly_sum[valid_mask] += data[valid_mask]
                        valid_days += 1

                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")

            if valid_days > 0 and monthly_sum is not None:
                # Write aggregated data
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(monthly_sum, 1)

                logger.info(f"Created monthly aggregate from {valid_days} daily files")
                return True
            else:
                logger.error("No valid data to aggregate")
                return False

        except Exception as e:
            logger.error(f"Failed to aggregate to monthly: {e}")
            return False

    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """Clean up old downloaded files.

        Args:
            days_to_keep: Number of days of files to retain

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for file_path in self.download_directory.glob("chirps-v2.0.*.tif"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old CHIRPS file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old CHIRPS files")
        return deleted_count

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    async def get_precipitation_data(self, *args, **kwargs):
        """Alias for download_rainfall_data for backward compatibility with tests."""
        return self.download_rainfall_data(*args, **kwargs)
