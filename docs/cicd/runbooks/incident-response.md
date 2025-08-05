# Incident Response Runbook

## Overview

This runbook provides procedures for responding to incidents affecting the Malaria Prediction Backend system, including classification, escalation, and resolution processes.

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [Response Team Structure](#response-team-structure)
3. [Response Procedures](#response-procedures)
4. [Communication Templates](#communication-templates)
5. [Resolution Steps](#resolution-steps)
6. [Post-Incident Review](#post-incident-review)

## Incident Classification

### Severity Levels

#### Critical (P0) - Immediate Response Required
- **Response Time**: 15 minutes
- **Resolution Target**: 1 hour
- **Escalation**: Immediate

**Criteria:**
- Complete system outage
- Data loss or corruption
- Security breach
- Payment/billing system failure
- 50%+ of users affected

**Examples:**
- API completely down
- Database corruption
- Container registry compromised
- ML model producing dangerous predictions

#### High (P1) - Urgent Response
- **Response Time**: 30 minutes
- **Resolution Target**: 4 hours
- **Escalation**: 2 hours if unresolved

**Criteria:**
- Major feature unavailable
- Significant performance degradation (>50%)
- 25-50% of users affected
- Data processing pipeline failure

**Examples:**
- Prediction API returning errors
- Authentication system failing
- Database performance severely degraded
- External API integrations down

#### Medium (P2) - Standard Response
- **Response Time**: 2 hours
- **Resolution Target**: 24 hours
- **Escalation**: 8 hours if unresolved

**Criteria:**
- Minor feature impact
- Performance degradation (10-50%)
- <25% of users affected
- Non-critical component failure

**Examples:**
- Monitoring dashboard issues
- Documentation unavailable
- Non-critical ML model underperforming
- Logs not being collected

#### Low (P3) - Planned Response
- **Response Time**: 8 hours
- **Resolution Target**: 7 days
- **Escalation**: As needed

**Criteria:**
- Cosmetic issues
- Enhancement requests
- Internal tooling problems
- Documentation updates

## Response Team Structure

### Incident Commander (IC)
- **Primary**: Senior DevOps Engineer
- **Secondary**: Platform Engineering Lead
- **Responsibilities**:
  - Overall incident coordination
  - Communication with stakeholders
  - Decision making authority
  - Resource allocation

### Technical Lead
- **Primary**: Senior Backend Developer
- **Secondary**: ML Engineering Lead
- **Responsibilities**:
  - Technical investigation
  - Solution implementation
  - Code changes and deployments
  - Technical communication

### Communications Lead
- **Primary**: Product Manager
- **Secondary**: Engineering Manager
- **Responsibilities**:
  - External communication
  - Status page updates
  - Customer notifications
  - Internal stakeholder updates

### Subject Matter Experts (SMEs)
- **Database**: Database Administrator
- **Security**: Security Engineer
- **ML Models**: ML Engineer
- **Infrastructure**: Platform Engineer
- **Frontend**: Frontend Developer

## Response Procedures

### Initial Response (First 15 Minutes)

#### 1. Acknowledge Alert
```bash
# Acknowledge PagerDuty alert
# Update status page: https://status.malaria-prediction.com
# Post in #incidents Slack channel
```

#### 2. Form Response Team
```
#incidents channel:
🚨 INCIDENT DECLARED 🚨
Severity: P[0-3]
Description: [Brief description]
IC: @[incident-commander]
TL: @[technical-lead]
CL: @[communications-lead]
Bridge: [Link to video call/war room]
```

#### 3. Initial Assessment
- [ ] Verify incident scope and impact
- [ ] Check related systems and dependencies
- [ ] Review recent changes/deployments
- [ ] Identify potential root cause
- [ ] Determine if rollback is needed

#### 4. Create Incident Channel
```bash
# Create dedicated Slack channel
# Format: incident-YYYY-MM-DD-brief-description
# Invite response team members
# Pin important information
```

### Investigation Phase

#### 1. Gather Information
```bash
# Check application health
curl -v https://api.malaria-prediction.com/health/liveness
curl -v https://api-staging.malaria-prediction.com/health/liveness

# Check system metrics
# Visit Grafana: https://grafana.malaria-prediction.com
# Check error rates, response times, resource usage

# Review recent deployments
gh run list --workflow=deploy.yml --limit=10

# Check infrastructure status
kubectl get pods --all-namespaces
kubectl get nodes
kubectl top nodes
```

#### 2. Application-Specific Diagnostics
```bash
# Check application logs
kubectl logs -f deployment/malaria-predictor-api \
  -n malaria-prediction-production --tail=100

# Check database connectivity
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  python -c "
  import asyncio
  import asyncpg
  import os

  async def check_db():
      try:
          conn = await asyncpg.connect(os.environ['DATABASE_URL'])
          result = await conn.fetchval('SELECT NOW()')
          print(f'DB Time: {result}')
          await conn.close()
      except Exception as e:
          print(f'DB Error: {e}')

  asyncio.run(check_db())
  "

# Check Redis connectivity
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  python -c "
  import redis
  import os

  try:
      r = redis.from_url(os.environ['REDIS_URL'])
      r.ping()
      print('Redis: OK')
  except Exception as e:
      print(f'Redis Error: {e}')
  "

# Check external API connectivity
kubectl exec -it deployment/malaria-predictor-api \
  -n malaria-prediction-production -- \
  python -c "
  import httpx
  import asyncio

  async def check_apis():
      async with httpx.AsyncClient() as client:
          try:
              # Check ERA5 API
              response = await client.get('https://cds.climate.copernicus.eu/api/status')
              print(f'ERA5 API: {response.status_code}')
          except Exception as e:
              print(f'ERA5 API Error: {e}')

  asyncio.run(check_apis())
  "
```

#### 3. Database Investigation
```bash
# Check database performance
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
  "

# Check active connections
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    count(*) as active_connections,
    state,
    client_addr
  FROM pg_stat_activity
  WHERE state = 'active'
  GROUP BY state, client_addr;
  "

# Check locks
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    l.mode,
    l.locktype,
    l.database,
    l.relation::regclass,
    a.query,
    a.state
  FROM pg_locks l
  JOIN pg_stat_activity a ON a.pid = l.pid
  WHERE NOT l.granted;
  "
```

### Resolution Phase

#### 1. Immediate Mitigation
Based on incident type, apply immediate fixes:

**Application Down:**
```bash
# Check if rollback is possible
kubectl rollout history deployment/malaria-predictor-api -n malaria-prediction-production

# Rollback if recent deployment caused issue
kubectl rollout undo deployment/malaria-predictor-api -n malaria-prediction-production

# Or switch to previous blue-green slot
CURRENT_SLOT=$(kubectl get service malaria-predictor-service \
  -n malaria-prediction-production \
  -o jsonpath='{.spec.selector.version}')

if [ "$CURRENT_SLOT" = "blue" ]; then
  TARGET_SLOT="green"
else
  TARGET_SLOT="blue"
fi

kubectl patch service malaria-predictor-service \
  -n malaria-prediction-production \
  --patch '{"spec":{"selector":{"version":"'$TARGET_SLOT'"}}}'
```

**High Error Rate:**
```bash
# Scale up pods to handle load
kubectl scale deployment malaria-predictor-api \
  -n malaria-prediction-production --replicas=10

# Check if specific endpoints are failing
kubectl logs deployment/malaria-predictor-api \
  -n malaria-prediction-production | grep -E "(ERROR|CRITICAL)" | tail -50
```

**Database Issues:**
```bash
# Kill long-running queries if necessary
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'active'
    AND query_start < NOW() - INTERVAL '5 minutes'
    AND query NOT LIKE '%pg_stat_activity%';
  "

# Restart database connection pooler
kubectl rollout restart deployment/pgbouncer -n malaria-prediction-production
```

**Resource Exhaustion:**
```bash
# Check resource limits
kubectl describe pods -n malaria-prediction-production -l app=malaria-predictor

# Increase resource limits temporarily
kubectl patch deployment malaria-predictor-api -n malaria-prediction-production \
  --patch='{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"8Gi","cpu":"4000m"}}}]}}}}'
```

#### 2. Root Cause Analysis
- [ ] Identify the underlying cause
- [ ] Document findings in incident channel
- [ ] Develop permanent fix plan
- [ ] Estimate fix timeline

#### 3. Implement Permanent Fix
- [ ] Create fix branch from main/develop
- [ ] Implement and test fix
- [ ] Deploy through normal CI/CD pipeline
- [ ] Verify fix resolves the issue

### Communication During Incident

#### Status Page Updates
```
Template for status page:

Title: [Service Name] - [Brief Description]
Status: Investigating | Identified | Monitoring | Resolved
Impact: [Affected Services]

We are currently investigating reports of [description].
Users may experience [specific impact].

Updates will be provided every 30 minutes.
Next update: [Time]

Affected Services:
- API Access: [Status]
- Web Dashboard: [Status]
- Mobile App: [Status]
```

#### Stakeholder Communication
```
Email template for stakeholders:

Subject: [P0/P1] Incident - [Brief Description] - [Status]

Dear [Stakeholders],

We are currently experiencing an incident affecting [services].

Impact: [Description of user impact]
Start Time: [Time]
Current Status: [Investigating/Identified/Monitoring/Resolved]
Next Update: [Time]

Our team is actively working to resolve this issue.

Best regards,
[Communications Lead]
```

#### Customer Communication
```
Template for customer-facing communication:

Subject: Service Update - [Date]

We're currently experiencing technical difficulties that may affect [service functionality].

What we know:
- [Brief description of impact]
- [Affected features]
- [Timeline if known]

What we're doing:
- [Actions being taken]
- [Expected resolution timeframe]

We apologize for any inconvenience and will provide updates as they become available.

For the latest updates, please visit: https://status.malaria-prediction.com

Thank you for your patience.
```

## Resolution Steps

### Verification Checklist
Before declaring incident resolved:

- [ ] All affected services are operational
- [ ] System metrics are within normal ranges
- [ ] Error rates have returned to baseline
- [ ] User-facing functionality works correctly
- [ ] No related alerts are firing
- [ ] Monitoring dashboards show healthy state

### Resolution Verification
```bash
# Health checks
curl -f https://api.malaria-prediction.com/health/liveness
curl -f https://api.malaria-prediction.com/health/readiness

# Performance verification
ab -n 100 -c 10 https://api.malaria-prediction.com/health/liveness

# Error rate check
kubectl logs deployment/malaria-predictor-api \
  -n malaria-prediction-production --since=10m | grep -c ERROR

# Resource usage
kubectl top pods -n malaria-prediction-production -l app=malaria-predictor
```

### Incident Closure
1. **Update Status Page**: Mark incident as resolved
2. **Notify Stakeholders**: Send resolution notification
3. **Update Incident Channel**: Declare incident resolved
4. **Schedule Post-Incident Review**: Within 24-48 hours
5. **Document Timeline**: Create detailed incident timeline

## Post-Incident Review

### Timeline Documentation
Create detailed timeline in incident channel:
```
Incident Timeline - [Date] - [Title]

[Time] - Incident detected
[Time] - Alert fired
[Time] - Response team assembled
[Time] - Root cause identified
[Time] - Mitigation applied
[Time] - Fix implemented
[Time] - Incident resolved

Total Duration: [Duration]
Time to Detection: [Duration]
Time to Resolution: [Duration]
```

### Post-Incident Review Meeting
Schedule within 24-48 hours with:
- Incident Commander
- Technical Lead
- All responders
- Relevant stakeholders

#### Meeting Agenda:
1. **Timeline Review** (10 min)
2. **Root Cause Analysis** (15 min)
3. **Response Effectiveness** (10 min)
4. **Action Items** (15 min)
5. **Process Improvements** (10 min)

#### Review Questions:
- What went well during the incident response?
- What could have been done better?
- Were our monitoring and alerting effective?
- Did we have adequate documentation?
- Are there systemic issues to address?
- What preventive measures can we implement?

### Action Items Template
| Action Item | Owner | Due Date | Priority | Status |
|------------|--------|----------|----------|--------|
| Improve alerting for [condition] | DevOps | +1 week | High | Open |
| Add monitoring for [metric] | SRE | +2 weeks | Medium | Open |
| Update runbook for [scenario] | TL | +1 week | High | Open |
| Implement [preventive measure] | Dev | +1 month | Low | Open |

### Incident Report Template
```markdown
# Incident Report - [Date] - [Title]

## Summary
Brief description of the incident and its impact.

## Timeline
Detailed timeline of events.

## Root Cause
Technical root cause analysis.

## Impact
- Users affected: [Number/Percentage]
- Services affected: [List]
- Duration: [Time]
- Financial impact: [If applicable]

## Resolution
Steps taken to resolve the incident.

## Lessons Learned
What we learned from this incident.

## Action Items
Preventive measures and improvements identified.

## Follow-up
- [ ] Action items assigned and tracked
- [ ] Process improvements implemented
- [ ] Documentation updated
- [ ] Team training conducted (if needed)
```

## Emergency Procedures

### Emergency Rollback
```bash
#!/bin/bash
# Emergency rollback script
set -e

echo "🚨 EMERGENCY ROLLBACK INITIATED 🚨"
echo "Time: $(date)"
echo "Initiated by: $USER"

# Rollback application
kubectl rollout undo deployment/malaria-predictor-api -n malaria-prediction-production
kubectl rollout status deployment/malaria-predictor-api -n malaria-prediction-production

# Verify rollback
sleep 10
if curl -f https://api.malaria-prediction.com/health/liveness; then
    echo "✅ Emergency rollback successful"
else
    echo "❌ Emergency rollback failed - manual intervention required"
    exit 1
fi

echo "Emergency rollback completed at $(date)"
```

### Service Degradation
If full rollback isn't possible, implement service degradation:

```bash
# Disable non-critical features
kubectl set env deployment/malaria-predictor-api \
  -n malaria-prediction-production \
  FEATURE_ML_PREDICTIONS=false \
  FEATURE_BACKGROUND_JOBS=false

# Reduce resource usage
kubectl scale deployment malaria-predictor-api \
  -n malaria-prediction-production --replicas=3
```

### Contact Information

#### Escalation Chain
1. **On-Call Engineer**: +1-555-ONCALL
2. **DevOps Lead**: +1-555-DEVOPS
3. **Engineering Manager**: +1-555-ENG-MGR
4. **CTO**: +1-555-CTO

#### External Support
- **Cloud Provider Support**: [Support Portal]
- **Database Vendor**: [Support Contact]
- **Monitoring Vendor**: [Support Contact]

#### Communication Channels
- **Incidents**: #incidents
- **DevOps**: #devops-alerts
- **Leadership**: #leadership-alerts
- **Status Updates**: #status-updates
