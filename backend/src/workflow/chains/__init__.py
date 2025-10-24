"""
Workflow chains package for DataPilotFlow.

This package contains all the LangChain Expression Language (LCEL) chains
for the workflow execution, primarily used by query enhancement strategies
for improved Opik traceability.

Each chain follows the pattern: prompt | model
"""

from .augmented_chain import get_augmented_chain
from .decomposition_chain import get_decomposition_chain
from .hyde_chain import get_hyde_chain
from .multi_query_chain import get_multi_query_chain
from .rag_fusion_chain import get_rag_fusion_chain
from .step_back_chain import get_step_back_chain

__version__ = "1.0.0"

__all__ = [
    "get_augmented_chain",
    "get_step_back_chain",
    "get_hyde_chain",
    "get_decomposition_chain",
    "get_rag_fusion_chain",
    "get_multi_query_chain",
]
