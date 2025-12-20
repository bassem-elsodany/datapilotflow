FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml .
COPY src ./src

# Install package
RUN pip install --no-cache-dir -e .

# Expose MCP port
EXPOSE 65510

# Run RAG MCP server
CMD ["rag-mcp-server"]
