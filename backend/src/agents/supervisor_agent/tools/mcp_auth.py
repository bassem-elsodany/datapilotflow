"""
MCP Authentication Utilities.

Helper functions for building MCP authentication headers for langchain-mcp-adapters.
Supports various authentication types for connecting to MCP servers via HTTP Streamable client.
"""

from typing import Any, Dict, Optional

import httpx


def build_mcp_auth(
    auth_type: Optional[str], auth_credentials: Optional[Dict[str, Any]]
) -> Optional[httpx.Auth | str]:
    """
    Build MCP authentication object from auth type and credentials.

    This is used to construct authentication for langchain-mcp-adapters HTTP Streamable client.

    Args:
        auth_type: Authentication type (none, bearer, basic, api_key)
        auth_credentials: Dictionary containing auth credentials

    Returns:
        httpx.Auth instance, token string, or None for no authentication

    Supported auth types:
        - bearer: Token string for Authorization: Bearer header
                 Server validates as JWT, static token, or opaque token
        - basic: httpx.BasicAuth with username/password
        - api_key: Custom Auth class with configurable header name
        - none/None: No authentication
    """
    if not auth_type or not auth_credentials:
        return None

    if auth_type == "bearer":
        # Token string - will be added as "Authorization: Bearer {token}" header
        # Server handles validation (JWT, static token, opaque token, etc.)
        token = auth_credentials.get("bearer_token") or auth_credentials.get(
            "token", ""
        )
        # Only return token if it's not empty
        if token and token.strip():
            return token.strip()
        return None

    elif auth_type == "basic":
        # HTTP Basic Authentication
        username = auth_credentials.get("username", "")
        password = auth_credentials.get("password", "")
        # Only return auth if both username and password are non-empty
        if username and username.strip() and password and password.strip():
            return httpx.BasicAuth(username=username.strip(), password=password.strip())
        return None

    elif auth_type == "api_key":
        # Create custom auth for API key with configurable header
        api_key = auth_credentials.get("api_key", "")
        header_name = auth_credentials.get("header_name", "X-API-Key")

        # Only return auth if api_key is non-empty
        if not api_key or not api_key.strip():
            return None

        class APIKeyAuth(httpx.Auth):
            """Custom Auth for API Key authentication with configurable header."""

            def __init__(self, api_key: str, header_name: str):
                self.api_key = api_key
                self.header_name = header_name

            def auth_flow(self, request):
                """Add API key to request headers."""
                request.headers[self.header_name] = self.api_key
                yield request

        return APIKeyAuth(api_key=api_key.strip(), header_name=header_name)

    return None
