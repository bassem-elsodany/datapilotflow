#!/usr/bin/env python3
"""
Notification Event Listener Runner.

This script starts the notification event listener service to process notification events.
"""

# CRITICAL: Configure service-specific logging BEFORE any other imports
import asyncio
import os
import sys

from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("notification-event-listener")

from loguru import logger

from datapilotflow.events.events_listeners import start_notification_event_listener


async def main():
    """Main function to start the notification event listener."""
    try:
        logger.info("Starting notification event listener service...")
        await start_notification_event_listener()
    except KeyboardInterrupt:
        logger.info("Notification event listener service stopped by user")
    except Exception as e:
        logger.error(f"Notification event listener service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
