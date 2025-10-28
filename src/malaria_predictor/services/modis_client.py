"""MODIS Vegetation Indices Data Ingestion Client.

This module provides a client for downloading MODIS vegetation indices data
(MOD13Q1/MYD13Q1) from NASA EarthData. It handles NASA EarthData authentication,
MODIS tile discovery, data download, quality filtering, and vegetation index
processing for malaria prediction applications.

Dependencies:
- requests: HTTP client for NASA EarthData API
- rasterio: Reading HDF4 and GeoTIFF files
- pyproj: Coordinate transformation (Sinusoidal to WGS84)
- numpy: Array operations for data processing
- h5py: HDF file reading capabilities

Key Features:
- NASA EarthData authentication (EDL credentials)
- Automated MODIS tile discovery for geographic regions
- NDVI/EVI processing with proper scaling and quality filtering
- 16-day composite processing pipeline
- Sinusoidal projection handling and coordinate transformation
- Temporal aggregation (monthly, seasonal averages)
- Cloud masking and quality assessment using VI Quality flags

Assumptions:
- NASA EarthData account with valid credentials
- Sufficient disk space for MODIS HDF files (~2-5MB per tile per date)
- Internet connectivity to NASA EarthData servers
- MODIS data availability (Terra: 2000+, Aqua: 2002+)
"""

import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import requests
from pydantic import BaseModel, ConfigDict, Field

from ..config import Settings

logger = logging.getLogger(__name__)


class MODISRequestConfig(BaseModel):
    """Configuration for MODIS vegetation indices data requests."""

    model_config = ConfigDict(frozen=True)

    # Data product configuration
    product: str = Field(
        default="MOD13Q1", description="MODIS product (MOD13Q1/MYD13Q1)"
    )
    collection: str = Field(default="061", description="MODIS collection version")

    # Vegetation indices to extract
    vegetation_indices: list[str] = Field(
        default=["NDVI", "EVI"], description="Vegetation indices to process"
    )

    # Geographic configuration
    area_bounds: tuple[float, float, float, float] = Field(
        default=(-20.0, -35.0, 55.0, 40.0),  # West, South, East, North
        description="Geographic area bounds (W, S, E, N) - Africa focus",
    )

    # Temporal configuration
    start_date: date = Field(..., description="Start date for data download")
    end_date: date = Field(..., description="End date for data download")

    # Quality filtering
    apply_quality_filter: bool = Field(
        default=True, description="Apply VI Quality flags filtering"
    )

    # Processing options
    sinusoidal_to_wgs84: bool = Field(
        default=True, description="Transform from Sinusoidal to WGS84 projection"
    )

    temporal_aggregation: str | None = Field(
        default=None,
        description="Temporal aggregation method (monthly, seasonal, none)",
    )


class MODISDownloadResult(BaseModel):
    """Result of a MODIS vegetation indices download operation."""

    request_id: str = Field(description="Download request identifier")
    file_paths: list[Path] = Field(description="Paths to downloaded MODIS files")
    total_size_bytes: int = Field(description="Total size of downloaded files")
    tiles_processed: list[str] = Field(description="MODIS tiles processed")
    temporal_coverage: dict[str, str] = Field(description="Start and end dates")
    download_duration_seconds: float = Field(description="Time taken for download")
    success: bool = Field(description="Whether download completed successfully")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    files_processed: int = Field(default=0, description="Number of files processed")
    quality_summary: dict[str, Any] = Field(
        default_factory=dict, description="Quality assessment summary"
    )


class MODISProcessingResult(BaseModel):
    """Result of MODIS vegetation indices processing."""

    file_path: Path = Field(description="Path to processed file")
    vegetation_index: str = Field(description="VI type (NDVI/EVI)")
    data_shape: tuple[int, int] = Field(description="Spatial dimensions")
    valid_pixel_count: int = Field(description="Number of valid pixels")
    statistics: dict[str, float] = Field(description="VI statistics")
    temporal_info: dict[str, str] = Field(description="Temporal metadata")
    quality_flags: dict[str, int] = Field(description="Quality flag counts")
    success: bool = Field(description="Processing success status")
    error_message: str | None = Field(default=None, description="Error details")


class MODISTileInfo(BaseModel):
    """Information about a MODIS tile."""

    horizontal: int = Field(description="Horizontal tile index")
    vertical: int = Field(description="Vertical tile index")
    tile_id: str = Field(description="Full tile identifier (e.g., h21v08)")
    center_lat: float = Field(description="Tile center latitude")
    center_lon: float = Field(description="Tile center longitude")
    bounds: tuple[float, float, float, float] = Field(
        description="Tile bounds (west, south, east, north)"
    )


class MODISClient:
    """Client for downloading and processing MODIS vegetation indices data."""

    # NASA EarthData endpoints
    EARTHDATA_LOGIN_URL = "https://urs.earthdata.nasa.gov"
    MODIS_DATA_URL = "https://e4ftl01.cr.usgs.gov"
    LAADS_SEARCH_URL = "https://ladsweb.modaps.eosdis.nasa.gov/search/order"

    # MODIS products and collections
    SUPPORTED_PRODUCTS = ["MOD13Q1", "MYD13Q1"]  # Terra and Aqua VI products
    SUPPORTED_COLLECTIONS = ["061", "006"]  # Collection 6.1 and 6.0

    # MODIS VI Quality bit flags
    VI_QUALITY_FLAGS = {
        "good_quality": 0x0000,
        "marginal_quality": 0x0001,
        "snow_ice": 0x0002,
        "cloudy": 0x0003,
    }

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize MODIS client with configuration.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.download_directory = Path(self.settings.data.directory) / "modis"
        self.download_directory.mkdir(parents=True, exist_ok=True)

        # Authentication session
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "MalariaPredictorBackend/1.0 (MODIS VI Client)"}
        )

        # Authentication status
        self._authenticated = False
        self._auth_token = None

        # Thread pool for parallel downloads
        self.executor = ThreadPoolExecutor(max_workers=4)

        # MODIS tile grid information (cached)
        self._tile_grid_cache: dict[str, MODISTileInfo] = {}

        logger.info(
            f"MODIS client initialized with download directory: {self.download_directory}"
        )

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with NASA EarthData Login.

        Args:
            username: NASA EarthData username
            password: NASA EarthData password

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info("Authenticating with NASA EarthData...")

            # Login to EarthData
            login_url = f"{self.EARTHDATA_LOGIN_URL}/login"

            response = self.session.get(login_url, timeout=30)
            response.raise_for_status()

            # Submit credentials
            login_data = {"username": username, "password": password}

            response = self.session.post(login_url, data=login_data, timeout=30)
            response.raise_for_status()

            # Check if authentication was successful
            if "Invalid" in response.text or "error" in response.text.lower():
                logger.error("Invalid EarthData credentials")
                return False

            self._authenticated = True
            logger.info("EarthData authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"EarthData authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            return False

    def discover_modis_tiles(
        self, area_bounds: tuple[float, float, float, float]
    ) -> list[MODISTileInfo]:
        """Discover MODIS tiles that cover the specified geographic area.

        Args:
            area_bounds: Geographic bounds (west, south, east, north)

        Returns:
            List of MODIS tile information objects
        """
        logger.info(f"Discovering MODIS tiles for bounds: {area_bounds}")

        west, south, east, north = area_bounds
        tiles = []

        try:
            # MODIS Sinusoidal tile grid parameters
            # Each tile is approximately 1200x1200 km at the equator
            tile_size = 1111950.5197665783  # meters
            earth_radius = 6371007.181  # meters

            # Convert geographic bounds to MODIS Sinusoidal coordinates
            # Simplified conversion for tile discovery
            for h in range(36):  # 36 horizontal tiles (0-35)
                for v in range(18):  # 18 vertical tiles (0-17)
                    # Calculate tile bounds in Sinusoidal projection
                    x_min = -20015109.354 + h * tile_size
                    x_max = x_min + tile_size
                    y_max = 10007554.677 - v * tile_size
                    y_min = y_max - tile_size

                    # Approximate conversion to geographic coordinates
                    # (simplified for tile discovery - not precise)
                    center_x = (x_min + x_max) / 2
                    center_y = (y_min + y_max) / 2

                    # Convert to lat/lon (simplified)
                    center_lat = center_y / earth_radius * 180 / math.pi
                    center_lon = (
                        center_x
                        / (earth_radius * math.cos(math.radians(center_lat)))
                        * 180
                        / math.pi
                    )

                    # Rough bounds calculation
                    lat_range = tile_size / earth_radius * 180 / math.pi
                    lon_range = (
                        tile_size
                        / (earth_radius * math.cos(math.radians(center_lat)))
                        * 180
                        / math.pi
                    )

                    tile_west = center_lon - lon_range / 2
                    tile_east = center_lon + lon_range / 2
                    tile_south = center_lat - lat_range / 2
                    tile_north = center_lat + lat_range / 2

                    # Check if tile intersects with requested bounds
                    if (
                        tile_west <= east
                        and tile_east >= west
                        and tile_south <= north
                        and tile_north >= south
                    ):
                        tile_id = f"h{h:02d}v{v:02d}"

                        tile_info = MODISTileInfo(
                            horizontal=h,
                            vertical=v,
                            tile_id=tile_id,
                            center_lat=center_lat,
                            center_lon=center_lon,
                            bounds=(tile_west, tile_south, tile_east, tile_north),
                        )

                        tiles.append(tile_info)
                        self._tile_grid_cache[tile_id] = tile_info

            logger.info(f"Found {len(tiles)} MODIS tiles covering the area")
            for tile in tiles:
                logger.debug(
                    f"  Tile {tile.tile_id}: center ({tile.center_lat:.2f}, {tile.center_lon:.2f})"
                )

            return tiles

        except Exception as e:
            logger.error(f"Failed to discover MODIS tiles: {e}")
            return []

    def download_vegetation_indices(
        self,
        start_date: date,
        end_date: date,
        product: str = "MOD13Q1",
        area_bounds: tuple[float, float, float, float] | None = None,
    ) -> MODISDownloadResult:
        """Download MODIS vegetation indices data for specified period and area.

        Args:
            start_date: Start date for data download
            end_date: End date for data download
            product: MODIS product (MOD13Q1 or MYD13Q1)
            area_bounds: Geographic bounds (W, S, E, N), defaults to Africa

        Returns:
            Download result with file paths and metadata
        """
        logger.info(f"Starting MODIS {product} download: {start_date} to {end_date}")

        if not self._authenticated:
            logger.error("Not authenticated with NASA EarthData")
            return self._create_failed_result("Authentication required")

        if product not in self.SUPPORTED_PRODUCTS:
            return self._create_failed_result(f"Unsupported product: {product}")

        download_start = datetime.now()
        downloaded_files = []
        total_size = 0
        processed_tiles = []

        try:
            # Use provided bounds or default to Africa
            bounds = area_bounds or (-20.0, -35.0, 55.0, 40.0)

            # Discover relevant MODIS tiles
            tiles = self.discover_modis_tiles(bounds)
            if not tiles:
                return self._create_failed_result(
                    "No MODIS tiles found for specified area"
                )

            # Generate 16-day periods for MODIS VI products
            periods = self._generate_16day_periods(start_date, end_date)
            logger.info(
                f"Processing {len(periods)} 16-day periods across {len(tiles)} tiles"
            )

            # Download files in parallel
            futures = []
            for period_start in periods:
                for tile in tiles:
                    future = self.executor.submit(
                        self._download_single_modis_file, product, period_start, tile
                    )
                    futures.append(future)

            # Wait for downloads to complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result["success"]:
                        downloaded_files.append(result["file_path"])
                        total_size += result["file_size"]
                        if result["tile_id"] not in processed_tiles:
                            processed_tiles.append(result["tile_id"])
                except Exception as e:
                    logger.error(f"Download task failed: {e}")

            download_duration = (datetime.now() - download_start).total_seconds()

            # Generate quality summary
            quality_summary = self._generate_quality_summary(downloaded_files)

            return MODISDownloadResult(
                request_id=f"modis_{product}_{datetime.now().isoformat()}",
                file_paths=downloaded_files,
                total_size_bytes=total_size,
                tiles_processed=processed_tiles,
                temporal_coverage={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "periods": str(len(periods)),
                },
                download_duration_seconds=download_duration,
                success=len(downloaded_files) > 0,
                files_processed=len(downloaded_files),
                quality_summary=quality_summary,
                error_message=None if downloaded_files else "No files downloaded",
            )

        except Exception as e:
            logger.error(f"MODIS download failed: {e}")
            return self._create_failed_result(str(e))

    def _download_single_modis_file(
        self, product: str, period_start: date, tile: MODISTileInfo
    ) -> dict[str, Any]:
        """Download a single MODIS file.

        Returns:
            Dict with download result information
        """
        try:
            # Generate filename
            year = period_start.year
            doy = period_start.timetuple().tm_yday  # Day of year

            filename = f"{product}.A{year}{doy:03d}.{tile.tile_id}.061.hdf"

            # Build download URL
            year_str = str(year)
            url = f"{self.MODIS_DATA_URL}/MOLA/{product}.061/{year_str}.{doy:02d}.{doy // 16 + 1:02d}/{filename}"

            output_path = self.download_directory / filename

            # Skip if already downloaded
            if output_path.exists():
                logger.debug(f"File already exists, skipping: {filename}")
                return {
                    "success": True,
                    "file_path": output_path,
                    "file_size": output_path.stat().st_size,
                    "tile_id": tile.tile_id,
                    "skipped": True,
                }

            # Download file with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Downloading: {filename} (attempt {attempt + 1})")
                    response = self.session.get(url, stream=True, timeout=300)
                    response.raise_for_status()

                    # Save to file
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    file_size = output_path.stat().st_size

                    # Validate file size (MODIS files should be > 100KB)
                    if file_size < 100 * 1024:
                        logger.warning(
                            f"Downloaded file too small: {filename} ({file_size} bytes)"
                        )
                        output_path.unlink()
                        continue

                    logger.info(
                        f"Downloaded successfully: {filename} ({file_size / 1024 / 1024:.2f} MB)"
                    )

                    return {
                        "success": True,
                        "file_path": output_path,
                        "file_size": file_size,
                        "tile_id": tile.tile_id,
                        "skipped": False,
                    }

                except requests.exceptions.RequestException as e:
                    logger.warning(
                        f"Download attempt {attempt + 1} failed for {filename}: {e}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                    else:
                        return {
                            "success": False,
                            "error": f"All download attempts failed: {e}",
                            "tile_id": tile.tile_id,
                        }

        except Exception as e:
            logger.error(
                f"Unexpected error downloading {product} for {tile.tile_id}: {e}"
            )
            return {"success": False, "error": str(e), "tile_id": tile.tile_id}

    def process_vegetation_indices(
        self,
        file_path: Path,
        vegetation_indices: list[str] = None,
        apply_quality_filter: bool = True,
        output_format: str = "geotiff",
    ) -> list[MODISProcessingResult]:
        """Process MODIS HDF file and extract vegetation indices.

        Args:
            file_path: Path to MODIS HDF file
            vegetation_indices: VIs to extract (NDVI, EVI, etc.)
            apply_quality_filter: Apply VI Quality flags filtering
            output_format: Output format (geotiff, numpy, both)

        Returns:
            List of processing results for each vegetation index
        """
        if vegetation_indices is None:
            vegetation_indices = ["NDVI", "EVI"]
        logger.info(f"Processing MODIS file: {file_path.name}")

        results = []

        try:
            # Read MODIS HDF file
            import rasterio

            with rasterio.open(str(file_path)) as hdf:
                # Get available subdatasets
                subdatasets = hdf.subdatasets

                for vi in vegetation_indices:
                    try:
                        result = self._process_single_vi(
                            file_path,
                            vi,
                            apply_quality_filter,
                            output_format,
                            subdatasets,
                        )
                        results.append(result)

                    except Exception as e:
                        logger.error(
                            f"Failed to process {vi} from {file_path.name}: {e}"
                        )
                        results.append(
                            MODISProcessingResult(
                                file_path=file_path,
                                vegetation_index=vi,
                                data_shape=(0, 0),
                                valid_pixel_count=0,
                                statistics={},
                                temporal_info={},
                                quality_flags={},
                                success=False,
                                error_message=str(e),
                            )
                        )

        except ImportError:
            error_msg = "rasterio package required for MODIS HDF processing"
            logger.error(error_msg)
            for vi in vegetation_indices:
                results.append(
                    MODISProcessingResult(
                        file_path=file_path,
                        vegetation_index=vi,
                        data_shape=(0, 0),
                        valid_pixel_count=0,
                        statistics={},
                        temporal_info={},
                        quality_flags={},
                        success=False,
                        error_message=error_msg,
                    )
                )
        except Exception as e:
            error_msg = f"Failed to open MODIS file: {e}"
            logger.error(error_msg)
            for vi in vegetation_indices:
                results.append(
                    MODISProcessingResult(
                        file_path=file_path,
                        vegetation_index=vi,
                        data_shape=(0, 0),
                        valid_pixel_count=0,
                        statistics={},
                        temporal_info={},
                        quality_flags={},
                        success=False,
                        error_message=error_msg,
                    )
                )

        return results

    def _process_single_vi(
        self,
        file_path: Path,
        vi_name: str,
        apply_quality_filter: bool,
        output_format: str,
        subdatasets: list[str],
    ) -> MODISProcessingResult:
        """Process a single vegetation index from MODIS HDF."""

        import rasterio

        # Find the appropriate subdataset for the VI
        vi_dataset = None
        quality_dataset = None

        for subdataset in subdatasets:
            # Check for VI name at the end of subdataset (e.g., "250m 16 days NDVI")
            if subdataset.endswith(vi_name) or f" {vi_name}" in subdataset:
                vi_dataset = subdataset
            elif "VI_Quality" in subdataset:
                quality_dataset = subdataset

        if not vi_dataset:
            raise ValueError(f"Vegetation index {vi_name} not found in MODIS file")

        # Read VI data
        with rasterio.open(vi_dataset) as src:
            vi_data = src.read(1).astype(np.float32)
            profile = src.profile

        # Apply scaling factors for MODIS VI
        if vi_name in ["NDVI", "EVI"]:
            # MODIS VI scaling factor
            vi_data = vi_data * 0.0001  # Scale factor for MODIS VI
            vi_data = np.where(vi_data < -1, np.nan, vi_data)  # Invalid values to NaN
            vi_data = np.where(vi_data > 1, np.nan, vi_data)  # Invalid values to NaN

        # Apply quality filtering if requested
        quality_flags = {}
        if apply_quality_filter and quality_dataset:
            try:
                with rasterio.open(quality_dataset) as qsrc:
                    quality_data = qsrc.read(1)

                # Extract quality flags
                good_quality_mask = (quality_data & 0x0003) == 0  # Bits 0-1 = 00 (good)
                marginal_quality_mask = (
                    quality_data & 0x0003
                ) == 1  # Bits 0-1 = 01 (marginal)
                cloudy_mask = (
                    quality_data & 0x0003
                ) >= 2  # Bits 0-1 >= 10 (poor/cloudy)

                # Count quality flags
                quality_flags = {
                    "good_quality": int(np.sum(good_quality_mask)),
                    "marginal_quality": int(np.sum(marginal_quality_mask)),
                    "poor_cloudy": int(np.sum(cloudy_mask)),
                    "total_pixels": int(quality_data.size),
                }

                # Apply quality mask (keep only good and marginal quality)
                quality_mask = good_quality_mask | marginal_quality_mask
                vi_data = np.where(quality_mask, vi_data, np.nan)

            except Exception as e:
                logger.warning(f"Failed to apply quality filtering: {e}")
                quality_flags = {"error": "Quality filtering failed"}

        # Calculate statistics
        valid_data = vi_data[~np.isnan(vi_data)]
        valid_pixel_count = len(valid_data)

        if valid_pixel_count > 0:
            statistics = {
                "min": float(valid_data.min()),
                "max": float(valid_data.max()),
                "mean": float(valid_data.mean()),
                "std": float(valid_data.std()),
                "percentile_25": float(np.percentile(valid_data, 25)),
                "percentile_75": float(np.percentile(valid_data, 75)),
            }
        else:
            statistics = {
                "min": 0,
                "max": 0,
                "mean": 0,
                "std": 0,
                "percentile_25": 0,
                "percentile_75": 0,
            }

        # Extract temporal information from filename
        filename = file_path.name
        if filename.startswith(("MOD13Q1", "MYD13Q1")):
            parts = filename.split(".")
            if len(parts) >= 3:
                date_part = parts[1]  # e.g., A2023001
                year = int(date_part[1:5])
                doy = int(date_part[5:8])
                acquisition_date = datetime(year, 1, 1) + timedelta(days=doy - 1)

                temporal_info = {
                    "acquisition_date": acquisition_date.date().isoformat(),
                    "year": str(year),
                    "day_of_year": str(doy),
                    "product": parts[0],
                }
            else:
                temporal_info = {"error": "Could not parse temporal information"}
        else:
            temporal_info = {"error": "Unknown filename format"}

        # Save processed data if requested
        output_path = file_path
        if output_format in ["geotiff", "both"]:
            try:
                # Create output GeoTIFF
                output_dir = self.download_directory / "processed"
                output_dir.mkdir(exist_ok=True)

                output_filename = f"{file_path.stem}_{vi_name}_processed.tif"
                output_path = output_dir / output_filename

                # Update profile for output
                profile.update(
                    {"dtype": "float32", "nodata": np.nan, "compress": "lzw"}
                )

                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(vi_data, 1)

                logger.info(f"Saved processed {vi_name} to: {output_path}")

            except Exception as e:
                logger.warning(f"Failed to save processed data: {e}")

        return MODISProcessingResult(
            file_path=output_path,
            vegetation_index=vi_name,
            data_shape=vi_data.shape,
            valid_pixel_count=valid_pixel_count,
            statistics=statistics,
            temporal_info=temporal_info,
            quality_flags=quality_flags,
            success=True,
            error_message=None,
        )

    def aggregate_temporal_data(
        self,
        file_paths: list[Path],
        aggregation_method: str = "monthly",
        vegetation_index: str = "NDVI",
        output_path: Path | None = None,
    ) -> Path | None:
        """Aggregate MODIS vegetation indices temporally.

        Args:
            file_paths: List of processed MODIS files
            aggregation_method: Aggregation method (monthly, seasonal, annual)
            vegetation_index: VI to aggregate
            output_path: Path for output file

        Returns:
            Path to aggregated file or None if failed
        """
        logger.info(
            f"Aggregating {len(file_paths)} files using {aggregation_method} method"
        )

        try:
            from collections import defaultdict

            import numpy as np
            import rasterio

            # Group files by time period
            grouped_files = defaultdict(list)

            for file_path in file_paths:
                if vegetation_index not in file_path.name:
                    continue

                # Extract date from filename
                filename = file_path.name
                if "A20" in filename:  # MODIS date format
                    # Handle both original and processed filenames
                    date_part = filename.split("A20")[1]
                    if "." in date_part:
                        date_str = date_part.split(".")[
                            0
                        ]  # Extract YYYYDDD before next dot
                    else:
                        date_str = date_part[:7]  # e.g., 2023001

                    year = int(date_str[:4])
                    doy = int(date_str[4:7])
                    file_date = datetime(year, 1, 1) + timedelta(days=doy - 1)

                    if aggregation_method == "monthly":
                        period_key = f"{year}-{file_date.month:02d}"
                    elif aggregation_method == "seasonal":
                        season = (file_date.month - 1) // 3 + 1
                        period_key = f"{year}-Q{season}"
                    elif aggregation_method == "annual":
                        period_key = str(year)
                    else:
                        period_key = file_date.date().isoformat()

                    grouped_files[period_key].append(file_path)

            if not grouped_files:
                logger.error("No valid files found for aggregation")
                return None

            # Process each time period
            aggregated_files = []

            for period, period_files in grouped_files.items():
                logger.info(
                    f"Aggregating {len(period_files)} files for period {period}"
                )

                # Read all files for this period
                data_arrays = []
                profile = None

                for file_path in period_files:
                    try:
                        with rasterio.open(file_path) as src:
                            data = src.read(1)
                            data_arrays.append(data)

                            if profile is None:
                                profile = src.profile.copy()
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")

                if not data_arrays:
                    continue

                # Calculate mean composite
                stacked_data = np.stack(data_arrays, axis=0)
                aggregated_data = np.nanmean(stacked_data, axis=0)

                # Create output filename
                if output_path:
                    output_file = output_path
                else:
                    output_dir = self.download_directory / "aggregated"
                    output_dir.mkdir(exist_ok=True)
                    output_file = (
                        output_dir
                        / f"MODIS_{vegetation_index}_{aggregation_method}_{period}.tif"
                    )

                # Save aggregated data
                with rasterio.open(output_file, "w", **profile) as dst:
                    dst.write(aggregated_data, 1)

                aggregated_files.append(output_file)
                logger.info(f"Saved aggregated data: {output_file}")

            return aggregated_files[0] if aggregated_files else None

        except Exception as e:
            logger.error(f"Temporal aggregation failed: {e}")
            return None

    def validate_modis_file(self, file_path: Path) -> dict[str, Any]:
        """Validate downloaded MODIS file.

        Args:
            file_path: Path to the MODIS HDF file to validate

        Returns:
            Dict with validation results
        """
        validation_result = {
            "file_exists": False,
            "file_size_valid": False,
            "hdf_readable": False,
            "has_vi_data": False,
            "has_quality_data": False,
            "subdatasets_count": 0,
            "spatial_dimensions_valid": False,
            "error_message": None,
            "file_size_mb": 0,
            "subdatasets": [],
            "spatial_info": {},
        }

        try:
            # Check file existence
            if not file_path.exists():
                validation_result["error_message"] = "File does not exist"
                validation_result["success"] = False
                return validation_result

            validation_result["file_exists"] = True

            # Check file size (MODIS files should be 1-10 MB)
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result["file_size_mb"] = round(file_size_mb, 2)
            validation_result["file_size_valid"] = 0.5 < file_size_mb < 20

            # Try to open HDF file
            try:
                import rasterio

                with rasterio.open(file_path) as src:
                    validation_result["hdf_readable"] = True

                    # Get subdatasets
                    subdatasets = src.subdatasets
                    validation_result["subdatasets_count"] = len(subdatasets)
                    validation_result["subdatasets"] = subdatasets

                    # Check for vegetation indices and quality data
                    vi_found = any("NDVI" in sd or "EVI" in sd for sd in subdatasets)
                    quality_found = any("VI_Quality" in sd for sd in subdatasets)

                    validation_result["has_vi_data"] = vi_found
                    validation_result["has_quality_data"] = quality_found

                    # Check spatial dimensions (MODIS should be ~4800x4800 pixels)
                    if subdatasets:
                        try:
                            with rasterio.open(subdatasets[0]) as vi_src:
                                height, width = vi_src.height, vi_src.width
                                validation_result["spatial_info"] = {
                                    "height": height,
                                    "width": width,
                                    "crs": str(vi_src.crs) if vi_src.crs else "Unknown",
                                }

                                # MODIS tiles should be approximately square and large
                                validation_result["spatial_dimensions_valid"] = (
                                    4000 <= height <= 5000 and 4000 <= width <= 5000
                                )
                        except Exception as e:
                            validation_result["spatial_info"] = {"error": str(e)}

            except ImportError:
                validation_result["error_message"] = (
                    "rasterio not available for HDF validation"
                )
            except Exception as e:
                validation_result["error_message"] = f"HDF validation error: {e}"

        except Exception as e:
            validation_result["error_message"] = f"File validation error: {e}"

        # Overall validation success
        validation_result["success"] = all(
            [
                validation_result["file_exists"],
                validation_result["file_size_valid"],
                validation_result["hdf_readable"],
                validation_result["has_vi_data"],
                validation_result["spatial_dimensions_valid"],
            ]
        )

        return validation_result

    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """Clean up old downloaded files.

        Args:
            days_to_keep: Number of days of files to retain

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        for file_path in self.download_directory.glob("*.hdf"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old MODIS file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old MODIS files")
        return deleted_count

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    async def get_vegetation_indices(self, *args, **kwargs):
        """Alias for download_vegetation_indices for backward compatibility with tests."""
        return self.download_vegetation_indices(*args, **kwargs)

    def _generate_16day_periods(self, start_date: date, end_date: date) -> list[date]:
        """Generate 16-day periods for MODIS VI products."""
        periods = []

        # MODIS VI products start on day 1 and 17 of each month (approximately)
        current = start_date

        while current <= end_date:
            # Find the next 16-day period start
            year = current.year
            doy = current.timetuple().tm_yday

            # MODIS 16-day periods start on specific days
            period_start = doy - ((doy - 1) % 16)
            period_date = datetime(year, 1, 1) + timedelta(days=period_start - 1)

            if period_date.date() >= start_date and period_date.date() <= end_date:
                periods.append(period_date.date())

            # Move to next 16-day period
            current = period_date.date() + timedelta(days=16)

        return periods

    def _generate_quality_summary(self, file_paths: list[Path]) -> dict[str, Any]:
        """Generate quality summary for downloaded files."""
        total_files = len(file_paths)
        valid_files = 0
        total_size = 0

        for file_path in file_paths:
            try:
                validation = self.validate_modis_file(file_path)
                if validation["success"]:
                    valid_files += 1
                total_size += file_path.stat().st_size
            except Exception:
                continue

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "validation_rate": valid_files / total_files if total_files > 0 else 0,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "average_file_size_mb": (
                round(total_size / total_files / 1024 / 1024, 2)
                if total_files > 0
                else 0
            ),
        }

    def _create_failed_result(self, error_message: str) -> MODISDownloadResult:
        """Create a failed download result."""
        return MODISDownloadResult(
            request_id="failed",
            file_paths=[],
            total_size_bytes=0,
            tiles_processed=[],
            temporal_coverage={},
            download_duration_seconds=0,
            success=False,
            files_processed=0,
            quality_summary={},
            error_message=error_message,
        )
