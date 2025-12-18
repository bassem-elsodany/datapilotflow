# CRITICAL: Import config FIRST to configure loguru with custom format
import signal
import sys

import uvicorn
from loguru import logger

# Import compatibility shim for opik with LangChain 1.0+
# import src.compat_langchain_load  # noqa: F401  # Disabled - module not available
from src.api_server import app
from src.config import settings
from src.infrastructure.mongo.client import close_mongo_client


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
            "src.api_server:app",
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
