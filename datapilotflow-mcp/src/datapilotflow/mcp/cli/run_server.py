"""
CLI entry point to run the DataPilotFlow MCP Server.

Usage:
    datapilotflow-mcp          # Run with default settings
    datapilotflow-mcp --help   # Show help

Environment variables:
    MCP_SERVER_HOST       - Server host (default: 0.0.0.0)
    MCP_SERVER_PORT       - Server port (default: 65510)
    MCP_LOG_LEVEL         - Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    MCP_ENABLED_TOOLS     - Comma-separated list of enabled tools (default: knowledge_expert)
"""

import sys

from loguru import logger

from datapilotflow.mcp.config import settings
from datapilotflow.mcp.server import mcp


def main():
    """Run DataPilotFlow MCP Server."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.MCP_LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )

    logger.info("=" * 70)
    logger.info("🚀 Starting DataPilotFlow MCP Server")
    logger.info("=" * 70)
    logger.info(f"Server: {settings.MCP_SERVER_NAME}")
    logger.info(f"Host: {settings.MCP_SERVER_HOST}")
    logger.info(f"Port: {settings.MCP_SERVER_PORT}")
    logger.info(f"Enabled tools: {settings.MCP_ENABLED_TOOLS}")
    logger.info(f"Log level: {settings.MCP_LOG_LEVEL}")
    logger.info("=" * 70)
    logger.info("")

    try:
        # Run FastMCP server with HTTP transport
        logger.info(f"Listening on http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}")
        mcp.run(transport="http", port=settings.MCP_SERVER_PORT)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
