"""
DataPilotFlow API Server

This module provides the main FastAPI application for the DataPilotFlow system,
including all routers, middleware, and configuration.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from opik.integrations.langchain import OpikTracer

# CRITICAL: Import config FIRST to configure loguru with custom format
from src.config import settings
from src.infrastructure.opik_utils import configure

if settings.AGENT_TRACING_ENABLED:
    logger.info("Agent tracing is enabled, configuring Opik")
    configure()
else:
    logger.info("Agent tracing is disabled, skipping Opik configuration")

from src.api.constants import API_CONFIG, API_PREFIX
from src.api.routers import (
    auth_router,
    conversation_router,
    document_splitter_router,
    health_router,
    knowledge_collection_router,
    knowledge_job_router,
    knowledge_router,
    knowledge_source_router,
    llm_content_filter_router,
    model_provider_router,
    notification_router,
    notification_websocket_router,
    rag_router,
    supervisor_router,
    tools_router,
    vectordb_collection_router,
)
from src.api.routers.knowledge.knowledge_source_preview_router import (
    router as knowledge_source_preview_router,
)
from src.api.routers.tools import mcp_servers_router

# Job timeline endpoints are now part of the knowledge job router
from src.api.routers.users import roles_router, users_router


async def initialize_system_if_needed():
    """Initialize system (admin user, roles, model providers, and document splitters) if needed."""
    try:
        from src.services.auth import get_admin_initialization_service
        from src.services.model_provider.model_provider_initialization_service import (
            ModelProviderInitializationService,
        )

        # Initialize admin user and roles first
        admin_init_service = get_admin_initialization_service()
        system_success = await admin_init_service.initialize_system_if_needed()

        if not system_success:
            logger.error("System initialization failed")
            return False

        # Get the admin user ID for initialization
        admin_user = admin_init_service.auth_dao.get_user_by_username("admin")
        if not admin_user or not admin_user.id:
            logger.error("Admin user not found for system initialization")
            return False

        # Initialize predefined unified model providers
        model_provider_init_service = ModelProviderInitializationService()
        model_provider_success = (
            await model_provider_init_service.initialize_predefined_model_providers(
                admin_user.id
            )
        )

        if model_provider_success:
            logger.info("System initialization completed successfully!")
            return True
        else:
            logger.warning(
                "System initialized but model provider initialization failed"
            )
            return True  # Still return True as core system is initialized

    except Exception as e:
        logger.error(f"Error during system initialization: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.debug("Starting DataPilotFlow API Server...")

    # Initialize system (admin user and roles) if needed
    await initialize_system_if_needed()

    logger.info("DataPilotFlow API ready and running")
    logger.info("RAG Agent configured for independent stateless query processing")

    yield  # Application is running

    # Handle graceful shutdown
    if settings.AGENT_TRACING_ENABLED:
        logger.info("Flushing Opik tracer...")
        try:
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("Opik tracer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing Opik tracer: {e}")

    # Shutdown
    logger.info("Shutting down DataPilotFlow API Server...")
    logger.debug("DataPilotFlow API Server shutdown complete")


# Create FastAPI app with lifespan management
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version_info"],
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Include routers under API version prefix
app.include_router(auth_router, prefix=API_PREFIX, tags=["Authentication Management"])
app.include_router(rag_router, prefix=API_PREFIX, tags=["RAG WebSocket"])
app.include_router(supervisor_router, prefix=API_PREFIX, tags=["Supervisor WebSocket"])
app.include_router(
    conversation_router, prefix=API_PREFIX, tags=["Conversations Management"]
)
app.include_router(
    tools_router, prefix=f"{API_PREFIX}/tools", tags=["Tools Management"]
)
app.include_router(
    mcp_servers_router,
    prefix=f"{API_PREFIX}/mcp-servers",
    tags=["MCP Servers Management"],
)
app.include_router(
    notification_router, prefix=API_PREFIX, tags=["Notifications Management"]
)
app.include_router(
    notification_websocket_router, prefix=API_PREFIX, tags=["Notifications WebSocket"]
)
app.include_router(knowledge_router, prefix=API_PREFIX, tags=["Knowledge Management"])
app.include_router(
    knowledge_source_router,
    prefix=f"{API_PREFIX}/knowledge/sources",
    tags=["Knowledge Source Configuration"],
)
app.include_router(
    knowledge_source_preview_router,
    prefix=f"{API_PREFIX}/knowledge/sources-preview-content",
    tags=["Knowledge Source Preview Content"],
)
app.include_router(
    knowledge_job_router,
    prefix=f"{API_PREFIX}/knowledge/jobs",
    tags=["Knowledge Job Management"],
)

app.include_router(
    knowledge_collection_router,
    prefix=f"{API_PREFIX}/knowledge/vectordb-collections",
    tags=["Knowledge Vector DB Collection Management"],
)

app.include_router(
    document_splitter_router,
    prefix=f"{API_PREFIX}/knowledge/document-splitters",
    tags=["Document Splitter Management"],
)

# VectorDB Collection Management endpoints
app.include_router(
    vectordb_collection_router,
    prefix=f"{API_PREFIX}/vectordb",
    tags=["Vector DB Collection Management"],
)
app.include_router(
    llm_content_filter_router,
    prefix=f"{API_PREFIX}/knowledge/content-filters",
    tags=["LLM Content Filter Management"],
)
app.include_router(
    model_provider_router,
    prefix=API_PREFIX,
    tags=["Unified Model Providers Management"],
)
app.include_router(users_router, prefix=API_PREFIX, tags=["User Management"])
app.include_router(roles_router, prefix=API_PREFIX, tags=["User Roles Management"])
app.include_router(health_router, prefix=API_PREFIX, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DataPilotFlow API Server",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "datapilotflow-api", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_SERVER_HOST, port=settings.API_SERVER_PORT)
