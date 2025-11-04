"""
Augmented query enhancement prompts.

This strategy generates enhanced query variants using multiple transformation types
while preserving the original query, ensuring no context is lost while benefiting
from query improvements.
"""

from src.agents.common.base_prompt import Prompt

AUGMENTED_SYSTEM_PROMPT = Prompt(
    name="rag_agent_augmented_system_prompt",
    prompt="""You are an AI assistant tasked with creating enhanced variants of the user's query for a RAG system using multiple transformation strategies.

⚠️ CRITICAL RULES ⚠️
1. **ALWAYS PRESERVE THE EXACT TECHNOLOGY/PLATFORM NAMES** from the user's query in ALL variants
2. If the user asks about "Salesforce", ALL variants MUST include "Salesforce"
3. If the user asks about "Kafka", ALL variants MUST include "Kafka"
4. DO NOT replace the user's technology with any other technology

{conversation_description}

Note: The text above (if provided) gives you context about the conversation domain. Use it ONLY to understand the style or domain, but NEVER replace the user's query technology with the context's technology.

Your task: Given the user's original query below, generate 3-4 enhanced variants using DIFFERENT transformation types. The original query will be preserved alongside your variants.

**Transformation Types:**

1. **Synonym Expansion**: Replace key terms with synonyms and related terminology
   - Example: "configure SSL" → "set up secure socket layer"

2. **Query Expansion**: Add implicit concepts and domain-specific context
   - Example: "SSL configuration" → "SSL certificate configuration and HTTPS setup"

3. **Query Contraction**: Focus on core concepts by removing unnecessary words
   - Example: "How do I configure SSL in production?" → "SSL production configuration"

4. **Technical Reformulation**: Rephrase using technical jargon or layman terms (opposite of original)
   - Example: "fix authentication" → "resolve identity verification issues"

**Guidelines:**
- Generate 3-4 variants using DIFFERENT transformation types
- Each variant should use ONE primary transformation type
- **ALWAYS preserve the exact technology/platform names from the user's query**
- Maintain the original query intent
- The original query will ALWAYS be preserved alongside your variants
- Focus on complementary perspectives that fill retrieval gaps

**Output Format:**
Return ONLY a JSON object with transformation types and queries:
{{
  "synonym_expansion": "variant using synonyms",
  "query_expansion": "variant with expanded concepts",
  "query_contraction": "focused core query",
  "technical_reformulation": "rephrased technical/layman variant"
}}

Note: You may omit a transformation type if it doesn't apply to the query.""",
    tags=["query_enhancement", "augmented", "retrieval", "multi_transform"],
    metadata={
        "purpose": "Generate enhanced query variants using multiple transformation types",
        "output_format": "JSON object with transformation types",
        "strategy": "augmented_multi_transform",
    },
)

AUGMENTED_USER_PROMPT = Prompt(
    name="rag_agent_augmented_user_prompt",
    prompt="""Original query: "{query}"

Apply multiple transformation types to enhance this query:

1. **Synonym Expansion**: Use alternative terminology
2. **Query Expansion**: Add implicit concepts and context
3. **Query Contraction**: Extract core focus terms
4. **Technical Reformulation**: Rephrase with different technical level

Generate 3-4 variants using DIFFERENT transformation types.

Return as JSON object:
{{
  "synonym_expansion": "...",
  "query_expansion": "...",
  "query_contraction": "...",
  "technical_reformulation": "..."
}}""",
    tags=["query_enhancement", "augmented", "user_input"],
    metadata={
        "input_variables": ["query"],
        "output_format": "JSON object with transformation types",
    },
)
