"""WorldPop Population Data Integration Client.

This module provides a client for downloading and processing WorldPop population
data including population density, age/sex structure, and population-at-risk
calculations using malaria risk surfaces.

WorldPop provides global population datasets at multiple resolutions (100m, 1km)
with temporal coverage from 2000-2030. The data is available via secure HTTPS REST API.

Dependencies:
- requests: HTTP client for API access and data downloads
- rasterio: GeoTIFF file reading and processing
- numpy: Array operations for population calculations
- pathlib: File system path handling

Assumptions:
- No authentication required (open access data)
- Sufficient disk space for population raster files
- Internet connectivity to WorldPop servers

SECURITY NOTE:
    FTP support has been removed due to security concerns (unencrypted transmission).
    All downloads now use HTTPS REST API exclusively.
"""

# Removed insecure FTP support - use HTTPS REST API instead
# import ftplib  # SECURITY: FTP is insecure (unencrypted), removed
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class WorldPopRequestConfig(BaseModel):
    """Configuration for WorldPop data requests."""

    model_config = ConfigDict(frozen=True)

    # Data type configuration
    data_type: str = Field(
        default="population_density",
        description="Type of population data (population_density, age_sex_structure, unconstrained)",
    )
    resolution: str = Field(
        default="100m", description="Spatial resolution (100m, 1km)"
    )
    format_type: str = Field(default="tif", description="Output format")

    # Geographic bounds (Africa focus by default)
    area_bounds: tuple[float, float, float, float] = Field(
        default=(-20.0, -35.0, 55.0, 40.0),  # West, South, East, North
        description="Geographic area bounds (W, S, E, N)",
    )
    country_codes: list[str] | None = Field(
        default=None, description="ISO3 country codes for specific countries"
    )

    # Temporal configuration
    target_year: int = Field(
        default=2020, description="Target year for population data"
    )
    age_groups: list[str] | None = Field(
        default=None,
        description="Age groups for age-specific data (e.g., ['0', '1', '5'])",
    )
    sex: str | None = Field(
        default=None,
        description="Sex for demographic data ('m', 'f', or None for both)",
    )


class WorldPopDownloadResult(BaseModel):
    """Result of a WorldPop data download operation."""

    request_id: str = Field(description="Download request identifier")
    file_paths: list[Path] = Field(description="Paths to downloaded files")
    total_size_bytes: int = Field(description="Total size of downloaded files")
    data_type: str = Field(description="Type of population data downloaded")
    resolution: str = Field(description="Spatial resolution of data")
    temporal_coverage: dict[str, str | int] = Field(
        description="Year and date information"
    )
    download_duration_seconds: float = Field(description="Time taken for download")
    success: bool = Field(description="Whether download completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    files_processed: int = Field(default=0, description="Number of files processed")
    metadata: dict[str, str | float | int] = Field(
        default_factory=dict, description="Additional metadata about the datasets"
    )


class PopulationAtRiskResult(BaseModel):
    """Result of population-at-risk calculation."""

    total_population: float = Field(description="Total population in area")
    population_at_risk: float = Field(description="Population at malaria risk")
    risk_percentage: float = Field(description="Percentage of population at risk")
    high_risk_population: float = Field(description="Population in high-risk areas")
    children_under_5_at_risk: float = Field(
        description="Children under 5 at malaria risk"
    )
    geographic_bounds: tuple[float, float, float, float] = Field(
        description="Area bounds analyzed"
    )
    calculation_metadata: dict[str, str | float] = Field(
        default_factory=dict, description="Metadata about the calculation"
    )


class WorldPopClient:
    """Client for downloading and processing WorldPop population data."""

    # WorldPop API endpoints (HTTPS only for security)
    BASE_API_URL = "https://www.worldpop.org/rest/data"
    REST_BASE_URL = "https://data.worldpop.org"
    # FTP_BASE_URL removed - SECURITY: FTP is insecure (unencrypted)

    # Common data paths and patterns
    POPULATION_DATASETS = {
        "population_density": "pop",
        "age_sex_structure": "age_sex",
        "unconstrained": "wpgp",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize WorldPop client with configuration.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.download_directory = Path(self.settings.data.directory) / "worldpop"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different data types
        for data_type in self.POPULATION_DATASETS.keys():
            (self.download_directory / data_type).mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "MalariaPredictorBackend/1.0 (WorldPop Population Client)"}
        )

        # Thread pool for parallel downloads
        self.executor = ThreadPoolExecutor(
            max_workers=3
        )  # Conservative for large files

        # Cache for dataset discovery
        self._dataset_cache = {}

        logger.info(
            f"WorldPop client initialized with download directory: {self.download_directory}"
        )

    def discover_available_datasets(
        self,
        country_codes: list[str] | None = None,
        data_type: str = "population_density",
        year: int | None = None,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Discover available WorldPop datasets.

        Args:
            country_codes: ISO3 country codes to search for
            data_type: Type of population data to discover
            year: Specific year to filter for

        Returns:
            Dictionary of available datasets by country
        """
        logger.info(f"Discovering WorldPop {data_type} datasets")

        try:
            # Use REST API to discover datasets
            api_url = f"{self.BASE_API_URL}/pop/wpgp"
            params = {"format": "json"}

            if country_codes:
                params["iso3"] = ",".join(country_codes)

            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Process and filter results
            available_datasets = {}

            for dataset in data.get("data", []):
                country = dataset.get("iso3", "unknown")
                dataset_year = dataset.get("year", 0)

                # Filter by year if specified
                if year and dataset_year != year:
                    continue

                if country not in available_datasets:
                    available_datasets[country] = []

                available_datasets[country].append(
                    {
                        "year": dataset_year,
                        "dataset_id": dataset.get("id"),
                        "title": dataset.get("title", ""),
                        "resolution": dataset.get("resolution", "unknown"),
                        "download_url": dataset.get("download_url", ""),
                        "file_size": dataset.get("file_size", 0),
                    }
                )

            # Cache results
            cache_key = f"{data_type}_{country_codes}_{year}"
            self._dataset_cache[cache_key] = available_datasets

            logger.info(f"Discovered datasets for {len(available_datasets)} countries")
            return available_datasets

        except Exception as e:
            logger.error(f"Failed to discover datasets: {e}")
            return {}

    def download_population_data(
        self,
        country_codes: list[str],
        target_year: int = 2020,
        data_type: str = "population_density",
        resolution: str = "100m",
        use_ftp: bool = False,  # DEPRECATED: Ignored for security, always uses HTTPS
    ) -> WorldPopDownloadResult:
        """Download WorldPop population data for specified countries.

        Args:
            country_codes: List of ISO3 country codes
            target_year: Year for population data
            data_type: Type of population data to download
            resolution: Spatial resolution of data
            use_ftp: DEPRECATED. Ignored for security. All downloads use HTTPS.

        Returns:
            Download result with file paths and metadata

        Security:
            FTP support has been removed. All downloads use secure HTTPS REST API.
        """
        if use_ftp:
            logger.warning(
                "FTP download deprecated for security (unencrypted transmission). "
                "Using secure HTTPS REST API instead."
            )
        logger.info(
            f"Starting WorldPop {data_type} download for {country_codes}, year {target_year}"
        )

        download_start = datetime.now()
        downloaded_files = []
        total_size = 0
        metadata = {}

        try:
            # First discover available datasets
            available_datasets = self.discover_available_datasets(
                country_codes=country_codes, data_type=data_type, year=target_year
            )

            if not available_datasets:
                raise ValueError(
                    f"No datasets found for {country_codes} in {target_year}"
                )

            # Download files for each country
            download_tasks = []

            for country_code in country_codes:
                if country_code not in available_datasets:
                    logger.warning(f"No data available for {country_code}")
                    continue

                for dataset in available_datasets[country_code]:
                    # Always use secure HTTPS REST API (FTP deprecated for security)
                    task = self.executor.submit(
                        self._download_via_rest,
                        country_code,
                        dataset,
                        data_type,
                        resolution,
                    )
                    download_tasks.append(task)

            # Wait for downloads to complete
            for future in as_completed(download_tasks):
                try:
                    file_path, file_size, file_metadata = future.result()
                    if file_path:
                        downloaded_files.append(file_path)
                        total_size += file_size
                        metadata.update(file_metadata)
                except Exception as e:
                    logger.error(f"Download task failed: {e}")

            download_duration = (datetime.now() - download_start).total_seconds()

            return WorldPopDownloadResult(
                request_id=f"worldpop_{data_type}_{target_year}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                data_type=data_type,
                resolution=resolution,
                temporal_coverage={
                    "target_year": target_year,
                    "download_date": datetime.now().isoformat(),
                },
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                files_processed=len(downloaded_files),
                error_message=None if downloaded_files else "No files downloaded",
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"WorldPop download failed: {e}")
            return WorldPopDownloadResult(
                request_id="failed",
                file_paths=[],
                total_size_bytes=0,
                data_type=data_type,
                resolution=resolution,
                temporal_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
                files_processed=0,
            )

    def _download_via_rest(
        self,
        country_code: str,
        dataset: dict[str, str | int],
        data_type: str,
        resolution: str,
    ) -> tuple[Path | None, int, dict[str, str | float]]:
        """Download single file via REST API.

        Returns:
            Tuple of (file_path, file_size, metadata) or (None, 0, {}) if failed
        """
        try:
            download_url = dataset.get("download_url", "")
            if not download_url:
                # Construct URL from dataset information
                year = dataset.get("year", 2020)

                # Build URL based on WorldPop naming conventions
                filename = f"{country_code.lower()}_{data_type}_{year}_{resolution}.tif"
                download_url = f"{self.REST_BASE_URL}/GIS/Population/Global_2000_2020/{year}/{resolution}/{filename}"

            # Extract filename from URL
            parsed_url = urlparse(download_url)
            filename = (
                Path(parsed_url.path).name
                or f"{country_code}_{data_type}_{dataset.get('year', 2020)}.tif"
            )

            output_path = self.download_directory / data_type / filename

            # Skip if already downloaded
            if output_path.exists():
                logger.info(f"File already exists, skipping: {filename}")
                return output_path, output_path.stat().st_size, {"cached": True}

            # Download file
            logger.info(f"Downloading {country_code} population data: {filename}")
            response = self.session.get(download_url, stream=True, timeout=600)
            response.raise_for_status()

            # Save to file with progress logging
            file_size = 0
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)

            logger.info(
                f"Downloaded successfully: {filename} ({file_size / 1024 / 1024:.2f} MB)"
            )

            # Extract metadata
            metadata = {
                "country_code": country_code,
                "dataset_id": dataset.get("dataset_id", ""),
                "year": dataset.get("year", 0),
                "original_url": download_url,
                "cached": False,
            }

            return output_path, file_size, metadata

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {country_code} via REST: {e}")
            return None, 0, {}
        except Exception as e:
            logger.error(f"Unexpected error downloading {country_code}: {e}")
            return None, 0, {}

    def _download_via_ftp(
        self,
        country_code: str,
        dataset: dict[str, str | int],
        data_type: str,
        resolution: str,
    ) -> tuple[Path | None, int, dict[str, str | float]]:
        """DEPRECATED: FTP download method removed for security.

        SECURITY: This method has been deprecated and disabled due to security concerns.
        FTP transmits data unencrypted, making it vulnerable to interception.
        Use _download_via_rest() instead, which uses secure HTTPS.

        Raises:
            NotImplementedError: Always raised - FTP support removed for security

        Returns:
            Never returns - always raises NotImplementedError
        """
        logger.error(
            "FTP download method called but has been removed for security. "
            "FTP transmits data unencrypted. Use HTTPS REST API instead."
        )
        raise NotImplementedError(
            "FTP download has been removed for security reasons. "
            "FTP is insecure (unencrypted transmission). "
            "All downloads now use secure HTTPS REST API. "
            "Update your code to use download_population_data() without use_ftp parameter."
        )

    def extract_population_for_region(
        self,
        file_path: Path,
        area_bounds: tuple[float, float, float, float],
        age_filter: str | None = None,
    ) -> dict[str, np.ndarray | dict[str, float]] | None:
        """Extract population data for specific geographic region.

        Args:
            file_path: Path to WorldPop GeoTIFF file
            area_bounds: Geographic bounds (W, S, E, N) to extract
            age_filter: Optional age group filter for age-specific data

        Returns:
            Dictionary with population data and metadata or None if failed
        """
        try:
            import rasterio
            from rasterio.windows import from_bounds

            logger.info(f"Extracting population data from {file_path.name}")

            with rasterio.open(file_path) as src:
                # Get window for specified bounds
                window = from_bounds(
                    area_bounds[0],
                    area_bounds[1],
                    area_bounds[2],
                    area_bounds[3],
                    transform=src.transform,
                )

                # Read population data for the window
                population_data = src.read(1, window=window)

                # Handle no-data values (WorldPop typically uses 0 or negative values)
                population_data = population_data.astype(np.float32)

                # WorldPop no-data handling (values < 0 are typically no-data)
                valid_mask = population_data >= 0
                population_data[~valid_mask] = np.nan

                # Calculate population statistics
                valid_population = population_data[valid_mask]

                stats = {
                    "total_population": (
                        float(np.sum(valid_population))
                        if len(valid_population) > 0
                        else 0.0
                    ),
                    "mean_density": (
                        float(np.mean(valid_population))
                        if len(valid_population) > 0
                        else 0.0
                    ),
                    "max_density": (
                        float(np.max(valid_population))
                        if len(valid_population) > 0
                        else 0.0
                    ),
                    "valid_pixels": int(np.sum(valid_mask)),
                    "total_pixels": int(population_data.size),
                    "coverage_ratio": float(np.sum(valid_mask) / population_data.size),
                }

                # Get the transform and bounds for the subset
                window_transform = src.window_transform(window)

                return {
                    "data": population_data,
                    "transform": window_transform,
                    "crs": src.crs,
                    "bounds": area_bounds,
                    "shape": population_data.shape,
                    "statistics": stats,
                    "metadata": {
                        "source_file": str(file_path),
                        "age_filter": age_filter,
                        "extraction_date": datetime.now().isoformat(),
                    },
                }

        except ImportError:
            logger.error("rasterio package required for GeoTIFF processing")
            return None
        except Exception as e:
            logger.error(f"Failed to extract population data: {e}")
            return None

    def calculate_population_at_risk(
        self,
        population_file: Path,
        malaria_risk_file: Path,
        area_bounds: tuple[float, float, float, float],
        risk_threshold: float = 0.1,
    ) -> PopulationAtRiskResult | None:
        """Calculate population at malaria risk using risk surfaces.

        Args:
            population_file: Path to WorldPop population density file
            malaria_risk_file: Path to malaria risk surface file
            area_bounds: Geographic bounds (W, S, E, N) to analyze
            risk_threshold: Minimum risk level to consider "at risk"

        Returns:
            Population-at-risk calculation results or None if failed
        """
        try:
            import rasterio
            from rasterio.warp import Resampling, reproject
            from rasterio.windows import from_bounds

            logger.info("Calculating population at malaria risk")

            # Extract population data
            pop_data = self.extract_population_for_region(population_file, area_bounds)
            if not pop_data:
                raise ValueError("Failed to extract population data")

            # Read malaria risk data
            with rasterio.open(malaria_risk_file) as risk_src:
                risk_window = from_bounds(
                    area_bounds[0],
                    area_bounds[1],
                    area_bounds[2],
                    area_bounds[3],
                    transform=risk_src.transform,
                )
                risk_data = risk_src.read(1, window=risk_window).astype(np.float32)
                risk_transform = risk_src.window_transform(risk_window)

            # Ensure both datasets have same dimensions and alignment
            population_array = pop_data["data"]

            # If dimensions don't match, resample risk data to population grid
            if risk_data.shape != population_array.shape:
                logger.info("Resampling risk data to match population grid")

                # Create destination array
                risk_resampled = np.zeros_like(population_array)

                # Reproject risk data to match population data
                reproject(
                    source=risk_data,
                    destination=risk_resampled,
                    src_transform=risk_transform,
                    src_crs=risk_src.crs,
                    dst_transform=pop_data["transform"],
                    dst_crs=pop_data["crs"],
                    resampling=Resampling.bilinear,
                )

                risk_data = risk_resampled

            # Calculate population at risk
            valid_pop_mask = ~np.isnan(population_array) & (population_array >= 0)
            valid_risk_mask = ~np.isnan(risk_data) & (risk_data >= 0)
            valid_mask = valid_pop_mask & valid_risk_mask

            # Apply risk threshold
            at_risk_mask = valid_mask & (risk_data >= risk_threshold)
            high_risk_mask = valid_mask & (
                risk_data >= risk_threshold * 2
            )  # High risk = 2x threshold

            # Calculate totals
            total_population = float(np.sum(population_array[valid_mask]))
            population_at_risk = float(np.sum(population_array[at_risk_mask]))
            high_risk_population = float(np.sum(population_array[high_risk_mask]))

            # Calculate children under 5 at risk (assume 12% of population)
            children_under_5_ratio = 0.12
            children_under_5_at_risk = population_at_risk * children_under_5_ratio

            # Calculate risk percentage
            risk_percentage = (
                (population_at_risk / total_population * 100)
                if total_population > 0
                else 0.0
            )

            return PopulationAtRiskResult(
                total_population=total_population,
                population_at_risk=population_at_risk,
                risk_percentage=risk_percentage,
                high_risk_population=high_risk_population,
                children_under_5_at_risk=children_under_5_at_risk,
                geographic_bounds=area_bounds,
                calculation_metadata={
                    "risk_threshold": risk_threshold,
                    "children_under_5_ratio": children_under_5_ratio,
                    "valid_pixels": int(np.sum(valid_mask)),
                    "at_risk_pixels": int(np.sum(at_risk_mask)),
                    "calculation_date": datetime.now().isoformat(),
                    "population_file": str(population_file),
                    "risk_file": str(malaria_risk_file),
                },
            )

        except Exception as e:
            logger.error(f"Failed to calculate population at risk: {e}")
            return None

    def get_age_specific_population(
        self,
        country_codes: list[str],
        target_year: int = 2020,
        age_groups: list[str] = None,
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> dict[str, dict[str, float]]:
        """Get age-specific population data for specified countries.

        Args:
            country_codes: List of ISO3 country codes
            target_year: Year for population data
            age_groups: List of age groups (e.g., ['0', '1', '5'])
            area_bounds: Optional geographic bounds to extract

        Returns:
            Dictionary of age-specific population by country and age group
        """
        if age_groups is None:
            age_groups = ["0", "1", "5"]  # Children under 5 focus

        logger.info(f"Retrieving age-specific population for {country_codes}")

        results = {}

        for country_code in country_codes:
            country_results = {}

            for age_group in age_groups:
                try:
                    # Download age-specific data
                    download_result = self.download_population_data(
                        country_codes=[country_code],
                        target_year=target_year,
                        data_type="age_sex_structure",
                        resolution="1km",  # Age data typically at 1km resolution
                    )

                    if download_result.success and download_result.file_paths:
                        # Find file for specific age group
                        age_file = None
                        for file_path in download_result.file_paths:
                            if f"_age_{age_group}_" in file_path.name:
                                age_file = file_path
                                break

                        if age_file:
                            # Extract population for age group
                            bounds = area_bounds or (
                                -180,
                                -90,
                                180,
                                90,
                            )  # World bounds if not specified
                            pop_data = self.extract_population_for_region(
                                age_file, bounds, age_group
                            )

                            if pop_data:
                                country_results[f"age_{age_group}"] = pop_data[
                                    "statistics"
                                ]["total_population"]
                            else:
                                country_results[f"age_{age_group}"] = 0.0
                        else:
                            logger.warning(
                                f"No age {age_group} file found for {country_code}"
                            )
                            country_results[f"age_{age_group}"] = 0.0

                except Exception as e:
                    logger.error(
                        f"Failed to get age {age_group} data for {country_code}: {e}"
                    )
                    country_results[f"age_{age_group}"] = 0.0

            results[country_code] = country_results

        return results

    def validate_population_file(
        self, file_path: Path
    ) -> dict[str, bool | str | float]:
        """Validate downloaded WorldPop file.

        Args:
            file_path: Path to the WorldPop file to validate

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "file_exists": False,
            "file_size_valid": False,
            "data_accessible": False,
            "has_valid_population": False,
            "spatial_resolution_valid": False,
            "coordinate_system_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "population_stats": {},
            "success": False,
        }

        try:
            # Check file existence
            if not file_path.exists():
                validation_result["error_message"] = "File does not exist"
                return validation_result

            validation_result["file_exists"] = True

            # Check file size (WorldPop files are typically 10-500 MB)
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            validation_result["file_size_valid"] = file_size_mb > 1.0  # At least 1MB

            # Try to open and validate GeoTIFF
            try:
                import rasterio

                with rasterio.open(file_path) as src:
                    validation_result["data_accessible"] = True

                    # Check coordinate system
                    if src.crs and src.crs.is_geographic:
                        validation_result["coordinate_system_valid"] = True

                    # Check population data
                    data = src.read(1)
                    valid_data = data[data >= 0]  # Population should be non-negative

                    if len(valid_data) > 0:
                        validation_result["has_valid_population"] = True
                        validation_result["population_stats"] = {
                            "total_population": float(np.sum(valid_data)),
                            "max_density": float(valid_data.max()),
                            "mean_density": float(valid_data.mean()),
                            "valid_pixels": int(len(valid_data)),
                            "total_pixels": int(data.size),
                        }

                    # Check spatial resolution (WorldPop is typically 100m or 1km)
                    res = abs(src.res[0])  # Get pixel size in degrees
                    expected_resolutions = [
                        0.0008333,  # ~100m at equator
                        0.008333,  # ~1km at equator
                    ]

                    validation_result["spatial_resolution_valid"] = any(
                        abs(res - expected) < 0.0001
                        for expected in expected_resolutions
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
                validation_result["has_valid_population"],
                validation_result["coordinate_system_valid"],
            ]
        )

        return validation_result

    def cleanup_old_files(self, days_to_keep: int = 90) -> int:
        """Clean up old downloaded files.

        Args:
            days_to_keep: Number of days of files to retain

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for data_type_dir in self.download_directory.iterdir():
            if data_type_dir.is_dir():
                for file_path in data_type_dir.glob("*.tif"):
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            logger.info(f"Deleted old WorldPop file: {file_path.name}")
                        except Exception as e:
                            logger.error(f"Failed to delete file {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old WorldPop files")
        return deleted_count

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    async def get_population_data(self, *args, **kwargs):
        """Alias for download_population_data for backward compatibility with tests."""
        return self.download_population_data(*args, **kwargs)
