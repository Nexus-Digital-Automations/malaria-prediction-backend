"""Database session management and initialization.

This module handles database connections, session management,
and initialization routines for the malaria prediction system.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ..config import settings
from .models import TIMESCALEDB_SETUP, Base

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None

# Connection pool configuration for production
PRODUCTION_POOL_CONFIG = {
    "pool_size": 20,  # Base number of connections to maintain
    "max_overflow": 30,  # Additional connections beyond pool_size
    "pool_timeout": 30,  # Timeout when getting connection from pool
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Validate connections before use
}

TESTING_POOL_CONFIG = {
    "poolclass": NullPool,  # No connection pooling for tests
}


def get_engine() -> AsyncEngine:
    """Get or create the database engine with optimized connection pooling.

    Returns:
        Async SQLAlchemy engine with production-grade connection pooling
    """
    global _engine

    if _engine is None:
        # Choose pool configuration based on environment
        if settings.testing:
            pool_config = TESTING_POOL_CONFIG.copy()
            logger.info("Creating database engine with testing pool configuration")
        else:
            pool_config = PRODUCTION_POOL_CONFIG.copy()
            logger.info("Creating database engine with production pool configuration")

        # Create engine with enhanced async support and connection pooling
        _engine = create_async_engine(
            settings.get_database_url(),
            echo=settings.database.echo,
            **pool_config,
            # Additional async-specific settings
            future=True,  # Use SQLAlchemy 2.0 style
            echo_pool=settings.database.echo,  # Log pool events if echo is enabled
        )

        logger.info(
            f"Database engine created with pool_size={pool_config.get('pool_size', 'default')}, "
            f"max_overflow={pool_config.get('max_overflow', 'default')}"
        )

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker.

    Returns:
        Async session maker instance
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Session maker created")

    return _async_session_maker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic transaction management.

    Yields:
        AsyncSession instance with automatic commit/rollback

    Example:
        async with get_session() as session:
            result = await session.execute(select(ERA5DataPoint))
            data_points = result.scalars().all()
    """
    async_session_maker = get_session_maker()
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error, rolling back: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_with_retry(
    max_retries: int = 3, retry_delay: float = 0.5
) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with automatic retry on connection failures.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Yields:
        AsyncSession instance with retry logic
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            async with get_session() as session:
                yield session
                return
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"Database connection failed after {max_retries + 1} attempts"
                )
                raise last_exception from e


async def init_database(drop_existing: bool = False) -> None:
    """Initialize the database schema.

    Args:
        drop_existing: Whether to drop existing tables before creation

    Note:
        This function should be called once during application startup
        or when setting up the database for the first time.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        if drop_existing:
            logger.warning("Dropping all existing tables")
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Creating database tables")
        await conn.run_sync(Base.metadata.create_all)

        # Set up TimescaleDB extensions and hypertables
        logger.info("Setting up TimescaleDB")
        for statement in TIMESCALEDB_SETUP.strip().split(";"):
            if statement.strip():
                try:
                    await conn.execute(text(statement))
                    await conn.commit()
                except Exception as e:
                    # TimescaleDB might not be installed in all environments
                    logger.warning(f"TimescaleDB setup warning: {e}")
                    # Continue anyway - tables will work as regular PostgreSQL tables

        logger.info("Database initialization complete")


async def get_connection_pool_status() -> dict:
    """Get detailed connection pool status for monitoring.

    Returns:
        Dictionary with connection pool metrics
    """
    engine = get_engine()
    pool = engine.sync_engine.pool if hasattr(engine, "sync_engine") else None

    pool_status = {
        "pool_size": None,
        "checked_in": None,
        "checked_out": None,
        "overflow": None,
        "invalid": None,
    }

    if pool:
        pool_status.update(
            {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
        )

    return pool_status


async def check_database_health() -> dict:
    """Check database connectivity and health with detailed metrics.

    Returns:
        Dictionary with comprehensive health check results
    """
    health_status = {
        "connected": False,
        "tables_exist": False,
        "timescaledb_enabled": False,
        "postgis_enabled": False,
        "connection_pool": {},
        "response_time_ms": None,
        "error": None,
    }

    start_time = asyncio.get_event_loop().time()

    try:
        async with get_session() as session:
            # Check basic connectivity
            result = await session.execute(text("SELECT 1"))
            health_status["connected"] = result.scalar() == 1

            # Calculate response time
            health_status["response_time_ms"] = int(
                (asyncio.get_event_loop().time() - start_time) * 1000
            )

            # Check if tables exist
            result = await session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('era5_data_points', 'chirps_data_points', 'processed_climate_data')
                """
                )
            )
            health_status["tables_exist"] = result.scalar() >= 3

            # Check TimescaleDB
            try:
                result = await session.execute(
                    text(
                        "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                )
                version = result.scalar()
                health_status["timescaledb_enabled"] = version is not None
                if version:
                    health_status["timescaledb_version"] = version
            except Exception:
                # TimescaleDB check failed, but that's okay
                pass

            # Check PostGIS
            try:
                result = await session.execute(
                    text(
                        "SELECT extversion FROM pg_extension WHERE extname = 'postgis'"
                    )
                )
                version = result.scalar()
                health_status["postgis_enabled"] = version is not None
                if version:
                    health_status["postgis_version"] = version
            except Exception:
                # PostGIS check failed, but that's okay
                pass

            # Check hypertables
            try:
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM timescaledb_information.hypertables
                        WHERE hypertable_name IN ('era5_data_points', 'chirps_data_points')
                    """
                    )
                )
                health_status["hypertables_count"] = result.scalar()
            except Exception:
                health_status["hypertables_count"] = 0

        # Get connection pool status
        health_status["connection_pool"] = await get_connection_pool_status()

    except Exception as e:
        health_status["error"] = str(e)
        health_status["response_time_ms"] = int(
            (asyncio.get_event_loop().time() - start_time) * 1000
        )
        logger.error(f"Database health check failed: {e}")

    return health_status


async def close_database() -> None:
    """Close database connections and cleanup.

    Should be called during application shutdown.
    """
    global _engine, _async_session_maker

    if _engine:
        await _engine.dispose()
        logger.info("Database engine disposed")
        _engine = None

    _async_session_maker = None


# Utility function for running sync operations in async context
async def get_database_session() -> AsyncSession:
    """Get a new database session for notification system compatibility.

    Note: This function creates a new session that must be manually closed.
    Prefer using get_session() async context manager when possible.

    Returns:
        AsyncSession instance that must be manually closed
    """
    async_session_maker = get_session_maker()
    return async_session_maker()


# Utility function for running sync operations in async context
async def run_async(func, *args, **kwargs):
    """Run a synchronous function in an async context.

    Args:
        func: Synchronous function to run
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function result
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)
