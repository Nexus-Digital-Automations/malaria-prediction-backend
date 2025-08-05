# Deployment Runbook

## Overview

This runbook provides step-by-step procedures for deploying the Malaria Prediction Backend application across different environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Staging Deployment](#staging-deployment)
3. [Production Deployment](#production-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

### Code Quality Verification

- [ ] All CI checks are passing
- [ ] Code review is approved
- [ ] Security scan results are acceptable
- [ ] Test coverage meets requirements (85% overall, 95% critical)
- [ ] No critical or high-severity vulnerabilities

### Environment Preparation

- [ ] Target environment is healthy
- [ ] Database migration is prepared (if needed)
- [ ] Configuration changes are reviewed
- [ ] Monitoring and alerting are functional
- [ ] Rollback plan is prepared

### Communication

- [ ] Deployment scheduled and communicated
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled (if required)
- [ ] On-call engineer identified

### Dependencies

- [ ] External API dependencies are available
- [ ] Database connections are tested
- [ ] Redis/caching layer is operational
- [ ] Container registry is accessible

## Staging Deployment

### Automatic Deployment

Staging deployments are triggered automatically when code is merged to `develop` branch.

```bash
# Verify the deployment workflow is running
gh workflow list --repo your-org/malaria-predictor
gh run list --workflow=deploy.yml --branch=develop

# Monitor the deployment
gh run view <run-id> --log
```

### Manual Deployment

If manual intervention is required:

```bash
# Trigger manual deployment
gh workflow run deploy.yml \
  --ref develop \
  -f environment=staging \
  -f skip_migration=false

# Monitor deployment progress
kubectl get deployments -n malaria-prediction-staging
kubectl rollout status deployment/malaria-predictor-api -n malaria-prediction-staging
```

### Verification Steps

1. **Health Check**
   ```bash
   curl -f https://api-staging.malaria-prediction.com/health/liveness
   curl -f https://api-staging.malaria-prediction.com/health/readiness
   ```

2. **API Functionality**
   ```bash
   curl -f https://api-staging.malaria-prediction.com/docs
   curl -f https://api-staging.malaria-prediction.com/api/v1/health
   ```

3. **Database Connectivity**
   ```bash
   kubectl exec -it deployment/malaria-predictor-api -n malaria-prediction-staging -- \
     python -c "
     import asyncio
     import asyncpg
     import os

     async def test_db():
         conn = await asyncpg.connect(os.environ['DATABASE_URL'])
         result = await conn.fetchval('SELECT version()')
         print(f'Database: {result}')
         await conn.close()

     asyncio.run(test_db())
     "
   ```

4. **Redis Connectivity**
   ```bash
   kubectl exec -it deployment/malaria-predictor-api -n malaria-prediction-staging -- \
     python -c "
     import redis
     import os

     r = redis.from_url(os.environ['REDIS_URL'])
     r.ping()
     print('Redis connection successful')
     "
   ```

## Production Deployment

### Prerequisites

- [ ] Staging deployment is successful and verified
- [ ] Load testing completed successfully
- [ ] Security review approved
- [ ] Change management approval obtained
- [ ] Rollback plan confirmed

### Blue-Green Deployment Process

Production uses blue-green deployment strategy with the following steps:

#### 1. Initiate Deployment

```bash
# Automatic deployment (recommended)
# Triggered when develop branch is merged to main

# Manual deployment (emergency use)
gh workflow run deploy.yml \
  --ref main \
  -f environment=production \
  -f force_deploy=false
```

#### 2. Monitor Deployment Progress

```bash
# Check workflow progress
gh run view <run-id> --log

# Monitor Kubernetes deployment
kubectl get deployments -n malaria-prediction-production
kubectl get pods -n malaria-prediction-production -l app=malaria-predictor

# Check which slot is active
kubectl get service malaria-predictor-service -n malaria-prediction-production \
  -o jsonpath='{.spec.selector.version}'
```

#### 3. Pre-Switch Validation

The deployment workflow automatically performs:
- Health checks on the new deployment
- Performance validation
- Integration testing
- Security verification

#### 4. Traffic Switch

Traffic is automatically switched if all validations pass:

```bash
# Monitor traffic switch
kubectl get service malaria-predictor-service -n malaria-prediction-production \
  -o yaml | grep version

# Verify new deployment is receiving traffic
curl -I https://api.malaria-prediction.com/health/liveness
```

#### 5. Post-Switch Monitoring

```bash
# Monitor application health
watch 'curl -s https://api.malaria-prediction.com/health/liveness | jq .'

# Check error rates
kubectl logs -f deployment/malaria-predictor-<active-slot> \
  -n malaria-prediction-production | grep ERROR

# Monitor resource usage
kubectl top pods -n malaria-prediction-production -l app=malaria-predictor
```

### Manual Blue-Green Deployment Steps

If automatic deployment fails, manual intervention may be required:

#### 1. Determine Current State

```bash
# Get current active slot
CURRENT_SLOT=$(kubectl get service malaria-predictor-service \
  -n malaria-prediction-production \
  -o jsonpath='{.spec.selector.version}')

# Determine target slot
if [ "$CURRENT_SLOT" = "blue" ]; then
  TARGET_SLOT="green"
else
  TARGET_SLOT="blue"
fi

echo "Current: $CURRENT_SLOT, Target: $TARGET_SLOT"
```

#### 2. Deploy to Target Slot

```bash
# Apply deployment to target slot
envsubst < k8s/deployment.yaml | \
  sed "s/malaria-predictor-api/malaria-predictor-$TARGET_SLOT/g" | \
  sed "s/version: v1.0.0/version: $TARGET_SLOT/g" | \
  kubectl apply -f -

# Wait for rollout
kubectl rollout status deployment/malaria-predictor-$TARGET_SLOT \
  -n malaria-prediction-production
```

#### 3. Validate Target Slot

```bash
# Port forward for testing
kubectl port-forward service/malaria-predictor-service-$TARGET_SLOT 8080:8000 \
  -n malaria-prediction-production &

# Test the deployment
curl -f http://localhost:8080/health/liveness
curl -f http://localhost:8080/health/readiness
curl -f http://localhost:8080/docs

# Stop port forward
pkill -f "kubectl port-forward"
```

#### 4. Switch Traffic

```bash
# Update service to point to new deployment
kubectl patch service malaria-predictor-service \
  -n malaria-prediction-production \
  --patch '{"spec":{"selector":{"version":"'$TARGET_SLOT'"}}}'

echo "Traffic switched to $TARGET_SLOT"
```

#### 5. Verify Switch

```bash
# Test public endpoint
curl -f https://api.malaria-prediction.com/health/liveness
curl -f https://api.malaria-prediction.com/health/readiness

# Monitor for 5 minutes
for i in {1..30}; do
  echo "Check $i: $(curl -s https://api.malaria-prediction.com/health/liveness | jq -r .status)"
  sleep 10
done
```

#### 6. Clean Up Old Deployment

```bash
# Remove old deployment (only after successful verification)
kubectl delete deployment malaria-predictor-$CURRENT_SLOT \
  -n malaria-prediction-production

# Remove old service
kubectl delete service malaria-predictor-service-$CURRENT_SLOT \
  -n malaria-prediction-production
```

## Post-Deployment Verification

### Automated Verification

The deployment pipeline automatically runs:
- Health endpoint checks
- Performance regression tests
- Error rate monitoring
- Resource utilization checks

### Manual Verification Steps

#### 1. Application Health

```bash
# Health endpoints
curl -v https://api.malaria-prediction.com/health/liveness
curl -v https://api.malaria-prediction.com/health/readiness
curl -v https://api.malaria-prediction.com/health/startup

# API documentation
curl -v https://api.malaria-prediction.com/docs
```

#### 2. Database Operations

```bash
# Test database queries
curl -X POST https://api.malaria-prediction.com/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": -1.2921, "longitude": 36.8219},
    "date": "2024-01-15",
    "features": {
      "temperature": 25.5,
      "precipitation": 2.1,
      "humidity": 75.0
    }
  }'
```

#### 3. Performance Testing

```bash
# Response time test
ab -n 100 -c 10 https://api.malaria-prediction.com/health/liveness

# Load test (if needed)
kubectl run load-test --image=httpd:alpine --rm -it -- \
  sh -c "for i in \$(seq 1 100); do wget -q -O- https://api.malaria-prediction.com/health/liveness; done"
```

#### 4. Monitoring Verification

```bash
# Check metrics are being collected
curl -s https://api.malaria-prediction.com/metrics | head -20

# Verify Prometheus is scraping
curl -s "${PROMETHEUS_URL}/api/v1/query?query=up{job=\"malaria-predictor-production\"}"

# Check Grafana dashboards are updating
# Visit: https://grafana.malaria-prediction.com/d/malaria-predictor-production
```

### Verification Checklist

- [ ] All health endpoints return 200 OK
- [ ] API documentation is accessible
- [ ] Database queries execute successfully
- [ ] Authentication/authorization works
- [ ] ML prediction endpoints respond correctly
- [ ] Metrics are being collected
- [ ] Logs are being generated
- [ ] No error spikes in monitoring
- [ ] Response times are within SLA
- [ ] Resource usage is normal

## Rollback Procedures

### Automatic Rollback

The deployment pipeline includes automatic rollback triggers:
- Health check failures for 2+ minutes
- Error rate above 5% for 3+ minutes
- Response time above 5 seconds for 5+ minutes

### Manual Rollback

#### Staging Environment

```bash
# Rollback to previous version
kubectl rollout undo deployment/malaria-predictor-api \
  -n malaria-prediction-staging

# Check rollout status
kubectl rollout status deployment/malaria-predictor-api \
  -n malaria-prediction-staging

# Verify rollback
curl -f https://api-staging.malaria-prediction.com/health/liveness
```

#### Production Environment (Blue-Green)

```bash
# Identify previous slot
CURRENT_SLOT=$(kubectl get service malaria-predictor-service \
  -n malaria-prediction-production \
  -o jsonpath='{.spec.selector.version}')

if [ "$CURRENT_SLOT" = "blue" ]; then
  PREVIOUS_SLOT="green"
else
  PREVIOUS_SLOT="blue"
fi

# Check if previous deployment exists
if kubectl get deployment malaria-predictor-$PREVIOUS_SLOT \
   -n malaria-prediction-production &>/dev/null; then

  # Switch traffic back
  kubectl patch service malaria-predictor-service \
    -n malaria-prediction-production \
    --patch '{"spec":{"selector":{"version":"'$PREVIOUS_SLOT'"}}}'

  echo "Rolled back to $PREVIOUS_SLOT"
else
  echo "Previous deployment not found. Manual intervention required."
fi
```

#### Database Rollback

If database migration needs to be rolled back:

```bash
# Check current migration version
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  alembic current

# Rollback to previous version (replace with actual version)
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  alembic downgrade -1

# Verify rollback
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  alembic current
```

### Emergency Rollback

For critical production issues:

```bash
# Immediate rollback script
#!/bin/bash
set -e

echo "EMERGENCY ROLLBACK INITIATED"
echo "Time: $(date)"

# Get current state
CURRENT_SLOT=$(kubectl get service malaria-predictor-service \
  -n malaria-prediction-production \
  -o jsonpath='{.spec.selector.version}')

echo "Current slot: $CURRENT_SLOT"

# Determine previous slot
if [ "$CURRENT_SLOT" = "blue" ]; then
  PREVIOUS_SLOT="green"
else
  PREVIOUS_SLOT="blue"
fi

echo "Rolling back to: $PREVIOUS_SLOT"

# Switch traffic immediately
kubectl patch service malaria-predictor-service \
  -n malaria-prediction-production \
  --patch '{"spec":{"selector":{"version":"'$PREVIOUS_SLOT'"}}}'

# Verify rollback
sleep 5
curl -f https://api.malaria-prediction.com/health/liveness

echo "Emergency rollback completed"
echo "Time: $(date)"
```

## Troubleshooting

### Common Deployment Issues

#### 1. Image Pull Errors

```bash
# Check image availability
docker pull ghcr.io/your-org/malaria-predictor:latest

# Check image pull secrets
kubectl get secret regcred -n malaria-prediction-production -o yaml

# Recreate image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n malaria-prediction-production
```

#### 2. Pod Startup Issues

```bash
# Check pod status
kubectl get pods -n malaria-prediction-production -l app=malaria-predictor

# Check pod logs
kubectl logs -f <pod-name> -n malaria-prediction-production

# Check pod events
kubectl describe pod <pod-name> -n malaria-prediction-production

# Check resource constraints
kubectl top pods -n malaria-prediction-production
```

#### 3. Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  python -c "
  import asyncio
  import asyncpg
  import os

  async def test():
      try:
          conn = await asyncpg.connect(os.environ['DATABASE_URL'])
          print('Database connection successful')
          await conn.close()
      except Exception as e:
          print(f'Database connection failed: {e}')

  asyncio.run(test())
  "

# Check database secret
kubectl get secret malaria-predictor-database-secret \
  -n malaria-prediction-production -o yaml
```

#### 4. Service Discovery Issues

```bash
# Check service endpoints
kubectl get endpoints malaria-predictor-service -n malaria-prediction-production

# Check service configuration
kubectl describe service malaria-predictor-service -n malaria-prediction-production

# Test internal service connectivity
kubectl run debug --image=curlimages/curl --rm -it -- \
  curl malaria-predictor-service.malaria-prediction-production.svc.cluster.local:8000/health/liveness
```

#### 5. Ingress/Load Balancer Issues

```bash
# Check ingress status
kubectl get ingress -n malaria-prediction-production

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/nginx-ingress-controller

# Test DNS resolution
nslookup api.malaria-prediction.com

# Check SSL certificate
openssl s_client -connect api.malaria-prediction.com:443 -servername api.malaria-prediction.com
```

### Escalation Procedures

#### Level 1: Developer Team
- Failed deployments
- Test failures
- Configuration issues

#### Level 2: DevOps Team
- Infrastructure issues
- Performance problems
- Security concerns

#### Level 3: Platform Team
- Cluster-wide issues
- Network problems
- Storage issues

### Emergency Contacts

- **Primary On-Call**: +1-555-ONCALL-1
- **Secondary On-Call**: +1-555-ONCALL-2
- **DevOps Team**: devops@malaria-prediction.com
- **Security Team**: security@malaria-prediction.com
- **Slack Channels**: #alerts, #deployments, #incidents

### Deployment Logs

Always maintain deployment logs for auditing:

```bash
# Save deployment details
cat > deployment-log-$(date +%Y%m%d-%H%M%S).json << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "production",
  "git_sha": "$GITHUB_SHA",
  "deployed_by": "$GITHUB_ACTOR",
  "deployment_type": "blue-green",
  "previous_version": "$PREVIOUS_SLOT",
  "new_version": "$TARGET_SLOT",
  "rollback_procedure": "available",
  "verification_status": "completed"
}
EOF
```
