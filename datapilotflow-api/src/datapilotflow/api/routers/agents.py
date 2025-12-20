"""
Agent query endpoints.

Exposes RAG and Assistant agent capabilities via REST API.
Supports both standard responses and streaming.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """RAG query request model."""
    query: str = Field(..., description="Search query for knowledge base")
    collection_name: str = Field(..., description="Collection to search in")
    user_id: str = Field(..., description="User ID")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    enable_reranking: bool = Field(default=True, description="Enable result reranking")


class DocumentResult(BaseModel):
    """Document search result."""
    id: str
    content: str
    source: str
    metadata: dict


class RAGQueryResponse(BaseModel):
    """RAG query response model."""
    query: str
    documents: list[DocumentResult]
    total_count: int
    sources: list[str]


class AssistantMessageRequest(BaseModel):
    """Assistant message request model."""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    agent_id: Optional[str] = Field(default=None, description="Optional agent ID")


class AssistantMessageResponse(BaseModel):
    """Assistant message response model."""
    message: str
    conversation_id: str
    message_id: str


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag_agent(request: RAGQueryRequest) -> RAGQueryResponse:
    """
    Query the RAG agent with retrieval-augmented generation.

    Retrieves relevant documents from the knowledge base and returns them
    along with metadata and sources.

    Args:
        request: RAG query parameters

    Returns:
        RAGQueryResponse: Retrieved documents and metadata
    """
    try:
        logger.info(
            f"RAG query - query={request.query}, collection={request.collection_name}, user={request.user_id}"
        )

        # TODO: Integrate with actual RAGAgentService
        # from datapilotflow.agents import RAGAgentService
        # rag_service = RAGAgentService()
        # results = await rag_service.query(request)

        return RAGQueryResponse(
            query=request.query,
            documents=[],
            total_count=0,
            sources=[],
        )
    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/message", response_model=AssistantMessageResponse)
async def send_assistant_message(request: AssistantMessageRequest) -> AssistantMessageResponse:
    """
    Send a message to the Assistant agent.

    Processes the user message and returns the assistant's response.
    Supports planning, tool calling, and multi-turn conversations.

    Args:
        request: Assistant message parameters

    Returns:
        AssistantMessageResponse: Assistant's response
    """
    try:
        logger.info(
            f"Assistant message - conversation={request.conversation_id}, user={request.user_id}"
        )

        # TODO: Integrate with actual Assistant agent
        # from datapilotflow.agents import create_assistant_agent_for_conversation
        # agent = await create_assistant_agent_for_conversation(request.conversation_id, ...)
        # response = await agent.invoke(request.message)

        return AssistantMessageResponse(
            message="Assistant response placeholder",
            conversation_id=request.conversation_id,
            message_id="msg_123",
        )
    except Exception as e:
        logger.error(f"Assistant message failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
