"""
MCP Server Configuration.

Configuration settings for the DataPilotFlow MCP server,
loaded from environment variables.
"""

from typing import Optional

from pydantic_settings import BaseSettings


class MCPSettings(BaseSettings):
    """MCP Server Configuration."""

    # Server settings
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 65510
    MCP_SERVER_NAME: str = "datapilotflow"

    # Enabled tools (comma-separated)
    # Example: "knowledge_expert,assistant_task"
    MCP_ENABLED_TOOLS: str = "knowledge_expert"

    # Logging
    MCP_LOG_LEVEL: str = "INFO"

    # Worker configuration for async execution
    MCP_WORKER_THREADS: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = MCPSettings()
