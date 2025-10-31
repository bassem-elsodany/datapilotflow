"""
Generate Response Service for LangGraph Workflow

This module handles the execution of the LangGraph workflow for generating
AI responses with query enhancement capabilities.
"""

import time
import traceback
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from langchain_community.chat_models import ChatLiteLLM
from loguru import logger
from opik.integrations.langchain import OpikTracer
from opik.integrations.litellm import track_litellm

from src.config import settings
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)
from src.workflow.graph import graph_dev as workflow
from src.workflow.state import WorkflowState, create_initial_state


async def get_response_stream(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    conversation_id: str,
    collection_name: str,
    selected_strategy: Optional[str] = None,
    retrieval_strategy: Optional[
        str
    ] = None,  # None = auto-detect based on query variants
    enhancement_config: Optional[Dict[str, Any]] = None,
    enable_reranking: bool = True,
    enable_llm_generation: bool = True,
    top_k: int = 5,
    conversation_description: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using LangGraph workflow with query enhancement (streaming).

    This function yields chunks as the workflow progresses, allowing real-time
    updates to the frontend for better interactivity.

    Args:
        query: User's question/query
        user_id: User ID for authentication and context
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        conversation_id: Conversation ID for context and tracing
        collection_name: Vector database collection name
        selected_strategy: Query enhancement strategy to use
        enhancement_config: Additional enhancement configuration
        enable_reranking: Whether to enable document reranking
        enable_llm_generation: Whether to enable LLM answer generation (True = generated, False = raw)

    Yields:
        Dict containing workflow state chunks with progress updates

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
            # Enable LiteLLM tracking for cost and token usage
            track_litellm()
            logger.debug("✅ LiteLLM tracking enabled for cost and token usage")

            # Build tags for Opik trace
            trace_tags = [
                f"strategy:{selected_strategy or 'native'}",
                f"provider:{llm_provider_id}",
                f"model:{llm_model_name}",
                f"collection:{collection_name}",
            ]
            if conversation_description:
                trace_tags.append(f"domain:{conversation_description[:50]}")

            opik_tracer = OpikTracer(
                graph=workflow.get_graph(xray=True),
                tags=trace_tags,
            )
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
            "enable_llm_generation": enable_llm_generation,
            "top_k": top_k,
            "retrieval_config": {
                "retrieval_strategy": retrieval_strategy,
                "top_k_per_query": 5,  # Retrieve 5 docs per query variant for RRF
                "rrf_k": 60,  # RRF constant (from original paper)
            },
        }

        logger.info(
            f"🔧 Workflow config: enable_reranking={enable_reranking}, enable_llm_generation={enable_llm_generation}, collection={collection_name}, strategy={selected_strategy}"
        )

        # Get provider configuration to create LLM client
        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(llm_provider_id, user_id)

        if not provider:
            raise ValueError(f"Provider not found: {llm_provider_id}")

        if not provider.is_active:
            raise ValueError(f"Provider is not active: {provider.name}")

        # Create LLM client using ChatLiteLLM
        model_string = f"{provider.provider_type}/{llm_model_name}"
        llm_client = ChatLiteLLM(
            model=model_string,
            api_key=provider.api_key,
            api_base=provider.endpoint if provider.endpoint else None,
            timeout=provider.timeout if provider.timeout else 60,
        )

        logger.info(f"✅ Created LLM client: {model_string}")

        # Add LLM client to workflow config
        workflow_config["llm_client"] = llm_client

        # Create initial state
        initial_state = create_initial_state(
            query=query,
            selected_strategy=selected_strategy,
            config=workflow_config,
            conversation_description=conversation_description,
        )

        logger.debug(f"Initial state created with strategy: {selected_strategy}")
        logger.debug(
            f"Initial state config keys: {list(initial_state.get('config', {}).keys())}"
        )
        logger.debug(
            f"Initial state enable_reranking: {initial_state.get('config', {}).get('enable_reranking', 'NOT SET')}"
        )

        # Execute LangGraph workflow with streaming
        logger.info("🔄 Executing LangGraph workflow (streaming mode)...")

        # Create the async stream iterator
        stream_iterator = workflow.astream(
            input=WorkflowState(**initial_state),
            config=config,
            stream_mode="updates",  # Stream node updates to track which node is running
        )

        # Track the last complete state for final result
        last_state = {}
        chunk_count = 0

        # Iterate over the stream and yield chunks to the frontend
        async for chunk in stream_iterator:
            chunk_count += 1

            # With stream_mode="updates", chunk is {node_name: state_update}
            # Extract the node name and state
            node_name = list(chunk.keys())[0] if chunk else "unknown"
            state_update = chunk.get(node_name, {}) if chunk else {}
            # Merge state updates to accumulate all fields
            last_state = {**last_state, **state_update}

            # Calculate current execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Create a streamable chunk with relevant state information
            stream_chunk = {
                "type": "workflow_progress",
                "chunk_number": chunk_count,
                "execution_time_ms": execution_time_ms,
                "current_node": node_name,
                "query": state_update.get("query", query),
                "enhanced_query": state_update.get("enhanced_query"),
                "retrieved_documents": state_update.get("retrieved_documents") or [],
                "final_answer": state_update.get("final_answer") or "",
                "workflow_completed": False,
            }

            logger.debug(
                f"📦 Streaming chunk {chunk_count}: node={stream_chunk['current_node']}, "
                f"docs={len(stream_chunk['retrieved_documents']) if stream_chunk['retrieved_documents'] else 0}, "
                f"answer_len={len(stream_chunk['final_answer'])}"
            )

            yield stream_chunk

        # Calculate final execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Yield final result with complete state
        if last_state:
            final_result = {
                "type": "workflow_complete",
                "execution_time_ms": execution_time_ms,
                "workflow_completed": True,
                "query": last_state.get("query", query),
                "response": last_state.get("final_answer", ""),
                "documents": last_state.get("retrieved_documents", []),
                "enhanced_query": last_state.get("enhanced_query"),
                "query_info": last_state.get(
                    "query_info"
                ),  # Contains enhanced_queries array
                "total_chunks": chunk_count,
            }

            logger.info(
                f"✅ LangGraph workflow completed in {execution_time_ms:.2f}ms "
                f"({chunk_count} chunks) for query: '{query[:50]}...'"
            )

            # Log workflow results summary
            if final_result.get("enhanced_query"):
                enhanced_query = final_result["enhanced_query"]
                logger.debug(
                    f"Enhanced queries generated: {len(enhanced_query.get('queries', []))}"
                )

            documents = final_result.get("documents", [])
            logger.debug(f"Documents retrieved: {len(documents)}")

            response = final_result.get("response", "")
            logger.debug(f"Response generated: {len(response)} characters")

            yield final_result
        else:
            logger.warning("⚠️ Workflow completed but no state was captured")
            yield {
                "type": "workflow_complete",
                "execution_time_ms": execution_time_ms,
                "workflow_completed": True,
                "query": query,
                "response": "",
                "documents": [],
                "enhanced_query": None,
                "error": "No workflow state captured",
                "total_chunks": chunk_count,
            }

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"❌ LangGraph workflow failed after {execution_time_ms:.2f}ms: {e}"
        )
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Yield error result
        yield {
            "type": "workflow_error",
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "workflow_completed": False,
            "query": query,
            "response": f"I encountered an error while processing your query: {str(e)}",
            "documents": [],
            "enhanced_query": None,
        }
