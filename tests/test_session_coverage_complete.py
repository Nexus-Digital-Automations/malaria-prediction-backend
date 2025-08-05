"""
Comprehensive test coverage for session.py module to achieve 100% coverage.

This module tests all database session management functions, connection pooling,
health checks, and database initialization routines.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestSessionComplete:
    """Complete test coverage for session.py module."""

    @pytest.mark.asyncio
    async def test_get_engine_testing_environment(self):
        """Test get_engine with testing configuration - covers lines 55-64."""
        from malaria_predictor.database import session

        # Reset global engine for clean test
        session._engine = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = True
            mock_settings.get_database_url.return_value = "sqlite+aiosqlite:///test.db"
            mock_settings.database.echo = False

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create_engine:
                mock_engine = AsyncMock()
                mock_create_engine.return_value = mock_engine

                result = session.get_engine()

                # Verify testing pool config was used (NullPool for testing)
                mock_create_engine.assert_called_once()
                call_args = mock_create_engine.call_args
                assert "poolclass" in call_args[1]  # NullPool for testing
                assert result == mock_engine

    @pytest.mark.asyncio
    async def test_get_engine_production_environment(self):
        """Test get_engine with production configuration - covers lines 55-64."""
        from malaria_predictor.database import session

        # Reset global engine for clean test
        session._engine = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = False
            mock_settings.get_database_url.return_value = (
                "postgresql+asyncpg://user:pass@localhost/db"
            )
            mock_settings.database.echo = True

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create_engine:
                mock_engine = AsyncMock()
                mock_create_engine.return_value = mock_engine

                result = session.get_engine()

                # Verify production pool config was used
                mock_create_engine.assert_called_once()
                call_args = mock_create_engine.call_args
                assert call_args[1]["pool_size"] == 20
                assert call_args[1]["max_overflow"] == 30
                assert call_args[1]["echo_pool"]  # Should match settings.database.echo
                assert result == mock_engine

    @pytest.mark.asyncio
    async def test_get_session_maker_creation(self):
        """Test get_session_maker creation - covers lines 90-103."""
        from malaria_predictor.database import session

        # Reset global session maker for clean test
        session._async_session_maker = None

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine

            with patch(
                "malaria_predictor.database.session.async_sessionmaker"
            ) as mock_async_sessionmaker:
                mock_session_maker = AsyncMock()
                mock_async_sessionmaker.return_value = mock_session_maker

                result = session.get_session_maker()

                # Verify session maker was created with correct parameters
                mock_async_sessionmaker.assert_called_once_with(
                    mock_engine,
                    class_=session.AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
                assert result == mock_session_maker

    @pytest.mark.asyncio
    async def test_get_session_context_manager_success(self):
        """Test get_session context manager success flow - covers lines 118-128."""
        from malaria_predictor.database.session import get_session

        # Create proper async context manager mock
        mock_session = AsyncMock()
        mock_session_maker = Mock()

        # Create a proper async context manager class
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Mock the session_maker to return our async context manager
        mock_session_maker.return_value = MockAsyncContextManager()

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            async with get_session() as session:
                assert session == mock_session
                # Verify session methods are called properly
                mock_session.commit.assert_not_called()  # Not called yet
                mock_session.rollback.assert_not_called()
                mock_session.close.assert_not_called()

            # After context exit, commit and close should be called
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_context_manager_exception(self):
        """Test get_session context manager exception handling - covers lines 123-128."""
        from malaria_predictor.database.session import get_session

        # Create proper async context manager mock
        mock_session = AsyncMock()
        mock_session_maker = Mock()

        # Create a proper async context manager class
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Mock the session_maker to return our async context manager
        mock_session_maker.return_value = MockAsyncContextManager()

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            try:
                async with get_session() as session:
                    assert session == mock_session
                    # Simulate an exception during session use
                    raise ValueError("Database error")
            except ValueError:
                pass  # Expected exception

            # After exception, rollback and close should be called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()  # Should not commit on exception

    @pytest.mark.asyncio
    async def test_get_session_with_retry_exponential_backoff(self):
        """Test get_session_with_retry with exponential backoff - covers retry delay logic."""
        from malaria_predictor.database.session import get_session_with_retry

        call_count = 0
        mock_session = AsyncMock()

        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        def mock_get_session_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two calls fail
                raise ConnectionError("Database unreachable")

            # Third call succeeds - return proper async context manager
            return MockAsyncContextManager()

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.side_effect = mock_get_session_side_effect

            with patch("asyncio.sleep") as mock_sleep:
                async with get_session_with_retry(
                    max_retries=3, retry_delay=0.1
                ) as session:
                    assert session == mock_session

                # Verify exponential backoff - first retry 0.1s, second retry 0.2s
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(0.1)
                mock_sleep.assert_any_call(0.2)

    @pytest.mark.asyncio
    async def test_init_database_drop_existing_tables(self):
        """Test init_database with drop_existing=True - covers lines 173-192."""
        from malaria_predictor.database.session import init_database

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_conn = AsyncMock()

            # Create proper async context manager for engine.begin()
            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_conn

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_engine.begin.return_value = MockAsyncContextManager()
            mock_get_engine.return_value = mock_engine

            # Mock Base metadata
            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION timescaledb;",
                ):
                    await init_database(drop_existing=True)

                    # Verify drop_all was called
                    mock_conn.run_sync.assert_any_call(mock_metadata.drop_all)
                    # Verify create_all was called
                    mock_conn.run_sync.assert_any_call(mock_metadata.create_all)
                    # Verify TimescaleDB setup was attempted
                    mock_conn.execute.assert_called()
                    mock_conn.commit.assert_called()

    @pytest.mark.asyncio
    async def test_init_database_timescaledb_setup_exception(self):
        """Test init_database with TimescaleDB setup exceptions - covers lines 182-191."""
        from malaria_predictor.database.session import init_database

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = AsyncMock()
            mock_conn = AsyncMock()

            # Create proper async context manager for engine.begin()
            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_conn

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_engine.begin.return_value = MockAsyncContextManager()
            mock_get_engine.return_value = mock_engine

            # Mock Base metadata
            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                # Make TimescaleDB setup fail
                mock_conn.execute.side_effect = Exception("TimescaleDB not available")

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION timescaledb;",
                ):
                    # Should not raise exception, just log warning
                    await init_database(drop_existing=False)

                    # Verify create_all was still called
                    mock_conn.run_sync.assert_called_with(mock_metadata.create_all)

    @pytest.mark.asyncio
    async def test_check_database_health_comprehensive_success(self):
        """Test check_database_health with all extensions available - covers lines 240-302."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_session = AsyncMock()

            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_get_session.return_value = MockAsyncContextManager()

            # Mock different query results
            def execute_side_effect(query):
                query_str = str(query)
                mock_result = Mock()

                if "SELECT 1" in query_str:
                    mock_result.scalar.return_value = 1
                elif "timescaledb_information.hypertables" in query_str:
                    mock_result.scalar.return_value = 2
                elif (
                    "COUNT(*)" in query_str and "information_schema.tables" in query_str
                ):
                    mock_result.scalar.return_value = 3
                elif "timescaledb" in query_str and "pg_extension" in query_str:
                    mock_result.scalar.return_value = "2.0.0"
                elif "postgis" in query_str and "pg_extension" in query_str:
                    mock_result.scalar.return_value = "3.1.0"
                else:
                    mock_result.scalar.return_value = None

                return mock_result

            mock_session.execute.side_effect = execute_side_effect

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool_status:
                mock_pool_status.return_value = {"pool_size": 20, "checked_out": 5}

                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = Mock()
                    mock_loop.time.side_effect = [1000.0, 1000.05]  # 50ms response time
                    mock_get_loop.return_value = mock_loop

                    result = await check_database_health()

                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is True
                    assert result["timescaledb_version"] == "2.0.0"
                    assert result["postgis_enabled"] is True
                    assert result["postgis_version"] == "3.1.0"
                    assert result["hypertables_count"] == 2
                    assert result["response_time_ms"] >= 49  # Allow for timing variance
                    assert result["error"] is None
                    assert result["connection_pool"] == {
                        "pool_size": 20,
                        "checked_out": 5,
                    }

    @pytest.mark.asyncio
    async def test_check_database_health_timescaledb_postgis_failures(self):
        """Test check_database_health with TimescaleDB/PostGIS failures - covers lines 263-302."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_session = AsyncMock()

            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_get_session.return_value = MockAsyncContextManager()

            execute_call_count = 0

            def execute_side_effect(query):
                nonlocal execute_call_count
                execute_call_count += 1
                query_str = str(query)
                mock_result = AsyncMock()

                if "SELECT 1" in query_str:
                    mock_result.scalar.return_value = 1
                elif "COUNT(*)" in query_str and "tables" in query_str:
                    mock_result.scalar.return_value = 3
                elif "timescaledb" in query_str:
                    # TimescaleDB check fails
                    raise Exception("TimescaleDB extension not found")
                elif "postgis" in query_str:
                    # PostGIS check fails
                    raise Exception("PostGIS extension not found")
                elif "hypertables" in query_str:
                    # Hypertables check fails
                    raise Exception("TimescaleDB schema not available")
                else:
                    mock_result.scalar.return_value = None

                return mock_result

            mock_session.execute.side_effect = execute_side_effect

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool_status:
                mock_pool_status.return_value = {"pool_size": None}

                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = Mock()
                    mock_loop.time.side_effect = [1000.0, 1000.1]  # 100ms response time
                    mock_get_loop.return_value = mock_loop

                    result = await check_database_health()

                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is False
                    assert "timescaledb_version" not in result
                    assert result["postgis_enabled"] is False
                    assert "postgis_version" not in result
                    assert result["hypertables_count"] == 0
                    assert result["response_time_ms"] == 100

    @pytest.mark.asyncio
    async def test_check_database_health_complete_failure(self):
        """Test check_database_health with complete database failure - covers lines 304-309."""
        from malaria_predictor.database.session import check_database_health

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            # Database connection completely fails
            mock_get_session.side_effect = Exception("Database connection failed")

            with patch("asyncio.get_event_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_loop.time.side_effect = [1000.0, 1000.5]  # 500ms response time
                mock_get_loop.return_value = mock_loop

                result = await check_database_health()

                assert result["connected"] is False
                assert result["tables_exist"] is False
                assert result["timescaledb_enabled"] is False
                assert result["postgis_enabled"] is False
                assert result["response_time_ms"] == 500
                assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_connection_pool_status_with_pool(self):
        """Test get_connection_pool_status with active pool - covers lines 201-221."""
        from malaria_predictor.database.session import get_connection_pool_status

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = Mock()

            # Mock sync_engine with pool
            mock_sync_engine = Mock()
            mock_pool = Mock()
            mock_pool.size.return_value = 20
            mock_pool.checkedin.return_value = 15
            mock_pool.checkedout.return_value = 5
            mock_pool.overflow.return_value = 3
            mock_pool.invalid.return_value = 0

            mock_sync_engine.pool = mock_pool
            mock_engine.sync_engine = mock_sync_engine
            mock_get_engine.return_value = mock_engine

            result = await get_connection_pool_status()

            assert result["pool_size"] == 20
            assert result["checked_in"] == 15
            assert result["checked_out"] == 5
            assert result["overflow"] == 3
            assert result["invalid"] == 0

    @pytest.mark.asyncio
    async def test_get_connection_pool_status_no_pool(self):
        """Test get_connection_pool_status with no pool available - covers lines 202-210."""
        from malaria_predictor.database.session import get_connection_pool_status

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = Mock()
            # No sync_engine attribute
            if hasattr(mock_engine, "sync_engine"):
                delattr(mock_engine, "sync_engine")
            mock_get_engine.return_value = mock_engine

            result = await get_connection_pool_status()

            # All values should be None when no pool is available
            assert result["pool_size"] is None
            assert result["checked_in"] is None
            assert result["checked_out"] is None
            assert result["overflow"] is None
            assert result["invalid"] is None

    @pytest.mark.asyncio
    async def test_close_database_with_engine(self):
        """Test close_database when engine exists - covers lines 317-325."""
        from malaria_predictor.database import session

        # Set up global engine
        mock_engine = AsyncMock()
        session._engine = mock_engine
        session._async_session_maker = Mock()

        await session.close_database()

        # Verify engine disposal and globals reset
        mock_engine.dispose.assert_called_once()
        assert session._engine is None
        assert session._async_session_maker is None

    @pytest.mark.asyncio
    async def test_close_database_no_engine(self):
        """Test close_database when no engine exists - covers lines 319-325."""
        from malaria_predictor.database import session

        # Ensure no engine exists
        session._engine = None
        session._async_session_maker = Mock()

        await session.close_database()

        # Should not raise exception, just reset globals
        assert session._engine is None
        assert session._async_session_maker is None

    @pytest.mark.asyncio
    async def test_run_async_function_with_args_and_kwargs(self):
        """Test run_async utility function with args and kwargs - covers lines 328-340."""
        from malaria_predictor.database.session import run_async

        def sync_function(x, y, multiplier=1):
            return (x + y) * multiplier

        with patch("asyncio.get_event_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_in_executor = AsyncMock(return_value=15)
            mock_get_loop.return_value = mock_loop

            result = await run_async(sync_function, 5, 2, multiplier=2)

            assert result == 15
            # Verify run_in_executor was called with correct parameters
            mock_loop.run_in_executor.assert_called_once_with(
                None, sync_function, 5, 2, multiplier=2
            )

    @pytest.mark.asyncio
    async def test_run_async_function_no_args(self):
        """Test run_async utility function with no additional args - covers lines 328-340."""
        from malaria_predictor.database.session import run_async

        def sync_function():
            return 42

        with patch("asyncio.get_event_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_in_executor = AsyncMock(return_value=42)
            mock_get_loop.return_value = mock_loop

            result = await run_async(sync_function)

            assert result == 42
            mock_loop.run_in_executor.assert_called_once_with(None, sync_function)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
