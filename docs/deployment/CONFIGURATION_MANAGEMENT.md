# Configuration Management - Deployment Guide

This guide provides comprehensive instructions for configuring and deploying the Malaria Prediction Backend across different environments with proper security and secrets management.

## Table of Contents

1. [Overview](#overview)
2. [Environment Configuration](#environment-configuration)
3. [Secrets Management](#secrets-management)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Configuration Validation](#configuration-validation)
7. [Troubleshooting](#troubleshooting)

## Overview

The Malaria Prediction Backend uses a hierarchical configuration system that supports:

- **Multiple environments**: development, staging, production, testing
- **Secure secrets management**: Docker secrets, Kubernetes secrets, environment variables
- **Configuration validation**: Comprehensive validation with health checks
- **Environment-specific overrides**: Per-environment configuration files
- **Security-first approach**: Secrets never stored in code or configuration files

### Configuration Priority (highest to lowest)

1. Docker/Kubernetes secrets (production)
2. Environment variables
3. Environment-specific `.env` files (`.env.production`, `.env.staging`, etc.)
4. Generic `.env` file
5. Default values in code

## Environment Configuration

### 1. Environment Template

Copy the `.env.template` file to create environment-specific configurations:

```bash
# Development
cp .env.template .env.development

# Staging
cp .env.template .env.staging

# Production
cp .env.template .env.production
```

### 2. Configuration Structure

The configuration uses nested environment variables with double underscores (`__`) as delimiters:

```bash
# Security settings
SECURITY__SECRET_KEY="your-secret-key"
SECURITY__JWT_EXPIRATION_HOURS="24"
SECURITY__CORS_ORIGINS='["https://app.yourdomain.com"]'

# Database settings
DATABASE__URL="postgresql+asyncpg://user:password@host:5432/db"
DATABASE__POOL_SIZE="20"
DATABASE__ECHO="false"

# External APIs
EXTERNAL_APIS__ERA5_API_KEY="your-era5-key"
EXTERNAL_APIS__MODIS_API_KEY="your-modis-key"
```

### 3. Environment-Specific Examples

#### Development (`.env.development`)

```bash
ENVIRONMENT="development"
DEBUG="true"
MONITORING__LOG_LEVEL="DEBUG"
SECURITY__CORS_ORIGINS='["*"]'
DATABASE__ECHO="true"
EXTERNAL_APIS__ERA5_API_KEY="test_key_development"
```

#### Production (`.env.production`)

```bash
ENVIRONMENT="production"
DEBUG="false"
MONITORING__LOG_LEVEL="INFO"
SECURITY__CORS_ORIGINS='["https://api.yourdomain.com"]'
DATABASE__ECHO="false"
# Secrets loaded from Docker/Kubernetes secrets
```

## Secrets Management

### 1. Development Secrets

For development, use environment variables or `.env` files:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env.development
SECURITY__SECRET_KEY="generated-secret-key"
DATABASE__URL="postgresql+asyncpg://user:password@localhost:5432/malaria_prediction"
```

### 2. Docker Secrets (Production)

#### Create Docker Secrets

```bash
# API secret key
echo "your-secure-api-secret-key" | docker secret create api_secret_key -

# Database password
echo "your-secure-database-password" | docker secret create db_password -

# Redis password (optional)
echo "your-secure-redis-password" | docker secret create redis_password -

# External API keys
echo "your-era5-api-key" | docker secret create era5_api_key -
echo "your-modis-api-key" | docker secret create modis_api_key -
```

#### Docker Compose with Secrets

```yaml
services:
  api:
    image: malaria-prediction-api:latest
    secrets:
      - api_secret_key
      - db_password
      - redis_password
      - era5_api_key
      - modis_api_key
    environment:
      ENVIRONMENT: production
      SECRET_KEY_FILE: /run/secrets/api_secret_key
      DATABASE_PASSWORD_FILE: /run/secrets/db_password

secrets:
  api_secret_key:
    external: true
  db_password:
    external: true
  redis_password:
    external: true
  era5_api_key:
    external: true
  modis_api_key:
    external: true
```

### 3. Kubernetes Secrets

#### Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace malaria-prediction

# API secret key
kubectl create secret generic malaria-predictor-secrets \
  --from-literal=api_secret_key="your-secure-api-secret-key" \
  -n malaria-prediction

# Database secrets
kubectl create secret generic malaria-predictor-database-secret \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:password@postgres:5432/malaria" \
  --from-literal=DATABASE_PASSWORD="your-secure-database-password" \
  -n malaria-prediction

# External API keys
kubectl create secret generic malaria-predictor-api-keys \
  --from-literal=ERA5_API_KEY="your-era5-api-key" \
  --from-literal=MODIS_API_KEY="your-modis-api-key" \
  -n malaria-prediction
```

#### Using Kubernetes Secrets

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: malaria-predictor-api
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: SECURITY__SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: malaria-predictor-secrets
              key: api_secret_key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: malaria-predictor-database-secret
              key: DATABASE_URL
```

## Docker Deployment

### 1. Development Deployment

```bash
# Build and start development environment
docker-compose up --build

# Or start specific services
docker-compose up database redis api
```

### 2. Production Deployment

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale API service
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### 3. Environment Variables

```bash
# Set environment for deployment
export ENVIRONMENT=production
export DATABASE_URL="postgresql+asyncpg://user:password@db:5432/malaria"
export REDIS_URL="redis://redis:6379/0"

# Deploy with environment
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install required tools
kubectl version --client
helm version

# Create namespace
kubectl create namespace malaria-prediction

# Set default namespace
kubectl config set-context --current --namespace=malaria-prediction
```

### 2. Deploy ConfigMaps and Secrets

```bash
# Apply configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Verify creation
kubectl get configmaps
kubectl get secrets
```

### 3. Deploy Application

```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# Check pod logs
kubectl logs -f deployment/malaria-predictor-api
```

### 4. Configure Ingress

```bash
# Install nginx-ingress (if not already installed)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx

# Install cert-manager (for automatic SSL)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Apply ingress configuration
kubectl apply -f k8s/deployment.yaml
```

### 5. Monitoring and Scaling

```bash
# Check horizontal pod autoscaler
kubectl get hpa

# Monitor resource usage
kubectl top pods
kubectl top nodes

# Scale manually (if needed)
kubectl scale deployment malaria-predictor-api --replicas=5
```

## Configuration Validation

### 1. Validation Command

```bash
# Run configuration validation
python -m malaria_predictor.cli validate-config

# Run with health checks
python -m malaria_predictor.cli validate-config --include-health-checks

# Check specific environment
ENVIRONMENT=production python -m malaria_predictor.cli validate-config
```

### 2. Health Check Endpoints

```bash
# Check application health
curl http://localhost:8000/health/liveness
curl http://localhost:8000/health/readiness
curl http://localhost:8000/health/startup

# Detailed health check with configuration validation
curl http://localhost:8000/health/detailed
```

### 3. Validation API

```python
from malaria_predictor.config_validation import ConfigValidator
from malaria_predictor.config import settings

# Create validator
validator = ConfigValidator(settings)

# Run all validations
results = validator.validate_all()

# Check results
if results["validation_summary"]["failed"] > 0:
    print("Configuration validation failed!")
    print(results)
else:
    print("Configuration validation passed!")
```

## Troubleshooting

### 1. Common Issues

#### Missing Secrets

```bash
# Check if secrets exist
docker secret ls
kubectl get secrets -n malaria-prediction

# Verify secret content (Kubernetes)
kubectl get secret malaria-predictor-secrets -o yaml

# Test secret loading
python -c "
from malaria_predictor.secrets import get_secrets_manager
manager = get_secrets_manager()
print(manager.get_secret_status())
"
```

#### Configuration Validation Errors

```bash
# Run validation with debug output
DEBUG=true python -m malaria_predictor.cli validate-config

# Check individual components
python -c "
from malaria_predictor.config import settings
print('Environment:', settings.environment)
print('Database URL:', settings.database.url)
print('Redis URL:', settings.redis.url)
"
```

#### Database Connection Issues

```bash
# Test database connectivity
python -c "
from malaria_predictor.config import settings
from sqlalchemy import create_engine
engine = create_engine(settings.get_database_url(sync=True))
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection successful!')
"
```

#### Redis Connection Issues

```bash
# Test Redis connectivity
python -c "
from malaria_predictor.config import settings
import redis
client = redis.from_url(settings.get_redis_url())
client.ping()
print('Redis connection successful!')
"
```

### 2. Debug Configuration

```bash
# Enable debug logging
export MONITORING__LOG_LEVEL=DEBUG
export MONITORING__LOG_FORMAT=text

# Start application with debug output
python -c "
from malaria_predictor.config import load_settings
settings = load_settings()
print('Loaded configuration:', settings.model_dump())
"
```

### 3. Environment Detection

```bash
# Check environment detection
python -c "
import os
from malaria_predictor.config import load_settings

print('ENVIRONMENT env var:', os.getenv('ENVIRONMENT'))
settings = load_settings()
print('Detected environment:', settings.environment)
print('Is production:', settings.is_production())
print('Is development:', settings.is_development())
"
```

### 4. Secrets Management Debug

```bash
# Check secrets manager status
python -c "
from malaria_predictor.secrets import get_secrets_manager
manager = get_secrets_manager()
status = manager.get_secret_status()
print('Secrets directory exists:', status['secrets_directory_exists'])
print('Available secret files:', status['available_secret_files'])
"

# Validate production secrets
python -c "
from malaria_predictor.secrets import validate_production_secrets
try:
    results = validate_production_secrets()
    print('Secrets validation results:', results)
except Exception as e:
    print('Secrets validation failed:', e)
"
```

## Security Best Practices

### 1. Secret Generation

```bash
# Generate secure random secrets
openssl rand -base64 32  # For secret keys
openssl rand -hex 16     # For passwords
uuidgen                  # For unique identifiers
```

### 2. Secret Rotation

```bash
# Rotate Docker secrets
echo "new-secret-value" | docker secret create api_secret_key_v2 -
docker service update --secret-rm api_secret_key --secret-add api_secret_key_v2 malaria_api

# Rotate Kubernetes secrets
kubectl create secret generic malaria-predictor-secrets-v2 \
  --from-literal=api_secret_key="new-secret-value"
kubectl patch deployment malaria-predictor-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"SECURITY__SECRET_KEY","valueFrom":{"secretKeyRef":{"name":"malaria-predictor-secrets-v2","key":"api_secret_key"}}}]}]}}}}'
```

### 3. Access Control

```bash
# Kubernetes RBAC
kubectl create serviceaccount malaria-predictor -n malaria-prediction
kubectl create role secret-reader --verb=get,list --resource=secrets -n malaria-prediction
kubectl create rolebinding malaria-predictor-secret-reader --role=secret-reader --serviceaccount=malaria-prediction:malaria-predictor -n malaria-prediction
```

## Production Checklist

### Pre-Deployment

- [ ] All secrets generated and stored securely
- [ ] Environment-specific configuration files created
- [ ] Database migrations tested
- [ ] SSL certificates obtained and configured
- [ ] Monitoring and logging configured
- [ ] Backup procedures implemented

### Deployment

- [ ] Configuration validation passes
- [ ] Health checks return healthy status
- [ ] External API connectivity verified
- [ ] Performance benchmarks meet requirements
- [ ] Security scan completed
- [ ] Load testing performed

### Post-Deployment

- [ ] Application logs monitoring
- [ ] Resource usage monitoring
- [ ] Error tracking active
- [ ] Backup verification
- [ ] Documentation updated
- [ ] Team access configured

## Support

For additional support:

1. Check the application logs for detailed error messages
2. Run configuration validation with debug output
3. Verify all required secrets are properly configured
4. Test individual components (database, Redis, external APIs)
5. Consult the troubleshooting section above

Remember to never log or expose sensitive configuration values in production environments.
