"""
Mock API Server for External Service Testing.

This mock server simulates external APIs (ERA5, CHIRPS, MODIS, WorldPop, MAP)
for reliable integration testing without depending on external services.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data directory
MOCK_DATA_DIR = Path("/app/test_data")

# Create FastAPI apps for different services
era5_app = FastAPI(title="Mock ERA5 API", version="1.0.0")
chirps_app = FastAPI(title="Mock CHIRPS API", version="1.0.0")
modis_app = FastAPI(title="Mock MODIS API", version="1.0.0")
worldpop_app = FastAPI(title="Mock WorldPop API", version="1.0.0")
map_app = FastAPI(title="Mock MAP API", version="1.0.0")
main_app = FastAPI(title="Mock API Coordinator", version="1.0.0")

# Add CORS middleware to all apps
for app in [era5_app, chirps_app, modis_app, worldpop_app, map_app, main_app]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class LocationRequest(BaseModel):
    """Location request model."""

    latitude: float
    longitude: float


class DateRangeRequest(BaseModel):
    """Date range request model."""

    start_date: str
    end_date: str


def load_mock_data(filename: str) -> dict[str, Any]:
    """Load mock data from JSON file."""
    file_path = MOCK_DATA_DIR / filename
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)
    return {}


def generate_realistic_delay() -> float:
    """Generate realistic API response delay."""
    return random.uniform(0.1, 0.5)  # 100-500ms delay


async def simulate_api_delay():
    """Simulate realistic API response time."""
    await asyncio.sleep(generate_realistic_delay())


def add_request_noise(
    data: dict[str, Any], noise_factor: float = 0.05
) -> dict[str, Any]:
    """Add realistic noise to mock data."""
    if not isinstance(data, dict):
        return data

    result = data.copy()

    # Add small variations to numerical values
    for key, value in result.items():
        if isinstance(value, int | float) and key not in [
            "latitude",
            "longitude",
            "year",
        ]:
            if isinstance(value, float):
                noise = random.uniform(
                    -abs(value * noise_factor), abs(value * noise_factor)
                )
                result[key] = round(value + noise, 4)
            elif (
                isinstance(value, int) and value > 10
            ):  # Don't add noise to small integers
                noise = int(
                    random.uniform(
                        -abs(value * noise_factor), abs(value * noise_factor)
                    )
                )
                result[key] = max(0, value + noise)
        elif isinstance(value, dict):
            result[key] = add_request_noise(value, noise_factor)
        elif (
            isinstance(value, list)
            and len(value) > 0
            and isinstance(value[0], int | float)
        ):
            result[key] = [
                (
                    round(
                        v
                        + random.uniform(-abs(v * noise_factor), abs(v * noise_factor)),
                        4,
                    )
                    if isinstance(v, float)
                    else v
                )
                for v in value
            ]

    return result


# =============================================================================
# ERA5 Mock API
# =============================================================================


@era5_app.get("/health")
async def era5_health():
    """ERA5 health check."""
    return {"status": "healthy", "service": "ERA5 Mock API"}


@era5_app.get("/climate-data")
async def get_era5_climate_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(...),
    end_date: str = Query(...),
    variables: str | None = Query(None),
):
    """Mock ERA5 climate data endpoint."""
    await simulate_api_delay()

    # Load base mock data
    mock_data = load_mock_data("location_1/era5_data.json")

    if not mock_data:
        # Generate synthetic data if no mock file exists
        mock_data = generate_synthetic_era5_data(
            latitude, longitude, start_date, end_date
        )

    # Add location-specific variations
    mock_data = customize_era5_data_for_location(mock_data, latitude, longitude)

    # Add realistic noise
    mock_data = add_request_noise(mock_data)

    return mock_data


def generate_synthetic_era5_data(
    lat: float, lon: float, start_date: str, end_date: str
) -> dict[str, Any]:
    """Generate synthetic ERA5 data."""
    # Parse dates
    start = datetime.fromisoformat(start_date.replace("Z", ""))
    end = datetime.fromisoformat(end_date.replace("Z", ""))

    # Generate 6-hourly data
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current.isoformat())
        current += timedelta(hours=6)

    n_points = len(timestamps)

    # Base climate values based on latitude
    base_temp = 20 + (abs(lat) * -0.5) + 5
    base_precip = 2.0 if abs(lat) < 10 else 1.0
    base_humidity = 70 if abs(lat) < 20 else 60
    base_wind = 5

    return {
        "data": {
            "2m_temperature": [base_temp + random.gauss(0, 3) for _ in range(n_points)],
            "total_precipitation": [
                max(0, base_precip + random.gauss(0, 1)) for _ in range(n_points)
            ],
            "2m_relative_humidity": [
                max(0, min(100, base_humidity + random.gauss(0, 10)))
                for _ in range(n_points)
            ],
            "10m_wind_speed": [
                max(0, base_wind + random.gauss(0, 2)) for _ in range(n_points)
            ],
            "time": timestamps,
            "latitude": [lat] * n_points,
            "longitude": [lon] * n_points,
        },
        "metadata": {
            "source": "ERA5 Mock",
            "location": {"latitude": lat, "longitude": lon},
            "date_range": {"start": start_date, "end": end_date},
        },
    }


def customize_era5_data_for_location(
    data: dict[str, Any], lat: float, lon: float
) -> dict[str, Any]:
    """Customize ERA5 data based on location."""
    result = data.copy()

    # Adjust temperature based on latitude (rough approximation)
    if "data" in result and "2m_temperature" in result["data"]:
        temp_adjustment = -0.5 * abs(lat)  # Colder at higher latitudes
        result["data"]["2m_temperature"] = [
            t + temp_adjustment for t in result["data"]["2m_temperature"]
        ]

    # Update location metadata
    if "metadata" in result:
        result["metadata"]["location"] = {"latitude": lat, "longitude": lon}

    return result


@era5_app.post("/climate-data")
async def post_era5_climate_data(request: Request):
    """Mock ERA5 climate data POST endpoint."""
    await simulate_api_delay()

    body = await request.json()
    lat = body.get("latitude", 0)
    lon = body.get("longitude", 0)
    start_date = body.get("start_date", "2024-01-01")
    end_date = body.get("end_date", "2024-01-31")

    return await get_era5_climate_data(lat, lon, start_date, end_date)


# =============================================================================
# CHIRPS Mock API
# =============================================================================


@chirps_app.get("/health")
async def chirps_health():
    """CHIRPS health check."""
    return {"status": "healthy", "service": "CHIRPS Mock API"}


@chirps_app.get("/precipitation")
async def get_chirps_precipitation(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    """Mock CHIRPS precipitation data endpoint."""
    await simulate_api_delay()

    mock_data = load_mock_data("location_1/chirps_data.json")

    if not mock_data:
        mock_data = generate_synthetic_chirps_data(
            latitude, longitude, start_date, end_date
        )

    mock_data = customize_chirps_data_for_location(mock_data, latitude, longitude)
    mock_data = add_request_noise(mock_data)

    return mock_data


def generate_synthetic_chirps_data(
    lat: float, lon: float, start_date: str, end_date: str
) -> dict[str, Any]:
    """Generate synthetic CHIRPS data."""
    from datetime import datetime

    import pandas as pd

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    date_range = pd.date_range(start.date(), end.date(), freq="D")

    # Base precipitation based on latitude
    base_precip = 4.0 if abs(lat) < 10 else 2.0 if abs(lat) < 23 else 1.0

    precipitation_data = []
    for date in date_range:
        if random.random() < 0.25:  # 25% chance of rain
            precip = max(0, random.lognormvariate(0, 0.8) * base_precip)
        else:
            precip = 0.0

        precipitation_data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "precipitation": round(precip, 1),
                "latitude": lat,
                "longitude": lon,
            }
        )

    return {
        "data": precipitation_data,
        "metadata": {
            "source": "CHIRPS Mock v2.0",
            "location": {"latitude": lat, "longitude": lon},
            "resolution": "0.05 degrees",
            "units": "mm/day",
        },
    }


def customize_chirps_data_for_location(
    data: dict[str, Any], lat: float, lon: float
) -> dict[str, Any]:
    """Customize CHIRPS data based on location."""
    result = data.copy()

    # Update location in data points
    if "data" in result:
        for point in result["data"]:
            point["latitude"] = lat
            point["longitude"] = lon

    # Update metadata
    if "metadata" in result:
        result["metadata"]["location"] = {"latitude": lat, "longitude": lon}

    return result


# =============================================================================
# MODIS Mock API
# =============================================================================


@modis_app.get("/health")
async def modis_health():
    """MODIS health check."""
    return {"status": "healthy", "service": "MODIS Mock API"}


@modis_app.get("/vegetation")
async def get_modis_vegetation(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(...),
    end_date: str = Query(...),
    product: str = Query("MOD13Q1"),
):
    """Mock MODIS vegetation data endpoint."""
    await simulate_api_delay()

    mock_data = load_mock_data("location_1/modis_data.json")

    if not mock_data:
        mock_data = generate_synthetic_modis_data(
            latitude, longitude, start_date, end_date
        )

    mock_data = customize_modis_data_for_location(mock_data, latitude, longitude)
    mock_data = add_request_noise(mock_data)

    return mock_data


def generate_synthetic_modis_data(
    lat: float, lon: float, start_date: str, end_date: str
) -> dict[str, Any]:
    """Generate synthetic MODIS data."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    # Generate 16-day composites
    current_date = start
    composite_dates = []
    while current_date <= end:
        composite_dates.append(current_date)
        current_date += timedelta(days=16)

    # Base values based on latitude
    base_ndvi = 0.7 if abs(lat) < 10 else 0.5 if abs(lat) < 23 else 0.4
    base_evi = base_ndvi * 0.8
    base_lst_day = 305 if abs(lat) < 10 else 300 if abs(lat) < 23 else 295
    base_lst_night = base_lst_day - 15

    results = []
    for date in composite_dates:
        results.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "pixel_reliability": "Good" if random.random() > 0.1 else "Marginal",
                "ndvi": max(0, min(1, base_ndvi + random.gauss(0, 0.05))),
                "evi": max(0, min(1, base_evi + random.gauss(0, 0.04))),
                "lst_day": base_lst_day + random.gauss(0, 2),
                "lst_night": base_lst_night + random.gauss(0, 1.5),
                "qa_quality_flag": (
                    "Good quality" if random.random() > 0.15 else "Acceptable quality"
                ),
            }
        )

    return {
        "results": results,
        "metadata": {
            "source": "MODIS Mock",
            "product": "MOD13Q1",
            "version": "061",
            "pixel_size": "250m",
            "location": {"latitude": lat, "longitude": lon},
        },
    }


def customize_modis_data_for_location(
    data: dict[str, Any], lat: float, lon: float
) -> dict[str, Any]:
    """Customize MODIS data based on location."""
    result = data.copy()

    if "metadata" in result:
        result["metadata"]["location"] = {"latitude": lat, "longitude": lon}

    return result


# =============================================================================
# WorldPop Mock API
# =============================================================================


@worldpop_app.get("/health")
async def worldpop_health():
    """WorldPop health check."""
    return {"status": "healthy", "service": "WorldPop Mock API"}


@worldpop_app.get("/population")
async def get_worldpop_population(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    year: int = Query(2023),
    dataset: str = Query("ppp_2023_1km_Aggregated"),
):
    """Mock WorldPop population data endpoint."""
    await simulate_api_delay()

    mock_data = load_mock_data("location_1/worldpop_data.json")

    if not mock_data:
        mock_data = generate_synthetic_worldpop_data(latitude, longitude, year)

    mock_data = customize_worldpop_data_for_location(mock_data, latitude, longitude)
    mock_data = add_request_noise(mock_data, noise_factor=0.1)

    return mock_data


def generate_synthetic_worldpop_data(
    lat: float, lon: float, year: int
) -> dict[str, Any]:
    """Generate synthetic WorldPop data."""
    dataset = "worldpop_unconstrained"  # Default dataset identifier
    # Rough population density estimates based on location
    if abs(lat - (-1.286389)) < 0.1 and abs(lon - 36.817222) < 0.1:  # Near Nairobi
        base_density = 4500
        urban_fraction = 0.85
    elif abs(lat) < 10:  # Tropical regions
        base_density = random.uniform(200, 1000)
        urban_fraction = random.uniform(0.3, 0.7)
    else:
        base_density = random.uniform(50, 500)
        urban_fraction = random.uniform(0.2, 0.6)

    population_density = base_density * random.uniform(0.8, 1.2)
    total_population = int(population_density)

    return {
        "data": {
            "population_density": round(population_density, 2),
            "total_population": total_population,
            "age_structure": {
                "0-1": int(total_population * 0.04),
                "1-5": int(total_population * 0.12),
                "5-15": int(total_population * 0.22),
                "15-65": int(total_population * 0.58),
                "65+": int(total_population * 0.04),
            },
            "urban_rural": {
                "urban": int(total_population * urban_fraction),
                "rural": int(total_population * (1 - urban_fraction)),
            },
        },
        "metadata": {
            "source": "WorldPop Mock",
            "year": year,
            "resolution": "100m",
            "dataset": dataset,
            "location": {"latitude": lat, "longitude": lon},
        },
    }


def customize_worldpop_data_for_location(
    data: dict[str, Any], lat: float, lon: float
) -> dict[str, Any]:
    """Customize WorldPop data based on location."""
    result = data.copy()

    if "metadata" in result:
        result["metadata"]["location"] = {"latitude": lat, "longitude": lon}

    return result


# =============================================================================
# MAP Mock API
# =============================================================================


@map_app.get("/health")
async def map_health():
    """MAP health check."""
    return {"status": "healthy", "service": "MAP Mock API"}


@map_app.get("/malaria-data")
async def get_map_malaria_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    year: int = Query(2023),
    metrics: str | None = Query(None),
):
    """Mock MAP malaria data endpoint."""
    await simulate_api_delay()

    mock_data = load_mock_data("location_1/map_data.json")

    if not mock_data:
        mock_data = generate_synthetic_map_data(latitude, longitude, year)

    mock_data = customize_map_data_for_location(mock_data, latitude, longitude)
    mock_data = add_request_noise(mock_data)

    return mock_data


def generate_synthetic_map_data(lat: float, lon: float, year: int) -> dict[str, Any]:
    """Generate synthetic MAP data."""
    # Base malaria risk based on latitude (rough climate approximation)
    if abs(lat) < 10:  # Tropical belt
        base_incidence = random.uniform(0.15, 0.35)
        environmental_suitability = random.uniform(0.6, 0.85)
    elif abs(lat) < 23:  # Subtropical
        base_incidence = random.uniform(0.05, 0.20)
        environmental_suitability = random.uniform(0.4, 0.70)
    else:  # Temperate
        base_incidence = random.uniform(0.001, 0.05)
        environmental_suitability = random.uniform(0.1, 0.40)

    parasite_rate = base_incidence * 0.7

    # Intervention coverage (higher coverage often means lower incidence)
    coverage_factor = 1.2 - base_incidence

    return {
        "data": {
            "malaria_incidence": round(base_incidence, 4),
            "parasite_rate": round(parasite_rate, 4),
            "intervention_coverage": {
                "itn_coverage": round(
                    max(0.2, min(0.9, random.uniform(0.4, 0.8) * coverage_factor)), 3
                ),
                "irs_coverage": round(
                    max(0.1, min(0.7, random.uniform(0.2, 0.6) * coverage_factor)), 3
                ),
                "act_coverage": round(
                    max(0.3, min(0.95, random.uniform(0.5, 0.9) * coverage_factor)), 3
                ),
                "rdt_coverage": round(
                    max(0.2, min(0.8, random.uniform(0.3, 0.7) * coverage_factor)), 3
                ),
            },
            "environmental_suitability": round(environmental_suitability, 3),
            "transmission_intensity": (
                "high"
                if base_incidence > 0.2
                else "moderate" if base_incidence > 0.1 else "low"
            ),
        },
        "metadata": {
            "source": "MAP Mock Global Database",
            "country": "Unknown",
            "year": year,
            "location": {"latitude": lat, "longitude": lon},
            "last_updated": datetime.now().isoformat(),
        },
    }


def customize_map_data_for_location(
    data: dict[str, Any], lat: float, lon: float
) -> dict[str, Any]:
    """Customize MAP data based on location."""
    result = data.copy()

    if "metadata" in result:
        result["metadata"]["location"] = {"latitude": lat, "longitude": lon}

    return result


# =============================================================================
# Main Coordinator API
# =============================================================================


@main_app.get("/health")
async def main_health():
    """Main health check."""
    return {
        "status": "healthy",
        "service": "Mock API Coordinator",
        "services": {
            "era5": "http://localhost:9001",
            "chirps": "http://localhost:9002",
            "modis": "http://localhost:9003",
            "worldpop": "http://localhost:9004",
            "map": "http://localhost:9005",
        },
    }


@main_app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Mock API Coordinator for Malaria Prediction Testing",
        "services": {
            "era5": {"port": 9001, "description": "ERA5 climate data mock"},
            "chirps": {"port": 9002, "description": "CHIRPS precipitation data mock"},
            "modis": {"port": 9003, "description": "MODIS vegetation data mock"},
            "worldpop": {"port": 9004, "description": "WorldPop population data mock"},
            "map": {"port": 9005, "description": "MAP malaria data mock"},
        },
        "endpoints": {
            "health": "GET /health",
            "era5_climate": "GET http://localhost:9001/climate-data",
            "chirps_precipitation": "GET http://localhost:9002/precipitation",
            "modis_vegetation": "GET http://localhost:9003/vegetation",
            "worldpop_population": "GET http://localhost:9004/population",
            "map_malaria": "GET http://localhost:9005/malaria-data",
        },
    }


# =============================================================================
# Error Handlers
# =============================================================================


@main_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


# Add the same error handler to all service apps
for app in [era5_app, chirps_app, modis_app, worldpop_app, map_app]:
    app.exception_handler(Exception)(general_exception_handler)


# =============================================================================
# Server Setup
# =============================================================================


async def run_mock_services():
    """Run all mock services on different ports."""
    import multiprocessing

    def run_service(app, port):
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

    # Start each service in a separate process
    processes = [
        multiprocessing.Process(target=run_service, args=(main_app, 9000)),
        multiprocessing.Process(target=run_service, args=(era5_app, 9001)),
        multiprocessing.Process(target=run_service, args=(chirps_app, 9002)),
        multiprocessing.Process(target=run_service, args=(modis_app, 9003)),
        multiprocessing.Process(target=run_service, args=(worldpop_app, 9004)),
        multiprocessing.Process(target=run_service, args=(map_app, 9005)),
    ]

    for process in processes:
        process.start()

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        logger.info("Shutting down mock services...")
        for process in processes:
            process.terminate()
            process.join()


if __name__ == "__main__":
    asyncio.run(run_mock_services())
