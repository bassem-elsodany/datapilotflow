# DataPilotFlow API Server
# Optimized for API server only
FROM python:3.13-slim

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy monorepo structure - only API dependencies
COPY datapilotflow-domain ./datapilotflow-domain
COPY datapilotflow-infrastructure ./datapilotflow-infrastructure
COPY datapilotflow-services ./datapilotflow-services
COPY datapilotflow-api ./datapilotflow-api

# Copy API entry point
COPY datapilotflow-api/run_api_server.py ./

# Copy API service configuration
COPY docker/services/api/.env .env

# Install dependencies using uv
WORKDIR /app/datapilotflow-api
RUN uv pip install -e . && \
    uv pip install -e ../datapilotflow-services && \
    uv pip install -e ../datapilotflow-infrastructure && \
    uv pip install -e ../datapilotflow-domain

WORKDIR /app

# Create necessary directories
RUN mkdir -p logs

# Expose API port
EXPOSE 8800

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8800/health || exit 1

# Run API server
CMD ["uv", "run", "python", "run_api_server.py"]
