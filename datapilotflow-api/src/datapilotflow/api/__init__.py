"""
DataPilotFlow API - REST API exposure layer for UI and integrations.

This package provides a FastAPI-based REST API that exposes:
- Agent capabilities (RAG and Assistant agents)
- Knowledge management (search, upload, management)
- Conversation management
- MCP tool integration
- Real-time streaming via WebSockets
"""

from .app import create_app

__version__ = "1.0.0"

__all__ = ["create_app"]
