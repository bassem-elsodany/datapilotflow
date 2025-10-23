#!/usr/bin/env python3
"""
Notification Listener Service Runner

This script runs the notification listener service that consumes notification events
from RabbitMQ and creates notifications in MongoDB.
"""

import asyncio
import sys
import os
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.notification.notification_listener_service import start_notification_listener


async def main():
    """Main function to start the notification listener service."""
    try:
        logger.info("Starting Notification Listener Service...")
        await start_notification_listener()
    except KeyboardInterrupt:
        logger.info("Notification Listener Service stopped by user")
    except Exception as e:
        logger.error(f"Notification Listener Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
