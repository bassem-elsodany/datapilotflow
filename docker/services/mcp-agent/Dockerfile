# DataPilotFlow RAG Agent MCP Server
# Provides knowledge retrieval via Model Context Protocol
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

# Copy monorepo structure - RAG agent dependencies
COPY datapilotflow-domain ./datapilotflow-domain
COPY datapilotflow-infrastructure ./datapilotflow-infrastructure
COPY datapilotflow-services ./datapilotflow-services
COPY datapilotflow-rag-agent ./datapilotflow-rag-agent

# Copy MCP server entry point
COPY datapilotflow-rag-agent/run_rag_mcp_server.py ./

# Copy RAG agent service configuration
COPY docker/services/mcp-agent/.env .env

# Install dependencies using uv
WORKDIR /app/datapilotflow-rag-agent
RUN uv pip install -e . && \
    uv pip install -e ../datapilotflow-services && \
    uv pip install -e ../datapilotflow-infrastructure && \
    uv pip install -e ../datapilotflow-domain

WORKDIR /app

# Create necessary directories
RUN mkdir -p logs

# Expose MCP server port
EXPOSE 65510

# Health check - verify MCP server is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:65510/ || exit 1

# Run MCP server
CMD ["uv", "run", "python", "run_rag_mcp_server.py"]
