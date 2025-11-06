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
    prompt="""You are an AI assistant tasked with analyzing and decomposing user queries for a RAG system.

⚠️ CRITICAL RULES ⚠️
1. **PRESERVE EXACT NAMES/TERMS** from the original query in ALL sub-queries
2. If the query mentions "X", ALL sub-queries MUST include "X"
3. DO NOT replace the user's terms with different ones

{conversation_description}

Note: The text above (if provided) gives you context about the conversation domain. Use it ONLY to understand the style, but NEVER replace the query's terms with the context's terms.

---

**YOUR TASK:**

Analyze the query and decide:
- **Simple/focused query?** → Return as-is (don't decompose)
- **Multiple distinct concepts?** → Break into 2-4 focused sub-queries
- **Single concept with aspects?** → Break into 2-4 sub-queries covering different aspects

**GUIDELINES:**

1. **Don't Over-Decompose:**
   - If query is already simple and focused → return it unchanged
   - Example: "What is X?" → ["What is X?"] (single query)

2. **Focus on Core Concepts:**
   - Identify 2-4 MAIN concepts or aspects (ignore minor/generic mentions)
   - Each sub-query should target ONE core concept or aspect
   - Example: Query mentions A, B, C, D, E, F → Focus on 2-3 most important

3. **Preserve Names:**
   - Keep exact names, terms, brands, subjects from original query
   - Don't substitute or generalize

4. **Question Format:**
   - Use question format for better document matching
   - Be specific and focused

5. **For Multiple Concepts:**
   - Last sub-query should address how concepts relate (if relevant)
   - Example: If query asks about "X with Y" → include "How X and Y work together"

---

**EXAMPLES:**

Example 1 (Simple - DON'T decompose):
Query: "What is microservices architecture?"
Output: ["What is microservices architecture?"]

Example 2 (Multiple aspects - DO decompose):
Query: "What are the impacts of climate change on the environment?"
Output:
["What are the impacts of climate change on biodiversity?",
 "How does climate change affect the oceans?",
 "What are the effects of climate change on agriculture?"]

Example 3 (Multiple concepts - DO decompose):
Query: "How to configure Salesforce platform event listeners?"
Output:
["What are the prerequisites for Salesforce platform event listeners?",
 "How to create Salesforce platform event definitions?",
 "How to subscribe to Salesforce platform events in Apex?"]

Example 4 (Multiple entities - DO decompose, include relationship):
Query: "generate http listener xml flow with apikit"
Output:
["What is HTTP listener configuration?",
 "How does APIKit work?",
 "How to use HTTP listener with APIKit?"]

Example 5 (Focused topic - DON'T over-decompose):
Query: "SSL configuration"
Output: ["SSL configuration"]

---

**Original Query:**
{query}

Analyze and decide: decompose or return as-is?
If decomposing, create 2-4 focused sub-queries.

**Output Format (CRITICAL):**
Return ONLY a valid JSON array of strings.
NO numbered lists, NO preamble, NO explanation, NO markdown blocks.
Just the raw JSON array.

Examples:
- Not decomposed: ["original query"]
- Decomposed: ["sub-query 1", "sub-query 2", "sub-query 3"]""",
)

DECOMPOSITION_USER_PROMPT = Prompt(
    name="rag_agent_decomposition_user_prompt",
    prompt="""Original Question: {query}

Generate 2-4 sub-queries that break down this question.

Return ONLY a valid JSON array of strings. Example: ["sub-query 1", "sub-query 2", "sub-query 3"]""",
)
