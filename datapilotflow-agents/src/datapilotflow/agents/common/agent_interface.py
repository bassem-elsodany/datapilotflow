"""Base interface for all agents in the multi-agent system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .agent_state import AgentState


class AgentService(ABC):
    """
    Abstract base class for all agents.

    All agents must implement this interface to work with the supervisor.
    Agents are independent, self-contained workers with their own logic.
    """

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent's logic.

        Args:
            state: Current AgentState containing messages and context

        Returns:
            Updated AgentState with agent's results
        """
        pass

    @abstractmethod
    def get_agent_name(self) -> str:
        """Return the agent's display name."""
        pass

    @abstractmethod
    def get_supported_intents(self) -> List[str]:
        """
        Return list of intents this agent can handle.

        Examples:
        - RAG Agent: ["rag_only", "rag_then_task"]
        - Task Agent: ["rag_then_task"]
        - Supervisor: ["routing"]
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return description of what this agent does."""
        pass
