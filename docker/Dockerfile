# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
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

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY backend/src ./src
COPY backend/run_api_server.py ./
COPY backend/run_file_listener.py ./
COPY backend/run_notification_listener.py ./
COPY backend/run_notification_websocket_service.py ./

# Create necessary directories
RUN mkdir -p upload/inbound upload/archive upload/failed upload/interview logs

# Set permissions
RUN chmod +x run_api_server.py

# Expose the API port
EXPOSE 8800

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8800/health || exit 1

# Default command
CMD ["uv", "run", "python", "run_api_server.py"]
