# Rate Limiting Guide

> **Request throttling and usage quotas**

## Overview

The Malaria Prediction API implements rate limiting to ensure fair usage and system stability.

## Rate Limit Tiers

| Tier | Requests/Minute | Requests/Day | Burst Limit |
|------|-----------------|--------------|-------------|
| **Free** | 60 | 5,000 | 10 |
| **Standard** | 100 | 50,000 | 20 |
| **Premium** | 1,000 | 500,000 | 100 |
| **Enterprise** | 10,000 | 5,000,000 | 500 |

**Burst Limit**: Maximum requests in a 10-second window

## Rate Limit Headers

Every API response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640000060
X-RateLimit-Tier: standard
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per minute |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |
| `X-RateLimit-Tier` | Your account tier |

## Rate Limit Exceeded

When rate limit is exceeded:

**Response**: HTTP 429 Too Many Requests

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

**Headers**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000060
```

## Endpoint-Specific Limits

Some endpoints have additional limits:

| Endpoint | Additional Limit | Reason |
|----------|------------------|--------|
| `/predict/batch` | Max 10/minute | Resource intensive |
| `/reports/generate` | Max 5/minute | Long processing time |
| `/analytics/trends` | Max 20/minute | Complex queries |

## Best Practices

### 1. Monitor Rate Limit Headers

```python
def make_request(url, data):
    response = requests.post(url, json=data)

    # Check remaining requests
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))

    if remaining < 10:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_seconds = reset_time - time.time()
        logger.warning(f"Rate limit low. Resets in {wait_seconds}s")

    return response.json()
```

### 2. Implement Exponential Backoff

```python
def api_call_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            retry_after = e.retry_after or (2 ** attempt)
            logger.info(f"Rate limited. Retrying in {retry_after}s")
            time.sleep(retry_after)
```

### 3. Use Batch Endpoints

Instead of:
```python
# ❌ Multiple single requests (uses 50 requests)
for location in locations:
    result = predict_single(location)
```

Do this:
```python
# ✅ Single batch request (uses 1 request)
results = predict_batch(locations)
```

### 4. Cache Results

```python
import functools
from cachetools import TTLCache, cached

# Cache predictions for 1 hour
prediction_cache = TTLCache(maxsize=1000, ttl=3600)

@cached(cache=prediction_cache)
def get_prediction(location, date):
    return api.predict_single(location, date)
```

### 5. Distribute Requests

```python
import time

def distributed_requests(requests_list, requests_per_minute=90):
    interval = 60 / requests_per_minute

    for request in requests_list:
        start = time.time()
        yield make_request(request)

        # Wait to maintain rate
        elapsed = time.time() - start
        if elapsed < interval:
            time.sleep(interval - elapsed)
```

## Rate Limit Strategies

### Client-Side Rate Limiting

Prevent exceeding limits proactively:

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=90, period=60)  # 90 calls per minute (buffer)
def api_call(endpoint, data):
    return requests.post(f"{API_BASE}{endpoint}", json=data)
```

### Request Queue

Queue requests to stay under limits:

```python
from queue import Queue
import threading
import time

class RateLimitedAPI:
    def __init__(self, requests_per_minute=90):
        self.queue = Queue()
        self.rate = requests_per_minute
        self.interval = 60 / self.rate
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def _process_queue(self):
        while True:
            if not self.queue.empty():
                request = self.queue.get()
                self._execute_request(request)
                time.sleep(self.interval)

    def enqueue(self, endpoint, data, callback=None):
        self.queue.put({"endpoint": endpoint, "data": data, "callback": callback})

# Usage
api = RateLimitedAPI(requests_per_minute=90)
api.enqueue("/predict/single", data, callback=process_result)
```

## Upgrading Tier

To increase rate limits:

1. **Contact Sales**: sales@malaria-prediction.example.com
2. **Provide Usage Metrics**: Expected requests/day
3. **Specify Use Case**: Academic, commercial, public health
4. **Review Pricing**: Tier upgrade costs

Enterprise tier includes:
- Custom rate limits
- Dedicated support
- SLA guarantees
- Priority processing

## Monitoring Usage

### Dashboard

View real-time usage at:
```
https://dashboard.malaria-prediction.example.com/usage
```

Metrics:
- Requests per hour/day/month
- Rate limit hits
- Average response time
- Endpoint usage breakdown

### API Endpoint

**GET /v1/account/usage**

```json
{
  "data": {
    "current_tier": "standard",
    "rate_limit": 100,
    "usage": {
      "requests_this_minute": 23,
      "requests_today": 1543,
      "requests_this_month": 45234
    },
    "rate_limit_hits_today": 3
  }
}
```

## Troubleshooting

### Consistent 429 Errors

**Problem**: Frequently hitting rate limits
**Solutions**:
1. Implement request caching
2. Use batch endpoints
3. Distribute requests over time
4. Upgrade tier
5. Check for retry loops

### Unexpected Rate Limit Resets

**Problem**: `X-RateLimit-Reset` shows past time
**Cause**: Server time vs client time mismatch
**Solution**: Use server-provided timestamps, not local time

### Rate Limits on Specific Endpoints

**Problem**: Getting 429 on specific endpoint only
**Cause**: Endpoint has additional limits
**Solution**: Check [endpoint-specific limits](#endpoint-specific-limits)

---

**See Also**:
- [API Overview](./overview.md)
- [Error Codes](./error-codes.md)
- [Authentication](./authentication.md)

**Last Updated**: October 27, 2025
