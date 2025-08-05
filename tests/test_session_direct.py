"""
Direct integration tests for session.py to achieve 100% coverage.

These tests use minimal mocking and direct function calls to cover remaining lines.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestSessionDirect:
    """Direct tests for session.py functions with minimal mocking."""

    def test_get_engine_global_caching(self):
        """Test that get_engine caches the engine globally."""
        from malaria_predictor.database import session

        # Start with clean state
        session._engine = None

        with patch("malaria_predictor.database.session.settings") as mock_settings:
            mock_settings.testing = True
            mock_settings.database_url = "sqlite+aiosqlite:///test.db"
            mock_settings.database_echo = False

            with patch(
                "malaria_predictor.database.session.create_async_engine"
            ) as mock_create:
                mock_engine = Mock()
                mock_create.return_value = mock_engine

                # First call should create engine
                result1 = session.get_engine()
                assert result1 == mock_engine
                assert mock_create.call_count == 1

                # Second call should return cached engine
                result2 = session.get_engine()
                assert result2 == mock_engine
                assert mock_create.call_count == 1  # No additional calls

    def test_get_session_maker_global_caching(self):
        """Test that get_session_maker caches the session maker globally."""
        from malaria_predictor.database import session

        # Start with clean state
        session._async_session_maker = None

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            with patch(
                "malaria_predictor.database.session.async_sessionmaker"
            ) as mock_sessionmaker:
                mock_session_maker = Mock()
                mock_sessionmaker.return_value = mock_session_maker

                # First call should create session maker
                result1 = session.get_session_maker()
                assert result1 == mock_session_maker
                assert mock_sessionmaker.call_count == 1

                # Second call should return cached session maker
                result2 = session.get_session_maker()
                assert result2 == mock_session_maker
                assert mock_sessionmaker.call_count == 1  # No additional calls

    @pytest.mark.asyncio
    async def test_get_session_direct_with_proper_mock(self):
        """Test get_session function with proper async context manager mock."""
        from malaria_predictor.database.session import get_session

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Create a mock session maker that returns a properly configured async context manager
        class MockAsyncSession:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_session_maker = Mock()
        mock_session_maker.return_value = MockAsyncSession()

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            # Test successful path
            async with get_session() as session:
                assert session == mock_session

            # Verify commit and close were called
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_exception_handling(self):
        """Test get_session exception handling path."""
        from malaria_predictor.database.session import get_session

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Create a mock session maker that returns a properly configured async context manager
        class MockAsyncSession:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_session_maker = Mock()
        mock_session_maker.return_value = MockAsyncSession()

        with patch(
            "malaria_predictor.database.session.get_session_maker"
        ) as mock_get_maker:
            mock_get_maker.return_value = mock_session_maker

            # Test exception path
            try:
                async with get_session() as session:
                    assert session == mock_session
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Verify rollback and close were called, not commit
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_database_direct_with_proper_mock(self):
        """Test init_database function with proper async context manager."""
        from malaria_predictor.database.session import init_database

        # Create a mock connection
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        # Create a mock engine with proper async context manager
        class MockAsyncEngine:
            async def __aenter__(self):
                return mock_conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_engine = Mock()
        mock_engine.begin.return_value = MockAsyncEngine()

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION timescaledb;",
                ):
                    # Test drop_existing=False
                    await init_database(drop_existing=False)

                    # Verify create_all was called but not drop_all
                    mock_conn.run_sync.assert_called_with(mock_metadata.create_all)
                    mock_conn.execute.assert_called()
                    mock_conn.commit.assert_called()

    @pytest.mark.asyncio
    async def test_init_database_with_drop_existing(self):
        """Test init_database with drop_existing=True."""
        from malaria_predictor.database.session import init_database

        # Create a mock connection
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        # Create a mock engine with proper async context manager
        class MockAsyncEngine:
            async def __aenter__(self):
                return mock_conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_engine = Mock()
        mock_engine.begin.return_value = MockAsyncEngine()

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION timescaledb;",
                ):
                    # Test drop_existing=True
                    await init_database(drop_existing=True)

                    # Verify both drop_all and create_all were called
                    mock_conn.run_sync.assert_any_call(mock_metadata.drop_all)
                    mock_conn.run_sync.assert_any_call(mock_metadata.create_all)

    @pytest.mark.asyncio
    async def test_check_database_health_direct(self):
        """Test check_database_health with direct mocking."""
        from malaria_predictor.database.session import check_database_health

        # Create a mock session
        mock_session = AsyncMock()

        # Mock query results
        def mock_execute(query):
            result = Mock()  # Use Mock instead of AsyncMock for result
            query_str = str(query)
            if "SELECT 1" in query_str:
                result.scalar.return_value = 1
            elif "COUNT(*)" in query_str:
                result.scalar.return_value = 3
            elif "timescaledb" in query_str:
                result.scalar.return_value = "2.8.1"
            elif "postgis" in query_str:
                result.scalar.return_value = "3.2.0"
            elif "hypertables" in query_str:
                result.scalar.return_value = 2
            return result

        mock_session.execute.side_effect = mock_execute

        # Create proper async context manager
        class MockGetSession:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.return_value = MockGetSession()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool:
                mock_pool.return_value = {"pool_size": 20}

                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_event_loop = Mock()
                    mock_event_loop.time.side_effect = [1000.0, 1000.1]
                    mock_loop.return_value = mock_event_loop

                    result = await check_database_health()

                    # Verify comprehensive health check results
                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is True
                    assert result["timescaledb_version"] == "2.8.1"
                    assert result["postgis_enabled"] is True
                    assert result["postgis_version"] == "3.2.0"
                    assert result["hypertables_count"] == 2
                    assert result["response_time_ms"] == 100

    @pytest.mark.asyncio
    async def test_check_database_health_extension_failures(self):
        """Test check_database_health with extension check failures."""
        from malaria_predictor.database.session import check_database_health

        # Create a mock session
        mock_session = AsyncMock()

        # Mock query results where extensions fail
        def mock_execute(query):
            result = Mock()  # Use Mock instead of AsyncMock for result
            query_str = str(query)
            if "SELECT 1" in query_str:
                result.scalar.return_value = 1
            elif "COUNT(*)" in query_str:
                result.scalar.return_value = 3
            elif (
                "timescaledb" in query_str
                or "postgis" in query_str
                or "hypertables" in query_str
            ):
                raise Exception("Extension not available")
            return result

        mock_session.execute.side_effect = mock_execute

        # Create proper async context manager
        class MockGetSession:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.return_value = MockGetSession()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool:
                mock_pool.return_value = {"pool_size": None}

                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_event_loop = Mock()
                    mock_event_loop.time.side_effect = [1000.0, 1000.05]
                    mock_loop.return_value = mock_event_loop

                    result = await check_database_health()

                    # Basic connectivity should work, extensions should be disabled
                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is False
                    assert result["postgis_enabled"] is False
                    assert result["hypertables_count"] == 0

    @pytest.mark.asyncio
    async def test_run_async_direct(self):
        """Test run_async function directly."""
        from malaria_predictor.database.session import run_async

        def sync_function(x, y=10):
            return x + y

        result = await run_async(sync_function, 5)
        assert result == 15

    @pytest.mark.asyncio
    async def test_init_database_timescaledb_exception_handling(self):
        """Test init_database TimescaleDB exception handling - covers lines 187-189."""
        from malaria_predictor.database.session import init_database

        # Create a mock connection
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        # Make TimescaleDB execute fail
        mock_conn.execute.side_effect = Exception("TimescaleDB extension not available")
        mock_conn.commit = AsyncMock()

        # Create a mock engine with proper async context manager
        class MockAsyncEngine:
            async def __aenter__(self):
                return mock_conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_engine = Mock()
        mock_engine.begin.return_value = MockAsyncEngine()

        with patch("malaria_predictor.database.session.get_engine") as mock_get_engine:
            mock_get_engine.return_value = mock_engine

            with patch("malaria_predictor.database.session.Base") as mock_base:
                mock_metadata = Mock()
                mock_base.metadata = mock_metadata

                with patch(
                    "malaria_predictor.database.session.TIMESCALEDB_SETUP",
                    "CREATE EXTENSION timescaledb;",
                ):
                    with patch(
                        "malaria_predictor.database.session.logger"
                    ) as mock_logger:
                        # Should not raise exception, just log warning
                        await init_database(drop_existing=False)

                        # Verify warning was logged
                        mock_logger.warning.assert_called_with(
                            "TimescaleDB setup warning: TimescaleDB extension not available"
                        )
                        # Verify create_all was still called
                        mock_conn.run_sync.assert_called_with(mock_metadata.create_all)

    @pytest.mark.asyncio
    async def test_check_database_health_hypertables_exception(self):
        """Test check_database_health hypertables exception handling - covers lines 298-299."""
        from malaria_predictor.database.session import check_database_health

        # Create a mock session
        mock_session = AsyncMock()

        # Mock query results where hypertables query fails
        def mock_execute(query):
            result = Mock()
            query_str = str(query)
            if "SELECT 1" in query_str:
                result.scalar.return_value = 1
            elif "COUNT(*)" in query_str and "tables" in query_str:
                result.scalar.return_value = 3
            elif "timescaledb" in query_str:
                result.scalar.return_value = "2.8.1"
            elif "postgis" in query_str:
                result.scalar.return_value = "3.2.0"
            elif "hypertables" in query_str:
                # This specific query should fail
                raise Exception("Hypertables query failed")
            return result

        mock_session.execute.side_effect = mock_execute

        # Create proper async context manager
        class MockGetSession:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        with patch(
            "malaria_predictor.database.session.get_session"
        ) as mock_get_session:
            mock_get_session.return_value = MockGetSession()

            with patch(
                "malaria_predictor.database.session.get_connection_pool_status"
            ) as mock_pool:
                mock_pool.return_value = {"pool_size": 20}

                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_event_loop = Mock()
                    mock_event_loop.time.side_effect = [1000.0, 1000.05]
                    mock_loop.return_value = mock_event_loop

                    result = await check_database_health()

                    # Verify that hypertables_count is set to 0 when exception occurs
                    assert result["connected"] is True
                    assert result["tables_exist"] is True
                    assert result["timescaledb_enabled"] is True
                    assert result["timescaledb_version"] == "2.8.1"
                    assert result["postgis_enabled"] is True
                    assert result["postgis_version"] == "3.2.0"
                    assert (
                        result["hypertables_count"] == 0
                    )  # Should be 0 due to exception


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
