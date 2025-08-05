#!/bin/bash

# Malaria Prediction Backend Test Execution Script
# Provides comprehensive test execution with different test suites

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
ENVIRONMENT="test"
CLEANUP=true
VERBOSE=false
COVERAGE=true
PARALLEL=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE          Test type: unit, integration, e2e, performance, all (default: all)"
    echo "  -e, --environment ENV    Environment: test, ci (default: test)"
    echo "  -c, --no-cleanup         Skip cleanup after tests"
    echo "  -v, --verbose            Verbose output"
    echo "  --no-coverage            Skip coverage reporting"
    echo "  -p, --parallel           Run tests in parallel where possible"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --type unit --verbose"
    echo "  $0 --type integration --no-cleanup"
    echo "  $0 --type e2e --environment ci"
    echo "  $0 --parallel"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--no-cleanup)
            CLEANUP=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            usage
            exit 1
            ;;
    esac
done

# Validate test type
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|e2e|performance|all)$ ]]; then
    echo -e "${RED}Error: Invalid test type '$TEST_TYPE'${NC}"
    usage
    exit 1
fi

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🧪 Malaria Prediction Backend Test Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo "Test type: $TEST_TYPE"
echo "Environment: $ENVIRONMENT"
echo "Coverage: $COVERAGE"
echo "Parallel: $PARALLEL"
echo "Cleanup: $CLEANUP"
echo ""

# Create necessary directories
mkdir -p test_outputs test_reports logs

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to run command with error handling
run_cmd() {
    local cmd="$1"
    local description="$2"

    log "$description"

    if [[ "$VERBOSE" == "true" ]]; then
        echo "Executing: $cmd"
    fi

    if eval "$cmd"; then
        echo -e "${GREEN}✓ $description completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ $description failed${NC}"
        return 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
}

# Function to wait for service health
wait_for_service() {
    local service_name="$1"
    local health_url="$2"
    local max_attempts=30
    local attempt=1

    log "Waiting for $service_name to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$health_url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is healthy${NC}"
            return 0
        fi

        echo "Attempt $attempt/$max_attempts - waiting for $service_name..."
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}✗ $service_name failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Function to cleanup test environment
cleanup_test_env() {
    if [[ "$CLEANUP" == "true" ]]; then
        log "Cleaning up test environment"

        # Stop and remove test containers
        docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true

        # Clean up test data
        rm -rf test_outputs/* test_reports/* 2>/dev/null || true

        echo -e "${GREEN}✓ Test environment cleaned up${NC}"
    else
        log "Skipping cleanup (test environment preserved for debugging)"
    fi
}

# Function to setup test environment
setup_test_env() {
    log "Setting up test environment"

    check_docker

    # Stop any existing test containers
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true

    # Build and start test services
    run_cmd "docker-compose -f docker-compose.test.yml up -d test-database test-redis mock-api" \
            "Starting test infrastructure services"

    # Wait for services to be healthy
    wait_for_service "PostgreSQL" "http://localhost:5433" || (
        echo -e "${RED}Database health check via direct connection${NC}"
        docker-compose -f docker-compose.test.yml exec test-database pg_isready -U test_user -d test_malaria_prediction
    )

    wait_for_service "Redis" "http://localhost:6380" || (
        echo -e "${RED}Redis health check via direct connection${NC}"
        docker-compose -f docker-compose.test.yml exec test-redis redis-cli ping
    )

    wait_for_service "Mock API" "http://localhost:9000/health"

    echo -e "${GREEN}✓ Test environment setup completed${NC}"
}

# Function to run unit tests
run_unit_tests() {
    log "Running unit tests"

    local pytest_args="tests/ -v --tb=short"

    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args="$pytest_args --cov=src/malaria_predictor --cov-report=html:test_outputs/unit_htmlcov --cov-report=xml:test_outputs/unit_coverage.xml --cov-report=term-missing"
    fi

    pytest_args="$pytest_args --junit-xml=test_reports/unit_junit.xml"

    if [[ "$PARALLEL" == "true" ]]; then
        pytest_args="$pytest_args -n auto"
    fi

    # Exclude integration and e2e tests
    pytest_args="$pytest_args --ignore=tests/integration --ignore=tests/e2e --ignore=tests/performance"

    run_cmd "uv run pytest $pytest_args" "Unit tests execution"
}

# Function to run integration tests
run_integration_tests() {
    log "Running integration tests"

    setup_test_env

    local pytest_args="tests/integration/ -v --tb=short"

    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args="$pytest_args --cov=src/malaria_predictor --cov-report=html:test_outputs/integration_htmlcov --cov-report=xml:test_outputs/integration_coverage.xml --cov-report=term-missing"
    fi

    pytest_args="$pytest_args --junit-xml=test_reports/integration_junit.xml"

    # Set environment variables for integration tests
    export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
    export REDIS_URL="redis://localhost:6380/0"

    run_cmd "uv run pytest $pytest_args" "Integration tests execution"
}

# Function to run e2e tests
run_e2e_tests() {
    log "Running end-to-end tests"

    setup_test_env

    # Start the API service
    run_cmd "docker-compose -f docker-compose.test.yml up -d test-api" \
            "Starting API service for E2E tests"

    wait_for_service "API" "http://localhost:8001/health/liveness"

    local pytest_args="tests/e2e/ -v --tb=short --junit-xml=test_reports/e2e_junit.xml"

    # Set environment variables for e2e tests
    export API_BASE_URL="http://localhost:8001"
    export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
    export REDIS_URL="redis://localhost:6380/0"

    run_cmd "uv run pytest $pytest_args" "End-to-end tests execution"
}

# Function to run performance tests
run_performance_tests() {
    log "Running performance tests"

    setup_test_env

    # Start the API service
    run_cmd "docker-compose -f docker-compose.test.yml up -d test-api" \
            "Starting API service for performance tests"

    wait_for_service "API" "http://localhost:8001/health/liveness"

    local pytest_args="tests/performance/ -v --tb=short --junit-xml=test_reports/performance_junit.xml"

    # Set environment variables for performance tests
    export API_BASE_URL="http://localhost:8001"
    export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_malaria_prediction"
    export REDIS_URL="redis://localhost:6380/0"

    run_cmd "uv run pytest $pytest_args" "Performance tests execution"
}

# Function to generate test report
generate_test_report() {
    log "Generating test report"

    local report_file="test_reports/test_summary.html"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Malaria Prediction Backend - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .success { color: green; }
        .failure { color: red; }
        .warning { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Malaria Prediction Backend - Test Report</h1>
        <p><strong>Generated:</strong> $timestamp</p>
        <p><strong>Test Type:</strong> $TEST_TYPE</p>
        <p><strong>Environment:</strong> $ENVIRONMENT</p>
    </div>

    <div class="section">
        <h2>Test Results</h2>
        <table>
            <tr><th>Test Suite</th><th>Status</th><th>Report</th></tr>
EOF

    # Add results for each test type that was run
    if [[ -f "test_reports/unit_junit.xml" ]]; then
        echo "            <tr><td>Unit Tests</td><td class=\"success\">✓ Passed</td><td><a href=\"unit_junit.xml\">JUnit XML</a></td></tr>" >> "$report_file"
    fi

    if [[ -f "test_reports/integration_junit.xml" ]]; then
        echo "            <tr><td>Integration Tests</td><td class=\"success\">✓ Passed</td><td><a href=\"integration_junit.xml\">JUnit XML</a></td></tr>" >> "$report_file"
    fi

    if [[ -f "test_reports/e2e_junit.xml" ]]; then
        echo "            <tr><td>E2E Tests</td><td class=\"success\">✓ Passed</td><td><a href=\"e2e_junit.xml\">JUnit XML</a></td></tr>" >> "$report_file"
    fi

    if [[ -f "test_reports/performance_junit.xml" ]]; then
        echo "            <tr><td>Performance Tests</td><td class=\"success\">✓ Passed</td><td><a href=\"performance_junit.xml\">JUnit XML</a></td></tr>" >> "$report_file"
    fi

    cat >> "$report_file" << EOF
        </table>
    </div>

    <div class="section">
        <h2>Coverage Reports</h2>
        <ul>
EOF

    if [[ -d "test_outputs/unit_htmlcov" ]]; then
        echo "            <li><a href=\"../test_outputs/unit_htmlcov/index.html\">Unit Test Coverage</a></li>" >> "$report_file"
    fi

    if [[ -d "test_outputs/integration_htmlcov" ]]; then
        echo "            <li><a href=\"../test_outputs/integration_htmlcov/index.html\">Integration Test Coverage</a></li>" >> "$report_file"
    fi

    cat >> "$report_file" << EOF
        </ul>
    </div>

    <div class="section">
        <h2>Test Artifacts</h2>
        <ul>
            <li><a href="../logs/">Log files</a></li>
            <li><a href="../test_outputs/">Test outputs</a></li>
        </ul>
    </div>
</body>
</html>
EOF

    echo -e "${GREEN}✓ Test report generated: $report_file${NC}"
}

# Main execution
main() {
    # Trap to ensure cleanup on exit
    trap cleanup_test_env EXIT

    case "$TEST_TYPE" in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "all")
            log "Running complete test suite"
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            run_performance_tests
            ;;
    esac

    generate_test_report

    echo ""
    echo -e "${GREEN}🎉 Test execution completed successfully!${NC}"
    echo -e "${BLUE}📊 Test reports available in: test_reports/${NC}"
    echo -e "${BLUE}📈 Coverage reports available in: test_outputs/${NC}"

    if [[ "$CLEANUP" == "false" ]]; then
        echo -e "${YELLOW}⚠️  Test environment preserved for debugging${NC}"
        echo -e "${YELLOW}   Use 'docker-compose -f docker-compose.test.yml down --volumes' to clean up${NC}"
    fi
}

# Run main function
main "$@"
