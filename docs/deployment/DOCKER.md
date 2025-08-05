# Docker Deployment Guide

## Malaria Prediction Backend - Container Deployment

This guide provides comprehensive instructions for deploying the Malaria Prediction Backend using Docker containers in both development and production environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Quick Start

### Development Environment

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd malaria-prediction-backend
   cp .env.template .env
   # Edit .env with your configuration
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   ```

### Production Environment

1. **Setup secrets**
   ```bash
   # Create Docker secrets
   echo "your-db-password" | docker secret create db_password -
   echo "your-redis-password" | docker secret create redis_password -
   echo "your-api-secret" | docker secret create api_secret_key -
   ```

2. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Architecture Overview

### Container Services

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   FastAPI App   │    │ Celery Workers  │
│   Port: 80/443  │    │   Port: 8000    │    │  Background     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
         ┌─────────────────┐    ┌─────────────────┐
         │  TimescaleDB    │    │     Redis       │
         │  Port: 5432     │    │   Port: 6379    │
         └─────────────────┘    └─────────────────┘
```

### Multi-Stage Docker Build

- **Base Stage**: System dependencies and Python runtime
- **Builder Stage**: Compile dependencies and create virtual environment
- **Production Stage**: Minimal runtime with compiled dependencies
- **Development Stage**: Additional dev tools and hot reload
- **Testing Stage**: Test dependencies and configuration

## Development Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM available
- 20GB+ disk space

### Environment Configuration

1. **Copy environment template**
   ```bash
   cp .env.development .env
   ```

2. **Key development settings**
   ```env
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=debug
   ENABLE_RELOAD=true
   MOCK_EXTERNAL_APIS=true
   ```

### Service Startup

1. **Standard development stack**
   ```bash
   docker-compose up -d
   ```

2. **With development tools**
   ```bash
   docker-compose --profile dev-tools up -d
   ```

3. **Individual services**
   ```bash
   # Database only
   docker-compose up -d database redis

   # API with hot reload
   docker-compose up api
   ```

### Available Services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI application |
| Docs | http://localhost:8000/docs | Interactive API documentation |
| Adminer | http://localhost:8080 | Database administration |
| Redis UI | http://localhost:8081 | Redis management |
| Jupyter | http://localhost:8888 | Data analysis notebooks |

### Development Workflows

#### Hot Reload Development
```bash
# Start with hot reload enabled
docker-compose up api

# Make changes to src/ files
# API automatically reloads
```

#### Running Tests
```bash
# Run test suite in container
docker-compose run --rm api pytest

# Run with coverage
docker-compose run --rm api pytest --cov=src/malaria_predictor
```

#### Database Operations
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Database shell
docker-compose exec database psql -U malaria_user -d malaria_prediction
```

## Production Deployment

### Prerequisites

- Docker Swarm or Kubernetes cluster
- Load balancer (if not using built-in Nginx)
- SSL certificates
- Monitoring infrastructure

### Security Setup

1. **Create Docker secrets**
   ```bash
   # Database password
   openssl rand -base64 32 | docker secret create db_password -

   # Redis password
   openssl rand -base64 32 | docker secret create redis_password -

   # API secret key
   openssl rand -base64 64 | docker secret create api_secret_key -

   # External API keys
   echo "your-era5-key" | docker secret create era5_api_key -
   echo "your-modis-key" | docker secret create modis_api_key -
   ```

2. **SSL certificates**
   ```bash
   # Copy SSL certificates
   mkdir -p docker/nginx/ssl
   cp your-cert.pem docker/nginx/ssl/
   cp your-key.pem docker/nginx/ssl/
   ```

### Environment Configuration

1. **Production environment**
   ```bash
   cp .env.production .env.prod
   # Edit with production-specific values
   ```

2. **Key production settings**
   ```env
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=info
   WORKERS=4
   ENABLE_HTTPS=true
   ENABLE_RATE_LIMITING=true
   ```

### Deployment Commands

1. **Docker Compose deployment**
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d

   # With monitoring
   docker-compose -f docker-compose.prod.yml --profile monitoring up -d
   ```

2. **Docker Swarm deployment**
   ```bash
   # Initialize swarm
   docker swarm init

   # Deploy stack
   docker stack deploy -c docker-compose.prod.yml malaria-prediction
   ```

### Scaling Services

```bash
# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=5

# Docker Swarm scaling
docker service scale malaria-prediction_api=3
docker service scale malaria-prediction_worker=5
```

## Configuration

### Environment Variables

#### Core Application
- `ENVIRONMENT`: Runtime environment (development/production)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (debug/info/warning/error)
- `API_HOST`: API bind address
- `API_PORT`: API port number
- `WORKERS`: Number of worker processes

#### Database
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Connection pool size
- `DATABASE_SSL_MODE`: SSL mode (disable/prefer/require)

#### Redis
- `REDIS_URL`: Redis connection string
- `REDIS_SSL`: Enable SSL (true/false)

#### External APIs
- `ERA5_API_KEY`: ERA5 Climate Data Service key
- `MODIS_API_KEY`: NASA Earth Data key

### Volume Mounts

#### Development
```yaml
volumes:
  - ./src:/app/src:ro          # Source code (read-only)
  - ./data:/app/data           # Data files
  - ./models:/app/models       # ML models
  - ./logs:/app/logs           # Application logs
```

#### Production
```yaml
volumes:
  - data_volume:/app/data      # Persistent data
  - model_volume:/app/models   # Model storage
  - logs_volume:/app/logs      # Log aggregation
```

### Network Configuration

#### Development Network
- Bridge network with custom subnet
- All services communicate via service names
- Exposed ports for development tools

#### Production Network
- Internal network for service communication
- External network for public access
- Network isolation for security

## Monitoring

### Health Checks

#### Application Health
```bash
# Liveness probe
curl http://localhost:8000/health/liveness

# Readiness probe
curl http://localhost:8000/health/readiness

# Detailed health
curl http://localhost:8000/health/detailed
```

#### Container Health
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs api

# Monitor resource usage
docker stats
```

### Metrics Collection

#### Prometheus Integration
- Metrics endpoint: `/health/metrics`
- Custom application metrics
- System resource metrics
- Database performance metrics

#### Grafana Dashboards
- Application performance dashboard
- Infrastructure monitoring
- ML model performance tracking
- Error rate and latency monitoring

### Log Aggregation

#### Development
```bash
# View logs
docker-compose logs -f api

# Search logs
docker-compose logs api | grep ERROR
```

#### Production
- Fluentd log aggregation
- Centralized log storage
- Log rotation and retention
- Alert integration

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check container logs
docker-compose logs service_name

# Verify configuration
docker-compose config

# Check resource usage
docker system df
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec database pg_isready

# Verify connection string
docker-compose exec api python -c "from src.malaria_predictor.database.session import engine; print(engine.url)"

# Test connectivity
docker-compose exec api nc -zv database 5432
```

#### Memory Issues
```bash
# Check memory usage
docker stats --no-stream

# Increase memory limits
# Edit docker-compose.yml deploy.resources.limits.memory
```

#### SSL/TLS Issues
```bash
# Verify certificates
openssl x509 -in docker/nginx/ssl/cert.pem -text -noout

# Test HTTPS connection
curl -k https://localhost/health
```

### Performance Optimization

#### Container Optimization
- Multi-stage builds for smaller images
- Layer caching optimization
- Resource limits and reservations
- Health check intervals

#### Application Optimization
- Connection pooling
- Request caching
- Response compression
- Background task optimization

### Debugging

#### Development Debugging
```bash
# Interactive shell
docker-compose exec api bash

# Python debugger
docker-compose run --rm -p 5678:5678 api python -m debugpy --listen 0.0.0.0:5678 main.py

# Database shell
docker-compose exec database psql -U malaria_user -d malaria_prediction
```

#### Production Debugging
```bash
# Non-disruptive debugging
docker-compose exec api python -c "import sys; print(sys.path)"

# Performance profiling
docker-compose exec api python -m cProfile -o profile.stats main.py
```

## Security Considerations

### Container Security

#### Image Security
- Non-root user execution
- Minimal base images
- Regular security updates
- Vulnerability scanning

#### Runtime Security
- Read-only root filesystem
- Resource limits
- Network policies
- Secret management

### Application Security

#### Authentication & Authorization
- API key management
- JWT token security
- Rate limiting
- CORS configuration

#### Data Protection
- Encryption at rest
- Encryption in transit
- Secret rotation
- Audit logging

### Network Security

#### Network Isolation
- Internal networks for service communication
- Firewall rules
- VPN access for management
- Load balancer security

#### SSL/TLS Configuration
- Strong cipher suites
- Certificate management
- HSTS headers
- Security headers

## Maintenance

### Updates and Upgrades

#### Application Updates
```bash
# Build new image
docker-compose build

# Rolling update
docker-compose up -d --no-deps api

# Verify update
docker-compose exec api python -c "import src.malaria_predictor; print(src.malaria_predictor.__version__)"
```

#### System Updates
```bash
# Update base images
docker-compose pull

# Rebuild with updates
docker-compose build --pull

# Clean up old images
docker image prune -f
```

### Backup and Recovery

#### Database Backups
```bash
# Create backup
docker-compose exec database pg_dump -U malaria_user malaria_prediction > backup.sql

# Restore backup
docker-compose exec -T database psql -U malaria_user malaria_prediction < backup.sql
```

#### Volume Backups
```bash
# Backup data volume
docker run --rm -v malaria_data_volume:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data

# Restore data volume
docker run --rm -v malaria_data_volume:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /
```

## Best Practices

### Development
- Use volume mounts for hot reload
- Mock external APIs in development
- Use separate test database
- Enable debug logging

### Production
- Use Docker secrets for sensitive data
- Implement health checks
- Set resource limits
- Enable monitoring
- Use SSL/TLS
- Regular security updates
- Automated backups

### Performance
- Optimize Docker images
- Use multi-stage builds
- Implement caching
- Monitor resource usage
- Scale horizontally

---

For additional support, please refer to the main project documentation or open an issue in the project repository.
