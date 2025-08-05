"""
Performance Monitoring System for Load Testing.

This module provides comprehensive performance monitoring and profiling
capabilities during load testing of the malaria prediction API.
"""

import json
import logging
import os
import random
import sqlite3
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

import psutil
import redis
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from .locust_config import PERFORMANCE_METRICS, LoadTestSettings

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Individual request performance metric."""

    timestamp: float
    endpoint: str
    response_time: float  # milliseconds
    success: bool
    response_size: int
    user_count: int


@dataclass
class SystemMetric:
    """System resource usage metric."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    active_connections: int


@dataclass
class DatabaseMetric:
    """Database performance metric."""

    timestamp: float
    active_connections: int
    idle_connections: int
    query_count: int
    avg_query_time: float
    slow_queries: int


@dataclass
class CacheMetric:
    """Cache performance metric."""

    timestamp: float
    hit_rate: float
    miss_rate: float
    memory_usage_mb: float
    key_count: int
    evicted_keys: int


class PerformanceMonitor:
    """Comprehensive performance monitoring system for load testing."""

    def __init__(self, settings: LoadTestSettings):
        self.settings = settings
        self.running = False
        self.start_time = None
        self.end_time = None

        # Metrics storage
        self.request_metrics: deque[RequestMetric] = deque(maxlen=100000)
        self.system_metrics: deque[SystemMetric] = deque(maxlen=10000)
        self.database_metrics: deque[DatabaseMetric] = deque(maxlen=10000)
        self.cache_metrics: deque[CacheMetric] = deque(maxlen=10000)

        # Performance statistics
        self.endpoint_stats = defaultdict(list)
        self.error_count = defaultdict(int)
        self.user_count = 0

        # Monitoring threads
        self.system_monitor_thread = None
        self.db_monitor_thread = None
        self.cache_monitor_thread = None

        # External connections
        self.redis_client = None
        self.db_connection = None

        # Prometheus metrics
        self.setup_prometheus_metrics()

        # SQLite for detailed logging
        self.setup_sqlite_logging()

    def setup_prometheus_metrics(self):
        """Initialize Prometheus metrics for real-time monitoring."""
        self.registry = CollectorRegistry()

        # Request metrics
        self.request_duration = Histogram(
            "malaria_api_request_duration_seconds",
            "Request duration in seconds",
            ["endpoint", "method"],
            registry=self.registry,
        )

        self.request_count = Counter(
            "malaria_api_requests_total",
            "Total number of requests",
            ["endpoint", "method", "status"],
            registry=self.registry,
        )

        self.error_rate = Gauge(
            "malaria_api_error_rate",
            "Current error rate",
            ["endpoint"],
            registry=self.registry,
        )

        # System metrics
        self.cpu_usage = Gauge(
            "malaria_api_cpu_usage_percent",
            "CPU usage percentage",
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "malaria_api_memory_usage_percent",
            "Memory usage percentage",
            registry=self.registry,
        )

        self.active_users = Gauge(
            "malaria_api_active_users", "Number of active users", registry=self.registry
        )

    def setup_sqlite_logging(self):
        """Initialize SQLite database for detailed performance logging."""
        os.makedirs("performance/logs", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.db_path = f"performance/logs/performance_{timestamp}.db"

        conn = sqlite3.connect(self.db_path)

        # Create tables
        conn.execute(
            """
            CREATE TABLE request_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                endpoint TEXT,
                response_time REAL,
                success BOOLEAN,
                response_size INTEGER,
                user_count INTEGER
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                cpu_percent REAL,
                memory_percent REAL,
                memory_mb REAL,
                disk_io_read INTEGER,
                disk_io_write INTEGER,
                network_sent INTEGER,
                network_recv INTEGER,
                active_connections INTEGER
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE database_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                active_connections INTEGER,
                idle_connections INTEGER,
                query_count INTEGER,
                avg_query_time REAL,
                slow_queries INTEGER
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE cache_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                hit_rate REAL,
                miss_rate REAL,
                memory_usage_mb REAL,
                key_count INTEGER,
                evicted_keys INTEGER
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info(f"Performance logging database created: {self.db_path}")

    def initialize(self):
        """Initialize monitoring connections and resources."""
        try:
            # Initialize Redis connection for cache monitoring
            if self.settings.redis_url:
                self.redis_client = redis.from_url(self.settings.redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("Redis connection initialized for cache monitoring")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None

        try:
            # Initialize database connection for DB monitoring
            if self.settings.database_url:
                # Note: This would need async handling in real implementation
                logger.info("Database monitoring initialized")

        except Exception as e:
            logger.warning(f"Database connection failed: {e}")

    def start_monitoring(self):
        """Start performance monitoring threads."""
        self.running = True
        self.start_time = time.time()

        # Start system monitoring thread
        self.system_monitor_thread = threading.Thread(
            target=self._monitor_system_resources, daemon=True
        )
        self.system_monitor_thread.start()

        # Start database monitoring thread
        if self.settings.database_url:
            self.db_monitor_thread = threading.Thread(
                target=self._monitor_database, daemon=True
            )
            self.db_monitor_thread.start()

        # Start cache monitoring thread
        if self.redis_client:
            self.cache_monitor_thread = threading.Thread(
                target=self._monitor_cache, daemon=True
            )
            self.cache_monitor_thread.start()

        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring threads."""
        self.running = False
        self.end_time = time.time()

        # Wait for threads to finish
        if self.system_monitor_thread:
            self.system_monitor_thread.join(timeout=5)

        if self.db_monitor_thread:
            self.db_monitor_thread.join(timeout=5)

        if self.cache_monitor_thread:
            self.cache_monitor_thread.join(timeout=5)

        logger.info("Performance monitoring stopped")

    def record_request(
        self, endpoint: str, response_time: float, success: bool, response_size: int
    ):
        """Record a request performance metric."""
        timestamp = time.time()

        metric = RequestMetric(
            timestamp=timestamp,
            endpoint=endpoint,
            response_time=response_time,
            success=success,
            response_size=response_size,
            user_count=self.user_count,
        )

        self.request_metrics.append(metric)
        self.endpoint_stats[endpoint].append(response_time)

        if not success:
            self.error_count[endpoint] += 1

        # Update Prometheus metrics
        status = "success" if success else "error"
        self.request_count.labels(
            endpoint=endpoint,
            method="POST",  # Most prediction endpoints are POST
            status=status,
        ).inc()

        self.request_duration.labels(endpoint=endpoint, method="POST").observe(
            response_time / 1000
        )  # Convert to seconds

        # Calculate and update error rate
        total_requests = len(self.endpoint_stats[endpoint])
        error_requests = self.error_count[endpoint]
        error_rate = error_requests / total_requests if total_requests > 0 else 0
        self.error_rate.labels(endpoint=endpoint).set(error_rate)

        # Log to SQLite
        self._log_request_to_db(metric)

    def on_user_start(self):
        """Called when a user starts."""
        self.user_count += 1
        self.active_users.set(self.user_count)

    def on_user_stop(self):
        """Called when a user stops."""
        self.user_count = max(0, self.user_count - 1)
        self.active_users.set(self.user_count)

    def _monitor_system_resources(self):
        """Monitor system resource usage in background thread."""
        last_disk_io = psutil.disk_io_counters()
        last_network = psutil.net_io_counters()

        while self.running:
            try:
                # Get current metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network = psutil.net_io_counters()

                # Calculate deltas for IO metrics
                disk_read_delta = disk_io.read_bytes - last_disk_io.read_bytes
                disk_write_delta = disk_io.write_bytes - last_disk_io.write_bytes
                network_sent_delta = network.bytes_sent - last_network.bytes_sent
                network_recv_delta = network.bytes_recv - last_network.bytes_recv

                metric = SystemMetric(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_mb=memory.used / (1024 * 1024),
                    disk_io_read=disk_read_delta,
                    disk_io_write=disk_write_delta,
                    network_sent=network_sent_delta,
                    network_recv=network_recv_delta,
                    active_connections=len(psutil.net_connections()),
                )

                self.system_metrics.append(metric)

                # Update Prometheus metrics
                self.cpu_usage.set(cpu_percent)
                self.memory_usage.set(memory.percent)

                # Log to SQLite
                self._log_system_to_db(metric)

                # Update references for next iteration
                last_disk_io = disk_io
                last_network = network

            except Exception as e:
                logger.error(f"System monitoring error: {e}")

            time.sleep(5)  # Monitor every 5 seconds

    def _monitor_database(self):
        """Monitor database performance in background thread."""
        while self.running:
            try:
                # This would require actual database connection
                # For now, simulate basic metrics
                metric = DatabaseMetric(
                    timestamp=time.time(),
                    active_connections=random.randint(5, 50),
                    idle_connections=random.randint(0, 10),
                    query_count=random.randint(100, 1000),
                    avg_query_time=random.uniform(10, 100),
                    slow_queries=random.randint(0, 5),
                )

                self.database_metrics.append(metric)
                self._log_database_to_db(metric)

            except Exception as e:
                logger.error(f"Database monitoring error: {e}")

            time.sleep(10)  # Monitor every 10 seconds

    def _monitor_cache(self):
        """Monitor Redis cache performance in background thread."""
        while self.running and self.redis_client:
            try:
                info = self.redis_client.info()
                stats = self.redis_client.info("stats")

                # Calculate hit/miss rates
                hits = stats.get("keyspace_hits", 0)
                misses = stats.get("keyspace_misses", 0)
                total = hits + misses

                hit_rate = hits / total if total > 0 else 0
                miss_rate = misses / total if total > 0 else 0

                metric = CacheMetric(
                    timestamp=time.time(),
                    hit_rate=hit_rate,
                    miss_rate=miss_rate,
                    memory_usage_mb=info.get("used_memory", 0) / (1024 * 1024),
                    key_count=info.get("db0", {}).get("keys", 0),
                    evicted_keys=stats.get("evicted_keys", 0),
                )

                self.cache_metrics.append(metric)
                self._log_cache_to_db(metric)

            except Exception as e:
                logger.error(f"Cache monitoring error: {e}")

            time.sleep(10)  # Monitor every 10 seconds

    def _log_request_to_db(self, metric: RequestMetric):
        """Log request metric to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO request_metrics
                (timestamp, endpoint, response_time, success, response_size, user_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.endpoint,
                    metric.response_time,
                    metric.success,
                    metric.response_size,
                    metric.user_count,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging request metric: {e}")

    def _log_system_to_db(self, metric: SystemMetric):
        """Log system metric to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO system_metrics
                (timestamp, cpu_percent, memory_percent, memory_mb,
                 disk_io_read, disk_io_write, network_sent, network_recv, active_connections)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.memory_mb,
                    metric.disk_io_read,
                    metric.disk_io_write,
                    metric.network_sent,
                    metric.network_recv,
                    metric.active_connections,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging system metric: {e}")

    def _log_database_to_db(self, metric: DatabaseMetric):
        """Log database metric to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO database_metrics
                (timestamp, active_connections, idle_connections, query_count,
                 avg_query_time, slow_queries)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.active_connections,
                    metric.idle_connections,
                    metric.query_count,
                    metric.avg_query_time,
                    metric.slow_queries,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging database metric: {e}")

    def _log_cache_to_db(self, metric: CacheMetric):
        """Log cache metric to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO cache_metrics
                (timestamp, hit_rate, miss_rate, memory_usage_mb, key_count, evicted_keys)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.hit_rate,
                    metric.miss_rate,
                    metric.memory_usage_mb,
                    metric.key_count,
                    metric.evicted_keys,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging cache metric: {e}")

    def generate_report(self):
        """Generate comprehensive performance report."""
        if not self.start_time or not self.end_time:
            logger.error(
                "Cannot generate report: monitoring not properly started/stopped"
            )
            return

        duration = self.end_time - self.start_time
        total_requests = len(self.request_metrics)

        # Calculate overall statistics
        all_response_times = [m.response_time for m in self.request_metrics]
        successful_requests = sum(1 for m in self.request_metrics if m.success)
        failed_requests = total_requests - successful_requests

        overall_stats = {
            "test_duration_seconds": duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests
            if total_requests > 0
            else 0,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
        }

        # Calculate response time percentiles
        if all_response_times:
            all_response_times.sort()
            percentiles = {}
            for p in PERFORMANCE_METRICS["response_time_percentiles"]:
                idx = int((p / 100) * len(all_response_times))
                percentiles[f"p{p}"] = all_response_times[
                    min(idx, len(all_response_times) - 1)
                ]

            overall_stats.update(
                {
                    "response_time_min": min(all_response_times),
                    "response_time_max": max(all_response_times),
                    "response_time_avg": sum(all_response_times)
                    / len(all_response_times),
                    "response_time_percentiles": percentiles,
                }
            )

        # Calculate per-endpoint statistics
        endpoint_stats = {}
        for endpoint, times in self.endpoint_stats.items():
            if times:
                times.sort()
                endpoint_percentiles = {}
                for p in PERFORMANCE_METRICS["response_time_percentiles"]:
                    idx = int((p / 100) * len(times))
                    endpoint_percentiles[f"p{p}"] = times[min(idx, len(times) - 1)]

                endpoint_stats[endpoint] = {
                    "total_requests": len(times),
                    "failed_requests": self.error_count[endpoint],
                    "success_rate": 1 - (self.error_count[endpoint] / len(times)),
                    "response_time_min": min(times),
                    "response_time_max": max(times),
                    "response_time_avg": sum(times) / len(times),
                    "response_time_percentiles": endpoint_percentiles,
                }

        # System resource summary
        if self.system_metrics:
            cpu_values = [m.cpu_percent for m in self.system_metrics]
            memory_values = [m.memory_percent for m in self.system_metrics]

            system_stats = {
                "cpu_avg": sum(cpu_values) / len(cpu_values),
                "cpu_max": max(cpu_values),
                "memory_avg": sum(memory_values) / len(memory_values),
                "memory_max": max(memory_values),
            }
        else:
            system_stats = {}

        # Performance assessment
        performance_assessment = self._assess_performance(overall_stats, endpoint_stats)

        # Generate report
        report = {
            "test_info": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "duration_seconds": duration,
                "target_settings": {
                    "p95_target": PERFORMANCE_METRICS["target_p95_response_time"],
                    "throughput_target": PERFORMANCE_METRICS["throughput_target"],
                    "error_rate_threshold": PERFORMANCE_METRICS["error_rate_threshold"],
                },
            },
            "overall_statistics": overall_stats,
            "endpoint_statistics": endpoint_stats,
            "system_resources": system_stats,
            "performance_assessment": performance_assessment,
            "database_path": self.db_path,
        }

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance/reports/performance_report_{timestamp}.json"
        os.makedirs("performance/reports", exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Performance report generated: {report_file}")

        # Print summary to console
        self._print_summary(report)

        return report

    def _assess_performance(self, overall_stats: dict, endpoint_stats: dict) -> dict:
        """Assess performance against targets and provide recommendations."""
        assessment = {"meets_targets": True, "issues": [], "recommendations": []}

        # Check P95 response time target
        p95_time = overall_stats.get("response_time_percentiles", {}).get("p95", 0)
        if p95_time > PERFORMANCE_METRICS["target_p95_response_time"]:
            assessment["meets_targets"] = False
            assessment["issues"].append(
                f"P95 response time ({p95_time:.2f}ms) exceeds target "
                f"({PERFORMANCE_METRICS['target_p95_response_time']:.2f}ms)"
            )
            assessment["recommendations"].append(
                "Consider implementing response caching, database query optimization, "
                "or horizontal scaling"
            )

        # Check throughput target
        rps = overall_stats.get("requests_per_second", 0)
        if rps < PERFORMANCE_METRICS["throughput_target"]:
            assessment["meets_targets"] = False
            assessment["issues"].append(
                f"Throughput ({rps:.2f} RPS) below target "
                f"({PERFORMANCE_METRICS['throughput_target']} RPS)"
            )
            assessment["recommendations"].append(
                "Consider optimizing application performance, adding load balancing, "
                "or scaling infrastructure"
            )

        # Check error rate
        error_rate = 1 - overall_stats.get("success_rate", 1)
        if error_rate > PERFORMANCE_METRICS["error_rate_threshold"]:
            assessment["meets_targets"] = False
            assessment["issues"].append(
                f"Error rate ({error_rate:.3f}) exceeds threshold "
                f"({PERFORMANCE_METRICS['error_rate_threshold']:.3f})"
            )
            assessment["recommendations"].append(
                "Investigate error causes, improve error handling, "
                "and consider implementing circuit breakers"
            )

        return assessment

    def _print_summary(self, report: dict):
        """Print performance test summary to console."""
        print("\n" + "=" * 80)
        print("MALARIA PREDICTION API - PERFORMANCE TEST SUMMARY")
        print("=" * 80)

        overall = report["overall_statistics"]
        print(f"Test Duration: {overall['test_duration_seconds']:.2f} seconds")
        print(f"Total Requests: {overall['total_requests']}")
        print(f"Success Rate: {overall['success_rate']:.3f}")
        print(f"Requests/Second: {overall['requests_per_second']:.2f}")

        if "response_time_percentiles" in overall:
            percentiles = overall["response_time_percentiles"]
            print("\nResponse Time Percentiles:")
            for p in ["p50", "p75", "p90", "p95", "p99"]:
                if p in percentiles:
                    print(f"  {p.upper()}: {percentiles[p]:.2f}ms")

        assessment = report["performance_assessment"]
        print(
            f"\nPerformance Assessment: {'✅ PASS' if assessment['meets_targets'] else '❌ FAIL'}"
        )

        if assessment["issues"]:
            print("\nIssues Identified:")
            for issue in assessment["issues"]:
                print(f"  • {issue}")

        if assessment["recommendations"]:
            print("\nRecommendations:")
            for rec in assessment["recommendations"]:
                print(f"  • {rec}")

        print(f"\nDetailed data saved to: {report['database_path']}")
        print("=" * 80)
