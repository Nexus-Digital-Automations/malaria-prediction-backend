# API Overview

> **Malaria Prediction Backend - RESTful API Documentation**
>
> Version: 1.0.0 | FastAPI-based asynchronous API

## Introduction

The Malaria Prediction Backend provides a comprehensive REST API built with FastAPI that enables:

- **Malaria risk predictions** using advanced ML models (LSTM, Transformer, Ensemble)
- **Real-time alerts** via WebSocket connections
- **Healthcare professional tools** for patient management and resource planning
- **Analytics and reporting** for public health decision-making
- **Environmental data integration** from 80+ sources (ERA5, CHIRPS, MODIS, MAP, WorldPop)

## Architecture Principles

### Design Philosophy

1. **Async-First**: Built on FastAPI's async capabilities for high-performance I/O operations
2. **Security by Default**: JWT authentication, rate limiting, and comprehensive audit logging
3. **RESTful Standards**: Follows REST principles with resource-based URLs and HTTP semantics
4. **OpenAPI Compliant**: Automatic Swagger UI and ReDoc documentation generation
5. **Production-Ready**: Comprehensive error handling, logging, and monitoring

### Key Features

- ⚡ **Sub-500ms response times** for prediction endpoints
- 🔒 **OAuth 2.0 + JWT** authentication with scope-based authorization
- 📊 **Automatic API documentation** at `/docs` (Swagger) and `/redoc` (ReDoc)
- 🚦 **Rate limiting** (100 requests/minute default)
- 💾 **Redis caching** for frequently accessed predictions
- 🔌 **WebSocket support** for real-time alert delivery
- 📝 **Comprehensive audit logging** for compliance (HIPAA-ready)
- 🌐 **CORS enabled** for web frontend integration

## API Structure

### Base URL

```
Production:  https://api.malaria-prediction.example.com/v1
Development: http://localhost:8000/v1
```

### Router Organization

The API is organized into logical routers:

| Router | Base Path | Description |
|--------|-----------|-------------|
| **Prediction** | `/predict` | Core malaria risk prediction endpoints |
| **Alerts** | `/alerts` | Alert management and WebSocket connections |
| **Analytics** | `/analytics` | Data analytics and visualization |
| **Reports** | `/reports` | Report generation (PDF, CSV) |
| **Outbreak** | `/outbreak` | Outbreak detection and analysis |
| **Healthcare** | `/healthcare` | Healthcare professional tools |
| **Notifications** | `/notifications` | Firebase Cloud Messaging integration |
| **Auth** | `/auth` | Authentication and token management |
| **Health** | `/health` | System health and monitoring |
| **Operations** | `/ops` | Operational endpoints for admins |

### Endpoint Patterns

All endpoints follow RESTful conventions:

```
GET    /resource          # List resources
GET    /resource/{id}     # Get specific resource
POST   /resource          # Create new resource
PUT    /resource/{id}     # Update resource (full)
PATCH  /resource/{id}     # Update resource (partial)
DELETE /resource/{id}     # Delete resource
```

## Request/Response Format

### Content Type

All requests and responses use **JSON** (`application/json`).

### Standard Response Structure

```json
{
  "data": { },           // Response payload
  "metadata": {
    "request_id": "uuid",
    "timestamp": "ISO 8601 timestamp",
    "processing_time_ms": 150
  }
}
```

### Error Response Structure

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { },       // Additional error context
    "request_id": "uuid"
  }
}
```

## Middleware Stack

Requests flow through multiple middleware layers:

```
┌─────────────────────────────┐
│  CORS Middleware            │  Cross-origin support
├─────────────────────────────┤
│  GZip Middleware            │  Response compression
├─────────────────────────────┤
│  Security Headers           │  HSTS, CSP, X-Frame-Options
├─────────────────────────────┤
│  Request ID                 │  UUID for request tracking
├─────────────────────────────┤
│  Logging Middleware         │  Comprehensive request logging
├─────────────────────────────┤
│  Rate Limit Middleware      │  Request throttling
├─────────────────────────────┤
│  Audit Logging              │  HIPAA compliance logging
├─────────────────────────────┤
│  Input Validation           │  Request sanitization
└─────────────────────────────┘
```

## Versioning

The API uses URL-based versioning:

```
/v1/predict/single    # Current stable version
/v2/predict/single    # Future version (when available)
```

**Current Version**: `v1`

**Deprecation Policy**:
- Minimum 6 months notice for breaking changes
- Deprecated endpoints return `X-API-Deprecated` header
- Migration guides provided in documentation

## Rate Limiting

Default rate limits apply to all endpoints:

- **Standard Users**: 100 requests/minute
- **Premium Users**: 1000 requests/minute
- **Admin Users**: 10,000 requests/minute

Rate limit headers returned with every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640000000
```

See [Rate Limiting Guide](./rate-limiting.md) for details.

## Authentication

All endpoints (except `/health` and `/auth/login`) require authentication.

**Method**: Bearer token (JWT)

```http
Authorization: Bearer <your-jwt-token>
```

See [Authentication Guide](./authentication.md) for complete details.

## Pagination

List endpoints support cursor-based pagination:

**Request**:
```http
GET /analytics/predictions?limit=50&cursor=eyJpZCI6MTIzfQ==
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTczfQ==",
    "has_more": true,
    "total_count": 1543
  }
}
```

**Parameters**:
- `limit`: Items per page (default: 25, max: 100)
- `cursor`: Opaque cursor for next page

## Filtering and Sorting

Query parameters for filtering:

```http
GET /predictions?
  location=nairobi&
  risk_level=high&
  date_from=2024-01-01&
  date_to=2024-12-31&
  sort_by=risk_score&
  order=desc
```

**Common Filter Parameters**:
- `location`: Geographic filter (coordinates, names, regions)
- `risk_level`: Filter by risk category (low, medium, high, very_high)
- `date_from` / `date_to`: Date range filters
- `sort_by`: Field to sort by
- `order`: Sort direction (`asc` or `desc`)

## Data Formats

### Dates and Times

All timestamps use **ISO 8601** format in **UTC**:

```json
{
  "created_at": "2024-01-15T14:30:00Z",
  "target_date": "2024-02-01"
}
```

### Geographic Coordinates

Coordinates use **WGS84** (EPSG:4326):

```json
{
  "location": {
    "latitude": -1.2921,    // Decimal degrees
    "longitude": 36.8219,   // Decimal degrees
    "name": "Nairobi, Kenya"
  }
}
```

### Risk Scores

Risk scores are normalized to **[0.0, 1.0]** range:

```json
{
  "risk_score": 0.73,        // 0.0 = no risk, 1.0 = maximum risk
  "risk_level": "high",      // categorical classification
  "uncertainty": 0.05        // prediction uncertainty (±)
}
```

## Performance Considerations

### Response Time SLAs

| Endpoint Type | Target | Maximum |
|---------------|--------|---------|
| Single Prediction | < 300ms | 500ms |
| Batch Prediction | < 2s | 5s |
| Analytics Queries | < 1s | 3s |
| Health Checks | < 50ms | 100ms |

### Caching Strategy

- Prediction results cached for **1 hour** (configurable)
- Environmental data cached for **24 hours**
- Analytics aggregations cached for **15 minutes**

**Cache Headers**:
```http
X-Cache: HIT
Cache-Control: public, max-age=3600
ETag: "abc123def456"
```

## WebSocket Connections

Real-time features use WebSocket connections:

```javascript
ws://localhost:8000/v1/alerts/ws?token=<jwt-token>
```

See [WebSocket Guide](./websockets.md) for details.

## API Health and Status

### Health Check Endpoints

```http
GET /health              # Basic health check
GET /health/ready        # Readiness probe (K8s)
GET /health/live         # Liveness probe (K8s)
GET /health/detailed     # Comprehensive system status
```

### Status Page

Real-time API status available at:
```
https://status.malaria-prediction.example.com
```

## Getting Started

1. **Obtain API credentials** from your administrator
2. **Authenticate** to get JWT token: `POST /auth/login`
3. **Make your first prediction**: `POST /predict/single`
4. **Explore Swagger UI**: Navigate to `/docs`

## Further Reading

- [API Endpoints Reference](./endpoints.md) - Complete endpoint catalog
- [Authentication Guide](./authentication.md) - Auth flows and token management
- [Error Codes](./error-codes.md) - Error code reference
- [Rate Limiting](./rate-limiting.md) - Rate limit details
- [WebSockets](./websockets.md) - Real-time connections

## Support

- **Documentation**: [https://docs.malaria-prediction.example.com](https://docs.malaria-prediction.example.com)
- **API Issues**: Create issue on GitHub
- **Email**: api-support@malaria-prediction.example.com

---

**Last Updated**: October 27, 2025
