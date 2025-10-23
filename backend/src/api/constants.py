"""
API Constants

This module contains constants used throughout the API server.
"""

# API Version configuration
# To change API version, simply update this value (e.g., "v2", "v3")
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# API Configuration
API_CONFIG = {
    "version": API_VERSION,
    "prefix": API_PREFIX,
    "title": "DataPilotFlow API",
    "description": "API for DataPilotFlow interview management system",
    "version_info": "1.0.0",
}
