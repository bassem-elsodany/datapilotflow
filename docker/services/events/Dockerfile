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

# Copy full source. An editable install needs the real source tree present
# at install time — a pyproject.toml-only copy followed by `uv pip install
# -e .` (as this used to do, to get a cacheable dependency layer) silently
# builds a broken/empty editable link, since there's nothing to link to yet.
COPY datapilotflow-domain ./datapilotflow-domain
COPY datapilotflow-infrastructure ./datapilotflow-infrastructure
COPY datapilotflow-services ./datapilotflow-services
COPY datapilotflow-processors ./datapilotflow-processors
COPY datapilotflow-events ./datapilotflow-events

# Copy event listener entry point and service config
COPY datapilotflow-events/run_all_event_listeners.py ./
COPY docker/services/events/.env .env

# A single editable install resolves the full local dependency graph (via
# each package's [tool.uv.sources] path entries) in one pass. Installing
# each sibling editable as a separate `uv pip install -e` command clobbers
# the shared datapilotflow/ namespace between steps — the last package wins
# and the others become unimportable.
WORKDIR /app/datapilotflow-events
RUN uv pip install -e .

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
