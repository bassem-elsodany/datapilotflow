"""
AI Response Prompts

This module contains prompts used for generating AI responses based on
search results and conversation context.
"""

from .base import Prompt


ai_response_prompt = Prompt(
    name="ai_response",
    prompt="""
Based on the following search results, please answer this question: {query}

Search Results:
{search_results}

INSTRUCTIONS:
1. Answer the question based on the search results provided
2. Reference specific sources when providing information
3. Provide a comprehensive and relevant response
4. If the search results don't contain enough information, acknowledge this and provide what you can
5. Keep the response concise but informative
"""
)

context_aware_ai_response_prompt = Prompt(
    name="context_aware_ai_response",
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
6. Consider the conversation history to provide more contextual and relevant answers
"""
)
