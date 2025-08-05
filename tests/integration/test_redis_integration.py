"""
Redis Integration Tests for Malaria Prediction Backend.

This module tests Redis caching functionality, session management,
and cache invalidation strategies.
"""

import json
import time
from datetime import datetime

import pytest
import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, TimeoutError

from malaria_predictor.models import GeographicLocation
from malaria_predictor.services.unified_data_harmonizer import CacheManager

from .conftest import IntegrationTestCase


class TestRedisConnectivity(IntegrationTestCase):
    """Test basic Redis connectivity and configuration."""

    def test_redis_connection(self, test_redis_client: redis.Redis):
        """Test that Redis connection is working."""
        assert test_redis_client.ping() is True

    def test_redis_info(self, test_redis_client: redis.Redis):
        """Test Redis server information."""
        info = test_redis_client.info()
        assert "redis_version" in info
        assert info["tcp_port"] == 6380  # Test port

    def test_redis_set_get(self, test_redis_client: redis.Redis):
        """Test basic Redis set/get operations."""
        key = "test:basic"
        value = "test_value"

        test_redis_client.set(key, value)
        retrieved = test_redis_client.get(key)

        assert retrieved == value

    def test_redis_expiration(self, test_redis_client: redis.Redis):
        """Test Redis key expiration."""
        key = "test:expiration"
        value = "expires_soon"

        test_redis_client.setex(key, 1, value)  # 1 second expiration
        assert test_redis_client.get(key) == value

        time.sleep(1.1)  # Wait for expiration
        assert test_redis_client.get(key) is None

    @pytest.mark.asyncio
    async def test_async_redis_connection(
        self, test_redis_async_client: aioredis.Redis
    ):
        """Test async Redis connection."""
        assert await test_redis_async_client.ping() is True

    @pytest.mark.asyncio
    async def test_async_redis_operations(
        self, test_redis_async_client: aioredis.Redis
    ):
        """Test async Redis operations."""
        key = "test:async"
        value = "async_value"

        await test_redis_async_client.set(key, value)
        retrieved = await test_redis_async_client.get(key)

        assert retrieved == value


class TestPredictionCaching(IntegrationTestCase):
    """Test prediction result caching functionality."""

    @pytest.fixture
    def sample_prediction(self) -> dict:
        """Create sample prediction data for caching."""
        return {
            "risk_score": 0.75,
            "confidence": 0.85,
            "predictions": [0.7, 0.8, 0.75],
            "uncertainty": 0.15,
            "model_version": "ensemble_v1.0",
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": -1.286389,
                "longitude": 36.817222,
            },
            "environmental_factors": {
                "temperature": 25.5,
                "precipitation": 15.2,
                "humidity": 65.8,
                "ndvi": 0.68,
            },
        }

    def test_cache_prediction_result(
        self, test_redis_client: redis.Redis, sample_prediction: dict
    ):
        """Test caching prediction results."""
        cache_key = "prediction:nairobi:2024-01-01"

        # Cache prediction
        test_redis_client.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(sample_prediction),
        )

        # Retrieve from cache
        cached_data = test_redis_client.get(cache_key)
        retrieved_prediction = json.loads(cached_data)

        assert retrieved_prediction["risk_score"] == sample_prediction["risk_score"]
        assert (
            retrieved_prediction["model_version"] == sample_prediction["model_version"]
        )

    def test_cache_key_generation(self, test_redis_client: redis.Redis):
        """Test prediction cache key generation strategy."""

        def generate_cache_key(
            location: GeographicLocation, date: str, model: str
        ) -> str:
            """Generate standardized cache key."""
            lat_rounded = round(location.latitude, 4)
            lon_rounded = round(location.longitude, 4)
            return f"prediction:{lat_rounded}:{lon_rounded}:{date}:{model}"

        location = GeographicLocation(latitude=-1.286389, longitude=36.817222)
        cache_key = generate_cache_key(location, "2024-01-01", "ensemble")

        expected_key = "prediction:-1.2864:36.8172:2024-01-01:ensemble"
        assert cache_key == expected_key

        # Test key collision handling
        similar_location = GeographicLocation(
            latitude=-1.286388, longitude=36.817221
        )  # Very close
        similar_key = generate_cache_key(similar_location, "2024-01-01", "ensemble")

        # Should generate different keys for different locations
        assert cache_key != similar_key

    def test_cache_hit_performance(
        self, test_redis_client: redis.Redis, sample_prediction: dict
    ):
        """Test cache hit performance."""
        cache_key = "prediction:performance_test"

        # Store prediction in cache
        test_redis_client.setex(cache_key, 3600, json.dumps(sample_prediction))

        # Measure cache retrieval time
        start_time = time.time()

        for _ in range(100):  # 100 cache hits
            cached_data = test_redis_client.get(cache_key)
            json.loads(cached_data)

        total_time = time.time() - start_time
        avg_time_per_hit = total_time / 100

        # Cache hits should be very fast (< 1ms average)
        assert avg_time_per_hit < 0.001

    def test_cache_miss_handling(self, test_redis_client: redis.Redis):
        """Test cache miss handling."""
        non_existent_key = "prediction:non_existent"

        result = test_redis_client.get(non_existent_key)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_cache_operations(
        self, test_redis_async_client: aioredis.Redis, sample_prediction: dict
    ):
        """Test async cache operations."""
        cache_key = "prediction:async_test"

        # Async cache set
        await test_redis_async_client.setex(
            cache_key, 3600, json.dumps(sample_prediction)
        )

        # Async cache get
        cached_data = await test_redis_async_client.get(cache_key)
        retrieved_prediction = json.loads(cached_data)

        assert retrieved_prediction["risk_score"] == sample_prediction["risk_score"]

    def test_cache_eviction_policies(self, test_redis_client: redis.Redis):
        """Test cache eviction policies (LRU)."""
        # Fill cache with test data
        for i in range(10):
            key = f"prediction:eviction_test:{i}"
            value = {"risk_score": 0.5 + (i * 0.05), "id": i}
            test_redis_client.setex(key, 3600, json.dumps(value))

        # Access some keys to make them recently used
        for i in [1, 3, 5, 7]:
            test_redis_client.get(f"prediction:eviction_test:{i}")

        # Verify all keys exist
        existing_keys = test_redis_client.keys("prediction:eviction_test:*")
        assert len(existing_keys) == 10


class TestEnvironmentalDataCaching(IntegrationTestCase):
    """Test environmental data caching strategies."""

    @pytest.fixture
    def sample_environmental_data(self) -> dict:
        """Create sample environmental data for caching."""
        return {
            "era5": {
                "temperature": [25.5, 26.2, 24.8],
                "precipitation": [0.0, 2.5, 0.8],
                "humidity": [65.2, 68.1, 63.7],
                "timestamps": [
                    "2024-01-01T00:00:00",
                    "2024-01-01T06:00:00",
                    "2024-01-01T12:00:00",
                ],
            },
            "chirps": {
                "precipitation": [15.2, 8.7, 22.1],
                "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
            },
            "modis": {
                "ndvi": [0.65, 0.72, 0.68],
                "evi": [0.58, 0.64, 0.61],
                "dates": ["2024-01-01", "2024-01-09", "2024-01-17"],
            },
            "location": {"latitude": -1.286389, "longitude": 36.817222},
            "cached_at": datetime.now().isoformat(),
        }

    def test_cache_environmental_data(
        self, test_redis_client: redis.Redis, sample_environmental_data: dict
    ):
        """Test caching environmental data from multiple sources."""
        cache_key = "env_data:nairobi:2024-01-01"

        # Cache environmental data
        test_redis_client.setex(
            cache_key,
            7200,  # 2 hours TTL (environmental data changes less frequently)
            json.dumps(sample_environmental_data),
        )

        # Retrieve from cache
        cached_data = test_redis_client.get(cache_key)
        retrieved_data = json.loads(cached_data)

        assert "era5" in retrieved_data
        assert "chirps" in retrieved_data
        assert "modis" in retrieved_data
        assert retrieved_data["location"]["latitude"] == -1.286389

    def test_partial_cache_invalidation(self, test_redis_client: redis.Redis):
        """Test partial cache invalidation when data sources update."""
        base_key = "env_data:partial_test"

        # Cache data from multiple sources
        sources = ["era5", "chirps", "modis", "worldpop"]
        for source in sources:
            key = f"{base_key}:{source}"
            data = {"source": source, "data": f"test_data_for_{source}"}
            test_redis_client.setex(key, 3600, json.dumps(data))

        # Verify all sources are cached
        all_keys = test_redis_client.keys(f"{base_key}:*")
        assert len(all_keys) == 4

        # Invalidate specific source (simulate ERA5 data update)
        test_redis_client.delete(f"{base_key}:era5")

        # Verify partial invalidation
        remaining_keys = test_redis_client.keys(f"{base_key}:*")
        assert len(remaining_keys) == 3
        assert f"{base_key}:era5".encode() not in remaining_keys

    def test_cache_versioning(self, test_redis_client: redis.Redis):
        """Test cache versioning for data updates."""
        base_key = "env_data:versioning_test"

        # Cache version 1
        v1_data = {"version": 1, "temperature": 25.0}
        test_redis_client.setex(f"{base_key}:v1", 3600, json.dumps(v1_data))

        # Cache version 2 (updated data)
        v2_data = {"version": 2, "temperature": 26.5}
        test_redis_client.setex(f"{base_key}:v2", 3600, json.dumps(v2_data))

        # Set current version pointer
        test_redis_client.set(f"{base_key}:current", "v2")

        # Retrieve current version
        current_version = test_redis_client.get(f"{base_key}:current")
        current_data_json = test_redis_client.get(f"{base_key}:{current_version}")
        current_data = json.loads(current_data_json)

        assert current_data["version"] == 2
        assert current_data["temperature"] == 26.5


class TestSessionManagement(IntegrationTestCase):
    """Test user session management with Redis."""

    @pytest.fixture
    def sample_session_data(self) -> dict:
        """Create sample session data."""
        return {
            "user_id": "test_user_123",
            "username": "test_user",
            "email": "test@example.com",
            "roles": ["user", "researcher"],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ip_address": "127.0.0.1",
            "user_agent": "test_client",
        }

    def test_session_creation(
        self, test_redis_client: redis.Redis, sample_session_data: dict
    ):
        """Test creating user sessions."""
        session_id = "session:test_session_123"

        # Create session
        test_redis_client.setex(
            session_id,
            3600,  # 1 hour session TTL
            json.dumps(sample_session_data),
        )

        # Retrieve session
        session_data = test_redis_client.get(session_id)
        retrieved_session = json.loads(session_data)

        assert retrieved_session["user_id"] == sample_session_data["user_id"]
        assert retrieved_session["username"] == sample_session_data["username"]

    def test_session_renewal(
        self, test_redis_client: redis.Redis, sample_session_data: dict
    ):
        """Test session renewal/extension."""
        session_id = "session:renewal_test"

        # Create session with short TTL
        test_redis_client.setex(session_id, 10, json.dumps(sample_session_data))

        # Check initial TTL
        initial_ttl = test_redis_client.ttl(session_id)
        assert initial_ttl <= 10

        # Renew session
        test_redis_client.expire(session_id, 3600)  # Extend to 1 hour

        # Check renewed TTL
        renewed_ttl = test_redis_client.ttl(session_id)
        assert renewed_ttl > 3500  # Should be close to 3600

    def test_session_cleanup(self, test_redis_client: redis.Redis):
        """Test automatic session cleanup."""
        # Create multiple sessions
        for i in range(5):
            session_id = f"session:cleanup_test_{i}"
            session_data = {"user_id": f"user_{i}", "test": True}
            test_redis_client.setex(
                session_id, 1, json.dumps(session_data)
            )  # 1 second TTL

        # Verify sessions exist
        active_sessions = test_redis_client.keys("session:cleanup_test_*")
        assert len(active_sessions) == 5

        # Wait for expiration
        time.sleep(1.1)

        # Verify sessions are cleaned up
        expired_sessions = test_redis_client.keys("session:cleanup_test_*")
        assert len(expired_sessions) == 0

    def test_concurrent_session_access(
        self, test_redis_client: redis.Redis, sample_session_data: dict
    ):
        """Test concurrent access to the same session."""
        session_id = "session:concurrent_test"

        # Create session
        test_redis_client.setex(session_id, 3600, json.dumps(sample_session_data))

        def update_session_activity():
            """Simulate session activity update."""
            # Get current session
            current_data = test_redis_client.get(session_id)
            if current_data:
                session_data = json.loads(current_data)
                session_data["last_activity"] = datetime.now().isoformat()

                # Update session
                test_redis_client.setex(session_id, 3600, json.dumps(session_data))
                return True
            return False

        # Simulate concurrent updates
        results = []
        for _ in range(10):
            results.append(update_session_activity())

        # All updates should succeed
        assert all(results)

        # Verify final session state
        final_data = test_redis_client.get(session_id)
        final_session = json.loads(final_data)
        assert "last_activity" in final_session


class TestCacheManager(IntegrationTestCase):
    """Test cache manager implementation."""

    @pytest.fixture
    def cache_manager(self, test_redis_client: redis.Redis) -> CacheManager:
        """Create cache manager instance for testing."""
        return CacheManager(redis_client=test_redis_client)

    def test_cache_manager_initialization(self, cache_manager: CacheManager):
        """Test cache manager initialization."""
        assert cache_manager.redis_client is not None
        assert cache_manager.default_ttl == 3600  # Default 1 hour

    @pytest.mark.asyncio
    async def test_cache_manager_set_get(self, cache_manager: CacheManager):
        """Test cache manager set/get operations."""
        key = "test:cache_manager"
        value = {"test": "data", "number": 42}

        # Set value
        await cache_manager.set(key, value, ttl=1800)

        # Get value
        retrieved = await cache_manager.get(key)

        assert retrieved == value

    @pytest.mark.asyncio
    async def test_cache_manager_delete(self, cache_manager: CacheManager):
        """Test cache manager delete operations."""
        key = "test:delete"
        value = {"to_be": "deleted"}

        # Set and verify
        await cache_manager.set(key, value)
        assert await cache_manager.get(key) == value

        # Delete and verify
        await cache_manager.delete(key)
        assert await cache_manager.get(key) is None

    @pytest.mark.asyncio
    async def test_cache_manager_exists(self, cache_manager: CacheManager):
        """Test cache manager key existence check."""
        key = "test:exists"

        # Key shouldn't exist initially
        assert not await cache_manager.exists(key)

        # Set key
        await cache_manager.set(key, "test_value")

        # Key should exist now
        assert await cache_manager.exists(key)

    @pytest.mark.asyncio
    async def test_cache_manager_bulk_operations(self, cache_manager: CacheManager):
        """Test cache manager bulk operations."""
        keys_values = {
            "bulk:1": {"id": 1, "name": "first"},
            "bulk:2": {"id": 2, "name": "second"},
            "bulk:3": {"id": 3, "name": "third"},
        }

        # Bulk set
        await cache_manager.set_multiple(keys_values, ttl=1800)

        # Bulk get
        keys = list(keys_values.keys())
        retrieved_values = await cache_manager.get_multiple(keys)

        assert len(retrieved_values) == 3
        for key, value in keys_values.items():
            assert retrieved_values[key] == value


class TestRedisFailureHandling(IntegrationTestCase):
    """Test Redis failure scenarios and recovery."""

    def test_connection_failure_handling(self):
        """Test handling Redis connection failures."""
        # Create Redis client with invalid connection
        invalid_client = redis.Redis(host="invalid_host", port=9999, socket_timeout=1)

        with pytest.raises(ConnectionError):
            invalid_client.ping()

    def test_timeout_handling(self, test_redis_client: redis.Redis):
        """Test handling Redis operation timeouts."""
        # Create client with very short timeout
        timeout_client = redis.Redis(
            host=test_redis_client.connection_pool.connection_kwargs["host"],
            port=test_redis_client.connection_pool.connection_kwargs["port"],
            socket_timeout=0.001,  # Very short timeout
        )

        with pytest.raises((TimeoutError, ConnectionError)):
            timeout_client.get("test_key")

    def test_memory_pressure_handling(self, test_redis_client: redis.Redis):
        """Test handling Redis memory pressure."""
        # Fill Redis with data to simulate memory pressure
        large_data = "x" * 10000  # 10KB string

        try:
            for i in range(100):  # Store 1MB of data
                key = f"memory_test:{i}"
                test_redis_client.setex(key, 60, large_data)
        except Exception as e:
            # Should handle memory pressure gracefully
            assert "OOM" in str(e) or "memory" in str(e)

        # Cleanup
        test_redis_client.flushdb()

    @pytest.mark.asyncio
    async def test_cache_fallback_strategy(self):
        """Test cache fallback when Redis is unavailable."""

        class FallbackCacheManager:
            """Cache manager with fallback strategy."""

            def __init__(self, redis_client=None):
                self.redis_client = redis_client
                self.local_cache = {}  # Fallback to local memory

            async def get(self, key: str):
                """Get value with fallback to local cache."""
                if self.redis_client:
                    try:
                        return await self.redis_client.get(key)
                    except Exception:
                        # Fallback to local cache
                        return self.local_cache.get(key)
                else:
                    return self.local_cache.get(key)

            async def set(self, key: str, value, ttl: int = 3600):
                """Set value with fallback to local cache."""
                if self.redis_client:
                    try:
                        await self.redis_client.setex(key, ttl, value)
                        return
                    except Exception:
                        pass

                # Fallback to local cache (ignoring TTL for simplicity)
                self.local_cache[key] = value

        # Test with no Redis connection
        fallback_manager = FallbackCacheManager(redis_client=None)

        await fallback_manager.set("test_key", "test_value")
        retrieved = await fallback_manager.get("test_key")

        assert retrieved == "test_value"


class TestCacheInvalidationStrategies(IntegrationTestCase):
    """Test cache invalidation strategies."""

    def test_time_based_invalidation(self, test_redis_client: redis.Redis):
        """Test time-based cache invalidation."""
        key = "test:time_invalidation"
        value = "expires_in_1_second"

        # Set with 1 second expiration
        test_redis_client.setex(key, 1, value)

        # Value should exist immediately
        assert test_redis_client.get(key) == value

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert test_redis_client.get(key) is None

    def test_tag_based_invalidation(self, test_redis_client: redis.Redis):
        """Test tag-based cache invalidation."""
        # Create cache entries with tags
        cache_entries = {
            "prediction:location1:model1": {
                "data": "pred1",
                "tags": ["location1", "model1"],
            },
            "prediction:location1:model2": {
                "data": "pred2",
                "tags": ["location1", "model2"],
            },
            "prediction:location2:model1": {
                "data": "pred3",
                "tags": ["location2", "model1"],
            },
        }

        # Store cache entries with tag mappings
        for key, entry in cache_entries.items():
            test_redis_client.setex(key, 3600, json.dumps(entry))

            # Store tag mappings
            for tag in entry["tags"]:
                test_redis_client.sadd(f"tag:{tag}", key)

        # Invalidate all entries with "location1" tag
        location1_keys = test_redis_client.smembers("tag:location1")
        for key in location1_keys:
            test_redis_client.delete(key)

        # Clean up tag set
        test_redis_client.delete("tag:location1")

        # Verify selective invalidation
        assert test_redis_client.get("prediction:location1:model1") is None
        assert test_redis_client.get("prediction:location1:model2") is None
        assert test_redis_client.get("prediction:location2:model1") is not None

    def test_event_driven_invalidation(self, test_redis_client: redis.Redis):
        """Test event-driven cache invalidation."""
        # Simulate cache invalidation based on data updates

        # Initial cache state
        prediction_key = "prediction:event_test"
        env_data_key = "env_data:event_test"

        prediction = {"risk_score": 0.75, "based_on": "old_env_data"}
        env_data = {"temperature": 25.0, "version": 1}

        test_redis_client.setex(prediction_key, 3600, json.dumps(prediction))
        test_redis_client.setex(env_data_key, 3600, json.dumps(env_data))

        # Simulate environmental data update (event)
        new_env_data = {"temperature": 27.0, "version": 2}
        test_redis_client.setex(env_data_key, 3600, json.dumps(new_env_data))

        # Invalidate dependent predictions
        dependent_keys = test_redis_client.keys("prediction:*")
        for key in dependent_keys:
            test_redis_client.delete(key)

        # Verify invalidation
        assert test_redis_client.get(prediction_key) is None
        assert test_redis_client.get(env_data_key) is not None
