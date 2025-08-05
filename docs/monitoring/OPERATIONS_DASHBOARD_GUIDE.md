# Production Operations Dashboard - User Guide

This guide provides comprehensive instructions for using and maintaining the production operations dashboard for the Malaria Prediction Backend system.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Dashboard Components](#dashboard-components)
4. [Real-time Monitoring](#real-time-monitoring)
5. [Alert Management](#alert-management)
6. [Grafana Dashboards](#grafana-dashboards)
7. [API Endpoints](#api-endpoints)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Overview

The Production Operations Dashboard provides comprehensive visibility into the malaria prediction system including:

- **Real-time System Health**: Live monitoring of API, ML models, and infrastructure
- **Performance Metrics**: Request rates, response times, resource utilization
- **ML Model Monitoring**: Prediction accuracy, inference latency, model drift detection
- **Alert Management**: Automated alerting with escalation and runbook integration
- **Operational Integration**: Direct links to runbooks and incident response procedures

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI App    │    │   Prometheus    │    │    Grafana      │
│  + Metrics      │───▶│   Collection    │───▶│   Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Operations       │    │  Alertmanager   │    │   Real-time     │
│Dashboard        │    │   Routing       │    │   WebSocket     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Start the Monitoring Stack

```bash
# Start the enhanced monitoring stack
cd docker/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access the Dashboards

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Operations Dashboard | http://localhost:8000/operations/dashboard | - |
| Grafana | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |

### 3. Start Operations Monitoring

```bash
# Start monitoring via API
curl -X POST http://localhost:8000/operations/monitoring/start

# Or access the dashboard directly - monitoring starts automatically
open http://localhost:8000/operations/dashboard
```

## Dashboard Components

### System Health Overview

The main dashboard provides at-a-glance system health information:

#### Health Status Indicators
- **🟢 Healthy**: All systems operational
- **🟡 Warning**: Some issues detected, system still functional
- **🔴 Critical**: Major issues requiring immediate attention

#### Key Metrics Cards

1. **📊 API Request Rate**
   - Current requests per second
   - Trend visualization
   - Thresholds: Green (<50 RPS), Yellow (50-100 RPS), Red (>100 RPS)

2. **⚠️ Error Rate**
   - Current error percentage
   - 4xx and 5xx error breakdown
   - Thresholds: Green (<1%), Yellow (1-5%), Red (>5%)

3. **⏱️ Response Time**
   - P95 response time in milliseconds
   - Response time distribution
   - Thresholds: Green (<500ms), Yellow (500-1000ms), Red (>1000ms)

4. **🧠 ML Predictions**
   - Predictions per second
   - Model performance indicators
   - Accuracy trends

5. **💾 Cache Hit Rate**
   - Current cache performance
   - Hit/miss ratio trends
   - Thresholds: Green (>95%), Yellow (80-95%), Red (<80%)

6. **🗄️ Database Connections**
   - Active connection count
   - Connection pool utilization
   - Thresholds: Green (<15), Yellow (15-20), Red (>20)

7. **🖥️ System Resources**
   - CPU and memory usage
   - Disk utilization
   - Network I/O

### Real-time Charts

Each metric card includes a mini-chart showing the last 20 data points with automatic updates every 30 seconds.

## Real-time Monitoring

### WebSocket Connection

The dashboard uses WebSocket connections for real-time updates:

```javascript
// Connection status indicators
🔗 Connected    - Real-time updates active
❌ Disconnected - Connection lost, attempting to reconnect
```

### Data Update Frequency

- **System Health**: Every 30 seconds
- **Performance Metrics**: Every 30 seconds
- **Alert Status**: Immediate updates
- **Chart Data**: Rolling 20-point window

### Auto-refresh Features

- Automatic reconnection on connection loss
- Graceful degradation if WebSocket unavailable
- Fallback to periodic HTTP polling

## Alert Management

### Alert Severity Levels

1. **Critical** (🔴)
   - Service down
   - High error rates (>15%)
   - System resource exhaustion (>95%)
   - Immediate escalation required

2. **Warning** (🟡)
   - Performance degradation
   - Resource usage above normal (>85%)
   - ML model accuracy drift
   - Requires attention within defined timeframe

3. **Info** (🔵)
   - Rate limiting triggered
   - Maintenance notifications
   - Operational information

### Alert Components

Each alert displays:
- **Alert Name**: Clear, descriptive title
- **Description**: Detailed explanation of the issue
- **Severity**: Visual severity indicator
- **Team**: Responsible team (platform, ml-ops)
- **Triggered Time**: When the alert first fired
- **Runbook Link**: Direct link to troubleshooting procedures

### Alert Lifecycle

1. **Detection**: Prometheus evaluates alert rules
2. **Firing**: Alert conditions met for specified duration
3. **Notification**: Alertmanager routes to appropriate channels
4. **Display**: Alert appears in operations dashboard
5. **Resolution**: Conditions return to normal, alert clears

## Grafana Dashboards

### Available Dashboards

1. **🦟 Production Operations - Overview**
   - System health status with real-time indicators
   - API performance metrics with detailed breakdowns
   - Resource utilization across all components
   - Active alert summary with priority filtering

2. **🤖 ML Model Operations - Detailed Monitoring**
   - Model accuracy trends over time
   - Inference performance metrics (P50, P95, P99)
   - Prediction confidence distribution analysis
   - Model memory usage and optimization metrics
   - Feature engineering performance tracking
   - Batch processing statistics

3. **🏗️ System Infrastructure - Health & Performance**
   - CPU usage by core with threshold indicators
   - Memory utilization with available memory tracking
   - Disk usage by device with capacity planning
   - Network I/O with bandwidth utilization
   - Load average trending and capacity planning
   - Database connection pool detailed analysis
   - Process metrics and system health indicators

### Importing Dashboards

```bash
# Get dashboard configurations
curl http://localhost:8000/operations/config/grafana > dashboards.json

# Import via Grafana UI:
# 1. Login to Grafana (http://localhost:3000)
# 2. Go to "+" → Import
# 3. Paste JSON content or upload file
# 4. Configure data source (Prometheus)
```

### Dashboard Variables

Most dashboards include template variables for filtering:

- **instance**: Filter by specific application instances
- **model_type**: Filter by ML model type (lstm, transformer, ensemble)
- **model_version**: Filter by model version
- **time_range**: Adjustable time windows (1h, 6h, 24h, 7d)

## API Endpoints

### Dashboard Management

```bash
# Get dashboard summary
curl http://localhost:8000/operations/summary

# Get active alerts
curl http://localhost:8000/operations/alerts

# Get alert history (last 24 hours)
curl http://localhost:8000/operations/alerts/history?hours=24

# Get detailed health status
curl http://localhost:8000/operations/health/detailed
```

### Monitoring Control

```bash
# Start monitoring
curl -X POST http://localhost:8000/operations/monitoring/start

# Stop monitoring
curl -X POST http://localhost:8000/operations/monitoring/stop
```

### System Information

```bash
# Get system resources
curl http://localhost:8000/operations/system/resources

# Get database status
curl http://localhost:8000/operations/database/status

# Get cache status
curl http://localhost:8000/operations/cache/status

# Get ML models status
curl http://localhost:8000/operations/models/status
```

### Configuration Export

```bash
# Export Grafana dashboard configurations
curl http://localhost:8000/operations/config/grafana > grafana-dashboards.json

# Export Prometheus alert rules
curl http://localhost:8000/operations/config/prometheus-alerts > alert-rules.yml
```

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
1. Check if the FastAPI application is running
2. Verify WebSocket connection in browser developer tools
3. Check network connectivity to localhost:8000

```bash
# Check service status
curl http://localhost:8000/health

# Check operations endpoint
curl http://localhost:8000/operations/summary
```

#### No Metrics Data
1. Verify Prometheus is collecting metrics
2. Check if metrics endpoints are accessible
3. Confirm monitoring is started

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check if monitoring is active
curl http://localhost:8000/operations/summary
```

#### Alerts Not Firing
1. Check Prometheus alert rules
2. Verify Alertmanager configuration
3. Confirm notification channels

```bash
# Check Prometheus alerts
curl http://localhost:9090/api/v1/alerts

# Check Alertmanager status
curl http://localhost:9093/api/v1/status
```

#### WebSocket Connection Issues
1. Check browser WebSocket support
2. Verify firewall/proxy settings
3. Check server WebSocket endpoint

```javascript
// Test WebSocket connection manually
const ws = new WebSocket('ws://localhost:8000/ws/operations-dashboard');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Performance Issues

#### Slow Dashboard Loading
1. Check system resource usage
2. Verify database performance
3. Optimize chart rendering

```bash
# Check system resources
curl http://localhost:8000/operations/system/resources

# Check database connections
curl http://localhost:8000/operations/database/status
```

#### High Memory Usage
1. Monitor chart data retention
2. Check WebSocket connection count
3. Verify garbage collection

### Log Analysis

#### Application Logs
```bash
# Check FastAPI application logs
docker logs malaria-api-prod

# Check monitoring service logs
docker logs malaria-prometheus
docker logs malaria-grafana
```

#### Dashboard-specific Logs
```bash
# Check WebSocket connections
grep "WebSocket" /app/logs/application.log

# Check monitoring loop errors
grep "monitoring loop error" /app/logs/application.log
```

## Maintenance

### Regular Tasks

#### Daily
- [ ] Review active alerts and their trends
- [ ] Check system resource utilization
- [ ] Verify all monitoring targets are up
- [ ] Review ML model performance metrics

#### Weekly
- [ ] Analyze alert patterns and frequencies
- [ ] Review dashboard performance
- [ ] Check storage usage for metrics data
- [ ] Update alert thresholds based on trends

#### Monthly
- [ ] Review and update alert rules
- [ ] Optimize dashboard queries
- [ ] Clean up old alert history
- [ ] Update monitoring documentation

### Configuration Updates

#### Adding New Metrics
1. Add metric collection in the application code
2. Update Prometheus scraping configuration
3. Create or update Grafana dashboard panels
4. Add alert rules if necessary

#### Modifying Alert Thresholds
1. Edit alert rules in `prometheus/alert-rules.yml`
2. Reload Prometheus configuration
3. Test alert firing with controlled conditions
4. Update documentation

```bash
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

#### Dashboard Customization
1. Edit dashboard configuration in `operations_dashboard_config.json`
2. Restart the FastAPI application
3. Verify changes in the web interface
4. Update any dependent Grafana dashboards

### Backup and Recovery

#### Configuration Backup
```bash
# Backup monitoring configurations
tar -czf monitoring-config-$(date +%Y%m%d).tar.gz \
  docker/monitoring/ \
  src/malaria_predictor/monitoring/operations_dashboard_config.json
```

#### Data Backup
```bash
# Backup Prometheus data
docker exec malaria-prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus

# Backup Grafana data
docker exec malaria-grafana tar -czf /tmp/grafana-backup.tar.gz /var/lib/grafana
```

### Scaling Considerations

#### High Load Handling
- Configure additional Prometheus instances for high-cardinality metrics
- Use Grafana data source clustering
- Implement metric aggregation for long-term storage

#### Multi-Environment Setup
- Separate monitoring stacks per environment
- Cross-environment alert aggregation
- Unified dashboard views with environment filtering

## Security Considerations

### Access Control
- Configure authentication for Grafana dashboards
- Restrict Prometheus access to internal networks
- Use HTTPS for external dashboard access

### Data Privacy
- Avoid logging sensitive user data in metrics
- Implement metric data retention policies
- Ensure compliance with data protection regulations

### Network Security
- Use internal networks for monitoring communication
- Configure firewall rules for monitoring ports
- Enable TLS for inter-service communication

## Support and Resources

### Documentation
- [Production Monitoring Guide](PRODUCTION_MONITORING_GUIDE.md)
- [Alert Runbooks](../cicd/runbooks/)
- [System Architecture](../development/architecture-overview.md)

### Contact Information
- **Platform Team**: platform@malaria-prediction.com
- **ML-Ops Team**: ml-ops@malaria-prediction.com
- **On-call Support**: oncall@malaria-prediction.com

### External Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

For additional support or questions about the operations dashboard, please refer to the internal documentation or contact the platform team.
