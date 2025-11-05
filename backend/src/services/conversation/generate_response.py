"""
Generate Response Service for LangGraph Workflow

This module handles the execution of the LangGraph workflow for generating
AI responses with query enhancement capabilities.
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
from src.orchestration.orchestrator import create_multi_agent_orchestrator
from src.services.conversation.conversation_history_service import (
    ConversationMessage,
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
        top_k_per_query = max(5, int(top_k * 1.5))  # 50% more to account for RRF deduplication

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

        if conversation_description:
            logger.info(f"📝 [SUPERVISOR] Conversation description included: {conversation_description[:100]}...")

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
            rag_config_for_events = {
                "configurable": {"thread_id": str(start_time)}
            }

            async for event in supervisor.rag_agent.rag_graph.astream_events(
                input=rag_state_input,
                config=rag_config_for_events,
                version="v2"
            ):
                event_type = event.get("event", "")
                node_name = event.get("name", "")
                event_data = event.get("data", {})

                logger.debug(f"📡 [SUPERVISOR RAG EVENT] type={event_type}, node={node_name}")

                # Capture final state when workflow completes
                # With version="v2", the final state comes from on_chain_end for LangGraph node
                if event_type == "on_chain_end" and node_name == "LangGraph":
                    logger.critical(f"🔴 [SUPERVISOR RAG] LangGraph on_chain_end event received - THIS IS THE FINAL STATE!")
                    logger.critical(f"🔴 [SUPERVISOR RAG] event_data type: {type(event_data)}")

                    # Extract output from event_data
                    if hasattr(event_data, 'output'):
                        rag_result = event_data.output
                        logger.critical(f"🔴 [SUPERVISOR RAG] Extracted from event_data.output")
                    elif isinstance(event_data, dict) and 'output' in event_data:
                        rag_result = event_data['output']
                        logger.critical(f"🔴 [SUPERVISOR RAG] Extracted from event_data['output']")
                    elif isinstance(event_data, dict):
                        rag_result = event_data
                        logger.critical(f"🔴 [SUPERVISOR RAG] Using event_data directly as dict")
                    else:
                        rag_result = {}
                        logger.critical(f"🔴 [SUPERVISOR RAG] Could not extract output, using empty dict")

                    logger.critical(f"🔴 [SUPERVISOR RAG] rag_result type: {type(rag_result)}")
                    if isinstance(rag_result, dict):
                        logger.critical(f"🔴 [SUPERVISOR RAG] rag_result has {len(rag_result)} keys: {list(rag_result.keys())[:10]}")
                    continue

                # Handle node END events to extract output data
                if event_type == "on_chain_end":
                    logger.info(f"📊 [SUPERVISOR RAG] Node completed: {node_name}")

                    # Extract the node output from the event
                    if hasattr(event_data, 'output'):
                        node_output = event_data.output
                    elif isinstance(event_data, dict) and 'output' in event_data:
                        node_output = event_data['output']
                    else:
                        node_output = event_data

                    # Log node output for debugging
                    if isinstance(node_output, dict):
                        logger.debug(f"🔍 [SUPERVISOR RAG NODE OUTPUT] {node_name} keys: {list(node_output.keys())}")

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
                                enhanced_queries = node_output.get("enhanced_query", {}).get("variants", [])

                                # If not found, try direct variants key
                                if not enhanced_queries:
                                    enhanced_queries = node_output.get("variants", [])

                                # If still not found, try augmented_queries (used by some strategies)
                                if not enhanced_queries:
                                    enhanced_queries = node_output.get("augmented_queries", [])

                                logger.info(f"📊 [SUPERVISOR] Query enhancement output: {node_output.keys()}")
                                logger.info(f"📊 [SUPERVISOR] Extracted {len(enhanced_queries)} enhanced queries: {enhanced_queries[:2] if enhanced_queries else 'NONE'}")
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
                                retrieved_docs = node_output.get("retrieved_documents", [])
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
                        if enable_reranking and "document_judging" not in rag_stages_emitted:
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
                                relevance_scores = node_output.get("relevance_scores", [])
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
                                        sum(relevance_scores)
                                        / len(relevance_scores)
                                        if relevance_scores
                                        else 0
                                    ),
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }
                        elif not enable_reranking and "document_judging_skipped" not in rag_stages_emitted:
                            logger.info(
                                f"⚠️ [SUPERVISOR] Skipping document_judger event emission - reranking is disabled"
                            )
                            rag_stages_emitted.add("document_judging_skipped")

            # Process RAG results and update state
            from src.agents.common.agent_state import RAGContext

            rag_time_ms = (time.time() - rag_start) * 1000
            logger.info(f"✅ RAG Agent completed in {rag_time_ms:.2f}ms")

            # Extract RAG results from final chunk
            logger.critical(f"🔴 [RAG RESULT CHECK] rag_result is None: {rag_result is None}")
            if rag_result:
                logger.critical(f"🔴 [RAG RESULT CHECK] rag_result keys: {list(rag_result.keys()) if isinstance(rag_result, dict) else 'NOT A DICT'}")
                logger.critical(f"🔴 [RAG RESULT CHECK] rag_result type: {type(rag_result)}")
            else:
                logger.critical(f"🔴 [RAG RESULT CHECK] rag_result is empty or None!")

            if rag_result:
                retrieved_docs = rag_result.get("retrieved_documents", [])
                judged_docs = rag_result.get("judged_documents", [])
                relevance_scores = rag_result.get("relevance_scores", [])
                relevance_threshold = rag_config.get("reranking_config", {}).get(
                    "relevance_threshold", 0.5
                )

                # Create RAGContext
                rag_context = RAGContext(
                    query=query,
                    original_documents=retrieved_docs,
                    judged_documents=judged_docs,
                    relevance_scores=relevance_scores,
                    relevance_threshold=relevance_threshold,
                    retrieved_count=len(retrieved_docs),
                    relevant_count=len(
                        [
                            doc
                            for doc in judged_docs
                            if getattr(doc, "is_relevant", True)
                        ]
                    ),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

                result_state["rag_context"] = rag_context

                # Log RAG context for debugging
                logger.critical(f"🔴 [RAG CONTEXT] Stored in result_state")
                logger.critical(f"🔴 [RAG CONTEXT] Retrieved count: {rag_context.retrieved_count}")
                logger.critical(f"🔴 [RAG CONTEXT] Relevant count: {rag_context.relevant_count}")
                logger.critical(f"🔴 [RAG CONTEXT] Judged docs count: {len(rag_context.judged_documents)}")
                if rag_context.judged_documents:
                    logger.critical(f"🔴 [RAG CONTEXT] First doc type: {type(rag_context.judged_documents[0])}")
                    logger.critical(f"🔴 [RAG CONTEXT] First doc: {str(rag_context.judged_documents[0])[:300]}")

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
                logger.info(f"📝 Added task_result to messages ({len(task_result)} chars)")

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
        logger.info(f"📋 [SUPERVISOR] result_state.messages length: {len(result_state.get('messages', []))}")
        if result_state.get("messages"):
            logger.info(f"📋 [SUPERVISOR] Last message: {result_state['messages'][-1].get('content', '')[:100]}")

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
                final_response = task_result.get("response", "") or task_result.get("result", "")
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
        logger.info(f"📝 [SUPERVISOR] Checking messages: {len(result_state.get('messages', []))} messages")
        logger.info(f"📝 [SUPERVISOR] Task result: {result_state.get('task_result', 'NONE')}")
        logger.info(f"📝 [SUPERVISOR] Final answer: {result_state.get('final_answer', 'NONE')[:100] if result_state.get('final_answer') else 'NONE'}")
        logger.info(f"📝 [SUPERVISOR] final_response length: {len(final_response) if final_response else 0}")
        logger.info(f"📝 [SUPERVISOR] final_response content: {final_response[:100] if final_response else 'EMPTY'}")

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
                        f"🔴 [SUPERVISOR RESPONSE] Emitting first chunk with metadata: {len(source_urls)} sources, {len(chunk_ids)} chunks"
                    )
                    yield {
                        "type": "streaming_response",
                        "chunk": chunk,
                        "metadata": {
                            "source_urls": source_urls,
                            "chunk_ids": chunk_ids,
                            "document_count": len(rag_documents),
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

        final_result = {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "documents": rag_documents,
            "intent": detected_intent,
            "total_chunks": 1,
        }

        logger.info(
            f"✅ Supervisor orchestration completed in {execution_time_ms:.2f}ms "
            f"for query: '{query[:50]}...'"
        )

        # SAVE messages to conversation history (same as RAG mode)
        try:
            source_urls = []
            chunk_ids = []
            for doc in rag_documents:
                if isinstance(doc, dict) and doc.get("source_url"):
                    if doc["source_url"] not in source_urls:
                        source_urls.append(doc["source_url"])
                if isinstance(doc, dict) and doc.get("chunk_id"):
                    if doc["chunk_id"] not in chunk_ids:
                        chunk_ids.append(doc["chunk_id"])

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


async def get_response_stream_rag(
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
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using direct RAG-only pipeline (streaming).

    **RAG-ONLY MODE** - This endpoint uses ONLY the RAG pipeline without any supervisor/agent routing.

    Yields:
        Dict containing workflow state chunks with progress updates
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
                f"conversation:{conversation_id}",
            ]
            if conversation_description:
                trace_tags.append(f"domain:{conversation_description[:50]}")

            opik_tracer = OpikTracer(
                graph=workflow.get_graph(xray=True),
                tags=trace_tags,
            )
            # Note: No thread_id needed - each query is independent (stateless RAG)
            config = {
                "callbacks": [opik_tracer],
            }
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

        logger.info("📚 Using direct RAG workflow (no supervisor)")

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
            logger.debug(
                f"🔴 [RAG EVENT] Received event: {event.get('event', 'unknown')}, name: {event.get('name', 'unknown')}"
            )
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

                # Only stream if we're in the actual last step
                if last_stage != last_step_for_streaming:
                    logger.debug(f"⏭️ [LLM STREAM SKIP] Skipping stream from {node_name} (current stage: {last_stage}) - last step is {last_step_for_streaming}")
                    continue

                chunk_data = event_data.get("chunk", {})
                if hasattr(chunk_data, "content"):
                    content = chunk_data.content
                elif isinstance(chunk_data, dict):
                    content = chunk_data.get("content", "")
                else:
                    content = str(chunk_data) if chunk_data else ""

                if content:
                    logger.debug(f"📤 [LLM STREAM - RESPONSE] Emitting chunk from response_generation: {content[:50]}...")

                    # Emit metadata ONLY on the first chunk
                    if not first_llm_chunk_emitted:
                        first_llm_chunk_emitted = True

                        # Build metadata from retrieved documents (may be empty if not yet populated)
                        retrieved_docs = last_state.get("retrieved_documents") or []
                        source_urls = []
                        chunk_ids = []

                        if retrieved_docs:
                            for doc in retrieved_docs:
                                if (
                                    doc.get("source_url")
                                    and doc["source_url"] not in source_urls
                                ):
                                    source_urls.append(doc["source_url"])
                                if (
                                    doc.get("chunk_id")
                                    and doc["chunk_id"] not in chunk_ids
                                ):
                                    chunk_ids.append(doc["chunk_id"])

                        # Extract enhanced queries from query_info
                        query_info = last_state.get("query_info") or {}
                        enhanced_queries = query_info.get("enhanced_queries", [])
                        strategy_used = query_info.get("strategy_used", "augmented")

                        logger.critical(
                            f"📤 [FIRST CHUNK - RESPONSE] Emitting with metadata: {len(source_urls)} sources, {len(retrieved_docs)} docs"
                        )
                        yield {
                            "type": "streaming_response",
                            "chunk": content,
                            "metadata": {
                                "source_urls": source_urls,
                                "chunk_ids": chunk_ids,
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

            # Skip non-node events
            if not event_type.startswith("on_chain"):
                continue

            logger.critical(f"🔴 [RAG NODE EVENT] type={event_type}, node={node_name}")

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
                            all_queries = enhanced_query_dict.get(
                                "augmented_queries", []
                            )
                            enhanced_queries = (
                                all_queries[1:] if len(all_queries) > 1 else []
                            )
                        elif "multi_query_variants" in enhanced_query_dict:
                            enhanced_queries = enhanced_query_dict.get(
                                "multi_query_variants", []
                            )
                        elif "sub_queries" in enhanced_query_dict:
                            enhanced_queries = enhanced_query_dict.get(
                                "sub_queries", []
                            )
                        elif "hypothetical_answer" in enhanced_query_dict:
                            ha = enhanced_query_dict.get("hypothetical_answer")
                            enhanced_queries = [ha] if ha else []

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

        logger.critical(
            f"🔴 [RAG STREAM ENDED] Stream finished after {chunk_count} chunks"
        )
        logger.critical(
            f"🔴 [RAG STREAM ENDED] answer_generation_emitted={answer_generation_emitted}, has_final_answer={bool(last_state.get('final_answer'))}"
        )
        logger.critical(
            f"🔴 [RAG STREAM ENDED] final_answer length={len(last_state.get('final_answer', ''))}"
        )

        # CRITICAL FIX 3: If response_generation wasn't emitted but we have final_answer, emit it now
        if not answer_generation_emitted and last_state.get("final_answer"):
            # Determine if this is from raw_response_formatter or answer_generator
            is_raw_response = not enable_llm_generation and "Raw Results Mode" in last_state.get("final_answer", "")
            response_source = "raw_response_formatter" if is_raw_response else "answer_generator/unknown"

            logger.critical(
                f"🔴 [RAG END STATE] Detected final_answer from {response_source} at end of stream!"
            )
            logger.critical(
                f"🔴 [RAG END STATE] Emitting response_generation START and COMPLETE events now"
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
            logger.critical(
                f"✅ [RAG END STATE] EMITTED response_generation_complete with {len(final_answer)} chars (mode: {generation_mode})"
            )

        # Emit the final_answer as streaming_response so frontend can display it
        final_answer = last_state.get("final_answer", "") if last_state else ""
        if final_answer:
            logger.critical(
                f"🔴 [RAG EMIT RESPONSE] Emitting final_answer as streaming_response ({len(final_answer)} chars)"
            )

            # Emit metadata on first chunk only
            retrieved_docs = last_state.get("retrieved_documents", []) or []
            source_urls = [doc.get("source_url") for doc in retrieved_docs if doc.get("source_url")]
            chunk_ids = [doc.get("chunk_id") for doc in retrieved_docs if doc.get("chunk_id")]

            # Extract enhanced queries from query_info
            query_info = last_state.get("query_info") or {}
            enhanced_queries = query_info.get("enhanced_queries", [])
            strategy_used = query_info.get("strategy_used", "augmented")

            # Break response into chunks to avoid React update depth issues
            # Emit chunks of ~500 chars at a time
            chunk_size = 500
            for i in range(0, len(final_answer), chunk_size):
                chunk = final_answer[i:i + chunk_size]

                response_event = {
                    "type": "streaming_response",
                    "chunk": chunk,
                }

                # Add metadata only on first chunk
                if i == 0:
                    response_event["metadata"] = {
                        "source_urls": source_urls,
                        "chunk_ids": chunk_ids,
                        "document_count": len(retrieved_docs),
                        "enhancement_strategy": strategy_used,
                        "enhanced_queries": enhanced_queries,
                    }

                logger.debug(f"📤 [RAG RESPONSE CHUNK] Emitting chunk {i//chunk_size + 1} ({len(chunk)} chars)")
                yield response_event

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

            # SAVE messages to conversation history
            try:
                query_info = last_state.get("query_info", {})

                # Extract metadata for the response message
                source_urls = []
                chunk_ids = []
                retrieved_docs = last_state.get("retrieved_documents", [])
                for doc in retrieved_docs:
                    if doc.get("source_url") and doc["source_url"] not in source_urls:
                        source_urls.append(doc["source_url"])
                    if doc.get("chunk_id") and doc["chunk_id"] not in chunk_ids:
                        chunk_ids.append(doc["chunk_id"])

                enhanced_queries = (
                    query_info.get("enhanced_queries", []) if query_info else []
                )
                enhancement_strategy = (
                    query_info.get("strategy_used", "augmented")
                    if query_info
                    else "augmented"
                )

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
                    content=response,
                    timestamp=datetime.now(timezone.utc),
                    source_urls=source_urls,
                    chunk_ids=chunk_ids,
                    enhancement_strategy_used=enhancement_strategy,
                    enhanced_queries=enhanced_queries,
                    document_count=len(retrieved_docs),
                    processing_time_ms=int(execution_time_ms),
                )
                conversation_history_service.add_message(
                    conversation_id, assistant_message
                )
                logger.info(
                    f"✅ [CONVERSATION] Saved assistant response to conversation {conversation_id}"
                )

            except Exception as e:
                logger.error(
                    f"❌ [CONVERSATION] Failed to save messages to conversation: {e}"
                )

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
