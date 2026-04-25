#!/usr/bin/env python3
"""
All Event Listeners Runner.

This script starts all event listener services concurrently to process various event types.
"""

# CRITICAL: Configure service-specific logging BEFORE any other imports
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("all-event-listeners")

from loguru import logger


class EventListenerManager:
    """Manages multiple event listeners running in separate processes."""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.shutdown_event = asyncio.Event()
        self.shutdown_initiated = False
        self.signal_count = 0
        self.listener_configs = [
            {
                "name": "Job Event Listener",
                "script": "run_job_event_listener.py",
                "log_file": "logs/job_event_listener.log",
            },
            {
                "name": "File Upload Event Listener",
                "script": "run_file_upload_event_listener.py",
                "log_file": "logs/file_upload_event_listener.log",
            },
            {
                "name": "Notification Event Listener",
                "script": "run_notification_event_listener.py",
                "log_file": "logs/notification_event_listener.log",
            },
        ]

    async def start_all_listeners(self):
        """Start all event listeners in separate processes."""
        logger.info("Starting all event listener services in separate processes...")

        # Start each listener in a separate process
        for config in self.listener_configs:
            await self._start_listener_process(config)

        logger.info("All event listeners started successfully")
        logger.debug("Event listeners status:")
        for config in self.listener_configs:
            logger.debug(f"  {config['name']} - running in separate process")
        logger.debug("All listeners are running in separate processes")

        # Start status monitoring task
        status_task = asyncio.create_task(self._monitor_status())

        # Wait for shutdown signal
        await self.shutdown_event.wait()

        # Cancel status monitoring
        status_task.cancel()

        # Terminate all processes with timeout
        logger.info("Shutting down all event listeners...")
        try:
            # Run shutdown in a separate thread with timeout
            import threading
            import time

            shutdown_complete = threading.Event()
            shutdown_thread = threading.Thread(
                target=lambda: (self._shutdown_all_processes(), shutdown_complete.set())
            )
            shutdown_thread.daemon = True
            shutdown_thread.start()

            # Wait for shutdown with timeout
            if shutdown_complete.wait(timeout=10):
                logger.info("All event listeners stopped")
            else:
                logger.error("Shutdown timed out after 10 seconds")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            logger.info("Forcing exit...")

    async def _monitor_status(self):
        """Monitor and log status of all listeners."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                running_count = sum(1 for proc in self.processes if proc.poll() is None)
                logger.debug(
                    f"Status: {running_count}/{len(self.processes)} listeners running"
                )

                # Check for crashed processes and restart them
                for i, proc in enumerate(self.processes):
                    if proc.poll() is not None:
                        config = self.listener_configs[i]
                        logger.warning(f"{config['name']} crashed, restarting...")
                        await self._start_listener_process(config, i)
            except asyncio.CancelledError:
                break

    async def _start_listener_process(self, config: dict, index: int = None):
        """Start a single event listener in a separate process."""
        try:
            logger.debug(f"Starting {config['name']} in separate process...")

            # Resolve the directory containing this script — child runner scripts
            # (run_job_event_listener.py, etc.) are siblings of this file.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, config["script"])

            # Start the process — each listener configures its own loguru file via
            # setup_service_logging(), so stdout/stderr can be suppressed here.
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=script_dir,
            )

            # Store the process
            if index is not None:
                self.processes[index] = proc
            else:
                self.processes.append(proc)

            logger.debug(f"{config['name']} started with PID {proc.pid}")

        except Exception as e:
            logger.error(f"Failed to start {config['name']}: {e}")

    def _shutdown_all_processes(self):
        """Gracefully shutdown all processes."""
        import time

        logger.debug("Starting process shutdown...")

        # First pass: Send SIGTERM to all processes
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:  # Process is still running
                config = self.listener_configs[i]
                logger.debug(
                    f"Sending SIGTERM to {config['name']} (PID {proc.pid})"
                )
                try:
                    proc.terminate()
                except Exception as e:
                    logger.error(f"Error sending SIGTERM to {config['name']}: {e}")

        # Wait briefly for graceful shutdown
        logger.debug("Waiting 3 seconds for graceful shutdown...")
        time.sleep(3)

        # Second pass: Check which processes are still running and force kill
        still_running = []
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:  # Process is still running
                still_running.append((i, proc))

        if still_running:
            logger.warning(
                f"{len(still_running)} processes still running, force killing..."
            )
            for i, proc in still_running:
                config = self.listener_configs[i]
                logger.warning(f"Force killing {config['name']} (PID {proc.pid})")
                try:
                    proc.kill()
                    # Don't wait for the process to die, just kill it
                    logger.debug(f"Sent SIGKILL to {config['name']}")
                except Exception as e:
                    logger.error(f"Error force killing {config['name']}: {e}")
        else:
            logger.debug("All processes terminated gracefully")

        logger.debug("Process shutdown completed")

    def _check_process_health(self):
        """Check the health of all processes."""
        healthy_count = 0
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:  # Process is running
                healthy_count += 1
            else:
                config = self.listener_configs[i]
                logger.warning(
                    f"{config['name']} is not running (exit code: {proc.returncode})"
                )

        return healthy_count

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.signal_count += 1

        if not self.shutdown_initiated:
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_initiated = True
            self.shutdown_event.set()
        else:
            logger.warning(
                f"Received signal {signum} but shutdown already in progress... (signal #{self.signal_count})"
            )

            # Force exit after 3 signals
            if self.signal_count >= 3:
                logger.error(
                    "Force exit after 3 signals - killing all processes immediately"
                )
                import os
                import signal

                for proc in self.processes:
                    if proc.poll() is None:
                        try:
                            os.kill(proc.pid, signal.SIGKILL)
                        except:
                            pass
                os._exit(1)


async def main():
    """Main function to start all event listeners."""
    manager = EventListenerManager()

    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    try:
        # Add timeout to prevent hanging
        await asyncio.wait_for(manager.start_all_listeners(), timeout=None)
    except asyncio.TimeoutError:
        logger.error("Event listener manager timed out")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Event listener manager interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Event listener manager failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
