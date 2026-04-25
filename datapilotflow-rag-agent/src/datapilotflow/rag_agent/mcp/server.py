"""
Unified DataPilotFlow MCP Server.

Implements the MCP server protocol to expose DataPilotFlow agents
as a unified service using FastMCP with HTTP Transport.

Provides knowledge retrieval from vector databases with multi-query search
and structured document output for any agent or application.

See: https://gofastmcp.com/deployment/running-server
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from datapilotflow.domain.config import settings

from .adapters.rag_adapter import RAGAdapter
from .tools.rag_tools import RAGQueryInput, RAGQueryOutput

# Create FastMCP server with HTTP Transport (Streamable)
# Transport is configured in run() method with transport="streamable-http"
mcp = FastMCP(settings.MCP_SERVER_NAME)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": settings.MCP_SERVER_NAME})

# Initialize adapters
rag_adapter = RAGAdapter()


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
    conversation_description: Optional[str] = None,
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

        # Execute via adapter
        output = await rag_adapter.execute_knowledge_expert(query_input)
        return output.model_dump()

    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}", exc_info=True)
        error_output = RAGQueryOutput(
            documents=[],
            metadata={},
            error=str(e),
        )
        return error_output.model_dump()


def create_mcp_server() -> FastMCP:
    """Factory function to create and return MCP Server."""
    return mcp


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
