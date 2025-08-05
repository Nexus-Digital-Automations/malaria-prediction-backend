"""
Database Integration Tests for Malaria Prediction Backend.

This module tests database operations, TimescaleDB functionality,
and data persistence layer integration.
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from dateutil import parser
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from malaria_predictor.api.models import (
    EnvironmentalData,
    EnvironmentalDataCreate,
    Location,
    MalariaIncidenceCreate,
    MalariaIncidenceData,
    PredictionCreate,
    PredictionData,
)
from malaria_predictor.api.security import (
    UserCreate,
)
from malaria_predictor.database.repositories import (
    EnvironmentalDataRepository,
    ERA5Repository,
    MalariaIncidenceRepository,
    PredictionRepository,
    UserRepository,
)
from malaria_predictor.models import (
    EnvironmentalFactors,
    GeographicLocation,
    MalariaPrediction,
    RiskAssessment,
)

from .conftest import IntegrationTestCase


class TestDatabaseConnectivity(IntegrationTestCase):
    """Test basic database connectivity and configuration."""

    @pytest.mark.asyncio
    async def test_database_connection(self, test_db_session: AsyncSession):
        """Test that database connection is working."""
        result = await test_db_session.execute(text("SELECT 1 as test"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_timescaledb_extension(self, test_db_session: AsyncSession):
        """Test that TimescaleDB extension is available."""
        result = await test_db_session.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
        )
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_postgis_extension(self, test_db_session: AsyncSession):
        """Test that PostGIS extension is available."""
        result = await test_db_session.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
        )
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_database_tables_exist(self, test_db_session: AsyncSession):
        """Test that all required tables exist."""
        tables = [
            "era5_data_points",
            "processed_climate_data",
            "malaria_risk_indices",
            "users",
        ]

        for table in tables:
            result = await test_db_session.execute(
                text(
                    f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'"
                )
            )
            assert result.scalar() == 1, f"Table {table} does not exist"


class TestEnvironmentalDataIntegration(IntegrationTestCase):
    """Test environmental data database operations."""

    @pytest.fixture
    def sample_era5_data(self) -> dict:
        """Create sample ERA5 data for testing."""
        return {
            "timestamp": "2024-01-01T12:00:00+00:00",
            "latitude": -1.286389,
            "longitude": 36.817222,
            "temperature_2m": 25.5,
            "total_precipitation": 15.2,
            "wind_speed_10m": 3.2,
            "surface_pressure": 101325.0,
        }

    @pytest.mark.asyncio
    async def test_create_environmental_data(
        self, test_db_session: AsyncSession, sample_era5_data: dict
    ):
        """Test creating environmental data record."""
        repo = ERA5Repository(test_db_session)

        # Convert string timestamp to datetime object
        data_with_datetime = sample_era5_data.copy()
        data_with_datetime["timestamp"] = parser.parse(sample_era5_data["timestamp"])

        result = await repo.bulk_insert_data_points([data_with_datetime])

        assert result > 0

    @pytest.mark.asyncio
    async def test_get_environmental_data_by_location(
        self,
        test_db_session: AsyncSession,
        sample_environmental_data: EnvironmentalFactors,
    ):
        """Test retrieving environmental data by location."""
        repo = EnvironmentalDataRepository(test_db_session)

        # Create test data
        created = await repo.create(sample_environmental_data)

        # Query by location
        results = await repo.get_by_location(
            latitude=sample_environmental_data.location.latitude,
            longitude=sample_environmental_data.location.longitude,
            radius_km=1.0,
        )

        assert len(results) == 1
        assert results[0].id == created.id

    @pytest.mark.asyncio
    async def test_get_environmental_data_by_time_range(
        self, test_db_session: AsyncSession
    ):
        """Test retrieving environmental data by time range."""
        repo = EnvironmentalDataRepository(test_db_session)

        base_time = datetime.now()

        # Create test data across different times
        for i in range(5):
            data = EnvironmentalDataCreate(
                location=Location(latitude=-1.286389, longitude=36.817222),
                timestamp=base_time + timedelta(days=i),
                temperature=25.0 + i,
                precipitation=10.0,
                humidity=65.0,
                wind_speed=8.0,
                ndvi=0.6,
                evi=0.5,
                elevation=1800.0,
                population_density=400.0,
                data_source="test",
            )
            await repo.create(data)

        # Query specific time range
        start_time = base_time + timedelta(days=1)
        end_time = base_time + timedelta(days=3)

        results = await repo.get_by_time_range(
            start_time=start_time,
            end_time=end_time,
        )

        assert len(results) == 3  # Days 1, 2, 3
        temperatures = [r.temperature for r in results]
        assert 26.0 in temperatures  # Day 1
        assert 27.0 in temperatures  # Day 2
        assert 28.0 in temperatures  # Day 3

    @pytest.mark.asyncio
    async def test_spatial_query_performance(self, test_db_session: AsyncSession):
        """Test spatial query performance with multiple records."""
        repo = EnvironmentalDataRepository(test_db_session)

        # Create multiple records in a grid pattern
        records_created = 0
        for lat_offset in range(-2, 3):  # 5 latitudes
            for lon_offset in range(-2, 3):  # 5 longitudes
                data = EnvironmentalDataCreate(
                    location=Location(
                        latitude=-1.286389 + (lat_offset * 0.1),
                        longitude=36.817222 + (lon_offset * 0.1),
                    ),
                    timestamp=datetime.now(),
                    temperature=25.0,
                    precipitation=10.0,
                    humidity=65.0,
                    wind_speed=8.0,
                    ndvi=0.6,
                    evi=0.5,
                    elevation=1800.0,
                    population_density=400.0,
                    data_source="performance_test",
                )
                await repo.create(data)
                records_created += 1

        assert records_created == 25

        # Test spatial query performance
        import time

        start_time = time.time()

        results = await repo.get_by_location(
            latitude=-1.286389,
            longitude=36.817222,
            radius_km=20.0,  # Should capture all records
        )

        query_time = time.time() - start_time

        assert len(results) == 25
        assert query_time < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_timescaledb_hypertable_functionality(
        self, test_db_session: AsyncSession
    ):
        """Test TimescaleDB hypertable functionality."""
        # Check if environmental_data is a hypertable
        result = await test_db_session.execute(
            text(
                """
                SELECT 1 FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'environmental_data'
            """
            )
        )

        # If not a hypertable, create it (for testing purposes)
        if not result.scalar():
            await test_db_session.execute(
                text("SELECT create_hypertable('environmental_data', 'timestamp')")
            )
            await test_db_session.commit()

        # Verify hypertable creation
        result = await test_db_session.execute(
            text(
                """
                SELECT 1 FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'environmental_data'
            """
            )
        )
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_environmental_data_aggregation(self, test_db_session: AsyncSession):
        """Test environmental data aggregation queries."""
        repo = EnvironmentalDataRepository(test_db_session)

        base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        location = Location(latitude=-1.286389, longitude=36.817222)

        # Create hourly data for one day
        temperatures = [
            20,
            22,
            25,
            28,
            30,
            28,
            25,
            22,
            20,
            18,
            16,
            15,
            17,
            20,
            23,
            26,
            28,
            27,
            24,
            21,
            19,
            17,
            15,
            14,
        ]

        for hour, temp in enumerate(temperatures):
            data = EnvironmentalDataCreate(
                location=location,
                timestamp=base_time + timedelta(hours=hour),
                temperature=temp,
                precipitation=0.0,
                humidity=65.0,
                wind_speed=8.0,
                ndvi=0.6,
                evi=0.5,
                elevation=1800.0,
                population_density=400.0,
                data_source="aggregation_test",
            )
            await repo.create(data)

        # Test daily aggregation
        daily_avg = await test_db_session.execute(
            select(func.avg(EnvironmentalData.temperature)).where(
                EnvironmentalData.timestamp >= base_time,
                EnvironmentalData.timestamp < base_time + timedelta(days=1),
                EnvironmentalData.data_source == "aggregation_test",
            )
        )

        avg_temp = daily_avg.scalar()
        expected_avg = sum(temperatures) / len(temperatures)
        assert abs(avg_temp - expected_avg) < 0.1


class TestMalariaIncidenceIntegration(IntegrationTestCase):
    """Test malaria incidence data database operations."""

    @pytest.fixture
    def sample_malaria_data(self) -> dict:
        """Create sample malaria incidence data for testing."""
        return {
            "latitude": -1.286389,
            "longitude": 36.817222,
            "date": datetime.now().date(),
            "incidence_rate": 0.12,
            "parasite_rate": 0.08,
            "mortality_rate": 0.002,
            "age_group": "all",
            "population_at_risk": 25000,
            "cases_reported": 3000,
            "data_source": "integration_test",
        }

    @pytest.mark.asyncio
    async def test_create_malaria_incidence(
        self, test_db_session: AsyncSession, sample_malaria_data: dict
    ):
        """Test creating malaria incidence record."""
        repo = MalariaIncidenceRepository(test_db_session)

        result = await repo.create(sample_malaria_data)

        assert result.id is not None
        assert result.incidence_rate == sample_malaria_data.incidence_rate
        assert result.cases_reported == sample_malaria_data.cases_reported

    @pytest.mark.asyncio
    async def test_malaria_data_temporal_queries(self, test_db_session: AsyncSession):
        """Test temporal queries for malaria incidence data."""
        repo = MalariaIncidenceRepository(test_db_session)

        base_date = datetime.now().date()
        location = Location(latitude=-1.286389, longitude=36.817222)

        # Create monthly data for one year
        monthly_incidence = [
            0.08,
            0.10,
            0.15,
            0.20,
            0.18,
            0.22,
            0.25,
            0.23,
            0.20,
            0.15,
            0.12,
            0.09,
        ]

        for month, incidence in enumerate(monthly_incidence):
            data = MalariaIncidenceCreate(
                location=location,
                date=base_date.replace(month=month + 1, day=1),
                incidence_rate=incidence,
                parasite_rate=incidence * 0.7,
                mortality_rate=incidence * 0.01,
                age_group="all",
                population_at_risk=25000,
                cases_reported=int(incidence * 25000),
                data_source="temporal_test",
            )
            await repo.create(data)

        # Query seasonal patterns
        wet_season_avg = await test_db_session.execute(
            select(func.avg(MalariaIncidenceData.incidence_rate)).where(
                MalariaIncidenceData.date.between(
                    base_date.replace(month=3, day=1),
                    base_date.replace(month=8, day=31),
                ),
                MalariaIncidenceData.data_source == "temporal_test",
            )
        )

        dry_season_avg = await test_db_session.execute(
            select(func.avg(MalariaIncidenceData.incidence_rate)).where(
                MalariaIncidenceData.date < base_date.replace(month=3, day=1),
                MalariaIncidenceData.data_source == "temporal_test",
            )
        )

        wet_avg = wet_season_avg.scalar()
        dry_avg = dry_season_avg.scalar()

        # Wet season should have higher incidence
        assert wet_avg > dry_avg


class TestPredictionDataIntegration(IntegrationTestCase):
    """Test prediction data database operations."""

    @pytest.fixture
    def sample_prediction_data(self) -> MalariaPrediction:
        """Create sample prediction data for testing."""
        from malaria_predictor.models import RiskLevel

        return MalariaPrediction(
            location=GeographicLocation(
                latitude=-1.286389,
                longitude=36.817222,
                area_name="Nairobi",
                country_code="KE",
            ),
            environmental_data=EnvironmentalFactors(
                mean_temperature=25.5,
                min_temperature=20.0,
                max_temperature=31.0,
                monthly_rainfall=15.2,
                relative_humidity=65.8,
                ndvi=0.68,
                evi=0.61,
                elevation=1795.0,
            ),
            risk_assessment=RiskAssessment(
                risk_score=0.75,
                risk_level=RiskLevel.HIGH,
                confidence=0.85,
                temperature_factor=0.7,
                rainfall_factor=0.6,
                humidity_factor=0.8,
                vegetation_factor=0.7,
                elevation_factor=0.5,
            ),
            prediction_date=datetime.now().date(),
            time_horizon_days=30,
        )

    @pytest.mark.asyncio
    async def test_create_prediction(
        self, test_db_session: AsyncSession, sample_prediction_data: MalariaPrediction
    ):
        """Test creating prediction record."""
        repo = PredictionRepository(test_db_session)

        result = await repo.create(sample_prediction_data)

        assert result.id is not None
        assert result.risk_score == sample_prediction_data.risk_score
        assert result.model_version == sample_prediction_data.model_version
        assert (
            result.environmental_factors == sample_prediction_data.environmental_factors
        )

    @pytest.mark.asyncio
    async def test_prediction_model_comparison(self, test_db_session: AsyncSession):
        """Test comparing predictions from different models."""
        repo = PredictionRepository(test_db_session)

        location = Location(latitude=-1.286389, longitude=36.817222)
        pred_date = datetime.now().date()

        # Create predictions from different models
        models = ["lstm_v1.0", "transformer_v1.0", "ensemble_v1.0"]
        risk_scores = [0.72, 0.78, 0.75]

        for model, risk in zip(models, risk_scores, strict=False):
            data = PredictionCreate(
                location=location,
                prediction_date=pred_date,
                risk_score=risk,
                confidence_score=0.85,
                model_version=model,
                prediction_horizon_days=30,
                environmental_factors={"test": "data"},
                uncertainty_metrics={"std_dev": 0.08},
            )
            await repo.create(data)

        # Query predictions by model
        results = await repo.get_by_model_version("ensemble_v1.0")
        assert len(results) >= 1
        assert results[0].risk_score == 0.75

    @pytest.mark.asyncio
    async def test_prediction_performance_tracking(self, test_db_session: AsyncSession):
        """Test tracking prediction performance over time."""
        repo = PredictionRepository(test_db_session)

        base_date = datetime.now().date()
        location = Location(latitude=-1.286389, longitude=36.817222)

        # Create predictions with varying accuracy
        for days_back in range(30):
            pred_date = base_date - timedelta(days=days_back)
            # Simulate model improvement over time
            accuracy = 0.7 + (days_back * 0.01)  # Better recent predictions

            data = PredictionCreate(
                location=location,
                prediction_date=pred_date,
                risk_score=0.75,
                confidence_score=accuracy,
                model_version="ensemble_v1.0",
                prediction_horizon_days=30,
                environmental_factors={"test": "data"},
                uncertainty_metrics={"std_dev": 0.08},
            )
            await repo.create(data)

        # Analyze recent vs. older predictions
        recent_avg = await test_db_session.execute(
            select(func.avg(PredictionData.confidence_score)).where(
                PredictionData.prediction_date >= base_date - timedelta(days=7),
                PredictionData.model_version == "ensemble_v1.0",
            )
        )

        older_avg = await test_db_session.execute(
            select(func.avg(PredictionData.confidence_score)).where(
                PredictionData.prediction_date < base_date - timedelta(days=14),
                PredictionData.model_version == "ensemble_v1.0",
            )
        )

        recent_confidence = recent_avg.scalar()
        older_confidence = older_avg.scalar()

        # Recent predictions should have lower confidence (higher accuracy)
        assert recent_confidence < older_confidence


class TestUserManagementIntegration(IntegrationTestCase):
    """Test user management database operations."""

    @pytest.fixture
    def sample_user_data(self) -> UserCreate:
        """Create sample user data for testing."""
        return UserCreate(
            username="test_user",
            email="test@example.com",
            password="secure_password_123",
            full_name="Test User",
            organization="Test Organization",
        )

    @pytest.mark.asyncio
    async def test_create_user(
        self, test_db_session: AsyncSession, sample_user_data: UserCreate
    ):
        """Test creating user record."""
        repo = UserRepository(test_db_session)

        result = await repo.create(sample_user_data)

        assert result.id is not None
        assert result.username == sample_user_data.username
        assert result.email == sample_user_data.email
        assert result.hashed_password != sample_user_data.password  # Should be hashed

    @pytest.mark.asyncio
    async def test_user_authentication(
        self, test_db_session: AsyncSession, sample_user_data: UserCreate
    ):
        """Test user authentication process."""
        repo = UserRepository(test_db_session)

        # Create user
        created_user = await repo.create(sample_user_data)

        # Authenticate user
        authenticated_user = await repo.authenticate(
            username=sample_user_data.username,
            password=sample_user_data.password,
        )

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id

        # Test wrong password
        wrong_auth = await repo.authenticate(
            username=sample_user_data.username,
            password="wrong_password",
        )

        assert wrong_auth is None


class TestDatabaseTransactions(IntegrationTestCase):
    """Test database transaction handling and rollback scenarios."""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db_session: AsyncSession):
        """Test transaction rollback on error."""
        repo = EnvironmentalDataRepository(test_db_session)

        # Start transaction
        try:
            # Create valid record
            data1 = EnvironmentalDataCreate(
                location=Location(latitude=-1.286389, longitude=36.817222),
                timestamp=datetime.now(),
                temperature=25.5,
                precipitation=15.2,
                humidity=65.8,
                wind_speed=8.3,
                ndvi=0.68,
                evi=0.61,
                elevation=1795.0,
                population_density=450.2,
                data_source="transaction_test",
            )
            await repo.create(data1)

            # Force an error (invalid latitude)
            data2 = EnvironmentalDataCreate(
                location=Location(latitude=91.0, longitude=36.817222),  # Invalid
                timestamp=datetime.now(),
                temperature=25.5,
                precipitation=15.2,
                humidity=65.8,
                wind_speed=8.3,
                ndvi=0.68,
                evi=0.61,
                elevation=1795.0,
                population_density=450.2,
                data_source="transaction_test",
            )
            await repo.create(data2)

            await test_db_session.commit()

        except Exception:
            await test_db_session.rollback()

            # Verify first record was also rolled back
            results = await repo.get_by_data_source("transaction_test")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_concurrent_access(self, test_database_engine):
        """Test concurrent database access."""
        from sqlalchemy.ext.asyncio import AsyncSession, sessionmaker

        async_session_maker = sessionmaker(
            test_database_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def create_records(session_id: int):
            """Create records in separate session."""
            async with async_session_maker() as session:
                repo = EnvironmentalDataRepository(session)

                for i in range(5):
                    data = EnvironmentalDataCreate(
                        location=Location(
                            latitude=-1.286389 + (session_id * 0.01),
                            longitude=36.817222 + (i * 0.01),
                        ),
                        timestamp=datetime.now(),
                        temperature=25.0,
                        precipitation=10.0,
                        humidity=65.0,
                        wind_speed=8.0,
                        ndvi=0.6,
                        evi=0.5,
                        elevation=1800.0,
                        population_density=400.0,
                        data_source=f"concurrent_test_{session_id}",
                    )
                    await repo.create(data)

                await session.commit()

        # Run multiple concurrent sessions
        tasks = [create_records(i) for i in range(3)]
        await asyncio.gather(*tasks)

        # Verify all records were created
        async with async_session_maker() as session:
            result = await session.execute(
                select(func.count(EnvironmentalData.id)).where(
                    EnvironmentalData.data_source.like("concurrent_test_%")
                )
            )
            count = result.scalar()
            assert count == 15  # 3 sessions * 5 records each
