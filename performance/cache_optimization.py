"""
Redis Caching Optimization for Malaria Prediction API.

This module provides comprehensive caching strategies for ML models,
environmental data, and frequently accessed query results to improve
API performance and reduce database load.
"""

import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache optimization settings."""

    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_mb: int = 512
    eviction_policy: str = "allkeys-lru"

    # Cache namespace prefixes
    model_cache_prefix: str = "malaria:model:"
    prediction_cache_prefix: str = "malaria:prediction:"
    environmental_cache_prefix: str = "malaria:env:"
    spatial_cache_prefix: str = "malaria:spatial:"

    # TTL settings for different data types
    model_ttl: int = 86400 * 7  # 7 days for ML models
    prediction_ttl: int = 3600 * 6  # 6 hours for predictions
    environmental_ttl: int = 3600 * 24  # 24 hours for environmental data
    spatial_ttl: int = 3600 * 12  # 12 hours for spatial data

    # Performance settings
    compression_enabled: bool = True
    pipeline_batch_size: int = 100
    connection_pool_size: int = 20


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hit_count: int = 0
    miss_count: int = 0
    set_count: int = 0
    delete_count: int = 0
    error_count: int = 0
    total_size_mb: float = 0
    avg_response_time_ms: float = 0


class CacheOptimizer:
    """Comprehensive Redis caching optimization system."""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        self.metrics = CacheMetrics()
        self._connection_pool = None

        # Cache key patterns for different data types
        self.key_patterns = {
            "model": f"{self.config.model_cache_prefix}{{model_type}}:{{version}}",
            "prediction": f"{self.config.prediction_cache_prefix}{{lat}}:{{lon}}:{{date}}:{{model}}",
            "environmental": f"{self.config.environmental_cache_prefix}{{source}}:{{lat}}:{{lon}}:{{date}}",
            "spatial": f"{self.config.spatial_cache_prefix}{{bounds_hash}}:{{date}}:{{resolution}}",
            "batch": f"{self.config.prediction_cache_prefix}batch:{{request_hash}}",
            "timeseries": f"{self.config.prediction_cache_prefix}timeseries:{{lat}}:{{lon}}:{{range_hash}}",
        }

    async def initialize(self) -> bool:
        """Initialize Redis connection and configure cache settings."""
        try:
            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=self.config.connection_pool_size,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            # Create Redis client
            self.redis_client = Redis(
                connection_pool=self._connection_pool,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding ourselves for binary data
            )

            # Test connection
            await self.redis_client.ping()

            # Configure Redis settings
            await self._configure_redis()

            logger.info("Redis cache optimizer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            return False

    async def _configure_redis(self):
        """Configure Redis settings for optimal performance."""
        try:
            # Set memory policy
            await self.redis_client.config_set(
                "maxmemory-policy", self.config.eviction_policy
            )

            # Set maximum memory
            max_memory_bytes = self.config.max_memory_mb * 1024 * 1024
            await self.redis_client.config_set("maxmemory", str(max_memory_bytes))

            # Configure persistence settings for performance
            await self.redis_client.config_set("save", "")  # Disable RDB snapshots
            await self.redis_client.config_set("appendonly", "no")  # Disable AOF

            logger.info(
                f"Redis configured: {self.config.max_memory_mb}MB max memory, {self.config.eviction_policy} eviction"
            )

        except Exception as e:
            logger.warning(f"Could not configure Redis settings: {e}")

    def _generate_cache_key(self, pattern_name: str, **kwargs) -> str:
        """Generate cache key from pattern and parameters."""
        pattern = self.key_patterns.get(pattern_name, "malaria:unknown:{hash}")

        # Replace placeholders with actual values
        try:
            return pattern.format(**kwargs)
        except KeyError:
            # Fallback to hash-based key if formatting fails
            key_data = json.dumps(kwargs, sort_keys=True)
            key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
            return f"malaria:{pattern_name}:{key_hash}"

    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for cache storage with optional compression."""
        try:
            if self.config.compression_enabled:
                # Use pickle for complex objects, JSON for simple ones
                if isinstance(data, dict | list | str | int | float | bool):
                    serialized = json.dumps(data).encode()
                else:
                    serialized = pickle.dumps(data)

                # Simple compression using zlib
                import zlib

                return zlib.compress(serialized)
            else:
                if isinstance(data, dict | list | str | int | float | bool):
                    return json.dumps(data).encode()
                else:
                    return pickle.dumps(data)

        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise

    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from cache storage."""
        try:
            if self.config.compression_enabled:
                import zlib

                decompressed = zlib.decompress(data)

                # Try JSON first, fall back to pickle
                try:
                    return json.loads(decompressed.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return pickle.loads(decompressed)
            else:
                # Try JSON first, fall back to pickle
                try:
                    return json.loads(data.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return pickle.loads(data)

        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise

    async def cache_model(
        self, model_type: str, model_version: str, model_data: Any
    ) -> bool:
        """Cache ML model data with long TTL."""
        key = self._generate_cache_key(
            "model", model_type=model_type, version=model_version
        )

        try:
            start_time = time.time()

            serialized_data = self._serialize_data(model_data)

            # Use pipeline for atomic operation
            async with self.redis_client.pipeline() as pipe:
                await pipe.set(key, serialized_data, ex=self.config.model_ttl)
                await pipe.execute()

            self.metrics.set_count += 1
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time_ms = (
                self.metrics.avg_response_time_ms * (self.metrics.set_count - 1)
                + response_time
            ) / self.metrics.set_count

            logger.debug(
                f"Cached model {model_type}:{model_version} in {response_time:.2f}ms"
            )
            return True

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to cache model {model_type}:{model_version}: {e}")
            return False

    async def get_cached_model(self, model_type: str, model_version: str) -> Any | None:
        """Retrieve cached ML model data."""
        key = self._generate_cache_key(
            "model", model_type=model_type, version=model_version
        )

        try:
            start_time = time.time()

            data = await self.redis_client.get(key)
            response_time = (time.time() - start_time) * 1000

            if data:
                self.metrics.hit_count += 1
                deserialized = self._deserialize_data(data)
                logger.debug(
                    f"Cache hit for model {model_type}:{model_version} in {response_time:.2f}ms"
                )
                return deserialized
            else:
                self.metrics.miss_count += 1
                logger.debug(f"Cache miss for model {model_type}:{model_version}")
                return None

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(
                f"Failed to get cached model {model_type}:{model_version}: {e}"
            )
            return None

    async def cache_prediction(
        self,
        latitude: float,
        longitude: float,
        target_date: str,
        model_type: str,
        prediction_result: dict,
    ) -> bool:
        """Cache prediction result for specific location and parameters."""
        key = self._generate_cache_key(
            "prediction",
            lat=f"{latitude:.4f}",
            lon=f"{longitude:.4f}",
            date=target_date,
            model=model_type,
        )

        try:
            # Add metadata to cached prediction
            cache_data = {
                "prediction": prediction_result,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "1.0",
            }

            serialized_data = self._serialize_data(cache_data)

            await self.redis_client.set(
                key, serialized_data, ex=self.config.prediction_ttl
            )
            self.metrics.set_count += 1

            logger.debug(
                f"Cached prediction for {latitude},{longitude} on {target_date}"
            )
            return True

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to cache prediction: {e}")
            return False

    async def get_cached_prediction(
        self, latitude: float, longitude: float, target_date: str, model_type: str
    ) -> dict | None:
        """Retrieve cached prediction result."""
        key = self._generate_cache_key(
            "prediction",
            lat=f"{latitude:.4f}",
            lon=f"{longitude:.4f}",
            date=target_date,
            model=model_type,
        )

        try:
            data = await self.redis_client.get(key)

            if data:
                self.metrics.hit_count += 1
                cache_data = self._deserialize_data(data)

                # Check if cached data is still valid
                cached_at = datetime.fromisoformat(cache_data["cached_at"])
                if datetime.utcnow() - cached_at < timedelta(
                    seconds=self.config.prediction_ttl
                ):
                    logger.debug(
                        f"Cache hit for prediction {latitude},{longitude} on {target_date}"
                    )
                    return cache_data["prediction"]
                else:
                    # Data expired, remove from cache
                    await self.redis_client.delete(key)

            self.metrics.miss_count += 1
            return None

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to get cached prediction: {e}")
            return None

    async def cache_environmental_data(
        self, source: str, latitude: float, longitude: float, date: str, data: dict
    ) -> bool:
        """Cache environmental data (ERA5, CHIRPS, etc.)."""
        key = self._generate_cache_key(
            "environmental",
            source=source,
            lat=f"{latitude:.4f}",
            lon=f"{longitude:.4f}",
            date=date,
        )

        try:
            cache_data = {
                "data": data,
                "cached_at": datetime.utcnow().isoformat(),
                "source": source,
            }

            serialized_data = self._serialize_data(cache_data)
            await self.redis_client.set(
                key, serialized_data, ex=self.config.environmental_ttl
            )
            self.metrics.set_count += 1

            return True

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to cache environmental data: {e}")
            return False

    async def get_cached_environmental_data(
        self, source: str, latitude: float, longitude: float, date: str
    ) -> dict | None:
        """Retrieve cached environmental data."""
        key = self._generate_cache_key(
            "environmental",
            source=source,
            lat=f"{latitude:.4f}",
            lon=f"{longitude:.4f}",
            date=date,
        )

        try:
            data = await self.redis_client.get(key)

            if data:
                self.metrics.hit_count += 1
                cache_data = self._deserialize_data(data)
                return cache_data["data"]
            else:
                self.metrics.miss_count += 1
                return None

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to get cached environmental data: {e}")
            return None

    async def cache_batch_prediction(
        self, request_hash: str, batch_results: dict
    ) -> bool:
        """Cache batch prediction results."""
        key = self._generate_cache_key("batch", request_hash=request_hash)

        try:
            cache_data = {
                "results": batch_results,
                "cached_at": datetime.utcnow().isoformat(),
                "result_count": len(batch_results.get("predictions", [])),
            }

            serialized_data = self._serialize_data(cache_data)
            await self.redis_client.set(
                key, serialized_data, ex=self.config.prediction_ttl
            )
            self.metrics.set_count += 1

            return True

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to cache batch prediction: {e}")
            return False

    async def get_cached_batch_prediction(self, request_hash: str) -> dict | None:
        """Retrieve cached batch prediction results."""
        key = self._generate_cache_key("batch", request_hash=request_hash)

        try:
            data = await self.redis_client.get(key)

            if data:
                self.metrics.hit_count += 1
                cache_data = self._deserialize_data(data)
                return cache_data["results"]
            else:
                self.metrics.miss_count += 1
                return None

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to get cached batch prediction: {e}")
            return None

    async def cache_spatial_grid(
        self, bounds_hash: str, date: str, resolution: float, grid_data: dict
    ) -> bool:
        """Cache spatial grid prediction results."""
        key = self._generate_cache_key(
            "spatial",
            bounds_hash=bounds_hash,
            date=date,
            resolution=f"{resolution:.2f}",
        )

        try:
            cache_data = {
                "grid_data": grid_data,
                "cached_at": datetime.utcnow().isoformat(),
                "point_count": len(grid_data.get("predictions", [])),
            }

            serialized_data = self._serialize_data(cache_data)
            await self.redis_client.set(
                key, serialized_data, ex=self.config.spatial_ttl
            )
            self.metrics.set_count += 1

            return True

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to cache spatial grid: {e}")
            return False

    async def get_cached_spatial_grid(
        self, bounds_hash: str, date: str, resolution: float
    ) -> dict | None:
        """Retrieve cached spatial grid results."""
        key = self._generate_cache_key(
            "spatial",
            bounds_hash=bounds_hash,
            date=date,
            resolution=f"{resolution:.2f}",
        )

        try:
            data = await self.redis_client.get(key)

            if data:
                self.metrics.hit_count += 1
                cache_data = self._deserialize_data(data)
                return cache_data["grid_data"]
            else:
                self.metrics.miss_count += 1
                return None

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to get cached spatial grid: {e}")
            return None

    async def batch_cache_operations(
        self, operations: list[tuple[str, str, Any, int]]
    ) -> dict:
        """Perform multiple cache operations in a single pipeline."""
        results = {"success": 0, "failed": 0, "errors": []}

        try:
            async with self.redis_client.pipeline() as pipe:
                for operation, key, data, ttl in operations:
                    if operation == "set":
                        serialized_data = self._serialize_data(data)
                        await pipe.set(key, serialized_data, ex=ttl)
                    elif operation == "get":
                        await pipe.get(key)
                    elif operation == "delete":
                        await pipe.delete(key)

                pipeline_results = await pipe.execute()

                for _i, result in enumerate(pipeline_results):
                    if result is not None:
                        results["success"] += 1
                    else:
                        results["failed"] += 1

        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Batch cache operation failed: {e}")

        return results

    async def get_cache_statistics(self) -> dict:
        """Get comprehensive cache performance statistics."""
        try:
            # Get Redis info
            redis_info = await self.redis_client.info()

            # Calculate hit/miss rates
            total_requests = self.metrics.hit_count + self.metrics.miss_count
            hit_rate = (
                self.metrics.hit_count / total_requests if total_requests > 0 else 0
            )
            miss_rate = (
                self.metrics.miss_count / total_requests if total_requests > 0 else 0
            )

            # Get memory usage
            used_memory_mb = redis_info.get("used_memory", 0) / (1024 * 1024)
            max_memory_mb = redis_info.get("maxmemory", 0) / (1024 * 1024)

            statistics = {
                "performance_metrics": {
                    "hit_count": self.metrics.hit_count,
                    "miss_count": self.metrics.miss_count,
                    "hit_rate": hit_rate,
                    "miss_rate": miss_rate,
                    "set_operations": self.metrics.set_count,
                    "delete_operations": self.metrics.delete_count,
                    "error_count": self.metrics.error_count,
                    "avg_response_time_ms": self.metrics.avg_response_time_ms,
                },
                "memory_usage": {
                    "used_memory_mb": used_memory_mb,
                    "max_memory_mb": max_memory_mb,
                    "memory_utilization": used_memory_mb / max_memory_mb
                    if max_memory_mb > 0
                    else 0,
                    "evicted_keys": redis_info.get("evicted_keys", 0),
                    "expired_keys": redis_info.get("expired_keys", 0),
                },
                "connection_info": {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "total_connections_received": redis_info.get(
                        "total_connections_received", 0
                    ),
                    "rejected_connections": redis_info.get("rejected_connections", 0),
                },
                "key_statistics": await self._get_key_statistics(),
                "configuration": {
                    "maxmemory_policy": redis_info.get("maxmemory_policy", "unknown"),
                    "redis_version": redis_info.get("redis_version", "unknown"),
                    "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                },
            }

            return statistics

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {"error": str(e)}

    async def _get_key_statistics(self) -> dict:
        """Get statistics about cached keys by type."""
        key_stats = {"total_keys": 0, "by_type": {}}

        try:
            # Get all keys (be careful in production)
            all_keys = await self.redis_client.keys("malaria:*")
            key_stats["total_keys"] = len(all_keys)

            # Count by type
            for key in all_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                key_type = key_str.split(":")[1] if ":" in key_str else "unknown"

                if key_type not in key_stats["by_type"]:
                    key_stats["by_type"][key_type] = 0
                key_stats["by_type"][key_type] += 1

        except Exception as e:
            logger.error(f"Failed to get key statistics: {e}")

        return key_stats

    async def optimize_cache_performance(self) -> dict:
        """Analyze and optimize cache performance."""
        recommendations = []
        optimizations_applied = []

        try:
            stats = await self.get_cache_statistics()

            # Analyze hit rate
            hit_rate = stats.get("performance_metrics", {}).get("hit_rate", 0)
            if hit_rate < 0.7:  # Less than 70% hit rate
                recommendations.append(
                    f"Low cache hit rate ({hit_rate:.2%}). Consider increasing TTL "
                    "for frequently accessed data or reviewing cache keys"
                )

            # Analyze memory usage
            memory_util = stats.get("memory_usage", {}).get("memory_utilization", 0)
            if memory_util > 0.9:  # Over 90% memory usage
                recommendations.append(
                    f"High memory utilization ({memory_util:.1%}). "
                    "Consider increasing max memory or optimizing data size"
                )

            # Analyze evictions
            evicted_keys = stats.get("memory_usage", {}).get("evicted_keys", 0)
            if evicted_keys > 1000:
                recommendations.append(
                    f"High number of evicted keys ({evicted_keys}). "
                    "Consider increasing memory or reducing TTL for less critical data"
                )

            # Apply automatic optimizations
            if memory_util > 0.95:
                # Emergency: Clear some old cached data
                cleared = await self._emergency_cache_cleanup()
                optimizations_applied.append(
                    f"Emergency cleanup: cleared {cleared} old entries"
                )

            return {
                "current_performance": stats,
                "recommendations": recommendations,
                "optimizations_applied": optimizations_applied,
                "next_review_time": (
                    datetime.utcnow() + timedelta(hours=1)
                ).isoformat(),
            }

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"error": str(e)}

    async def _emergency_cache_cleanup(self) -> int:
        """Perform emergency cache cleanup when memory is critically high."""
        try:
            # Clear expired keys first
            cleared_count = 0

            # Get keys that are close to expiring
            all_keys = await self.redis_client.keys("malaria:*")

            for key in all_keys[:100]:  # Limit to avoid timeout
                ttl = await self.redis_client.ttl(key)
                if ttl is not None and ttl < 300:  # Less than 5 minutes
                    await self.redis_client.delete(key)
                    cleared_count += 1

            logger.warning(
                f"Emergency cache cleanup completed: {cleared_count} keys removed"
            )
            return cleared_count

        except Exception as e:
            logger.error(f"Emergency cache cleanup failed: {e}")
            return 0

    async def close(self):
        """Close Redis connections and cleanup."""
        try:
            if self.redis_client:
                await self.redis_client.close()

            if self._connection_pool:
                await self._connection_pool.disconnect()

            logger.info("Cache optimizer closed successfully")

        except Exception as e:
            logger.error(f"Error closing cache optimizer: {e}")


# Utility functions for generating cache keys
def generate_request_hash(request_data: dict) -> str:
    """Generate hash for request data to use as cache key."""
    # Sort keys for consistent hashing
    sorted_data = json.dumps(request_data, sort_keys=True)
    return hashlib.md5(sorted_data.encode()).hexdigest()[:16]


def generate_bounds_hash(bounds: dict) -> str:
    """Generate hash for spatial bounds."""
    bounds_str = (
        f"{bounds['south']},{bounds['north']},{bounds['west']},{bounds['east']}"
    )
    return hashlib.md5(bounds_str.encode()).hexdigest()[:16]


# Global cache optimizer instance
_cache_optimizer = None


async def get_cache_optimizer() -> CacheOptimizer:
    """Get or create global cache optimizer instance."""
    global _cache_optimizer

    if _cache_optimizer is None:
        _cache_optimizer = CacheOptimizer()
        await _cache_optimizer.initialize()

    return _cache_optimizer
