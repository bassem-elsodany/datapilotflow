#!/usr/bin/env python3
"""
Notification WebSocket Service Runner

This script runs the notification WebSocket service that manages real-time
WebSocket connections and broadcasts notifications to connected users.
"""

import asyncio
import sys
import os
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.notification.notification_websocket_service import NotificationWebSocketService


async def main():
    """Main function to start the notification WebSocket service."""
    try:
        logger.info("Starting Notification WebSocket Service...")
        
        # Create the WebSocket service instance (singleton)
        websocket_service = NotificationWebSocketService()
        
        logger.info("Notification WebSocket Service initialized successfully")
        logger.info(f"Active connections: {len(websocket_service.active_connections)}")
        logger.info(f"Subscribed users: {len(websocket_service.subscribed_users)}")
        logger.info("Service is ready to handle WebSocket connections and broadcast notifications")
        
        # Keep the service running and monitor connections
        while True:
            await asyncio.sleep(5)
            logger.debug(f"Service status - Active connections: {len(websocket_service.active_connections)}, Subscribed users: {len(websocket_service.subscribed_users)}")
            
    except KeyboardInterrupt:
        logger.info("Notification WebSocket Service stopped by user")
    except Exception as e:
        logger.error(f"Notification WebSocket Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
