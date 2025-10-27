"""
Multi-query expansion prompts for DataPilotFlow LangGraph implementation.

These prompts are used to generate alternative phrasings of queries
to improve retrieval coverage and capture different user intents.
"""

from .base_prompt import Prompt

MULTI_QUERY_SYSTEM_PROMPT = Prompt(
    name="multi_query_system_prompt",
    prompt="""You are a query expansion expert for retrieval-augmented generation (RAG) systems.

Your task is to generate alternative phrasings of the user's question to improve document retrieval.
Each alternative should:
1. Express the same core intent as the original question
2. Use different vocabulary, synonyms, or phrasing
3. Target different document types or sources
4. Be specific and actionable
5. Provide diverse search coverage

Guidelines:
- Generate 3-5 alternative phrasings
- Use varied terminology and technical language
- Consider different user backgrounds or expertise levels
- Include both formal and informal phrasings
- Ensure each alternative is independently useful

Examples:
Original: "How to configure SSL in Mule 4.5?"
Alternatives:
- "What are the steps to set up SSL certificates in MuleSoft 4.5?"
- "How do I enable HTTPS with SSL in Mule 4.5?"
- "SSL certificate configuration for Mule 4.5 connectors"
- "Setting up secure connections in MuleSoft 4.5"
- "How to implement SSL/TLS in Mule 4.5 applications?"

Original: "Database optimization techniques"
Alternatives:
- "How to improve database performance?"
- "What are database tuning best practices?"
- "Database optimization strategies and methods"
- "How to speed up database queries?"
- "Database performance improvement techniques"

Output Format:
Return each alternative on a separate line, numbered 1, 2, 3, etc.
No preamble, no explanation.""",
)

MULTI_QUERY_USER_PROMPT = Prompt(
    name="multi_query_user_prompt",
    prompt="""Original Question: {{ query }}

Generate alternative phrasings:""",
)
