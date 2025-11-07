"""
Generate Response Service using Tool Calling Pattern (LangChain Recommended)

This module implements the OFFICIAL LangChain multi-agent pattern:
https://docs.langchain.com/oss/python/langchain/multi-agent

The RAG agent is wrapped as a tool that the main ReAct agent can invoke.
"""

import asyncio
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional

import litellm
from langchain.agents import create_agent
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from loguru import logger
from opik.integrations.langchain import OpikTracer
from opik.integrations.litellm import opik_tracker

# Import compatibility shim for opik with LangChain 1.0+ (MUST be first)
import src.compat_langchain_load  # noqa: F401
from src.agents.common.prompts import MAIN_AGENT_SYSTEM_PROMPT
from src.agents.rag_agent.graph import graph_dev as rag_workflow
from src.agents.rag_agent.state import create_initial_state
from src.agents.task_agent.tools import get_task_agent_tools
from src.config import settings
from src.domain.conversation import ConversationMessage
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Enable dropping unsupported params for different LLM providers
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
    rag_agent_name: str = "knowledge_expert",
    rag_agent_description: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using Tool Calling Pattern (LangChain recommended).

    The RAG agent is wrapped as a tool that the main ReAct agent invokes.
    Reference: https://docs.langchain.com/oss/python/langchain/multi-agent
    """
    start_time = time.time()

    try:
        # Yield initialization START event
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing Multi-Agent System (Tool Calling Pattern)",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # Initialize workflow config for RAG agent
        top_k_per_query = max(5, int(top_k * 1.5))

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

        # Get provider configuration
        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(llm_provider_id, user_id)

        if not provider:
            raise ValueError(f"Provider not found: {llm_provider_id}")
        if not provider.is_active:
            raise ValueError(f"Provider is not active: {provider.name}")
        if not provider.api_key or provider.api_key.strip() == "":
            raise ValueError(f"API key not configured for provider '{provider.name}'")

        # Get temperature and max_tokens from provider's generative config
        generative_config = provider.generative.config if provider.generative else {}
        temperature = generative_config.get("temperature", 0.7)
        max_tokens = generative_config.get("max_tokens", 4096)

        # Create LLM client
        model_string = f"{provider.provider_type}/{llm_model_name}"
        llm_client = ChatLiteLLM(
            model=model_string,
            api_key=provider.api_key,
            api_base=provider.endpoint if provider.endpoint else None,
            timeout=provider.timeout if provider.timeout else 60,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(f"✅ Created LLM client: {model_string}")

        # Add LLM client to workflow config
        workflow_config["llm_client"] = llm_client

        # Retrieve selected system prompt if provided
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
                        f"📝 Using system prompt: '{selected_system_prompt.name}'"
                    )
                else:
                    logger.warning(
                        f"⚠️ System prompt not found: {selected_system_prompt_id}"
                    )
            except Exception as e:
                logger.error(f"⚠️ Error retrieving system prompt: {e}")

        # Track RAG execution state (shared across tool invocations)
        rag_execution_state = {
            "stages_emitted": set(),
            "total_docs": 0,
            "relevant_docs": 0,
            "documents": [],
            "enhanced_queries": [],
            "enhancement_strategy": selected_strategy or "native",
            "final_answer": "",
        }

        # Build RAG agent description
        default_rag_description = (
            "Retrieves and ranks relevant documents from the knowledge base. "
            "This is the PRIMARY SOURCE OF TRUTH for accurate information. "
            "ALWAYS call this tool FIRST to ground your response in factual knowledge. "
            "Returns: Relevant context, documents, and metadata from the knowledge base."
        )

        # Add knowledge base context to description if available
        if conversation_description and not rag_agent_description:
            default_rag_description += (
                f"\n\nKnowledge base domain: {conversation_description[:100]}"
            )

        final_rag_description = rag_agent_description or default_rag_description

        # Create RAG tool wrapper (ASYNC)
        @tool(
            rag_agent_name,
            description=final_rag_description,
        )
        async def retrieve_knowledge_tool(
            search_query: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> str:
            """
            Wrapper tool for RAG agent - keeps RAG agent completely unchanged.
            Converts query → RAG state, invokes RAG, extracts result → tool response.
            """
            logger.info(f"🔍 RAG Tool invoked with query: {search_query}")

            try:
                # Create RAG agent input state using the same function as RAG websocket
                rag_input_state = create_initial_state(
                    query=search_query,
                    top_k=workflow_config["top_k"],
                    config=workflow_config,
                    selected_strategy=selected_strategy,
                    conversation_description=conversation_description,
                )

                # Configure Opik tracing for RAG invocation (if enabled)
                rag_config = {}
                if settings.AGENT_TRACING_ENABLED:
                    # Build tags for RAG tool trace
                    rag_trace_tags = [
                        "rag_agent",
                        "tool_invocation",
                        f"strategy:{selected_strategy or 'native'}",
                        f"provider:{llm_provider_id}",
                        f"model:{llm_model_name}",
                        f"collection:{collection_name}",
                        f"parent:supervisor",
                    ]

                    # Create OpikTracer for RAG workflow
                    rag_opik_tracer = OpikTracer(
                        graph=rag_workflow.get_graph(xray=True),
                        tags=rag_trace_tags,
                    )

                    rag_config = {
                        "callbacks": [rag_opik_tracer],
                    }
                    logger.debug("✅ OpikTracer configured for RAG tool invocation")

                logger.info(
                    f"📊 Invoking RAG agent workflow with strategy={selected_strategy}..."
                )
                rag_result = await rag_workflow.ainvoke(
                    rag_input_state, config=rag_config
                )

                # Extract results from RAG agent's custom state
                final_answer = rag_result.get("final_answer", "No answer generated")
                retrieved_documents = rag_result.get("retrieved_documents", [])
                judged_documents = rag_result.get("judged_documents", [])
                query_info = rag_result.get("query_info", {})

                # Update shared state
                rag_execution_state["documents"] = retrieved_documents
                rag_execution_state["total_docs"] = len(retrieved_documents)
                rag_execution_state["relevant_docs"] = len(
                    [d for d in (judged_documents or []) if d.get("is_relevant", False)]
                )
                rag_execution_state["final_answer"] = final_answer

                # Extract enhancement info
                if query_info:
                    rag_execution_state["enhancement_strategy"] = query_info.get(
                        "strategy_used", rag_execution_state["enhancement_strategy"]
                    )
                    rag_execution_state["enhanced_queries"] = query_info.get(
                        "enhanced_queries", []
                    )

                logger.info(
                    f"✅ RAG agent completed: {rag_execution_state['relevant_docs']}/{rag_execution_state['total_docs']} relevant docs"
                )

                # Format response for the main agent
                source_urls = []
                for doc in retrieved_documents:
                    if doc.get("source_url") and doc["source_url"] not in source_urls:
                        source_urls.append(doc["source_url"])

                # Extract raw document content for passing to other tools (e.g., flow generator)
                raw_context_parts = []
                for i, doc in enumerate(retrieved_documents[:5], 1):  # Top 5 docs
                    content = doc.get("content", "")
                    if content:
                        raw_context_parts.append(
                            f"[Document {i}]\n{content[:1000]}"
                        )  # First 1000 chars

                raw_context = (
                    "\n\n".join(raw_context_parts)
                    if raw_context_parts
                    else "No document content available"
                )

                tool_response = f"""**Retrieved Knowledge:**
{final_answer}

**Sources:** {len(source_urls)} unique sources, {rag_execution_state['total_docs']} total documents, {rag_execution_state['relevant_docs']} relevant.
**Source URLs:** {', '.join(source_urls[:5])}{'...' if len(source_urls) > 5 else ''}

**Raw Documentation Context (for code/flow generation):**
{raw_context}

**Important Instructions:**
- Use this retrieved knowledge as the foundation for your response
- If generating code/flows (MuleSoft, Python, etc.), pass the "Raw Documentation Context" to the generation tool's retrieved_context parameter
- This ensures generated code follows documented best practices and patterns"""

                return tool_response

            except Exception as e:
                logger.error(f"❌ RAG tool error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f"Error retrieving knowledge: {str(e)}"

        # Get task agent tools
        task_tools = get_task_agent_tools()

        # Combine RAG tool + task tools
        all_tools = [retrieve_knowledge_tool] + task_tools

        logger.info(
            f"🛠️ Created {len(all_tools)} tools: 1 RAG tool + {len(task_tools)} task tools"
        )

        # Build system prompt for main agent
        system_prompt_parts = []

        # Base prompt: Use custom prompt if provided, otherwise use our standard main agent prompt
        if selected_system_prompt and selected_system_prompt.prompt_template:
            system_prompt_parts.append(selected_system_prompt.prompt_template)
        else:
            # Use the properly structured prompt from our prompts package
            system_prompt_parts.append(MAIN_AGENT_SYSTEM_PROMPT.prompt)

        # Add knowledge base context if available
        if conversation_description:
            system_prompt_parts.append(
                f"\n\n**Knowledge Base Context:**\n{conversation_description}"
            )

        system_prompt = "\n".join(system_prompt_parts)

        # Create main ReAct agent with all tools
        logger.info("🤖 Creating main ReAct agent with Tool Calling pattern")

        main_agent = create_agent(
            model=llm_client,
            tools=all_tools,
            system_prompt=system_prompt,
        )

        logger.info("✅ Main ReAct agent created successfully")

        # Configure Opik tracing (if enabled)
        config_for_stream = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 50,
        }

        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Supervisor config: strategy={selected_strategy}, "
                f"collection={collection_name}, provider={llm_provider_id}, model={llm_model_name}"
            )

            # Enable LiteLLM tracking for cost and token usage
            opik_tracker.track_litellm()
            logger.debug("✅ LiteLLM tracking enabled for cost and token usage")

            # Build tags for Opik trace
            trace_tags = [
                "supervisor_agent",
                "tool_calling_pattern",
                f"strategy:{selected_strategy or 'native'}",
                f"provider:{llm_provider_id}",
                f"model:{llm_model_name}",
                f"collection:{collection_name}",
                f"conversation:{conversation_id}",
            ]
            if conversation_description:
                trace_tags.append(f"domain:{conversation_description[:50]}")

            # Create OpikTracer for main agent graph
            opik_tracer = OpikTracer(
                graph=main_agent.get_graph(xray=True),
                tags=trace_tags,
            )

            # Add tracer to config callbacks
            config_for_stream["callbacks"] = [opik_tracer]
            logger.debug("✅ OpikTracer configured for supervisor agent")
        else:
            logger.debug(
                f"Agent tracing disabled: Supervisor config: strategy={selected_strategy}, collection={collection_name}"
            )

        # Yield initialization complete event
        yield {
            "type": "supervisor_progress",
            "stage": "supervisor_init_complete",
            "message": "Multi-Agent System initialized (Tool Calling Pattern)",
            "data": {
                "orchestrator_type": "tool_calling_pattern",
                "tools_available": [f"{rag_agent_name} (RAG)"]
                + [t.name for t in task_tools],
                "rag_agent_name": rag_agent_name,
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
                "tracing_enabled": settings.AGENT_TRACING_ENABLED,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Execute main agent and stream events
        logger.info("📊 Starting main agent execution...")

        # Track state
        final_messages = []
        tools_used = []
        rag_tool_called = False

        # Stream events from main agent
        async for event in main_agent.astream_events(
            {"messages": [{"role": "user", "content": query}]},
            config=config_for_stream,
            version="v2",
        ):
            event_type = event.get("event", "")
            event_name = event.get("name", "")
            event_data = event.get("data", {})

            # Track tool calls
            if event_type == "on_chat_model_stream":
                chunk = event_data.get("chunk", {})
                if "tool_calls" in chunk:
                    for tool_call in chunk.get("tool_calls", []):
                        tool_name = tool_call.get("name", "")

                        if tool_name and tool_name not in tools_used:
                            tools_used.append(tool_name)
                            logger.info(f"🔧 Tool call detected: {tool_name}")

                            # Emit RAG agent execution event
                            if tool_name == rag_agent_name:
                                rag_tool_called = True
                                yield {
                                    "type": "supervisor_progress",
                                    "stage": "rag_agent_executing",
                                    "message": f"{rag_agent_name.replace('_', ' ').title()}: Retrieving and ranking documents",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                            # Emit task tool execution event
                            elif tool_name in [t.name for t in task_tools]:
                                yield {
                                    "type": "supervisor_progress",
                                    "stage": "task_agent_executing",
                                    "message": f"Task Tool: Executing {tool_name}",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

            # Capture final output
            if event_type == "on_chain_end" and event_name == "LangGraph":
                if hasattr(event_data, "output"):
                    final_output = event_data.output
                elif isinstance(event_data, dict) and "output" in event_data:
                    final_output = event_data["output"]
                else:
                    final_output = event_data

                if isinstance(final_output, dict) and "messages" in final_output:
                    final_messages = final_output["messages"]
                    logger.info(
                        f"✅ Main agent completed with {len(final_messages)} messages"
                    )

        # Extract final response
        execution_time_ms = (time.time() - start_time) * 1000

        final_response = ""
        if final_messages:
            # Get last AI message content
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage) or (
                    isinstance(msg, dict) and msg.get("role") == "assistant"
                ):
                    final_response = (
                        msg.content
                        if hasattr(msg, "content")
                        else msg.get("content", "")
                    )
                    break

        logger.info(f"📝 Final response length: {len(final_response)}")

        # Emit completion events
        yield {
            "type": "supervisor_progress",
            "stage": "response_generation_complete",
            "message": "Final response generated",
            "data": {
                "response_length": len(final_response),
                "tools_used": tools_used,
                "rag_tool_called": rag_tool_called,
            },
            "execution_time_ms": execution_time_ms,
        }

        # Stream response in chunks
        if final_response:
            chunk_size = 500
            for i in range(0, len(final_response), chunk_size):
                chunk = final_response[i : i + chunk_size]

                if i == 0:
                    # First chunk with metadata
                    metadata = {
                        "tools_used": tools_used,
                        "orchestrator_type": "tool_calling_pattern",
                        "enhancement_strategy": rag_execution_state[
                            "enhancement_strategy"
                        ],
                    }

                    # Add RAG-specific metadata if RAG tool was called
                    if rag_tool_called:
                        source_urls = []
                        chunk_ids = []

                        # Extract source URLs and chunk IDs from documents
                        for doc in rag_execution_state["documents"]:
                            if (
                                doc.get("source_url")
                                and doc["source_url"] not in source_urls
                            ):
                                source_urls.append(doc["source_url"])
                            if doc.get("chunk_id") and doc["chunk_id"] not in chunk_ids:
                                chunk_ids.append(doc["chunk_id"])

                        metadata.update(
                            {
                                "source_urls": source_urls,
                                "chunk_ids": chunk_ids,
                                "document_count": rag_execution_state["total_docs"],
                                "relevant_document_count": rag_execution_state[
                                    "relevant_docs"
                                ],
                                "enhanced_queries": rag_execution_state[
                                    "enhanced_queries"
                                ],
                            }
                        )

                    yield {
                        "type": "streaming_response",
                        "chunk": chunk,
                        "metadata": metadata,
                        "execution_time_ms": execution_time_ms,
                    }
                else:
                    # Subsequent chunks
                    yield {
                        "type": "streaming_response",
                        "chunk": chunk,
                        "execution_time_ms": execution_time_ms,
                    }

        # Save to conversation history
        try:
            user_message = ConversationMessage(
                role="user",
                content=query,
                timestamp=datetime.now(timezone.utc),
                search_query=query,
            )
            conversation_history_service.add_message(conversation_id, user_message)

            assistant_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
                processing_time_ms=int(execution_time_ms),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(f"✅ Saved messages to conversation {conversation_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save conversation: {e}")

        # Final result with RAG documents if available
        final_result = {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "metadata": {
                "orchestrator_type": "tool_calling_pattern",
                "tools_used": tools_used,
                "enhancement_strategy": rag_execution_state["enhancement_strategy"],
            },
        }

        # Add RAG documents if RAG tool was called
        if rag_tool_called:
            final_result["documents"] = rag_execution_state["documents"]
            final_result["metadata"]["document_count"] = rag_execution_state[
                "total_docs"
            ]
            final_result["metadata"]["relevant_document_count"] = rag_execution_state[
                "relevant_docs"
            ]
            final_result["metadata"]["enhanced_queries"] = rag_execution_state[
                "enhanced_queries"
            ]
        else:
            final_result["documents"] = []

        yield final_result

        logger.info(f"✅ Tool Calling Pattern completed in {execution_time_ms:.2f}ms")

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Tool Calling Pattern failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        yield {
            "type": "supervisor_error",
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "workflow_completed": False,
            "query": query,
            "response": f"I encountered an error: {str(e)}",
        }
