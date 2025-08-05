#!/bin/bash

# Entrypoint script for Malaria Prediction Backend containers
# Handles initialization, health checks, and service startup

set -euo pipefail

# =============================================================================
# Configuration and Environment Setup
# =============================================================================

# Default values
DEFAULT_API_HOST="${API_HOST:-0.0.0.0}"
DEFAULT_API_PORT="${API_PORT:-8000}"
DEFAULT_WORKERS="${WORKERS:-1}"
DEFAULT_LOG_LEVEL="${LOG_LEVEL:-info}"
DEFAULT_ENVIRONMENT="${ENVIRONMENT:-development}"

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Logging Functions
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "${LOG_LEVEL}" == "debug" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

# Check if a service is available
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts="${4:-30}"
    local attempt=1

    log_info "Waiting for $service_name at $host:$port..."

    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_info "$service_name is available!"
            return 0
        fi

        log_debug "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done

    log_error "$service_name is not available after $max_attempts attempts"
    return 1
}

# Extract connection details from DATABASE_URL
parse_database_url() {
    if [[ -n "${DATABASE_URL:-}" ]]; then
        # Extract components from postgresql+asyncpg://user:pass@host:port/db
        if [[ $DATABASE_URL =~ postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"
            export DB_USER DB_HOST DB_PORT DB_NAME
            log_debug "Parsed database connection: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
        else
            log_warn "Could not parse DATABASE_URL format"
        fi
    fi
}

# Extract connection details from REDIS_URL
parse_redis_url() {
    if [[ -n "${REDIS_URL:-}" ]]; then
        # Extract components from redis://[:password@]host:port[/db]
        if [[ $REDIS_URL =~ redis://(:([^@]+)@)?([^:]+):([^/]+)(/(.+))? ]]; then
            REDIS_HOST="${BASH_REMATCH[3]}"
            REDIS_PORT="${BASH_REMATCH[4]}"
            export REDIS_HOST REDIS_PORT
            log_debug "Parsed Redis connection: $REDIS_HOST:$REDIS_PORT"
        else
            log_warn "Could not parse REDIS_URL format"
        fi
    fi
}

# Initialize directories with proper permissions
init_directories() {
    local dirs=(
        "/app/data"
        "/app/logs"
        "/app/models"
        "/tmp"
    )

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_info "Creating directory: $dir"
            mkdir -p "$dir"
        fi

        # Ensure proper permissions
        if [[ -w "$dir" ]]; then
            log_debug "Directory $dir is writable"
        else
            log_warn "Directory $dir is not writable"
        fi
    done
}

# Run database migrations
run_migrations() {
    if [[ "${ENVIRONMENT}" != "production" ]] && command -v alembic >/dev/null 2>&1; then
        log_info "Running database migrations..."
        if alembic upgrade head; then
            log_info "Database migrations completed successfully"
        else
            log_error "Database migrations failed"
            return 1
        fi
    else
        log_debug "Skipping migrations (production environment or alembic not available)"
    fi
}

# Health check function
health_check() {
    local max_attempts="${1:-10}"
    local attempt=1

    log_info "Performing application health check..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:${DEFAULT_API_PORT}/health/liveness" >/dev/null 2>&1; then
            log_info "Application health check passed!"
            return 0
        fi

        log_debug "Health check attempt $attempt/$max_attempts failed"
        sleep 3
        ((attempt++))
    done

    log_error "Application health check failed after $max_attempts attempts"
    return 1
}

# =============================================================================
# Environment-specific Setup
# =============================================================================

setup_development() {
    log_info "Setting up development environment..."

    # Enable debug mode for development
    export PYTHONPATH="/app/src:${PYTHONPATH:-}"
    export PYTHONDONTWRITEBYTECODE=0

    # Install development dependencies if needed
    if [[ -f "/app/pyproject.toml" ]] && command -v uv >/dev/null 2>&1; then
        log_debug "Development dependencies should already be installed"
    fi
}

setup_production() {
    log_info "Setting up production environment..."

    # Production optimizations
    export PYTHONPATH="/app/src:${PYTHONPATH:-}"
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONUNBUFFERED=1

    # Ensure log directory exists and has proper permissions
    mkdir -p /app/logs

    # Set secure file permissions
    find /app -type f -name "*.py" -exec chmod 644 {} \;
    find /app -type d -exec chmod 755 {} \;
}

# =============================================================================
# Service-specific Startup Functions
# =============================================================================

start_api() {
    log_info "Starting FastAPI application..."

    # Build uvicorn command
    local cmd="uvicorn"
    local args=(
        "main:app"
        "--host" "$DEFAULT_API_HOST"
        "--port" "$DEFAULT_API_PORT"
        "--log-level" "$DEFAULT_LOG_LEVEL"
    )

    # Add environment-specific arguments
    if [[ "$DEFAULT_ENVIRONMENT" == "development" ]]; then
        args+=("--reload" "--reload-dir" "./src")
    else
        args+=("--workers" "$DEFAULT_WORKERS")
    fi

    log_info "Executing: $cmd ${args[*]}"
    exec "$cmd" "${args[@]}"
}

start_worker() {
    log_info "Starting Celery worker..."

    local concurrency="${CELERY_CONCURRENCY:-4}"
    local max_tasks="${CELERY_MAX_TASKS_PER_CHILD:-1000}"

    exec celery -A malaria_predictor.workers.celery worker \
        --loglevel="$DEFAULT_LOG_LEVEL" \
        --concurrency="$concurrency" \
        --max-tasks-per-child="$max_tasks"
}

start_scheduler() {
    log_info "Starting Celery beat scheduler..."

    exec celery -A malaria_predictor.workers.celery beat \
        --loglevel="$DEFAULT_LOG_LEVEL" \
        --schedule=/tmp/celerybeat-schedule
}

start_jupyter() {
    log_info "Starting Jupyter Lab..."

    exec jupyter lab \
        --ip=0.0.0.0 \
        --port=8888 \
        --no-browser \
        --allow-root \
        --NotebookApp.token='' \
        --NotebookApp.password=''
}

# =============================================================================
# Main Initialization
# =============================================================================

main() {
    log_info "Starting Malaria Prediction Backend container..."
    log_info "Environment: $DEFAULT_ENVIRONMENT"
    log_info "Log Level: $DEFAULT_LOG_LEVEL"

    # Parse connection URLs
    parse_database_url
    parse_redis_url

    # Initialize directories
    init_directories

    # Environment-specific setup
    case "$DEFAULT_ENVIRONMENT" in
        "development")
            setup_development
            ;;
        "production")
            setup_production
            ;;
        *)
            log_warn "Unknown environment: $DEFAULT_ENVIRONMENT, using default setup"
            ;;
    esac

    # Wait for dependencies
    if [[ -n "${DB_HOST:-}" ]] && [[ -n "${DB_PORT:-}" ]]; then
        wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL" 30
    fi

    if [[ -n "${REDIS_HOST:-}" ]] && [[ -n "${REDIS_PORT:-}" ]]; then
        wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis" 30
    fi

    # Run migrations (development only)
    if [[ "$DEFAULT_ENVIRONMENT" == "development" ]]; then
        run_migrations || log_warn "Migration failed, continuing..."
    fi

    # Determine service type and start accordingly
    if [[ $# -eq 0 ]]; then
        log_info "No command specified, starting API server"
        start_api
    else
        case "$1" in
            "api"|"uvicorn")
                shift
                start_api "$@"
                ;;
            "worker"|"celery-worker")
                shift
                start_worker "$@"
                ;;
            "scheduler"|"celery-beat")
                shift
                start_scheduler "$@"
                ;;
            "jupyter")
                shift
                start_jupyter "$@"
                ;;
            "bash"|"sh")
                log_info "Starting interactive shell"
                exec /bin/bash
                ;;
            *)
                log_info "Executing custom command: $*"
                exec "$@"
                ;;
        esac
    fi
}

# =============================================================================
# Signal Handlers
# =============================================================================

# Graceful shutdown handler
shutdown_handler() {
    log_info "Received shutdown signal, performing graceful shutdown..."

    # Kill background processes
    jobs -p | xargs -r kill

    # Wait for processes to finish
    wait

    log_info "Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# =============================================================================
# Entry Point
# =============================================================================

# Ensure we're in the right directory
cd /app

# Install netcat for service checks if not available
if ! command -v nc >/dev/null 2>&1; then
    log_debug "Installing netcat for service checks..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq && apt-get install -qq -y netcat-openbsd
    elif command -v apk >/dev/null 2>&1; then
        apk add --no-cache netcat-openbsd
    fi
fi

# Run main function
main "$@"
