# Error Codes Reference

> **Comprehensive error code catalog for the Malaria Prediction API**

## Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context about the error"
    },
    "request_id": "uuid-for-tracking",
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

## HTTP Status Codes

| Status | Description | When Used |
|--------|-------------|-----------|
| 400 | Bad Request | Invalid request parameters or malformed JSON |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Requested resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors in request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server-side error |
| 503 | Service Unavailable | Service temporarily down or overloaded |

---

## Error Codes by Category

### Authentication Errors (AUTH_*)

#### AUTH_INVALID_CREDENTIALS
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```
**HTTP Status**: 401
**Cause**: Incorrect login credentials
**Solution**: Verify username and password

#### AUTH_TOKEN_EXPIRED
```json
{
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Access token has expired",
    "details": {
      "expired_at": "2024-01-15T13:30:00Z"
    }
  }
}
```
**HTTP Status**: 401
**Cause**: JWT token past expiration time
**Solution**: Use refresh token to obtain new access token

#### AUTH_TOKEN_INVALID
```json
{
  "error": {
    "code": "AUTH_TOKEN_INVALID",
    "message": "Token signature is invalid or token has been tampered with"
  }
}
```
**HTTP Status**: 401
**Cause**: Invalid JWT signature or malformed token
**Solution**: Obtain new token via login

#### AUTH_INSUFFICIENT_PERMISSIONS
```json
{
  "error": {
    "code": "AUTH_INSUFFICIENT_PERMISSIONS",
    "message": "User lacks required permissions",
    "details": {
      "required_scopes": ["write:predictions"],
      "granted_scopes": ["read:predictions"]
    }
  }
}
```
**HTTP Status**: 403
**Cause**: User doesn't have required scopes
**Solution**: Contact administrator for permission upgrade

---

### Validation Errors (VALIDATION_*)

#### VALIDATION_REQUIRED_FIELD
```json
{
  "error": {
    "code": "VALIDATION_REQUIRED_FIELD",
    "message": "Required field missing from request",
    "details": {
      "field": "location.latitude",
      "required_type": "number"
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Required field not provided
**Solution**: Include all required fields in request

#### VALIDATION_INVALID_TYPE
```json
{
  "error": {
    "code": "VALIDATION_INVALID_TYPE",
    "message": "Field has invalid type",
    "details": {
      "field": "risk_score",
      "expected_type": "number",
      "received_type": "string"
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Field value has wrong data type
**Solution**: Ensure field values match expected types

#### VALIDATION_OUT_OF_RANGE
```json
{
  "error": {
    "code": "VALIDATION_OUT_OF_RANGE",
    "message": "Field value outside allowed range",
    "details": {
      "field": "location.latitude",
      "value": 95.0,
      "allowed_range": "[-90, 90]"
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Numeric value outside valid range
**Solution**: Provide value within allowed range

#### VALIDATION_INVALID_DATE_FORMAT
```json
{
  "error": {
    "code": "VALIDATION_INVALID_DATE_FORMAT",
    "message": "Date format is invalid",
    "details": {
      "field": "target_date",
      "value": "15-01-2024",
      "expected_format": "YYYY-MM-DD (ISO 8601)"
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Date not in ISO 8601 format
**Solution**: Use format: `YYYY-MM-DD` (e.g., `2024-01-15`)

---

### Prediction Errors (PREDICTION_*)

#### PREDICTION_SERVICE_UNAVAILABLE
```json
{
  "error": {
    "code": "PREDICTION_SERVICE_UNAVAILABLE",
    "message": "Prediction service is temporarily unavailable"
  }
}
```
**HTTP Status**: 503
**Cause**: ML model service is down or initializing
**Solution**: Retry after a few seconds

#### PREDICTION_MODEL_NOT_FOUND
```json
{
  "error": {
    "code": "PREDICTION_MODEL_NOT_FOUND",
    "message": "Requested ML model not available",
    "details": {
      "requested_model": "custom_model_v3",
      "available_models": ["lstm", "transformer", "ensemble"]
    }
  }
}
```
**HTTP Status**: 404
**Cause**: Requested model doesn't exist
**Solution**: Use one of the available model types

#### PREDICTION_DATA_UNAVAILABLE
```json
{
  "error": {
    "code": "PREDICTION_DATA_UNAVAILABLE",
    "message": "Environmental data not available for specified location and date",
    "details": {
      "location": {"latitude": -1.29, "longitude": 36.82},
      "target_date": "2030-01-15",
      "missing_data": ["ERA5", "CHIRPS"]
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Required environmental data missing
**Solution**: Choose a different location/date or wait for data availability

#### PREDICTION_BATCH_SIZE_EXCEEDED
```json
{
  "error": {
    "code": "PREDICTION_BATCH_SIZE_EXCEEDED",
    "message": "Batch request exceeds maximum allowed size",
    "details": {
      "requested_size": 75,
      "max_allowed": 50
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Too many locations in batch request
**Solution**: Split into multiple requests (max 50 locations each)

---

### Rate Limiting Errors (RATE_LIMIT_*)

#### RATE_LIMIT_EXCEEDED
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "window": "60 seconds",
      "retry_after": 45
    }
  }
}
```
**HTTP Status**: 429
**Headers**: `Retry-After: 45`
**Cause**: Too many requests in time window
**Solution**: Wait `retry_after` seconds before retrying

---

### Resource Errors (RESOURCE_*)

#### RESOURCE_NOT_FOUND
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Requested resource not found",
    "details": {
      "resource_type": "alert",
      "resource_id": "uuid-123"
    }
  }
}
```
**HTTP Status**: 404
**Cause**: Resource with given ID doesn't exist
**Solution**: Verify resource ID or check if resource was deleted

#### RESOURCE_ALREADY_EXISTS
```json
{
  "error": {
    "code": "RESOURCE_ALREADY_EXISTS",
    "message": "Resource with this identifier already exists",
    "details": {
      "resource_type": "subscription",
      "conflicting_field": "fcm_token"
    }
  }
}
```
**HTTP Status**: 409
**Cause**: Attempting to create duplicate resource
**Solution**: Use existing resource or update instead of create

---

### Data Source Errors (DATA_*)

#### DATA_SOURCE_TIMEOUT
```json
{
  "error": {
    "code": "DATA_SOURCE_TIMEOUT",
    "message": "External data source request timed out",
    "details": {
      "source": "ERA5",
      "timeout_seconds": 30
    }
  }
}
```
**HTTP Status**: 504
**Cause**: External API didn't respond in time
**Solution**: Retry request

#### DATA_QUALITY_CHECK_FAILED
```json
{
  "error": {
    "code": "DATA_QUALITY_CHECK_FAILED",
    "message": "Environmental data failed quality validation",
    "details": {
      "source": "CHIRPS",
      "failed_checks": ["completeness", "consistency"]
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Data quality below acceptable threshold
**Solution**: Wait for data quality to improve or use alternative date range

---

### Alert Errors (ALERT_*)

#### ALERT_ALREADY_ACKNOWLEDGED
```json
{
  "error": {
    "code": "ALERT_ALREADY_ACKNOWLEDGED",
    "message": "Alert has already been acknowledged",
    "details": {
      "alert_id": "uuid-123",
      "acknowledged_at": "2024-01-15T12:00:00Z",
      "acknowledged_by": "user@example.com"
    }
  }
}
```
**HTTP Status**: 409
**Cause**: Attempting to acknowledge already-acknowledged alert
**Solution**: No action needed, alert already processed

#### ALERT_WEBSOCKET_CONNECTION_FAILED
```json
{
  "error": {
    "code": "ALERT_WEBSOCKET_CONNECTION_FAILED",
    "message": "Failed to establish WebSocket connection",
    "details": {
      "reason": "Invalid authentication token"
    }
  }
}
```
**HTTP Status**: 401
**Cause**: WebSocket connection rejected
**Solution**: Verify JWT token is valid and included in connection URL

---

### Report Errors (REPORT_*)

#### REPORT_GENERATION_FAILED
```json
{
  "error": {
    "code": "REPORT_GENERATION_FAILED",
    "message": "Report generation encountered an error",
    "details": {
      "report_id": "uuid-123",
      "failure_reason": "Insufficient data for specified date range"
    }
  }
}
```
**HTTP Status**: 500
**Cause**: Report generation process failed
**Solution**: Review report parameters and retry

#### REPORT_FORMAT_NOT_SUPPORTED
```json
{
  "error": {
    "code": "REPORT_FORMAT_NOT_SUPPORTED",
    "message": "Requested report format is not supported",
    "details": {
      "requested_format": "xlsx",
      "supported_formats": ["pdf", "csv"]
    }
  }
}
```
**HTTP Status**: 422
**Cause**: Unsupported export format
**Solution**: Use one of the supported formats

---

### Server Errors (SERVER_*)

#### SERVER_INTERNAL_ERROR
```json
{
  "error": {
    "code": "SERVER_INTERNAL_ERROR",
    "message": "An unexpected server error occurred",
    "details": {
      "request_id": "uuid-for-support"
    }
  }
}
```
**HTTP Status**: 500
**Cause**: Unexpected server-side error
**Solution**: Retry request. If persists, contact support with `request_id`

#### SERVER_DATABASE_ERROR
```json
{
  "error": {
    "code": "SERVER_DATABASE_ERROR",
    "message": "Database operation failed"
  }
}
```
**HTTP Status**: 500
**Cause**: Database connection or query error
**Solution**: Retry request. If persists, contact support

#### SERVER_MAINTENANCE
```json
{
  "error": {
    "code": "SERVER_MAINTENANCE",
    "message": "Service is undergoing maintenance",
    "details": {
      "estimated_completion": "2024-01-15T16:00:00Z"
    }
  }
}
```
**HTTP Status**: 503
**Cause**: Planned maintenance
**Solution**: Wait until maintenance window ends

---

## Error Handling Best Practices

### Client Implementation

```python
def make_api_request(endpoint, data):
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        error_data = e.response.json().get("error", {})
        error_code = error_data.get("code")

        # Handle specific errors
        if error_code == "AUTH_TOKEN_EXPIRED":
            refresh_access_token()
            return make_api_request(endpoint, data)  # Retry

        elif error_code == "RATE_LIMIT_EXCEEDED":
            retry_after = error_data.get("details", {}).get("retry_after", 60)
            time.sleep(retry_after)
            return make_api_request(endpoint, data)  # Retry

        elif error_code == "VALIDATION_REQUIRED_FIELD":
            missing_field = error_data.get("details", {}).get("field")
            raise ValidationError(f"Missing required field: {missing_field}")

        else:
            raise APIError(error_code, error_data.get("message"))

    except requests.exceptions.RequestException as e:
        raise NetworkError(str(e))
```

### Retry Strategy

| Error Code | Retry? | Strategy |
|------------|--------|----------|
| `AUTH_TOKEN_EXPIRED` | Yes | Refresh token, retry once |
| `RATE_LIMIT_EXCEEDED` | Yes | Exponential backoff with `retry_after` |
| `PREDICTION_SERVICE_UNAVAILABLE` | Yes | Exponential backoff (max 3 attempts) |
| `SERVER_INTERNAL_ERROR` | Yes | Exponential backoff (max 3 attempts) |
| `VALIDATION_*` | No | Fix request and retry manually |
| `AUTH_INVALID_CREDENTIALS` | No | Requires user intervention |

### Exponential Backoff Example

```python
def exponential_backoff_retry(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

## Support and Debugging

When reporting errors to support, include:

1. **Request ID**: Found in error response
2. **Timestamp**: When error occurred
3. **Error Code**: Specific error code received
4. **Request Details**: Endpoint, method, parameters (sanitized)
5. **User Context**: User ID, scopes, account type

**Example Support Request**:
```
Error Code: PREDICTION_SERVICE_UNAVAILABLE
Request ID: abc123-def456-ghi789
Timestamp: 2024-01-15T14:30:00Z
Endpoint: POST /v1/predict/single
User: user@example.com
Details: Prediction failed for location (-1.29, 36.82)
```

---

**See Also**:
- [API Overview](./overview.md)
- [Endpoints Reference](./endpoints.md)
- [Authentication](./authentication.md)

**Last Updated**: October 27, 2025
