"""
Knowledge Base Prompts

This module contains prompts used for knowledge base search and retrieval operations.
"""

from .base import Prompt


knowledge_search_prompt = Prompt(
    name="knowledge_search",
    prompt="""
Based on the following context from the knowledge base, please answer the user's question.

Context:
{context}

User Question: {query}

INSTRUCTIONS:
1. Answer the question based ONLY on the information provided in the context
2. CRITICAL: When referencing information, ALWAYS cite the specific knowledge source URL (e.g., 'According to [source_url]...' or 'As mentioned in [source_url]...')
3. Do NOT use generic terms like 'Result1', 'Result2', etc.
4. If the context doesn't contain enough information to answer the question, please say so
5. Use specific details from the context to support your answer
6. Keep your response concise but comprehensive
7. Synthesize and combine information from all relevant context entries to provide a unified answer.
8. If multiple context entries provide related or overlapping information, consolidate them and avoid repetition.
9. Do not simply list the context entries; instead, write a coherent, human-readable answer that integrates the most useful details.
"""
)

entity_search_prompt = Prompt(
    name="entity_search",
    prompt="""
Based on the following documents that contain the entities {entities}, please provide information about these entities.

Context:
{context}

Please provide a comprehensive summary of what you found about these entities.
"""
)

relationship_search_prompt = Prompt(
    name="relationship_search",
    prompt="""
Based on the following documents that contain relationships {relationships}, please provide information about these relationships.

Context:
{context}

Please provide a comprehensive summary of what you found about these relationships.
"""
)

context_aware_response_prompt = Prompt(
    name="context_aware_response",
    prompt="""
Based on the following search results and conversation context, please answer this question: {query}

Search Results:
{search_results}

Conversation Context:
{conversation_context}

INSTRUCTIONS:
1. Answer the question based on the search results and conversation context
2. Reference specific sources when providing information
3. Maintain conversation flow and context
4. Provide a comprehensive and relevant response
5. If the search results don't contain enough information, acknowledge this and provide what you can
"""
)
