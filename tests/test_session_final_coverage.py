"""
Final comprehensive test coverage for session.py module to achieve 100% coverage.

This module addresses the remaining uncovered lines using proper async mocking techniques.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestSessionFinalCoverage:
    """Final test coverage for session.py module."""

    def create_async_context_manager(self, return_value):
        """Helper to create a proper async context manager mock."""

        @asynccontextmanager
        async def mock_context():
            yield return_value

        return mock_context()

    @pytest.mark.asyncio
    async def test_get_session_success_path(self):
        """Test get_session success path - covers lines 118-128."""
        from malaria_predictor.database.session import get_session

        mock_session = AsyncMock()

        # Create a proper mock session maker that returns an async context manager
        mock_session_maker = Mock()
        mock_context = self.create_async_context_manager(mock_session)
        mock_session_maker.return_value = mock_context

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            async with get_session() as session:
                assert session == mock_session

            # Verify session methods were called
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_exception_path(self):
        """Test get_session exception handling - covers lines 123-128."""
        from malaria_predictor.database.session import get_session

        mock_session = AsyncMock()

        # Create a mock session maker
        mock_session_maker = Mock()

        @asynccontextmanager
        async def mock_context():
            yield mock_session
            # This will be reached after the exception

        mock_session_maker.return_value = mock_context()

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            try:
                async with get_session() as session:
                    assert session == mock_session
                    # Raise an exception to test rollback path
                    raise ValueError("Database error")
            except ValueError:
                pass

            # Verify rollback and close were called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_with_retry_successful_retry(self):
        """Test get_session_with_retry successful after retry - covers lines 145-157."""
        from malaria_predictor.database.session import get_session_with_retry

        call_count = 0
        mock_session = AsyncMock()

        def mock_get_session():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First attempt fails")
            # Second attempt succeeds - return the async context manager directly
            return self.create_async_context_manager(mock_session)

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session_func:
            mock_get_session_func.side_effect = mock_get_session

            with patch("asyncio.sleep") as mock_sleep:
                async with get_session_with_retry(
                    max_retries=2, retry_delay=0.1
                ) as session:
                    assert session == mock_session

                # Should have slept once (after first failure)
                mock_sleep.assert_called_once_with(0.1)
                assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_session_with_retry_final_failure(self):
        """Test get_session_with_retry when all retries fail - covers lines 149-157."""
        from malaria_predictor.database.session import get_session_with_retry

        def mock_get_session():
            raise ConnectionError("Persistent failure")

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session_func:
            mock_get_session_func.side_effect = mock_get_session

            with patch("asyncio.sleep") as mock_sleep:
                with pytest.raises(ConnectionError, match="Persistent failure"):
                    async with get_session_with_retry(max_retries=1, retry_delay=0.1):
                        pass

                # Should have slept once (after first failure, before second attempt)
                mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    async def test_init_database_comprehensive(self):
        """Test init_database with comprehensive setup - covers lines 170-192."""
        from malaria_predictor.database.session import init_database

        mock_engine = AsyncMock()
        mock_conn = AsyncMock()

        # Create proper async context manager for engine.begin()
        @asynccontextmanager
        async def mock_begin():
            yield mock_conn

        mock_engine.begin = Mock(return_value=mock_begin())

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                # Mock TimescaleDB setup with multiple statements
                timescale_setup = """
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                SELECT create_hypertable('era5_data_points', 'timestamp');
                SELECT create_hypertable('chirps_data_points', 'timestamp');
                """

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    timescale_setup,
                ):
                    await init_database(drop_existing=True)

                    # Verify metadata operations
                    mock_conn.run_sync.assert_any_call(mock_metadata.drop_all)
                    mock_conn.run_sync.assert_any_call(mock_metadata.create_all)

                    # Verify TimescaleDB statements were executed
                    assert mock_conn.execute.call_count >= 3  # At least 3 statements
                    assert mock_conn.commit.call_count >= 3

    @pytest.mark.asyncio
    async def test_init_database_timescaledb_partial_failure(self):
        """Test init_database with partial TimescaleDB failures - covers lines 182-191."""
        from malaria_predictor.database.session import init_database

        mock_engine = AsyncMock()
        mock_conn = AsyncMock()

        @asynccontextmanager
        async def mock_begin():
            yield mock_conn

        mock_engine.begin = Mock(return_value=mock_begin())

        # Make some TimescaleDB commands fail
        def execute_side_effect(statement):
            if "hypertable" in str(statement):
                raise Exception("Hypertable creation failed")
            return AsyncMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                timescale_setup = """
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                SELECT create_hypertable('era5_data_points', 'timestamp');
                """

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    timescale_setup,
                ):
                    # Should not raise exception, just log warnings
                    await init_database(drop_existing=False)

                    # Verify basic operations still worked
                    mock_conn.run_sync.assert_called_once_with(mock_metadata.create_all)
                    # TimescaleDB commands were attempted but some failed
                    assert mock_conn.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_check_database_health_extensions_comprehensive(self):
        """Test check_database_health with comprehensive extension checks - covers lines 240-302."""
        from malaria_predictor.database.session import check_database_health

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        # Mock different query results based on query content
        def execute_side_effect(query):
            query_str = str(query)
            mock_result = AsyncMock()

            if "SELECT 1" in query_str:
                mock_result.scalar.return_value = 1
            elif "COUNT(*)" in query_str and "information_schema.tables" in query_str:
                mock_result.scalar.return_value = 3
            elif "timescaledb" in query_str and "pg_extension" in query_str:
                mock_result.scalar.return_value = "2.8.1"
            elif "postgis" in query_str and "pg_extension" in query_str:
                mock_result.scalar.return_value = "3.2.0"
            elif "hypertables" in query_str:
                mock_result.scalar.return_value = 2
            else:
                mock_result.scalar.return_value = None

            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session_func:
            mock_get_session_func.return_value = mock_get_session()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool_status:
                mock_pool_status.return_value = {
                    "pool_size": 20,
                    "checked_in": 15,
                    "checked_out": 5,
                    "overflow": 0,
                    "invalid": 0,
                }

                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = Mock()
                    mock_loop.time.side_effect = [
                        1000.0,
                        1000.025,
                    ]  # 25ms response time
                    mock_get_loop.return_value = mock_loop

                    result = await check_database_health()

                    # Verify all health check results
                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is True
                    assert result["timescaledb_version"] == "2.8.1"
                    assert result["postgis_enabled"] is True
                    assert result["postgis_version"] == "3.2.0"
                    assert result["hypertables_count"] == 2
                    assert result["response_time_ms"] == 25
                    assert result["error"] is None
                    assert result["connection_pool"]["pool_size"] == 20

    @pytest.mark.asyncio
    async def test_check_database_health_extension_failures(self):
        """Test check_database_health with extension check failures - covers lines 271-299."""
        from malaria_predictor.database.session import check_database_health

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        # Mock query results where extension checks fail
        def execute_side_effect(query):
            query_str = str(query)
            mock_result = AsyncMock()

            if "SELECT 1" in query_str:
                mock_result.scalar.return_value = 1
            elif "COUNT(*)" in query_str and "information_schema.tables" in query_str:
                mock_result.scalar.return_value = 3
            elif (
                "timescaledb" in query_str
                or "postgis" in query_str
                or "hypertables" in query_str
            ):
                # All extension checks fail
                raise Exception("Extension check failed")
            else:
                mock_result.scalar.return_value = None

            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session_func:
            mock_get_session_func.return_value = mock_get_session()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool_status:
                mock_pool_status.return_value = {"pool_size": None}

                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = Mock()
                    mock_loop.time.side_effect = [1000.0, 1000.1]  # 100ms response time
                    mock_get_loop.return_value = mock_loop

                    result = await check_database_health()

                    # Basic connectivity should work, but extensions should be disabled
                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is False
                    assert result["postgis_enabled"] is False
                    assert result["hypertables_count"] == 0
                    assert result["response_time_ms"] == 100
                    assert result["error"] is None

    @pytest.mark.asyncio
    async def test_check_database_health_no_tables(self):
        """Test check_database_health when tables don't exist - covers lines 252-260."""
        from malaria_predictor.database.session import check_database_health

        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        def execute_side_effect(query):
            query_str = str(query)
            mock_result = AsyncMock()

            if "SELECT 1" in query_str:
                mock_result.scalar.return_value = 1
            elif "COUNT(*)" in query_str and "information_schema.tables" in query_str:
                # No required tables exist
                mock_result.scalar.return_value = 0
            else:
                mock_result.scalar.return_value = None

            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session_func:
            mock_get_session_func.return_value = mock_get_session()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool_status:
                mock_pool_status.return_value = {"pool_size": 10}

                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = Mock()
                    mock_loop.time.side_effect = [1000.0, 1000.05]
                    mock_get_loop.return_value = mock_loop

                    result = await check_database_health()

                    assert result["connected"] is True
                    assert (
                        result["tables_exist"] is False
                    )  # Important: tables don't exist
                    assert result["response_time_ms"] == 50

    @pytest.mark.asyncio
    async def test_run_async_with_partial_function(self):
        """Test run_async with functools.partial function - covers edge case in lines 328-340."""
        import functools

        from malaria_predictor.database.session import run_async

        def sync_function(x, y, multiplier=1):
            return (x + y) * multiplier

        # Create a partial function
        partial_func = functools.partial(sync_function, multiplier=3)

        with patch("asyncio.get_event_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_in_executor = AsyncMock(return_value=21)
            mock_get_loop.return_value = mock_loop

            result = await run_async(partial_func, 5, 2)

            assert result == 21
            mock_loop.run_in_executor.assert_called_once_with(None, partial_func, 5, 2)

    @pytest.mark.asyncio
    async def test_session_module_logging_paths(self):
        """Test logging paths in session module - covers logging statements."""
        from malaria_predictor.database import session

        # Reset global state
        session._engine = None
        session._async_session_maker = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = False
            mock_settings.database_url = "postgresql+asyncpg://test"
            mock_settings.database_echo = False

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create_engine:
                mock_engine = AsyncMock()
                mock_create_engine.return_value = mock_engine

                with patch("malaria_predictor.database.session.logger") as mock_logger:
                    # Test engine creation logging
                    session.get_engine()

                    # Verify logging calls were made
                    assert mock_logger.info.call_count >= 2
                    mock_logger.info.assert_any_call(
                        "Creating database engine with production pool configuration"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
