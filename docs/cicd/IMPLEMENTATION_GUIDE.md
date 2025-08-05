# CI/CD Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the CI/CD pipeline for the Malaria Prediction Backend. It covers initial setup, configuration, and operational procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Configuration](#configuration)
4. [Testing the Pipeline](#testing-the-pipeline)
5. [Operational Procedures](#operational-procedures)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Infrastructure Requirements

#### Kubernetes Cluster
- **Staging**: 3 nodes, 4 vCPU/8GB RAM each
- **Production**: 5+ nodes, 8 vCPU/16GB RAM each
- **Storage**: SSD-backed persistent volumes
- **Networking**: Load balancer with SSL termination

#### External Services
- **Container Registry**: GitHub Container Registry (ghcr.io)
- **Monitoring**: Prometheus + Grafana stack
- **Secrets Management**: Kubernetes secrets + external secret operator
- **Database**: PostgreSQL with TimescaleDB (managed or self-hosted)
- **Cache**: Redis cluster

#### CI/CD Tools
- **GitHub Actions**: For pipeline execution
- **Docker**: For container builds
- **Helm**: For Kubernetes deployments
- **MLflow**: For ML model management

### Access Requirements

#### GitHub Setup
- Repository admin access
- GitHub Actions enabled
- Container registry permissions
- Branch protection rules configured

#### Kubernetes Access
- Cluster admin permissions
- kubectl configured for all environments
- Helm installed and configured
- Appropriate RBAC roles created

#### External Services
- Database admin credentials
- Monitoring system access
- Cloud provider credentials (if applicable)
- External API keys and secrets

## Initial Setup

### 1. Repository Configuration

#### Enable GitHub Actions
```bash
# Check if Actions are enabled
gh api repos/:owner/:repo/actions/permissions

# Enable Actions (if needed)
gh api --method PUT repos/:owner/:repo/actions/permissions \
  --field enabled=true \
  --field allowed_actions=all
```

#### Configure Branch Protection
```bash
# Protect main branch
gh api --method PUT repos/:owner/:repo/branches/main/protection \
  --field required_status_checks='{"strict":true,"contexts":["CI Pipeline"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2}' \
  --field restrictions=null
```

#### Set Up Repository Secrets
```bash
# Required secrets for CI/CD
gh secret set KUBECONFIG --body "$(cat ~/.kube/config | base64 -w 0)"
gh secret set GITHUB_TOKEN --body "$GITHUB_TOKEN"
gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK_URL"

# Database secrets
gh secret set DATABASE_URL --body "$DATABASE_URL"
gh secret set DATABASE_PASSWORD --body "$DATABASE_PASSWORD"

# External API keys
gh secret set ERA5_API_KEY --body "$ERA5_API_KEY"
gh secret set MODIS_API_KEY --body "$MODIS_API_KEY"

# Monitoring secrets
gh secret set PROMETHEUS_URL --body "$PROMETHEUS_URL"
gh secret set GRAFANA_URL --body "$GRAFANA_URL"
gh secret set GRAFANA_API_KEY --body "$GRAFANA_API_KEY"

# Security scanning
gh secret set SNYK_TOKEN --body "$SNYK_TOKEN"
gh secret set SONAR_TOKEN --body "$SONAR_TOKEN"

# ML/MLflow
gh secret set MLFLOW_TRACKING_URI --body "$MLFLOW_TRACKING_URI"
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
```

### 2. Kubernetes Setup

#### Create Namespaces
```bash
# Create namespaces for each environment
kubectl create namespace malaria-prediction-staging
kubectl create namespace malaria-prediction-production
kubectl create namespace monitoring

# Label namespaces
kubectl label namespace malaria-prediction-staging environment=staging
kubectl label namespace malaria-prediction-production environment=production
```

#### Set Up RBAC
```bash
# Apply RBAC configurations
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: malaria-predictor-deployer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: malaria-predictor-deployer-binding
subjects:
- kind: ServiceAccount
  name: github-actions
  namespace: default
roleRef:
  kind: ClusterRole
  name: malaria-predictor-deployer
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-actions
  namespace: default
EOF
```

#### Install Monitoring Stack
```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus and Grafana
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values - <<EOF
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi

grafana:
  adminPassword: "$(openssl rand -base64 32)"
  ingress:
    enabled: true
    hosts:
      - grafana.malaria-prediction.com

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi
EOF
```

### 3. Database Setup

#### Install PostgreSQL with TimescaleDB
```bash
# Add TimescaleDB Helm repo
helm repo add timescale https://charts.timescale.com
helm repo update

# Install TimescaleDB
helm install timescaledb timescale/timescaledb-single \
  --namespace malaria-prediction-production \
  --values - <<EOF
image:
  tag: "pg15-latest"

persistentVolume:
  size: 500Gi
  storageClass: fast-ssd

resources:
  requests:
    memory: 4Gi
    cpu: 2000m
  limits:
    memory: 8Gi
    cpu: 4000m

postgresql:
  databases:
    - malaria_prediction
  users:
    - username: app_user
      password: "$(openssl rand -base64 32)"
      databases:
        - malaria_prediction

backup:
  enabled: true
  schedule: "0 2 * * *"
  retention: "30d"
EOF
```

#### Configure Secrets
```bash
# Create database secrets
kubectl create secret generic malaria-predictor-database-secret \
  --namespace malaria-prediction-production \
  --from-literal=DATABASE_HOST=timescaledb.malaria-prediction-production.svc.cluster.local \
  --from-literal=DATABASE_PORT=5432 \
  --from-literal=DATABASE_NAME=malaria_prediction \
  --from-literal=DATABASE_USER=app_user \
  --from-literal=DATABASE_PASSWORD="$DB_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://app_user:$DB_PASSWORD@timescaledb:5432/malaria_prediction"

# Replicate for staging
kubectl create secret generic malaria-predictor-database-secret \
  --namespace malaria-prediction-staging \
  --from-literal=DATABASE_HOST=timescaledb.malaria-prediction-staging.svc.cluster.local \
  --from-literal=DATABASE_PORT=5432 \
  --from-literal=DATABASE_NAME=malaria_prediction_staging \
  --from-literal=DATABASE_USER=app_user \
  --from-literal=DATABASE_PASSWORD="$STAGING_DB_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://app_user:$STAGING_DB_PASSWORD@timescaledb:5432/malaria_prediction_staging"
```

### 4. Redis Setup

#### Install Redis Cluster
```bash
# Add Bitnami Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Redis
helm install redis bitnami/redis \
  --namespace malaria-prediction-production \
  --values - <<EOF
auth:
  enabled: true
  password: "$(openssl rand -base64 32)"

master:
  persistence:
    enabled: true
    size: 32Gi
    storageClass: fast-ssd

replica:
  replicaCount: 2
  persistence:
    enabled: true
    size: 32Gi
    storageClass: fast-ssd

metrics:
  enabled: true
  serviceMonitor:
    enabled: true
EOF

# Create Redis secrets
kubectl create secret generic malaria-predictor-redis-secret \
  --namespace malaria-prediction-production \
  --from-literal=REDIS_HOST=redis-master.malaria-prediction-production.svc.cluster.local \
  --from-literal=REDIS_PORT=6379 \
  --from-literal=REDIS_PASSWORD="$REDIS_PASSWORD" \
  --from-literal=REDIS_URL="redis://:$REDIS_PASSWORD@redis-master:6379/0"
```

## Configuration

### 1. Environment-Specific Configuration

#### Staging ConfigMap
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: malaria-predictor-config
  namespace: malaria-prediction-staging
data:
  ENVIRONMENT: "staging"
  LOG_LEVEL: "DEBUG"
  DEBUG: "true"

  # Feature flags
  FEATURE_ML_PREDICTIONS: "true"
  FEATURE_DATA_INGESTION: "true"
  FEATURE_BACKGROUND_JOBS: "true"

  # Performance settings
  WORKER_PROCESSES: "2"
  MAX_CONNECTIONS: "100"
  CONNECTION_TIMEOUT: "30"

  # External APIs
  ERA5_API_URL: "https://cds.climate.copernicus.eu/api/v2"
  MODIS_API_URL: "https://modis.gsfc.nasa.gov/data"
  MAP_API_URL: "https://map.ox.ac.uk/research-group"

  # Monitoring
  ENABLE_METRICS: "true"
  METRICS_PORT: "9090"
  HEALTH_CHECK_INTERVAL: "30"
EOF
```

#### Production ConfigMap
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: malaria-predictor-config
  namespace: malaria-prediction-production
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "WARNING"
  DEBUG: "false"

  # Feature flags
  FEATURE_ML_PREDICTIONS: "true"
  FEATURE_DATA_INGESTION: "true"
  FEATURE_BACKGROUND_JOBS: "true"

  # Performance settings
  WORKER_PROCESSES: "4"
  MAX_CONNECTIONS: "1000"
  CONNECTION_TIMEOUT: "60"

  # External APIs
  ERA5_API_URL: "https://cds.climate.copernicus.eu/api/v2"
  MODIS_API_URL: "https://modis.gsfc.nasa.gov/data"
  MAP_API_URL: "https://map.ox.ac.uk/research-group"

  # Monitoring
  ENABLE_METRICS: "true"
  METRICS_PORT: "9090"
  HEALTH_CHECK_INTERVAL: "60"

  # Security
  SECURITY_STRICT_MODE: "true"
  RATE_LIMIT_ENABLED: "true"
  CORS_ENABLED: "false"
EOF
```

### 2. Security Configuration

#### Create Security Secrets
```bash
# Application secrets
kubectl create secret generic malaria-predictor-secrets \
  --namespace malaria-prediction-production \
  --from-literal=api_secret_key="$(openssl rand -base64 64)" \
  --from-literal=jwt_secret="$(openssl rand -base64 32)" \
  --from-literal=encryption_key="$(openssl rand -base64 32)"

# API keys
kubectl create secret generic malaria-predictor-api-keys \
  --namespace malaria-prediction-production \
  --from-literal=ERA5_API_KEY="$ERA5_API_KEY" \
  --from-literal=MODIS_API_KEY="$MODIS_API_KEY" \
  --from-literal=MAP_API_KEY="$MAP_API_KEY" \
  --from-literal=SENTRY_DSN="$SENTRY_DSN"

# CORS configuration
kubectl create configmap malaria-predictor-cors-config \
  --namespace malaria-prediction-production \
  --from-literal=cors_origins.json='["https://app.malaria-prediction.com","https://dashboard.malaria-prediction.com"]'
```

### 3. Monitoring Configuration

#### Prometheus Rules
```bash
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: malaria-predictor-alerts
  namespace: malaria-prediction-production
spec:
  groups:
  - name: malaria-predictor
    rules:
    - alert: MalariaPredictorDown
      expr: up{job="malaria-predictor-production"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Malaria Predictor is down"
        description: "Malaria Predictor has been down for more than 2 minutes"

    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="malaria-predictor-production"}[5m])) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ \$value }}s"

    - alert: HighErrorRate
      expr: rate(http_requests_total{job="malaria-predictor-production",status=~"5.."}[5m]) > 0.05
      for: 3m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ \$value | humanizePercentage }}"
EOF
```

#### Grafana Dashboards
```bash
# Create Grafana dashboard ConfigMap
kubectl create configmap malaria-predictor-dashboard \
  --namespace monitoring \
  --from-file=dashboard.json=docs/monitoring/grafana-dashboard.json

# Label for automatic discovery
kubectl label configmap malaria-predictor-dashboard \
  --namespace monitoring \
  grafana_dashboard=1
```

## Testing the Pipeline

### 1. Initial Pipeline Test

#### Create Test Branch
```bash
# Create and push test branch
git checkout -b test/ci-cd-setup
git commit --allow-empty -m "Test CI/CD pipeline setup"
git push origin test/ci-cd-setup
```

#### Monitor Pipeline Execution
```bash
# Watch workflow runs
gh run list --workflow=ci.yml --branch=test/ci-cd-setup

# View detailed logs
gh run view <run-id> --log

# Check individual jobs
gh run view <run-id> --job=unit-tests
gh run view <run-id> --job=integration-tests
```

### 2. Deployment Test

#### Test Staging Deployment
```bash
# Merge test branch to develop (triggers staging deployment)
git checkout develop
git merge test/ci-cd-setup
git push origin develop

# Monitor deployment
gh run list --workflow=deploy.yml --branch=develop

# Verify staging deployment
curl -f https://api-staging.malaria-prediction.com/health/liveness
curl -f https://api-staging.malaria-prediction.com/docs
```

#### Test Production Deployment
```bash
# Merge to main (triggers production deployment)
git checkout main
git merge develop
git push origin main

# Monitor blue-green deployment
gh run list --workflow=deploy.yml --branch=main

# Verify production deployment
curl -f https://api.malaria-prediction.com/health/liveness
curl -f https://api.malaria-prediction.com/docs
```

### 3. Security Pipeline Test

#### Trigger Security Scan
```bash
# Manual security scan
gh workflow run security.yml --ref main

# Check security results
gh run list --workflow=security.yml

# Review security reports
gh run view <run-id> --job=security-summary
```

### 4. ML Model Pipeline Test

#### Test Model Training
```bash
# Create ML model change
echo "# Model training update" >> src/malaria_predictor/ml/models/ensemble_model.py
git add src/malaria_predictor/ml/models/ensemble_model.py
git commit -m "Update ML model for testing"
git push origin main

# Monitor ML pipeline
gh run list --workflow=ml-model-deploy.yml

# Check MLflow for new model versions
curl -H "Authorization: Bearer $MLFLOW_TOKEN" \
  "$MLFLOW_TRACKING_URI/api/2.0/mlflow/registered-models/list"
```

## Operational Procedures

### 1. Daily Operations

#### Morning Checklist
```bash
#!/bin/bash
# daily-ops-check.sh

echo "🌅 Daily Operations Check - $(date)"

# Check pipeline status
echo "📊 Recent Pipeline Runs:"
gh run list --limit 10

# Check application health
echo "🏥 Application Health:"
curl -s https://api.malaria-prediction.com/health/liveness | jq .
curl -s https://api-staging.malaria-prediction.com/health/liveness | jq .

# Check resource usage
echo "📈 Resource Usage:"
kubectl top nodes
kubectl top pods -n malaria-prediction-production

# Check recent alerts
echo "🚨 Recent Alerts:"
curl -s "$PROMETHEUS_URL/api/v1/query?query=ALERTS" | jq '.data.result[] | select(.value[1] == "1")'

echo "✅ Daily check completed"
```

#### Monitor Key Metrics
```bash
# Application metrics
curl -s https://api.malaria-prediction.com/metrics | grep -E "(http_requests_total|http_request_duration_seconds)"

# Database performance
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    query,
    calls,
    mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 5;
  "

# Check error logs
kubectl logs --tail=100 deployment/malaria-predictor-api -n malaria-prediction-production | grep ERROR
```

### 2. Weekly Operations

#### Security Review
```bash
# Run comprehensive security scan
gh workflow run security.yml --ref main -f scan_type=all

# Review dependency updates
gh workflow run dependabot.yml

# Check for outdated packages
kubectl exec -it deployment/malaria-predictor-api -n malaria-prediction-production -- \
  pip list --outdated
```

#### Performance Review
```bash
# Performance regression check
gh workflow run ci.yml --ref main -f run_performance_tests=true

# Database maintenance
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "ANALYZE;"

# Clear old logs and metrics
kubectl delete pods -l app=log-cleaner -n monitoring
```

### 3. Monthly Operations

#### Capacity Planning
```bash
# Resource usage trends
kubectl describe nodes | grep -A 5 "Allocated resources"

# Database growth analysis
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
  "
```

#### Disaster Recovery Test
```bash
# Test backup restoration (in staging)
kubectl exec -it postgres-0 -n malaria-prediction-staging -- \
  pg_restore -U postgres -d malaria_prediction_test \
  /backups/latest-backup.dump

# Test blue-green deployment rollback
gh workflow run deploy.yml --ref main -f force_deploy=true -f test_rollback=true
```

## Troubleshooting

### Common Issues

#### 1. Pipeline Failures

**Issue**: Tests failing due to environment issues
```bash
# Check test environment
docker-compose -f docker-compose.test.yml ps
docker-compose -f docker-compose.test.yml logs

# Reset test environment
docker-compose -f docker-compose.test.yml down --volumes
docker-compose -f docker-compose.test.yml up -d
```

**Issue**: Container build failures
```bash
# Check Dockerfile syntax
docker build --no-cache -t test-build .

# Check base image availability
docker pull python:3.11-slim

# Clear Docker cache
docker system prune -a
```

#### 2. Deployment Issues

**Issue**: Kubernetes deployment stuck
```bash
# Check pod status
kubectl get pods -n malaria-prediction-production -l app=malaria-predictor

# Check events
kubectl get events -n malaria-prediction-production --sort-by=.metadata.creationTimestamp

# Force rollout restart
kubectl rollout restart deployment/malaria-predictor-api -n malaria-prediction-production
```

**Issue**: Database migration failures
```bash
# Check migration job logs
kubectl logs job/db-migration-<id> -n malaria-prediction-production

# Check database connectivity
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "SELECT version();"

# Manual migration rollback
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  alembic downgrade -1
```

#### 3. Security Issues

**Issue**: Security scan blocking deployment
```bash
# Review security findings
gh run view <security-run-id> --job=security-summary

# Create exception (if false positive)
echo "CVE-2024-XXXXX" >> .security-exceptions

# Update dependencies
pip-audit --fix
```

#### 4. Performance Issues

**Issue**: High response times
```bash
# Check application metrics
curl -s https://api.malaria-prediction.com/metrics | grep duration

# Scale up pods
kubectl scale deployment malaria-predictor-api --replicas=10 -n malaria-prediction-production

# Check database performance
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT query, mean_time, calls
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
  "
```

### Emergency Procedures

#### Complete System Failure
```bash
#!/bin/bash
# emergency-recovery.sh

echo "🚨 EMERGENCY RECOVERY INITIATED"

# Check overall system status
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running

# Restart critical services
kubectl rollback deployment/malaria-predictor-api -n malaria-prediction-production
kubectl rollback deployment/postgres -n malaria-prediction-production

# Switch to backup region (if configured)
kubectl config use-context backup-cluster
kubectl apply -f k8s/

# Notify stakeholders
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"🚨 EMERGENCY: System failure detected. Recovery in progress."}'

echo "Emergency recovery procedures initiated"
```

### Support Contacts

- **DevOps Team**: devops@malaria-prediction.com
- **Platform Engineering**: platform@malaria-prediction.com
- **Security Team**: security@malaria-prediction.com
- **Database Team**: dba@malaria-prediction.com
- **On-Call**: +1-555-ONCALL

### Additional Resources

- [Pipeline Documentation](README.md)
- [Deployment Runbook](runbooks/deployment.md)
- [Incident Response](runbooks/incident-response.md)
- [Security Procedures](runbooks/security-incident.md)
- [Database Operations](runbooks/database-operations.md)
- [Monitoring Dashboards](https://grafana.malaria-prediction.com)
- [Status Page](https://status.malaria-prediction.com)
