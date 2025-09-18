"""Malaria Atlas Project (MAP) Data Ingestion Client.

This module provides a client for downloading MAP (Malaria Atlas Project) data
including parasite rate surveys, incidence data, and modeled risk surfaces.
It handles both R-based access via malariaAtlas package and direct HTTP access
to MAP data repositories.

Dependencies:
- requests: HTTP client for direct data downloads
- rasterio: GeoTIFF file reading and processing
- numpy: Array operations for data processing
- rpy2: Python-R bridge for malariaAtlas package (optional)
- pathlib: File system path handling

Assumptions:
- No authentication required (open access data)
- Sufficient disk space for downloaded raster files
- Internet connectivity to MAP data servers
- R and malariaAtlas package installed (optional, falls back to HTTP)
"""

import logging
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import requests
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class MAPDataType:
    """Available MAP data types."""

    PARASITE_RATE = "pr"  # Plasmodium falciparum parasite rate
    INCIDENCE = "incidence"  # Clinical incidence
    MORTALITY = "mortality"  # Mortality rates
    VECTOR_OCCURRENCE = "vector"  # Anopheles vector occurrence
    INTERVENTION_COVERAGE = "intervention"  # ITN, IRS coverage


class MAPRequestConfig(BaseModel):
    """Configuration for MAP data requests."""

    model_config = ConfigDict(frozen=True)

    data_type: str = Field(default="pr", description="Type of MAP data to download")
    species: str = Field(default="Pf", description="Parasite species (Pf or Pv)")
    year: int = Field(..., description="Year of data")

    # Geographic bounds (Africa focus by default)
    area_bounds: tuple[float, float, float, float] = Field(
        default=(-20.0, -35.0, 55.0, 40.0),  # West, South, East, North
        description="Geographic area bounds (W, S, E, N)",
    )

    # Age group for parasite rate
    age_range: tuple[int, int] = Field(
        default=(2, 10), description="Age range for parasite rate (min, max years)"
    )

    # Resolution for raster data
    resolution: Literal["1km", "5km"] = Field(
        default="5km", description="Spatial resolution for raster data"
    )


class MAPDownloadResult(BaseModel):
    """Result of a MAP data download operation."""

    request_id: str = Field(description="Download request identifier")
    file_paths: list[Path] = Field(description="Paths to downloaded files")
    total_size_bytes: int = Field(description="Total size of downloaded files")
    data_type: str = Field(description="Type of data downloaded")
    temporal_coverage: dict[str, Any] = Field(description="Time period covered")
    spatial_coverage: dict[str, float] = Field(description="Geographic bounds")
    download_duration_seconds: float = Field(description="Time taken for download")
    success: bool = Field(description="Whether download completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MAPClient:
    """Client for downloading Malaria Atlas Project data."""

    # MAP data repository URLs
    BASE_URL = "https://data.malariaatlas.org"
    RASTER_URL = "https://data.malariaatlas.org/rasters"
    PR_POINTS_URL = "https://malariaatlas.org/explorer-api/getPR"

    def __init__(self, settings: Settings | None = None):
        """Initialize MAP client with configuration.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.download_directory = Path(self.settings.data.directory) / "map"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "MalariaPredictorBackend/1.0 (MAP Data Client)"}
        )

        # Thread pool for parallel downloads
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Check R availability
        self._r_available = self._check_r_availability()

        logger.info(
            f"MAP client initialized with download directory: {self.download_directory}"
        )
        logger.info(f"R integration available: {self._r_available}")

    def _check_r_availability(self) -> bool:
        """Check if R and malariaAtlas package are available."""
        try:
            # Check if R is installed
            result = subprocess.run(
                ["R", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return False

            # Check if malariaAtlas package is installed
            r_check_script = """
            if (requireNamespace("malariaAtlas", quietly = TRUE)) {
                cat("OK")
            } else {
                cat("MISSING")
            }
            """

            result = subprocess.run(
                ["R", "--slave", "-e", r_check_script],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return "OK" in result.stdout

        except Exception as e:
            logger.debug(f"R availability check failed: {e}")
            return False

    def download_parasite_rate_surface(
        self,
        year: int,
        species: str = "Pf",
        age_standardized: bool = True,
        resolution: Literal["1km", "5km"] = "5km",
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> MAPDownloadResult:
        """Download MAP parasite rate surface for specified year.

        Args:
            year: Year of data to download
            species: Parasite species ("Pf" for P. falciparum, "Pv" for P. vivax)
            age_standardized: Whether to download age-standardized (2-10) data
            resolution: Spatial resolution ("1km" or "5km")
            area_bounds: Geographic bounds (W, S, E, N), defaults to Africa

        Returns:
            Download result with file paths and metadata
        """
        logger.info(
            f"Starting MAP parasite rate download: {species} {year} at {resolution}"
        )

        download_start = datetime.now()

        try:
            # Try R-based download first if available
            if self._r_available:
                result = self._download_via_r(
                    data_type="pr",
                    year=year,
                    species=species,
                    resolution=resolution,
                    area_bounds=area_bounds,
                )
                if result.success:
                    return result
                else:
                    logger.warning("R-based download failed, falling back to HTTP")

            # Fall back to HTTP download
            return self._download_via_http(
                data_type="pr",
                year=year,
                species=species,
                resolution=resolution,
                area_bounds=area_bounds or (-20.0, -35.0, 55.0, 40.0),
            )

        except Exception as e:
            logger.error(f"MAP download failed: {e}")
            return MAPDownloadResult(
                request_id="failed",
                file_paths=[],
                total_size_bytes=0,
                data_type="pr",
                temporal_coverage={"year": year},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def download_vector_occurrence_data(
        self,
        species_complex: str = "gambiae",
        start_year: int | None = None,
        end_year: int | None = None,
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> MAPDownloadResult:
        """Download Anopheles vector occurrence data.

        Args:
            species_complex: Anopheles species complex (e.g., "gambiae", "funestus")
            start_year: Start year for data (optional)
            end_year: End year for data (optional)
            area_bounds: Geographic bounds (W, S, E, N)

        Returns:
            Download result with vector occurrence data
        """
        logger.info(f"Starting MAP vector occurrence download: {species_complex}")

        download_start = datetime.now()

        try:
            if self._r_available:
                result = self._download_vector_via_r(
                    species_complex=species_complex,
                    start_year=start_year,
                    end_year=end_year,
                    area_bounds=area_bounds,
                )
                if result.success:
                    return result

            # Fall back to HTTP API
            return self._download_vector_via_http(
                species_complex=species_complex,
                start_year=start_year,
                end_year=end_year,
                area_bounds=area_bounds or (-20.0, -35.0, 55.0, 40.0),
            )

        except Exception as e:
            logger.error(f"Vector data download failed: {e}")
            return MAPDownloadResult(
                request_id="failed",
                file_paths=[],
                total_size_bytes=0,
                data_type="vector",
                temporal_coverage={"start_year": start_year, "end_year": end_year},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def download_intervention_coverage(
        self,
        intervention_type: Literal["ITN", "IRS", "ACT"],
        year: int,
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> MAPDownloadResult:
        """Download intervention coverage data (ITN, IRS, ACT).

        Args:
            intervention_type: Type of intervention
            year: Year of coverage data
            area_bounds: Geographic bounds (W, S, E, N)

        Returns:
            Download result with intervention coverage data
        """
        logger.info(f"Starting MAP intervention download: {intervention_type} {year}")

        download_start = datetime.now()

        try:
            # Map intervention types to MAP dataset names
            intervention_map = {
                "ITN": "ITN_use",
                "IRS": "IRS_coverage",
                "ACT": "ACT_coverage",
            }

            dataset_name = intervention_map.get(intervention_type)
            if not dataset_name:
                raise ValueError(f"Unknown intervention type: {intervention_type}")

            return self._download_via_http(
                data_type="intervention",
                year=year,
                dataset_name=dataset_name,
                area_bounds=area_bounds or (-20.0, -35.0, 55.0, 40.0),
                metadata={"intervention_type": intervention_type},
            )

        except Exception as e:
            logger.error(f"Intervention data download failed: {e}")
            return MAPDownloadResult(
                request_id="failed",
                file_paths=[],
                total_size_bytes=0,
                data_type="intervention",
                temporal_coverage={"year": year},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
                metadata={"intervention_type": intervention_type},
            )

    def _download_via_r(
        self,
        data_type: str,
        year: int,
        species: str = "Pf",
        resolution: str = "5km",
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> MAPDownloadResult:
        """Download MAP data using R's malariaAtlas package."""
        download_start = datetime.now()

        try:
            # Create temporary R script
            with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False) as f:
                r_script = self._generate_r_download_script(
                    data_type=data_type,
                    year=year,
                    species=species,
                    resolution=resolution,
                    area_bounds=area_bounds,
                    output_dir=str(self.download_directory),
                )
                f.write(r_script)
                r_script_path = f.name

            # Execute R script
            result = subprocess.run(
                ["Rscript", r_script_path],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            # Clean up script
            os.unlink(r_script_path)

            if result.returncode != 0:
                logger.error(f"R script failed: {result.stderr}")
                raise RuntimeError(f"R download failed: {result.stderr}")

            # Parse output to get downloaded files
            output_lines = result.stdout.strip().split("\n")
            downloaded_files = []
            total_size = 0

            for line in output_lines:
                if line.startswith("DOWNLOADED:"):
                    file_path = Path(line.replace("DOWNLOADED:", "").strip())
                    if file_path.exists():
                        downloaded_files.append(file_path)
                        total_size += file_path.stat().st_size

            download_duration = (datetime.now() - download_start).total_seconds()

            return MAPDownloadResult(
                request_id=f"map_r_{data_type}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                data_type=data_type,
                temporal_coverage={"year": year},
                spatial_coverage=(
                    self._bounds_to_dict(area_bounds) if area_bounds else {}
                ),
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                error_message=None if downloaded_files else "No files downloaded",
            )

        except Exception as e:
            logger.error(f"R-based download failed: {e}")
            return MAPDownloadResult(
                request_id="failed_r",
                file_paths=[],
                total_size_bytes=0,
                data_type=data_type,
                temporal_coverage={"year": year},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _download_via_http(
        self,
        data_type: str,
        year: int,
        species: str = "Pf",
        resolution: str = "5km",
        dataset_name: str | None = None,
        area_bounds: tuple[float, float, float, float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MAPDownloadResult:
        """Download MAP data via direct HTTP access."""
        download_start = datetime.now()
        downloaded_files = []
        total_size = 0

        try:
            # Construct download URL based on data type
            if data_type == "pr":
                # Parasite rate surface
                filename = f"{species}_parasite_rate_{year}_{resolution}.tif"
                url = f"{self.RASTER_URL}/pr/{species}/{year}/{filename}"
            elif data_type == "intervention" and dataset_name:
                # Intervention coverage
                filename = f"{dataset_name}_{year}.tif"
                url = (
                    f"{self.RASTER_URL}/interventions/{dataset_name}/{year}/{filename}"
                )
            else:
                raise ValueError(
                    f"Unsupported data type for HTTP download: {data_type}"
                )

            output_path = self.download_directory / filename

            # Skip if already downloaded
            if output_path.exists():
                logger.info(f"File already exists, skipping: {filename}")
                downloaded_files.append(output_path)
                total_size = output_path.stat().st_size
            else:
                # Download file
                logger.info(f"Downloading: {filename} from {url}")
                response = self.session.get(url, stream=True, timeout=300)
                response.raise_for_status()

                # Save to file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                file_size = output_path.stat().st_size
                total_size += file_size
                downloaded_files.append(output_path)

                logger.info(
                    f"Downloaded successfully: {filename} ({file_size / 1024 / 1024:.2f} MB)"
                )

            # If bounds specified, crop the downloaded file
            if area_bounds and downloaded_files:
                cropped_files = []
                for file_path in downloaded_files:
                    cropped_path = self._crop_raster_to_bounds(file_path, area_bounds)
                    if cropped_path:
                        cropped_files.append(cropped_path)
                downloaded_files = cropped_files

            download_duration = (datetime.now() - download_start).total_seconds()

            return MAPDownloadResult(
                request_id=f"map_http_{data_type}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                data_type=data_type,
                temporal_coverage={"year": year},
                spatial_coverage=(
                    self._bounds_to_dict(area_bounds) if area_bounds else {}
                ),
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                error_message=None if downloaded_files else "Download failed",
                metadata=metadata or {},
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP download failed: {e}")
            return MAPDownloadResult(
                request_id="failed_http",
                file_paths=[],
                total_size_bytes=0,
                data_type=data_type,
                temporal_coverage={"year": year},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _download_vector_via_r(
        self,
        species_complex: str,
        start_year: int | None,
        end_year: int | None,
        area_bounds: tuple[float, float, float, float] | None,
    ) -> MAPDownloadResult:
        """Download vector occurrence data using R."""
        download_start = datetime.now()

        try:
            # Create R script for vector data download
            with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False) as f:
                r_script = f"""
library(malariaAtlas)

# Set bounds if provided
if (!is.null(c{area_bounds})) {{
    extent <- list(
        xmin = {area_bounds[0] if area_bounds else "NULL"},
        ymin = {area_bounds[1] if area_bounds else "NULL"},
        xmax = {area_bounds[2] if area_bounds else "NULL"},
        ymax = {area_bounds[3] if area_bounds else "NULL"}
    )
}} else {{
    extent <- NULL
}}

# Download vector occurrence data
vector_data <- getVecOcc(
    species = "{species_complex}",
    extent = extent
)

# Save as CSV
output_file <- file.path("{self.download_directory}",
                        paste0("vector_", "{species_complex}", "_occurrence.csv"))
write.csv(vector_data, output_file, row.names = FALSE)

cat("DOWNLOADED:", output_file, "\\n")
"""
                f.write(r_script)
                r_script_path = f.name

            # Execute R script
            result = subprocess.run(
                ["Rscript", r_script_path], capture_output=True, text=True, timeout=300
            )

            os.unlink(r_script_path)

            if result.returncode != 0:
                raise RuntimeError(f"R vector download failed: {result.stderr}")

            # Parse output
            downloaded_files = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith("DOWNLOADED:"):
                    file_path = Path(line.replace("DOWNLOADED:", "").strip())
                    if file_path.exists():
                        downloaded_files.append(file_path)

            total_size = sum(f.stat().st_size for f in downloaded_files)
            download_duration = (datetime.now() - download_start).total_seconds()

            return MAPDownloadResult(
                request_id=f"map_vector_{species_complex}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                data_type="vector",
                temporal_coverage={"start_year": start_year, "end_year": end_year},
                spatial_coverage=(
                    self._bounds_to_dict(area_bounds) if area_bounds else {}
                ),
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                error_message=None,
                metadata={"species_complex": species_complex},
            )

        except Exception as e:
            logger.error(f"R vector download failed: {e}")
            return MAPDownloadResult(
                request_id="failed_vector_r",
                file_paths=[],
                total_size_bytes=0,
                data_type="vector",
                temporal_coverage={},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _download_vector_via_http(
        self,
        species_complex: str,
        start_year: int | None,
        end_year: int | None,
        area_bounds: tuple[float, float, float, float],
    ) -> MAPDownloadResult:
        """Download vector data via HTTP API."""
        download_start = datetime.now()

        try:
            # Prepare API request
            params = {"species": species_complex, "format": "csv"}

            if start_year:
                params["year_start"] = start_year
            if end_year:
                params["year_end"] = end_year

            # Add bounds
            params["bbox"] = (
                f"{area_bounds[0]},{area_bounds[1]},{area_bounds[2]},{area_bounds[3]}"
            )

            # Make API request
            response = self.session.get(
                f"{self.BASE_URL}/api/vector_occurrence", params=params, timeout=120
            )
            response.raise_for_status()

            # Save response
            output_file = (
                self.download_directory / f"vector_{species_complex}_occurrence.csv"
            )
            with open(output_file, "w") as f:
                f.write(response.text)

            file_size = output_file.stat().st_size
            download_duration = (datetime.now() - download_start).total_seconds()

            return MAPDownloadResult(
                request_id=f"map_vector_http_{datetime.now().isoformat()}",
                file_paths=[output_file],
                total_size_bytes=file_size,
                data_type="vector",
                temporal_coverage={"start_year": start_year, "end_year": end_year},
                spatial_coverage=self._bounds_to_dict(area_bounds),
                download_duration_seconds=download_duration,
                success=True,
                error_message=None,
                metadata={"species_complex": species_complex},
            )

        except Exception as e:
            logger.error(f"HTTP vector download failed: {e}")
            return MAPDownloadResult(
                request_id="failed_vector_http",
                file_paths=[],
                total_size_bytes=0,
                data_type="vector",
                temporal_coverage={},
                spatial_coverage={},
                download_duration_seconds=(
                    datetime.now() - download_start
                ).total_seconds(),
                success=False,
                error_message=str(e),
            )

    def _generate_r_download_script(
        self,
        data_type: str,
        year: int,
        species: str,
        resolution: str,
        area_bounds: tuple[float, float, float, float] | None,
        output_dir: str,
    ) -> str:
        """Generate R script for downloading MAP data."""

        # Convert Python resolution to MAP surface name
        surface_map = {
            "pr": {
                "5km": f"Plasmodium falciparum PR2-10 {year}",
                "1km": f"Plasmodium falciparum PR2-10 {year} 1km",
            }
        }

        surface_name = surface_map.get(data_type, {}).get(resolution, "")

        script = f"""
library(malariaAtlas)

# List available rasters (for debugging)
available_rasters <- listRaster()
print(head(available_rasters))

# Set output directory
output_dir <- "{output_dir}"

# Download raster
tryCatch({{
    raster_data <- getRaster(
        surface = "{surface_name}",
        shp = NULL,
        file_path = output_dir
    )

    # Get the downloaded file path
    files <- list.files(output_dir, pattern = "*.tif", full.names = TRUE)
    latest_file <- files[order(file.info(files)$mtime, decreasing = TRUE)][1]

    cat("DOWNLOADED:", latest_file, "\\n")

}}, error = function(e) {{
    cat("ERROR:", conditionMessage(e), "\\n")
    quit(status = 1)
}})
"""

        return script

    def _crop_raster_to_bounds(
        self, input_path: Path, bounds: tuple[float, float, float, float]
    ) -> Path | None:
        """Crop a raster file to specified bounds."""
        try:
            import rasterio
            from rasterio.mask import mask
            from shapely.geometry import box

            # Create output filename
            output_path = (
                input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
            )

            with rasterio.open(input_path) as src:
                # Create bounding box geometry
                bbox = box(bounds[0], bounds[1], bounds[2], bounds[3])

                # Crop raster
                out_image, out_transform = mask(src, [bbox], crop=True)
                out_meta = src.meta.copy()

                # Update metadata
                out_meta.update(
                    {
                        "driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                    }
                )

                # Write cropped raster
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)

            # Remove original and keep cropped
            input_path.unlink()

            logger.info(f"Cropped raster to bounds: {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to crop raster: {e}")
            return None

    def _bounds_to_dict(
        self, bounds: tuple[float, float, float, float]
    ) -> dict[str, float]:
        """Convert bounds tuple to dictionary."""
        return {
            "west": bounds[0],
            "south": bounds[1],
            "east": bounds[2],
            "north": bounds[3],
        }

    def validate_raster_file(self, file_path: Path) -> dict[str, Any]:
        """Validate downloaded MAP raster file.

        Args:
            file_path: Path to the raster file to validate

        Returns:
            Dict with validation results
        """
        validation_result = {
            "file_exists": False,
            "file_size_valid": False,
            "data_accessible": False,
            "has_valid_data": False,
            "spatial_resolution_valid": False,
            "crs_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "data_range": {},
            "resolution": None,
            "crs": None,
        }

        try:
            # Check file existence
            if not file_path.exists():
                validation_result["error_message"] = "File does not exist"
                validation_result["success"] = False
                return validation_result

            validation_result["file_exists"] = True

            # Check file size
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            validation_result["file_size_valid"] = file_size_mb > 0.1

            # Try to open and validate raster
            try:
                import rasterio

                with rasterio.open(file_path) as src:
                    validation_result["data_accessible"] = True

                    # Check data
                    data = src.read(1)
                    valid_data = data[~np.isnan(data)]

                    if len(valid_data) > 0:
                        validation_result["has_valid_data"] = True
                        validation_result["data_range"] = {
                            "min": float(valid_data.min()),
                            "max": float(valid_data.max()),
                            "mean": float(valid_data.mean()),
                            "std": float(valid_data.std()),
                        }

                    # Check resolution
                    res = src.res
                    validation_result["resolution"] = (res[0], res[1])

                    # For 5km data, expect ~0.05 degree resolution
                    # For 1km data, expect ~0.01 degree resolution
                    if abs(res[0] - 0.05) < 0.01 or abs(res[0] - 0.01) < 0.001:
                        validation_result["spatial_resolution_valid"] = True

                    # Check CRS (should be WGS84)
                    validation_result["crs"] = str(src.crs)
                    validation_result["crs_valid"] = src.crs.to_epsg() == 4326

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
                validation_result["crs_valid"],
            ]
        )

        return validation_result

    def process_parasite_rate_data(
        self, file_path: Path, output_format: Literal["array", "dataframe"] = "array"
    ) -> np.ndarray | Any | None:
        """Process MAP parasite rate raster data.

        Args:
            file_path: Path to MAP raster file
            output_format: Output format ("array" or "dataframe")

        Returns:
            Processed data as numpy array or pandas DataFrame
        """
        try:
            import rasterio

            with rasterio.open(file_path) as src:
                # Read data
                pr_data = src.read(1)

                # Handle no-data values
                pr_data = pr_data.astype(np.float32)
                pr_data[pr_data < 0] = np.nan

                # Convert to percentage
                pr_data = pr_data * 100  # MAP stores as fraction

                if output_format == "array":
                    return pr_data

                elif output_format == "dataframe":
                    try:
                        import pandas as pd
                        from rasterio.transform import xy

                        # Get coordinates
                        rows, cols = np.meshgrid(
                            np.arange(src.height), np.arange(src.width), indexing="ij"
                        )

                        # Convert to lat/lon
                        lons, lats = xy(src.transform, rows.flatten(), cols.flatten())

                        # Create DataFrame
                        df = pd.DataFrame(
                            {
                                "latitude": lats,
                                "longitude": lons,
                                "parasite_rate": pr_data.flatten(),
                            }
                        )

                        # Remove NaN values
                        df = df.dropna(subset=["parasite_rate"])

                        return df

                    except ImportError:
                        logger.error("pandas required for dataframe output")
                        return None

        except ImportError:
            logger.error("rasterio required for processing raster data")
            return None
        except Exception as e:
            logger.error(f"Failed to process parasite rate data: {e}")
            return None

    def cleanup_old_files(self, days_to_keep: int = 90) -> int:
        """Clean up old downloaded files.

        Args:
            days_to_keep: Number of days of files to retain

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for file_path in self.download_directory.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old MAP file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old MAP files")
        return deleted_count

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    async def get_malaria_data(self, *args, **kwargs):
        """Alias for download_parasite_rate_surface for backward compatibility with tests."""
        return self.download_parasite_rate_surface(*args, **kwargs)
