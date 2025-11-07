"""
Common prompts package for DataPilotFlow agents.

This package contains shared prompts used across multiple agents,
including supervisor orchestration prompts.
"""

from src.agents.common.base_prompt import Prompt
from src.agents.common.prompts.supervisor_prompts import (
    MAIN_AGENT_SYSTEM_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
)

__version__ = "1.0.0"

__all__ = [
    "Prompt",
    "SUPERVISOR_SYSTEM_PROMPT",
    "MAIN_AGENT_SYSTEM_PROMPT",
]
