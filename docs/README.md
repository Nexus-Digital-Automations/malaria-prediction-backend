# Documentation Index

> **Comprehensive documentation for the Malaria Prediction System**

## 🎯 Quick Links

| I want to... | Go to |
|--------------|-------|
| **Make API predictions** | [API Overview](./api/overview.md) → [Endpoints](./api/endpoints.md) |
| **Train ML models** | [ML Architecture](./ml/model-architecture.md) → [Training Guide](./ml/training-guide.md) |
| **Integrate data sources** | [Data Sources Overview](./data-sources/overview.md) |
| **Deploy to production** | [Deployment](./deployment/DOCKER.md) → [ML Deployment](./ml/deployment-workflow.md) |
| **Monitor the system** | [Production Monitoring](./monitoring/PRODUCTION_MONITORING_GUIDE.md) |
| **Run tests** | [Testing Framework](../tests/README.md) |

---

## 📚 Documentation Categories

### 🔌 API Documentation
**Location**: [`docs/api/`](./api/)

Complete REST API reference for malaria predictions.

| Document | Description |
|----------|-------------|
| [API Overview](./api/overview.md) | Architecture, design principles, versioning |
| [Endpoints Reference](./api/endpoints.md) | Complete endpoint catalog with examples |
| [Authentication](./api/authentication.md) | JWT authentication and authorization |
| [Error Codes](./api/error-codes.md) | Comprehensive error reference |
| [Rate Limiting](./api/rate-limiting.md) | Rate limits and best practices |
| [WebSockets](./api/websockets.md) | Real-time alert connections |

**Key Topics**: FastAPI, JWT tokens, WebSocket alerts, rate limiting, error handling

---

### 🤖 Machine Learning Documentation
**Location**: [`docs/ml/`](./ml/)

ML model architecture, training, and deployment.

| Document | Description |
|----------|-------------|
| [Model Architecture](./ml/model-architecture.md) | LSTM, Transformer, Ensemble models |
| [Training Guide](./ml/training-guide.md) | Step-by-step training procedures |
| [Deployment Workflow](./ml/deployment-workflow.md) | Production deployment strategies |
| [Feature Engineering](./ml/feature-engineering.md) | Environmental data features |
| [Model Evaluation](./ml/model-evaluation.md) | Performance metrics and validation |
| [Hyperparameter Tuning](./ml/hyperparameter-tuning.md) | Optimization strategies |

**Key Topics**: PyTorch, LSTM, Transformer, MLflow, model deployment, feature extraction

---

### 🌍 Data Sources Documentation
**Location**: [`docs/data-sources/`](./data-sources/)

Environmental data integration from 80+ sources.

| Document | Description |
|----------|-------------|
| [Data Sources Overview](./data-sources/overview.md) | Data pipeline architecture |
| [ERA5 Integration](./data-sources/era5-integration.md) | Climate data (temperature, humidity) |
| [CHIRPS Integration](./data-sources/chirps-integration.md) | Rainfall data |
| [MODIS Integration](./data-sources/modis-integration.md) | Vegetation indices (NDVI, EVI) |
| [MAP Integration](./data-sources/map-integration.md) | Malaria prevalence data |
| [WorldPop Integration](./data-sources/worldpop-integration.md) | Population density data |
| [Data Quality Validation](./data-sources/data-quality-validation.md) | Automated quality checks |
| [Troubleshooting](./data-sources/troubleshooting.md) | Common issues and solutions |

**Key Topics**: ERA5, CHIRPS, MODIS, TimescaleDB, data harmonization, quality validation

---

### 🚀 Deployment Documentation
**Location**: [`docs/deployment/`](./deployment/)

Production deployment and configuration.

| Document | Description |
|----------|-------------|
| [Docker Deployment](./deployment/DOCKER.md) | Docker containerization guide |
| [Configuration Management](./deployment/CONFIGURATION_MANAGEMENT.md) | Environment configuration |

**See Also**:
- [ML Model Deployment](./ml/deployment-workflow.md)
- [CI/CD Documentation](./cicd/)

---

### 📊 Monitoring & Operations
**Location**: [`docs/monitoring/`](./monitoring/)

Production monitoring and operations.

| Document | Description |
|----------|-------------|
| [Production Monitoring Guide](./monitoring/PRODUCTION_MONITORING_GUIDE.md) | Prometheus, Grafana, alerts |
| [Operations Dashboard Guide](./monitoring/OPERATIONS_DASHBOARD_GUIDE.md) | Dashboard usage and metrics |

---

### 🧪 Testing Documentation
**Location**: [`tests/README.md`](../tests/README.md) and [`docs/testing/`](./testing/)

Comprehensive testing framework.

| Document | Description |
|----------|-------------|
| [Testing Framework](../tests/README.md) | Unit, integration, e2e tests |
| [Testing Standards](./testing/TESTING_FRAMEWORK.md) | Testing best practices |

**Coverage Target**: 95%+ across all modules

---

### ⚙️ CI/CD Documentation
**Location**: [`docs/cicd/`](./cicd/)

Continuous integration and deployment.

| Document | Description |
|----------|-------------|
| [CI/CD Overview](./cicd/README.md) | Pipeline architecture |
| [Implementation Guide](./cicd/IMPLEMENTATION_GUIDE.md) | Setup and configuration |
| [Deployment Runbook](./cicd/runbooks/deployment.md) | Deployment procedures |
| [Database Operations](./cicd/runbooks/database-operations.md) | Database management |
| [Incident Response](./cicd/runbooks/incident-response.md) | Incident handling |
| [Security Incidents](./cicd/runbooks/security-incident.md) | Security protocols |

---

### 🚀 Getting Started
- **[Getting Started Guide](./getting-started/)** - Complete setup and quickstart guide
  - Prerequisites and system requirements
  - Docker quick start (5 minutes)
  - Local development setup
  - First API request walkthrough
  - Running tests

### 🏗️ Architecture & Design
- **[System Architecture](./architecture/)** - Comprehensive architecture documentation
  - High-level system overview
  - Component architecture details
  - Data flow diagrams
  - Technology stack
  - Deployment architecture
  - Security architecture

### 🔒 Security
- **[Security Documentation](./security/)** - Security architecture and compliance
  - Authentication & authorization (JWT, RBAC)
  - Data protection & encryption
  - API security
  - Infrastructure security
  - HIPAA & GDPR compliance
  - Incident response procedures

### 📖 User Guides
- **[User Guides](./user-guides/)** - Practical guides for common tasks
  - Healthcare professional workflows
  - Data scientist guides (training models, feature engineering)
  - System administrator guides (deployment, monitoring)
  - API developer integration examples

### 📱 Frontend Development
- **[Flutter Frontend](./frontend/)** - Flutter application documentation
  - Architecture & project structure
  - BLoC pattern implementation
  - Features (maps, analytics, alerts)
  - API integration
  - Testing guide

### 💻 Code Examples
- **[Code Examples](./examples/)** - Practical code snippets
  - API usage examples (Python, JavaScript, cURL)
  - ML model training examples
  - Data processing examples
  - Integration examples

### 📖 Additional Documentation

#### Pre-Commit Hooks
- [Pre-Commit Guide](./PRE_COMMIT_GUIDE.md) - Setup and usage

#### Map Integration
- [Map Client Usage](./map_client_usage.md) - Flutter map integration
- [MODIS Usage](./modis_usage.md) - MODIS satellite data

#### Project Management
- [Features](../development/essentials/features.md) - Feature catalog (single source of truth)
- [Architecture Overview](../development/essentials/architecture-overview.md) - System architecture
- [Flutter Frontend Architecture](../development/essentials/flutter-frontend-architecture.md) - Flutter app structure

---

## 🎓 Learning Paths

### For New Developers

1. **Start Here**: [Getting Started Guide](./getting-started/)
2. **Understand the Architecture**: [System Architecture](./architecture/)
3. **Setup Development Environment**: [Getting Started - Local Setup](./getting-started/README.md#local-development-setup)
4. **Make Your First API Call**: [Getting Started - First API Request](./getting-started/README.md#first-api-request)
5. **Run Tests**: [Testing Framework](../tests/README.md)
6. **Explore Examples**: [Code Examples](./examples/)

### For Data Scientists

1. **Quick Start**: [Getting Started](./getting-started/)
2. **Model Architecture**: [ML Models](./ml/model-architecture.md)
3. **Data Sources**: [Data Integration](./data-sources/overview.md)
4. **Feature Engineering**: [Features](./ml/feature-engineering.md)
5. **Train Models**: [Training Guide](./ml/training-guide.md) + [User Guide - Model Training](./user-guides/README.md#model-training)
6. **Evaluate Performance**: [Model Evaluation](./ml/model-evaluation.md)
7. **Code Examples**: [ML Examples](./examples/README.md#ml-model-examples)

### For DevOps Engineers

1. **Quick Start**: [Getting Started - Docker](./getting-started/README.md#quick-start-docker)
2. **Architecture**: [System Architecture](./architecture/)
3. **Security**: [Security Documentation](./security/)
4. **Deployment**: [Docker Guide](./deployment/DOCKER.md) + [User Guide - Deployment](./user-guides/README.md#deployment)
5. **CI/CD**: [CI/CD Implementation](./cicd/IMPLEMENTATION_GUIDE.md)
6. **Monitoring**: [Production Monitoring](./monitoring/PRODUCTION_MONITORING_GUIDE.md)
7. **Runbooks**: [Operations Runbooks](./cicd/runbooks/)

### For Frontend Developers

1. **Flutter Setup**: [Frontend Documentation](./frontend/)
2. **Architecture**: [Flutter Architecture](./frontend/README.md#architecture)
3. **API Integration**: [API Endpoints](./api/endpoints.md) + [Frontend API Integration](./frontend/README.md#api-integration)
4. **Authentication**: [JWT Auth](./api/authentication.md)
5. **WebSockets**: [Real-time Alerts](./api/websockets.md)
6. **Map Integration**: [Map Client Usage](./map_client_usage.md)
7. **Code Examples**: [Frontend Examples](./examples/)

---

## 🔍 Search by Topic

### Authentication & Security
- [JWT Authentication](./api/authentication.md)
- [API Security](./api/overview.md#security)
- [Security Incidents](./cicd/runbooks/security-incident.md)

### Data & ML
- [Data Sources](./data-sources/overview.md)
- [ML Models](./ml/model-architecture.md)
- [Feature Engineering](./ml/feature-engineering.md)
- [Model Training](./ml/training-guide.md)

### Deployment & Operations
- [Docker Deployment](./deployment/DOCKER.md)
- [Production Monitoring](./monitoring/PRODUCTION_MONITORING_GUIDE.md)
- [CI/CD Pipeline](./cicd/README.md)
- [Incident Response](./cicd/runbooks/incident-response.md)

### API & Integration
- [API Endpoints](./api/endpoints.md)
- [WebSockets](./api/websockets.md)
- [Error Handling](./api/error-codes.md)
- [Rate Limiting](./api/rate-limiting.md)

---

## 📞 Support & Contributing

### Getting Help
- **Documentation Issues**: Create issue on GitHub
- **API Questions**: See [API Documentation](./api/)
- **ML Questions**: See [ML Documentation](./ml/)

### Contributing
- See [CONTRIBUTING.md](../CONTRIBUTING.md) *(coming soon)*
- Follow [Pre-Commit Guide](./PRE_COMMIT_GUIDE.md)
- Read [Testing Framework](../tests/README.md)

---

## 📊 Documentation Statistics

- **Total Documentation Files**: 40+ markdown files
- **API Documentation**: 6 comprehensive guides
- **ML Documentation**: 6 detailed guides
- **Data Sources**: 8 integration guides
- **Deployment & Operations**: 15+ runbooks and guides
- **Code Coverage**: 95%+ target

---

---

## 📊 Documentation Statistics

- **Total Documentation Files**: 50+ markdown files
- **Getting Started**: Complete quickstart guide
- **Architecture**: Comprehensive system design documentation
- **Security**: Full security & compliance guide
- **User Guides**: Practical guides for all user types
- **API Documentation**: 6 comprehensive guides
- **ML Documentation**: 6 detailed guides
- **Data Sources**: 8 integration guides
- **Frontend**: Complete Flutter application guide
- **Code Examples**: Extensive practical examples
- **Deployment & Operations**: 15+ runbooks and guides
- **Code Coverage**: 95%+ target

---

**Last Updated**: November 3, 2025

**Documentation Version**: 2.0.0
