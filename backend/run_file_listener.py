#!/usr/bin/env python3
"""
File Upload Event Listener Runner.

This script starts the file upload event listener service to process file upload events.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from loguru import logger
from src.services.events_listeners import start_file_upload_event_listener


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