#!/usr/bin/env python3
"""
Job Event Listener Runner.

This script starts the job event listener service to process job execution events.
"""

# CRITICAL: Set UTF-8 encoding BEFORE any imports
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['LANG'] = 'en_US.UTF-8'

# Force UTF-8 for all I/O
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from loguru import logger

from src.services.events_listeners import start_job_event_listener

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
    "logs/job_event_listener.log",
    level="DEBUG",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    compression="zip",  # Compress old logs
)


async def main():
    """Main function to start the job event listener."""
    try:
        logger.info("=" * 80)
        logger.info("Starting Job Event Listener with NEW REFACTORED ARCHITECTURE")
        logger.info("Using: Orchestrator + Pipeline Pattern + Modular Steps")
        logger.info("=" * 80)
        await start_job_event_listener()
    except KeyboardInterrupt:
        logger.info("Job event listener service stopped by user")
    except Exception as e:
        logger.error(f"Job event listener service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
