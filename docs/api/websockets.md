# WebSocket Guide

> **Real-time alert delivery via WebSocket connections**

## Overview

The Malaria Prediction API provides WebSocket connections for real-time alert delivery with sub-100ms latency.

### Features

- ⚡ **Low Latency**: < 100ms message delivery
- 🔄 **Auto-Reconnection**: Automatic reconnection with exponential backoff
- 💾 **Offline Queueing**: Messages queued when disconnected
- 🔒 **Secure**: JWT authentication required
- 📊 **Health Monitoring**: Connection status and diagnostics
- 🎯 **Topic Subscription**: Subscribe to specific alert types and locations

## Connection

### URL Format

```
wss://api.malaria-prediction.example.com/v1/alerts/ws?token=<jwt-token>
```

**Parameters**:
- `token` (required): Your JWT access token

**Note**: Use `wss://` (secure WebSocket) in production

### JavaScript Example

```javascript
const token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...";
const ws = new WebSocket(
  `wss://api.malaria-prediction.example.com/v1/alerts/ws?token=${token}`
);

ws.onopen = (event) => {
  console.log('Connected to alert system');

  // Subscribe to alerts
  ws.send(JSON.stringify({
    action: "subscribe",
    locations: [
      {latitude: -1.2921, longitude: 36.8219, name: "Nairobi"}
    ],
    severities: ["high", "critical"]
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleAlert(message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Disconnected:', event.code, event.reason);
  // Implement reconnection logic
};
```

### Python Example

```python
import asyncio
import websockets
import json

async def connect_alerts(token):
    uri = f"wss://api.malaria-prediction.example.com/v1/alerts/ws?token={token}"

    async with websockets.connect(uri) as websocket:
        print("Connected to alert system")

        # Subscribe
        await websocket.send(json.dumps({
            "action": "subscribe",
            "locations": [
                {"latitude": -1.2921, "longitude": 36.8219}
            ]
        }))

        # Receive alerts
        async for message in websocket:
            alert = json.parse(message)
            handle_alert(alert)

asyncio.run(connect_alerts(access_token))
```

## Message Types

### Server → Client

#### Risk Alert

```json
{
  "type": "risk_alert",
  "alert_id": "uuid-123",
  "severity": "high",
  "location": {
    "latitude": -1.2921,
    "longitude": 36.8219,
    "name": "Nairobi, Kenya"
  },
  "risk_score": 0.82,
  "risk_level": "high",
  "message": "Elevated malaria risk detected in Nairobi",
  "prediction_date": "2024-01-15",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "contributing_factors": {
      "temperature": 0.3,
      "rainfall": 0.4,
      "humidity": 0.3
    },
    "affected_population": 150000
  }
}
```

#### System Message

```json
{
  "type": "system",
  "message": "Prediction model updated to v2.1",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "model_version": "2.1",
    "improvements": "Enhanced accuracy for East Africa region"
  }
}
```

#### Subscription Confirmation

```json
{
  "type": "subscription_confirmed",
  "subscription_id": "uuid-456",
  "locations": [...],
  "severities": ["high", "critical"],
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Heartbeat

```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-15T14:30:00Z",
  "connections": 142
}
```

### Client → Server

#### Subscribe to Alerts

```json
{
  "action": "subscribe",
  "locations": [
    {"latitude": -1.2921, "longitude": 36.8219, "name": "Nairobi"},
    {"latitude": -1.9536, "longitude": 30.0606, "name": "Kigali"}
  ],
  "severities": ["high", "critical"],
  "alert_types": ["risk_alert", "outbreak_detection"]
}
```

**Optional fields**:
- `severities`: Filter by severity (default: all)
- `alert_types`: Filter by type (default: all)

#### Unsubscribe

```json
{
  "action": "unsubscribe",
  "subscription_id": "uuid-456"
}
```

#### Ping (keep-alive)

```json
{
  "action": "ping"
}
```

**Response**:
```json
{
  "type": "pong",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

## Connection Management

### Auto-Reconnection

Implement exponential backoff for reconnections:

```javascript
class AlertWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectDelay = 1000;  // Start at 1 second
    this.maxReconnectDelay = 30000;  // Max 30 seconds
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(
      `wss://api.malaria-prediction.example.com/v1/alerts/ws?token=${this.token}`
    );

    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectDelay = 1000;  // Reset delay on successful connection
      this.resubscribe();
    };

    this.ws.onclose = (event) => {
      console.log('Disconnected:', event.code);

      if (event.code !== 1000) {  // Not a normal closure
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };
  }

  scheduleReconnect() {
    setTimeout(() => {
      console.log(`Reconnecting in ${this.reconnectDelay}ms...`);
      this.connect();

      // Exponential backoff
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
    }, this.reconnectDelay);
  }

  resubscribe() {
    // Restore previous subscriptions
    if (this.currentSubscription) {
      this.ws.send(JSON.stringify(this.currentSubscription));
    }
  }
}
```

### Heartbeat / Keep-Alive

Server sends heartbeat every 30 seconds. Client should respond:

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'heartbeat') {
    ws.send(JSON.stringify({action: 'ping'}));
  } else {
    handleAlert(message);
  }
};
```

### Connection Timeout

Detect stale connections:

```javascript
let lastHeartbeat = Date.now();
const heartbeatInterval = 30000;  // 30 seconds
const timeoutThreshold = 60000;  // 60 seconds

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'heartbeat') {
    lastHeartbeat = Date.now();
  }
};

// Check for timeout
setInterval(() => {
  if (Date.now() - lastHeartbeat > timeoutThreshold) {
    console.warn('Connection timeout detected, reconnecting...');
    ws.close();
    connect();  // Trigger reconnection
  }
}, heartbeatInterval);
```

## Advanced Features

### Message Queue (Offline Support)

Queue messages when disconnected:

```javascript
class QueuedWebSocket {
  constructor(token) {
    this.queue = [];
    this.connected = false;
    // ... connection setup
  }

  send(message) {
    if (this.connected && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.queue.push(message);
    }
  }

  onConnect() {
    this.connected = true;

    // Send queued messages
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### Multi-Location Subscriptions

Subscribe to multiple locations efficiently:

```javascript
const subscriptions = [
  {latitude: -1.2921, longitude: 36.8219, name: "Nairobi"},
  {latitude: -1.9536, longitude: 30.0606, name: "Kigali"},
  {latitude: -6.7924, longitude: 39.2083, name: "Dar es Salaam"}
];

ws.send(JSON.stringify({
  action: "subscribe",
  locations: subscriptions,
  severities: ["high", "critical"]
}));
```

### Alert Filtering

Client-side filtering for specific criteria:

```javascript
function handleAlert(alert) {
  // Filter by custom criteria
  if (alert.type === 'risk_alert' &&
      alert.severity === 'high' &&
      alert.risk_score > 0.8) {

    // Show notification
    showNotification(alert);

    // Update UI
    updateDashboard(alert);

    // Log for analytics
    logAlert(alert);
  }
}
```

## Error Handling

### Connection Errors

| Error | Code | Reason | Solution |
|-------|------|--------|----------|
| Authentication Failed | 4001 | Invalid JWT token | Refresh token and reconnect |
| Forbidden | 4003 | Insufficient permissions | Check scopes |
| Rate Limit | 4029 | Too many connections | Wait before reconnecting |
| Server Error | 1011 | Internal server error | Retry with backoff |

```javascript
ws.onclose = (event) => {
  console.log('Close code:', event.code);

  switch (event.code) {
    case 4001:  // Authentication failed
      refreshToken().then(newToken => {
        this.token = newToken;
        this.connect();
      });
      break;

    case 4029:  // Rate limit
      setTimeout(() => this.connect(), 60000);  // Wait 1 minute
      break;

    case 1011:  // Server error
      this.scheduleReconnect();
      break;

    default:
      if (event.code !== 1000) {  // Not normal closure
        this.scheduleReconnect();
      }
  }
};
```

## Performance Optimization

### Connection Pooling

Reuse connections across application components:

```javascript
class AlertManager {
  static instance = null;

  static getInstance(token) {
    if (!AlertManager.instance) {
      AlertManager.instance = new AlertManager(token);
    }
    return AlertManager.instance;
  }

  constructor(token) {
    this.ws = new AlertWebSocket(token);
    this.listeners = new Map();
  }

  subscribe(id, callback) {
    this.listeners.set(id, callback);
  }

  unsubscribe(id) {
    this.listeners.delete(id);
  }

  broadcast(alert) {
    this.listeners.forEach(callback => callback(alert));
  }
}

// Usage
const alertManager = AlertManager.getInstance(token);
alertManager.subscribe('dashboard', updateDashboard);
alertManager.subscribe('notifications', showNotification);
```

### Message Batching

Batch subscriptions to reduce overhead:

```javascript
let pendingSubscriptions = [];
let batchTimeout = null;

function subscribe(location) {
  pendingSubscriptions.push(location);

  clearTimeout(batchTimeout);
  batchTimeout = setTimeout(() => {
    ws.send(JSON.stringify({
      action: "subscribe",
      locations: pendingSubscriptions
    }));
    pendingSubscriptions = [];
  }, 100);  // Batch within 100ms
}
```

## Testing

### Mock WebSocket Server

```python
import asyncio
import websockets
import json

async def alert_handler(websocket):
    print(f"Client connected")

    try:
        async for message in websocket:
            data = json.loads(message)

            if data.get("action") == "subscribe":
                # Send confirmation
                await websocket.send(json.dumps({
                    "type": "subscription_confirmed",
                    "subscription_id": "test-123"
                }))

                # Send test alert
                await websocket.send(json.dumps({
                    "type": "risk_alert",
                    "severity": "high",
                    "risk_score": 0.85
                }))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    async with websockets.serve(alert_handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Run forever

asyncio.run(main())
```

## Security Considerations

### Token Expiration

JWT tokens expire after 1 hour. Handle token refresh:

```javascript
async function maintainConnection() {
  let ws = new AlertWebSocket(accessToken);

  // Refresh token before expiry
  setInterval(async () => {
    const newToken = await refreshAccessToken();
    ws.close(1000, "Token refresh");  // Normal closure
    ws = new AlertWebSocket(newToken);
  }, 55 * 60 * 1000);  // Refresh every 55 minutes
}
```

### Validate Server Messages

```javascript
function isValidAlert(message) {
  return (
    message.type &&
    message.timestamp &&
    message.alert_id &&
    message.severity &&
    ['low', 'medium', 'high', 'critical'].includes(message.severity)
  );
}

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (isValidAlert(message)) {
    handleAlert(message);
  } else {
    console.warn('Invalid message received:', message);
  }
};
```

## Monitoring

Track WebSocket metrics:

```javascript
const metrics = {
  connectTime: null,
  messagesReceived: 0,
  reconnections: 0,
  averageLatency: 0
};

ws.onopen = () => {
  metrics.connectTime = Date.now();
};

ws.onmessage = (event) => {
  metrics.messagesReceived++;

  const message = JSON.parse(event.data);
  if (message.timestamp) {
    const latency = Date.now() - new Date(message.timestamp).getTime();
    metrics.averageLatency =
      (metrics.averageLatency + latency) / 2;
  }
};
```

---

**See Also**:
- [API Overview](./overview.md)
- [Authentication](./authentication.md)
- [Error Codes](./error-codes.md)

**Last Updated**: October 27, 2025
