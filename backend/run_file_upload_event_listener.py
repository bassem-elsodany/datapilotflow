#!/usr/bin/env python3
"""
File Upload Event Listener Runner.

This script starts the file upload event listener service to process file upload events.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from loguru import logger

from src.services.events_listeners import start_file_upload_event_listener

# Configure logging following main app strategy
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Remove ALL existing handlers to prevent cross-contamination with main app logs
logger.remove()  # Remove all handlers

# Console logging (stderr) - updated format
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    level="INFO",
)

# File logging - same format as console with proper daily rotation
logger.add(
    "logs/file_upload_event_listener.log",
    level="DEBUG",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    compression="zip",  # Compress old logs
)


async def main():
    """Main function to start the file upload event listener."""
    try:
        logger.info("Starting file upload event listener service...")
        await start_file_upload_event_listener()
    except KeyboardInterrupt:
        logger.info("File upload event listener service stopped by user")
    except Exception as e:
        logger.error(f"File upload event listener service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
