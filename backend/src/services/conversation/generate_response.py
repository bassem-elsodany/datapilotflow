"""
Generate Response Service for LangGraph Workflow

This module handles the execution of the LangGraph workflow for generating
AI responses with query enhancement capabilities.
"""

import time
import traceback
import uuid
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
            )

            # Yield supervisor initialization COMPLETE event
            yield {
                "type": "supervisor_progress",
                "stage": "supervisor_init_complete",
                "message": "Supervisor orchestration initialized successfully",
                "data": {
                    "orchestrator_type": "multi_agent",
                    "agents_available": ["rag_agent", "task_agent"],
                    "initialization_time_ms": (time.time() - supervisor_init_start)
                    * 1000,
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
                    conversation_description=result_state.get(
                        "conversation_description"
                    ),
                )

                last_rag_node = None
                rag_result = None

                # Only emit query enhancement if a strategy is configured (not native)
                if selected_strategy and selected_strategy != "native":
                    yield {
                        "type": "workflow_progress",
                        "stage": "query_enhancement",
                        "message": "Enhancing query...",
                        "execution_time_ms": (time.time() - start_time) * 1000,
                    }

                # Stream through RAG graph nodes - emit START and COMPLETE events
                async for chunk in supervisor.rag_agent.rag_graph.astream(
                    rag_state_input
                ):
                    rag_result = chunk
                    # Detect node changes and emit START + COMPLETE events
                    for node_name, node_output in chunk.items():
                        if (
                            node_name != last_rag_node
                            and node_name != "__start__"
                            and node_name != "__end__"
                        ):
                            last_rag_node = node_name
                            logger.info(f"📊 RAG Node: {node_name}")

                            # Map node names to substage events
                            # 1. Emit START event (no data)
                            # 2. Emit COMPLETE event (with actual output data)

                            if node_name in [
                                "multi_query_strategy_node",
                                "hyde_strategy_node",
                                "decomposition_strategy_node",
                                "augmented_strategy_node",
                            ]:
                                # START event
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "query_enhancement",
                                    "message": "Enhancing query...",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                                # COMPLETE event with data
                                enhanced_queries = node_output.get(
                                    "enhanced_query", {}
                                ).get("variants", [])
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "query_enhancement_complete",
                                    "message": f"Query enhanced with {len(enhanced_queries)} variants",
                                    "data": {
                                        "strategy": node_name.replace(
                                            "_strategy_node", ""
                                        ),
                                        "query_variants": enhanced_queries,
                                        "variant_count": len(enhanced_queries),
                                    },
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                            elif node_name == "document_retriever":
                                # START event
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "document_retrieval",
                                    "message": "Retrieving documents...",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                                # COMPLETE event with data
                                retrieved_docs = node_output.get(
                                    "retrieved_documents", []
                                )
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
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                            elif node_name == "document_judger":
                                # START event
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "document_judging",
                                    "message": "Ranking documents...",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                                # COMPLETE event with data
                                judged_docs = node_output.get("judged_documents", [])
                                relevance_scores = node_output.get(
                                    "relevance_scores", []
                                )
                                relevant_count = len(
                                    [s for s in relevance_scores if s >= 0.5]
                                )
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
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                # Process RAG results and update state
                from src.agents.common.agent_state import RAGContext

                rag_time_ms = (time.time() - rag_start) * 1000
                logger.info(f"✅ RAG Agent completed in {rag_time_ms:.2f}ms")

                # Extract RAG results from final chunk
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

                    # Add response message
                    response_content = rag_result.get("response", "")
                    if response_content:
                        result_state["messages"] = result_state.get("messages", []) + [
                            {"role": "assistant", "content": response_content}
                        ]

                    total_docs = len(retrieved_docs)
                    relevant_docs = len(
                        [
                            doc
                            for doc in judged_docs
                            if getattr(doc, "is_relevant", True)
                        ]
                    )

                # Emit RAG agent COMPLETE event
                yield {
                    "type": "supervisor_progress",
                    "stage": "rag_agent_executing_complete",
                    "message": f"RAG Agent completed - Retrieved {total_docs} documents",
                        "data": {
                            "documents_retrieved": total_docs,
                            "relevant_documents": relevant_docs,
                            "strategy_used": selected_strategy or "native",
                            "rag_execution_time_ms": rag_time_ms,
                        },
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

                # Emit Task agent COMPLETE event immediately
                task_result = result_state.get("task_result", {})
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
            final_response = (
                result_state.get("messages", [])[-1].get("content", "")
                if result_state.get("messages")
                else ""
            )
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
        last_stage = None
        stage_mapping = {
            "augmented_strategy_node": "query_enhancement",
            "multi_query_strategy_node": "query_enhancement",
            "hyde_strategy_node": "query_enhancement",
            "decomposition_strategy_node": "query_enhancement",
            "document_retriever": "document_retrieval",
            "document_judger": "document_judging",
            "answer_generator": "answer_generation",
            "raw_response_formatter": "answer_generation",
        }

        # Track stage completion to emit COMPLETE events
        stages_completed = set()
        query_enhancement_emitted = False  # Track if we've emitted query_enhancement START event

        async for chunk in stream_iterator:
            logger.critical(f"🔴 [RAG CHUNK] Received chunk with keys: {list(chunk.keys())}")
            chunk_count += 1

            # With stream_mode="updates", chunk is {node_name: state_update}
            # Extract the node name and state
            node_name = list(chunk.keys())[0] if chunk else "unknown"
            state_update = chunk.get(node_name, {}) if chunk else {}
            logger.critical(f"🔴 [RAG NODE] node_name={node_name}, state_keys={list(state_update.keys())[:5]}")

            # Merge state updates to accumulate all fields
            last_state = {**last_state, **state_update}

            # Calculate current execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # CRITICAL FIX: Some strategy nodes may not emit chunks to the stream
            # But their output appears in subsequent nodes' state
            # Check if enhanced_query exists and query_enhancement hasn't been emitted yet
            if (not query_enhancement_emitted and
                state_update.get("enhanced_query") and
                last_stage is None):  # Haven't emitted any stage yet
                logger.critical(f"🔴 [RAG HIDDEN NODE] Detected enhanced_query in state but no strategy node chunk received!")
                logger.critical(f"🔴 [RAG HIDDEN NODE] Emitting query_enhancement START event for missing/silent strategy node")

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

            # Map node to stage for consistency with supervisor path
            current_stage = stage_mapping.get(node_name, node_name)
            logger.critical(f"🔴 [RAG MAPPING] node_name={node_name} -> current_stage={current_stage}, last_stage={last_stage}")

            # Skip special nodes
            if node_name in ["__start__", "__end__"]:
                logger.critical(f"🔴 [RAG SKIP] Skipping special node: {node_name}")
                continue

            # Emit START event when we transition to a new stage
            if current_stage != last_stage and current_stage in stage_mapping.values():
                last_stage = current_stage
                start_event = {
                    "type": "workflow_progress",
                    "stage": current_stage,
                    "message": f"Processing {current_stage}...",
                    "execution_time_ms": execution_time_ms,
                }
                logger.critical(f"🚀 [RAG START EVENT] EMITTING START: stage={current_stage}, node={node_name}")
                yield start_event
                logger.critical(f"✅ [RAG START EVENT] YIELDED START event for {current_stage}")

            # Emit COMPLETE events with detailed data based on stage
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
                            all_queries = enhanced_query_dict.get("augmented_queries", [])
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

                    logger.info(f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for query_enhancement_complete with {len(enhanced_queries)} variants")
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

                    logger.info(f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for document_retrieval_complete with {document_count} documents")
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

                    logger.info(f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for document_judging_complete with {relevant_count}/{len(judged_docs)} relevant")
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
                    # Answer Generation / Raw Formatting
                    final_answer = state_update.get("final_answer", "")

                    # Emit COMPLETE event for answer generation
                    logger.info(f"✅ [RAG COMPLETE EVENT] Emitting COMPLETE event for answer_generation_complete with {len(final_answer)} characters")
                    yield {
                        "type": "workflow_progress",
                        "stage": "answer_generation_complete",
                        "message": f"Generated response: {len(final_answer)} characters",
                        "data": {
                            "response_length": len(final_answer),
                            "generation_mode": (
                                "llm" if node_name == "answer_generator" else "raw"
                            ),
                        },
                        "execution_time_ms": execution_time_ms,
                    }
                    # Skip the generic stream_chunk for this node since we already sent complete event
                    continue

            # Only yield generic stream_chunk for nodes that don't have explicit completion events
            # This prevents duplicate events for query enhancement, document retrieval, etc.
            logger.debug(
                f"📦 Streaming chunk {chunk_count}: node={node_name}, stage={current_stage}, "
                f"retrieved={len(state_update.get('retrieved_documents', []))}, "
                f"judged={len(state_update.get('judged_documents', []))}, "
                f"answer_len={len(state_update.get('final_answer', ''))}"
            )

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
