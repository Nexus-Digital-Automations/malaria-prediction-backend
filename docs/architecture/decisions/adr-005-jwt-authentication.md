# ADR-005: JWT-Based Authentication

## Status
Accepted

## Context

The API requires authentication and authorization to:
- Protect prediction endpoints from abuse
- Support role-based access control (healthcare workers, researchers, admins)
- Enable audit logging of API usage
- Allow stateless scaling across multiple API instances
- Support mobile and web clients

Options considered:
1. **Session-based Authentication** - Server-side sessions with cookies
2. **API Keys** - Simple but limited security features
3. **OAuth 2.0 with External Provider** - Delegated auth (Google, Auth0)
4. **JWT (JSON Web Tokens)** - Stateless, self-contained tokens
5. **Hybrid (JWT + Refresh Tokens)** - JWTs with refresh mechanism

## Decision

We chose **JWT-based authentication with refresh tokens**:

### Token Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │     │   API       │     │  Database   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  POST /auth/login │                   │
       │  {email, password}│                   │
       │──────────────────>│                   │
       │                   │  Verify credentials
       │                   │──────────────────>│
       │                   │<──────────────────│
       │                   │                   │
       │   {access_token,  │                   │
       │    refresh_token} │                   │
       │<──────────────────│                   │
       │                   │                   │
       │  GET /predictions │                   │
       │  Authorization:   │                   │
       │  Bearer <token>   │                   │
       │──────────────────>│                   │
       │                   │  Verify JWT       │
       │   {prediction...} │  (no DB call)     │
       │<──────────────────│                   │
       │                   │                   │
```

### Token Specifications

| Token Type | Lifetime | Storage | Purpose |
|------------|----------|---------|---------|
| Access Token | 15 minutes | Memory/Header | API authentication |
| Refresh Token | 7 days | HttpOnly Cookie | Token renewal |
| API Key | Long-lived | Database | Service-to-service auth |

### JWT Payload Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "roles": ["healthcare_worker"],
  "permissions": ["predictions:read", "reports:read"],
  "iat": 1699000000,
  "exp": 1699000900,
  "iss": "malaria-predictor"
}
```

### Security Features

1. **Token Signing**: RS256 asymmetric signing (private key signs, public key verifies)
2. **Token Rotation**: Refresh tokens are rotated on use
3. **Token Revocation**: Blacklist stored in Redis for immediate revocation
4. **Rate Limiting**: Per-user and per-endpoint rate limits
5. **Audit Logging**: All authentication events logged

## Consequences

### Positive
- Stateless authentication enables horizontal scaling
- Self-contained tokens reduce database lookups
- Role-based access control embedded in tokens
- Mobile-friendly (no cookies required for access tokens)
- Standards-based (RFC 7519)

### Negative
- Tokens cannot be invalidated before expiry without blacklist
- Token payload increases request size
- Key management complexity for RS256
- Clock skew can cause validation issues

### Mitigations
- Short-lived access tokens (15 min) limit exposure window
- Redis-based token blacklist for immediate revocation
- Automatic key rotation with grace period
- NTP synchronization across servers

## References

- [Authentication Documentation](../../api/authentication.md)
- [Security Documentation](../../security/README.md)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
