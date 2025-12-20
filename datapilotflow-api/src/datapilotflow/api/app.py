"""
FastAPI application factory and configuration.

Creates and configures the main FastAPI application with all routers,
middleware, and dependencies for the DataPilotFlow API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from datapilotflow.domain.config import settings

from .routers import (
    health, auth, agents, conversations, knowledge,
    model_provider, notifications, tools, users, vectordb
)


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
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(knowledge.router, prefix="/api/v1")
    app.include_router(model_provider.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(vectordb.router, prefix="/api/v1")

    logger.info("DataPilotFlow API initialized successfully")

    return app


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return create_app()
