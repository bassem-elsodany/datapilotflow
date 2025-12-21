#!/usr/bin/env python3
"""
File Upload Event Listener Runner.

This script starts the file upload event listener service to process file upload events.
"""

# CRITICAL: Configure service-specific logging BEFORE any other imports
import asyncio
import os
import sys

from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("file-upload-event-listener")

from loguru import logger

from datapilotflow.events.events_listeners import start_file_upload_event_listener


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
