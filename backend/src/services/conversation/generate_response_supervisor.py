"""
Generate Response Service for Supervisor Agent Mode

This module handles the execution of the multi-agent supervisor orchestration
for generating AI responses with intent routing and task execution.
"""

import asyncio
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

import litellm
from langchain_community.chat_models import ChatLiteLLM
from loguru import logger
from opik.integrations.langchain import OpikTracer
from opik.integrations.litellm import track_litellm

from src.agents.common.agent_state import AgentState
from src.agents.rag_agent.graph import graph_dev as workflow
from src.agents.rag_agent.state import RAGWorkflowState as WorkflowState
from src.agents.rag_agent.state import create_initial_state
from src.config import settings
from src.domain.conversation import ConversationMessage
from src.orchestration.orchestrator import create_multi_agent_orchestrator
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Enable dropping unsupported params for different LLM providers
# (e.g., GPT-5 only supports temperature=1, not 0.7)
litellm.drop_params = True


async def get_response_stream_supervisor(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
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
    selected_system_prompt_id: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using Supervisor Agent for intent routing (streaming).

    **SUPERVISOR MODE ONLY** - This endpoint uses the multi-agent supervisor architecture
    with intent detection and routing to RAG and/or Task agents.

    Yields:
        Dict containing workflow state chunks with progress updates
    """
    start_time = time.time()

    try:

        # Yield supervisor initialization START event
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing supervisor agent orchestration",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # Initialize workflow config (same as RAG function)
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
                "use_score_based": True,
            },
            "enable_llm_generation": enable_llm_generation,
            "top_k": top_k,
            "retrieval_config": {
                "top_k_per_query": top_k_per_query,
                "rrf_k": 60,
            },
        }

        logger.info(
            f"🔧 Supervisor Config: enable_reranking={enable_reranking}, enable_llm_generation={enable_llm_generation}, collection={collection_name}, strategy={selected_strategy}"
        )

        # Auto-set strategy to decomposition for supervisor mode
        # Decomposition breaks complex queries into sub-queries for comprehensive knowledge retrieval
        original_strategy = selected_strategy
        if selected_strategy != "decomposition":
            selected_strategy = "decomposition"
            logger.info(
                f"🔄 [SUPERVISOR MODE] Auto-changing enhancement strategy: '{original_strategy or 'native'}' → 'decomposition'"
            )
            logger.info(
                "📋 [SUPERVISOR MODE] Reason: Decomposition provides optimal query breakdown for multi-concept task execution"
            )

            # Notify user about strategy change
            yield {
                "type": "supervisor_progress",
                "stage": "strategy_auto_adjusted",
                "message": f"Enhancement strategy automatically set to 'decomposition' for optimal multi-concept query handling (original: '{original_strategy or 'native'}')",
                "data": {
                    "original_strategy": original_strategy or "native",
                    "new_strategy": "decomposition",
                    "reason": "Supervisor mode benefits from query decomposition to identify and retrieve all relevant concepts before task execution",
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Retrieve selected system prompt if provided (Phase 1)
        selected_system_prompt = None
        if selected_system_prompt_id:
            try:
                selected_system_prompt = conversation_history_service.get_system_prompt(
                    conversation_id=conversation_id,
                    prompt_id=selected_system_prompt_id,
                    user_id=user_id,
                )
                if selected_system_prompt:
                    logger.info(
                        f"📝 [SUPERVISOR] Using system prompt: '{selected_system_prompt.name}'"
                    )
                    # Add to workflow config for agent access
                    workflow_config["selected_system_prompt"] = selected_system_prompt
                else:
                    logger.warning(
                        f"⚠️ [SUPERVISOR] System prompt not found: {selected_system_prompt_id}"
                    )
            except Exception as e:
                logger.error(f"⚠️ [SUPERVISOR] Error retrieving system prompt: {e}")

        # Get provider configuration to create LLM client
        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(llm_provider_id, user_id)

        if not provider:
            raise ValueError(f"Provider not found: {llm_provider_id}")

        if not provider.is_active:
            raise ValueError(f"Provider is not active: {provider.name}")

        # Get temperature and max_tokens from provider's generative config
        generative_config = provider.generative.config if provider.generative else {}
        temperature = generative_config.get("temperature", 0.7)
        max_tokens = generative_config.get("max_tokens", 4096)

        # Create LLM client using ChatLiteLLM with provider's config
        model_string = f"{provider.provider_type}/{llm_model_name}"
        llm_client = ChatLiteLLM(
            model=model_string,
            api_key=provider.api_key,
            api_base=provider.endpoint if provider.endpoint else None,
            timeout=provider.timeout if provider.timeout else 60,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"✅ Created LLM client: {model_string} (temperature={temperature}, max_tokens={max_tokens})"
        )

        # Add LLM client to workflow config
        workflow_config["llm_client"] = llm_client

        logger.info("🤖 Using Supervisor orchestration with multi-agent routing")

        # Create multi-agent orchestrator
        supervisor = create_multi_agent_orchestrator(
            llm_client=llm_client,
            rag_graph=workflow,
            conversation_service=None,  # Optional conversation service
        )

        # Create initial state for supervisor
        supervisor_initial_state = AgentState(
            messages=[{"role": "user", "content": query}],
            conversation_id=conversation_id,
            user_id=user_id,
            config=workflow_config,
            conversation_description=conversation_description,  # Pass collection description for Task Agent enrichment
        )

        # Add system prompt to state if selected (Phase 1 integration)
        if selected_system_prompt:
            supervisor_initial_state["system_prompt_task"] = selected_system_prompt
            logger.info(
                f"📝 [SUPERVISOR] System prompt added to state: '{selected_system_prompt.name}'"
            )

        if conversation_description:
            logger.info(
                f"📝 [SUPERVISOR] Conversation description included: {conversation_description[:100]}..."
            )

        # Yield supervisor initialization COMPLETE event
        yield {
            "type": "supervisor_progress",
            "stage": "supervisor_init_complete",
            "message": "Supervisor orchestration initialized successfully",
            "data": {
                "orchestrator_type": "multi_agent",
                "agents_available": ["rag_agent", "task_agent"],
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        logger.info("📊 Supervisor: Detecting user intent...")

        # Yield intent detection START event
        yield {
            "type": "supervisor_progress",
            "stage": "intent_detection",
            "message": "Analyzing user query to determine routing strategy",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        intent_detection_start = time.time()

        # Detect intent first (fast, separate from execution)
        detected_intent = await supervisor._detect_intent(supervisor_initial_state)
        logger.info(f"✅ Supervisor: Intent detected as '{detected_intent}'")

        # Map intent to human-readable description
        intent_descriptions = {
            "rag_only": "Knowledge retrieval only - User needs information from documents",
            "rag_then_task": "Knowledge retrieval + Task execution - User needs information and action",
            "task_only": "Direct task execution - User needs action without prior knowledge",
        }

        # Yield intent detection COMPLETE event
        yield {
            "type": "supervisor_progress",
            "stage": "intent_detection_complete",
            "message": f"Intent detected: {detected_intent}",
            "data": {
                "intent": detected_intent,
                "intent_description": intent_descriptions.get(
                    detected_intent, "Unknown intent"
                ),
                "routing_decision": (
                    "rag_agent"
                    if detected_intent in ["rag_only", "rag_then_task"]
                    else "task_agent"
                ),
                "detection_time_ms": (time.time() - intent_detection_start) * 1000,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Set intent in state
        supervisor_initial_state["intent"] = detected_intent

        # Execute agents based on detected intent
        result_state = supervisor_initial_state

        # Execute RAG Agent if needed
        if detected_intent in ["rag_only", "rag_then_task"]:
            logger.info("📚 Supervisor: Routing to RAG Agent...")

            # Yield RAG Agent START event
            yield {
                "type": "supervisor_progress",
                "stage": "rag_agent_executing",
                "message": "Executing RAG Agent - retrieving and ranking documents",
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

            rag_start = time.time()

            # Stream RAG graph execution to emit node progress in real-time
            rag_config = result_state.get("config", {}) or {}
            rag_state_input = create_initial_state(
                query=result_state.get("messages", [])[-1].get("content", ""),
                top_k=rag_config.get("top_k", 5),
                config=rag_config,
                selected_strategy=selected_strategy,  # FIX: Pass the strategy explicitly!
                conversation_description=result_state.get("conversation_description"),
            )

            rag_result = None
            logger.info(f"🔍 [SUPERVISOR RAG] Starting RAG graph streaming...")

            # Only emit query enhancement if a strategy is configured (not native)
            if selected_strategy and selected_strategy != "native":
                yield {
                    "type": "workflow_progress",
                    "stage": "query_enhancement",
                    "message": "Enhancing query...",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            # Track RAG execution details to include in complete event
            rag_enhanced_queries = []
            rag_enhancement_strategy = selected_strategy or "native"

            # Track emitted stages to avoid duplicates
            rag_stages_emitted = set()

            # Initialize document counts (will be updated from events)
            total_docs = 0
            relevant_docs = 0

            # Stream through RAG graph events - emit START and COMPLETE events
            # Using astream_events() gives us better event metadata like in RAG mode
            rag_config_for_events = {"configurable": {"thread_id": str(start_time)}}

            async for event in supervisor.rag_agent.rag_graph.astream_events(
                input=rag_state_input, config=rag_config_for_events, version="v2"
            ):
                event_type = event.get("event", "")
                node_name = event.get("name", "")
                event_data = event.get("data", {})

                # Capture final state when workflow completes
                # With version="v2", the final state comes from on_chain_end for LangGraph node
                if event_type == "on_chain_end" and node_name == "LangGraph":
                    logger.critical(
                        f"🔴 [SUPERVISOR RAG] LangGraph on_chain_end event received - THIS IS THE FINAL STATE!"
                    )
                    logger.critical(
                        f"🔴 [SUPERVISOR RAG] event_data type: {type(event_data)}"
                    )

                    # Extract output from event_data
                    if hasattr(event_data, "output"):
                        rag_result = event_data.output
                        logger.critical(
                            f"🔴 [SUPERVISOR RAG] Extracted from event_data.output"
                        )
                    elif isinstance(event_data, dict) and "output" in event_data:
                        rag_result = event_data["output"]
                        logger.critical(
                            f"🔴 [SUPERVISOR RAG] Extracted from event_data['output']"
                        )
                    elif isinstance(event_data, dict):
                        rag_result = event_data
                        logger.critical(
                            f"🔴 [SUPERVISOR RAG] Using event_data directly as dict"
                        )
                    else:
                        rag_result = {}
                        logger.critical(
                            f"🔴 [SUPERVISOR RAG] Could not extract output, using empty dict"
                        )

                    logger.critical(
                        f"🔴 [SUPERVISOR RAG] rag_result type: {type(rag_result)}"
                    )
                    if isinstance(rag_result, dict):
                        logger.critical(
                            f"🔴 [SUPERVISOR RAG] rag_result has {len(rag_result)} keys: {list(rag_result.keys())[:10]}"
                        )
                    continue

                # Handle node END events to extract output data
                if event_type == "on_chain_end":
                    logger.info(f"📊 [SUPERVISOR RAG] Node completed: {node_name}")

                    # Extract the node output from the event
                    if hasattr(event_data, "output"):
                        node_output = event_data.output
                    elif isinstance(event_data, dict) and "output" in event_data:
                        node_output = event_data["output"]
                    else:
                        node_output = event_data

                    # Log node output for debugging
                    if isinstance(node_output, dict):
                        logger.debug(
                            f"🔍 [SUPERVISOR RAG NODE OUTPUT] {node_name} keys: {list(node_output.keys())}"
                        )

                    # Map node names to substage events
                    if node_name in [
                        "multi_query_strategy_node",
                        "hyde_strategy_node",
                        "decomposition_strategy_node",
                        "augmented_strategy_node",
                    ]:
                        if "query_enhancement" not in rag_stages_emitted:
                            # START event
                            yield {
                                "type": "workflow_progress",
                                "stage": "query_enhancement",
                                "message": "Enhancing query...",
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }
                            rag_stages_emitted.add("query_enhancement")

                            # COMPLETE event with data
                            if isinstance(node_output, dict):
                                # Try multiple possible structures for enhanced queries
                                enhanced_queries = (
                                    node_output.get("enhanced_query", {}).get(
                                        "variants", []
                                    )
                                    if node_output.get("enhanced_query")
                                    else []
                                )

                                # If not found, try direct variants key
                                if not enhanced_queries:
                                    enhanced_queries = node_output.get("variants") or []

                                # If still not found, try augmented_queries (used by augmented strategy)
                                if not enhanced_queries:
                                    enhanced_queries = (
                                        node_output.get("augmented_queries") or []
                                    )

                                # If still not found, try sub_queries (used by decomposition strategy)
                                if not enhanced_queries:
                                    enhanced_queries = (
                                        node_output.get("sub_queries") or []
                                    )

                                # If still not found, try multi_query_variants (used by multi-query strategy)
                                if not enhanced_queries:
                                    enhanced_queries = (
                                        node_output.get("multi_query_variants") or []
                                    )

                                # Ensure enhanced_queries is always a list, never None
                                if enhanced_queries is None:
                                    enhanced_queries = []

                                logger.info(
                                    f"📊 [SUPERVISOR] Query enhancement output: {node_output.keys()}"
                                )
                                logger.info(
                                    f"📊 [SUPERVISOR] Extracted {len(enhanced_queries)} enhanced queries: {enhanced_queries[:2] if enhanced_queries else 'NONE'}"
                                )
                            else:
                                enhanced_queries = []

                            strategy_name = node_name.replace("_strategy_node", "")

                            # Store for later inclusion in rag_agent_executing_complete event
                            rag_enhanced_queries = enhanced_queries
                            rag_enhancement_strategy = strategy_name

                            yield {
                                "type": "workflow_progress",
                                "stage": "query_enhancement_complete",
                                "message": f"Query enhanced with {len(enhanced_queries)} variants",
                                "data": {
                                    "strategy": strategy_name,
                                    "query_variants": enhanced_queries,
                                    "variant_count": len(enhanced_queries),
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                    elif node_name == "document_retriever":
                        if "document_retrieval" not in rag_stages_emitted:
                            # START event
                            yield {
                                "type": "workflow_progress",
                                "stage": "document_retrieval",
                                "message": "Retrieving documents...",
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }
                            rag_stages_emitted.add("document_retrieval")

                            # COMPLETE event with data
                            if isinstance(node_output, dict):
                                retrieved_docs = node_output.get(
                                    "retrieved_documents", []
                                )
                            else:
                                retrieved_docs = []

                            # Update total_docs count
                            total_docs = len(retrieved_docs)

                            yield {
                                "type": "workflow_progress",
                                "stage": "document_retrieval_complete",
                                "message": f"Retrieved {len(retrieved_docs)} documents",
                                "data": {
                                    "document_count": len(retrieved_docs),
                                    "collection": rag_config.get(
                                        "collection_name", "unknown"
                                    ),
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                    elif node_name == "document_judger":
                        # Only emit if reranking is enabled
                        if (
                            enable_reranking
                            and "document_judging" not in rag_stages_emitted
                        ):
                            # START event
                            yield {
                                "type": "workflow_progress",
                                "stage": "document_judging",
                                "message": "Ranking documents...",
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }
                            rag_stages_emitted.add("document_judging")

                            # COMPLETE event with data
                            if isinstance(node_output, dict):
                                judged_docs = node_output.get("judged_documents", [])
                                relevance_scores = node_output.get(
                                    "relevance_scores", []
                                )
                            else:
                                judged_docs = []
                                relevance_scores = []

                            relevant_count = len(
                                [s for s in relevance_scores if s >= 0.5]
                            )

                            # Update relevant_docs count
                            relevant_docs = relevant_count

                            yield {
                                "type": "workflow_progress",
                                "stage": "document_judging_complete",
                                "message": f"Ranked {relevant_count} relevant documents",
                                "data": {
                                    "total_documents": len(judged_docs),
                                    "relevant_documents": relevant_count,
                                    "avg_score": (
                                        sum(relevance_scores) / len(relevance_scores)
                                        if relevance_scores
                                        else 0
                                    ),
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }
                        elif (
                            not enable_reranking
                            and "document_judging_skipped" not in rag_stages_emitted
                        ):
                            logger.info(
                                f"⚠️ [SUPERVISOR] Skipping document_judger event emission - reranking is disabled"
                            )
                            rag_stages_emitted.add("document_judging_skipped")

            # Process RAG results and update state
            from src.agents.common.agent_state import RAGContext

            rag_time_ms = (time.time() - rag_start) * 1000
            logger.info(f"✅ RAG Agent completed in {rag_time_ms:.2f}ms")

            # Extract RAG results from final chunk
            logger.critical(
                f"🔴 [RAG RESULT CHECK] rag_result is None: {rag_result is None}"
            )
            if rag_result:
                logger.critical(
                    f"🔴 [RAG RESULT CHECK] rag_result keys: {list(rag_result.keys()) if isinstance(rag_result, dict) else 'NOT A DICT'}"
                )
                logger.critical(
                    f"🔴 [RAG RESULT CHECK] rag_result type: {type(rag_result)}"
                )
            else:
                logger.critical(f"🔴 [RAG RESULT CHECK] rag_result is empty or None!")

            if rag_result:
                retrieved_docs = rag_result.get("retrieved_documents", []) or []
                judged_docs = rag_result.get("judged_documents", []) or []
                logger.critical(
                    f"🔴 [RAG DOCS EXTRACTED] retrieved_docs type: {type(retrieved_docs)}, count: {len(retrieved_docs) if retrieved_docs else 0}"
                )
                logger.critical(
                    f"🔴 [RAG DOCS EXTRACTED] judged_docs type: {type(judged_docs)}, count: {len(judged_docs) if judged_docs else 0}"
                )
                relevance_scores = rag_result.get("relevance_scores", [])
                relevance_threshold = rag_config.get("reranking_config", {}).get(
                    "relevance_threshold", 0.5
                )

                # Create RAGContext
                # Safety check: ensure judged_docs is a list
                if not judged_docs:
                    judged_docs = []

                relevant_count = (
                    len(
                        [
                            doc
                            for doc in (judged_docs or [])
                            if getattr(doc, "is_relevant", True)
                        ]
                    )
                    if judged_docs
                    else 0
                )

                rag_context = RAGContext(
                    query=query,
                    original_documents=retrieved_docs or [],
                    judged_documents=judged_docs or [],
                    relevance_scores=relevance_scores or [],
                    relevance_threshold=relevance_threshold,
                    retrieved_count=len(retrieved_docs or []),
                    relevant_count=relevant_count,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

                result_state["rag_context"] = rag_context

                # Log RAG context for debugging
                logger.critical(f"🔴 [RAG CONTEXT] Stored in result_state")
                logger.critical(
                    f"🔴 [RAG CONTEXT] Retrieved count: {rag_context.retrieved_count}"
                )
                logger.critical(
                    f"🔴 [RAG CONTEXT] Relevant count: {rag_context.relevant_count}"
                )
                logger.critical(
                    f"🔴 [RAG CONTEXT] Judged docs count: {len(rag_context.judged_documents)}"
                )
                if rag_context.judged_documents:
                    logger.critical(
                        f"🔴 [RAG CONTEXT] First doc type: {type(rag_context.judged_documents[0])}"
                    )
                    logger.critical(
                        f"🔴 [RAG CONTEXT] First doc: {str(rag_context.judged_documents[0])[:300]}"
                    )

                # Add response message from RAG agent's final_answer
                # RAG nodes set final_answer in their state, not response
                response_content = rag_result.get("final_answer", "")
                if response_content:
                    result_state["messages"] = result_state.get("messages", []) + [
                        {"role": "assistant", "content": response_content}
                    ]

                total_docs = len(retrieved_docs)
                relevant_docs = len(
                    [doc for doc in judged_docs if getattr(doc, "is_relevant", True)]
                )

            # Emit RAG agent COMPLETE event
            rag_complete_data = {
                "documents_retrieved": total_docs,
                "relevant_documents": relevant_docs,
                "strategy_used": rag_enhancement_strategy,
                "rag_execution_time_ms": rag_time_ms,
            }

            # Include enhanced queries if available
            if rag_enhanced_queries:
                rag_complete_data["query_variants"] = rag_enhanced_queries
                rag_complete_data["variant_count"] = len(rag_enhanced_queries)

            yield {
                "type": "supervisor_progress",
                "stage": "rag_agent_executing_complete",
                "message": f"RAG Agent completed - Retrieved {total_docs} documents",
                "data": rag_complete_data,
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Execute Task Agent if needed
        if detected_intent == "rag_then_task":
            logger.info("🔨 Supervisor: Routing to Task Agent...")

            # Yield Task Agent START event
            yield {
                "type": "supervisor_progress",
                "stage": "task_agent_executing",
                "message": "Executing Task Agent with RAG context",
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

            task_start = time.time()
            result_state = await supervisor.task_agent.execute(result_state)
            task_time_ms = (time.time() - task_start) * 1000
            logger.info(f"✅ Task Agent completed in {task_time_ms:.2f}ms")

            # Add task result to messages for consistent response extraction
            task_result = result_state.get("task_result", "")
            if task_result:
                result_state["messages"] = result_state.get("messages", []) + [
                    {"role": "assistant", "content": task_result}
                ]
                logger.info(
                    f"📝 Added task_result to messages ({len(task_result)} chars)"
                )

            # Emit Task agent COMPLETE event immediately
            task_details = result_state.get("task_details", {})
            yield {
                "type": "supervisor_progress",
                "stage": "task_agent_executing_complete",
                "message": "Task Agent execution completed successfully",
                "data": {
                    "task_type": task_details.get("type", "unknown"),
                    "task_status": "completed",
                    "used_rag_context": task_details.get("used_rag_context", False),
                    "task_execution_time_ms": task_time_ms,
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Extract results from agent execution
        execution_time_ms = (time.time() - start_time) * 1000

        # Log result_state.messages to debug response
        logger.info(
            f"📋 [SUPERVISOR] result_state.messages length: {len(result_state.get('messages', []))}"
        )
        if result_state.get("messages"):
            logger.info(
                f"📋 [SUPERVISOR] Last message: {result_state['messages'][-1].get('content', '')[:100]}"
            )

        # Get RAG context documents if available
        rag_documents = []
        relevant_doc_count = 0
        total_doc_count = 0
        if result_state.get("rag_context"):
            rag_context = result_state["rag_context"]
            rag_documents = (
                rag_context.judged_documents
                if hasattr(rag_context, "judged_documents")
                else []
            )
            total_doc_count = len(rag_documents)
            relevant_doc_count = len(
                [doc for doc in rag_documents if getattr(doc, "is_relevant", True)]
            )

        # NOTE: RAG and Task agent COMPLETE events are already emitted immediately after execution above

        # Yield response generation START event
        yield {
            "type": "supervisor_progress",
            "stage": "response_generation",
            "message": "Generating final response",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Yield response generation COMPLETE event
        # Try to extract response from multiple possible locations
        final_response = ""

        # First, try from messages (set by agents)
        if result_state.get("messages"):
            final_response = result_state["messages"][-1].get("content", "")

        # If no response from messages, try from task_result (for task agent)
        if not final_response and result_state.get("task_result"):
            task_result = result_state["task_result"]
            if isinstance(task_result, dict):
                final_response = task_result.get("response", "") or task_result.get(
                    "result", ""
                )
            elif isinstance(task_result, str):
                final_response = task_result

        # If still no response, try from final_answer (for RAG-only mode)
        if not final_response and result_state.get("final_answer"):
            final_response = result_state["final_answer"]

        yield {
            "type": "supervisor_progress",
            "stage": "response_generation_complete",
            "message": "Final response generated successfully",
            "data": {
                "response_length": len(final_response),
                "tokens_estimated": len(final_response.split()),
                "generation_time_ms": execution_time_ms,
                "sources_used": total_doc_count,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Stream response in chunks for Supervisor mode (same as RAG mode)
        logger.info(
            f"📝 [SUPERVISOR] Checking messages: {len(result_state.get('messages', []))} messages"
        )
        logger.info(
            f"📝 [SUPERVISOR] Task result: {result_state.get('task_result', 'NONE')}"
        )
        logger.info(
            f"📝 [SUPERVISOR] Final answer: {result_state.get('final_answer', 'NONE')[:100] if result_state.get('final_answer') else 'NONE'}"
        )
        logger.info(
            f"📝 [SUPERVISOR] final_response length: {len(final_response) if final_response else 0}"
        )
        logger.info(
            f"📝 [SUPERVISOR] final_response content: {final_response[:100] if final_response else 'EMPTY'}"
        )

        if final_response:
            logger.critical(
                f"🔴 [SUPERVISOR RESPONSE] Emitting streaming_response with final answer ({len(final_response)} chars)"
            )

            # Stream response in chunks (every 500 characters, matching RAG mode)
            chunk_size = 500
            for i in range(0, len(final_response), chunk_size):
                chunk = final_response[i : i + chunk_size]

                # Emit metadata ONLY on the first chunk
                if i == 0:
                    # Build metadata from retrieved documents
                    source_urls = []
                    chunk_ids = []
                    for doc in rag_documents:
                        if isinstance(doc, dict) and doc.get("source_url"):
                            if doc["source_url"] not in source_urls:
                                source_urls.append(doc["source_url"])
                        if isinstance(doc, dict) and doc.get("chunk_id"):
                            if doc["chunk_id"] not in chunk_ids:
                                chunk_ids.append(doc["chunk_id"])

                    logger.critical(
                        f"🔴 [SUPERVISOR RESPONSE] Emitting first chunk with metadata: {len(source_urls)} sources, {len(chunk_ids)} chunks, strategy={rag_enhancement_strategy}, {len(rag_enhanced_queries) if rag_enhanced_queries else 0} enhanced queries"
                    )
                    yield {
                        "type": "streaming_response",
                        "chunk": chunk,
                        "metadata": {
                            "source_urls": source_urls,
                            "chunk_ids": chunk_ids,
                            "document_count": len(rag_documents),
                            "enhancement_strategy": (
                                rag_enhancement_strategy
                                if rag_enhancement_strategy
                                else "native"
                            ),
                            "enhanced_queries": (
                                rag_enhanced_queries if rag_enhanced_queries else []
                            ),
                        },
                        "execution_time_ms": execution_time_ms,
                    }
                else:
                    # Subsequent chunks don't include metadata
                    yield {
                        "type": "streaming_response",
                        "chunk": chunk,
                        "execution_time_ms": execution_time_ms,
                    }

            logger.critical(
                f"✅ [SUPERVISOR RESPONSE] EMITTED all streaming_response chunks for {len(final_response)} chars"
            )

        # Extract metadata for UI
        source_urls = []
        chunk_ids = []
        for doc in rag_documents:
            if isinstance(doc, dict) and doc.get("source_url"):
                if doc["source_url"] not in source_urls:
                    source_urls.append(doc["source_url"])
            if isinstance(doc, dict) and doc.get("chunk_id"):
                if doc["chunk_id"] not in chunk_ids:
                    chunk_ids.append(doc["chunk_id"])

        final_result = {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "documents": rag_documents,
            "intent": detected_intent,
            "total_chunks": 1,
            # Include metadata for UI
            "metadata": {
                "source_urls": source_urls,
                "chunk_ids": chunk_ids,
                "document_count": len(rag_documents),
                "enhancement_strategy": (
                    rag_enhancement_strategy if rag_enhancement_strategy else "native"
                ),
                "enhanced_queries": (
                    rag_enhanced_queries if rag_enhanced_queries else []
                ),
            },
        }

        logger.info(
            f"✅ Supervisor orchestration completed in {execution_time_ms:.2f}ms "
            f"for query: '{query[:50]}...'"
        )

        # SAVE messages to conversation history (same as RAG mode)
        try:
            # Save user query message
            user_message = ConversationMessage(
                role="user",
                content=query,
                timestamp=datetime.now(timezone.utc),
                search_query=query,
            )
            conversation_history_service.add_message(conversation_id, user_message)
            logger.info(
                f"✅ [CONVERSATION] Saved user query to conversation {conversation_id}"
            )

            # Save assistant response message with metadata
            assistant_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
                source_urls=source_urls,
                chunk_ids=chunk_ids,
                document_count=len(rag_documents),
                processing_time_ms=int(execution_time_ms),
                enhancement_strategy_used=(
                    rag_enhancement_strategy if rag_enhancement_strategy else "native"
                ),
                enhanced_queries=rag_enhanced_queries if rag_enhanced_queries else [],
            )
            conversation_history_service.add_message(conversation_id, assistant_message)
            logger.info(
                f"✅ [CONVERSATION] Saved assistant response to conversation {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [CONVERSATION] Failed to save messages to conversation: {e}"
            )

        yield final_result
        return

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"❌ Supervisor orchestration failed after {execution_time_ms:.2f}ms: {e}"
        )
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Yield error result
        yield {
            "type": "supervisor_error",
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "workflow_completed": False,
            "query": query,
            "response": f"I encountered an error while processing your query: {str(e)}",
            "documents": [],
        }
