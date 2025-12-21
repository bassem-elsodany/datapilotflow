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

# CRITICAL: Configure service-specific logging BEFORE any other imports
import asyncio

from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("job-event-listener")

from loguru import logger

from datapilotflow.events.events_listeners import start_job_event_listener


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
