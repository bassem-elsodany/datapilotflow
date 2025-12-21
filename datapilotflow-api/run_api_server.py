# CRITICAL: Configure service-specific logging BEFORE any other imports
import signal
import sys

# Set up service-specific logging first
from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("api")

import uvicorn
from datapilotflow.infrastructure.mongo.client import close_mongo_client
from loguru import logger

from datapilotflow.api.config import settings
from datapilotflow.api.server import app


def signal_handler(signum, frame):
    """Handle shutdown signals to ensure proper cleanup."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    close_mongo_client()
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting DataPilotFlow FastAPI server...")
    try:
        uvicorn.run(
            "datapilotflow.api.server:app",
            host=settings.API_SERVER_HOST,
            port=settings.API_SERVER_PORT,
            reload=True,
        )
    except KeyboardInterrupt:
        logger.info("FastAPI server stopped by user.")
        close_mongo_client()
    except Exception as e:
        logger.error(f"FastAPI server crashed: {e}")
        close_mongo_client()
