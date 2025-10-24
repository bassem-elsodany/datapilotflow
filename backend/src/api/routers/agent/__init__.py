"""
Agent Router Package

This package contains WebSocket endpoints for AI agent interactions,
including LangGraph workflow execution with query enhancement.
"""

from .agent_websocket_router import router as agent_websocket_router

__all__ = ["agent_websocket_router"]
