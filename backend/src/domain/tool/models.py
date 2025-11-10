"""
Tool Domain Models

Standalone tool configurations that can be used across the application.
Tools are user-level entities, not tied to specific conversations.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolType(str, Enum):
    """Types of tools that can be configured."""

    PROMPT_BASED = "prompt_based"  # Tool that uses LLM with a custom system prompt
    MCP_REMOTE = (
        "mcp_remote"  # Tool from MCP server (references server via mcp_server_id)
    )


@dataclass
class PromptBasedToolConfig:
    """Configuration for a prompt-based tool that uses LLM."""

    system_prompt: str  # The system prompt that defines tool behavior
    llm_provider_id: Optional[str] = (
        None  # Optional: specific LLM provider for this tool
    )
    llm_model_name: Optional[str] = None  # Optional: specific model for this tool
    temperature: float = 0.7  # LLM temperature for tool execution
    instructions: Optional[str] = None  # Additional usage instructions


@dataclass
class MCPServerConfig:
    """
    MCP Server connection configuration.

    Represents a single MCP server connection (NO tool list stored here).
    Individual tools reference this server via mcp_server_id foreign key.
    Tool descriptions/schemas are fetched at runtime (not stored statically).
    """

    id: str  # UUID identifier
    user_id: str  # Owner of this server configuration
    name: str  # Human-readable server name (e.g., "My Utilities Server")
    server_url: str  # MCP server endpoint (http://host:port/mcp)
    server_type: str = "http"  # Only HTTP Transport (Streamable) is supported

    # Authentication (shared by all tools on this server)
    auth_type: Optional[str] = None  # "none", "bearer", "basic", "api_key"
    auth_credentials: Optional[Dict[str, str]] = None
    # For bearer: {"token": "your-token"}
    # For basic: {"username": "user", "password": "pass"}
    # For api_key: {"api_key": "your-key", "header_name": "X-API-Key"}

    # Server metadata
    is_active: bool = True
    timeout: int = 30  # Request timeout in seconds
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id or self.id == "":
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class Tool:
    """Represents a standalone tool configuration."""

    id: str  # UUID identifier
    name: str  # Tool name (used by LLM to invoke)
    display_name: str  # Human-readable name for UI
    description: str  # Tool description for LLM understanding
    tool_type: ToolType  # Type of tool (prompt_based or mcp_remote)
    user_id: str  # Owner of the tool
    is_active: bool = True  # Whether this tool is enabled

    # For PROMPT_BASED tools
    prompt_config: Optional[PromptBasedToolConfig] = None

    # For MCP_REMOTE tools (references MCP server + specific tool on that server)
    mcp_server_id: Optional[str] = None  # Foreign key to MCPServerConfig
    mcp_tool_name: Optional[str] = (
        None  # Tool name on the MCP server (e.g., "calculate")
    )

    tags: List[str] = field(default_factory=list)  # Tags for organization and filtering
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id or self.id == "":
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

        # Validation
        if self.tool_type == ToolType.PROMPT_BASED and not self.prompt_config:
            raise ValueError(
                f"Tool '{self.name}': prompt_config required for PROMPT_BASED tools"
            )
        if self.tool_type == ToolType.MCP_REMOTE and not (
            self.mcp_server_id and self.mcp_tool_name
        ):
            raise ValueError(
                f"Tool '{self.name}': mcp_server_id and mcp_tool_name required for MCP_REMOTE tools"
            )
