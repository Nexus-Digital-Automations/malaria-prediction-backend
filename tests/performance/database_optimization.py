"""
Database Performance Optimization for Malaria Prediction API.

This module provides comprehensive database performance optimizations
including query optimization, indexing strategies, and connection pooling.
"""

import logging
import time
from dataclasses import dataclass

from sqlalchemy import text

from src.malaria_predictor.database.session import get_session

logger = logging.getLogger(__name__)


@dataclass
class IndexingStrategy:
    """Defines an indexing strategy for database optimization."""

    table_name: str
    index_name: str
    columns: list[str]
    index_type: str = "btree"  # btree, hash, gin, gist, etc.
    condition: str | None = None  # For partial indexes
    description: str = ""
    estimated_benefit: str = "medium"  # low, medium, high


@dataclass
class QueryOptimization:
    """Defines a query optimization strategy."""

    name: str
    description: str
    before_query: str
    after_query: str
    estimated_improvement: str = "medium"
    applies_to: list[str] = None  # List of endpoint names


class DatabaseOptimizer:
    """Comprehensive database performance optimizer."""

    def __init__(self):
        self.indexing_strategies = self._define_indexing_strategies()
        self.query_optimizations = self._define_query_optimizations()
        self.performance_cache = {}

    def _define_indexing_strategies(self) -> list[IndexingStrategy]:
        """Define comprehensive indexing strategies for all tables."""
        return [
            # ERA5 climate data indexes
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_spatial_temporal",
                columns=["latitude", "longitude", "timestamp"],
                index_type="btree",
                description="Primary spatial-temporal index for climate data queries",
                estimated_benefit="high",
            ),
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_timestamp",
                columns=["timestamp"],
                index_type="btree",
                description="Temporal index for time-series queries",
                estimated_benefit="high",
            ),
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_spatial",
                columns=["latitude", "longitude"],
                index_type="btree",
                description="Spatial index for location-based queries",
                estimated_benefit="high",
            ),
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_temperature",
                columns=["temperature_2m"],
                index_type="btree",
                condition="temperature_2m IS NOT NULL",
                description="Temperature-based filtering index",
                estimated_benefit="medium",
            ),
            # CHIRPS precipitation data indexes
            IndexingStrategy(
                table_name="chirps_data_points",
                index_name="idx_chirps_spatial_temporal",
                columns=["latitude", "longitude", "date"],
                index_type="btree",
                description="Primary spatial-temporal index for precipitation data",
                estimated_benefit="high",
            ),
            IndexingStrategy(
                table_name="chirps_data_points",
                index_name="idx_chirps_precipitation",
                columns=["precipitation"],
                index_type="btree",
                condition="precipitation > 0",
                description="Precipitation-based filtering index",
                estimated_benefit="medium",
            ),
            # Processed climate data indexes
            IndexingStrategy(
                table_name="processed_climate_data",
                index_name="idx_processed_spatial_temporal",
                columns=["latitude", "longitude", "date"],
                index_type="btree",
                description="Primary index for processed climate data",
                estimated_benefit="high",
            ),
            IndexingStrategy(
                table_name="processed_climate_data",
                index_name="idx_processed_risk_score",
                columns=["malaria_risk_score"],
                index_type="btree",
                condition="malaria_risk_score IS NOT NULL",
                description="Risk score filtering index",
                estimated_benefit="medium",
            ),
            # WorldPop population data indexes
            IndexingStrategy(
                table_name="worldpop_data",
                index_name="idx_worldpop_spatial",
                columns=["latitude", "longitude"],
                index_type="btree",
                description="Spatial index for population data",
                estimated_benefit="high",
            ),
            # MODIS vegetation data indexes
            IndexingStrategy(
                table_name="modis_data_points",
                index_name="idx_modis_spatial_temporal",
                columns=["latitude", "longitude", "date"],
                index_type="btree",
                description="Spatial-temporal index for vegetation data",
                estimated_benefit="high",
            ),
            # Composite indexes for common query patterns
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_temp_humidity",
                columns=["temperature_2m", "relative_humidity_2m"],
                index_type="btree",
                description="Composite index for temperature-humidity queries",
                estimated_benefit="medium",
            ),
            # GIN index for full-text search (if implemented)
            IndexingStrategy(
                table_name="processed_climate_data",
                index_name="idx_processed_metadata_gin",
                columns=["metadata"],
                index_type="gin",
                description="GIN index for metadata JSON queries",
                estimated_benefit="low",
            ),
            # Partial indexes for active data
            IndexingStrategy(
                table_name="era5_data_points",
                index_name="idx_era5_recent",
                columns=["timestamp", "latitude", "longitude"],
                index_type="btree",
                condition="timestamp >= NOW() - INTERVAL '1 year'",
                description="Partial index for recent climate data",
                estimated_benefit="medium",
            ),
        ]

    def _define_query_optimizations(self) -> list[QueryOptimization]:
        """Define query optimization strategies."""
        return [
            QueryOptimization(
                name="spatial_range_optimization",
                description="Optimize spatial range queries with proper bounds",
                before_query="""
                    SELECT * FROM era5_data_points
                    WHERE latitude BETWEEN %s AND %s
                    AND longitude BETWEEN %s AND %s
                """,
                after_query="""
                    SELECT * FROM era5_data_points
                    WHERE latitude BETWEEN %s AND %s
                    AND longitude BETWEEN %s AND %s
                    AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp DESC, latitude, longitude
                """,
                estimated_improvement="high",
                applies_to=["predict_single", "predict_batch", "predict_spatial"],
            ),
            QueryOptimization(
                name="limit_with_order_optimization",
                description="Add explicit ordering for LIMIT queries",
                before_query="""
                    SELECT * FROM era5_data_points
                    WHERE latitude = %s AND longitude = %s
                    LIMIT 100
                """,
                after_query="""
                    SELECT * FROM era5_data_points
                    WHERE latitude = %s AND longitude = %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """,
                estimated_improvement="medium",
                applies_to=["predict_single", "predict_time_series"],
            ),
            QueryOptimization(
                name="join_optimization",
                description="Optimize joins between climate and population data",
                before_query="""
                    SELECT e.*, w.population_density
                    FROM era5_data_points e, worldpop_data w
                    WHERE e.latitude = w.latitude AND e.longitude = w.longitude
                """,
                after_query="""
                    SELECT e.*, w.population_density
                    FROM era5_data_points e
                    INNER JOIN worldpop_data w USING (latitude, longitude)
                    WHERE e.timestamp >= %s
                """,
                estimated_improvement="high",
                applies_to=["predict_single", "predict_batch"],
            ),
            QueryOptimization(
                name="aggregation_optimization",
                description="Optimize aggregation queries with proper grouping",
                before_query="""
                    SELECT AVG(temperature_2m), AVG(precipitation)
                    FROM era5_data_points e, chirps_data_points c
                    WHERE e.latitude = c.latitude AND e.longitude = c.longitude
                """,
                after_query="""
                    SELECT
                        AVG(e.temperature_2m) as avg_temp,
                        AVG(c.precipitation) as avg_precip
                    FROM era5_data_points e
                    INNER JOIN chirps_data_points c
                        ON e.latitude = c.latitude
                        AND e.longitude = c.longitude
                        AND DATE(e.timestamp) = c.date
                    WHERE e.timestamp >= %s AND e.timestamp <= %s
                    GROUP BY e.latitude, e.longitude
                """,
                estimated_improvement="high",
                applies_to=["predict_spatial", "predict_time_series"],
            ),
        ]

    async def analyze_query_performance(self, query: str, params: tuple = None) -> dict:
        """Analyze query performance using EXPLAIN ANALYZE."""
        async with get_session() as session:
            try:
                # Run EXPLAIN ANALYZE
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

                start_time = time.time()
                result = await session.execute(text(explain_query), params)
                execution_time = (time.time() - start_time) * 1000

                explain_data = result.fetchone()[0][0]

                return {
                    "query": query,
                    "execution_time_ms": execution_time,
                    "planning_time": explain_data.get("Planning Time", 0),
                    "execution_time": explain_data.get("Execution Time", 0),
                    "total_cost": explain_data.get("Plan", {}).get("Total Cost", 0),
                    "rows_returned": explain_data.get("Plan", {}).get("Actual Rows", 0),
                    "analysis": self._analyze_execution_plan(explain_data),
                }

            except Exception as e:
                logger.error(f"Query analysis failed: {e}")
                return {"error": str(e)}

    def _analyze_execution_plan(self, plan_data: dict) -> dict:
        """Analyze execution plan and provide optimization recommendations."""
        analysis = {
            "recommendations": [],
            "warnings": [],
            "performance_score": "good",  # good, fair, poor
        }

        plan = plan_data.get("Plan", {})

        # Check for table scans
        if "Seq Scan" in plan.get("Node Type", ""):
            analysis["warnings"].append(
                "Sequential scan detected - consider adding indexes"
            )
            analysis["performance_score"] = "poor"

        # Check for expensive operations
        total_cost = plan.get("Total Cost", 0)
        if total_cost > 10000:
            analysis["warnings"].append(f"High query cost: {total_cost:.2f}")
            analysis["performance_score"] = "fair"

        # Check for slow execution
        execution_time = plan_data.get("Execution Time", 0)
        if execution_time > 1000:  # 1 second
            analysis["warnings"].append(f"Slow execution time: {execution_time:.2f}ms")
            analysis["performance_score"] = "poor"

        # Check buffer usage
        shared_hit = plan.get("Shared Hit Blocks", 0)
        shared_read = plan.get("Shared Read Blocks", 0)

        if shared_read > shared_hit:
            analysis["recommendations"].append(
                "Poor cache hit ratio - consider increasing shared_buffers"
            )

        return analysis

    async def create_indexes(self, strategies: list[IndexingStrategy] = None) -> dict:
        """Create database indexes based on optimization strategies."""
        if strategies is None:
            strategies = self.indexing_strategies

        results = {"created": [], "failed": [], "skipped": []}

        async with get_session() as session:
            for strategy in strategies:
                try:
                    # Check if index already exists
                    check_query = """
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = :index_name
                    """

                    result = await session.execute(
                        text(check_query), {"index_name": strategy.index_name}
                    )

                    if result.fetchone():
                        results["skipped"].append(
                            {"index": strategy.index_name, "reason": "Already exists"}
                        )
                        continue

                    # Create index
                    columns_str = ", ".join(strategy.columns)

                    if strategy.index_type == "gin":
                        index_query = f"""
                            CREATE INDEX CONCURRENTLY {strategy.index_name}
                            ON {strategy.table_name}
                            USING {strategy.index_type} ({columns_str})
                        """
                    else:
                        index_query = f"""
                            CREATE INDEX CONCURRENTLY {strategy.index_name}
                            ON {strategy.table_name} ({columns_str})
                        """

                    if strategy.condition:
                        index_query += f" WHERE {strategy.condition}"

                    logger.info(f"Creating index: {strategy.index_name}")
                    await session.execute(text(index_query))

                    results["created"].append(
                        {
                            "index": strategy.index_name,
                            "table": strategy.table_name,
                            "columns": strategy.columns,
                            "benefit": strategy.estimated_benefit,
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to create index {strategy.index_name}: {e}")
                    results["failed"].append(
                        {"index": strategy.index_name, "error": str(e)}
                    )

        return results

    async def analyze_table_statistics(self, table_names: list[str] = None) -> dict:
        """Analyze table statistics for performance optimization."""
        if table_names is None:
            table_names = [
                "era5_data_points",
                "chirps_data_points",
                "processed_climate_data",
                "worldpop_data",
                "modis_data_points",
            ]

        statistics = {}

        async with get_session() as session:
            for table_name in table_names:
                try:
                    # Get table size and row count
                    stats_query = """
                        SELECT
                            schemaname,
                            tablename,
                            attname,
                            n_distinct,
                            correlation,
                            most_common_vals,
                            most_common_freqs
                        FROM pg_stats
                        WHERE tablename = :table_name
                        ORDER BY attname
                    """

                    result = await session.execute(
                        text(stats_query), {"table_name": table_name}
                    )

                    column_stats = []
                    for row in result:
                        column_stats.append(
                            {
                                "column": row.attname,
                                "distinct_values": row.n_distinct,
                                "correlation": row.correlation,
                                "most_common_values": row.most_common_vals,
                                "frequencies": row.most_common_freqs,
                            }
                        )

                    # Get table size
                    size_query = """
                        SELECT
                            pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                            pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                            reltuples::bigint as estimated_rows
                        FROM pg_class
                        WHERE relname = :table_name
                    """

                    size_result = await session.execute(
                        text(size_query), {"table_name": table_name}
                    )

                    size_row = size_result.fetchone()

                    statistics[table_name] = {
                        "total_size": size_row.total_size if size_row else "Unknown",
                        "table_size": size_row.table_size if size_row else "Unknown",
                        "estimated_rows": size_row.estimated_rows if size_row else 0,
                        "column_statistics": column_stats,
                    }

                except Exception as e:
                    logger.error(f"Failed to get statistics for {table_name}: {e}")
                    statistics[table_name] = {"error": str(e)}

        return statistics

    async def optimize_connection_pool(self) -> dict:
        """Optimize database connection pool settings."""
        optimizations = {
            "current_settings": {},
            "recommendations": [],
            "applied_changes": [],
        }

        async with get_session() as session:
            try:
                # Get current connection settings
                settings_query = """
                    SELECT name, setting, unit, short_desc
                    FROM pg_settings
                    WHERE name IN (
                        'max_connections',
                        'shared_buffers',
                        'effective_cache_size',
                        'work_mem',
                        'maintenance_work_mem',
                        'checkpoint_completion_target',
                        'wal_buffers',
                        'default_statistics_target'
                    )
                    ORDER BY name
                """

                result = await session.execute(text(settings_query))

                for row in result:
                    optimizations["current_settings"][row.name] = {
                        "value": row.setting,
                        "unit": row.unit,
                        "description": row.short_desc,
                    }

                # Generate recommendations based on current settings
                optimizations["recommendations"] = self._generate_pool_recommendations(
                    optimizations["current_settings"]
                )

            except Exception as e:
                optimizations["error"] = str(e)

        return optimizations

    def _generate_pool_recommendations(self, current_settings: dict) -> list[str]:
        """Generate connection pool optimization recommendations."""
        recommendations = []

        # Check max_connections
        max_conn = int(current_settings.get("max_connections", {}).get("value", "100"))
        if max_conn < 200:
            recommendations.append(
                f"Consider increasing max_connections from {max_conn} to 200+ for high-load scenarios"
            )

        # Check shared_buffers
        shared_buf = current_settings.get("shared_buffers", {}).get("value", "128MB")
        if "MB" in shared_buf and int(shared_buf.replace("MB", "")) < 512:
            recommendations.append(
                f"Consider increasing shared_buffers from {shared_buf} to 25% of total RAM"
            )

        # Check work_mem
        work_mem = current_settings.get("work_mem", {}).get("value", "4MB")
        if "MB" in work_mem and int(work_mem.replace("MB", "")) < 8:
            recommendations.append(
                f"Consider increasing work_mem from {work_mem} to 8-16MB for complex queries"
            )

        return recommendations

    async def update_table_statistics(self, table_names: list[str] = None) -> dict:
        """Update table statistics for better query planning."""
        if table_names is None:
            table_names = [
                "era5_data_points",
                "chirps_data_points",
                "processed_climate_data",
                "worldpop_data",
                "modis_data_points",
            ]

        results = {"updated": [], "failed": []}

        async with get_session() as session:
            for table_name in table_names:
                try:
                    logger.info(f"Updating statistics for {table_name}")
                    await session.execute(text(f"ANALYZE {table_name}"))
                    results["updated"].append(table_name)

                except Exception as e:
                    logger.error(f"Failed to update statistics for {table_name}: {e}")
                    results["failed"].append({"table": table_name, "error": str(e)})

        return results

    async def benchmark_queries(
        self, test_queries: list[tuple[str, dict]] = None
    ) -> dict:
        """Benchmark common queries to identify performance bottlenecks."""
        if test_queries is None:
            test_queries = self._get_benchmark_queries()

        results = []

        for query_name, query_info in test_queries:
            try:
                query = query_info["query"]
                params = query_info.get("params", {})

                # Run query multiple times for average
                times = []
                for _ in range(3):
                    start_time = time.time()

                    async with get_session() as session:
                        await session.execute(text(query), params)

                    times.append((time.time() - start_time) * 1000)

                avg_time = sum(times) / len(times)

                # Analyze query performance
                analysis = await self.analyze_query_performance(
                    query, tuple(params.values()) if params else None
                )

                results.append(
                    {
                        "query_name": query_name,
                        "avg_execution_time_ms": avg_time,
                        "min_time_ms": min(times),
                        "max_time_ms": max(times),
                        "analysis": analysis,
                        "query": query,
                    }
                )

            except Exception as e:
                results.append({"query_name": query_name, "error": str(e)})

        return {"benchmark_results": results}

    def _get_benchmark_queries(self) -> list[tuple[str, dict]]:
        """Get common queries for benchmarking."""
        return [
            (
                "single_location_climate",
                {
                    "query": """
                    SELECT * FROM era5_data_points
                    WHERE latitude BETWEEN :lat - 0.1 AND :lat + 0.1
                    AND longitude BETWEEN :lon - 0.1 AND :lon + 0.1
                    AND timestamp >= :start_date
                    ORDER BY timestamp DESC LIMIT 100
                """,
                    "params": {"lat": 0.0, "lon": 0.0, "start_date": "2023-01-01"},
                },
            ),
            (
                "spatial_aggregation",
                {
                    "query": """
                    SELECT
                        AVG(temperature_2m) as avg_temp,
                        COUNT(*) as point_count
                    FROM era5_data_points
                    WHERE latitude BETWEEN :south AND :north
                    AND longitude BETWEEN :west AND :east
                    AND timestamp >= :start_date
                    GROUP BY DATE(timestamp)
                    ORDER BY DATE(timestamp) DESC
                """,
                    "params": {
                        "south": -5.0,
                        "north": 5.0,
                        "west": -5.0,
                        "east": 5.0,
                        "start_date": "2023-01-01",
                    },
                },
            ),
            (
                "climate_precipitation_join",
                {
                    "query": """
                    SELECT
                        e.temperature_2m,
                        c.precipitation,
                        e.timestamp
                    FROM era5_data_points e
                    INNER JOIN chirps_data_points c
                        ON e.latitude = c.latitude
                        AND e.longitude = c.longitude
                        AND DATE(e.timestamp) = c.date
                    WHERE e.latitude = :lat AND e.longitude = :lon
                    AND e.timestamp >= :start_date
                    ORDER BY e.timestamp DESC LIMIT 50
                """,
                    "params": {"lat": 0.0, "lon": 0.0, "start_date": "2023-01-01"},
                },
            ),
        ]
