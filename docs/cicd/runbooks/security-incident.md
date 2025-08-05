# Security Incident Response Runbook

## Overview

This runbook provides procedures for responding to security incidents affecting the Malaria Prediction Backend system, from detection through resolution and post-incident activities.

## Table of Contents

1. [Security Incident Classification](#security-incident-classification)
2. [Immediate Response](#immediate-response)
3. [Investigation Procedures](#investigation-procedures)
4. [Containment & Eradication](#containment--eradication)
5. [Recovery Procedures](#recovery-procedures)
6. [Communication & Legal](#communication--legal)
7. [Post-Incident Activities](#post-incident-activities)

## Security Incident Classification

### Critical Security Incidents (S1)
- **Response Time**: Immediate (5 minutes)
- **Notification**: CISO, Legal, PR within 1 hour

**Examples:**
- Active data exfiltration
- Compromised production systems
- Ransomware/malware detected
- Unauthorized access to sensitive data
- Public disclosure of vulnerabilities
- DDoS attacks affecting availability

### High Security Incidents (S2)
- **Response Time**: 30 minutes
- **Notification**: Security team, Engineering leads within 2 hours

**Examples:**
- Attempted unauthorized access
- Suspicious network activity
- Vulnerabilities in production code
- Insider threat indicators
- Failed security controls
- Suspicious authentication patterns

### Medium Security Incidents (S3)
- **Response Time**: 2 hours
- **Notification**: Security team within 4 hours

**Examples:**
- Policy violations
- Security misconfigurations
- Failed compliance checks
- Minor data exposure
- Suspicious but contained activity

## Immediate Response

### Alert Triage (First 5 Minutes)

#### 1. Initial Assessment
```bash
# Check security monitoring dashboard
# Visit: https://security.malaria-prediction.com

# Review recent security alerts
curl -H "Authorization: Bearer $SECURITY_TOKEN" \
  https://api.security-platform.com/alerts/recent

# Check system integrity
kubectl get pods --all-namespaces | grep -v Running
```

#### 2. Activate Security Response Team
```
#security-incident channel:
🚨 SECURITY INCIDENT DECLARED 🚨
Severity: S[1-3]
Type: [Data Breach/Unauthorized Access/Malware/DDoS/Other]
Description: [Brief description]
Security Lead: @[security-lead]
IC: @[incident-commander]
Legal: @[legal-counsel] (for S1 only)
Bridge: [Secure video call link]
```

#### 3. Preserve Evidence
```bash
# Create forensic snapshots (for critical incidents)
kubectl exec -it security-tools -- \
  dd if=/dev/sda of=/forensics/system-snapshot-$(date +%Y%m%d%H%M%S).img

# Capture current system state
kubectl get all --all-namespaces > system-state-$(date +%Y%m%d%H%M%S).txt
kubectl logs --all-containers --all-namespaces --since=1h > system-logs-$(date +%Y%m%d%H%M%S).txt

# Network traffic capture (if applicable)
kubectl exec -it network-monitor -- \
  tcpdump -i any -w /tmp/incident-$(date +%Y%m%d%H%M%S).pcap
```

### Critical Incident Actions (S1)

#### 1. Immediate Containment
```bash
# Isolate affected systems
kubectl cordon <affected-node>
kubectl drain <affected-node> --ignore-daemonsets --force

# Block suspicious IP addresses
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-suspicious-ips
  namespace: malaria-prediction-production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - <suspicious-ip>/32
EOF

# Disable compromised accounts immediately
kubectl delete serviceaccount <compromised-sa> -n <namespace>
```

#### 2. Stop Data Exfiltration
```bash
# Block external network access
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-egress
  namespace: malaria-prediction-production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress: []
EOF

# Monitor data flows
kubectl exec -it network-monitor -- \
  netstat -tupln | grep ESTABLISHED
```

#### 3. Revoke Access
```bash
# Rotate all secrets immediately
kubectl delete secret --all -n malaria-prediction-production
# Note: Ensure new secrets are available before deletion

# Revoke API keys
curl -X DELETE -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.external-service.com/keys/<compromised-key>

# Disable SSO integration temporarily
kubectl scale deployment sso-proxy --replicas=0 -n auth-system
```

## Investigation Procedures

### Evidence Collection

#### 1. System Logs Analysis
```bash
# Collect application logs
kubectl logs deployment/malaria-predictor-api \
  -n malaria-prediction-production \
  --since=24h > incident-app-logs.txt

# Collect security logs
kubectl logs deployment/security-monitor \
  -n security-system \
  --since=24h > incident-security-logs.txt

# Collect audit logs
kubectl get events --all-namespaces \
  --sort-by='.metadata.creationTimestamp' > incident-k8s-events.txt
```

#### 2. Network Traffic Analysis
```bash
# Analyze suspicious connections
kubectl exec -it network-analyzer -- \
  python analyze_traffic.py \
  --pcap /tmp/incident-$(date +%Y%m%d).pcap \
  --output /tmp/traffic-analysis.json

# Check DNS queries
kubectl logs deployment/dns-monitor -n security-system | \
  grep -E "(malicious|suspicious|exfiltration)" > dns-analysis.txt
```

#### 3. File System Analysis
```bash
# Check for modified files
kubectl exec -it <affected-pod> -- \
  find /app -type f -newermt "$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

# Look for suspicious processes
kubectl exec -it <affected-pod> -- \
  ps aux | grep -v -E "(python|uvicorn|gunicorn)"

# Check for backdoors
kubectl exec -it <affected-pod> -- \
  find /app -name "*.py" -exec grep -l "backdoor\|shell\|exec" {} \;
```

#### 4. Database Investigation
```bash
# Check for suspicious queries
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    query,
    calls,
    total_time,
    state_change,
    client_addr
  FROM pg_stat_statements
  JOIN pg_stat_activity ON pg_stat_activity.query = pg_stat_statements.query
  WHERE query ILIKE '%DROP%'
     OR query ILIKE '%DELETE%'
     OR query ILIKE '%UPDATE%'
  ORDER BY state_change DESC
  LIMIT 50;
  "

# Check for unauthorized access
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT DISTINCT
    usename,
    application_name,
    client_addr,
    backend_start,
    state
  FROM pg_stat_activity
  WHERE state = 'active'
    AND client_addr IS NOT NULL
  ORDER BY backend_start DESC;
  "
```

### Threat Intelligence

#### 1. IOC Analysis
```bash
# Check against threat intelligence feeds
python security-tools/ioc_checker.py \
  --ips "$(grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' incident-logs.txt)" \
  --domains "$(grep -o '[a-zA-Z0-9.-]*\.[a-zA-Z]{2,}' incident-logs.txt)"

# VirusTotal API check
for hash in $(sha256sum suspicious-files/* | awk '{print $1}'); do
  curl -H "x-apikey: $VT_API_KEY" \
    "https://www.virustotal.com/api/v3/files/$hash" >> vt-results.json
done
```

#### 2. Attribution Analysis
```bash
# Analyze attack patterns
python security-tools/pattern_analyzer.py \
  --logs incident-logs.txt \
  --output attribution-analysis.json

# Check for known attack signatures
grep -f known-attack-patterns.txt incident-logs.txt > matched-patterns.txt
```

## Containment & Eradication

### Containment Strategies

#### 1. Network Segmentation
```bash
# Isolate affected services
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-service
  namespace: malaria-prediction-production
spec:
  podSelector:
    matchLabels:
      app: compromised-service
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
EOF
```

#### 2. Access Control
```bash
# Revoke all access tokens
kubectl get secrets -o name | xargs kubectl delete

# Reset all passwords
python security-tools/password_reset.py --all-users

# Disable compromised accounts
kubectl patch user <compromised-user> --patch '{"spec":{"disabled":true}}'
```

#### 3. System Isolation
```bash
# Quarantine affected pods
kubectl label pods -l app=affected-service quarantine=true
kubectl patch deployment affected-service --patch '{"spec":{"template":{"spec":{"nodeSelector":{"quarantine":"true"}}}}}'
```

### Eradication Procedures

#### 1. Malware Removal
```bash
# Scan for malware
kubectl exec -it security-scanner -- \
  clamscan -r /app --infected --remove

# Remove backdoors
kubectl exec -it <pod> -- \
  find /app -name "*.py" -exec grep -l "suspicious_patterns" {} \; | \
  xargs rm -f
```

#### 2. Vulnerability Patching
```bash
# Update container images
docker pull ghcr.io/your-org/malaria-predictor:security-patch
kubectl set image deployment/malaria-predictor-api \
  api=ghcr.io/your-org/malaria-predictor:security-patch \
  -n malaria-prediction-production

# Apply security patches
kubectl apply -f security-patches/
```

#### 3. Configuration Hardening
```bash
# Apply security policies
kubectl apply -f security-configs/pod-security-policy.yaml
kubectl apply -f security-configs/network-policies.yaml
kubectl apply -f security-configs/rbac-restrictions.yaml

# Update security settings
kubectl set env deployment/malaria-predictor-api \
  SECURITY_STRICT_MODE=true \
  AUTH_REQUIRE_MFA=true \
  -n malaria-prediction-production
```

## Recovery Procedures

### System Recovery

#### 1. Restore from Backup
```bash
# Identify clean backup point
kubectl get volumesnapshots | grep -v compromised

# Restore database
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_restore -U postgres -d malaria_prediction \
  /backups/clean-backup-$(date -d '2 days ago' +%Y%m%d).dump

# Restore application data
kubectl exec -it storage-pod -- \
  rsync -av /backups/clean-app-data/ /app/data/
```

#### 2. Rebuild Compromised Systems
```bash
# Recreate compromised pods
kubectl delete pods -l compromised=true
kubectl rollout restart deployment/malaria-predictor-api -n malaria-prediction-production

# Rebuild container images
docker build --no-cache -t ghcr.io/your-org/malaria-predictor:clean .
docker push ghcr.io/your-org/malaria-predictor:clean
```

#### 3. Validate System Integrity
```bash
# Run security validation
kubectl exec -it security-validator -- \
  python validate_system.py --comprehensive

# Verify checksums
kubectl exec -it <pod> -- \
  sha256sum -c /app/checksums.txt

# Test functionality
curl -f https://api.malaria-prediction.com/health/security-check
```

### Service Recovery

#### 1. Gradual Service Restoration
```bash
# Start with limited functionality
kubectl set env deployment/malaria-predictor-api \
  FEATURE_PREDICTIONS=false \
  FEATURE_DATA_INGESTION=false \
  -n malaria-prediction-production

# Enable monitoring first
kubectl scale deployment monitoring-stack --replicas=3

# Gradually restore features
kubectl set env deployment/malaria-predictor-api \
  FEATURE_PREDICTIONS=true \
  -n malaria-prediction-production
```

#### 2. Security Monitoring
```bash
# Enhanced monitoring
kubectl apply -f enhanced-security-monitoring.yaml

# Real-time threat detection
kubectl scale deployment threat-detector --replicas=5

# Increase log retention
kubectl patch configmap fluentd-config --patch '{"data":{"retention":"30d"}}'
```

## Communication & Legal

### Internal Communication

#### 1. Incident Updates
```
Security Incident Update #[N] - [Timestamp]

Status: [Investigating/Contained/Eradicated/Recovered]
Impact: [Description]
Actions Taken: [List of actions]
Next Steps: [Planned actions]
ETA: [If known]

Current Response Team:
- Security Lead: [Name]
- Incident Commander: [Name]
- Technical Lead: [Name]
```

#### 2. Executive Briefing
```
CONFIDENTIAL - Security Incident Executive Summary

Incident ID: SEC-[YYYY]-[###]
Severity: S[1-3]
Detection Time: [Timestamp]
Current Status: [Status]

Business Impact:
- Services Affected: [List]
- Data at Risk: [Description]
- Customer Impact: [Description]
- Financial Impact: [Estimate if known]

Response Actions:
- Immediate containment completed
- Investigation in progress
- Recovery plan developed

Legal Considerations:
- Regulatory notification required: [Yes/No]
- Customer notification required: [Yes/No]
- Law enforcement involvement: [Yes/No]

Next 24 Hours:
- [Key milestones]
```

### External Communication

#### 1. Customer Notification (if required)
```
Subject: Important Security Notice - [Date]

Dear [Customer],

We are writing to inform you of a security incident that may have affected your account.

What Happened:
[Brief, clear description without technical details]

Information Involved:
[Specific data types that may have been affected]

What We're Doing:
- Immediately secured the affected systems
- Launched a comprehensive investigation
- Implemented additional security measures
- Working with law enforcement [if applicable]

What You Should Do:
- Change your password as a precaution
- Monitor your account for unusual activity
- Enable two-factor authentication

We sincerely apologize for this incident and any inconvenience it may cause.

For questions: security@malaria-prediction.com
For updates: https://status.malaria-prediction.com

[Contact Information]
```

#### 2. Regulatory Notification
```bash
# GDPR notification template (if EU data affected)
# Must be submitted within 72 hours

curl -X POST https://gdpr-notification-portal.eu/ \
  -H "Content-Type: application/json" \
  -d '{
    "organization": "Malaria Prediction Inc",
    "incident_date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "detection_date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "affected_records": 1000,
    "data_types": ["personal_identifiers", "health_data"],
    "breach_nature": "unauthorized_access",
    "containment_measures": "Systems isolated, access revoked, investigation ongoing",
    "contact": "security@malaria-prediction.com"
  }'
```

### Law Enforcement

#### 1. Evidence Preservation
```bash
# Create legal hold
kubectl exec -it legal-hold-system -- \
  python create_legal_hold.py \
  --incident-id SEC-2024-001 \
  --preserve-days 365

# Chain of custody documentation
echo "Evidence collected at $(date) by $USER" > chain-of-custody.log
sha256sum evidence/* >> chain-of-custody.log
```

#### 2. Law Enforcement Cooperation
- Prepare evidence in legally admissible format
- Document all actions taken
- Provide technical expertise as needed
- Coordinate with legal counsel

## Post-Incident Activities

### Lessons Learned

#### 1. Incident Analysis
```bash
# Generate incident timeline
python security-tools/timeline_generator.py \
  --logs incident-logs.txt \
  --events k8s-events.txt \
  --output incident-timeline.html

# Root cause analysis
python security-tools/root_cause_analyzer.py \
  --incident-data incident-data.json \
  --output root-cause-report.pdf
```

#### 2. Security Improvements
- [ ] Update security policies
- [ ] Implement additional monitoring
- [ ] Enhance detection capabilities
- [ ] Improve response procedures
- [ ] Conduct security training

### Recovery Validation

#### 1. Security Testing
```bash
# Penetration testing
kubectl run pentest --image=penetration-tester -- \
  python pentest.py --target malaria-predictor-api

# Vulnerability scanning
kubectl run vuln-scan --image=vulnerability-scanner -- \
  nmap -sV -O api.malaria-prediction.com

# Security audit
kubectl exec -it security-auditor -- \
  python audit_system.py --comprehensive
```

#### 2. Compliance Verification
```bash
# SOC 2 compliance check
python compliance-tools/soc2_validator.py --full-audit

# HIPAA compliance verification
python compliance-tools/hipaa_checker.py --validate-all

# GDPR compliance assessment
python compliance-tools/gdpr_assessor.py --post-incident
```

### Documentation Updates

#### 1. Incident Report
```markdown
# Security Incident Report - SEC-[YYYY]-[###]

## Executive Summary
[High-level summary for leadership]

## Incident Details
- Detection: [How and when detected]
- Scope: [What was affected]
- Impact: [Business and technical impact]
- Duration: [Timeline]

## Timeline
[Detailed chronological sequence]

## Root Cause
[Technical analysis of how incident occurred]

## Response Actions
[What was done to contain and resolve]

## Lessons Learned
[What worked well and what didn't]

## Recommendations
[Specific actions to prevent recurrence]

## Appendices
- Technical logs
- Communications
- Evidence
```

#### 2. Runbook Updates
- Update incident response procedures
- Add new threat indicators
- Improve detection rules
- Enhance containment procedures

### Follow-up Actions

#### 1. Security Enhancements
```bash
# Deploy additional security tools
kubectl apply -f security-enhancements/

# Update security configurations
kubectl apply -f updated-security-configs/

# Implement new monitoring rules
kubectl apply -f enhanced-monitoring/
```

#### 2. Team Training
- Conduct incident response simulation
- Security awareness training
- Technical security training
- Update emergency procedures

### Metrics and KPIs

Track security incident metrics:
- Mean Time to Detection (MTTD)
- Mean Time to Containment (MTTC)
- Mean Time to Recovery (MTTR)
- False positive rate
- Security tool effectiveness

## Emergency Contacts

### Security Team
- **CISO**: +1-555-CISO
- **Security Lead**: +1-555-SEC-LEAD
- **Security Engineer**: +1-555-SEC-ENG

### Legal & Compliance
- **General Counsel**: +1-555-LEGAL
- **Privacy Officer**: +1-555-PRIVACY
- **Compliance Manager**: +1-555-COMPLIANCE

### External Partners
- **Security Vendor**: +1-555-SEC-VENDOR
- **Legal Counsel**: +1-555-EXT-LEGAL
- **Cyber Insurance**: +1-555-INSURANCE
- **Law Enforcement**: +1-555-FBI-CYBER

### Communication Channels
- **Security Incidents**: #security-incidents
- **Executive Updates**: #exec-security
- **Legal Communications**: #legal-security
- **External Comms**: #external-security
