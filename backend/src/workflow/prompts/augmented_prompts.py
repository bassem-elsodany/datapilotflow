"""
Augmented query enhancement prompts.

This strategy generates enhanced query variants while preserving the original query,
ensuring no context is lost while benefiting from query improvements.
"""

from src.workflow.prompts.base_prompt import Prompt

AUGMENTED_SYSTEM_PROMPT = Prompt(
    name="augmented_system_prompt",
    prompt="""You are a query enhancement expert specializing in augmenting user queries for better retrieval.

Your task is to generate 2-3 enhanced variants of the user's query that:
1. Rephrase the query using different terminology
2. Expand on implicit concepts
3. Add relevant context or synonyms
4. Maintain the original intent

The original query will ALWAYS be preserved and used alongside your variants.
Focus on generating complementary perspectives that fill gaps the original query might miss.

Return ONLY a JSON array of enhanced query strings, nothing else.
Example: ["enhanced query 1", "enhanced query 2", "enhanced query 3"]""",
    tags=["query_enhancement", "augmented", "retrieval"],
    metadata={
        "purpose": "Generate enhanced query variants while preserving original query",
        "output_format": "JSON array of strings",
        "strategy": "augmented",
    },
)

AUGMENTED_USER_PROMPT = Prompt(
    name="augmented_user_prompt",
    prompt="""Original query: "{{ query }}"

Generate 2-3 enhanced variants that complement this query. Focus on:
- Alternative terminology and synonyms
- Expanded concepts
- Different phrasings
- Related aspects

Return as JSON array: ["variant 1", "variant 2", "variant 3"]""",
    tags=["query_enhancement", "augmented", "user_input"],
    metadata={
        "input_variables": ["query"],
        "output_format": "JSON array of strings",
    },
)
