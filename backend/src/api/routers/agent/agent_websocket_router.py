"""
Agent WebSocket Router - LangGraph Workflow Interface

This module provides WebSocket endpoints for real-time AI agent interactions
using the LangGraph workflow with query enhancement capabilities.
"""

import asyncio
import json
import time
import traceback
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger
from opik.integrations.langchain import OpikTracer

from src.api.routers.auth.auth_router import decode_access_token
from src.config import settings
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.conversation.generate_response import get_response_stream
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Workflow logic moved to generate_response service

router = APIRouter(tags=["Agent WebSocket"])


def extract_enhanced_query_text(enhanced_query_dict: dict, strategy: str = None) -> str:
    """
    Extract the actual enhanced query text from the enhanced_query dictionary.

    Args:
        enhanced_query_dict: Dictionary containing enhanced query data
        strategy: The enhancement strategy used

    Returns:
        The enhanced query as a string
    """
    if not enhanced_query_dict:
        return None

    logger.debug(
        f"📝 Extracting enhanced query text from dict keys: {list(enhanced_query_dict.keys())}, strategy: {strategy}"
    )

    # Try to extract based on known keys
    if "hypothetical_answer" in enhanced_query_dict:
        result = enhanced_query_dict["hypothetical_answer"]
        logger.debug(
            f"✅ Extracted hypothetical_answer: {result[:100] if result else None}..."
        )
        return result
    elif "multi_query_variants" in enhanced_query_dict:
        variants = enhanced_query_dict["multi_query_variants"]
        result = variants[0] if variants and len(variants) > 0 else None
        logger.debug(
            f"✅ Extracted multi_query_variants[0]: {result[:100] if result else None}..."
        )
        return result
    elif "augmented_queries" in enhanced_query_dict:
        augmented = enhanced_query_dict["augmented_queries"]
        # Return first variant after original (index 1), or first if only one
        result = (
            augmented[1]
            if augmented and len(augmented) > 1
            else (augmented[0] if augmented else None)
        )
        logger.debug(
            f"✅ Extracted augmented_queries[1]: {result[:100] if result else None}..."
        )
        return result
    elif "sub_queries" in enhanced_query_dict:
        sub_queries = enhanced_query_dict["sub_queries"]
        result = sub_queries[0] if sub_queries and len(sub_queries) > 0 else None
        logger.debug(
            f"✅ Extracted sub_queries[0]: {result[:100] if result else None}..."
        )
        return result
    elif "fusion_perspectives" in enhanced_query_dict:
        perspectives = enhanced_query_dict["fusion_perspectives"]
        result = perspectives[0] if perspectives and len(perspectives) > 0 else None
        logger.debug(
            f"✅ Extracted fusion_perspectives[0]: {result[:100] if result else None}..."
        )
        return result

    logger.warning(
        f"⚠️ Could not extract enhanced query from dict: {enhanced_query_dict}"
    )
    return None


@router.websocket("/ws/agent/query/rag")
async def agent_query_rag_websocket(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for RAG-only query processing (no supervisor/agent routing).

    This endpoint processes user queries using ONLY the RAG pipeline without any intent detection
    or task agent routing. It provides direct access to the knowledge base retrieval and answer
    generation pipeline.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database"
    }
    ```

    **Response Format** (to client - RAG events):
    ```json
    {
        "type": "workflow_progress",
        "stage": "query_enhancement|query_enhancement_complete|document_retrieval|document_retrieval_complete|document_judging|document_judging_complete|answer_generation|answer_generation_complete",
        "message": "Status message",
        "data": {},
        "execution_time_ms": 123.45
    }
    ```

    **Stages**:
    1. `query_enhancement` (START) - Beginning query enhancement
    2. `query_enhancement_complete` (COMPLETE) - Query enhanced with variants
    3. `document_retrieval` (START) - Beginning document retrieval
    4. `document_retrieval_complete` (COMPLETE) - Documents retrieved
    5. `document_judging` (START) - Beginning document ranking (if enabled)
    6. `document_judging_complete` (COMPLETE) - Documents ranked
    7. `answer_generation` (START) - Beginning answer generation
    8. `answer_generation_complete` (COMPLETE) - Response generated
    9. `workflow_complete` - Final result with complete response

    RAG-only mode is ideal for:
    - Pure knowledge base retrieval without task execution
    - Consistent, deterministic retrieval pipelines
    - Lower latency compared to supervisor with multiple agents
    """
    # Delegate to main handler with force_rag_only=True to force direct RAG mode
    await agent_query_websocket(websocket, token, force_rag_only=True)


@router.websocket("/ws/agent/query/supervisor")
async def agent_query_supervisor_websocket(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for AI agent query processing with SUPERVISOR MODE.

    This endpoint processes user queries through the multi-agent supervisor architecture,
    with intent detection and routing to RAG and/or Task agents.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database",
        "llm_provider_id": "provider_id_from_database",
        "llm_model_name": "model-name",
        "collection_name": "LongTermMemory"
    }
    ```

    **Response Format** (to client - supervisor events):
    ```json
    {
        "type": "supervisor_progress",
        "stage": "supervisor_init|intent_detection|rag_agent_executing|task_agent_executing|response_generation|completed",
        "message": "Status message",
        "data": {},
        "timestamp": "ISO timestamp"
    }
    ```
    """
    # Use the same handler but ensure enable_knowledge_assistant is True
    await agent_query_websocket(websocket, token, force_supervisor=True)


@router.websocket("/ws/agent/query")
async def agent_query_websocket(websocket: WebSocket, token: str = Query(None), force_supervisor: bool = False, force_rag_only: bool = False):
    """
    WebSocket endpoint for AI agent query processing.

    - If `enable_knowledge_assistant=True` in conversation settings: Routes to supervisor architecture (RAG + Task agents)
    - If `enable_knowledge_assistant=False` in conversation settings: Uses legacy RAG-only LangGraph workflow

    Recommended: Use `/ws/agent/query/supervisor` for supervisor mode (cleaner separation)

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "selected_strategy": "multi_query|hyde|decomposition|query_fusion",
        "llm_provider_id": "provider_id_from_database",
        "llm_model_name": "model-name",
        "collection_name": "LongTermMemory",
        "enhancement_config": {
            "query_enhancement": {
                "enabled": true,
                "timeout_seconds": 30
            }
        }
    }
    ```

    **Response Format** (to client):
    ```json
    {
        "stage": "query_enhancement|document_retrieval|response_generation|completed|error",
        "message": "Status message",
        "data": {},
        "timestamp": "ISO timestamp"
    }
    ```

    **Stages**:
    1. `starting` - Connection established, processing initiated
    2. `query_enhancement` - Enhancing query using selected strategy
    3. `document_retrieval` - Retrieving relevant documents
    4. `response_generation` - Generating AI response
    5. `streaming_response` - Streaming AI response chunks
    6. `completed` - Processing completed successfully
    7. `error` - Error occurred during processing
    """
    logger.info("Agent query WebSocket connection requested")

    # Validate JWT token
    timeout = settings.WEBSOCKET_TIMEOUT

    try:
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Decode and validate token
        payload = decode_access_token(token)
        user_id = payload.get("user_id")  # Use user_id (ObjectId), not sub (username)
        username = payload.get("sub")

        if not user_id:
            await websocket.close(code=1008, reason="Invalid token payload")
            return

        logger.debug(f"WebSocket auth: user_id={user_id}, username={username}")

    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    await websocket.accept()
    logger.info(
        f"Agent WebSocket connected for user: {user_id} with timeout: {timeout}"
    )

    try:
        while True:
            try:
                # Wait for message from client with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                msg = json.loads(data)

                # Extract ONLY query and conversation_id from UI
                query = msg.get("query")
                conversation_id = msg.get("conversation_id") or msg.get("session_id")

                # Initialize defaults
                llm_provider_id = None
                llm_model_name = None
                selected_strategy = None
                collection_name = None
                enhancement_config = {}
                enable_reranking = True
                enable_llm_generation = True
                top_k = 5
                enable_knowledge_assistant = True
                conversation_description = None

                # Load ALL settings from conversation (UI should NOT send these)
                if conversation_id:
                    try:
                        logger.debug(
                            f"Loading ALL conversation settings from conversation_id: {conversation_id}"
                        )
                        conversation = conversation_history_service.get_conversation(
                            conversation_id
                        )
                        if conversation:
                            logger.debug(f"Conversation found: {conversation.name}")
                            logger.debug(
                                f"Conversation user_id: {conversation.user_id}"
                            )
                            logger.debug(f"Current JWT user_id: {user_id}")

                            # Load ALL settings from conversation
                            llm_provider_id = conversation.llm_provider_id
                            llm_model_name = conversation.llm_model_name
                            collection_name = conversation.collection_name

                            # Load enhancement strategy
                            if conversation.enhancement_config:
                                selected_strategy = (
                                    conversation.enhancement_config.strategy
                                )

                            # Retrieval strategy is auto-detected at runtime based on query variants
                            # No need to load from conversation - always use None for auto-detection
                            retrieval_strategy = None

                            # Load reranking settings - DEBUG
                            logger.debug(
                                f"🔍 Conversation object type: {type(conversation)}"
                            )
                            logger.debug(
                                f"🔍 Conversation enable_reranking value: {getattr(conversation, 'enable_reranking', 'NOT FOUND')}"
                            )

                            enable_reranking = getattr(
                                conversation, "enable_reranking", True
                            )

                            # Load relevance threshold for reranking
                            relevance_threshold = getattr(
                                conversation, "relevance_threshold", 0.5
                            )

                            # Load LLM generation setting
                            enable_llm_generation = getattr(
                                conversation, "enable_llm_generation", True
                            )

                            # Load top_k setting
                            top_k = getattr(conversation, "top_k", None)
                            if top_k is None:
                                logger.warning(
                                    f"⚠️ Conversation {conversation_id} has no top_k setting, using default 5"
                                )
                                top_k = 5

                            # Load supervisor setting
                            enable_knowledge_assistant = getattr(
                                conversation, "enable_knowledge_assistant", True
                            )

                            # Override if force_rag_only is set (from /ws/agent/query/rag endpoint)
                            if force_rag_only:
                                enable_knowledge_assistant = False
                                logger.info(
                                    f"🔄 Force RAG-only mode: overriding enable_knowledge_assistant=False"
                                )

                            logger.debug(
                                f"🤖 Supervisor setting: enable_knowledge_assistant={enable_knowledge_assistant}"
                            )

                            # Load conversation description for query enhancement context
                            conversation_description = getattr(
                                conversation, "description", None
                            )
                            if conversation_description:
                                logger.debug(
                                    f"📝 Loaded conversation description: '{conversation_description[:50]}...'"
                                )

                            logger.info(
                                f"📋 Loaded ALL settings from conversation: provider={llm_provider_id}, model={llm_model_name}, strategy={selected_strategy}, collection={collection_name}, reranking={enable_reranking}, llm_generation={enable_llm_generation}, top_k={top_k}, has_description={bool(conversation_description)}"
                            )
                        else:
                            error_msg = f"Conversation not found: {conversation_id}"
                            logger.error(f"❌ {error_msg}")
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "stage": "error",
                                        "message": "Conversation not found. Please refresh and try again.",
                                        "timestamp": time.time(),
                                    }
                                )
                            )
                            continue
                    except Exception as e:
                        error_msg = f"Failed to load conversation settings: {str(e)}"
                        logger.error(f"❌ {error_msg}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "error",
                                    "message": f"Error loading conversation: {str(e)}",
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                # Validate required fields
                if not query or not query.strip():
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": "Query is required",
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                if not llm_provider_id:
                    error_msg = "LLM provider ID is required. Please configure a provider for this conversation."
                    logger.error(
                        f"❌ {error_msg} - conversation_id: {conversation_id}, user: {user_id}"
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": error_msg,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                logger.info(
                    f"Processing agent query: '{query[:50]}...' "
                    f"with strategy: {selected_strategy}, provider: {llm_provider_id}"
                )

                # Send initial status
                await websocket.send_text(
                    json.dumps(
                        {
                            "stage": "starting",
                            "message": f"Processing query: {query[:100]}...",
                            "data": {
                                "query": query,
                                "strategy": selected_strategy,
                                "provider_id": llm_provider_id,
                            },
                            "timestamp": time.time(),
                        }
                    )
                )

                # Resolve LLM provider configuration
                try:
                    provider_service = get_model_provider_service()
                    logger.debug(
                        f"Looking up provider ID: {llm_provider_id} for user: {user_id}"
                    )
                    provider = provider_service.get_model_provider(
                        llm_provider_id, user_id
                    )

                    if not provider:
                        error_msg = f"LLM provider not found: {llm_provider_id}"
                        logger.error(f"❌ {error_msg} for user: {user_id}")
                        logger.error(
                            f"This could mean: 1) Provider was deleted, 2) Provider belongs to different user, 3) Invalid provider ID"
                        )

                        # Try to get all providers for this user to help debug
                        try:
                            all_providers = provider_service.list_model_providers(
                                user_id
                            )
                            logger.error(
                                f"Available providers for user {user_id}: {[(p.id, p.name) for p in all_providers]}"
                            )
                        except Exception as debug_e:
                            logger.error(
                                f"Could not list available providers: {debug_e}"
                            )

                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "error",
                                    "message": error_msg,
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                    if not provider.is_active:
                        error_msg = f"LLM provider is not active: {provider.name}"
                        logger.error(
                            f"❌ {error_msg} - provider_id: {llm_provider_id}, user: {user_id}"
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "error",
                                    "message": error_msg,
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                    logger.info(
                        f"Using LLM provider: {provider.name} ({provider.provider_type})"
                    )

                    # Pass provider ID and model name to workflow
                    llm_provider_id = provider.id
                    llm_model_name = llm_model_name or provider.generative.default_model

                except Exception as e:
                    error_msg = f"Failed to configure LLM provider: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": error_msg,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # Workflow state creation is now handled in get_response function

                # Execute LangGraph workflow with streaming
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "workflow_started",
                                "message": "Starting LangGraph workflow...",
                                "data": {"strategy": selected_strategy or "native"},
                                "timestamp": time.time(),
                            }
                        )
                    )

                    # Execute workflow using the streaming generate_response service
                    stream = get_response_stream(
                        query=query,
                        user_id=user_id,
                        llm_provider_id=llm_provider_id,
                        llm_model_name=llm_model_name,
                        conversation_id=conversation_id,
                        collection_name=collection_name,
                        selected_strategy=selected_strategy,
                        retrieval_strategy=retrieval_strategy,
                        enhancement_config=enhancement_config,
                        enable_reranking=enable_reranking,
                        relevance_threshold=relevance_threshold,
                        enable_llm_generation=enable_llm_generation,
                        top_k=top_k,
                        enable_knowledge_assistant=enable_knowledge_assistant,
                        conversation_description=conversation_description,
                    )

                    # Variables to track workflow state
                    final_response = ""
                    documents = []
                    enhanced_query = None
                    enhanced_queries = None  # Array of all enhanced query variants
                    last_node = None

                    # Iterate over workflow stream chunks
                    async for chunk in stream:
                        chunk_type = chunk.get("type", "unknown")
                        current_node = chunk.get("current_node", "unknown")

                        # Handle supervisor and workflow progress events
                        if chunk_type in [
                            "supervisor_started",
                            "supervisor_progress",
                            "workflow_progress",
                        ]:
                            logger.info(
                                f"📡 Forwarding event: type={chunk_type}, stage={chunk.get('stage')}, message={chunk.get('message')}"
                            )
                            logger.debug(f"📡 Full event payload: {json.dumps(chunk)}")
                            await websocket.send_text(json.dumps(chunk))
                            logger.info(f"✅ Event sent to client successfully")
                            continue

                        # Track the state changes
                        if current_node != last_node and current_node != "unknown":
                            last_node = current_node
                            logger.info(f"🔄 Node changed to: {current_node}")

                            # Map node names to user-friendly stage names and messages
                            node_info = {
                                "multi_query_strategy_node": {
                                    "stage": "query_enhancement",
                                    "message": "🔍 Enhancing query (Multi-Query strategy)...",
                                    "description": "Creating alternative phrasings",
                                },
                                "hyde_strategy_node": {
                                    "stage": "query_enhancement",
                                    "message": "🔍 Enhancing query (HyDE strategy)...",
                                    "description": "Generating hypothetical answers",
                                },
                                "decomposition_strategy_node": {
                                    "stage": "query_enhancement",
                                    "message": "🔍 Enhancing query (Decomposition strategy)...",
                                    "description": "Breaking down into sub-questions",
                                },
                                "augmented_strategy_node": {
                                    "stage": "query_enhancement",
                                    "message": "🔍 Enhancing query (Augmented strategy)...",
                                    "description": "Combining original with enhanced variants",
                                },
                                "document_retriever": {
                                    "stage": "document_retrieval",
                                    "message": "📚 Searching knowledge base...",
                                    "description": "Retrieving relevant documents",
                                },
                                "document_judger": {
                                    "stage": "document_judging",
                                    "message": "⚖️ Evaluating document relevance...",
                                    "description": "Judging and ranking retrieved documents",
                                },
                                "answer_generator": {
                                    "stage": "response_generation",
                                    "message": "✨ Generating answer...",
                                    "description": "Synthesizing final response",
                                },
                                "raw_response_formatter": {
                                    "stage": "raw_response_formatting",
                                    "message": "📋 Formatting raw results...",
                                    "description": "Preparing unmodified documents",
                                },
                            }

                            info = node_info.get(
                                current_node,
                                {
                                    "stage": "processing",
                                    "message": f"⚙️ Processing {current_node}...",
                                    "description": "Working on your query",
                                },
                            )

                            # Send stage update
                            stage_data = {
                                "node": current_node,
                                "description": info["description"],
                                "execution_time_ms": chunk.get("execution_time_ms", 0),
                            }

                            # Include strategy for all messages (especially query_enhancement)
                            if selected_strategy:
                                stage_data["strategy"] = selected_strategy

                            # ALWAYS extract enhanced_queries as ARRAY (never single string)
                            enhanced_query_dict = chunk.get("enhanced_query")
                            if enhanced_query_dict and isinstance(
                                enhanced_query_dict, dict
                            ):
                                # Extract array based on strategy
                                if enhanced_query_dict.get("augmented_queries"):
                                    stage_data["enhanced_queries"] = (
                                        enhanced_query_dict["augmented_queries"]
                                    )
                                elif enhanced_query_dict.get("multi_query_variants"):
                                    stage_data["enhanced_queries"] = (
                                        enhanced_query_dict["multi_query_variants"]
                                    )
                                elif enhanced_query_dict.get("fusion_perspectives"):
                                    stage_data["enhanced_queries"] = (
                                        enhanced_query_dict["fusion_perspectives"]
                                    )
                                elif enhanced_query_dict.get("sub_queries"):
                                    stage_data["enhanced_queries"] = (
                                        enhanced_query_dict["sub_queries"]
                                    )
                                elif enhanced_query_dict.get("hypothetical_answer"):
                                    # Single answer → array
                                    stage_data["enhanced_queries"] = [
                                        enhanced_query_dict["hypothetical_answer"]
                                    ]

                                logger.info(
                                    f"📤 Sending enhanced_queries for {info['stage']}: {stage_data.get('enhanced_queries')}"
                                )

                            # Include document count if available
                            if chunk.get("retrieved_documents"):
                                stage_data["document_count"] = len(
                                    chunk["retrieved_documents"]
                                )

                            # Log enhanced queries being sent
                            if stage_data.get("enhanced_queries"):
                                logger.info(
                                    f"📤 Sending enhanced_queries during {info['stage']}: {stage_data['enhanced_queries']}"
                                )

                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "stage": info["stage"],
                                        "message": info["message"],
                                        "data": stage_data,
                                        "timestamp": time.time(),
                                    }
                                )
                            )

                        # Handle progress chunks
                        if chunk_type == "workflow_progress":
                            # Update tracked variables
                            if chunk.get("enhanced_query"):
                                enhanced_query_text = extract_enhanced_query_text(
                                    chunk["enhanced_query"], selected_strategy
                                )
                                if enhanced_query_text:
                                    enhanced_query = enhanced_query_text

                            if chunk.get("retrieved_documents"):
                                documents = chunk["retrieved_documents"]

                                # Send document retrieval update
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "stage": "document_retrieval_complete",
                                            "message": f"Retrieved {len(documents)} relevant documents",
                                            "data": {
                                                "document_count": len(documents),
                                                "documents": documents[
                                                    :5
                                                ],  # First 5 for preview
                                            },
                                            "timestamp": time.time(),
                                        }
                                    )
                                )

                            # Handle judged documents from judge ranker
                            if chunk.get("judged_documents"):
                                judged_docs = chunk["judged_documents"]
                                relevance_scores = chunk.get("relevance_scores", [])
                                relevance_threshold = chunk.get(
                                    "relevance_threshold", 0.5
                                )

                                # Count relevant documents (those above threshold)
                                relevant_count = sum(
                                    1
                                    for score in relevance_scores
                                    if score >= relevance_threshold
                                )

                                logger.info(
                                    f"📊 Judge Ranker complete: {len(judged_docs)} evaluated, {relevant_count} relevant (threshold: {relevance_threshold})"
                                )

                                # Send judge ranker update
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "stage": "judge_ranker_complete",
                                            "message": f"Evaluated {len(judged_docs)} documents, {relevant_count} ranked as relevant",
                                            "data": {
                                                "document_count": len(judged_docs),
                                                "relevant_count": relevant_count,
                                                "documents": judged_docs[
                                                    :5
                                                ],  # First 5 for preview
                                            },
                                            "timestamp": time.time(),
                                        }
                                    )
                                )

                            if chunk.get("final_answer"):
                                final_response = chunk["final_answer"]

                                # Stream response word by word for better UX (like ChatGPT)
                                if final_response:
                                    words = final_response.split()
                                    accumulated_text = ""

                                    for word_idx, word in enumerate(words):
                                        accumulated_text += word + (
                                            " " if word_idx < len(words) - 1 else ""
                                        )

                                        await websocket.send_text(
                                            json.dumps(
                                                {
                                                    "stage": "streaming_response",
                                                    "message": "Streaming response...",
                                                    "data": {
                                                        "chunk": word + " ",
                                                        "accumulated": accumulated_text,
                                                        "chunk_index": word_idx,
                                                        "total_words": len(words),
                                                        "is_complete": False,
                                                    },
                                                    "timestamp": time.time(),
                                                }
                                            )
                                        )
                                        # Small delay for smooth streaming effect
                                        await asyncio.sleep(0.03)

                        # Handle completion
                        elif chunk_type == "workflow_complete":
                            final_response = chunk.get("response", "")
                            documents = chunk.get("documents", [])

                            # Extract query_info if available (contains enhanced_query and enhanced_queries)
                            query_info = chunk.get("query_info", {})
                            logger.info(f"🔍 DEBUG: chunk keys: {list(chunk.keys())}")
                            logger.info(
                                f"🔍 DEBUG: query_info keys: {list(query_info.keys()) if query_info else 'None'}"
                            )
                            logger.info(f"🔍 DEBUG: query_info content: {query_info}")

                            # Get enhanced_queries array from query_info - ALWAYS as array
                            enhanced_queries = (
                                query_info.get("enhanced_queries")
                                if query_info
                                else None
                            )

                            # ALWAYS ensure we have enhanced_queries as an array
                            if not enhanced_queries or not isinstance(
                                enhanced_queries, list
                            ):
                                # Fallback to original query (native strategy or missing data)
                                enhanced_queries = [query]
                                logger.info(
                                    f"⚠️ No enhanced_queries found, using original query as array: {enhanced_queries}"
                                )
                            else:
                                logger.info(
                                    f"✅ enhanced_queries from query_info: {enhanced_queries}"
                                )

                            # Stream final response if not already streamed
                            if final_response and not chunk.get("already_streamed"):
                                chunk_size = 50
                                for i in range(0, len(final_response), chunk_size):
                                    response_chunk = final_response[i : i + chunk_size]
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "stage": "streaming_response",
                                                "message": "Streaming response...",
                                                "data": {
                                                    "chunk": response_chunk,
                                                    "chunk_index": i // chunk_size,
                                                    "total_length": len(final_response),
                                                },
                                                "timestamp": time.time(),
                                            }
                                        )
                                    )
                                    await asyncio.sleep(0.01)

                        # Handle errors
                        elif chunk_type == "workflow_error":
                            error_msg = chunk.get("error", "Unknown error")
                            logger.error(f"❌ Workflow error: {error_msg}")

                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "stage": "error",
                                        "message": f"Error: {error_msg}",
                                        "data": {
                                            "error": error_msg,
                                            "execution_time_ms": chunk.get(
                                                "execution_time_ms", 0
                                            ),
                                        },
                                        "timestamp": time.time(),
                                    }
                                )
                            )

                            # Use error response as final response
                            final_response = chunk.get("response", "")

                    # Extract metadata from documents
                    source_urls = []
                    correlation_ids = []
                    chunk_ids = []

                    for i, doc in enumerate(documents, 1):
                        if isinstance(doc, dict):
                            # Check both direct fields and metadata
                            source_url = doc.get("source_url") or doc.get(
                                "metadata", {}
                            ).get("source_url")
                            correlation_id = doc.get("correlation_id") or doc.get(
                                "metadata", {}
                            ).get("correlation_id")
                            chunk_id = doc.get("chunk_id") or doc.get(
                                "metadata", {}
                            ).get("chunk_id")

                            if source_url:
                                source_urls.append(source_url)
                            if correlation_id:
                                correlation_ids.append(correlation_id)
                            if chunk_id:
                                chunk_ids.append(chunk_id)
                        elif hasattr(doc, "metadata"):
                            # For document objects, check metadata
                            if doc.metadata.get("source_url"):
                                source_urls.append(doc.metadata["source_url"])
                            if doc.metadata.get("correlation_id"):
                                correlation_ids.append(doc.metadata["correlation_id"])
                            if doc.metadata.get("chunk_id"):
                                chunk_ids.append(doc.metadata["chunk_id"])
                        elif hasattr(doc, "source_url"):
                            # For document objects with direct fields
                            if doc.source_url:
                                source_urls.append(doc.source_url)
                            if hasattr(doc, "correlation_id") and doc.correlation_id:
                                correlation_ids.append(doc.correlation_id)
                            if hasattr(doc, "chunk_id") and doc.chunk_id:
                                chunk_ids.append(doc.chunk_id)

                    # Send completion message with ONLY enhanced_queries (array)
                    completion_data = {
                        "query": query,
                        "response": final_response,
                        "document_count": len(documents),
                        "enhancement_strategy": selected_strategy,
                        "enhanced_queries": enhanced_queries,  # ALWAYS array, never single string
                        "source_urls": source_urls,
                        "correlation_ids": correlation_ids,
                        "chunk_ids": chunk_ids,
                    }

                    logger.info(
                        f"📤 SENDING enhanced_queries (array): {enhanced_queries}"
                    )

                    logger.info(
                        f"📦 COMPLETION DATA KEYS: {list(completion_data.keys())}"
                    )
                    logger.info(
                        f"📦 completion_data['enhancement_strategy']: {completion_data.get('enhancement_strategy')}"
                    )

                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "completed",
                                "message": "Query processing completed successfully",
                                "data": completion_data,
                                "timestamp": time.time(),
                            }
                        )
                    )

                    logger.info(
                        f"✅ Agent query completed successfully for user {user_id}: "
                        f"'{query[:50]}...' -> {len(final_response)} chars"
                    )

                    # Save to conversation history if conversation_id provided
                    if conversation_id:
                        try:
                            from datetime import datetime

                            from src.services.conversation.conversation_history_service import (
                                ConversationMessage,
                            )

                            # Create user message
                            user_message = ConversationMessage(
                                role="user",
                                content=query,
                                timestamp=datetime.utcnow(),
                                search_query=query,
                            )

                            # Create assistant message
                            assistant_message = ConversationMessage(
                                role="assistant",
                                content=final_response,
                                timestamp=datetime.utcnow(),
                                enhancement_strategy_used=selected_strategy,
                                document_count=len(documents),
                            )

                            # Save messages
                            conversation_history_service.add_message(
                                conversation_id, user_message
                            )
                            conversation_history_service.add_message(
                                conversation_id, assistant_message
                            )

                            logger.info(
                                f"💾 Saved conversation messages to session: {conversation_id}"
                            )
                        except Exception as save_error:
                            logger.error(
                                f"Failed to save conversation history: {save_error}"
                            )
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            # Don't fail the whole request if history save fails

                except Exception as e:
                    error_type = type(e).__name__
                    error_details = str(e)
                    logger.error(
                        f"❌ Error executing workflow: {error_type}: {error_details}"
                    )
                    logger.error(f"Traceback: {traceback.format_exc()}")

                    # Create user-friendly error message
                    user_message = "An error occurred while processing your query."
                    if "provider not found" in error_details.lower():
                        user_message = "LLM provider configuration error. Please check your settings."
                    elif (
                        "collection" in error_details.lower()
                        or "milvus" in error_details.lower()
                    ):
                        user_message = "Vector database error. Please try again or contact support."
                    elif "embedding" in error_details.lower():
                        user_message = "Error generating embeddings. Please check your provider configuration."
                    elif "timeout" in error_details.lower():
                        user_message = "Request timed out. Please try again."

                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": user_message,
                                "data": {
                                    "error_type": error_type,
                                    "error_details": error_details,
                                    "technical_message": f"{error_type}: {error_details}",
                                },
                                "timestamp": time.time(),
                            }
                        )
                    )

            except WebSocketDisconnect:
                logger.info(f"Agent WebSocket disconnected for user: {user_id}")
                return

            except asyncio.TimeoutError:
                logger.info(f"Agent WebSocket timeout for user: {user_id}")
                await websocket.close(code=1000, reason="Connection timeout")
                return

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "stage": "error",
                            "message": "Invalid JSON format",
                            "timestamp": time.time(),
                        }
                    )
                )

            except Exception as e:
                logger.error(f"Error processing agent query: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": f"Processing failed: {str(e)}",
                                "timestamp": time.time(),
                            }
                        )
                    )
                except Exception:
                    # Connection might be closed
                    return

    except asyncio.TimeoutError:
        logger.info(f"Agent WebSocket timeout for user: {user_id}")
        await websocket.close(code=1000, reason="Connection timeout")
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return

    except WebSocketDisconnect:
        logger.info(f"Agent WebSocket disconnected for user: {user_id}")
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return

    except Exception as e:
        logger.error(f"Agent WebSocket error for user {user_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return
