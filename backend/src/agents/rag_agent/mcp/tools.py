"""
RAG MCP Tool Definitions.

Defines the MCP tool schema and handlers for the RAG agent.

ASSISTANT MODE CONFIGURATION:
- Default strategy: custom_variants (matching supervisor agent)
- LLM generation: Disabled by default (returns raw documents)
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class RAGQueryInput(BaseModel):
    """Input schema for RAG query tool (Assistant Mode)."""

    search_query: List[str] = Field(
        description=(
            "List of exactly 5 diverse query variants for comprehensive retrieval. "
            "CRITICAL: ALL variants MUST be in the SAME LANGUAGE as the original user query. "
            "Generate variants covering different aspects: "
            "1) Exact user request (literal wording), "
            "2) Alternative phrasing (synonyms in same language), "
            "3) More specific/detailed version, "
            "4) More general/broader version, "
            "5) Related aspect or use case. "
            'MUST be a list: ["v1", "v2", "v3", "v4", "v5"]. '
            "Example: If user asks in Arabic, ALL 5 variants must be in Arabic."
        )
    )
    collection_name: str = Field(
        description="Name of the vector database collection to query"
    )
    top_k: int = Field(
        default=5,
        description="Number of documents to retrieve",
        ge=1,
        le=30,
    )
    user_id: str = Field(description="User ID for the RAG workflow")
    # Embedding configuration - from vector database collection
    embedding_provider_id: str = Field(
        description="Embedding provider ID (from vector database collection config)"
    )
    embedding_model_name: str = Field(
        description="Embedding model name (from vector database collection config)"
    )
    vector_dimension: int = Field(
        default=1536,
        description="Vector dimension of the embedding model (from collection config)",
        ge=1,
        le=4096,
    )
    # Reranking configuration
    enable_reranking: bool = Field(
        default=False,
        description="Enable document reranking by relevance using LLM provider"
    )
    # LLM configuration - only used for reranking (assistant provides enhanced queries)
    llm_provider_id: str = Field(
        default="",
        description="LLM provider ID for reranking (required if enable_reranking is True)"
    )
    llm_model_name: str = Field(
        default="",
        description="LLM model name for reranking (required if enable_reranking is True)"
    )
    conversation_id: str = Field(description="Conversation ID for tracking")
    conversation_description: Optional[str] = Field(
        default=None,
        description="Optional context about the conversation domain",
    )


class RAGQueryOutput(BaseModel):
    """Output schema for RAG query tool."""

    documents: List[Dict[str, Any]] = Field(
        description="List of documents with id, content, source, metadata"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Retrieval metadata: total_documents, relevant_documents, source_count, sources",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )


class RAGToolDefinition:
    """MCP Tool definition for RAG agent (Assistant Mode Compatible)."""

    name = "knowledge_expert"
    description = """Retrieve relevant documents from the knowledge base using RAG.

ASSISTANT MODE CONFIGURATION (Default):
- Strategy: custom_variants (matching supervisor agent pattern)
- LLM Generation: Disabled (returns raw documents for agent processing)

This tool performs:
1. Query enhancement using custom_variants strategy
2. Vector similarity search with multiple query variants
3. Document reranking with relevance scoring
4. Returns structured documents (no LLM generation in assistant mode)

Returns structured document results with metadata and relevance scores.

Use this tool whenever you need to:
- Find information from the knowledge base
- Answer questions based on stored documents
- Retrieve context for further processing by the agent
"""

    input_schema = RAGQueryInput
    output_schema = RAGQueryOutput

    @staticmethod
    def get_mcp_tool_definition() -> Dict[str, Any]:
        """Get MCP-compliant tool definition."""
        return {
            "name": RAGToolDefinition.name,
            "description": RAGToolDefinition.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 5,
                        "maxItems": 5,
                        "description": (
                            "List of exactly 5 diverse query variants for comprehensive retrieval. "
                            "CRITICAL: ALL variants MUST be in the SAME LANGUAGE as the original user query. "
                            "Generate variants covering different aspects: "
                            "1) Exact user request (literal wording), "
                            "2) Alternative phrasing (synonyms in same language), "
                            "3) More specific/detailed version, "
                            "4) More general/broader version, "
                            "5) Related aspect or use case. "
                            "Example: If user asks in Arabic, ALL 5 variants must be in Arabic."
                        ),
                    },
                    "collection_name": {
                        "type": "string",
                        "description": "Vector database collection name",
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 30,
                        "description": "Number of documents to retrieve",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID for RAG workflow",
                    },
                    "embedding_provider_id": {
                        "type": "string",
                        "description": "Embedding provider ID (from collection config)",
                    },
                    "embedding_model_name": {
                        "type": "string",
                        "description": "Embedding model name (from collection config)",
                    },
                    "vector_dimension": {
                        "type": "integer",
                        "default": 1536,
                        "minimum": 1,
                        "maximum": 4096,
                        "description": "Vector dimension of embedding model (from collection config)",
                    },
                    "enable_reranking": {
                        "type": "boolean",
                        "default": False,
                        "description": "Enable document reranking by relevance using LLM provider",
                    },
                    "llm_provider_id": {
                        "type": "string",
                        "description": "LLM provider ID for reranking (required if enable_reranking is True)",
                    },
                    "llm_model_name": {
                        "type": "string",
                        "description": "LLM model name for reranking (required if enable_reranking is True)",
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Conversation ID for tracking",
                    },
                    "conversation_description": {
                        "type": "string",
                        "description": "Conversation domain context",
                    },
                },
                "required": [
                    "search_query",
                    "collection_name",
                    "user_id",
                    "embedding_provider_id",
                    "embedding_model_name",
                    "conversation_id",
                ],
            },
        }
