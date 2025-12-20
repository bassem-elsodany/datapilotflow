"""
DataPilotFlow MCP - Model Context Protocol exposure layer.

Exposes DataPilotFlow agents as MCP servers for use by any MCP client.
Provides a unified MCP server with tools from various agents (RAG, Assistant, etc.).
"""

from datapilotflow.mcp.server import create_mcp_server

__all__ = [
    "create_mcp_server",
]
