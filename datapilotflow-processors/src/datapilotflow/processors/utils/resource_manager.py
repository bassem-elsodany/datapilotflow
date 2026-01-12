"""
Resource Management Utilities for DataPilotFlow

This module provides utilities for managing resources, suppressing warnings,
and ensuring proper cleanup of database connections and other resources.
"""

import warnings
import gc
import atexit
from contextlib import contextmanager
from typing import Optional
from loguru import logger


def suppress_resource_warnings():
    """Suppress common ResourceWarnings that are not critical to application functionality.
    
    This function suppresses warnings from:
    - SQLite connections (from Playwright and other libraries)
    - Python's inspect module
    - asyncio module
    - concurrent.futures module
    - Other common sources of ResourceWarnings
    """
    # Suppress SQLite ResourceWarnings from Playwright and other libraries
    warnings.filterwarnings("ignore", category=ResourceWarning, module="sqlite3")
    warnings.filterwarnings("ignore", category=ResourceWarning, module="inspect")
    warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")
    warnings.filterwarnings("ignore", category=ResourceWarning, module="concurrent.futures")
    
    # Suppress specific ResourceWarning patterns
    warnings.filterwarnings("ignore", message=".*unclosed database.*", category=ResourceWarning)
    warnings.filterwarnings("ignore", message=".*unclosed file.*", category=ResourceWarning)
    warnings.filterwarnings("ignore", message=".*Enable tracemalloc.*", category=ResourceWarning)


@contextmanager
def resource_cleanup_context():
    """Context manager for ensuring proper resource cleanup.
    
    This context manager ensures that:
    - Garbage collection is performed
    - Resource warnings are suppressed
    - Cleanup is performed even if exceptions occur
    
    Usage:
        with resource_cleanup_context():
            # Your code here
            pass
    """
    try:
        # Suppress warnings at the start
        suppress_resource_warnings()
        yield
    finally:
        # Force garbage collection
        gc.collect()
        logger.debug("Resource cleanup completed")


def register_cleanup_handlers():
    """Register cleanup handlers for application shutdown.
    
    This function registers handlers that will be called when the application
    exits, ensuring proper cleanup of resources.
    """
    def cleanup_on_exit():
        """Cleanup function called on application exit."""
        logger.debug("Performing application cleanup...")
        gc.collect()
        logger.debug("Application cleanup completed")
    
    # Register the cleanup function
    atexit.register(cleanup_on_exit)
    logger.debug("Registered cleanup handlers")


# Initialize warning suppression and cleanup handlers
suppress_resource_warnings()
register_cleanup_handlers() 