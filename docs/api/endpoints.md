# API Endpoints Reference

> **Complete catalog of all REST API endpoints**
>
> Base URL: `/v1`

## Table of Contents

- [Prediction Endpoints](#prediction-endpoints)
- [Alert Endpoints](#alert-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [Report Endpoints](#report-endpoints)
- [Outbreak Endpoints](#outbreak-endpoints)
- [Healthcare Endpoints](#healthcare-endpoints)
- [Notification Endpoints](#notification-endpoints)
- [Authentication Endpoints](#authentication-endpoints)
- [Health & Operations](#health--operations)

---

## Prediction Endpoints

### POST /predict/single

Make malaria risk prediction for a single location.

**Authentication**: Required (`read:predictions`, `write:predictions`)

**Request Body**:
```json
{
  "location": {
    "latitude": -1.2921,
    "longitude": 36.8219,
    "name": "Nairobi, Kenya"
  },
  "target_date": "2024-02-01",
  "model_type": "ensemble",
  "prediction_horizon": "30_days"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "location": {...},
    "target_date": "2024-02-01",
    "risk_score": 0.73,
    "risk_level": "high",
    "uncertainty": 0.05,
    "confidence_interval": [0.68, 0.78],
    "model_type": "ensemble",
    "contributing_factors": {
      "temperature": 0.25,
      "rainfall": 0.35,
      "humidity": 0.20,
      "historical_cases": 0.20
    },
    "prediction_horizon": "30_days",
    "processing_time_ms": 245
  },
  "metadata": {...}
}
```

**Errors**:
- `400` - Invalid request parameters
- `401` - Authentication required
- `403` - Insufficient permissions
- `422` - Validation error
- `500` - Prediction service error

---

### POST /predict/batch

Process multiple prediction requests in a single call.

**Authentication**: Required (`read:predictions`, `write:predictions`)

**Request Body**:
```json
{
  "locations": [
    {"latitude": -1.2921, "longitude": 36.8219, "name": "Nairobi"},
    {"latitude": -1.9536, "longitude": 30.0606, "name": "Kigali"}
  ],
  "target_date": "2024-02-01",
  "model_type": "ensemble"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "predictions": [
      {...},  // Prediction result for each location
      {...}
    ],
    "total_count": 2,
    "processing_time_ms": 512
  },
  "metadata": {...}
}
```

**Limits**: Maximum 50 locations per batch request

---

### POST /predict/timeseries

Generate time series risk predictions for a location.

**Authentication**: Required (`read:predictions`, `write:predictions`)

**Request Body**:
```json
{
  "location": {
    "latitude": -1.2921,
    "longitude": 36.8219
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "interval": "monthly",
  "model_type": "lstm"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "location": {...},
    "timeseries": [
      {
        "date": "2024-01-01",
        "risk_score": 0.45,
        "risk_level": "medium",
        "uncertainty": 0.03
      },
      ...
    ],
    "interval": "monthly",
    "model_type": "lstm"
  },
  "metadata": {...}
}
```

---

### POST /predict/spatial

Generate spatial risk map for a geographic region.

**Authentication**: Required (`read:predictions`, `write:predictions`)

**Request Body**:
```json
{
  "bounds": {
    "north": 5.0,
    "south": -5.0,
    "east": 42.0,
    "west": 34.0
  },
  "target_date": "2024-02-01",
  "resolution": "high",
  "model_type": "ensemble"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "grid_predictions": [...],  // Grid of predictions
    "resolution": "0.1 degrees",
    "bounds": {...},
    "target_date": "2024-02-01",
    "total_cells": 8100
  },
  "metadata": {...}
}
```

---

## Alert Endpoints

### WebSocket: /alerts/ws

Establish WebSocket connection for real-time alerts.

**Authentication**: Required (JWT token via query parameter)

**Connection URL**:
```
ws://localhost:8000/v1/alerts/ws?token=<jwt-token>
```

**Message Format** (Server → Client):
```json
{
  "type": "risk_alert",
  "alert_id": "uuid",
  "severity": "high",
  "location": {...},
  "risk_score": 0.82,
  "message": "High malaria risk detected",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Client Actions**:
```json
{
  "action": "subscribe",
  "locations": [
    {"latitude": -1.2921, "longitude": 36.8219}
  ]
}
```

See [WebSocket Guide](./websockets.md) for details.

---

### GET /alerts

List all alerts for the authenticated user.

**Authentication**: Required

**Query Parameters**:
- `status`: Filter by status (`active`, `acknowledged`, `resolved`)
- `severity`: Filter by severity (`low`, `medium`, `high`, `critical`)
- `limit`: Results per page (default: 25, max: 100)
- `cursor`: Pagination cursor

**Response** `200 OK`:
```json
{
  "data": {
    "alerts": [
      {
        "alert_id": "uuid",
        "severity": "high",
        "location": {...},
        "risk_score": 0.82,
        "status": "active",
        "created_at": "2024-01-15T14:30:00Z"
      },
      ...
    ]
  },
  "pagination": {...}
}
```

---

### GET /alerts/{alert_id}

Get specific alert details.

**Authentication**: Required

**Response** `200 OK`:
```json
{
  "data": {
    "alert_id": "uuid",
    "severity": "high",
    "location": {...},
    "risk_score": 0.82,
    "status": "active",
    "created_at": "2024-01-15T14:30:00Z",
    "acknowledged_at": null,
    "resolved_at": null,
    "actions_taken": []
  }
}
```

---

### PATCH /alerts/{alert_id}

Update alert status (acknowledge, resolve).

**Authentication**: Required

**Request Body**:
```json
{
  "status": "acknowledged",
  "notes": "Team notified and response initiated"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "alert_id": "uuid",
    "status": "acknowledged",
    "acknowledged_at": "2024-01-15T15:00:00Z"
  }
}
```

---

## Analytics Endpoints

### GET /analytics/predictions/accuracy

Get model prediction accuracy metrics.

**Authentication**: Required (`read:analytics`)

**Query Parameters**:
- `model_type`: Filter by model (optional)
- `date_from`: Start date
- `date_to`: End date
- `location`: Filter by location (optional)

**Response** `200 OK`:
```json
{
  "data": {
    "overall_accuracy": 0.92,
    "precision": 0.89,
    "recall": 0.94,
    "f1_score": 0.91,
    "mae": 0.05,
    "rmse": 0.07,
    "by_model": {
      "lstm": {"accuracy": 0.91, ...},
      "transformer": {"accuracy": 0.90, ...},
      "ensemble": {"accuracy": 0.92, ...}
    },
    "date_range": {...}
  }
}
```

---

### GET /analytics/trends/environmental

Get environmental trend analysis.

**Authentication**: Required (`read:analytics`)

**Response** `200 OK`:
```json
{
  "data": {
    "temperature_trend": {
      "current": 28.5,
      "change_30d": 1.2,
      "change_90d": 2.8,
      "anomaly": "above_normal"
    },
    "rainfall_trend": {...},
    "humidity_trend": {...}
  }
}
```

---

### GET /analytics/risk/map

Get current risk map data for visualization.

**Authentication**: Required (`read:analytics`)

**Query Parameters**:
- `bounds`: Geographic bounds (JSON)
- `resolution`: Map resolution (`low`, `medium`, `high`)
- `date`: Target date (default: current)

**Response** `200 OK`:
```json
{
  "data": {
    "risk_grid": [...],  // 2D array of risk values
    "bounds": {...},
    "resolution": "0.1 degrees",
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

---

## Report Endpoints

### POST /reports/generate

Generate custom malaria risk report.

**Authentication**: Required (`write:reports`)

**Request Body**:
```json
{
  "report_type": "risk_assessment",
  "format": "pdf",
  "location": {...},
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "sections": ["predictions", "trends", "recommendations"]
}
```

**Response** `202 Accepted`:
```json
{
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "estimated_completion": "2024-01-15T14:35:00Z"
  }
}
```

---

### GET /reports/{report_id}

Get report status or download completed report.

**Authentication**: Required (`read:reports`)

**Response** `200 OK` (Processing):
```json
{
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "progress": 45
  }
}
```

**Response** `200 OK` (Completed):
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="report_uuid.pdf"

<PDF binary data>
```

---

## Outbreak Endpoints

### GET /outbreak/detect

Detect potential outbreaks in a region.

**Authentication**: Required (`read:outbreak`)

**Query Parameters**:
- `location`: Geographic location
- `radius_km`: Search radius in kilometers
- `threshold`: Risk threshold for detection

**Response** `200 OK`:
```json
{
  "data": {
    "outbreaks_detected": true,
    "hotspots": [
      {
        "location": {...},
        "risk_score": 0.88,
        "affected_population": 150000,
        "severity": "high",
        "trend": "increasing"
      }
    ],
    "analysis_timestamp": "2024-01-15T14:30:00Z"
  }
}
```

---

### GET /outbreak/patterns

Analyze historical outbreak patterns.

**Authentication**: Required (`read:outbreak`)

**Response** `200 OK`:
```json
{
  "data": {
    "seasonal_patterns": [...],
    "geographic_clusters": [...],
    "temporal_trends": [...]
  }
}
```

---

## Healthcare Endpoints

### GET /healthcare/protocols

Get malaria treatment protocols.

**Authentication**: Required (`read:healthcare`)

**Query Parameters**:
- `region`: Geographic region
- `patient_type`: Patient category

**Response** `200 OK`:
```json
{
  "data": {
    "protocols": [
      {
        "protocol_id": "uuid",
        "name": "WHO Standard Treatment",
        "description": "...",
        "medications": [...],
        "dosage_guidelines": {...}
      }
    ]
  }
}
```

---

### POST /healthcare/resource-allocation

Calculate resource allocation recommendations.

**Authentication**: Required (`write:healthcare`)

**Request Body**:
```json
{
  "location": {...},
  "prediction_period": "30_days",
  "resources": ["antimalarials", "test_kits", "bed_nets"]
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "recommendations": [
      {
        "resource": "antimalarials",
        "recommended_quantity": 5000,
        "current_stock": 3200,
        "shortfall": 1800,
        "priority": "high"
      }
    ]
  }
}
```

---

## Notification Endpoints

### POST /notifications/subscribe

Subscribe to FCM push notifications.

**Authentication**: Required

**Request Body**:
```json
{
  "fcm_token": "...",
  "topics": ["risk_alerts", "system_updates"],
  "location_preferences": [...]
}
```

**Response** `201 Created`:
```json
{
  "data": {
    "subscription_id": "uuid",
    "topics": ["risk_alerts", "system_updates"],
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

---

### POST /notifications/send

Send push notification (admin only).

**Authentication**: Required (`admin:notifications`)

**Request Body**:
```json
{
  "topic": "risk_alerts",
  "title": "High Risk Alert",
  "body": "Malaria risk elevated in Nairobi",
  "data": {...}
}
```

---

## Authentication Endpoints

### POST /auth/login

Authenticate user and obtain JWT token.

**Authentication**: None required

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "secure-password"
}
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ...",
  "scopes": ["read:predictions", "write:predictions"]
}
```

---

### POST /auth/refresh

Refresh expired access token.

**Authentication**: Refresh token required

**Request Body**:
```json
{
  "refresh_token": "eyJ..."
}
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### POST /auth/logout

Invalidate current token.

**Authentication**: Required

**Response** `204 No Content`

---

## Health & Operations

### GET /health

Basic health check.

**Authentication**: None required

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

---

### GET /health/ready

Kubernetes readiness probe.

**Response** `200 OK`: Service ready to accept traffic
**Response** `503 Service Unavailable`: Service not ready

---

### GET /health/live

Kubernetes liveness probe.

**Response** `200 OK`: Service alive
**Response** `503 Service Unavailable`: Service needs restart

---

### GET /health/detailed

Comprehensive system status (admin only).

**Authentication**: Required (`admin:operations`)

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy", "latency_ms": 12},
    "redis": {"status": "healthy", "latency_ms": 3},
    "ml_models": {"status": "healthy", "loaded": 3},
    "websocket": {"status": "healthy", "connections": 142}
  },
  "metrics": {
    "requests_per_minute": 450,
    "average_response_time_ms": 245,
    "error_rate": 0.02
  }
}
```

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |
| 204 | No Content | Successful request with no response body |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

**See Also**:
- [Authentication Guide](./authentication.md)
- [Error Codes](./error-codes.md)
- [WebSockets](./websockets.md)

**Last Updated**: October 27, 2025
