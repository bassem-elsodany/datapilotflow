"""
Assistant Agent Package.

Integration of LangChain's Deep Agents framework with DataPilotFlow.
Provides battle-tested agent implementation with built-in planning,
file system tools, subagent spawning, and hybrid storage.

Key Features:
- Built-in planning with write_todos tool
- File system tools (read_file, write_file, edit_file, grep, glob)
- Subagent spawning for task delegation
- Hybrid storage: Transient (StateBackend) + Persistent (/memories/ via StoreBackend)
- Long-term memory across conversations via Store
- Middleware for policy enforcement

Architecture:
- Uses LangChain's deepagents library with CompositeBackend
- Integrates with existing DataPilotFlow infrastructure
- StateBackend for ephemeral files (per-thread)
- StoreBackend for persistent files under /memories/ (cross-thread)
- WebSocket streaming support
"""

from datapilotflow.agents.assistant_agent.factory import create_assistant_agent_for_conversation
from datapilotflow.agents.assistant_agent.response_handler import (
    get_assistant_agent_response,
    get_assistant_agent_streaming_response,
    set_checkpointer,
)

__version__ = "1.0.0"

__all__ = [
    # Factory
    "create_assistant_agent_for_conversation",
    # Response handlers
    "get_assistant_agent_response",
    "get_assistant_agent_streaming_response",
    "set_checkpointer",
]
