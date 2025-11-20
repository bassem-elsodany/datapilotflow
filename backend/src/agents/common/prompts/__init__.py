"""
Common prompts package for DataPilotFlow agents.

This package contains the base Prompt class and shared prompts used across multiple agents.
Agent-specific prompts are located in their respective agent packages.
"""

from src.agents.common.base_prompt import Prompt

__version__ = "1.0.0"

__all__ = [
    "Prompt",
]
