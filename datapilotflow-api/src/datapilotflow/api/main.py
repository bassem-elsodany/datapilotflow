"""
Main entry point for running the DataPilotFlow API.

Run with:
    uvicorn datapilotflow.api.main:app --host 0.0.0.0 --port 8000
"""

import sys

from loguru import logger

from .app import create_app

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
)

# Create FastAPI app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting DataPilotFlow API server...")
    uvicorn.run(
        "datapilotflow.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
