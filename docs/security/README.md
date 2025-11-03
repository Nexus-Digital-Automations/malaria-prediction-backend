# Security Documentation

> **🔒 Comprehensive security architecture and compliance guidelines**

## Table of Contents
- [Security Overview](#security-overview)
- [Authentication & Authorization](#authentication--authorization)
- [Data Protection](#data-protection)
- [API Security](#api-security)
- [Infrastructure Security](#infrastructure-security)
- [Compliance](#compliance)
- [Security Best Practices](#security-best-practices)
- [Incident Response](#incident-response)

---

## Security Overview

The Malaria Prediction System implements defense-in-depth security architecture with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────────┐
│              Security Layers (Defense in Depth)             │
├─────────────────────────────────────────────────────────────┤
│  Layer 7: Application Security                             │
│    • Input validation                                       │
│    • Output encoding                                        │
│    • Authentication & authorization                         │
│    • Session management                                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: Data Security                                     │
│    • Encryption at rest                                     │
│    • Encryption in transit                                  │
│    • Data masking & anonymization                          │
│    • Backup encryption                                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: API Security                                      │
│    • Rate limiting                                          │
│    • API authentication                                     │
│    • Request validation                                     │
│    • CORS policy                                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Network Security                                  │
│    • TLS 1.3                                                │
│    • Network segmentation                                   │
│    • Firewall rules                                         │
│    • DDoS protection                                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Infrastructure Security                           │
│    • Container security                                     │
│    • Host hardening                                         │
│    • Secrets management                                     │
│    • Vulnerability scanning                                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Monitoring & Detection                            │
│    • Audit logging                                          │
│    • Security monitoring                                    │
│    • Intrusion detection                                    │
│    • Anomaly detection                                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Compliance & Governance                           │
│    • HIPAA compliance                                       │
│    • GDPR compliance                                        │
│    • Security policies                                      │
│    • Incident response                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### JWT Authentication

**Token Structure:**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "role": "healthcare_professional",
    "permissions": ["predict:read", "analytics:read"],
    "exp": 1699000000,
    "iat": 1698996400
  }
}
```

**Authentication Flow:**

```
┌────────────┐                 ┌─────────────┐
│   Client   │                 │  API Server │
└──────┬─────┘                 └──────┬──────┘
       │                              │
       │  1. POST /auth/login         │
       │  {username, password}        │
       ├─────────────────────────────>│
       │                              │
       │                         2. Validate
       │                         credentials
       │                         (bcrypt)
       │                              │
       │  3. Return JWT tokens        │
       │  {access_token,              │
       │   refresh_token}             │
       │<─────────────────────────────┤
       │                              │
       │  4. API Request              │
       │  Authorization: Bearer <JWT> │
       ├─────────────────────────────>│
       │                              │
       │                         5. Verify JWT
       │                         • Signature
       │                         • Expiration
       │                         • Claims
       │                              │
       │  6. Return response          │
       │<─────────────────────────────┤
       │                              │
```

**Token Management:**

```python
# Token configuration (environment variables)
JWT_SECRET_KEY="<strong-random-secret-256-bits>"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password requirements
MIN_PASSWORD_LENGTH=12
REQUIRE_UPPERCASE=true
REQUIRE_LOWERCASE=true
REQUIRE_DIGITS=true
REQUIRE_SPECIAL_CHARS=true
PASSWORD_HISTORY=5  # Prevent reuse of last 5 passwords
```

### Role-Based Access Control (RBAC)

**User Roles:**

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | System administrator | All permissions |
| **Healthcare Professional** | Medical staff | Predictions, analytics, patient data |
| **Researcher** | Research personnel | Predictions, analytics, bulk exports |
| **Public Health Official** | Government health officers | Dashboard, reports, outbreak data |
| **Data Analyst** | Data analysis staff | Analytics, reports, data exports |
| **API User** | External API consumers | API-only access (limited endpoints) |

**Permission Matrix:**

| Resource | Admin | Healthcare | Researcher | Public Health | Data Analyst | API User |
|----------|-------|------------|------------|---------------|--------------|----------|
| Predictions | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Patient Data | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Analytics | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| User Management | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| System Config | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Bulk Export | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| ML Model Training | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |

**Implementation Example:**

```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: str):
    """Decorator to enforce permission-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if permission not in current_user.permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission} required"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage in endpoint
@router.post("/predict/single")
@require_permission("predict:create")
async def create_prediction(request: PredictionRequest, current_user: User):
    # Endpoint logic
    pass
```

---

## Data Protection

### Encryption Standards

**Encryption at Rest:**
- **Database**: PostgreSQL with Transparent Data Encryption (TDE)
- **Backups**: AES-256 encryption for all backup files
- **File Storage**: Server-side encryption (SSE-S3) for object storage
- **Secrets**: HashiCorp Vault or Kubernetes Secrets (encrypted etcd)

**Encryption in Transit:**
- **API Endpoints**: TLS 1.3 (minimum TLS 1.2)
- **Database Connections**: SSL/TLS with certificate verification
- **Internal Services**: Mutual TLS (mTLS) in service mesh
- **WebSockets**: WSS (WebSocket Secure) protocol

**TLS Configuration:**
```nginx
# NGINX TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

### Sensitive Data Handling

**PII (Personally Identifiable Information) Protection:**

```python
# Data classification
class DataClassification(Enum):
    PUBLIC = "public"           # No restrictions
    INTERNAL = "internal"       # Internal use only
    CONFIDENTIAL = "confidential"  # Sensitive data
    RESTRICTED = "restricted"   # Highly sensitive (PII/PHI)

# Data masking for logs
def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive fields in log output"""
    sensitive_fields = [
        'password', 'token', 'api_key', 'ssn',
        'credit_card', 'email', 'phone'
    ]

    masked_data = data.copy()
    for field in sensitive_fields:
        if field in masked_data:
            masked_data[field] = "***REDACTED***"

    return masked_data

# Usage in logging
logger.info(
    "User login attempt",
    extra=mask_sensitive_data({
        "username": "john.doe",
        "email": "john@example.com",  # Will be masked
        "ip_address": "192.168.1.1"
    })
)
```

**Data Retention & Deletion:**

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Prediction Requests | 2 years | Soft delete (anonymization) |
| User Activity Logs | 1 year | Hard delete |
| Audit Logs | 7 years | Archived (encrypted) |
| Patient Data | Per HIPAA/GDPR | Secure erasure |
| ML Training Data | Indefinite | Anonymized |

---

## API Security

### Rate Limiting

**Rate Limit Tiers:**

```python
# Rate limits per user tier
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 1000
    },
    "basic": {
        "requests_per_minute": 50,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "professional": {
        "requests_per_minute": 100,
        "requests_per_hour": 5000,
        "requests_per_day": 50000
    },
    "enterprise": {
        "requests_per_minute": 500,
        "requests_per_hour": 20000,
        "requests_per_day": 200000
    }
}
```

**Rate Limiting Implementation:**

```python
from fastapi import HTTPException
from redis import Redis
import time

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        user_id: str,
        tier: str
    ) -> bool:
        """Check if user has exceeded rate limit"""
        key = f"rate_limit:{user_id}:minute"
        current_count = self.redis.incr(key)

        if current_count == 1:
            # First request in window, set TTL
            self.redis.expire(key, 60)

        limit = RATE_LIMITS[tier]["requests_per_minute"]

        if current_count > limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )

        return True
```

### Input Validation

**Request Validation with Pydantic:**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

class PredictionRequest(BaseModel):
    """Validated prediction request model"""

    location: LocationData
    environmental_data: EnvironmentalData
    prediction_date: date
    model_type: str = Field(..., regex="^(lstm|transformer|ensemble)$")

    @validator('prediction_date')
    def validate_date_range(cls, v):
        """Ensure prediction date is within valid range"""
        today = date.today()
        max_future = today.replace(year=today.year + 1)

        if v < today:
            raise ValueError("Prediction date cannot be in the past")
        if v > max_future:
            raise ValueError("Prediction date too far in future (max 1 year)")

        return v

    @validator('environmental_data')
    def validate_environmental_ranges(cls, v):
        """Validate environmental data ranges"""
        if v.mean_temperature < -50 or v.mean_temperature > 60:
            raise ValueError("Temperature out of valid range")
        if v.monthly_rainfall < 0 or v.monthly_rainfall > 2000:
            raise ValueError("Rainfall out of valid range")

        return v

    class Config:
        # Prevent additional fields
        extra = 'forbid'
```

### SQL Injection Prevention

**Using SQLAlchemy ORM (Parameterized Queries):**

```python
from sqlalchemy.orm import Session
from sqlalchemy import select

# ❌ NEVER DO THIS (Vulnerable to SQL injection)
def get_user_unsafe(username: str, db: Session):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)

# ✅ SAFE: Use ORM or parameterized queries
def get_user_safe(username: str, db: Session):
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()

# ✅ SAFE: Named parameters
def get_user_with_params(username: str, db: Session):
    query = "SELECT * FROM users WHERE username = :username"
    return db.execute(query, {"username": username})
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",        # Production frontend
        "https://staging.example.com",    # Staging frontend
        "http://localhost:3000",          # Local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

---

## Infrastructure Security

### Container Security

**Dockerfile Security Best Practices:**

```dockerfile
# Use specific version tags (not 'latest')
FROM python:3.11.6-slim-bookworm

# Run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only necessary files
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Use HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set read-only root filesystem
# docker run --read-only --tmpfs /tmp ...
```

**Container Scanning:**

```yaml
# .github/workflows/security-scan.yml
name: Container Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build image
        run: docker build -t malaria-api:${{ github.sha }} .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'malaria-api:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### Secrets Management

**Never Store Secrets in Code:**

```bash
# ❌ BAD: Hardcoded secrets
DATABASE_URL = "postgresql://admin:SuperSecret123@db:5432/app"

# ✅ GOOD: Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ BETTER: Secrets management service
# Using HashiCorp Vault
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(role_id='...', secret_id='...')
database_creds = client.secrets.kv.v2.read_secret_version(
    path='database/credentials'
)
```

**Kubernetes Secrets:**

```yaml
# secrets.yaml (encrypted with Sealed Secrets or External Secrets)
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  database-url: postgresql://...
  jwt-secret: <base64-encoded-secret>
  api-key: <encrypted-api-key>
```

### Network Security

**Network Policies (Kubernetes):**

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: malaria-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow traffic from ingress controller only
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
      - protocol: TCP
        port: 8000
  egress:
    # Allow traffic to database and Redis only
    - to:
      - podSelector:
          matchLabels:
            app: postgresql
      ports:
      - protocol: TCP
        port: 5432
    - to:
      - podSelector:
          matchLabels:
            app: redis
      ports:
      - protocol: TCP
        port: 6379
```

---

## Compliance

### HIPAA Compliance

**Technical Safeguards:**

| Requirement | Implementation |
|-------------|----------------|
| Access Control | JWT authentication, RBAC |
| Audit Controls | Comprehensive audit logging |
| Integrity | Data validation, checksums |
| Transmission Security | TLS 1.3, mTLS |

**Administrative Safeguards:**
- Security management processes
- Workforce security training
- Contingency planning (disaster recovery)
- Access authorization procedures

**Physical Safeguards:**
- Cloud provider compliance (AWS/GCP/Azure)
- Facility access controls
- Workstation security policies

### GDPR Compliance

**Data Subject Rights:**

| Right | Implementation |
|-------|----------------|
| Right to Access | API endpoint to export user data |
| Right to Rectification | Update endpoints for data correction |
| Right to Erasure | Hard delete with audit trail |
| Right to Portability | JSON/CSV export functionality |
| Right to Object | Opt-out mechanisms |

**Data Processing Records:**
```python
# audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)  # "create", "read", "update", "delete"
    resource_type = Column(String)  # "prediction", "user", etc.
    resource_id = Column(UUID)
    ip_address = Column(String)
    user_agent = Column(String)
    changes = Column(JSONB)  # Before/after values
```

---

## Security Best Practices

### Development Security Checklist

- [ ] **Code Review**: All changes reviewed by security-aware developer
- [ ] **Dependency Scanning**: Regular scans with `pip-audit` or `safety`
- [ ] **Static Analysis**: SAST tools (Bandit, Semgrep)
- [ ] **Secret Scanning**: Pre-commit hooks to prevent secret commits
- [ ] **Input Validation**: All user inputs validated and sanitized
- [ ] **Error Handling**: No sensitive data in error messages
- [ ] **Logging**: Sensitive data masked in logs
- [ ] **Testing**: Security test cases in test suite

### Deployment Security Checklist

- [ ] **TLS Certificates**: Valid, not self-signed
- [ ] **Firewall Rules**: Minimal open ports
- [ ] **Environment Variables**: No secrets in Dockerfile
- [ ] **Container Scanning**: No critical vulnerabilities
- [ ] **Least Privilege**: Services run as non-root
- [ ] **Network Policies**: Strict ingress/egress rules
- [ ] **Monitoring**: Security events monitored
- [ ] **Backups**: Encrypted, tested recovery

### Security Monitoring

**Key Security Metrics:**

```python
# Prometheus metrics for security monitoring
security_events = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'severity']
)

failed_auth_attempts = Counter(
    'failed_auth_attempts_total',
    'Failed authentication attempts',
    ['username', 'ip_address']
)

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Rate limit violations',
    ['user_id', 'endpoint']
)
```

**Alert Rules:**

```yaml
# prometheus-alerts.yml
groups:
  - name: security
    rules:
      - alert: HighFailedAuthRate
        expr: rate(failed_auth_attempts_total[5m]) > 10
        for: 5m
        annotations:
          summary: "High rate of failed authentication attempts"

      - alert: RateLimitViolations
        expr: rate(rate_limit_exceeded_total[5m]) > 100
        for: 5m
        annotations:
          summary: "Excessive rate limit violations"
```

---

## Incident Response

### Security Incident Response Plan

**Phase 1: Detection & Analysis**
1. Monitor security alerts (Prometheus, CloudWatch, etc.)
2. Analyze logs for suspicious activity
3. Determine incident severity
4. Assemble incident response team

**Phase 2: Containment**
1. Isolate affected systems
2. Preserve evidence (logs, snapshots)
3. Block malicious IPs/users
4. Revoke compromised credentials

**Phase 3: Eradication**
1. Identify root cause
2. Remove malware/backdoors
3. Patch vulnerabilities
4. Update firewall rules

**Phase 4: Recovery**
1. Restore from clean backups
2. Verify system integrity
3. Monitor for re-infection
4. Gradual service restoration

**Phase 5: Post-Incident**
1. Document incident timeline
2. Update security measures
3. Conduct lessons learned session
4. Update incident response plan

### Emergency Contacts

```
Security Team Lead: security@example.com
On-Call Engineer: +1-xxx-xxx-xxxx
AWS Support: <account-support-email>
Legal Team: legal@example.com
```

---

## Security Audit Reports

Regular security audits are conducted:

- **Internal Audits**: Quarterly
- **External Penetration Testing**: Annually
- **Dependency Scans**: Weekly (automated)
- **Container Scans**: On every build (CI/CD)
- **Compliance Audits**: Annually (HIPAA/GDPR)

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [GDPR Compliance](https://gdpr.eu/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last Updated**: November 3, 2025
**Document Version**: 1.0.0
