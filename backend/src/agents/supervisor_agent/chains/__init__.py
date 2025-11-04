"""
Supervisor Agent chains package.

Contains LCEL chains for supervisor orchestration and routing.
"""

from src.agents.supervisor_agent.chains.intent_detection_chain import (
    get_intent_detection_chain,
)

__version__ = "1.0.0"

__all__ = ["get_intent_detection_chain"]
