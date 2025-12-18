"""
RAG Agent MCP Server Runner.

Starts the RAG agent as an MCP server with HTTP transport that can be consumed by
any MCP client, including LangGraph supervisor agents.

Usage:
    python run_rag_mcp_server.py

The server will be available at:
    http://localhost:8001 (or configured RAG_MCP_PORT)
"""

import sys

from loguru import logger

# Import the MCP server
from src.agents.rag_agent.mcp.server import mcp

# Import config first to configure logging
from src.config import settings

if __name__ == "__main__":
    logger.info("Starting RAG Agent MCP Server (FastMCP - HTTP Streamable)...")
    logger.info("=" * 80)
    logger.info("RAG Agent MCP Server")
    logger.info("Server Name: rag-agent")
    logger.info("Transport: HTTP (Streamable)")
    logger.info("Tool: rag_knowledge_retrieval")
    logger.info(
        f"MCP Endpoint: http://{settings.RAG_MCP_HOST}:{settings.RAG_MCP_PORT}/mcp"
    )
    logger.info("Protocol: Streamable HTTP (full bidirectional communication)")
    logger.info("=" * 80)

    try:
        # Run FastMCP server with HTTP transport (Streamable)
        mcp.run(
            transport="http",  # HTTP Transport (Streamable) - recommended for network deployments
            host=settings.RAG_MCP_HOST,
            port=settings.RAG_MCP_PORT,
        )
    except KeyboardInterrupt:
        logger.info("RAG MCP Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"RAG MCP Server crashed: {e}")
        sys.exit(1)
