# Disaster Recovery System for Malaria Prediction Backend

## Overview

This comprehensive disaster recovery (DR) system provides automated backup, recovery, failover, and business continuity capabilities for the Malaria Prediction System. The system is designed to meet stringent Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) while ensuring data integrity and service availability.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Components](#components)
3. [Installation and Setup](#installation-and-setup)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## System Architecture

The DR system consists of several interconnected components working together to provide comprehensive disaster recovery capabilities:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Disaster Recovery System                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Backup          │  │ Recovery        │  │ Failover        │  │
│  │ Orchestrator    │  │ Testing         │  │ Orchestrator    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Data Corruption │  │ Monitoring      │  │ Scheduler       │  │
│  │ Detection       │  │ Integration     │  │ Service         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Storage and Services                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Local Backup    │  │ S3 Remote       │  │ Kubernetes      │  │
│  │ Storage         │  │ Storage         │  │ Cluster         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ TimescaleDB     │  │ Redis Cache     │  │ Prometheus      │  │
│  │ Database        │  │                 │  │ Monitoring      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Backup Orchestrator (`backup_orchestrator.py`)

**Purpose**: Automated backup creation, encryption, and storage management

**Key Features**:
- Multi-component backup (database, ML models, configuration, logs)
- Encrypted backup storage with AES-256
- S3 remote storage integration
- Backup integrity verification
- Retention policy management
- Metadata generation for each backup

**Usage**:
```bash
# Create complete system backup
python disaster_recovery/backup_orchestrator.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  --s3-bucket malaria-prediction-dr-backups \
  backup --type complete --upload

# Verify backup integrity
python disaster_recovery/backup_orchestrator.py \
  verify /var/backups/malaria-prediction/complete/backup_file.tar.gz
```

### 2. Disaster Recovery Testing Framework (`disaster_recovery_tester.py`)

**Purpose**: Automated testing of DR procedures and system validation

**Key Features**:
- Backup integrity testing
- Application recovery simulation
- Database recovery testing
- Performance benchmarking after recovery
- Comprehensive system validation
- Metrics collection and reporting

**Usage**:
```bash
# Run comprehensive DR test
python disaster_recovery/disaster_recovery_tester.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  comprehensive

# Test specific component
python disaster_recovery/disaster_recovery_tester.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  application-recovery
```

### 3. Data Corruption Detection (`data_corruption_detector.py`)

**Purpose**: Real-time data integrity monitoring and automated recovery

**Key Features**:
- Continuous data quality monitoring
- Anomaly detection in time-series data
- Automated corruption recovery
- Data integrity metrics
- Alert generation for corruption events
- Recovery point creation and restoration

**Usage**:
```bash
# Start continuous monitoring
python disaster_recovery/data_corruption_detector.py \
  --database-url $DATABASE_URL \
  monitor

# Run single corruption scan
python disaster_recovery/data_corruption_detector.py \
  --database-url $DATABASE_URL \
  scan
```

### 4. Failover Orchestrator (`failover_orchestrator.py`)

**Purpose**: Automated service failover and blue-green deployment management

**Key Features**:
- Blue-green deployment automation
- Database failover with replica promotion
- Service health monitoring
- Automated failover decision making
- Rollback capabilities
- Multi-region failover support

**Usage**:
```bash
# Start automated monitoring with failover
python disaster_recovery/failover_orchestrator.py \
  --primary-db $DATABASE_URL \
  --replica-db $REPLICA_DB_URL \
  monitor

# Manual blue-green failover
python disaster_recovery/failover_orchestrator.py \
  --primary-db $DATABASE_URL \
  blue-green-failover
```

### 5. Monitoring Integration (`dr_monitoring_integration.py`)

**Purpose**: Integration with existing monitoring and alerting systems

**Key Features**:
- Prometheus metrics export
- Grafana dashboard integration
- Alert routing and management
- Operations dashboard integration
- Real-time DR status reporting
- Performance metrics tracking

**Usage**:
```bash
# Start DR monitoring service
python disaster_recovery/dr_monitoring_integration.py \
  --metrics-port 9091 \
  --webhook-url https://alerts.company.com/webhook \
  --slack-webhook $SLACK_WEBHOOK_URL
```

### 6. DR Scheduler (`dr_scheduler.py`)

**Purpose**: Automated scheduling of DR operations and maintenance

**Key Features**:
- Configurable backup schedules
- Automated DR testing execution
- Maintenance window coordination
- Task execution logging
- Manual job triggering
- Retention policy enforcement

**Usage**:
```bash
# Start DR scheduler service
python disaster_recovery/dr_scheduler.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  start

# Check scheduler status
python disaster_recovery/dr_scheduler.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  status
```

## Installation and Setup

### Prerequisites

1. **Python 3.9+** with required packages:
   ```bash
   pip install -r disaster_recovery/requirements.txt
   ```

2. **System Dependencies**:
   ```bash
   # PostgreSQL client tools
   apt-get install postgresql-client

   # Redis tools
   apt-get install redis-tools

   # Kubernetes client
   curl -LO https://dl.k8s.io/release/stable.txt
   curl -LO "https://dl.k8s.io/release/$(cat stable.txt)/bin/linux/amd64/kubectl"
   ```

3. **Cloud Provider CLI** (if using S3):
   ```bash
   pip install boto3
   aws configure  # or use IAM roles
   ```

### Environment Setup

1. **Create backup directories**:
   ```bash
   sudo mkdir -p /var/backups/malaria-prediction/{database,models,config,logs,complete}
   sudo chown -R $USER:$USER /var/backups/malaria-prediction
   ```

2. **Set up encryption keys**:
   ```bash
   # Generate encryption key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

   # Store in environment or secrets management
   export DR_ENCRYPTION_KEY="your-encryption-key-here"
   ```

3. **Configure S3 bucket** (optional):
   ```bash
   aws s3 mb s3://malaria-prediction-dr-backups
   aws s3api put-bucket-versioning \
     --bucket malaria-prediction-dr-backups \
     --versioning-configuration Status=Enabled
   ```

### Kubernetes Integration

1. **Apply RBAC configuration**:
   ```yaml
   # disaster_recovery/k8s/rbac.yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: dr-service-account
     namespace: malaria-prediction-production
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRole
   metadata:
     name: dr-cluster-role
   rules:
   - apiGroups: ["apps"]
     resources: ["deployments", "deployments/scale"]
     verbs: ["get", "list", "patch", "update"]
   - apiGroups: [""]
     resources: ["services", "pods"]
     verbs: ["get", "list", "patch", "update"]
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: dr-cluster-role-binding
   subjects:
   - kind: ServiceAccount
     name: dr-service-account
     namespace: malaria-prediction-production
   roleRef:
     kind: ClusterRole
     name: dr-cluster-role
     apiGroup: rbac.authorization.k8s.io
   ```

2. **Deploy DR monitoring service**:
   ```yaml
   # disaster_recovery/k8s/monitoring-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: dr-monitoring
     namespace: malaria-prediction-production
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: dr-monitoring
     template:
       metadata:
         labels:
           app: dr-monitoring
       spec:
         serviceAccountName: dr-service-account
         containers:
         - name: dr-monitoring
           image: malaria-prediction-dr:latest
           ports:
           - containerPort: 9091
             name: metrics
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: database-secret
                 key: url
           - name: REDIS_URL
             valueFrom:
               secretKeyRef:
                 name: redis-secret
                 key: url
   ```

## Configuration

### Backup Configuration

Create `disaster_recovery/backup_config.json`:
```json
{
  "retention_days": 30,
  "compression_enabled": true,
  "encryption_enabled": true,
  "s3_bucket": "malaria-prediction-dr-backups",
  "backup_verification": true,
  "components": {
    "database": {
      "enabled": true,
      "backup_types": ["full", "incremental"]
    },
    "models": {
      "enabled": true,
      "include_training_data": false
    },
    "configuration": {
      "enabled": true,
      "exclude_secrets": true
    }
  }
}
```

### Scheduler Configuration

Create `disaster_recovery/dr_schedule_config.json`:
```json
{
  "backup_schedules": {
    "database_full": {
      "schedule": "cron",
      "cron": "0 2 * * *",
      "enabled": true,
      "retention_days": 30
    },
    "complete_system": {
      "schedule": "cron",
      "cron": "0 1 * * 0",
      "enabled": true,
      "retention_days": 84
    }
  },
  "testing_schedules": {
    "comprehensive_dr_test": {
      "schedule": "cron",
      "cron": "0 2 1 * *",
      "enabled": true
    }
  },
  "maintenance_windows": {
    "primary": {
      "start_time": "01:00",
      "end_time": "05:00",
      "timezone": "UTC",
      "days": ["sunday"]
    }
  }
}
```

### Monitoring Configuration

Set environment variables:
```bash
export DR_METRICS_PORT=9091
export DR_WEBHOOK_URL="https://alerts.company.com/webhook"
export DR_SLACK_WEBHOOK="https://hooks.slack.com/your-webhook"
export DR_DASHBOARD_API="https://dashboard.company.com/api"
export DR_DASHBOARD_KEY="your-api-key"
```

## Usage

### Daily Operations

1. **Monitor DR System Status**:
   ```bash
   # Check backup status
   curl http://localhost:9091/metrics | grep dr_last_backup

   # Check recent DR test results
   python disaster_recovery/dr_scheduler.py status | jq '.recent_executions'
   ```

2. **Manual Backup Creation**:
   ```bash
   # Emergency backup before maintenance
   python disaster_recovery/backup_orchestrator.py \
     --database-url $DATABASE_URL \
     --redis-url $REDIS_URL \
     backup --type complete --upload
   ```

3. **Health Checks**:
   ```bash
   # Check service health
   python disaster_recovery/failover_orchestrator.py \
     --primary-db $DATABASE_URL \
     health

   # Check data integrity
   python disaster_recovery/data_corruption_detector.py \
     --database-url $DATABASE_URL \
     scan
   ```

### Emergency Procedures

1. **Service Failover**:
   ```bash
   # Emergency blue-green failover
   python disaster_recovery/failover_orchestrator.py \
     --primary-db $DATABASE_URL \
     blue-green-failover
   ```

2. **Data Recovery**:
   ```bash
   # List available backups
   python disaster_recovery/backup_orchestrator.py \
     --database-url $DATABASE_URL \
     list

   # Restore from specific backup
   python disaster_recovery/backup_orchestrator.py \
     --database-url $DATABASE_URL \
     restore /path/to/backup/file.tar.gz
   ```

3. **Corruption Recovery**:
   ```bash
   # Run corruption detection and auto-recovery
   python disaster_recovery/data_corruption_detector.py \
     --database-url $DATABASE_URL \
     monitor
   ```

### Testing and Validation

1. **Run DR Tests**:
   ```bash
   # Comprehensive DR test
   python disaster_recovery/disaster_recovery_tester.py \
     --database-url $DATABASE_URL \
     --redis-url $REDIS_URL \
     comprehensive

   # Backup integrity test
   python disaster_recovery/disaster_recovery_tester.py \
     --database-url $DATABASE_URL \
     backup-integrity
   ```

2. **Performance Validation**:
   ```bash
   # Run performance benchmark
   python disaster_recovery/disaster_recovery_tester.py \
     --database-url $DATABASE_URL \
     performance-benchmark
   ```

## Monitoring and Alerting

### Prometheus Metrics

The DR system exports the following key metrics:

- `dr_backup_operations_total`: Total backup operations by component and status
- `dr_backup_duration_seconds`: Backup operation duration
- `dr_recovery_operations_total`: Total recovery operations
- `dr_data_corruption_alerts_total`: Data corruption alerts by severity
- `dr_failover_operations_total`: Failover operations by type
- `dr_service_health_score`: Service health scores (0.0-1.0)

### Grafana Dashboard

Import the DR dashboard configuration:
```bash
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @disaster_recovery/grafana/dr-dashboard.json
```

### Alert Rules

Configure Prometheus alert rules:
```yaml
# disaster_recovery/prometheus/dr-alerts.yml
groups:
- name: disaster_recovery
  rules:
  - alert: BackupFailed
    expr: increase(dr_backup_operations_total{status="failure"}[1h]) > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "DR backup operation failed"

  - alert: DataCorruption
    expr: increase(dr_data_corruption_alerts_total{severity="high"}[15m]) > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "High severity data corruption detected"

  - alert: ServiceHealthDegraded
    expr: dr_service_health_score < 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Service health score below threshold"
```

## Testing

### Automated Testing Schedule

The DR system includes automated testing on the following schedule:

- **Daily**: Backup verification and data corruption scans
- **Weekly**: Application recovery and database recovery simulation
- **Monthly**: Comprehensive DR test including all components
- **Quarterly**: Full disaster recovery exercise with stakeholder involvement

### Manual Testing Procedures

1. **Backup and Restore Test**:
   ```bash
   # Create test backup
   python disaster_recovery/backup_orchestrator.py backup --type database

   # Verify backup integrity
   python disaster_recovery/backup_orchestrator.py verify $BACKUP_FILE

   # Test restoration (to test database)
   python disaster_recovery/backup_orchestrator.py restore $BACKUP_FILE --target-db test_db
   ```

2. **Failover Test**:
   ```bash
   # Test blue-green deployment switch
   python disaster_recovery/failover_orchestrator.py blue-green-failover

   # Verify service health after failover
   python disaster_recovery/failover_orchestrator.py health
   ```

3. **Data Corruption Recovery Test**:
   ```bash
   # Inject test corruption (in test environment only!)
   python disaster_recovery/data_corruption_detector.py inject-test-corruption

   # Verify detection and recovery
   python disaster_recovery/data_corruption_detector.py scan
   ```

## Troubleshooting

### Common Issues

1. **Backup Failures**:
   ```bash
   # Check disk space
   df -h /var/backups/malaria-prediction

   # Check database connectivity
   pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER

   # Check S3 permissions
   aws s3 ls s3://malaria-prediction-dr-backups/
   ```

2. **Recovery Issues**:
   ```bash
   # Check backup file integrity
   python disaster_recovery/backup_orchestrator.py verify $BACKUP_FILE

   # Check target database connectivity
   psql $TARGET_DATABASE_URL -c "SELECT version();"

   # Review recovery logs
   tail -f /var/log/malaria-prediction/backup.log
   ```

3. **Failover Problems**:
   ```bash
   # Check Kubernetes cluster status
   kubectl get nodes
   kubectl get pods -n malaria-prediction-production

   # Check service health
   curl -f https://api.malaria-prediction.com/health/liveness

   # Review failover logs
   tail -f /var/log/malaria-prediction/failover.log
   ```

### Log Locations

- **Backup Operations**: `/var/log/malaria-prediction/backup.log`
- **Recovery Testing**: `/var/log/malaria-prediction/dr-testing.log`
- **Data Corruption**: `/var/log/malaria-prediction/data-corruption.log`
- **Failover Operations**: `/var/log/malaria-prediction/failover.log`
- **Monitoring**: `/var/log/malaria-prediction/dr-monitoring.log`
- **Scheduler**: `/var/log/malaria-prediction/dr-scheduler.log`

### Support Contacts

For DR system issues:
- **Primary**: DevOps Team - devops@company.com
- **Secondary**: Platform Engineering - platform@company.com
- **Emergency**: On-call Engineer - +1-555-ONCALL

## Contributing

To contribute to the DR system:

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests for new functionality
4. Update documentation
5. Submit a pull request with detailed description

## License

This disaster recovery system is part of the Malaria Prediction Backend project and follows the same licensing terms.

---

**Last Updated**: 2024-07-24
**Version**: 1.0.0
**Maintainer**: DevOps Team
