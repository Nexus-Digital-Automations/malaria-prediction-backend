# Multi-stage Dockerfile for Malaria Prediction Backend
# Optimized for Python ML workloads with geospatial dependencies

# =============================================================================
# Stage 1: Base System Dependencies
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for geospatial and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    gfortran \
    # Geospatial libraries
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    # Scientific computing
    libhdf5-dev \
    libnetcdf-dev \
    libopenblas-dev \
    liblapack-dev \
    # System utilities
    curl \
    wget \
    git \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# =============================================================================
# Stage 2: Python Dependencies Builder
# =============================================================================
FROM base as builder

# Install UV for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# =============================================================================
# Stage 3: Production Runtime
# =============================================================================
FROM base as production

# Create non-root user for security
RUN groupadd -r malaria && \
    useradd -r -g malaria -u 1000 malaria && \
    mkdir -p /app /app/data /app/logs /app/models && \
    chown -R malaria:malaria /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=malaria:malaria /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH"

# Copy application code
WORKDIR /app
COPY --chown=malaria:malaria src/ ./src/
COPY --chown=malaria:malaria main.py ./
COPY --chown=malaria:malaria scripts/ ./scripts/

# Copy entrypoint script
COPY --chown=malaria:malaria docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Create directories for data and models with proper permissions
RUN mkdir -p \
    /app/data/era5 \
    /app/data/chirps \
    /app/data/modis \
    /app/data/worldpop \
    /app/data/map \
    /app/models/lstm \
    /app/models/transformer \
    /app/models/ensemble \
    /app/logs \
    && chown -R malaria:malaria /app

# Switch to non-root user
USER malaria

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Stage 4: Development Environment
# =============================================================================
FROM builder as development

# Install development dependencies
RUN . /opt/venv/bin/activate && \
    uv sync --frozen

# Install additional development tools
RUN . /opt/venv/bin/activate && \
    pip install debugpy ipdb

# Create non-root user for development
RUN groupadd -r developer && \
    useradd -r -g developer -u 1001 developer && \
    mkdir -p /app && \
    chown -R developer:developer /app

# Set PATH and environment for development
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONDONTWRITEBYTECODE=0 \
    ENVIRONMENT=development

WORKDIR /app
USER developer

# Expose ports for app and debugger
EXPOSE 8000 5678

# Development command with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "./src"]

# =============================================================================
# Stage 5: Testing Environment
# =============================================================================
FROM development as testing

# Switch back to root to install test dependencies
USER root

# Copy test files and configuration
COPY --chown=developer:developer tests/ ./tests/
COPY --chown=developer:developer pyproject.toml ./

# Switch back to developer user
USER developer

# Set environment for testing
ENV ENVIRONMENT=testing \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# Default test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src/malaria_predictor", "--cov-report=term-missing", "--cov-report=html"]

# =============================================================================
# Build Arguments and Labels
# =============================================================================

# Build arguments for multi-architecture support
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Metadata labels
LABEL org.opencontainers.image.title="Malaria Prediction Backend" \
      org.opencontainers.image.description="AI-powered malaria outbreak prediction system using LSTM and Transformers" \
      org.opencontainers.image.vendor="Malaria Prediction Team" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/your-org/malaria-predictor" \
      org.opencontainers.image.documentation="https://malaria-predictor.readthedocs.io" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-01-24" \
      malaria.predictor.component="backend-api" \
      malaria.predictor.tier="application"
