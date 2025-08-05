# Mock API Service for Testing External API Integrations

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY tests/fixtures/mock-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mock API application
COPY tests/fixtures/mock-api/ .

# Expose ports for different mock services
EXPOSE 9000 9001 9002 9003 9004 9005

# Run the mock API server
CMD ["python", "mock_api_server.py"]
