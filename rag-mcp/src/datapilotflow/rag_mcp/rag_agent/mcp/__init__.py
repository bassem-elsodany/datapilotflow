"""
RAG Agent MCP Package.

Exposes the RAG agent as an MCP (Model Context Protocol) server.
This allows the RAG agent to be consumed as a standalone service by
any MCP client, including LangGraph supervisor agents.
"""

from src.agents.rag_agent.mcp.server import create_rag_mcp_server
from src.agents.rag_agent.mcp.tools import RAGToolDefinition

__all__ = [
    "create_rag_mcp_server",
    "RAGToolDefinition",
]
