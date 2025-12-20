"""
RAG Adapter - translates between MCP tool calls and RAG agent workflow.

Handles the execution of RAG queries by orchestrating the RAG agent workflow
and formatting results for MCP protocol.
"""

import traceback
from typing import Any, Dict, List

from loguru import logger

from datapilotflow.agents.rag_agent.graph import graph_dev as rag_workflow
from datapilotflow.agents.rag_agent.state import create_initial_state
from datapilotflow.mcp.tools.rag_tools import RAGQueryInput, RAGQueryOutput


class RAGAdapter:
    """Adapter for executing RAG queries via MCP interface."""

    async def execute_knowledge_expert(
        self,
        input_data: RAGQueryInput,
    ) -> RAGQueryOutput:
        """
        Execute RAG workflow and return structured output for MCP.

        Args:
            input_data: Validated RAG query input

        Returns:
            RAGQueryOutput: Structured document results or error
        """
        try:
            # ASSISTANT MODE: Configuration
            # - Strategy: custom_variants (supervisor provides pre-generated query variants)
            # - LLM Generation: DISABLED (returns raw documents for agent to process)
            # - Reranking: CONTROLLED BY SUPERVISOR via enable_reranking flag
            selected_strategy = "custom_variants"  # Supervisor provides variants
            enable_llm_generation = False  # Assistant handles answer generation

            # Use the explicit enable_reranking flag from supervisor
            reranking_enabled = input_data.enable_reranking
            relevance_threshold = 0.5 if reranking_enabled else None

            logger.info(
                f"🔧 MCP Configuration: reranking={'ENABLED' if reranking_enabled else 'DISABLED'} "
                f"(supervisor {'enabled' if reranking_enabled else 'disabled'} reranking via flag)"
            )

            # Build workflow configuration
            workflow_config = {
                "collection_name": input_data.collection_name,
                "user_id": input_data.user_id,
                # Embedding configuration for vector search (REQUIRED)
                "embedding_provider_id": input_data.embedding_provider_id,
                "embedding_model_name": input_data.embedding_model_name,
                "vector_dimension": input_data.vector_dimension,
                # LLM configuration for reranking (OPTIONAL - only if supervisor enables it)
                "llm_provider_id": (
                    input_data.llm_provider_id if reranking_enabled else None
                ),
                "llm_model_name": (
                    input_data.llm_model_name if reranking_enabled else None
                ),
                # Conversation tracking
                "conversation_id": input_data.conversation_id,
                "conversation_description": input_data.conversation_description,
                # Retrieval parameters
                "top_k": input_data.top_k,
                "enable_reranking": reranking_enabled,
                "reranking_config": (
                    {
                        "relevance_threshold": relevance_threshold,
                        "use_score_based": True,
                    }
                    if reranking_enabled
                    else None
                ),
                "enable_llm_generation": enable_llm_generation,
                "selected_strategy": selected_strategy,
                "retrieval_config": {
                    "top_k_per_query": max(5, int(input_data.top_k * 1.5)),
                    "rrf_k": 60,
                },
            }

            # Create RAG input state
            rag_input_state = create_initial_state(
                query=input_data.search_query,  # List of variants from supervisor
                top_k=input_data.top_k,
                config=workflow_config,
                selected_strategy=selected_strategy,
                conversation_description=input_data.conversation_description,
            )

            logger.info(
                f"RAG MCP: Executing query with {len(input_data.search_query)} variants, strategy={selected_strategy}"
            )

            # Execute RAG workflow
            rag_result = await rag_workflow.ainvoke(rag_input_state, config={})

            # Extract RAG results
            retrieved_documents = rag_result.get("retrieved_documents", [])

            # Extract source URLs
            source_urls = []
            for doc in retrieved_documents:
                if doc.get("source_url") and doc["source_url"] not in source_urls:
                    source_urls.append(doc["source_url"])

            # Build structured document list for tools (matching supervisor format)
            documents_for_tools = []
            for i, doc in enumerate(retrieved_documents[:10], 1):  # Top 10 docs
                documents_for_tools.append(
                    {
                        "id": doc.get("id") or doc.get("chunk_id", f"doc_{i}"),
                        "content": doc.get("text") or doc.get("content", ""),
                        "source": doc.get("source_url", ""),
                        "metadata": {
                            k: v
                            for k, v in doc.items()
                            if k not in [
                                "text",
                                "content",
                                "id",
                                "source_url",
                                "chunk_id",
                            ]
                        },
                    }
                )

            # Build output
            output = RAGQueryOutput(
                documents=documents_for_tools,
                metadata={
                    "total_documents": len(retrieved_documents),
                    "relevant_documents": len(retrieved_documents),
                    "source_count": len(source_urls),
                    "sources": source_urls[:10],
                },
            )

            return output

        except Exception as e:
            error_msg = f"RAG query failed: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")

            error_output = RAGQueryOutput(
                documents=[],
                metadata={},
                error=error_msg,
            )

            return error_output
