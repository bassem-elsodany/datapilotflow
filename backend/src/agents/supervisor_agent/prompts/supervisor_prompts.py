"""
Supervisor Agent prompts for intent detection and orchestration.
"""

from src.agents.common.base_prompt import Prompt

INTENT_DETECTION_PROMPT = Prompt(
    name="supervisor_agent_intent_detection_prompt",
    prompt="""Classify this user request into EXACTLY ONE category:

**Our Knowledge Base is the ONLY source of truth. All requests must be grounded in knowledge base documents.**

1. "rag_only" - User ONLY wants to search/retrieve/find information from the knowledge base
   Examples: "What is X?", "Find documents about Y?", "Show me information on Z"
   → Route to RAG Agent for retrieval only
   → No task execution needed

2. "rag_then_task" - User wants to DO something based on retrieved knowledge from the knowledge base
   Examples: "Write code based on these docs", "Create a plan using this information", "Summarize what we know about X"
   → Route to RAG Agent first, then Task Agent to execute with retrieved knowledge
   → Knowledge base is the context for the task

User request: "{user_input}"

Respond with EXACTLY ONE option: "rag_only" or "rag_then_task". Nothing else.""",
)
