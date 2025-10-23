FROM python:3.11-slim

# Install security updates for system packages
RUN apt-get update && apt-get upgrade -y --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory.
WORKDIR /app

# Install the application dependencies.
COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen --no-cache

# Copy the application into the container.
COPY src/skillpilot skillpilot/
COPY tools tools/

CMD ["/app/.venv/bin/fastapi", "run", "skillpilot/infrastructure/skillpilot_api_server.py", "--port", "8000", "--host", "0.0.0.0"]
