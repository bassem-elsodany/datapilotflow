"""
RAG Agent MCP Server Runner.

Starts the RAG agent as an MCP server with HTTP transport that can be consumed by
any MCP client, including LangGraph supervisor agents.

Usage:
    python run_rag_mcp_server.py

The server will be available at:
    http://localhost:65510 (or configured MCP_SERVER_PORT)
"""

import asyncio
import logging
import sys

# CRITICAL: Configure service-specific logging BEFORE any other imports
from datapilotflow.domain.logging import setup_service_logging


class _SuppressHealthCheck(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(_SuppressHealthCheck())

setup_service_logging("rag-agent")

from datapilotflow.domain.config import settings
from loguru import logger

# Import the MCP server
from datapilotflow.rag_agent.mcp.server import mcp

if __name__ == "__main__":
    logger.info("Starting RAG Agent MCP Server (FastMCP - HTTP Streamable)...")
    logger.info("=" * 80)
    logger.info("RAG Agent MCP Server")
    logger.info(f"Server Name: {settings.MCP_SERVER_NAME}")
    logger.info("Transport: Streamable HTTP")
    logger.info("Tool: knowledge_expert")
    logger.info(
        f"MCP Endpoint: http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}/mcp"
    )
    logger.info("=" * 80)

    try:
        # FastMCP 2.14+: run_http_async with streamable-http transport
        asyncio.run(
            mcp.run_http_async(
                transport="streamable-http",
                host=settings.MCP_SERVER_HOST,
                port=settings.MCP_SERVER_PORT,
            )
        )
    except KeyboardInterrupt:
        logger.info("RAG MCP Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"RAG MCP Server crashed: {e}")
        logger.error(f"Traceback: {sys.exc_info()}")
        sys.exit(1)
