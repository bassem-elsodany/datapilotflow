"""
Centralized logging configuration for DataPilotFlow services.

This module provides a unified logging setup that ensures each service writes
to its own log file while maintaining consistent formatting across all services.

Usage:
    from datapilotflow.domain.logging import setup_service_logging
    
    # In your run script, before any other imports that use logger
    setup_service_logging("api")  # Creates logs/api.log
    setup_service_logging("rag-agent")  # Creates logs/rag-agent.log
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_service_logging(
    service_name: str,
    log_dir: Optional[Path] = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "00:00",
    retention: str = "30 days",
    compression: str = "zip",
) -> None:
    """
    Configure loguru logger for a specific service with separate log file.

    This function:
    1. Removes all existing handlers to prevent cross-contamination
    2. Sets up console logging (stderr) with INFO level
    3. Sets up file logging to logs/{service_name}.log with DEBUG level
    4. Applies consistent formatting across all services

    Args:
        service_name: Name of the service (e.g., "api", "rag-agent", "file-upload-event-listener")
                     This will be used as the log filename: logs/{service_name}.log
        log_dir: Optional custom log directory. Defaults to "logs" in current working directory.
        console_level: Log level for console output (stderr). Defaults to "INFO".
        file_level: Log level for file output. Defaults to "DEBUG".
        rotation: When to rotate log files. Defaults to "00:00" (midnight).
        retention: How long to keep old log files. Defaults to "30 days".
        compression: Compression format for old logs. Defaults to "zip".

    Example:
        >>> setup_service_logging("api")
        >>> logger.info("This will go to logs/api.log and stderr")
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)

    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove ALL existing handlers to prevent cross-contamination
    logger.remove()  # Remove all handlers

    # Consistent log format across all services
    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level:<8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # Console logging (stderr) - for real-time monitoring
    logger.add(
        sys.stderr,
        format=log_format,
        level=console_level,
        colorize=True,  # Enable colors in terminal
    )

    # File logging - service-specific log file
    log_file = log_dir / f"{service_name}.log"
    logger.add(
        str(log_file),
        format=log_format,
        level=file_level,
        rotation=rotation,  # Rotate at midnight
        retention=retention,  # Keep logs for 30 days
        compression=compression,  # Compress old logs
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Show full stack traces
        diagnose=True,  # Show variable values in stack traces
    )

    # Log that logging has been configured
    logger.debug(f"Logging configured for service '{service_name}' -> {log_file}")

