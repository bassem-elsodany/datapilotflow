"""
Workflow chains package for DataPilotFlow.

This package contains all the LangChain Expression Language (LCEL) chains
for the workflow execution, primarily used by query enhancement strategies
for improved Opik traceability.

Each chain follows the pattern: prompt | model
"""

from .answer_generation_chain import get_answer_generation_chain
from .augmented_chain import get_augmented_chain
from .decomposition_chain import get_decomposition_chain
from .hyde_chain import get_hyde_chain
from .judger_chain import get_judger_chain
from .multi_query_chain import get_multi_query_chain

__version__ = "1.0.0"

__all__ = [
    "get_augmented_chain",
    "get_hyde_chain",
    "get_decomposition_chain",
    "get_multi_query_chain",
    "get_judger_chain",
    "get_answer_generation_chain",
]
