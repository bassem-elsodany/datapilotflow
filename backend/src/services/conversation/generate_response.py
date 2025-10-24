"""
Generate Response Service for LangGraph Workflow

This module handles the execution of the LangGraph workflow for generating
AI responses with query enhancement capabilities.
"""

import time
import traceback
import uuid
from typing import Any, Dict, Optional

from loguru import logger
from opik.integrations.langchain import OpikTracer

from src.config import settings
from src.workflow.graph import graph_dev as workflow
from src.workflow.state import create_initial_state


async def get_response(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    conversation_id: str,
    collection_name: str = "LongTermMemory",
    selected_strategy: Optional[str] = None,
    enhancement_config: Optional[Dict[str, Any]] = None,
    enable_reranking: bool = True,
) -> Dict[str, Any]:
    """
    Generate AI response using LangGraph workflow with query enhancement.

    Args:
        query: User's question/query
        user_id: User ID for authentication and context
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        conversation_id: Conversation ID for context and tracing
        collection_name: Vector database collection name
        selected_strategy: Query enhancement strategy to use
        enhancement_config: Additional enhancement configuration

    Returns:
        Dict containing the workflow result with response and metadata

    Raises:
        Exception: If workflow execution fails
    """
    start_time = time.time()

    try:
        logger.info(f"🚀 Starting LangGraph workflow for query: '{query[:50]}...'")
        logger.debug(
            f"Workflow config: strategy={selected_strategy}, collection={collection_name}"
        )

        config = {}
        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Workflow config: strategy={selected_strategy}, collection={collection_name}, llm_provider_id={llm_provider_id}, llm_model_name={llm_model_name}"
            )
            opik_tracer = OpikTracer(graph=workflow.get_graph(xray=True))
            thread_id = conversation_id
            config = {
                "configurable": {"thread_id": thread_id},
                "callbacks": [opik_tracer],
            }
        else:
            logger.debug(
                f"Agent tracing disabled: Workflow config: strategy={selected_strategy}, collection={collection_name}"
            )

        # Build workflow configuration
        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "enhancement_config": enhancement_config or {},
            "conversation_id": conversation_id,
            "enable_reranking": enable_reranking,
        }

        # Create initial state
        initial_state = create_initial_state(
            query=query,
            selected_strategy=selected_strategy,
            config=workflow_config,
        )

        logger.debug(f"Initial state created with strategy: {selected_strategy}")

        # Execute LangGraph workflow
        logger.info("🔄 Executing LangGraph workflow...")
        result = await workflow.ainvoke(initial_state, config=config)

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Add execution metadata
        result["execution_time_ms"] = execution_time_ms
        result["workflow_completed"] = True

        logger.info(
            f"✅ LangGraph workflow completed in {execution_time_ms:.2f}ms "
            f"for query: '{query[:50]}...'"
        )

        # Log workflow results summary
        if result.get("enhanced_query"):
            enhanced_query = result["enhanced_query"]
            logger.debug(
                f"Enhanced queries generated: {len(enhanced_query.get('queries', []))}"
            )

        documents = result.get("documents", [])
        logger.debug(f"Documents retrieved: {len(documents)}")

        response = result.get("response", "")
        logger.debug(f"Response generated: {len(response)} characters")

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"❌ LangGraph workflow failed after {execution_time_ms:.2f}ms: {e}"
        )
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Return error result
        return {
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "workflow_completed": False,
            "query": query,
            "response": f"I encountered an error while processing your query: {str(e)}",
            "documents": [],
            "enhanced_query": None,
        }
