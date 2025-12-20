"""
FastAPI application factory and configuration.

Creates and configures the main FastAPI application with all routers,
middleware, and dependencies for the DataPilotFlow API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from datapilotflow.domain.config import settings

from .routers import agents, conversations, knowledge, health


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="DataPilotFlow API",
        description="REST API for DataPilotFlow - AI-powered knowledge retrieval and conversation management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])

    logger.info("DataPilotFlow API initialized successfully")

    return app


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return create_app()
