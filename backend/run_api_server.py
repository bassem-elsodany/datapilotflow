from loguru import logger
import uvicorn
import signal
import sys
from src.api_server import app
from src.infrastructure.mongo.client import close_mongo_client
from src.config import settings

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
        uvicorn.run("src.api_server:app", host=settings.API_SERVER_HOST, port=settings.API_SERVER_PORT, reload=True)
    except KeyboardInterrupt:
        logger.info("FastAPI server stopped by user.")
        close_mongo_client()
    except Exception as e:
        logger.error(f"FastAPI server crashed: {e}")
        close_mongo_client() 