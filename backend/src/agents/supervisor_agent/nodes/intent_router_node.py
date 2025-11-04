"""
Intent Router Node for Supervisor Agent.

Routes user input to appropriate agents based on detected intent.
"""

from typing import Any, Dict

from langchain_core.language_models.base import BaseLanguageModel
from loguru import logger

from src.agents.supervisor_agent.chains import get_intent_detection_chain
from src.agents.supervisor_agent.state import SupervisorAgentState


def intent_router_node(
    state: SupervisorAgentState, llm_client: BaseLanguageModel
) -> Dict[str, Any]:
    """
    Detect user intent and route to appropriate agent(s).

    Returns one of:
    - "rag_only": Route to RAG Agent only for retrieval
    - "rag_then_task": Route to RAG Agent then Task Agent for execution with knowledge

    Args:
        state: Current SupervisorAgentState
        llm_client: LLM client for intent detection

    Returns:
        Updated state with detected_intent populated
    """
    logger.info("🎯 Intent Router Node: Detecting user intent")

    user_input = state.get("user_input", "")
    if not user_input:
        logger.warning(
            "No user input for intent detection, defaulting to rag_only"
        )
        return {
            "detected_intent": "rag_only",
            "intent_confidence": 0.5,
        }

    logger.debug(f"📝 Intent Router: Processing input: {user_input[:100]}...")

    try:
        # Get intent detection chain
        chain = get_intent_detection_chain(llm_client)

        # Detect intent
        result = chain.invoke({"user_input": user_input})
        intent_text = result.content if hasattr(result, "content") else str(result)
        intent = intent_text.strip().lower()

        # Validate intent - only rag_only and rag_then_task are supported
        valid_intents = ["rag_only", "rag_then_task"]
        if intent not in valid_intents:
            logger.warning(
                f"Invalid intent detected: {intent}, defaulting to rag_only"
            )
            intent = "rag_only"

        logger.info(f"✅ Intent Router: Detected intent: {intent}")

        return {
            "detected_intent": intent,
            "intent_confidence": 0.95,
        }

    except Exception as e:
        logger.error(f"❌ Intent Router error: {e}, defaulting to rag_only")
        return {
            "detected_intent": "rag_only",
            "intent_confidence": 0.0,
        }
