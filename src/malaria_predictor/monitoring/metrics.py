"""
Prometheus Metrics Collection System.

This module provides comprehensive metrics collection for the malaria prediction
system including API metrics, ML model performance metrics, system metrics,
and custom business metrics.
"""

import asyncio

import psutil
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    multiprocess,
)
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST as OPENMETRICS_CONTENT_TYPE,
)

from ..config import settings


class MetricsCollector:
    """
    Base metrics collector with common functionality.

    Provides a foundation for all metric collection classes with
    standardized labeling, error handling, and metric management.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.enabled = settings.monitoring.enable_metrics
        self._metrics: dict[str, Counter | Gauge | Histogram | Summary] = {}

    def _create_counter(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Counter | None:
        """Create a Prometheus Counter metric or None if disabled."""
        if not self.enabled:
            return None

        labels = labels or []
        counter = Counter(
            name=name,
            documentation=description,
            labelnames=labels,
            registry=self.registry,
        )
        self._metrics[name] = counter
        return counter

    def _create_gauge(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Gauge | None:
        """Create a Prometheus Gauge metric or None if disabled."""
        if not self.enabled:
            return None

        labels = labels or []
        gauge = Gauge(
            name=name,
            documentation=description,
            labelnames=labels,
            registry=self.registry,
        )
        self._metrics[name] = gauge
        return gauge

    def _create_histogram(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
        buckets: tuple | None = None,
    ) -> Histogram | None:
        """Create a Prometheus Histogram metric or None if disabled."""
        if not self.enabled:
            return None

        labels = labels or []
        # Use default buckets if None
        if buckets is None:
            histogram = Histogram(
                name=name,
                documentation=description,
                labelnames=labels,
                registry=self.registry,
            )
        else:
            histogram = Histogram(
                name=name,
                documentation=description,
                labelnames=labels,
                buckets=buckets,
                registry=self.registry,
            )
        self._metrics[name] = histogram
        return histogram

    def _create_summary(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Summary | None:
        """Create a Prometheus Summary metric or None if disabled."""
        if not self.enabled:
            return None

        labels = labels or []
        summary = Summary(
            name=name,
            documentation=description,
            labelnames=labels,
            registry=self.registry,
        )
        self._metrics[name] = summary
        return summary

    def get_metric(self, name: str) -> Counter | Gauge | Histogram | Summary | None:
        """Get a metric by name."""
        return self._metrics.get(name)

    def increment_counter(
        self, name: str, labels: dict[str, str] | None = None, value: float = 1
    ) -> None:
        """Increment a counter metric."""
        if not self.enabled:
            return

        metric = self.get_metric(name)
        if metric and isinstance(metric, Counter):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        if not self.enabled:
            return

        metric = self.get_metric(name)
        if metric and isinstance(metric, Gauge):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def observe_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Observe a value in a histogram metric."""
        if not self.enabled:
            return

        metric = self.get_metric(name)
        if metric and isinstance(metric, Histogram):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def observe_summary(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Observe a value in a summary metric."""
        if not self.enabled:
            return

        metric = self.get_metric(name)
        if metric and isinstance(metric, Summary):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)


class APIMetrics(MetricsCollector):
    """
    API-specific metrics collection.

    Collects metrics related to HTTP requests, responses, and API performance
    including request counts, duration, error rates, and endpoint usage.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        super().__init__(registry)
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Initialize API metrics."""
        # Request metrics
        self.request_count = self._create_counter(
            "malaria_api_requests_total",
            "Total number of API requests",
            ["method", "endpoint", "status_code"],
        )

        self.request_duration = self._create_histogram(
            "malaria_api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
            buckets=(
                0.001,
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                10.0,
            ),
        )

        self.request_size = self._create_histogram(
            "malaria_api_request_size_bytes",
            "API request size in bytes",
            ["method", "endpoint"],
            buckets=(128, 512, 1024, 4096, 16384, 65536, 262144, 1048576),
        )

        self.response_size = self._create_histogram(
            "malaria_api_response_size_bytes",
            "API response size in bytes",
            ["method", "endpoint"],
            buckets=(128, 512, 1024, 4096, 16384, 65536, 262144, 1048576),
        )

        # Error metrics
        self.error_count = self._create_counter(
            "malaria_api_errors_total",
            "Total number of API errors",
            ["method", "endpoint", "error_type"],
        )

        # Rate limiting metrics
        self.rate_limit_hits = self._create_counter(
            "malaria_api_rate_limit_hits_total",
            "Total number of rate limit hits",
            ["endpoint"],
        )

        # Authentication metrics
        self.auth_attempts = self._create_counter(
            "malaria_api_auth_attempts_total",
            "Total authentication attempts",
            ["result"],  # success, failure
        )

        # Active connections
        self.active_connections = self._create_gauge(
            "malaria_api_active_connections",
            "Number of active connections",
        )

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0,
    ) -> None:
        """Record API request metrics."""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
        }

        # Request count and duration
        self.increment_counter("malaria_api_requests_total", labels)
        self.observe_histogram(
            "malaria_api_request_duration_seconds",
            duration,
            {"method": method, "endpoint": endpoint},
        )

        # Request/response sizes
        if request_size > 0:
            self.observe_histogram(
                "malaria_api_request_size_bytes",
                request_size,
                {"method": method, "endpoint": endpoint},
            )

        if response_size > 0:
            self.observe_histogram(
                "malaria_api_response_size_bytes",
                response_size,
                {"method": method, "endpoint": endpoint},
            )

    def record_error(self, method: str, endpoint: str, error_type: str) -> None:
        """Record API error metrics."""
        self.increment_counter(
            "malaria_api_errors_total",
            {"method": method, "endpoint": endpoint, "error_type": error_type},
        )

    def record_rate_limit_hit(self, endpoint: str) -> None:
        """Record rate limit hit."""
        self.increment_counter(
            "malaria_api_rate_limit_hits_total", {"endpoint": endpoint}
        )

    def record_auth_attempt(self, success: bool) -> None:
        """Record authentication attempt."""
        result = "success" if success else "failure"
        self.increment_counter("malaria_api_auth_attempts_total", {"result": result})

    def set_active_connections(self, count: int) -> None:
        """Set active connections count."""
        self.set_gauge("malaria_api_active_connections", count)


class MLModelMetrics(MetricsCollector):
    """
    Machine Learning model performance metrics.

    Collects metrics specific to ML model performance including prediction
    latency, accuracy, model loading times, and inference statistics.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        super().__init__(registry)
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Initialize ML model metrics."""
        # Prediction metrics
        self.prediction_count = self._create_counter(
            "malaria_ml_predictions_total",
            "Total number of ML predictions",
            ["model_type", "model_version"],
        )

        self.prediction_duration = self._create_histogram(
            "malaria_ml_prediction_duration_seconds",
            "ML prediction duration in seconds",
            ["model_type", "model_version"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )

        self.prediction_confidence = self._create_histogram(
            "malaria_ml_prediction_confidence",
            "ML prediction confidence scores",
            ["model_type", "model_version"],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99),
        )

        # Model loading metrics
        self.model_loading_duration = self._create_histogram(
            "malaria_ml_model_loading_duration_seconds",
            "Model loading duration in seconds",
            ["model_type", "model_version"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
        )

        # Model performance metrics
        self.model_accuracy = self._create_gauge(
            "malaria_ml_model_accuracy",
            "Model accuracy score",
            ["model_type", "model_version", "metric_type"],
        )

        self.model_memory_usage = self._create_gauge(
            "malaria_ml_model_memory_usage_bytes",
            "Model memory usage in bytes",
            ["model_type", "model_version"],
        )

        # Batch processing metrics
        self.batch_size = self._create_histogram(
            "malaria_ml_batch_size",
            "ML prediction batch sizes",
            ["model_type"],
            buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000),
        )

        # Model errors
        self.model_errors = self._create_counter(
            "malaria_ml_model_errors_total",
            "Total number of ML model errors",
            ["model_type", "model_version", "error_type"],
        )

        # Feature engineering metrics
        self.feature_extraction_duration = self._create_histogram(
            "malaria_ml_feature_extraction_duration_seconds",
            "Feature extraction duration in seconds",
            ["data_source"],
            buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

    def record_prediction(
        self,
        model_type: str,
        model_version: str,
        duration: float,
        confidence: float,
        batch_size: int = 1,
    ) -> None:
        """Record ML prediction metrics."""
        labels = {"model_type": model_type, "model_version": model_version}

        self.increment_counter("malaria_ml_predictions_total", labels)
        self.observe_histogram(
            "malaria_ml_prediction_duration_seconds", duration, labels
        )
        self.observe_histogram("malaria_ml_prediction_confidence", confidence, labels)
        self.observe_histogram(
            "malaria_ml_batch_size", batch_size, {"model_type": model_type}
        )

    def record_model_loading(
        self, model_type: str, model_version: str, duration: float
    ) -> None:
        """Record model loading metrics."""
        labels = {"model_type": model_type, "model_version": model_version}
        self.observe_histogram(
            "malaria_ml_model_loading_duration_seconds", duration, labels
        )

    def set_model_accuracy(
        self, model_type: str, model_version: str, metric_type: str, accuracy: float
    ) -> None:
        """Set model accuracy metric."""
        labels = {
            "model_type": model_type,
            "model_version": model_version,
            "metric_type": metric_type,
        }
        self.set_gauge("malaria_ml_model_accuracy", accuracy, labels)

    def set_model_memory_usage(
        self, model_type: str, model_version: str, memory_bytes: int
    ) -> None:
        """Set model memory usage metric."""
        labels = {"model_type": model_type, "model_version": model_version}
        self.set_gauge("malaria_ml_model_memory_usage_bytes", memory_bytes, labels)

    def record_model_error(self, model_type: str, model_version: str, error_type: str) -> None:
        """Record model error."""
        labels = {
            "model_type": model_type,
            "model_version": model_version,
            "error_type": error_type,
        }
        self.increment_counter("malaria_ml_model_errors_total", labels)

    def record_feature_extraction(self, data_source: str, duration: float) -> None:
        """Record feature extraction metrics."""
        self.observe_histogram(
            "malaria_ml_feature_extraction_duration_seconds",
            duration,
            {"data_source": data_source},
        )


class SystemMetrics(MetricsCollector):
    """
    System-level metrics collection.

    Collects metrics about system resource usage including CPU, memory,
    disk usage, network statistics, and database connections.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        super().__init__(registry)
        self._setup_metrics()
        self._collection_interval = 30  # seconds

    def _setup_metrics(self) -> None:
        """Initialize system metrics."""
        # CPU metrics
        self.cpu_usage_percent = self._create_gauge(
            "malaria_system_cpu_usage_percent",
            "CPU usage percentage",
            ["cpu"],
        )

        self.cpu_load_average = self._create_gauge(
            "malaria_system_cpu_load_average",
            "CPU load average",
            ["period"],  # 1min, 5min, 15min
        )

        # Memory metrics
        self.memory_usage_bytes = self._create_gauge(
            "malaria_system_memory_usage_bytes",
            "Memory usage in bytes",
            ["type"],  # total, available, used, free
        )

        self.memory_usage_percent = self._create_gauge(
            "malaria_system_memory_usage_percent",
            "Memory usage percentage",
        )

        # Disk metrics
        self.disk_usage_bytes = self._create_gauge(
            "malaria_system_disk_usage_bytes",
            "Disk usage in bytes",
            ["device", "type"],  # total, used, free
        )

        self.disk_usage_percent = self._create_gauge(
            "malaria_system_disk_usage_percent",
            "Disk usage percentage",
            ["device"],
        )

        self.disk_io_bytes = self._create_counter(
            "malaria_system_disk_io_bytes_total",
            "Total disk I/O in bytes",
            ["device", "direction"],  # read, write
        )

        # Network metrics
        self.network_bytes = self._create_counter(
            "malaria_system_network_bytes_total",
            "Total network bytes",
            ["interface", "direction"],  # sent, received
        )

        self.network_packets = self._create_counter(
            "malaria_system_network_packets_total",
            "Total network packets",
            ["interface", "direction"],  # sent, received
        )

        # Process metrics
        self.process_count = self._create_gauge(
            "malaria_system_process_count",
            "Number of processes",
            ["status"],  # running, sleeping, zombie, etc.
        )

        # Database connection metrics
        self.db_connections_active = self._create_gauge(
            "malaria_system_db_connections_active",
            "Active database connections",
        )

        self.db_connections_idle = self._create_gauge(
            "malaria_system_db_connections_idle",
            "Idle database connections",
        )

        # Cache metrics (Redis)
        self.cache_hit_rate = self._create_gauge(
            "malaria_system_cache_hit_rate",
            "Cache hit rate",
        )

        self.cache_memory_usage = self._create_gauge(
            "malaria_system_cache_memory_usage_bytes",
            "Cache memory usage in bytes",
        )

    async def collect_system_metrics(self) -> None:
        """Collect system metrics periodically."""
        if not self.enabled:
            return

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            for i, percent in enumerate(cpu_percent):
                self.set_gauge(
                    "malaria_system_cpu_usage_percent", percent, {"cpu": f"cpu{i}"}
                )

            # Load average
            if hasattr(psutil, "getloadavg"):
                load_avg = psutil.getloadavg()
                self.set_gauge(
                    "malaria_system_cpu_load_average", load_avg[0], {"period": "1min"}
                )
                self.set_gauge(
                    "malaria_system_cpu_load_average", load_avg[1], {"period": "5min"}
                )
                self.set_gauge(
                    "malaria_system_cpu_load_average", load_avg[2], {"period": "15min"}
                )

            # Memory metrics
            memory = psutil.virtual_memory()
            self.set_gauge(
                "malaria_system_memory_usage_bytes", memory.total, {"type": "total"}
            )
            self.set_gauge(
                "malaria_system_memory_usage_bytes",
                memory.available,
                {"type": "available"},
            )
            self.set_gauge(
                "malaria_system_memory_usage_bytes", memory.used, {"type": "used"}
            )
            self.set_gauge(
                "malaria_system_memory_usage_bytes", memory.free, {"type": "free"}
            )
            self.set_gauge("malaria_system_memory_usage_percent", memory.percent)

            # Disk metrics
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    device = partition.device

                    self.set_gauge(
                        "malaria_system_disk_usage_bytes",
                        usage.total,
                        {"device": device, "type": "total"},
                    )
                    self.set_gauge(
                        "malaria_system_disk_usage_bytes",
                        usage.used,
                        {"device": device, "type": "used"},
                    )
                    self.set_gauge(
                        "malaria_system_disk_usage_bytes",
                        usage.free,
                        {"device": device, "type": "free"},
                    )
                    self.set_gauge(
                        "malaria_system_disk_usage_percent",
                        (usage.used / usage.total) * 100,
                        {"device": device},
                    )
                except (PermissionError, OSError):
                    # Skip inaccessible partitions
                    continue

            # Network metrics
            network_io = psutil.net_io_counters(pernic=True)
            for interface, stats in network_io.items():
                labels_sent = {"interface": interface, "direction": "sent"}
                labels_received = {"interface": interface, "direction": "received"}

                # Note: These are cumulative counters, so we set them directly
                bytes_metric = self.get_metric("malaria_system_network_bytes_total")
                packets_metric = self.get_metric("malaria_system_network_packets_total")

                if bytes_metric is not None and hasattr(bytes_metric, "_value"):
                    bytes_metric.labels(**labels_sent)._value.set(stats.bytes_sent)
                    bytes_metric.labels(**labels_received)._value.set(stats.bytes_recv)

                if packets_metric is not None and hasattr(packets_metric, "_value"):
                    packets_metric.labels(**labels_sent)._value.set(stats.packets_sent)
                    packets_metric.labels(**labels_received)._value.set(stats.packets_recv)

        except Exception as e:
            # Log error but don't fail the application
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error collecting system metrics: {e}")

    def start_collection(self) -> None:
        """Start periodic system metrics collection."""
        if not self.enabled:
            return

        async def collection_loop() -> None:
            while True:
                await self.collect_system_metrics()
                await asyncio.sleep(self._collection_interval)

        # Start the collection loop in the background
        asyncio.create_task(collection_loop())


class PrometheusMetrics:
    """
    Main Prometheus metrics manager.

    Coordinates all metric collection and provides a unified interface
    for accessing metrics from different collectors.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()

        # Initialize metric collectors
        self.api_metrics = APIMetrics(self.registry)
        self.ml_metrics = MLModelMetrics(self.registry)
        self.system_metrics = SystemMetrics(self.registry)

        # Start system metrics collection
        if settings.monitoring.enable_metrics:
            self.system_metrics.start_collection()

    def get_metrics_output(self, accept_header: str = "") -> tuple[str, str]:
        """
        Get metrics in the requested format.

        Args:
            accept_header: HTTP Accept header value

        Returns:
            Tuple of (content, content_type)
        """
        if not settings.monitoring.enable_metrics:
            return "", "text/plain"

        try:
            # Handle multiprocess mode (for production deployments)
            if hasattr(multiprocess, "MultiProcessCollector"):
                # In multiprocess mode, we need to aggregate metrics from all processes
                registry = CollectorRegistry()
                multiprocess.MultiProcessCollector(registry)
                content = generate_latest(registry)
            else:
                # Single process mode
                content = generate_latest(self.registry)

            # Determine content type based on Accept header
            if OPENMETRICS_CONTENT_TYPE in accept_header:
                return content.decode("utf-8"), OPENMETRICS_CONTENT_TYPE
            else:
                return content.decode("utf-8"), CONTENT_TYPE_LATEST

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error generating metrics: {e}")
            return f"# Error generating metrics: {e}\n", "text/plain"

    def get_health_metrics(self) -> dict[str, int | float]:
        """
        Get key health metrics for monitoring dashboards.

        Returns:
            Dictionary of key health metrics
        """
        if not settings.monitoring.enable_metrics:
            return {}

        try:
            # This would typically query the actual metric values
            # For now, return placeholder values
            return {
                "api_requests_per_second": 0.0,
                "api_error_rate": 0.0,
                "average_response_time": 0.0,
                "active_connections": 0,
                "cpu_usage_percent": 0.0,
                "memory_usage_percent": 0.0,
                "disk_usage_percent": 0.0,
                "model_prediction_rate": 0.0,
                "model_error_rate": 0.0,
            }
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error getting health metrics: {e}")
            return {}


# Global metrics instance
_metrics_instance: PrometheusMetrics | None = None


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """Reset the global metrics instance (for testing)."""
    global _metrics_instance
    _metrics_instance = None


class PredictionMetrics:
    """Metrics collector for prediction pipeline performance."""

    def __init__(self) -> None:
        """Initialize prediction metrics collector."""
        self.enabled = True

    def record_prediction_time(self, duration: float) -> None:
        """Record prediction processing time.

        Args:
            duration: Time taken for prediction in seconds
        """
        if not self.enabled:
            return
        # In a real implementation this would record to a metrics backend
        pass

    def record_data_processing_time(self, duration: float) -> None:
        """Record data processing time.

        Args:
            duration: Time taken for data processing in seconds
        """
        if not self.enabled:
            return
        # In a real implementation this would record to a metrics backend
        pass

    def increment_prediction_count(self) -> None:
        """Increment the prediction count metric."""
        if not self.enabled:
            return
        # In a real implementation this would increment a counter metric
        pass
