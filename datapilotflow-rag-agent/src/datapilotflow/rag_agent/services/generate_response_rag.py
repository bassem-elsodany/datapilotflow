"""
Generate Response Service for RAG-Only Mode

This module handles the execution of the LangGraph workflow for generating
AI responses using direct RAG pipeline without supervisor routing.
"""

import asyncio
import os
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

import litellm
from datapilotflow.domain.config import settings
from datapilotflow.domain.conversation import ConversationMessage
from datapilotflow.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from datapilotflow.services.model_provider.model_provider_service import (
    get_model_provider_service,
)
from langchain_litellm import ChatLiteLLM
from loguru import logger

from datapilotflow.rag_agent.graph import graph_dev as workflow
from datapilotflow.rag_agent.state import RAGWorkflowState as WorkflowState
from datapilotflow.rag_agent.state import create_initial_state

from ..agent_state import AgentState

# Enable dropping unsupported params for different LLM providers
# (e.g., GPT-5 only supports temperature=1, not 0.7)
litellm.drop_params = True


async def get_response_stream_rag(
    query: str,
    user_id: str,
    llm_provider_id: Optional[str],
    llm_model_name: Optional[str],
    conversation_id: str,
    collection_name: str,
    selected_strategy: Optional[str] = None,
    retrieval_strategy: Optional[str] = None,
    enhancement_config: Optional[Dict[str, Any]] = None,
    enable_reranking: bool = True,
    relevance_threshold: float = 0.5,
    enable_llm_generation: bool = True,
    top_k: int = 5,
    conversation_description: Optional[str] = None,
    reranker_provider_id: Optional[str] = None,
    reranker_model_name: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using direct RAG-only pipeline (streaming).

    **RAG-ONLY MODE** - This endpoint uses ONLY the RAG pipeline without any supervisor/agent routing.

    Yields:
        Dict containing workflow state chunks with progress updates
    """
    start_time = time.time()

    try:
        logger.info(f"Starting LangGraph workflow for query: '{query[:50]}...'")
        logger.debug(
            f"Workflow config: strategy={selected_strategy}, collection={collection_name}"
        )

        # Note: No thread_id needed - each query is independent (stateless RAG)
        config = {
            "configurable": {"thread_id": uuid.uuid4()},
        }

        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Workflow config: strategy={selected_strategy}, collection={collection_name}, llm_provider_id={llm_provider_id}, llm_model_name={llm_model_name}"
            )
            # Enable LiteLLM tracking for cost and token usage
            logger.debug("LiteLLM tracking enabled for cost and token usage")
        else:
            logger.debug(
                f"Agent tracing disabled: Workflow config: strategy={selected_strategy}, collection={collection_name}"
            )

        # Build workflow configuration
        # Calculate top_k_per_query: For RRF, we retrieve more docs per query to account for fusion
        # Smart default: retrieve at least 5 per query, or scale with top_k if user requests more
        top_k_per_query = max(
            5, int(top_k * 1.5)
        )  # 50% more to account for RRF deduplication

        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "enhancement_config": enhancement_config or {},
            "conversation_id": conversation_id,
            "enable_reranking": enable_reranking,
            "reranking_config": {
                "relevance_threshold": relevance_threshold,
                "use_score_based": True,  # Use continuous scores instead of binary labels
            },
            "enable_llm_generation": enable_llm_generation,
            "top_k": top_k,
            "retrieval_config": {
                "top_k_per_query": top_k_per_query,  # Dynamically scale based on user's top_k
                "rrf_k": 60,  # RRF constant (from original paper)
            },
        }

        logger.info(
            f"🔧 Workflow config: enable_reranking={enable_reranking}, enable_llm_generation={enable_llm_generation}, collection={collection_name}, strategy={selected_strategy}"
        )

        # Determine if primary LLM is needed:
        # - For LLM generation (answer synthesis)
        # - For non-native strategies (augmented, hyde, multi_query need LLM for query enhancement)
        # - For reranking ONLY if no separate reranker provider is specified
        strategy_requires_llm = selected_strategy and selected_strategy.lower() not in [
            "native",
            "",
        ]
        needs_primary_llm = (
            enable_llm_generation
            or strategy_requires_llm
            or (enable_reranking and not reranker_provider_id)
        )

        # Create primary LLM client if needed
        if needs_primary_llm and llm_provider_id and llm_model_name:
            logger.info(
                f"🔑 Primary LLM provider required - fetching provider configuration (reranking={enable_reranking and not reranker_provider_id}, generation={enable_llm_generation}, strategy_requires_llm={strategy_requires_llm})"
            )

            # Get provider configuration to create primary LLM client
            provider_service = get_model_provider_service()
            provider = provider_service.get_model_provider(llm_provider_id, user_id)

            if not provider:
                raise ValueError(f"Primary provider not found: {llm_provider_id}")

            if not provider.is_active:
                raise ValueError(f"Primary provider is not active: {provider.name}")

            # Validate API key is configured for this provider
            if not provider.api_key or provider.api_key.strip() == "":
                raise ValueError(
                    f"API key not configured for provider '{provider.name}' ({provider.provider_type}). "
                    f"Please configure the API key in the provider settings."
                )

            logger.debug(
                f"🔑 Primary provider API key status: {'SET (' + str(len(provider.api_key)) + ' chars)' if provider.api_key else 'NOT SET'}"
            )

            # Get temperature and max_tokens from provider's generative config
            generative_config = (
                provider.generative.config if provider.generative else {}
            )
            temperature = generative_config.get("temperature", 0.7)
            max_tokens = generative_config.get("max_tokens", 4096)

            # Create primary LLM client using ChatLiteLLM with provider's config
            # If provider_type is "custom", use model name directly without prefix
            if provider.provider_type.lower() == "custom":
                model_string = llm_model_name
            else:
                model_string = f"{provider.provider_type}/{llm_model_name}"

            # Prepare ChatLiteLLM parameters with custom API key field name support
            llm_params = {
                "model": model_string,
                "api_base": provider.endpoint if provider.endpoint else None,
                "timeout": provider.timeout if provider.timeout else 60,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "streaming": True,  # Enable streaming for real-time response chunks
            }

            # Handle API key and custom header name
            if provider.api_key:
                llm_params["api_key"] = provider.api_key
                # If custom API key field name is specified, add it to extra_headers
                if (
                    provider.api_key_field_name
                    and provider.api_key_field_name != "api_key"
                ):
                    llm_params["extra_headers"] = {
                        provider.api_key_field_name: provider.api_key
                    }

            llm_client = ChatLiteLLM(**llm_params)

            logger.info(
                f"✅ Created primary LLM client: {model_string} (temperature={temperature}, max_tokens={max_tokens})"
            )

            # Add primary LLM client to workflow config
            workflow_config["llm_client"] = llm_client
        else:
            if not needs_primary_llm:
                logger.info(
                    f"⏭️  Skipping primary LLM provider setup - native strategy with no reranking/generation (strategy={selected_strategy})"
                )
            else:
                logger.warning(
                    "⚠️ Primary LLM provider ID or model name missing but required"
                )

        # Create reranker LLM client if reranking is enabled and separate provider is specified
        if enable_reranking and reranker_provider_id and reranker_model_name:
            logger.info(
                f"🔑 Reranker LLM provider specified - creating separate reranker client"
            )

            # Get reranker provider configuration
            provider_service = get_model_provider_service()
            reranker_provider = provider_service.get_model_provider(
                reranker_provider_id, user_id
            )

            if not reranker_provider:
                raise ValueError(f"Reranker provider not found: {reranker_provider_id}")

            if not reranker_provider.is_active:
                raise ValueError(
                    f"Reranker provider is not active: {reranker_provider.name}"
                )

            # Validate API key is configured for reranker provider
            if not reranker_provider.api_key or reranker_provider.api_key.strip() == "":
                raise ValueError(
                    f"API key not configured for reranker provider '{reranker_provider.name}' ({reranker_provider.provider_type}). "
                    f"Please configure the API key in the provider settings."
                )

            # Get temperature and max_tokens from reranker provider's generative config
            reranker_generative_config = (
                reranker_provider.generative.config
                if reranker_provider.generative
                else {}
            )
            reranker_temperature = reranker_generative_config.get("temperature", 0.7)
            reranker_max_tokens = reranker_generative_config.get("max_tokens", 4096)

            # Create reranker LLM client
            # If provider_type is "custom", use model name directly without prefix
            if reranker_provider.provider_type.lower() == "custom":
                reranker_model_string = reranker_model_name
            else:
                reranker_model_string = (
                    f"{reranker_provider.provider_type}/{reranker_model_name}"
                )

            # Prepare ChatLiteLLM parameters with custom API key field name support
            reranker_params = {
                "model": reranker_model_string,
                "api_base": (
                    reranker_provider.endpoint if reranker_provider.endpoint else None
                ),
                "timeout": (
                    reranker_provider.timeout if reranker_provider.timeout else 60
                ),
                "temperature": reranker_temperature,
                "max_tokens": reranker_max_tokens,
                "streaming": True,
            }

            # Handle API key and custom header name
            if reranker_provider.api_key:
                reranker_params["api_key"] = reranker_provider.api_key
                # If custom API key field name is specified, add it to extra_headers
                if (
                    reranker_provider.api_key_field_name
                    and reranker_provider.api_key_field_name != "api_key"
                ):
                    reranker_params["extra_headers"] = {
                        reranker_provider.api_key_field_name: reranker_provider.api_key
                    }

            reranker_client = ChatLiteLLM(**reranker_params)

            logger.info(
                f"✅ Created reranker LLM client: {reranker_model_string} (temperature={reranker_temperature}, max_tokens={reranker_max_tokens})"
            )

            # Add reranker LLM client to workflow config
            workflow_config["reranker_client"] = reranker_client
        elif enable_reranking:
            logger.info(
                "✅ Reranking enabled - will use primary LLM client for reranking"
            )

        logger.info("Using direct RAG workflow (no supervisor)")

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
        logger.info("Executing LangGraph workflow (streaming mode)...")

        # Create the async stream iterator with events mode to get START and END events
        stream_iterator = workflow.astream_events(
            input=WorkflowState(**initial_state),
            config=config,
            version="v2",  # Use v2 for better event tracking
        )

        # Track the last complete state for final result
        last_state = {}
        chunk_count = 0

        # Iterate over the stream and yield chunks to the frontend
        last_stage = None
        stage_mapping = {
            "augmented_strategy_node": "query_enhancement",
            "multi_query_strategy_node": "query_enhancement",
            "hyde_strategy_node": "query_enhancement",
            "decomposition_strategy_node": "query_enhancement",
            "document_retriever": "document_retrieval",
            "document_judger": "document_judging",
            "answer_generator": "response_generation",
            "raw_response_formatter": "response_generation",
        }

        # Track stage completion to emit COMPLETE events
        stages_completed = set()
        query_enhancement_emitted = (
            False  # Track if we've emitted query_enhancement START event
        )
        document_judging_emitted = (
            False  # Track if we've emitted document_judging START event
        )
        answer_generation_emitted = (
            False  # Track if we've emitted response_generation START event
        )
        first_llm_chunk_emitted = (
            False  # Track if we've emitted the first LLM chunk with metadata
        )

        # Store enable_reranking flag to avoid emitting judging events when disabled
        is_reranking_enabled = enable_reranking

        # CRITICAL: Determine the actual last step based on what's enabled
        # Pipeline order: query_enhancement → document_retrieval → document_judging → response_generation
        # Last step depends on enabled flags:
        # - If enable_llm_generation=True: last step is response_generation
        # - If enable_llm_generation=False AND enable_reranking=True: last step is document_judging
        # - If enable_llm_generation=False AND enable_reranking=False: last step is document_retrieval
        if enable_llm_generation:
            last_step_for_streaming = "response_generation"
        elif enable_reranking:
            last_step_for_streaming = "document_judging"
        else:
            last_step_for_streaming = "document_retrieval"

        logger.critical(
            f"🎯 [STREAMING CONFIG] Last step for streaming: {last_step_for_streaming} "
            f"(enable_llm_generation={enable_llm_generation}, enable_reranking={enable_reranking})"
        )

        async for event in stream_iterator:
            chunk_count += 1

            # With astream_events, we get events with 'event', 'name', 'data' fields
            event_type = event.get("event", "")
            node_name = event.get("name", "")
            event_data = event.get("data", {})

            # Handle LLM streaming chunks - ONLY FROM THE LAST STEP
            if event_type == "on_chat_model_stream":
                # CRITICAL: Only stream responses from the actual last step
                # Use last_stage which is tracked as nodes execute
                # Note: on_chat_model_stream events don't have the node name, so we track by last_stage

                logger.debug(
                    f"[RAG STREAM EVENT] Received chunk - last_stage={last_stage}, last_step_for_streaming={last_step_for_streaming}"
                )

                # Only stream if we're in the actual last step
                if last_stage != last_step_for_streaming:
                    logger.debug(
                        f"[RAG STREAM SKIP] Skipping chunk - not at last step yet"
                    )
                    continue

                chunk_data = event_data.get("chunk", {})
                if hasattr(chunk_data, "content"):
                    content = chunk_data.content
                elif isinstance(chunk_data, dict):
                    content = chunk_data.get("content", "")
                else:
                    content = str(chunk_data) if chunk_data else ""

                if content:
                    # Emit metadata ONLY on the first chunk
                    if not first_llm_chunk_emitted:
                        first_llm_chunk_emitted = True

                        # Build metadata from retrieved documents (may be empty if not yet populated)
                        retrieved_docs = last_state.get("retrieved_documents") or []

                        # Extract enhanced queries from query_info
                        query_info = last_state.get("query_info") or {}
                        enhanced_queries = query_info.get("enhanced_queries", [])
                        strategy_used = query_info.get("strategy_used", "augmented")

                        yield {
                            "type": "streaming_response",
                            "chunk": content,
                            "metadata": {
                                "document_count": len(retrieved_docs),
                                "enhancement_strategy": strategy_used,
                                "enhanced_queries": enhanced_queries,
                            },
                            "execution_time_ms": execution_time_ms,
                        }
                    else:
                        # Subsequent chunks don't include metadata
                        yield {
                            "type": "streaming_response",
                            "chunk": content,
                            "execution_time_ms": execution_time_ms,
                        }
                continue

            # Track when answer_generator starts (for real-time streaming)
            if event_type == "on_chain_start" and node_name == "answer_generator":
                logger.info(
                    "[RAG] answer_generator node STARTED - setting last_stage to response_generation for streaming"
                )
                last_stage = "response_generation"
                if not answer_generation_emitted:
                    answer_generation_emitted = True
                    yield {
                        "type": "workflow_progress",
                        "stage": "response_generation",
                        "message": "Generating final response...",
                        "execution_time_ms": (time.time() - start_time) * 1000,
                    }

            # Skip non-node events
            if not event_type.startswith("on_chain"):
                continue

                logger.critical(f"[RAG NODE EVENT] type={event_type}, node={node_name}")

            # Get state from output if available
            state_update = {}
            if event_type == "on_chain_end":
                output = event_data.get("output", {})
                if isinstance(output, dict):
                    state_update = output
                    last_state = {**last_state, **state_update}

            # Merge state updates to accumulate all fields
            last_state = {**last_state, **state_update}

            # Calculate current execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # CRITICAL FIX: Some strategy nodes may not emit chunks to the stream
            # But their output appears in subsequent nodes' state
            # Check if enhanced_query exists and query_enhancement hasn't been emitted yet
            if (
                not query_enhancement_emitted
                and state_update.get("enhanced_query")
                and last_stage is None
            ):  # Haven't emitted any stage yet
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Detected enhanced_query in state but no strategy node chunk received!"
                )
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Emitting query_enhancement START event for missing/silent strategy node"
                )

                # Emit START event for query_enhancement
                start_event = {
                    "type": "workflow_progress",
                    "stage": "query_enhancement",
                    "message": "Processing query_enhancement...",
                    "execution_time_ms": execution_time_ms,
                }
                yield start_event
                query_enhancement_emitted = True
                last_stage = "query_enhancement"

            # CRITICAL FIX 1b: document_judger might also be a silent node
            # But judged_documents appears in the state after it runs
            # Check if judged_documents exists and document_judging hasn't been emitted yet
            # ONLY emit if reranking is actually enabled
            if (
                is_reranking_enabled
                and not document_judging_emitted
                and state_update.get("judged_documents")
                and last_stage != "document_judging"
            ):
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Detected judged_documents in state but document_judging START not emitted!"
                )
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Emitting document_judging START event for missing/silent document_judger node"
                )

                # Emit START event for document_judging
                start_event = {
                    "type": "workflow_progress",
                    "stage": "document_judging",
                    "message": "Processing document_judging...",
                    "execution_time_ms": execution_time_ms,
                }
                yield start_event
                document_judging_emitted = True
                last_stage = "document_judging"

            # CRITICAL FIX 2: answer_generator node also doesn't emit chunks to stream
            # But final_answer appears in the state after it runs
            # Check if final_answer exists and response_generation hasn't been emitted yet
            # IMPORTANT: Emit after document_retrieval OR document_judging (depending on if reranking is enabled)
            if (
                not answer_generation_emitted
                and state_update.get("final_answer")
                and last_stage in ["document_retrieval", "document_judging"]
            ):
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Detected final_answer in state after {last_stage}!"
                )
                logger.critical(
                    f"🔴 [RAG HIDDEN NODE] Emitting response_generation START event for missing/silent answer_generator node"
                )

                # Emit START event for response_generation
                start_event = {
                    "type": "workflow_progress",
                    "stage": "response_generation",
                    "message": "Processing response generation...",
                    "execution_time_ms": execution_time_ms,
                }
                yield start_event
                answer_generation_emitted = True
                last_stage = "response_generation"

            # Map node to stage for consistency with supervisor path
            current_stage = stage_mapping.get(node_name, node_name)
            logger.critical(
                f"🔴 [RAG MAPPING] node_name={node_name} -> current_stage={current_stage}, event_type={event_type}"
            )

            # Skip special nodes
            if node_name in ["__start__", "__end__", ""] or not node_name:
                logger.critical(
                    f"🔴 [RAG SKIP] Skipping special/empty node: {node_name}"
                )
                continue

            # Handle START events (on_chain_start)
            if event_type == "on_chain_start":
                if (
                    current_stage in stage_mapping.values()
                    and current_stage != last_stage
                ):
                    last_stage = current_stage
                    start_event = {
                        "type": "workflow_progress",
                        "stage": current_stage,
                        "message": f"Processing {current_stage}...",
                        "execution_time_ms": execution_time_ms,
                    }
                    logger.critical(
                        f"🚀 [RAG START EVENT] Node {node_name} started -> Emitting START for stage={current_stage}"
                    )
                    yield start_event

                    # Mark response_generation as emitted if this is that stage
                    # (prevents double-emission at end of stream)
                    if current_stage == "response_generation":
                        answer_generation_emitted = True
                        logger.critical(
                            f"🔴 [RAG START EVENT] Marked answer_generation_emitted=True to prevent double-emission"
                        )

                continue  # Done with START event, wait for END event

            # Handle END events (on_chain_end) - emit COMPLETE
            if event_type == "on_chain_end":
                # Only emit completion event once per node (not repeatedly)
                if node_name not in stages_completed:
                    stages_completed.add(node_name)

                # Handle stage-specific completion events
                if node_name in [
                    "augmented_strategy_node",
                    "multi_query_strategy_node",
                    "hyde_strategy_node",
                    "decomposition_strategy_node",
                ]:
                    # Query Enhancement - extract variants from enhanced_query
                    enhanced_query_dict = state_update.get("enhanced_query", {})
                    enhanced_queries = []

                    # Extract variants based on the node type
                    if isinstance(enhanced_query_dict, dict):
                        if "augmented_queries" in enhanced_query_dict:
                            # Augmented: get all except first (which is original)
                            all_queries = (
                                enhanced_query_dict.get("augmented_queries", []) or []
                            )
                            enhanced_queries = (
                                all_queries[1:] if len(all_queries) > 1 else []
                            )
                        elif "multi_query_variants" in enhanced_query_dict:
                            enhanced_queries = (
                                enhanced_query_dict.get("multi_query_variants", [])
                                or []
                            )
                        elif "sub_queries" in enhanced_query_dict:
                            enhanced_queries = (
                                enhanced_query_dict.get("sub_queries", []) or []
                            )
                        elif "hypothetical_answer" in enhanced_query_dict:
                            ha = enhanced_query_dict.get("hypothetical_answer")
                            enhanced_queries = [ha] if ha else []

                    # Ensure enhanced_queries is always a list, never None
                    if enhanced_queries is None:
                        enhanced_queries = []

                    strategy = node_name.replace("_strategy_node", "")

                    logger.info(
                        f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for query_enhancement_complete with {len(enhanced_queries)} variants"
                    )
                    yield {
                        "type": "workflow_progress",
                        "stage": "query_enhancement_complete",
                        "message": f"Query enhanced with {len(enhanced_queries)} variants using {strategy} strategy",
                        "data": {
                            "strategy": strategy,
                            "query_variants": enhanced_queries,
                            "variant_count": len(enhanced_queries),
                        },
                        "execution_time_ms": execution_time_ms,
                    }
                    # Skip the generic stream_chunk for this node since we already sent complete event
                    continue

                elif node_name == "document_retriever":
                    # Document Retrieval - count retrieved documents
                    retrieved_docs = state_update.get("retrieved_documents", [])
                    document_count = len(retrieved_docs)

                    logger.info(
                        f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for document_retrieval_complete with {document_count} documents"
                    )
                    yield {
                        "type": "workflow_progress",
                        "stage": "document_retrieval_complete",
                        "message": f"Retrieved {document_count} documents",
                        "data": {
                            "document_count": document_count,
                            "collection": last_state.get("config", {}).get(
                                "collection_name", "unknown"
                            ),
                        },
                        "execution_time_ms": execution_time_ms,
                    }

                    # Skip the generic stream_chunk for this node since we already sent complete event
                    continue

                elif node_name == "document_judger":
                    # Document Judging - Only emit if reranking is enabled
                    if not is_reranking_enabled:
                        logger.warning(
                            f"⚠️ Skipping document_judger event emission - reranking is disabled"
                        )
                        continue

                    # Document Judging - count relevant documents
                    judged_docs = state_update.get("judged_documents", [])
                    relevance_scores = state_update.get("relevance_scores", [])
                    relevance_threshold = (
                        last_state.get("config", {})
                        .get("reranking_config", {})
                        .get("relevance_threshold", 0.5)
                    )
                    relevant_count = len(
                        [s for s in relevance_scores if s >= relevance_threshold]
                    )
                    avg_score = (
                        sum(relevance_scores) / len(relevance_scores)
                        if relevance_scores
                        else 0
                    )

                    logger.info(
                        f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for document_judging_complete with {relevant_count}/{len(judged_docs)} relevant"
                    )
                    yield {
                        "type": "workflow_progress",
                        "stage": "document_judging_complete",
                        "message": f"Ranked documents: {relevant_count} relevant",
                        "data": {
                            "total_documents": len(judged_docs),
                            "relevant_documents": relevant_count,
                            "avg_score": avg_score,
                        },
                        "execution_time_ms": execution_time_ms,
                    }
                    # Skip the generic stream_chunk for this node since we already sent complete event
                    continue

                elif node_name in ["answer_generator", "raw_response_formatter"]:
                    # Response Generation / Raw Formatting
                    # DON'T emit COMPLETE yet - streaming will happen after this
                    # We'll emit COMPLETE after streaming is done
                    logger.info(
                        f"✅ [RAG NODE DONE] answer_generator finished, will stream response and then mark complete"
                    )
                    # Skip emitting completion here - we'll do it after streaming
                    continue

        # Calculate final execution time
        execution_time_ms = (time.time() - start_time) * 1000
        final_answer_text = last_state.get("final_answer") or ""

        # CRITICAL FIX 3: If response_generation wasn't emitted but we have final_answer, emit it now
        if not answer_generation_emitted and last_state.get("final_answer"):
            # Determine if this is from raw_response_formatter or answer_generator
            is_raw_response = (
                not enable_llm_generation
                and "Raw Results Mode" in last_state.get("final_answer", "")
            )
            response_source = (
                "raw_response_formatter"
                if is_raw_response
                else "answer_generator/unknown"
            )

            # Emit START event
            start_event = {
                "type": "workflow_progress",
                "stage": "response_generation",
                "message": "Processing response generation...",
                "execution_time_ms": execution_time_ms,
            }
            yield start_event
            answer_generation_emitted = True

            # Emit COMPLETE event with answer data
            final_answer = last_state.get("final_answer", "")
            generation_mode = "raw_response" if is_raw_response else "llm"

            complete_event = {
                "type": "workflow_progress",
                "stage": "response_generation_complete",
                "message": f"Generated response: {len(final_answer)} characters",
                "data": {
                    "response_length": len(final_answer),
                    "generation_mode": generation_mode,
                },
                "execution_time_ms": execution_time_ms,
            }
            yield complete_event

        # Emit the final_answer as streaming_response so frontend can display it
        # NOTE: This is a FALLBACK for when real-time streaming didn't work
        # If first_llm_chunk_emitted is True, chunks were already streamed in real-time
        final_answer = last_state.get("final_answer", "") if last_state else ""
        if final_answer and not first_llm_chunk_emitted:
            # Emit metadata on first chunk only
            retrieved_docs = last_state.get("retrieved_documents", []) or []
            # Structured links with URL, title, chunk_id, and variant info
            source_links = []
            for doc in retrieved_docs:
                source_url = doc.get("source_url")
                if source_url:
                    title = doc.get("title") or doc.get("metadata", {}).get("title")
                    chunk_id = doc.get("chunk_id")
                    query_variant_index = doc.get("query_variant_index")
                    query_variant = doc.get("query_variant")
                    source_links.append(
                        {
                            "url": source_url,
                            "title": title or "Untitled Document",
                            "chunk_id": chunk_id or "",
                            "query_variant_index": query_variant_index,
                            "query_variant": query_variant,
                        }
                    )

            # Extract enhanced queries from query_info
            query_info = last_state.get("query_info") or {}
            enhanced_queries = query_info.get("enhanced_queries", [])
            strategy_used = query_info.get("strategy_used", "augmented")

            # Break response into chunks to avoid React update depth issues
            # Emit chunks of ~500 chars at a time
            chunk_size = 500
            for i in range(0, len(final_answer), chunk_size):
                chunk = final_answer[i : i + chunk_size]

                response_event = {
                    "type": "streaming_response",
                    "chunk": chunk,
                }

                # Add metadata only on first chunk
                if i == 0:
                    response_event["metadata"] = {
                        "source_links": source_links,  # Structured links with URL, title, and chunk_id
                        "document_count": len(retrieved_docs),
                        "enhancement_strategy": strategy_used,
                        "enhanced_queries": enhanced_queries,
                    }

                yield response_event

        # Yield final result with complete state
        if last_state:
            # FIRST: Extract metadata for the response message
            query_info = last_state.get("query_info", {})

            source_links = (
                []
            )  # Structured links with URL, title, chunk_id, and variant info
            retrieved_docs = last_state.get("retrieved_documents", [])
            for doc in retrieved_docs:
                source_url = doc.get("source_url")
                if source_url:
                    # Extract title, chunk_id, and variant info from document
                    title = doc.get("title") or doc.get("metadata", {}).get("title")
                    chunk_id = doc.get("chunk_id")
                    query_variant_index = doc.get("query_variant_index")
                    query_variant = doc.get("query_variant")
                    source_links.append(
                        {
                            "url": source_url,
                            "title": title or "Untitled Document",
                            "chunk_id": chunk_id or "",
                            "query_variant_index": query_variant_index,
                            "query_variant": query_variant,
                        }
                    )

            enhanced_queries = (
                query_info.get("enhanced_queries", []) if query_info else []
            )
            enhancement_strategy = (
                query_info.get("strategy_used", "augmented")
                if query_info
                else "augmented"
            )

            # Build final result with metadata included
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
                "metadata": {
                    "source_links": source_links,
                    "enhancement_strategy": enhancement_strategy,
                    "enhanced_queries": enhanced_queries,
                    "document_count": len(retrieved_docs),
                    "processing_time_ms": int(execution_time_ms),
                },
            }

            # Log workflow results summary
            if final_result.get("enhanced_query"):
                enhanced_query = final_result["enhanced_query"]

            # SAVE messages to conversation history
            try:
                # Extract the final response from state
                final_response = last_state.get("final_answer", "") or ""

                # Save user query message
                conversation_history_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="user",
                    content=query,
                )
                logger.info(
                    f"✅ [RAG] Saved user message to conversation {conversation_id}"
                )

                # Save assistant response message with metadata
                conversation_history_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=final_response,
                    source_links=source_links,
                    enhancement_strategy_used=enhancement_strategy,
                    enhanced_queries=enhanced_queries,
                    processing_time_ms=int(execution_time_ms),
                    document_count=len(retrieved_docs),
                )
                logger.info(
                    f"✅ [RAG] Saved assistant message to conversation {conversation_id} (response length: {len(final_response) if final_response else 0} chars)"
                )

            except Exception as e:
                logger.error(
                    f"❌ [RAG] FAILED to save messages to conversation {conversation_id}: {e}"
                )
                logger.error(f"Traceback: {traceback.format_exc()}")

            yield final_result
        else:
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
            f"Error: LangGraph workflow failed after {execution_time_ms:.2f}ms: {e}"
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
