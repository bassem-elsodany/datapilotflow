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

# Create virtual environment
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# ── Layer 1: copy only pyproject.toml files and install deps (cached unless deps change) ──
COPY datapilotflow-domain/pyproject.toml          ./datapilotflow-domain/pyproject.toml
COPY datapilotflow-infrastructure/pyproject.toml  ./datapilotflow-infrastructure/pyproject.toml
COPY datapilotflow-services/pyproject.toml        ./datapilotflow-services/pyproject.toml
COPY datapilotflow-processors/pyproject.toml      ./datapilotflow-processors/pyproject.toml
COPY datapilotflow-events/pyproject.toml          ./datapilotflow-events/pyproject.toml

WORKDIR /app/datapilotflow-events
RUN uv pip install -e . && \
    uv pip install -e ../datapilotflow-processors && \
    uv pip install -e ../datapilotflow-services && \
    uv pip install -e ../datapilotflow-infrastructure && \
    uv pip install -e ../datapilotflow-domain

# ── Layer 2: copy full source (only invalidates above if pyproject.toml changed) ──
WORKDIR /app
COPY datapilotflow-domain ./datapilotflow-domain
COPY datapilotflow-infrastructure ./datapilotflow-infrastructure
COPY datapilotflow-services ./datapilotflow-services
COPY datapilotflow-processors ./datapilotflow-processors
COPY datapilotflow-events ./datapilotflow-events

# Copy event listener entry point and service config
COPY datapilotflow-events/run_all_event_listeners.py ./
COPY docker/services/events/.env .env

# Create necessary directories
RUN mkdir -p logs datapilotflow-events/logs

# Note: No port exposed - event listeners only communicate via RabbitMQ
# This is an internal service

# Health check - verify the main listener process is running
# (ps aux is not available in slim images, use /proc instead)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD grep -ql "run_all_event_listeners" /proc/1/cmdline || exit 1

# Run event listeners from the datapilotflow-events directory so that
# child runner scripts (run_job_event_listener.py etc.) are resolvable as siblings.
# Use the pre-built venv directly (not uv run) so all editable installs are available.
WORKDIR /app/datapilotflow-events
CMD ["/app/.venv/bin/python", "run_all_event_listeners.py"]
