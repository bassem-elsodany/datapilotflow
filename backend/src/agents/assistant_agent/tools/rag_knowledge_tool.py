"""
RAG Knowledge Retrieval Tool for Assistant Agent.

This module provides the RAG tool that wraps the RAG agent and handles
multi-variant query parsing for intention analysis and comprehensive retrieval.
"""

import traceback
from typing import Annotated, Any, Dict, Optional

from langchain_core.tools import InjectedToolCallId, tool
from loguru import logger
from opik.integrations.langchain import OpikTracer

from src.agents.rag_agent.graph import graph_dev as rag_workflow
from src.agents.rag_agent.state import create_initial_state
from src.config import settings


def create_rag_knowledge_tool(
    rag_agent_name: str,
    rag_agent_description: str,
    workflow_config: Dict[str, Any],
    rag_execution_state: Dict[str, Any],
):
    """
    Create RAG knowledge retrieval tool with the given configuration.

    All configuration is centralized in workflow_config - no parameter duplication.

    Args:
        rag_agent_name: Name of the RAG tool
        rag_agent_description: Description for the RAG tool
        workflow_config: Complete configuration for RAG workflow containing:
            - selected_strategy: Query enhancement strategy (always 'custom_variants')
            - conversation_description: Optional conversation context
            - llm_provider_id: LLM provider ID
            - llm_model_name: LLM model name
            - collection_name: Collection name
            - top_k: Number of results
            - enable_reranking: Whether to rerank results
            - llm_client: LLM client instance
            - ... (all other RAG config)
        rag_execution_state: Shared state for tracking RAG execution

    Returns:
        LangChain tool for RAG knowledge retrieval
    """

    # Extract config values from workflow_config (single source of truth)
    selected_strategy = workflow_config.get("selected_strategy", "native")
    conversation_description = workflow_config.get("conversation_description")
    llm_provider_id = workflow_config.get("llm_provider_id")
    llm_model_name = workflow_config.get("llm_model_name")
    collection_name = workflow_config.get("collection_name")

    @tool(
        rag_agent_name,
        description=rag_agent_description,
    )
    async def retrieve_knowledge_tool(
        search_query: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> str:
        """
        Wrapper tool for RAG agent - keeps RAG agent completely unchanged.
        Converts query → RAG state, invokes RAG, extracts result → tool response.

        Supports multi-variant queries from agent:
        - Single query: "your query here"
        - Multiple variants: '["variant1", "variant2", "variant3"]' (JSON array string)
        """
        logger.info(f"RAG Tool invoked with query: {search_query}")

        try:
            # === PARSE AGENT'S QUERY INPUT ===
            # Agent may send single query OR JSON array of variants
            query_input = search_query  # Default: use as-is

            # Detect if agent provided JSON array of variants
            if isinstance(search_query, str) and search_query.strip().startswith("["):
                try:
                    import json

                    parsed_variants = json.loads(search_query)

                    if isinstance(parsed_variants, list) and len(parsed_variants) > 0:
                        # Validate all items are strings
                        variants = [
                            str(v).strip()
                            for v in parsed_variants
                            if v and str(v).strip()
                        ]

                        if variants:
                            logger.info(
                                f"[INTENT ANALYSIS] Agent provided {len(variants)} query variants"
                            )
                            logger.info("=" * 100)
                            for idx, variant in enumerate(variants, 1):
                                logger.info(
                                    f"   VARIANT [{idx}/{len(variants)}]: '{variant}'"
                                )
                            logger.info("=" * 100)

                            # Use variants for retrieval (will trigger RRF in document_retriever)
                            query_input = variants

                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Agent sent string starting with '[' but failed to parse as JSON: {e}"
                    )
                    logger.warning(
                        f"Using as single query string: {search_query[:100]}..."
                    )
                    query_input = search_query

            # Create RAG agent input state using the same function as RAG websocket
            rag_input_state = create_initial_state(
                query=query_input,  # Can be str OR List[str]
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
                logger.debug("OpikTracer configured for RAG tool invocation")

            logger.info(
                f"Invoking RAG agent workflow with strategy={selected_strategy}"
            )
            rag_result = await rag_workflow.ainvoke(rag_input_state, config=rag_config)

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
                f"RAG agent completed: {rag_execution_state['relevant_docs']}/{rag_execution_state['total_docs']} relevant docs"
            )

            # Format response for the main agent with both human-readable and machine-parseable content
            import json

            source_urls = []
            for doc in retrieved_documents:
                if doc.get("source_url") and doc["source_url"] not in source_urls:
                    source_urls.append(doc["source_url"])

            # Build structured document list for task tools to consume
            documents_for_tools = []
            for i, doc in enumerate(retrieved_documents[:10], 1):  # Top 10 docs
                documents_for_tools.append({
                    "id": doc.get("id") or doc.get("chunk_id", f"doc_{i}"),
                    "content": doc.get("text") or doc.get("content", ""),
                    "source": doc.get("source_url", ""),
                    "metadata": {k: v for k, v in doc.items()
                                if k not in ["text", "content", "id", "source_url", "chunk_id"]},
                })

            # Format response as JSON for machine parsing + human-readable text
            tool_response_data = {
                "type": "rag_retrieval_result",
                "answer": final_answer,
                "documents": documents_for_tools,
                "metadata": {
                    "total_documents": rag_execution_state['total_docs'],
                    "relevant_documents": rag_execution_state['relevant_docs'],
                    "source_count": len(source_urls),
                    "sources": source_urls[:10],
                }
            }

            # Return as JSON string so agent can parse it
            tool_response = json.dumps(tool_response_data, indent=2)

            logger.info(
                f"RAG tool returning {len(documents_for_tools)} documents in structured JSON format"
            )

            return tool_response

        except Exception as e:
            logger.error(f"RAG tool error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error retrieving knowledge: {str(e)}"

    return retrieve_knowledge_tool
