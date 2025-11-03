# Disaster Recovery Procedures for Malaria Prediction System

## Overview

This document provides comprehensive disaster recovery procedures for the Malaria Prediction Backend system, covering scenarios from data corruption to complete system failure. These procedures are designed to minimize downtime and ensure business continuity with defined Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO).

## Table of Contents

1. [Recovery Objectives](#recovery-objectives)
2. [System Architecture Overview](#system-architecture-overview)
3. [Backup Strategy](#backup-strategy)
4. [Disaster Recovery Scenarios](#disaster-recovery-scenarios)
5. [Recovery Procedures](#recovery-procedures)
6. [Testing and Validation](#testing-and-validation)
7. [Emergency Contacts](#emergency-contacts)

## Recovery Objectives

### Service Level Definitions

| Component | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) | Business Impact |
|-----------|-------------------------------|-------------------------------|------------------|
| **Database (TimescaleDB)** | 15 minutes | 2 hours | Critical - All predictions rely on this |
| **ML Models** | 24 hours | 1 hour | High - Predictions become stale |
| **API Service** | N/A | 30 minutes | Critical - User-facing service |
| **Configuration** | 24 hours | 1 hour | Medium - Required for deployment |
| **Redis Cache** | 1 hour | 30 minutes | Medium - Performance impact |
| **Monitoring** | 4 hours | 1 hour | Low - Operational visibility |

### Business Continuity Priorities

1. **P0 - Critical**: API service availability for predictions
2. **P1 - High**: Database integrity and availability
3. **P2 - Medium**: ML model freshness and accuracy
4. **P3 - Low**: Historical data and analytics

## System Architecture Overview

### Production Infrastructure

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  Kubernetes     │────│   Database      │
│   (NGINX)       │    │   Cluster       │    │  (TimescaleDB)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │──────────────│     Redis       │──────────────│
                        │    (Cache)      │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   Monitoring    │
                        │ (Prometheus/    │
                        │   Grafana)      │
                        └─────────────────┘
```

### Backup Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Primary       │────│   Local Backup  │────│   S3 Remote     │
│   System        │    │   Storage       │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Encrypted     │──────────────┘
                        │   Archives      │
                        └─────────────────┘
```

## Backup Strategy

### Automated Backup Schedule

| Component | Frequency | Retention | Location | Encryption |
|-----------|-----------|-----------|----------|------------|
| **Database Full** | Daily (2 AM UTC) | 30 days | Local + S3 | AES-256 |
| **Database Incremental** | Every 4 hours | 7 days | Local + S3 | AES-256 |
| **ML Models** | Daily (3 AM UTC) | 60 days | Local + S3 | AES-256 |
| **Configuration** | Daily (1 AM UTC) | 90 days | Local + S3 | AES-256 |
| **Redis Data** | Every 6 hours | 7 days | Local + S3 | AES-256 |
| **Application Logs** | Daily (4 AM UTC) | 30 days | Local + S3 | AES-256 |
| **Complete System** | Weekly (Sunday 1 AM) | 12 weeks | S3 Only | AES-256 |

### Backup Commands

```bash
# Create complete system backup
python disaster_recovery/backup_orchestrator.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  --s3-bucket malaria-prediction-dr-backups \
  backup --type complete --upload

# Create database-only backup
python disaster_recovery/backup_orchestrator.py \
  --database-url $DATABASE_URL \
  --redis-url $REDIS_URL \
  backup --type database --upload

# Verify backup integrity
python disaster_recovery/backup_orchestrator.py \
  verify /var/backups/malaria-prediction/complete/backup_file.tar.gz
```

## Disaster Recovery Scenarios

### Scenario 1: Database Corruption or Loss

**Symptoms:**
- Database connection failures
- Data integrity errors
- Query timeouts or failures
- Application errors related to data access

**Impact:** Critical - Complete service disruption

**Recovery Procedure:** [See Database Recovery](#database-recovery)

### Scenario 2: Application Pod/Container Failure

**Symptoms:**
- HTTP 5xx errors from API
- Pod restart loops
- Health check failures
- Application unavailable

**Impact:** High - Service disruption with automatic recovery

**Recovery Procedure:** [See Application Recovery](#application-recovery)

### Scenario 3: Kubernetes Cluster Failure

**Symptoms:**
- Unable to access Kubernetes API
- All pods unresponsive
- Node failures
- Network partitioning

**Impact:** Critical - Complete infrastructure failure

**Recovery Procedure:** [See Cluster Recovery](#cluster-recovery)

### Scenario 4: Data Center/Region Outage

**Symptoms:**
- Complete loss of access to primary region
- Network connectivity issues
- Infrastructure provider outage

**Impact:** Critical - Requires failover to secondary region

**Recovery Procedure:** [See Multi-Region Failover](#multi-region-failover)

### Scenario 5: ML Model Corruption or Performance Degradation

**Symptoms:**
- Prediction accuracy drops significantly
- Model inference errors
- Unusual prediction patterns
- Model loading failures

**Impact:** Medium - Predictions become unreliable

**Recovery Procedure:** [See Model Recovery](#model-recovery)

## Recovery Procedures

### Database Recovery

#### Prerequisites
- Access to backup files (local or S3)
- Database administrative credentials
- Kubernetes cluster access

#### Recovery Steps

1. **Assessment and Preparation**
   ```bash
   # Check database status
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -c "SELECT version();"

   # List available backups
   python disaster_recovery/backup_orchestrator.py \
     --database-url $DATABASE_URL \
     --redis-url $REDIS_URL \
     list-backups --component database
   ```

2. **Stop Application Services**
   ```bash
   # Scale down API pods to prevent data access during recovery
   kubectl scale deployment malaria-predictor-api \
     -n malaria-prediction-production --replicas=0

   # Verify no active connections
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -d malaria_prediction -c "
     SELECT count(*) FROM pg_stat_activity
     WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%';"
   ```

3. **Create Recovery Database**
   ```bash
   # Create new database for recovery
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -c "CREATE DATABASE malaria_prediction_recovery;"
   ```

4. **Restore from Backup**
   ```bash
   # Download and decrypt backup if from S3
   python disaster_recovery/backup_orchestrator.py \
     --s3-bucket malaria-prediction-dr-backups \
     download --backup-file database_full_20240724_020000.sql.gz.enc \
     --output /tmp/recovery_backup.sql.gz

   # Restore database
   kubectl exec -i postgres-0 -n malaria-prediction-production -- \
     pg_restore -U postgres -d malaria_prediction_recovery \
     --verbose --clean --no-owner --no-privileges \
     < /tmp/recovery_backup.sql.gz
   ```

5. **Validate Data Integrity**
   ```bash
   # Run data integrity checks
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -d malaria_prediction_recovery -c "
     -- Check record counts
     SELECT 'environmental_data' as table_name, count(*) FROM environmental_data
     UNION ALL
     SELECT 'predictions', count(*) FROM predictions
     UNION ALL
     SELECT 'malaria_risk_data', count(*) FROM malaria_risk_data;

     -- Check data freshness
     SELECT 'Latest environmental data', max(timestamp) FROM environmental_data;
     SELECT 'Latest prediction', max(created_at) FROM predictions;
     "
   ```

6. **Switch to Recovered Database**
   ```bash
   # Rename databases
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -c "
     ALTER DATABASE malaria_prediction RENAME TO malaria_prediction_corrupted;
     ALTER DATABASE malaria_prediction_recovery RENAME TO malaria_prediction;"

   # Update database statistics
   kubectl exec -it postgres-0 -n malaria-prediction-production -- \
     psql -U postgres -d malaria_prediction -c "ANALYZE;"
   ```

7. **Restart Application Services**
   ```bash
   # Scale up API pods
   kubectl scale deployment malaria-predictor-api \
     -n malaria-prediction-production --replicas=3

   # Verify service health
   kubectl wait --for=condition=available deployment/malaria-predictor-api \
     -n malaria-prediction-production --timeout=300s

   # Test API endpoints
   curl -f https://api.malaria-prediction.com/health/liveness
   curl -f https://api.malaria-prediction.com/health/readiness
   ```

**Estimated Recovery Time:** 1-2 hours depending on backup size

### Application Recovery

#### Quick Recovery (Pod Failures)

1. **Check Pod Status**
   ```bash
   kubectl get pods -n malaria-prediction-production -l app=malaria-predictor
   kubectl describe pod [failing-pod-name] -n malaria-prediction-production
   ```

2. **Automatic Recovery via Kubernetes**
   ```bash
   # Kubernetes will automatically restart failed pods
   # Monitor recovery progress
   kubectl logs -f deployment/malaria-predictor-api -n malaria-prediction-production
   ```

3. **Manual Recovery if Needed**
   ```bash
   # Delete failing pods to force recreation
   kubectl delete pod [failing-pod-name] -n malaria-prediction-production

   # Or restart deployment
   kubectl rollout restart deployment/malaria-predictor-api -n malaria-prediction-production
   ```

#### Full Application Recovery

1. **Emergency Rollback**
   ```bash
   # Check rollout history
   kubectl rollout history deployment/malaria-predictor-api -n malaria-prediction-production

   # Rollback to previous version
   kubectl rollout undo deployment/malaria-predictor-api -n malaria-prediction-production

   # Monitor rollback
   kubectl rollout status deployment/malaria-predictor-api -n malaria-prediction-production
   ```

2. **Recovery from Backup**
   ```bash
   # Pull specific container image version
   kubectl set image deployment/malaria-predictor-api \
     api=malaria-prediction-api:stable-backup \
     -n malaria-prediction-production
   ```

**Estimated Recovery Time:** 15-30 minutes

### Cluster Recovery

#### Prerequisites
- Access to Kubernetes cluster backups
- Infrastructure provisioning capabilities
- DNS and load balancer configuration access

#### Recovery Steps

1. **Assess Cluster Status**
   ```bash
   # Check node status
   kubectl get nodes
   kubectl describe nodes

   # Check critical system pods
   kubectl get pods -n kube-system
   kubectl get pods -n malaria-prediction-production
   ```

2. **Provision New Cluster (if necessary)**
   ```bash
   # Using Terraform/CloudFormation to provision new cluster
   # (Commands depend on your infrastructure as code setup)

   # Example using eksctl for AWS EKS
   eksctl create cluster --name malaria-prediction-dr \
     --region us-east-1 --zones us-east-1a,us-east-1b,us-east-1c \
     --nodegroup-name malaria-nodes --node-type m5.xlarge \
     --nodes 3 --nodes-min 1 --nodes-max 10
   ```

3. **Restore Configuration**
   ```bash
   # Apply Kubernetes manifests
   kubectl apply -f k8s/

   # Restore secrets (from backup)
   kubectl apply -f disaster_recovery/restored_secrets.yaml
   ```

4. **Restore Data Services**
   ```bash
   # Deploy database with persistent volumes
   # Follow database recovery procedure above if needed

   # Deploy Redis
   kubectl apply -f k8s/redis/
   ```

5. **Deploy Application**
   ```bash
   # Deploy application services
   kubectl apply -f k8s/deployment.yaml

   # Wait for services to be ready
   kubectl wait --for=condition=available deployment/malaria-predictor-api \
     -n malaria-prediction-production --timeout=600s
   ```

6. **Update DNS and Load Balancer**
   ```bash
   # Update DNS records to point to new cluster
   # (Commands depend on your DNS provider)

   # Verify connectivity
   curl -f https://api.malaria-prediction.com/health/liveness
   ```

**Estimated Recovery Time:** 2-4 hours

### Multi-Region Failover

#### Prerequisites
- Secondary region deployment (standby or active-active)
- Cross-region data replication
- DNS failover configuration

#### Recovery Steps

1. **Activate Secondary Region**
   ```bash
   # Switch DNS to secondary region
   # (Commands depend on your DNS provider - Route 53, CloudFlare, etc.)

   # Example with AWS Route 53
   aws route53 change-resource-record-sets --hosted-zone-id Z123456789 \
     --change-batch file://failover-changeset.json
   ```

2. **Promote Standby Database**
   ```bash
   # If using read replica, promote to primary
   # (Commands depend on your database setup)

   # For PostgreSQL streaming replication
   kubectl exec -it postgres-standby-0 -n malaria-prediction-secondary -- \
     /usr/bin/pg_promote
   ```

3. **Scale Up Secondary Region Services**
   ```bash
   # Scale up services in secondary region
   kubectl scale deployment malaria-predictor-api \
     -n malaria-prediction-secondary --replicas=5

   # Update load balancer health checks
   kubectl patch service malaria-predictor-service \
     -n malaria-prediction-secondary \
     --patch '{"spec":{"externalTrafficPolicy":"Local"}}'
   ```

4. **Verify Failover**
   ```bash
   # Test API availability from multiple locations
   curl -f https://api.malaria-prediction.com/health/liveness

   # Verify predictions are working
   curl -f https://api.malaria-prediction.com/predictions/test
   ```

**Estimated Recovery Time:** 30 minutes - 2 hours

### Model Recovery

#### Recovery Steps

1. **Assess Model Status**
   ```bash
   # Check model performance metrics
   kubectl logs deployment/malaria-predictor-api -n malaria-prediction-production | \
     grep -E "(model|prediction|accuracy)"

   # Check model files
   kubectl exec -it deployment/malaria-predictor-api -n malaria-prediction-production -- \
     ls -la /app/models/
   ```

2. **Restore Model from Backup**
   ```bash
   # Download model backup
   python disaster_recovery/backup_orchestrator.py \
     --s3-bucket malaria-prediction-dr-backups \
     download --backup-file models_20240724_030000.tar.gz.enc \
     --output /tmp/models_backup.tar.gz

   # Extract models to pod
   kubectl cp /tmp/models_backup.tar.gz \
     malaria-prediction-production/[pod-name]:/tmp/models_backup.tar.gz

   kubectl exec -it [pod-name] -n malaria-prediction-production -- \
     tar -xzf /tmp/models_backup.tar.gz -C /app/models/
   ```

3. **Restart Application to Load New Models**
   ```bash
   # Restart pods to reload models
   kubectl rollout restart deployment/malaria-predictor-api -n malaria-prediction-production

   # Monitor restart
   kubectl rollout status deployment/malaria-predictor-api -n malaria-prediction-production
   ```

4. **Validate Model Performance**
   ```bash
   # Run model validation tests
   kubectl exec -it deployment/malaria-predictor-api -n malaria-prediction-production -- \
     python -m malaria_predictor.ml.evaluation.validate_models
   ```

**Estimated Recovery Time:** 30 minutes - 1 hour

## Testing and Validation

### Regular DR Testing Schedule

| Test Type | Frequency | Duration | Scope |
|-----------|-----------|----------|-------|
| **Backup Verification** | Daily | 30 minutes | All backup files |
| **Database Recovery** | Weekly | 2 hours | Test database restore |
| **Application Recovery** | Bi-weekly | 1 hour | Pod/deployment recovery |
| **Model Recovery** | Monthly | 1 hour | ML model restoration |
| **Full System Recovery** | Quarterly | 4 hours | Complete system rebuild |
| **Multi-Region Failover** | Semi-annually | 8 hours | Regional disaster simulation |

### Testing Procedures

#### Backup Verification Test
```bash
# Run automated backup verification
python disaster_recovery/backup_orchestrator.py verify-all-backups

# Check backup integrity reports
cat /var/log/malaria-prediction/backup-verification.log
```

#### Recovery Time Testing
```bash
# Measure database recovery time
time python disaster_recovery/disaster_recovery_tester.py \
  --test database-recovery --measure-rto

# Measure application recovery time
time python disaster_recovery/disaster_recovery_tester.py \
  --test application-recovery --measure-rto
```

### Success Criteria

Each recovery test must meet the following criteria:

1. **RTO Compliance**: Recovery completed within defined time objectives
2. **Data Integrity**: No data loss beyond RPO limits
3. **Functional Verification**: All critical services operational
4. **Performance Validation**: System performance within 10% of baseline
5. **Monitoring Restoration**: All monitoring and alerting functional

## Emergency Contacts

### Escalation Chain

| Role | Contact | Phone | Email | Responsibility |
|------|---------|-------|-------|----------------|
| **On-Call Engineer** | [Name] | +1-555-0101 | oncall@company.com | First response |
| **DevOps Lead** | [Name] | +1-555-0102 | devops-lead@company.com | Technical decisions |
| **Database Administrator** | [Name] | +1-555-0103 | dba@company.com | Database recovery |
| **Engineering Manager** | [Name] | +1-555-0104 | eng-manager@company.com | Resource allocation |
| **CTO** | [Name] | +1-555-0105 | cto@company.com | Executive decisions |

### External Support

| Service | Contact | Support Level | SLA |
|---------|---------|---------------|-----|
| **AWS Support** | Enterprise | 24/7 | 15 min response |
| **Database Vendor** | PostgreSQL Professional | Business Hours | 2 hour response |
| **Kubernetes Platform** | Platform Provider | 24/7 | 30 min response |
| **Monitoring Vendor** | Datadog/New Relic | 24/7 | 1 hour response |

### Communication Channels

- **Primary**: Slack #disaster-recovery
- **Secondary**: Email distribution list
- **Emergency**: Conference call bridge
- **Status Updates**: Status page and Twitter

## Recovery Documentation

### Post-Recovery Checklist

After any disaster recovery event:

- [ ] Document timeline and actions taken
- [ ] Validate all systems are functioning normally
- [ ] Update monitoring dashboards and alerts
- [ ] Conduct post-incident review meeting
- [ ] Update DR procedures based on lessons learned
- [ ] Test backup systems are functioning
- [ ] Validate performance is within acceptable limits
- [ ] Update capacity planning based on resource usage during recovery

### Lessons Learned Template

```markdown
# Disaster Recovery Event Report

**Date:** [Date]
**Duration:** [Start Time - End Time]
**Type:** [Database/Application/Infrastructure failure]
**Severity:** [P0/P1/P2/P3]

## Incident Summary
[Brief description of what happened]

## Timeline
- [Time] - Incident detected
- [Time] - Recovery initiated
- [Time] - Service restored
- [Time] - Post-recovery validation completed

## Actions Taken
1. [Action 1]
2. [Action 2]
3. [Action 3]

## What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

## Areas for Improvement
- [Improvement 1]
- [Improvement 2]

## Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]
```

---

**Document Version:** 1.0
**Last Updated:** 2024-07-24
**Next Review Date:** 2024-10-24
**Owner:** DevOps Team
**Approved By:** Engineering Manager
