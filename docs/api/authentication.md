# Authentication Guide

> **JWT-based authentication with scope-based authorization**

## Overview

The Malaria Prediction API uses **JWT (JSON Web Tokens)** for authentication with **OAuth 2.0 scope-based authorization**.

### Authentication Flow

```
1. User submits credentials → POST /auth/login
2. Server validates credentials
3. Server returns JWT access token + refresh token
4. Client includes token in Authorization header
5. Server validates token and scopes for each request
```

## Obtaining Tokens

### Login

**Endpoint**: `POST /v1/auth/login`

**Request**:
```json
{
  "username": "user@example.com",
  "password": "secure-password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scopes": [
    "read:predictions",
    "write:predictions",
    "read:analytics"
  ]
}
```

### Token Types

| Token Type | Purpose | Lifetime |
|------------|---------|----------|
| **Access Token** | API requests | 1 hour |
| **Refresh Token** | Renew access tokens | 30 days |

## Using Access Tokens

Include the access token in the `Authorization` header:

```http
GET /v1/predict/single HTTP/1.1
Host: api.malaria-prediction.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Code Examples

**Python (requests)**:
```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.malaria-prediction.example.com/v1/predict/single",
    headers=headers,
    json={"location": {...}, "target_date": "2024-02-01"}
)
```

**JavaScript (fetch)**:
```javascript
const response = await fetch('/v1/predict/single', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    location: {...},
    target_date: '2024-02-01'
  })
});
```

**cURL**:
```bash
curl -X POST https://api.malaria-prediction.example.com/v1/predict/single \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"location": {...}, "target_date": "2024-02-01"}'
```

## Refreshing Tokens

When the access token expires, use the refresh token to obtain a new one:

**Endpoint**: `POST /v1/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Automatic Token Refresh

Implement automatic token refresh in your client:

```python
class APIClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.login()

    def login(self):
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": self.username, "password": self.password}
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expiry = time.time() + data["expires_in"]

    def ensure_valid_token(self):
        if time.time() >= self.token_expiry - 60:  # Refresh 1 min before expiry
            response = requests.post(
                f"{API_BASE}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expiry = time.time() + data["expires_in"]

    def make_request(self, endpoint, **kwargs):
        self.ensure_valid_token()
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        return requests.post(f"{API_BASE}{endpoint}", **kwargs)
```

## Authorization Scopes

### Available Scopes

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `read:predictions` | View predictions | GET /predict/* |
| `write:predictions` | Create predictions | POST /predict/* |
| `read:analytics` | View analytics | GET /analytics/* |
| `write:analytics` | Create analytics | POST /analytics/* |
| `read:alerts` | View alerts | GET /alerts/* |
| `write:alerts` | Manage alerts | POST/PATCH /alerts/* |
| `read:reports` | View reports | GET /reports/* |
| `write:reports` | Generate reports | POST /reports/* |
| `read:healthcare` | View healthcare data | GET /healthcare/* |
| `write:healthcare` | Manage healthcare data | POST /healthcare/* |
| `admin:operations` | System operations | GET /health/detailed, /ops/* |
| `admin:users` | User management | POST /auth/create-user |
| `admin:notifications` | Send notifications | POST /notifications/send |

### Scope Requirements

Endpoints require specific scopes:

```python
# Endpoint: POST /predict/single
Required scopes: ["read:predictions", "write:predictions"]

# Endpoint: GET /analytics/accuracy
Required scopes: ["read:analytics"]

# Endpoint: POST /reports/generate
Required scopes: ["write:reports"]
```

### User Roles and Scopes

| Role | Default Scopes |
|------|----------------|
| **Viewer** | `read:predictions`, `read:analytics`, `read:alerts` |
| **Analyst** | Viewer + `write:predictions`, `write:analytics` |
| **Healthcare Professional** | Analyst + `read:healthcare`, `write:healthcare`, `write:reports` |
| **Administrator** | All scopes |

## Token Structure

JWT tokens contain encoded information:

### Header
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

### Payload
```json
{
  "sub": "user123",
  "email": "user@example.com",
  "scopes": ["read:predictions", "write:predictions"],
  "iat": 1640000000,
  "exp": 1640003600,
  "jti": "unique-token-id"
}
```

### Signature
```
RSASHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  private_key
)
```

## Security Best Practices

### Token Storage

✅ **DO**:
- Store tokens securely in HttpOnly cookies (web)
- Use secure storage APIs (mobile: Keychain/KeyStore)
- Never log tokens in plain text
- Use environment variables for server-side tokens

❌ **DON'T**:
- Store tokens in localStorage (XSS vulnerable)
- Include tokens in URLs
- Commit tokens to version control
- Share tokens between applications

### Token Transmission

✅ **DO**:
- Always use HTTPS/TLS
- Include tokens only in Authorization header
- Validate server SSL certificate

❌ **DON'T**:
- Send tokens over HTTP
- Include tokens in query parameters
- Embed tokens in client-side JavaScript

### Token Lifecycle

✅ **DO**:
- Implement automatic token refresh
- Handle token expiration gracefully
- Logout on token invalidation
- Request minimal scopes needed

❌ **DON'T**:
- Reuse expired tokens
- Cache tokens indefinitely
- Request unnecessary scopes

## Logout

Invalidate current token:

**Endpoint**: `POST /v1/auth/logout`

**Request**:
```http
POST /v1/auth/logout HTTP/1.1
Authorization: Bearer eyJ...
```

**Response**: `204 No Content`

The token is added to a blocklist and cannot be reused.

## Error Responses

### 401 Unauthorized

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing authentication token",
    "request_id": "abc123"
  }
}
```

**Causes**:
- Missing Authorization header
- Invalid token format
- Expired token
- Token signature invalid

**Solution**: Obtain new token via login or refresh

### 403 Forbidden

```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Required scope 'write:predictions' not granted",
    "required_scopes": ["write:predictions"],
    "granted_scopes": ["read:predictions"],
    "request_id": "abc123"
  }
}
```

**Cause**: User lacks required scopes

**Solution**: Contact administrator for permission escalation

## WebSocket Authentication

WebSocket connections require JWT token in query parameter:

```javascript
const ws = new WebSocket(
  `wss://api.malaria-prediction.example.com/v1/alerts/ws?token=${accessToken}`
);
```

**Note**: Query parameter used because WebSocket API doesn't support custom headers.

## API Keys (Alternative)

For server-to-server communication, API keys can be used:

**Header**:
```http
X-API-Key: your-api-key-here
```

**Limitations**:
- No scopes (full access)
- No automatic expiration
- Admin-only creation

**Best Practice**: Prefer JWT tokens for client applications

## Testing Authentication

### Postman

1. Create environment variables:
   - `base_url`: API base URL
   - `access_token`: JWT token
2. Add to all requests:
   - Header: `Authorization` = `Bearer {{access_token}}`
3. Use Pre-request Script for auto-refresh:

```javascript
if (!pm.environment.get("access_token") || isTokenExpired()) {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/auth/login",
        method: 'POST',
        header: {'Content-Type': 'application/json'},
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                username: pm.environment.get("username"),
                password: pm.environment.get("password")
            })
        }
    }, function (err, res) {
        const data = res.json();
        pm.environment.set("access_token", data.access_token);
        pm.environment.set("token_expiry", Date.now() + (data.expires_in * 1000));
    });
}
```

### cURL

```bash
# Login and extract token
TOKEN=$(curl -s -X POST https://api.example.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# Use token
curl -X GET https://api.example.com/v1/predict/single \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid credentials" | Wrong username/password | Verify credentials |
| "Token expired" | Access token past expiry | Use refresh token |
| "Invalid signature" | Token tampered or wrong key | Obtain new token |
| "Insufficient permissions" | Scope not granted | Request permission escalation |
| "Too many requests" | Rate limit exceeded | Wait or upgrade tier |

## Related Documentation

- [API Overview](./overview.md)
- [Endpoints Reference](./endpoints.md)
- [Error Codes](./error-codes.md)
- [Rate Limiting](./rate-limiting.md)

---

**Last Updated**: October 27, 2025
