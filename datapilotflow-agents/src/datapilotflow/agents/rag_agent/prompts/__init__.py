"""
Workflow prompts package for DataPilotFlow.

This package contains all the prompts used in the workflow execution.
"""

from datapilotflow.agents.common.base_prompt import Prompt
from datapilotflow.rag_mcp.rag_agent.prompts.augmented_prompts import (
    AUGMENTED_SYSTEM_PROMPT,
    AUGMENTED_USER_PROMPT,
)
from datapilotflow.rag_mcp.rag_agent.prompts.decomposition_prompts import (
    DECOMPOSITION_SYSTEM_PROMPT,
    DECOMPOSITION_USER_PROMPT,
)
from datapilotflow.rag_mcp.rag_agent.prompts.generation_prompts import (
    GENERATION_SYSTEM_PROMPT,
    GENERATION_USER_PROMPT,
)
from datapilotflow.rag_mcp.rag_agent.prompts.hyde_prompts import (
    HYDE_SYSTEM_PROMPT,
    HYDE_USER_PROMPT,
)
from datapilotflow.rag_mcp.rag_agent.prompts.judge_prompts import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_PROMPT,
)
from datapilotflow.rag_mcp.rag_agent.prompts.multi_query_prompts import (
    MULTI_QUERY_SYSTEM_PROMPT,
    MULTI_QUERY_USER_PROMPT,
)

__version__ = "1.0.0"

__all__ = [
    "Prompt",
    # Core workflow prompts
    "JUDGE_SYSTEM_PROMPT",
    "JUDGE_USER_PROMPT",
    "GENERATION_SYSTEM_PROMPT",
    "GENERATION_USER_PROMPT",
    # Query enhancement strategy prompts
    "AUGMENTED_SYSTEM_PROMPT",
    "AUGMENTED_USER_PROMPT",
    "HYDE_SYSTEM_PROMPT",
    "HYDE_USER_PROMPT",
    "DECOMPOSITION_SYSTEM_PROMPT",
    "DECOMPOSITION_USER_PROMPT",
    "MULTI_QUERY_SYSTEM_PROMPT",
    "MULTI_QUERY_USER_PROMPT",
]
