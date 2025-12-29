# DataPilotFlow Event Listeners
# Runs all event listener services (Job, FileUpload, Notification)
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

# Copy monorepo structure - event processing dependencies
COPY datapilotflow-domain ./datapilotflow-domain
COPY datapilotflow-infrastructure ./datapilotflow-infrastructure
COPY datapilotflow-services ./datapilotflow-services
COPY datapilotflow-processors ./datapilotflow-processors
COPY datapilotflow-events ./datapilotflow-events

# Copy event listener entry point
COPY datapilotflow-events/run_all_event_listeners.py ./

# Install dependencies using uv
WORKDIR /app/datapilotflow-events
RUN uv pip install -e . && \
    uv pip install -e ../datapilotflow-processors && \
    uv pip install -e ../datapilotflow-services && \
    uv pip install -e ../datapilotflow-infrastructure && \
    uv pip install -e ../datapilotflow-domain

WORKDIR /app

# Create necessary directories
RUN mkdir -p logs

# Note: No port exposed - event listeners only communicate via RabbitMQ
# This is an internal service

# Health check - verify event listener is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ps aux | grep -q "run_all_event_listeners.py" || exit 1

# Run event listeners
CMD ["uv", "run", "python", "run_all_event_listeners.py"]
