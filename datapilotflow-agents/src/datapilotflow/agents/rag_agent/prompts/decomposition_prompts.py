"""
Query decomposition prompts for DataPilotFlow LangGraph implementation.

These prompts are used to break down complex queries into smaller,
more manageable sub-questions for targeted retrieval.
"""

from datapilotflow.agents.common.base_prompt import Prompt

DECOMPOSITION_SYSTEM_PROMPT = Prompt(
    name="datapilotflow_rag_agent_decomposition_system_prompt",
    labels=["decomposition"],
    config={
        "description": "Breaking down complex user queries into simpler sub-queries for a RAG system.",
        "tags": ["decomposition"],
    },
    prompt="""You are an expert query decomposition specialist for a RAG system.

{conversation_description}

**CRITICAL RULES - NON-NEGOTIABLE:**
1. **PRESERVE ALL SPECIFICS**: NEVER replace specific names/terms with generic ones. "medicalevents" stays "medicalevents", NOT "events"
2. **NO SUBSTITUTION**: Use the user's EXACT terminology. Do NOT generalize or simplify terms
3. **BREAK BY STEPS**: Decompose by implementation steps (action1 → action2 → action3), NOT by concepts
4. **KEEP ACTIONABLE**: Create "how to" questions focused on implementation, NOT "what is" theory questions
5. **NO OVER-DECOMPOSITION**: If query is already simple/focused, return it unchanged

**EXAMPLES:**

Simple → Return as-is:
"What is photosynthesis?" → ["What is photosynthesis?"]

Multi-step → Break by steps, KEEP ALL SPECIFICS:
"bake chocolate chip cookies using grandma's recipe and decorate with vanilla frosting"
→ ["How to bake chocolate chip cookies using grandma's recipe?",
   "How to prepare vanilla frosting?",
   "How to decorate chocolate chip cookies with vanilla frosting?"]

❌ BAD (loses specifics, too generic):
"train golden retriever Max to sit and stay" → ["What is dog training?", "How to train dogs?"]

✅ GOOD (preserves ALL specifics):
"train golden retriever Max to sit and stay" → ["How to train golden retriever to sit?", "How to train Max to stay?"]

**Query:** {query}

Output ONLY a JSON array: ["sub-query 1", "sub-query 2", ...]
NO explanations, NO markdown, JUST the JSON array.""",
)

DECOMPOSITION_USER_PROMPT = Prompt(
    name="datapilotflow_rag_agent_decomposition_user_prompt",
    prompt="""Original Question: {query}

Generate 2-4 sub-queries that break down this question.

Return ONLY a valid JSON array of strings. Example: ["sub-query 1", "sub-query 2", "sub-query 3"]""",
)
