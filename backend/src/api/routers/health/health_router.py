"""
Health Router

Provides service-wide health endpoints (API and database checks).
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from typing import List, Dict, Any
import os

from src.config import settings


router = APIRouter(prefix="/health", tags=["Health"])


def _read_project_version() -> str:
    """Resolve version from nearest pyproject.toml; fallback to env."""
    try:
        import tomllib  # Python 3.11+
        # Walk up from this file's directory to find pyproject.toml
        current_dir = os.path.dirname(__file__)
        for _ in range(8):  # search up to 8 parent levels
            candidate = os.path.join(current_dir, "pyproject.toml")
            if os.path.exists(candidate):
                with open(candidate, "rb") as f:
                    data = tomllib.load(f)
                    version = data.get("project", {}).get("version")
                    if version:
                        return version
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent
    except Exception:
        pass
    # Fallback to environment variable
    return os.getenv("SKILLPILOT_API_VERSION", "unknown")


def _feature_statuses() -> List[Dict[str, Any]]:
    """Assemble feature list mapped to UI menu features, plus technical components.
    Each feature exposes an 'enabled' boolean (instead of status strings).
    """
    features: List[Dict[str, Any]] = []

    # UI-mapped features (align with dashboard routes)
    features.extend([
        {
            "id": "knowledge-search",
            "name": "knowledge-search",
            "display_name": "Knowledge Search",
            "enabled": True,
            "menu": {"path": "/dashboard/apps/knowledge-search", "wildcard": False}
        },
        {
            "id": "conversation-chat",
            "name": "conversation-chat",
            "display_name": "Conversation Chat",
            "enabled": True,
            "details": {
                "websocket_endpoint": "/api/v1/ws/conversations/{conversation_id}/search",
                "protocol": "WebSocket",
                "authentication": "JWT Token"
            },
            "menu": {"path": "/dashboard/apps/conversation/*", "wildcard": True}
        },
        {
            "id": "knowledge-management",
            "name": "knowledge-management",
            "display_name": "Knowledge Management",
            "enabled": True,
            "menu": {"path": "/dashboard/management/knowledge/*", "wildcard": True}
        },
    ])

    # Note: Technical feature diagnostics intentionally omitted per requirements

    return features


@router.get("")
async def api_health():
    """Service-level health with version and feature statuses."""
    return {
        "service": "skillpilot-api",
        "version": _read_project_version(),
        "status": "healthy",
        "features": _feature_statuses(),
        "websocket_endpoints": {
            "conversation_search": {
                "endpoint": "/api/v1/ws/conversations/{conversation_id}/search",
                "description": "Real-time conversation chat with knowledge search",
                "authentication": "JWT Token via query parameter",
                "protocol": "WebSocket",
                "features": [
                    "Streaming AI responses",
                    "Knowledge base search",
                    "Conversation history management",
                    "Context-aware responses"
                ]
            },
            "notifications": {
                "endpoint": "/api/v1/notifications/ws",
                "description": "Real-time notification updates",
                "authentication": "JWT Token via query parameter",
                "protocol": "WebSocket"
            },
            "interview_websocket": {
                "endpoint": "/api/v1/interviews/ws/start-interview",
                "description": "Real-time interview session management",
                "authentication": "JWT Token via query parameter",
                "protocol": "WebSocket"
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

