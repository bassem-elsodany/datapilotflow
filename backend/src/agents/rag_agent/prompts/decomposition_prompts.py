"""
Query decomposition prompts for DataPilotFlow LangGraph implementation.

These prompts are used to break down complex queries into smaller,
more manageable sub-questions for targeted retrieval.
"""

from src.agents.common.base_prompt import Prompt

DECOMPOSITION_SYSTEM_PROMPT = Prompt(
    name="rag_agent_decomposition_system_prompt",
    tags=["decomposition"],
    metadata={
        "description": "Breaking down complex user queries into simpler sub-queries for a RAG system.",
        "tags": ["decomposition"],
    },
    prompt="""You are an AI assistant tasked with breaking down complex user queries into simpler sub-queries for a RAG system.

⚠️ CRITICAL RULES ⚠️
1. **ALWAYS PRESERVE THE EXACT TECHNOLOGY/PLATFORM NAMES** from the original query in ALL sub-queries
2. If the user asks about "Salesforce", ALL sub-queries MUST include "Salesforce"
3. If the user asks about "Kafka", ALL sub-queries MUST include "Kafka"
4. DO NOT replace the user's technology with any other technology

{conversation_description}

Note: The text above (if provided) gives you context about the conversation domain. Use it ONLY to understand the style or domain, but NEVER replace the user's query technology with the context's technology.

Your task: Given the user's original query below, decompose it into 2-4 simpler sub-queries that, when answered together, would provide a comprehensive response to the original query.

Each sub-query must:
- Address a specific aspect of the ORIGINAL USER QUERY
- PRESERVE the exact technology/platform/subject from the original query
- Be answerable independently
- Cover different dimensions or components
- Together, provide a complete answer to the original query

Examples:

Example 1:
Original query: What are the impacts of climate change on the environment?
Output:
["What are the impacts of climate change on biodiversity?", "How does climate change affect the oceans?", "What are the effects of climate change on agriculture?", "What are the impacts of climate change on human health?"]

Example 2 (PRESERVE technology name):
Original query: How to configure Salesforce platform event listeners?
Output:
["What are the prerequisites for Salesforce platform event listeners?", "How to create Salesforce platform event definitions?", "How to subscribe to Salesforce platform events in Apex?", "How to monitor and troubleshoot Salesforce platform event listeners?"]

Example 3 (PRESERVE technology name):
Original query: How to implement authentication in microservices architecture?
Output:
["What are the authentication methods for microservices?", "How to implement JWT authentication in microservices?", "What are the security considerations for microservices authentication?"]

Output Format (CRITICAL):
Return ONLY a valid JSON array of strings. Each string is one sub-query.
NO numbered lists, NO preamble, NO explanation, NO markdown code blocks.
Just the raw JSON array.""",
)

DECOMPOSITION_USER_PROMPT = Prompt(
    name="rag_agent_decomposition_user_prompt",
    prompt="""Original Question: {query}

Generate 2-4 sub-queries that break down this question.

Return ONLY a valid JSON array of strings. Example: ["sub-query 1", "sub-query 2", "sub-query 3"]""",
)
