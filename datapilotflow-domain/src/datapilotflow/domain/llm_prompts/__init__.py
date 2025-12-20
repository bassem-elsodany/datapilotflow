"""
LLM Prompts Subpackage

This subpackage contains all prompts used throughout the SkillPilot system,
organized by functionality and use case.
"""

from .base import Prompt

from .knowledge_base import (
    knowledge_search_prompt,
    entity_search_prompt,
    relationship_search_prompt,
    context_aware_response_prompt
)
# RAG prompts - module not found, commenting out
# from .rag import (
#     rag_synthesis_prompt,
#     rag_entity_search_prompt,
#     rag_relationship_search_prompt
# )
from .ai_responses import (
    ai_response_prompt,
    context_aware_ai_response_prompt
)
from .conversation import (
    structured_response_prompt,
    no_results_prompt,
    simple_response_prompt,
    context_aware_structured_prompt
)

__all__ = [
    # Base
    "Prompt",
    
    # Knowledge Base
    "knowledge_search_prompt",
    "entity_search_prompt",
    "relationship_search_prompt",
    "context_aware_response_prompt",
    
    # AI Responses
    "ai_response_prompt",
    "context_aware_ai_response_prompt",
    
    # Conversation
    "structured_response_prompt",
    "no_results_prompt",
    "simple_response_prompt",
    "context_aware_structured_prompt"
]
