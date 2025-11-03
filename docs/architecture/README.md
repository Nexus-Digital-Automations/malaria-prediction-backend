# System Architecture Documentation

> **🏗️ Comprehensive architecture overview of the Malaria Prediction System**

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Principles](#architecture-principles)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)

---

## System Overview

The Malaria Prediction System is a production-grade, AI-powered platform that combines environmental data from 80+ sources with advanced machine learning models to predict malaria outbreak risks.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Users                          │
│  Healthcare Professionals │ Researchers │ Public Health Officials│
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Flutter    │  │ Web Portal   │  │ Mobile Apps  │         │
│  │   Frontend   │  │  (Future)    │  │  (iOS/Android)│        │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTPS/WSS
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│  ┌──────────────────────────────────────────────────┐          │
│  │   FastAPI Application (Async ASGI)               │          │
│  │   • Authentication (JWT)                         │          │
│  │   • Rate Limiting                                │          │
│  │   • Request Validation                           │          │
│  │   • API Documentation (OpenAPI)                  │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│  │ Prediction  │  │ Analytics   │  │   Outbreak   │           │
│  │  Service    │  │  Service    │  │   Detection  │           │
│  └─────────────┘  └─────────────┘  └──────────────┘           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│  │   Data      │  │    Risk     │  │   Report     │           │
│  │ Harmonizer  │  │ Calculator  │  │  Generator   │           │
│  └─────────────┘  └─────────────┘  └──────────────┘           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML/AI Layer                                │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐             │
│  │    LSTM    │  │Transformer │  │   Ensemble   │             │
│  │   Model    │  │   Model    │  │    Model     │             │
│  └────────────┘  └────────────┘  └──────────────┘             │
│  ┌──────────────────────────────────────────────┐             │
│  │   Feature Engineering & Model Management     │             │
│  │   • MLflow (Experiment Tracking)             │             │
│  │   • Model Registry & Versioning              │             │
│  └──────────────────────────────────────────────┘             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────┐      │
│  │   TimescaleDB    │  │  PostgreSQL  │  │    Redis    │      │
│  │  (Time-Series)   │  │  (Metadata)  │  │   (Cache)   │      │
│  └──────────────────┘  └──────────────┘  └─────────────┘      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Data Sources                         │
│  ┌─────────┐ ┌─────────┐ ┌───────┐ ┌────────┐ ┌──────────┐   │
│  │  ERA5   │ │ CHIRPS  │ │ MODIS │ │  MAP   │ │ WorldPop │   │
│  │(Climate)│ │ (Rain)  │ │(NDVI) │ │(Malaria)│ │  (Pop)   │   │
│  └─────────┘ └─────────┘ └───────┘ └────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Principles

### 1. **Microservices-Oriented Design**
- Loosely coupled services with clear boundaries
- Independent deployment and scaling
- Service-to-service communication via REST APIs

### 2. **Asynchronous Processing**
- Non-blocking I/O with async/await patterns
- Background task processing with Celery
- Event-driven architecture for data ingestion

### 3. **Data-Centric Architecture**
- Time-series optimized data storage (TimescaleDB)
- Multi-level caching strategy (Redis, CDN)
- Efficient geospatial data handling (PostGIS)

### 4. **Cloud-Native Design**
- Container-first approach (Docker)
- Orchestration-ready (Kubernetes)
- Infrastructure as Code (IaC)

### 5. **Security by Design**
- Defense in depth
- Least privilege access
- End-to-end encryption
- Comprehensive audit logging

### 6. **Observability First**
- Metrics collection (Prometheus)
- Distributed tracing
- Structured logging
- Real-time monitoring dashboards (Grafana)

---

## Component Architecture

### API Gateway (FastAPI)

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                   Middleware Stack                      │
│  ┌────────────────────────────────────────────────┐    │
│  │ CORS Middleware                                │    │
│  │ Security Headers (HSTS, CSP, X-Frame-Options) │    │
│  │ Request ID Injection                           │    │
│  │ Compression (gzip)                             │    │
│  │ Rate Limiting (per user/IP)                    │    │
│  │ Authentication & Authorization (JWT)           │    │
│  │ Logging & Metrics Collection                   │    │
│  └────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                   API Routers                           │
│  /auth          - Authentication endpoints              │
│  /predict       - ML prediction endpoints               │
│  /analytics     - Analytics & reporting                 │
│  /data          - Data ingestion & validation           │
│  /health        - Health checks & metrics               │
│  /operations    - Operations dashboard                  │
│  /ws            - WebSocket real-time alerts            │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**
- Async request handling for high concurrency
- Automatic OpenAPI documentation generation
- Request/response validation with Pydantic
- Dependency injection for service composition

### ML Pipeline

```
┌────────────────────────────────────────────────────────────┐
│                    ML Pipeline Architecture                │
├────────────────────────────────────────────────────────────┤
│  Data Ingestion → Feature Engineering → Model Training    │
│       ↓                   ↓                    ↓           │
│  ┌──────────┐      ┌──────────┐      ┌──────────────┐    │
│  │ Raw Data │  →   │ Features │  →   │   Trained    │    │
│  │  Store   │      │   Store  │      │    Models    │    │
│  └──────────┘      └──────────┘      └──────────────┘    │
│       ↓                   ↓                    ↓           │
│  Validation        Normalization      Model Registry      │
│       ↓                   ↓                    ↓           │
│  Quality Checks    Temporal Align     Versioning          │
└────────────────────────────────────────────────────────────┘

                    Prediction Pipeline
┌────────────────────────────────────────────────────────────┐
│  Request → Feature Extraction → Model Inference → Response │
│             ↓                         ↓                     │
│       [Cache Check]            [Ensemble Voting]           │
│             ↓                         ↓                     │
│       [Historical Data]        [Uncertainty Quantification]│
└────────────────────────────────────────────────────────────┘
```

**Model Components:**
1. **LSTM Model** (`lstm_model.py`)
   - Bidirectional LSTM with attention
   - Sequence length: 90 days
   - Hidden dimensions: 128
   - Dropout: 0.3

2. **Transformer Model** (`transformer_model.py`)
   - Multi-head attention (8 heads)
   - Feed-forward dimension: 512
   - Positional encoding
   - Layer normalization

3. **Ensemble Model** (`ensemble_model.py`)
   - Weighted voting (LSTM + Transformer)
   - Confidence-based weighting
   - Uncertainty estimation

### Data Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              Data Ingestion Pipeline                        │
└─────────────────────────────────────────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
┌─────────┐        ┌─────────┐        ┌─────────┐
│  ERA5   │        │ CHIRPS  │        │  MODIS  │
│ Client  │        │ Client  │        │ Client  │
└─────────┘        └─────────┘        └─────────┘
     │                   │                   │
     └───────────────────┼───────────────────┘
                         ▼
              ┌────────────────────┐
              │ Data Harmonizer    │
              │ • Spatial align    │
              │ • Temporal align   │
              │ • Unit conversion  │
              │ • Quality checks   │
              └────────────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │   TimescaleDB      │
              │   Hypertables      │
              │ • Automatic chunks │
              │ • Compression      │
              │ • Retention policy │
              └────────────────────┘
```

### Database Schema

```sql
-- Environmental data (hypertable for time-series optimization)
CREATE TABLE environmental_data (
    time TIMESTAMPTZ NOT NULL,
    location_id UUID NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    ndvi DOUBLE PRECISION,
    -- ... additional environmental variables
    source VARCHAR(50),
    quality_score DOUBLE PRECISION,
    PRIMARY KEY (location_id, time)
);

SELECT create_hypertable('environmental_data', 'time');

-- Predictions table
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    location_id UUID NOT NULL,
    prediction_date DATE NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION,
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- ... additional metadata
);

-- User management
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Data Flow

### Prediction Request Flow

```
User Request
    │
    ▼
[API Gateway]
    │
    ├──> Authentication (JWT validation)
    ├──> Rate Limiting Check
    ├──> Request Validation (Pydantic)
    │
    ▼
[Prediction Service]
    │
    ├──> Check Redis Cache (cache hit?)
    │    └──> Yes: Return cached result
    │    └──> No: Continue to prediction
    │
    ├──> Fetch Environmental Data (TimescaleDB)
    ├──> Feature Engineering
    │    ├──> Temporal features (rolling averages, trends)
    │    ├──> Spatial features (neighborhood data)
    │    └──> Historical features (seasonal patterns)
    │
    ├──> Model Inference
    │    ├──> LSTM prediction
    │    ├──> Transformer prediction
    │    └──> Ensemble combination
    │
    ├──> Post-processing
    │    ├──> Risk level classification
    │    ├──> Uncertainty quantification
    │    └──> Factor importance calculation
    │
    ├──> Cache Result (Redis, TTL: 1 hour)
    ├──> Store Prediction (PostgreSQL)
    ├──> Emit Metrics (Prometheus)
    │
    ▼
Return Response to User
```

### Data Ingestion Flow

```
Scheduled Task (Cron/Celery Beat)
    │
    ▼
[Data Ingestion Service]
    │
    ├──> ERA5 Data Fetch
    │    ├──> API request with authentication
    │    ├──> Download NetCDF/GRIB files
    │    └──> Parse and extract variables
    │
    ├──> CHIRPS Data Fetch
    │    ├──> Download TIFF files
    │    └──> Extract precipitation data
    │
    ├──> MODIS Data Fetch
    │    ├──> Query NASA Earthdata
    │    └──> Download and process HDF files
    │
    ▼
[Data Harmonization]
    │
    ├──> Spatial Resampling (align to common grid)
    ├──> Temporal Alignment (daily aggregation)
    ├──> Unit Conversion (standardize units)
    ├──> Quality Validation
    │    ├──> Completeness check
    │    ├──> Range validation
    │    └──> Outlier detection
    │
    ▼
[Storage]
    │
    ├──> Insert into TimescaleDB
    ├──> Update data quality metrics
    ├──> Trigger downstream processes
    │    ├──> Model retraining (if needed)
    │    └──> Alert generation (if anomalies)
    │
    ▼
[Monitoring]
    │
    └──> Emit ingestion metrics
         ├──> Records processed
         ├──> Data quality scores
         └──> Processing duration
```

---

## Technology Stack

### Backend Core
- **Runtime**: Python 3.11+
- **Web Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Package Manager**: uv (fast, reliable dependency management)

### Machine Learning
- **ML Framework**: PyTorch 2.0+
- **Training**: PyTorch Lightning
- **Experiment Tracking**: MLflow
- **Model Registry**: MLflow Model Registry
- **Feature Store**: Custom (TimescaleDB-based)

### Data Storage
- **Primary Database**: PostgreSQL 14+
- **Time-Series Extension**: TimescaleDB 2.0+
- **Geospatial Extension**: PostGIS
- **Cache Layer**: Redis 6+
- **Object Storage**: S3-compatible (MinIO/AWS S3)

### Data Processing
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Data Formats**: NetCDF, GRIB2, GeoTIFF, Zarr
- **Geospatial Processing**: GDAL, Rasterio, GeoPandas

### Monitoring & Observability
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: Structured JSON logging
- **Tracing**: OpenTelemetry (planned)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **IaC**: Docker Compose, Kubernetes manifests

### Frontend (Flutter)
- **Framework**: Flutter 3.0+
- **State Management**: BLoC pattern
- **HTTP Client**: Dio
- **WebSockets**: web_socket_channel
- **Mapping**: flutter_map

---

## Deployment Architecture

### Development Environment
```
Docker Compose (Single Host)
┌──────────────────────────────────────┐
│  API Container (FastAPI)             │
│  DB Container (PostgreSQL+TimescaleDB)│
│  Redis Container                     │
│  Prometheus Container                │
│  Grafana Container                   │
└──────────────────────────────────────┘
```

### Production Environment (Kubernetes)
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│              (NGINX Ingress Controller)                 │
└────────────────────────┬────────────────────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
┌───────────┐      ┌───────────┐      ┌───────────┐
│ API Pod 1 │      │ API Pod 2 │      │ API Pod N │
│ (3 replicas minimum for HA)                       │
└───────────┘      └───────────┘      └───────────┘
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ TimescaleDB │  │    Redis     │  │    MLflow    │
│  StatefulSet│  │  StatefulSet │  │  Deployment  │
│ (Persistent)│  │  (Persistent)│  │              │
└─────────────┘  └──────────────┘  └──────────────┘
```

**High Availability Configuration:**
- **API**: 3+ replicas with horizontal pod autoscaling (HPA)
- **Database**: Primary with read replicas
- **Redis**: Redis Sentinel for failover
- **Monitoring**: Dedicated monitoring namespace

---

## Security Architecture

### Authentication & Authorization

```
┌──────────────────────────────────────────────────────┐
│              Authentication Flow                     │
└──────────────────────────────────────────────────────┘
User → Login Request
         ↓
    [Auth Service]
         ├──> Validate credentials (bcrypt password hash)
         ├──> Generate JWT token
         │    ├──> Access token (1 hour expiry)
         │    └──> Refresh token (7 days expiry)
         └──> Return tokens

Subsequent Requests
         ↓
    [JWT Middleware]
         ├──> Extract token from Authorization header
         ├──> Verify signature (HMAC-SHA256)
         ├──> Check expiration
         ├──> Validate claims
         └──> Extract user context
```

### Security Layers

1. **Network Security**
   - TLS 1.3 for all external connections
   - Internal service mesh (mutual TLS)
   - Network policies (Kubernetes)
   - DDoS protection (Cloudflare/AWS Shield)

2. **Application Security**
   - Input validation (Pydantic)
   - SQL injection prevention (SQLAlchemy ORM)
   - XSS protection (Content Security Policy)
   - CSRF protection (SameSite cookies)

3. **Data Security**
   - Encryption at rest (database-level)
   - Encryption in transit (TLS)
   - Sensitive data masking in logs
   - PII data access controls

4. **Access Control**
   - Role-based access control (RBAC)
   - Least privilege principle
   - API key rotation
   - Audit logging for all actions

---

## Scalability & Performance

### Horizontal Scaling Strategy

```
Performance Tier    │ API Pods │ DB Connections │ Redis Memory │ RPS
────────────────────┼──────────┼────────────────┼──────────────┼──────
Development         │    1     │      10        │    256 MB    │  50
Staging             │    2     │      25        │    512 MB    │  200
Production (Small)  │    3     │      50        │    2 GB      │  500
Production (Medium) │    5     │     100        │    4 GB      │ 1000
Production (Large)  │   10+    │     200+       │    8 GB+     │ 2000+
```

### Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│            Multi-Level Caching Architecture             │
└─────────────────────────────────────────────────────────┘

L1: Application Cache (In-Memory)
    ├──> Model weights (cached in RAM)
    ├──> Feature normalization parameters
    └──> TTL: Indefinite (updated on model deployment)

L2: Redis Cache (Distributed)
    ├──> Prediction results (TTL: 1 hour)
    ├──> User sessions (TTL: 24 hours)
    ├──> Rate limiting counters (TTL: 1 minute)
    └──> Environmental data (TTL: 6 hours)

L3: TimescaleDB Cache (Database-level)
    ├──> Query result caching
    └──> Continuous aggregates (pre-computed rollups)

L4: CDN Cache (Edge)
    ├──> Static assets
    └──> API documentation
```

### Performance Optimizations

1. **Database Optimizations**
   - TimescaleDB hypertables for automatic partitioning
   - Continuous aggregates for pre-computed metrics
   - Indexed queries on frequently accessed columns
   - Connection pooling (pgBouncer)

2. **API Optimizations**
   - Async request handling (non-blocking I/O)
   - Response compression (gzip)
   - Batch prediction endpoints
   - Conditional requests (ETags)

3. **ML Model Optimizations**
   - Model quantization (INT8 inference)
   - ONNX runtime for faster inference
   - Batch prediction processing
   - GPU acceleration (when available)

---

## Architecture Decision Records (ADRs)

For detailed architecture decisions and trade-offs, see:
- [ADR Directory](./decisions/) - Architecture Decision Records

---

## References

- [API Documentation](../api/overview.md)
- [ML Model Architecture](../ml/model-architecture.md)
- [Data Sources Overview](../data-sources/overview.md)
- [Deployment Guide](../deployment/DOCKER.md)
- [Security Documentation](../security/)

---

**Last Updated**: November 3, 2025
**Architecture Version**: 2.0.0
