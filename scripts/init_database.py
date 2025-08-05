#!/usr/bin/env python3
"""Initialize the malaria prediction database.

This script sets up the database schema, creates tables,
and optionally loads sample data for testing.

Usage:
    python scripts/init_database.py [--drop-existing] [--sample-data]
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from malaria_predictor.database.session import (
    check_database_health,
    close_database,
    init_database,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main initialization routine."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize malaria prediction database"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before creating new ones",
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Load sample data after initialization",
    )

    args = parser.parse_args()

    try:
        # Check current database health
        logger.info("Checking database health...")
        health = await check_database_health()

        if health["connected"]:
            logger.info("✅ Database connection successful")
            if health["tables_exist"]:
                logger.warning("⚠️  Tables already exist in database")
                if not args.drop_existing:
                    logger.error("Use --drop-existing to recreate tables")
                    return 1
        else:
            logger.error(f"❌ Database connection failed: {health.get('error')}")
            return 1

        # Initialize database
        logger.info("Initializing database schema...")
        await init_database(drop_existing=args.drop_existing)

        # Verify initialization
        health = await check_database_health()
        if health["tables_exist"]:
            logger.info("✅ Database tables created successfully")

            if health["timescaledb_enabled"]:
                logger.info(
                    f"✅ TimescaleDB enabled (version {health.get('timescaledb_version')})"
                )
            else:
                logger.warning(
                    "⚠️  TimescaleDB not available - using standard PostgreSQL tables"
                )
        else:
            logger.error("❌ Table creation failed")
            return 1

        # Load sample data if requested
        if args.sample_data:
            logger.info("Loading sample data...")
            await load_sample_data()
            logger.info("✅ Sample data loaded")

        logger.info("🎉 Database initialization complete!")
        return 0

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return 1
    finally:
        await close_database()


async def load_sample_data():
    """Load sample data for testing."""
    from datetime import datetime, timedelta

    from malaria_predictor.database.repositories import (
        ERA5Repository,
        MalariaRiskRepository,
    )
    from malaria_predictor.database.session import get_session

    async with get_session() as session:
        # Insert sample ERA5 data points
        era5_repo = ERA5Repository(session)

        sample_points = []
        base_date = datetime.utcnow() - timedelta(days=7)

        # Create sample data for Kampala, Uganda
        for day in range(7):
            for hour in range(0, 24, 6):  # Every 6 hours
                timestamp = base_date + timedelta(days=day, hours=hour)
                sample_points.append(
                    {
                        "timestamp": timestamp,
                        "latitude": 0.3163,
                        "longitude": 32.5822,
                        "temperature_2m": 20.0 + 5 * (hour / 24),  # Daily variation
                        "temperature_2m_max": 25.0,
                        "temperature_2m_min": 18.0,
                        "dewpoint_2m": 15.0,
                        "total_precipitation": 5.0
                        if hour == 18
                        else 0.0,  # Evening rain
                        "file_reference": "sample_data",
                    }
                )

        await era5_repo.bulk_insert_data_points(sample_points)
        logger.info(f"Inserted {len(sample_points)} sample ERA5 data points")

        # Insert sample processed climate data
        # climate_repo = ProcessedClimateRepository(session)  # Reserved for future use

        # Insert sample risk assessment
        risk_repo = MalariaRiskRepository(session)
        risk_data = {
            "composite_score": 0.65,
            "temp_risk": 0.8,
            "precip_risk": 0.6,
            "humidity_risk": 0.5,
            "confidence": 0.85,
            "prediction_date": datetime.utcnow(),
            "time_horizon_days": 30,
            "model_type": "rule-based",
            "data_sources": ["ERA5", "sample"],
        }

        await risk_repo.save_risk_assessment(
            assessment_date=datetime.utcnow(),
            latitude=0.3163,
            longitude=32.5822,
            risk_data=risk_data,
        )
        logger.info("Inserted sample risk assessment")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
