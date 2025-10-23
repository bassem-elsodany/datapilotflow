"""
Workflow prompts package for DataPilotFlow.

This package contains all the prompts used in the workflow execution.
"""

from .base_prompt import Prompt
from .rewrite_prompts import REWRITE_SYSTEM_PROMPT, REWRITE_USER_PROMPT
from .judge_prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT
from .generation_prompts import GENERATION_SYSTEM_PROMPT, GENERATION_USER_PROMPT

__version__ = "1.0.0"

__all__ = [
    "Prompt",
    "REWRITE_SYSTEM_PROMPT",
    "REWRITE_USER_PROMPT", 
    "JUDGE_SYSTEM_PROMPT",
    "JUDGE_USER_PROMPT",
    "GENERATION_SYSTEM_PROMPT",
    "GENERATION_USER_PROMPT"
]
