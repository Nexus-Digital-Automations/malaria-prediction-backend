"""
External API Integration Tests for Malaria Prediction Backend.

This module tests integration with external data APIs (ERA5, CHIRPS, MODIS, WorldPop, MAP)
using mock services for reliable testing.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
from httpx import Response

from malaria_predictor.models import GeographicLocation
from malaria_predictor.services.chirps_client import CHIRPSClient
from malaria_predictor.services.era5_client import ERA5Client
from malaria_predictor.services.map_client import MAPClient
from malaria_predictor.services.modis_client import MODISClient
from malaria_predictor.services.worldpop_client import WorldPopClient

from .conftest import IntegrationTestCase


class TestERA5Integration(IntegrationTestCase):
    """Test ERA5 climate data API integration."""

    @pytest.fixture
    def era5_client(self, test_settings) -> ERA5Client:
        """Create ERA5 client for testing."""
        return ERA5Client(settings=test_settings)

    @pytest.fixture
    def mock_era5_response(self) -> dict:
        """Mock ERA5 API response."""
        return {
            "data": {
                "2m_temperature": [298.15, 299.20, 297.85],  # Kelvin
                "total_precipitation": [0.0, 0.0025, 0.0008],  # meters
                "2m_relative_humidity": [65.2, 68.1, 63.7],  # percentage
                "10m_u_component_of_wind": [2.1, 3.2, 1.8],  # m/s
                "10m_v_component_of_wind": [1.5, 2.8, 2.1],  # m/s
                "time": [
                    "2024-01-01T00:00:00",
                    "2024-01-01T06:00:00",
                    "2024-01-01T12:00:00",
                ],
                "latitude": [-1.25],
                "longitude": [36.75],
            },
            "status": "complete",
            "request_id": "test_request_123",
        }

    @pytest.mark.asyncio
    async def test_era5_data_retrieval(
        self, era5_client: ERA5Client, mock_era5_response: dict
    ):
        """Test ERA5 data retrieval with mocked API."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        with patch.object(era5_client, "_make_api_request") as mock_request:
            mock_request.return_value = mock_era5_response

            result = await era5_client.get_climate_data(
                location=location,
                start_date=start_date,
                end_date=end_date,
                variables=[
                    "2m_temperature",
                    "total_precipitation",
                    "2m_relative_humidity",
                ],
            )

            assert result is not None
            assert "temperature" in result
            assert "precipitation" in result
            assert "humidity" in result
            assert len(result["temperature"]) == 3

    @pytest.mark.asyncio
    async def test_era5_data_validation(
        self, era5_client: ERA5Client, mock_era5_response: dict
    ):
        """Test ERA5 data validation and unit conversion."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(era5_client, "_make_api_request") as mock_request:
            mock_request.return_value = mock_era5_response

            result = await era5_client.get_climate_data(
                location=location,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
            )

            # Validate temperature conversion (Kelvin to Celsius)
            assert all(
                temp < 100 for temp in result["temperature"]
            )  # Should be in Celsius
            assert all(temp > -50 for temp in result["temperature"])  # Reasonable range

            # Validate precipitation conversion (meters to mm)
            assert all(precip >= 0 for precip in result["precipitation"])

            # Validate humidity range
            assert all(0 <= hum <= 100 for hum in result["humidity"])

    @pytest.mark.asyncio
    async def test_era5_error_handling(self, era5_client: ERA5Client):
        """Test ERA5 API error handling."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Test API error response
        error_response = {
            "error": {
                "code": 400,
                "message": "Invalid date range",
            }
        }

        with patch.object(era5_client, "_make_api_request") as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400, json=lambda: error_response),
            )

            with pytest.raises(httpx.HTTPStatusError):
                await era5_client.get_climate_data(
                    location=location,
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2),
                )

    @pytest.mark.asyncio
    async def test_era5_rate_limiting(self, era5_client: ERA5Client):
        """Test ERA5 API rate limiting handling."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Mock rate limit response
        rate_limit_response = Response(
            status_code=429,
            headers={"Retry-After": "60"},
            content=b'{"error": "Rate limit exceeded"}',
        )

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = rate_limit_response

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await era5_client.get_climate_data(
                    location=location,
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2),
                )

            assert exc_info.value.response.status_code == 429

    @pytest.mark.asyncio
    async def test_era5_caching_integration(
        self, era5_client: ERA5Client, mock_era5_response: dict, test_redis_client
    ):
        """Test ERA5 data caching integration."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Set up cache client
        era5_client.cache_client = test_redis_client

        with patch.object(era5_client, "_make_api_request") as mock_request:
            mock_request.return_value = mock_era5_response

            # First request should hit API
            result1 = await era5_client.get_climate_data(
                location=location,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
            )

            # Second request should use cache
            result2 = await era5_client.get_climate_data(
                location=location,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
            )

            # API should only be called once
            assert mock_request.call_count == 1
            assert result1 == result2


class TestCHIRPSIntegration(IntegrationTestCase):
    """Test CHIRPS precipitation data API integration."""

    @pytest.fixture
    def chirps_client(self, test_settings) -> CHIRPSClient:
        """Create CHIRPS client for testing."""
        return CHIRPSClient(settings=test_settings)

    @pytest.fixture
    def mock_chirps_response(self) -> dict:
        """Mock CHIRPS API response."""
        return {
            "data": [
                {
                    "date": "2024-01-01",
                    "precipitation": 15.2,
                    "latitude": -1.286389,
                    "longitude": 36.817222,
                },
                {
                    "date": "2024-01-02",
                    "precipitation": 8.7,
                    "latitude": -1.286389,
                    "longitude": 36.817222,
                },
                {
                    "date": "2024-01-03",
                    "precipitation": 22.1,
                    "latitude": -1.286389,
                    "longitude": 36.817222,
                },
            ],
            "metadata": {
                "source": "CHIRPS v2.0",
                "resolution": "0.05 degrees",
                "units": "mm",
            },
        }

    @pytest.mark.asyncio
    async def test_chirps_data_retrieval(
        self, chirps_client: CHIRPSClient, mock_chirps_response: dict
    ):
        """Test CHIRPS precipitation data retrieval."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )
        start_date = datetime(2024, 1, 1).date()
        end_date = datetime(2024, 1, 3).date()

        with patch.object(chirps_client, "_fetch_data") as mock_fetch:
            mock_fetch.return_value = mock_chirps_response

            result = await chirps_client.get_precipitation_data(
                location=location,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            assert "precipitation" in result
            assert "dates" in result
            assert len(result["precipitation"]) == 3
            assert result["precipitation"][0] == 15.2

    @pytest.mark.asyncio
    async def test_chirps_data_aggregation(
        self, chirps_client: CHIRPSClient, mock_chirps_response: dict
    ):
        """Test CHIRPS data aggregation capabilities."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(chirps_client, "_fetch_data") as mock_fetch:
            mock_fetch.return_value = mock_chirps_response

            # Test monthly aggregation
            result = await chirps_client.get_monthly_precipitation(
                location=location,
                year=2024,
                month=1,
            )

            expected_total = sum([15.2, 8.7, 22.1])  # Sum of daily values
            assert abs(result["total_precipitation"] - expected_total) < 0.1

    @pytest.mark.asyncio
    async def test_chirps_spatial_queries(self, chirps_client: CHIRPSClient):
        """Test CHIRPS spatial data queries."""
        # Mock response for bounding box query
        bbox_response = {
            "data": [
                {"lat": -1.0, "lon": 36.0, "precipitation": 12.5, "date": "2024-01-01"},
                {"lat": -1.0, "lon": 37.0, "precipitation": 18.3, "date": "2024-01-01"},
                {"lat": -2.0, "lon": 36.0, "precipitation": 14.7, "date": "2024-01-01"},
                {"lat": -2.0, "lon": 37.0, "precipitation": 20.1, "date": "2024-01-01"},
            ]
        }

        with patch.object(chirps_client, "_fetch_data") as mock_fetch:
            mock_fetch.return_value = bbox_response

            result = await chirps_client.get_precipitation_grid(
                bbox={"north": -1.0, "south": -2.0, "east": 37.0, "west": 36.0},
                date=datetime(2024, 1, 1).date(),
            )

            assert len(result["grid_data"]) == 4
            assert all("precipitation" in point for point in result["grid_data"])


class TestMODISIntegration(IntegrationTestCase):
    """Test MODIS vegetation data API integration."""

    @pytest.fixture
    def modis_client(self, test_settings) -> MODISClient:
        """Create MODIS client for testing."""
        return MODISClient(settings=test_settings)

    @pytest.fixture
    def mock_modis_response(self) -> dict:
        """Mock MODIS API response."""
        return {
            "results": [
                {
                    "date": "2024-01-01",
                    "pixel_reliability": "Good",
                    "ndvi": 0.6521,
                    "evi": 0.5834,
                    "lst_day": 298.5,
                    "lst_night": 285.1,
                    "qa_quality_flag": "Good quality",
                },
                {
                    "date": "2024-01-09",  # 8-day composite
                    "pixel_reliability": "Good",
                    "ndvi": 0.7189,
                    "evi": 0.6412,
                    "lst_day": 301.2,
                    "lst_night": 287.3,
                    "qa_quality_flag": "Good quality",
                },
            ],
            "metadata": {
                "product": "MOD13Q1",
                "version": "061",
                "pixel_size": "250m",
            },
        }

    @pytest.mark.asyncio
    async def test_modis_vegetation_data(
        self, modis_client: MODISClient, mock_modis_response: dict
    ):
        """Test MODIS vegetation index data retrieval."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )
        start_date = datetime(2024, 1, 1).date()
        end_date = datetime(2024, 1, 31).date()

        with patch.object(modis_client, "_query_api") as mock_query:
            mock_query.return_value = mock_modis_response

            result = await modis_client.get_vegetation_indices(
                location=location,
                start_date=start_date,
                end_date=end_date,
                products=["MOD13Q1"],  # NDVI/EVI product
            )

            assert result is not None
            assert "ndvi" in result
            assert "evi" in result
            assert len(result["ndvi"]) == 2
            assert 0 <= result["ndvi"][0] <= 1  # NDVI range validation

    @pytest.mark.asyncio
    async def test_modis_land_surface_temperature(
        self, modis_client: MODISClient, mock_modis_response: dict
    ):
        """Test MODIS land surface temperature data retrieval."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(modis_client, "_query_api") as mock_query:
            mock_query.return_value = mock_modis_response

            result = await modis_client.get_land_surface_temperature(
                location=location,
                start_date=datetime(2024, 1, 1).date(),
                end_date=datetime(2024, 1, 31).date(),
            )

            assert "lst_day" in result
            assert "lst_night" in result

            # Temperature should be in reasonable range (converted from Kelvin)
            for temp in result["lst_day"]:
                assert 200 < temp < 350  # Kelvin range

    @pytest.mark.asyncio
    async def test_modis_quality_filtering(
        self, modis_client: MODISClient, mock_modis_response: dict
    ):
        """Test MODIS data quality filtering."""
        # Add poor quality data to response
        poor_quality_response = mock_modis_response.copy()
        poor_quality_response["results"].append(
            {
                "date": "2024-01-17",
                "pixel_reliability": "Cloudy",
                "ndvi": -0.1,  # Invalid NDVI
                "evi": -0.05,  # Invalid EVI
                "lst_day": 0,  # Invalid temperature
                "lst_night": 0,
                "qa_quality_flag": "Poor quality",
            }
        )

        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(modis_client, "_query_api") as mock_query:
            mock_query.return_value = poor_quality_response

            result = await modis_client.get_vegetation_indices(
                location=location,
                start_date=datetime(2024, 1, 1).date(),
                end_date=datetime(2024, 1, 31).date(),
                quality_filter=True,
            )

            # Poor quality data should be filtered out
            assert len(result["ndvi"]) == 2  # Only good quality data
            assert all(ndvi >= 0 for ndvi in result["ndvi"])


class TestWorldPopIntegration(IntegrationTestCase):
    """Test WorldPop population data api integration."""

    @pytest.fixture
    def worldpop_client(self, test_settings) -> WorldPopClient:
        """Create WorldPop client for testing."""
        return WorldPopClient(settings=test_settings)

    @pytest.fixture
    def mock_worldpop_response(self) -> dict:
        """Mock WorldPop API response."""
        return {
            "data": {
                "population_density": 450.23,
                "total_population": 25000,
                "age_structure": {
                    "0-1": 1250,
                    "1-5": 3750,
                    "5-15": 5500,
                    "15-65": 13750,
                    "65+": 750,
                },
                "urban_rural": {
                    "urban": 21250,
                    "rural": 3750,
                },
            },
            "metadata": {
                "year": 2023,
                "resolution": "100m",
                "country": "Kenya",
                "dataset": "ppp_2023_1km_Aggregated",
            },
        }

    @pytest.mark.asyncio
    async def test_worldpop_population_data(
        self, worldpop_client: WorldPopClient, mock_worldpop_response: dict
    ):
        """Test WorldPop population data retrieval."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(worldpop_client, "_fetch_population_data") as mock_fetch:
            mock_fetch.return_value = mock_worldpop_response

            result = await worldpop_client.get_population_data(
                location=location,
                year=2023,
                dataset="ppp_2023_1km_Aggregated",
            )

            assert result["population_density"] == 450.23
            assert result["total_population"] == 25000
            assert "age_structure" in result

    @pytest.mark.asyncio
    async def test_worldpop_age_structure_analysis(
        self, worldpop_client: WorldPopClient, mock_worldpop_response: dict
    ):
        """Test WorldPop age structure analysis."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(worldpop_client, "_fetch_population_data") as mock_fetch:
            mock_fetch.return_value = mock_worldpop_response

            result = await worldpop_client.get_age_structure_analysis(
                location=location,
                year=2023,
            )

            assert "vulnerable_population" in result  # Children under 5
            assert "at_risk_population" in result  # Children + elderly
            assert result["vulnerable_population"] == 5000  # 0-1 + 1-5

    @pytest.mark.asyncio
    async def test_worldpop_urbanization_metrics(
        self, worldpop_client: WorldPopClient, mock_worldpop_response: dict
    ):
        """Test WorldPop urbanization metrics."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(worldpop_client, "_fetch_population_data") as mock_fetch:
            mock_fetch.return_value = mock_worldpop_response

            result = await worldpop_client.get_urbanization_metrics(
                location=location,
                year=2023,
            )

            assert "urban_fraction" in result
            assert "rural_fraction" in result
            assert abs(result["urban_fraction"] - 0.85) < 0.01  # 21250/25000


class TestMAPIntegration(IntegrationTestCase):
    """Test Malaria Atlas Project API integration."""

    @pytest.fixture
    def map_client(self, test_settings) -> MAPClient:
        """Create MAP client for testing."""
        return MAPClient(settings=test_settings)

    @pytest.fixture
    def mock_map_response(self) -> dict:
        """Mock MAP API response."""
        return {
            "data": {
                "malaria_incidence": 0.12,
                "parasite_rate": 0.08,
                "intervention_coverage": {
                    "itn_coverage": 0.75,  # Insecticide-treated nets
                    "irs_coverage": 0.45,  # Indoor residual spraying
                    "act_coverage": 0.82,  # Artemisinin combination therapy
                    "rdt_coverage": 0.68,  # Rapid diagnostic tests
                },
                "environmental_suitability": 0.68,
                "transmission_intensity": "moderate",
            },
            "metadata": {
                "country": "Kenya",
                "year": 2023,
                "data_source": "MAP Global Database",
                "last_updated": "2024-01-01",
            },
        }

    @pytest.mark.asyncio
    async def test_map_malaria_data(
        self, map_client: MAPClient, mock_map_response: dict
    ):
        """Test MAP malaria incidence data retrieval."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(map_client, "_query_database") as mock_query:
            mock_query.return_value = mock_map_response

            result = await map_client.get_malaria_data(
                location=location,
                year=2023,
                metrics=["incidence", "parasite_rate", "interventions"],
            )

            assert result["malaria_incidence"] == 0.12
            assert result["parasite_rate"] == 0.08
            assert "intervention_coverage" in result

    @pytest.mark.asyncio
    async def test_map_intervention_coverage(
        self, map_client: MAPClient, mock_map_response: dict
    ):
        """Test MAP intervention coverage analysis."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(map_client, "_query_database") as mock_query:
            mock_query.return_value = mock_map_response

            result = await map_client.get_intervention_coverage(
                location=location,
                year=2023,
            )

            interventions = result["intervention_coverage"]
            assert interventions["itn_coverage"] == 0.75
            assert interventions["act_coverage"] == 0.82

            # Calculate overall intervention score
            overall_score = sum(interventions.values()) / len(interventions)
            assert 0 <= overall_score <= 1

    @pytest.mark.asyncio
    async def test_map_environmental_suitability(
        self, map_client: MAPClient, mock_map_response: dict
    ):
        """Test MAP environmental suitability data."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        with patch.object(map_client, "_query_database") as mock_query:
            mock_query.return_value = mock_map_response

            result = await map_client.get_environmental_suitability(
                location=location,
                year=2023,
            )

            assert result["environmental_suitability"] == 0.68
            assert result["transmission_intensity"] == "moderate"


class TestAPIIntegrationWorkflow(IntegrationTestCase):
    """Test complete API integration workflow."""

    @pytest.mark.asyncio
    async def test_multi_source_data_collection(
        self, mock_external_apis: dict, test_settings
    ):
        """Test collecting data from multiple external APIs."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )
        date_range = {
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 1, 31),
        }

        # Initialize clients
        era5_client = ERA5Client(settings=test_settings)
        chirps_client = CHIRPSClient(settings=test_settings)
        modis_client = MODISClient(settings=test_settings)
        worldpop_client = WorldPopClient(settings=test_settings)
        map_client = MAPClient(settings=test_settings)

        # Mock all API calls
        with (
            patch.object(era5_client, "_make_api_request") as mock_era5,
            patch.object(chirps_client, "_fetch_data") as mock_chirps,
            patch.object(modis_client, "_query_api") as mock_modis,
            patch.object(worldpop_client, "_fetch_population_data") as mock_worldpop,
            patch.object(map_client, "_query_database") as mock_map,
        ):
            # Set up mock responses
            mock_era5.return_value = mock_external_apis["era5"]
            mock_chirps.return_value = mock_external_apis["chirps"]
            mock_modis.return_value = mock_external_apis["modis"]
            mock_worldpop.return_value = mock_external_apis["worldpop"]
            mock_map.return_value = mock_external_apis["map"]

            # Collect data from all sources
            era5_data = await era5_client.get_climate_data(
                location=location,
                start_date=date_range["start_date"],
                end_date=date_range["end_date"],
            )

            chirps_data = await chirps_client.get_precipitation_data(
                location=location,
                start_date=date_range["start_date"].date(),
                end_date=date_range["end_date"].date(),
            )

            modis_data = await modis_client.get_vegetation_indices(
                location=location,
                start_date=date_range["start_date"].date(),
                end_date=date_range["end_date"].date(),
            )

            worldpop_data = await worldpop_client.get_population_data(
                location=location,
                year=2023,
            )

            map_data = await map_client.get_malaria_data(
                location=location,
                year=2023,
            )

            # Validate all data sources returned data
            assert era5_data is not None
            assert chirps_data is not None
            assert modis_data is not None
            assert worldpop_data is not None
            assert map_data is not None

            # Validate data structure consistency
            self.assert_environmental_data(
                {
                    "location": location.dict(),
                    "date_range": date_range,
                    "climate_data": era5_data,
                }
            )

    @pytest.mark.asyncio
    async def test_api_failure_resilience(self, test_settings):
        """Test system resilience to individual API failures."""
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Initialize clients
        era5_client = ERA5Client(settings=test_settings)
        chirps_client = CHIRPSClient(settings=test_settings)

        # Mock ERA5 success and CHIRPS failure
        with (
            patch.object(era5_client, "_make_api_request") as mock_era5,
            patch.object(chirps_client, "_fetch_data") as mock_chirps,
        ):
            mock_era5.return_value = {"data": {"temperature": [25.0]}}
            mock_chirps.side_effect = httpx.HTTPStatusError(
                "Service Unavailable",
                request=MagicMock(),
                response=MagicMock(status_code=503),
            )

            # ERA5 should succeed
            era5_result = await era5_client.get_climate_data(
                location=location,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
            )
            assert era5_result is not None

            # CHIRPS should fail gracefully
            with pytest.raises(httpx.HTTPStatusError):
                await chirps_client.get_precipitation_data(
                    location=location,
                    start_date=datetime(2024, 1, 1).date(),
                    end_date=datetime(2024, 1, 2).date(),
                )

    @pytest.mark.asyncio
    async def test_api_response_validation(self, test_settings):
        """Test API response validation and error handling."""
        era5_client = ERA5Client(settings=test_settings)
        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Test invalid response format
        invalid_response = {"invalid": "format", "missing": "required_fields"}

        with patch.object(era5_client, "_make_api_request") as mock_request:
            mock_request.return_value = invalid_response

            with pytest.raises(ValueError) as exc_info:
                await era5_client.get_climate_data(
                    location=location,
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2),
                )

            assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(
        self, mock_external_apis: dict, test_settings
    ):
        """Test concurrent API requests for performance."""
        import asyncio

        location = GeographicLocation(
            latitude=-1.286389,
            longitude=36.817222,
            area_name="Nairobi",
            country_code="KE",
        )

        # Initialize clients
        clients = {
            "era5": ERA5Client(settings=test_settings),
            "chirps": CHIRPSClient(settings=test_settings),
            "modis": MODISClient(settings=test_settings),
        }

        async def fetch_era5():
            with patch.object(clients["era5"], "_make_api_request") as mock:
                mock.return_value = mock_external_apis["era5"]
                return await clients["era5"].get_climate_data(
                    location=location,
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2),
                )

        async def fetch_chirps():
            with patch.object(clients["chirps"], "_fetch_data") as mock:
                mock.return_value = mock_external_apis["chirps"]
                return await clients["chirps"].get_precipitation_data(
                    location=location,
                    start_date=datetime(2024, 1, 1).date(),
                    end_date=datetime(2024, 1, 2).date(),
                )

        async def fetch_modis():
            with patch.object(clients["modis"], "_query_api") as mock:
                mock.return_value = mock_external_apis["modis"]
                return await clients["modis"].get_vegetation_indices(
                    location=location,
                    start_date=datetime(2024, 1, 1).date(),
                    end_date=datetime(2024, 1, 2).date(),
                )

        # Execute concurrent requests
        start_time = datetime.now()

        results = await asyncio.gather(
            fetch_era5(), fetch_chirps(), fetch_modis(), return_exceptions=True
        )

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # All requests should complete successfully
        assert len(results) == 3
        assert all(not isinstance(result, Exception) for result in results)

        # Concurrent execution should be faster than sequential
        assert execution_time < 5.0  # Should complete within 5 seconds
