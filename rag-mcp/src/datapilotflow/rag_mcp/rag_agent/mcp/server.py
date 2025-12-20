"""
RAG Agent MCP Server.

Implements the MCP server protocol to expose RAG agent functionality
as a standalone service using FastMCP with HTTP Transport (Streamable).

Provides knowledge retrieval from vector databases with multi-query search
and structured document output for any agent or application.

See: https://gofastmcp.com/deployment/running-server
"""

import traceback
from typing import Any, Dict, List, Union

from fastmcp import FastMCP
from loguru import logger

from src.agents.rag_agent.graph import graph_dev as rag_workflow
from src.agents.rag_agent.mcp.tools import RAGQueryInput, RAGQueryOutput
from src.agents.rag_agent.state import create_initial_state
from src.config import settings

# Create FastMCP server with HTTP Transport (Streamable)
# Transport is configured in run() method with transport="http"
mcp = FastMCP(
    "rag-agent",
    dependencies=["loguru", "langgraph"],
)


@mcp.tool()
async def knowledge_expert(
    search_query: List[str],
    collection_name: str,
    top_k: int = 5,
    user_id: str = "",
    embedding_provider_id: str = "",
    embedding_model_name: str = "",
    vector_dimension: int = 1536,
    enable_reranking: bool = False,
    llm_provider_id: str = "",
    llm_model_name: str = "",
    conversation_id: str = "",
    conversation_description: str | None = None,
) -> Dict[str, Any]:
    """
    Retrieve relevant documents from the knowledge base using RAG with reranking.

    This tool searches through the knowledge base using multiple query variants
    to ensure comprehensive document retrieval. It then reranks documents by relevance
    and returns structured documents with metadata that you can use to answer questions.

    ASSISTANT MODE CONFIGURATION:
    - Strategy: custom_variants (supervisor provides pre-generated query variants)
    - Reranking: ENABLED (uses agent's LLM to rank by relevance)
    - LLM Generation: Disabled (returns raw documents for agent processing)
    - Embedding: Uses collection's configured embedding model for vector search

    Args:
        search_query: List of exactly 5 diverse query variants for comprehensive retrieval.
            **CRITICAL**: ALL variants MUST be in the SAME LANGUAGE as the original user query.

            Generate variants that cover different aspects and phrasings:
            1. Exact user request (literal wording)
            2. Alternative phrasing (synonyms in the SAME language)
            3. More specific/detailed version (narrow focus)
            4. More general/broader version (wider context)
            5. Related aspect or use case (contextual variant)

            Language Preservation Examples:
            - If user asks in Arabic: ALL 5 variants MUST be in Arabic
            - If user asks in English: ALL 5 variants MUST be in English
            - If user asks in Hebrew: ALL 5 variants MUST be in Hebrew

            Format Validation:
            - INVALID: search_query="single string"
            - VALID: search_query=["variant1", "variant2", "variant3", "variant4", "variant5"]
        collection_name: Vector database collection name
        top_k: Number of documents to retrieve (default: 5, max: 30)
        user_id: User ID for RAG workflow
        embedding_provider_id: Embedding provider ID (from vector database collection config)
        embedding_model_name: Embedding model name (from vector database collection config)
        vector_dimension: Vector dimension of embedding model (from collection config)
        enable_reranking: Enable document reranking by relevance (default: False)
        llm_provider_id: LLM provider ID for reranking (required if enable_reranking is True)
        llm_model_name: LLM model name for reranking (required if enable_reranking is True)
        conversation_id: Conversation ID for tracking
        conversation_description: Optional conversation domain context

    Returns:
        Dictionary containing:
        - documents: List of ranked documents with {id, content, source, metadata}
        - metadata: {total_documents, relevant_documents, source_count, sources}
        - error: Error message if failed (null on success)
    """
    try:
        # Validate input
        query_input = RAGQueryInput(
            search_query=search_query,
            collection_name=collection_name,
            top_k=top_k,
            user_id=user_id,
            embedding_provider_id=embedding_provider_id,
            embedding_model_name=embedding_model_name,
            vector_dimension=vector_dimension,
            enable_reranking=enable_reranking,
            llm_provider_id=llm_provider_id,
            llm_model_name=llm_model_name,
            conversation_id=conversation_id,
            conversation_description=conversation_description,
        )

        # ASSISTANT MODE: Configuration
        # - Strategy: custom_variants (supervisor provides pre-generated query variants)
        # - LLM Generation: DISABLED (returns raw documents for agent to process)
        # - Reranking: CONTROLLED BY SUPERVISOR via enable_reranking flag
        selected_strategy = "custom_variants"  # Supervisor provides variants
        enable_llm_generation = False  # Assistant handles answer generation

        # Use the explicit enable_reranking flag from supervisor
        reranking_enabled = query_input.enable_reranking
        relevance_threshold = 0.5 if reranking_enabled else None

        logger.info(
            f"🔧 MCP Configuration: reranking={'ENABLED' if reranking_enabled else 'DISABLED'} "
            f"(supervisor {'enabled' if reranking_enabled else 'disabled'} reranking via flag)"
        )

        # Build workflow configuration
        workflow_config = {
            "collection_name": query_input.collection_name,
            "user_id": query_input.user_id,
            # Embedding configuration for vector search (REQUIRED)
            "embedding_provider_id": query_input.embedding_provider_id,
            "embedding_model_name": query_input.embedding_model_name,
            "vector_dimension": query_input.vector_dimension,
            # LLM configuration for reranking (OPTIONAL - only if supervisor enables it)
            "llm_provider_id": query_input.llm_provider_id if reranking_enabled else None,
            "llm_model_name": query_input.llm_model_name if reranking_enabled else None,
            # Conversation tracking
            "conversation_id": query_input.conversation_id,
            "conversation_description": query_input.conversation_description,
            # Retrieval parameters
            "top_k": query_input.top_k,
            "enable_reranking": reranking_enabled,
            "reranking_config": {
                "relevance_threshold": relevance_threshold,
                "use_score_based": True,
            } if reranking_enabled else None,
            "enable_llm_generation": enable_llm_generation,
            "selected_strategy": selected_strategy,
            "retrieval_config": {
                "top_k_per_query": max(5, int(query_input.top_k * 1.5)),
                "rrf_k": 60,
            },
        }

        # Create RAG input state
        rag_input_state = create_initial_state(
            query=query_input.search_query,  # List of variants from supervisor
            top_k=query_input.top_k,
            config=workflow_config,
            selected_strategy=selected_strategy,
            conversation_description=query_input.conversation_description,
        )

        logger.info(
            f"RAG MCP: Executing query with {len(search_query)} variants, strategy={selected_strategy}"
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
                        if k not in ["text", "content", "id", "source_url", "chunk_id"]
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

        return output.model_dump()

    except Exception as e:
        error_msg = f"RAG query failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        error_output = RAGQueryOutput(
            documents=[],
            metadata={},
            error=error_msg,
        )

        return error_output.model_dump()


def create_rag_mcp_server() -> FastMCP:
    """Factory function to return RAG MCP Server."""
    return mcp


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
