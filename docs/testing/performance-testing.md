# Malaria Prediction API - Performance Testing & Optimization

This directory contains a comprehensive performance testing and optimization framework for the Malaria Prediction API. The system provides load testing, database optimization, caching strategies, real-time monitoring, and CI/CD integration.

## 🚀 Quick Start

### Run Load Tests

```bash
# Basic smoke test
locust -f performance/locustfile.py --host http://localhost:8000 --users 5 --spawn-rate 1 --run-time 2m --headless

# Full load test
python performance/test_scenarios.py --scenarios load_test

# Run all test scenarios
python performance/test_scenarios.py
```

### Database Optimization

```python
from performance.database_optimization import DatabaseOptimizer

optimizer = DatabaseOptimizer()

# Create performance indexes
await optimizer.create_indexes()

# Analyze query performance
analysis = await optimizer.analyze_query_performance(
    "SELECT * FROM era5_data_points WHERE latitude = %s AND longitude = %s",
    (0.0, 0.0)
)

# Benchmark common queries
results = await optimizer.benchmark_queries()
```

### Cache Optimization

```python
from performance.cache_optimization import get_cache_optimizer

cache = await get_cache_optimizer()

# Cache ML model
await cache.cache_model("lstm", "v1.0", model_data)

# Cache prediction results
await cache.cache_prediction(lat, lon, date, model_type, prediction)

# Get cache statistics
stats = await cache.get_cache_statistics()
```

### Performance Monitoring

```python
from performance.monitoring_dashboard import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()

# Start real-time monitoring
await dashboard.start_monitoring()

# Access dashboard at http://localhost:8000/dashboard
```

## 📊 Components

### 1. Load Testing Framework (`locustfile.py`)

Comprehensive Locust-based load testing with realistic user behavior patterns:

- **Realistic User Profiles**: Research analyst, dashboard user, bulk processor, API explorer
- **Multiple Test Scenarios**: Single predictions, batch processing, spatial grids, time series
- **Concurrent Load Simulation**: Up to 500+ concurrent users
- **Performance Metrics**: Response times, throughput, error rates, resource usage

#### User Behavior Profiles

| Profile | Weight | Primary Tasks | Wait Time | Description |
|---------|--------|---------------|-----------|-------------|
| Research Analyst | 40% | Single predictions, time series | 2-8s | Detailed analysis workflows |
| Dashboard User | 35% | Quick predictions, health checks | 1-3s | Frequent lightweight queries |
| Bulk Processor | 15% | Batch analysis, spatial grids | 5-15s | Large dataset processing |
| API Explorer | 10% | Mixed exploration | 0.5-2s | New user discovery patterns |

### 2. Database Optimization (`database_optimization.py`)

Advanced database performance optimization:

- **Intelligent Indexing**: Spatial-temporal indexes, partial indexes, composite indexes
- **Query Optimization**: Execution plan analysis, query rewriting recommendations
- **Connection Pool Tuning**: Dynamic pool sizing, connection health monitoring
- **Performance Analytics**: Query benchmarking, table statistics analysis

#### Indexing Strategies

```sql
-- Spatial-temporal indexes for climate data
CREATE INDEX CONCURRENTLY idx_era5_spatial_temporal
ON era5_data_points (latitude, longitude, timestamp);

-- Partial indexes for recent data
CREATE INDEX CONCURRENTLY idx_era5_recent
ON era5_data_points (timestamp, latitude, longitude)
WHERE timestamp >= NOW() - INTERVAL '1 year';

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_era5_temp_humidity
ON era5_data_points (temperature_2m, relative_humidity_2m);
```

### 3. Redis Caching System (`cache_optimization.py`)

Intelligent caching strategy for ML models and environmental data:

- **ML Model Caching**: Long-term storage of trained models (7-day TTL)
- **Prediction Caching**: Spatial prediction results (6-hour TTL)
- **Environmental Data Caching**: Climate data with appropriate TTLs (24-hour TTL)
- **Batch Operation Support**: Pipeline operations for high throughput
- **Cache Performance Monitoring**: Hit rates, memory usage, eviction tracking

#### Cache Key Strategy

```python
# Model caching
malaria:model:{model_type}:{version}

# Prediction caching
malaria:prediction:{lat}:{lon}:{date}:{model}

# Environmental data caching
malaria:env:{source}:{lat}:{lon}:{date}

# Spatial grid caching
malaria:spatial:{bounds_hash}:{date}:{resolution}
```

### 4. Real-time Monitoring Dashboard (`monitoring_dashboard.py`)

Comprehensive performance monitoring with web-based dashboard:

- **Real-time Metrics**: CPU, memory, database connections, cache performance
- **WebSocket Updates**: Live metric streaming to connected clients
- **Performance Alerting**: Configurable alert rules with thresholds
- **Prometheus Integration**: Metrics export for external monitoring systems
- **HTML Dashboard**: Interactive charts and performance visualizations

#### Alert Rules

| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| High Response Time | P95 > 2s | 60s | Warning |
| Critical Response Time | P95 > 5s | 30s | Critical |
| High Error Rate | > 5% | 120s | Warning |
| Low Cache Hit Rate | < 70% | 300s | Warning |
| High DB Connections | > 80% | 60s | Warning |
| High CPU Usage | > 85% | 180s | Warning |
| High Memory Usage | > 90% | 120s | Critical |

### 5. Test Scenarios Runner (`test_scenarios.py`)

Automated test scenario execution with comprehensive reporting:

- **Multiple Test Types**: Smoke, load, stress, spike, endurance tests
- **Performance Validation**: Automated pass/fail criteria
- **Detailed Reporting**: HTML reports, CSV data, performance analysis
- **Baseline Comparison**: Regression detection against historical performance

#### Test Scenarios

| Scenario | Users | Duration | Purpose |
|----------|--------|----------|---------|
| Smoke Test | 5 | 2m | Basic functionality verification |
| Load Test | 50 | 10m | Normal load conditions |
| Stress Test | 200 | 15m | High load stress testing |
| Spike Test | 500 | 5m | Sudden traffic spike simulation |
| Endurance Test | 100 | 60m | Long-duration stability testing |

### 6. CI/CD Integration (`ci_cd_integration.py`)

Automated performance testing in CI/CD pipelines:

- **GitHub Actions Workflow**: Automated PR and merge testing
- **Jenkins Pipeline**: Enterprise CI/CD integration
- **Performance Gates**: Automated pass/fail criteria
- **Baseline Management**: Performance regression detection
- **Comprehensive Reporting**: PR comments, HTML reports, JUnit XML

## 🎯 Performance Targets

### API Performance Goals

| Metric | Target | Monitoring |
|--------|--------|------------|
| P95 Response Time | < 2 seconds | ✅ Automated alerts |
| Throughput | > 100 RPS | ✅ Load testing |
| Error Rate | < 1% | ✅ Real-time monitoring |
| Cache Hit Rate | > 70% | ✅ Redis monitoring |
| Database Connections | < 80% of pool | ✅ Connection monitoring |

### Resource Utilization Targets

| Resource | Target | Monitoring |
|----------|--------|------------|
| CPU Usage | < 80% | ✅ System monitoring |
| Memory Usage | < 85% | ✅ Memory alerts |
| Database Query Time | < 100ms P95 | ✅ Query profiling |
| Cache Memory | < 512MB | ✅ Redis monitoring |

## 🔧 Configuration

### Environment Variables

```bash
# Load Testing Configuration
LOAD_TEST_API_HOST=http://localhost:8000
LOAD_TEST_SPAWN_RATE=10
LOAD_TEST_TARGET_P95_RESPONSE_TIME=2000
LOAD_TEST_TARGET_THROUGHPUT=100

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/malaria
LOAD_TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/malaria_test

# Redis Configuration
REDIS_URL=redis://localhost:6379
LOAD_TEST_REDIS_URL=redis://localhost:6379/1

# Monitoring Configuration
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
GRAFANA_DASHBOARD_URL=http://localhost:3000
```

### Performance Configuration (`performance/ci_cd_config.yml`)

```yaml
enabled: true
run_on_pr: true
run_on_merge: true

performance_gates:
  max_p95_response_time: 2000  # ms
  min_throughput: 50           # RPS
  max_error_rate: 0.01         # 1%
  min_cache_hit_rate: 0.7      # 70%

notification:
  slack_webhook: null
  email_recipients: []
  github_status: true

artifact_retention_days: 30
baseline_branch: main
```

## 🚀 Running Performance Tests

### Local Development

```bash
# 1. Start services
docker-compose up -d postgres redis

# 2. Initialize database
python -m malaria_predictor.cli init-database

# 3. Start API server
uvicorn src.malaria_predictor.api.main:app --reload

# 4. Run performance tests
python performance/test_scenarios.py --scenarios load_test

# 5. View monitoring dashboard
# Navigate to http://localhost:8000/dashboard
```

### CI/CD Integration

```bash
# Generate GitHub Actions workflow
python performance/ci_cd_integration.py --generate-workflow github

# Generate Jenkins pipeline
python performance/ci_cd_integration.py --generate-workflow jenkins

# Run CI performance tests
python performance/ci_cd_integration.py --run-all --update-baseline
```

### Docker-based Testing

```bash
# Build performance testing image
docker build -f performance/Dockerfile -t malaria-perf-test .

# Run load tests in container
docker run --network host malaria-perf-test \
  python performance/test_scenarios.py --scenarios load_test
```

## 📈 Monitoring and Alerting

### Prometheus Metrics

The system exports comprehensive Prometheus metrics:

```python
# API request metrics
malaria_api_requests_total{endpoint, method, status}
malaria_api_request_duration_seconds{endpoint, method}

# System metrics
malaria_system_cpu_usage_percent
malaria_system_memory_usage_percent

# Database metrics
malaria_database_connections{state}
malaria_database_query_duration_seconds

# Cache metrics
malaria_cache_operations_total{operation, status}
malaria_cache_hit_rate
malaria_cache_memory_usage_bytes

# ML metrics
malaria_prediction_latency_seconds{model_type}
malaria_active_users
```

### Grafana Dashboard

Import the provided Grafana dashboard configuration:

```bash
# Import dashboard
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @performance/grafana_dashboard.json
```

## 🔍 Troubleshooting

### Common Issues

#### High Response Times
```bash
# Check database query performance
python -c "
from performance.database_optimization import DatabaseOptimizer
import asyncio
optimizer = DatabaseOptimizer()
asyncio.run(optimizer.benchmark_queries())
"

# Analyze slow queries
# Check database logs for slow query analysis
```

#### Low Cache Hit Rate
```bash
# Check cache statistics
python -c "
from performance.cache_optimization import get_cache_optimizer
import asyncio
cache = asyncio.run(get_cache_optimizer())
stats = asyncio.run(cache.get_cache_statistics())
print(stats)
"

# Optimize cache TTL settings
# Review cache key patterns
```

#### Database Connection Pool Exhaustion
```bash
# Check connection pool status
python -c "
from src.malaria_predictor.database.session import get_connection_pool_status
import asyncio
status = asyncio.run(get_connection_pool_status())
print(status)
"

# Tune connection pool settings in src/malaria_predictor/database/session.py
```

### Performance Debugging

```bash
# Profile API endpoints
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn src.malaria_predictor.api.main:app

# Memory profiling
pip install memory-profiler
mprof run python performance/test_scenarios.py
mprof plot

# Database query analysis
# Enable query logging in PostgreSQL
# Analyze slow queries with EXPLAIN ANALYZE
```

## 📚 Best Practices

### Load Testing
- Start with smoke tests before load tests
- Use realistic test data and user patterns
- Monitor system resources during tests
- Establish performance baselines
- Run tests in isolated environments

### Database Optimization
- Create indexes for common query patterns
- Use EXPLAIN ANALYZE for query optimization
- Monitor connection pool utilization
- Update table statistics regularly
- Use appropriate data types and constraints

### Caching Strategy
- Cache at multiple levels (application, database, CDN)
- Use appropriate TTL values for different data types
- Monitor cache hit rates and memory usage
- Implement cache warming strategies
- Handle cache failures gracefully

### Monitoring and Alerting
- Set up comprehensive monitoring for all components
- Use appropriate alert thresholds to avoid noise
- Implement escalation procedures for critical alerts
- Create dashboards for different stakeholders
- Regularly review and update monitoring configuration

This performance testing framework provides a solid foundation for ensuring the Malaria Prediction API can handle production traffic with excellent performance characteristics. The comprehensive monitoring and optimization capabilities help maintain performance over time and quickly identify any performance regressions.
