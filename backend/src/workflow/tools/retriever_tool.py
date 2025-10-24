"""
Retriever tool for DataPilotFlow workflow.

This module provides a LangChain retriever tool that searches the vector database
for relevant context to enrich the agent's responses.
"""

from typing import Any, Dict

from langchain.tools.retriever import create_retriever_tool
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from loguru import logger

from src.infrastructure.milvus.client import MilvusClientWrapper
from src.services.knowledge.vectordb_collection_service import (
    get_vectordb_collection_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)


class MilvusRetriever(BaseRetriever):
    """Custom retriever that uses Milvus for vector search."""

    collection_name: str
    user_id: str
    top_k: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> list[Document]:
        """
        Retrieve relevant documents from Milvus.

        Args:
            query: The search query
            run_manager: Callback manager for the retriever run

        Returns:
            List of relevant documents
        """
        try:
            logger.debug(f"🔍 Retrieving documents for query: '{query[:100]}...'")

            # Get collection configuration
            vectordb_service = get_vectordb_collection_service()
            collection_config = vectordb_service.get_collection_by_name(
                self.collection_name
            )

            if not collection_config:
                raise ValueError(f"Collection not found: {self.collection_name}")

            # Get embedding provider
            embedding_provider_id = collection_config.embedding_model_provider_id
            embedding_model_name = collection_config.embedding_model_name
            vector_dimension = collection_config.vector_dimension

            model_provider_service = get_model_provider_service()
            provider = model_provider_service.get_model_provider(
                embedding_provider_id, self.user_id
            )

            if not provider:
                raise ValueError(
                    f"Embedding provider not found: {embedding_provider_id}"
                )

            if not provider.embedding:
                raise ValueError(
                    f"Embedding not configured for provider: {provider.name}"
                )

            # Initialize Milvus client
            from src.domain.rag.rag_file_upload import RagFileUpload

            milvus_client = MilvusClientWrapper(
                model=RagFileUpload,
                collection_name=self.collection_name,
                vector_dimension=vector_dimension,
            )

            # Generate query embedding
            import litellm

            litellm_model = f"{provider.provider_type}/{embedding_model_name}"
            embedding_response = litellm.embedding(
                model=litellm_model,
                input=[query],
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
            )

            query_vector = embedding_response.data[0]["embedding"]

            # Search Milvus
            results = milvus_client.search_with_vector(
                query_vector=query_vector,
                limit=self.top_k,
            )

            # Convert to LangChain Documents
            documents = []
            for result in results:
                doc = Document(
                    page_content=result.get("text", ""),
                    metadata={
                        **result.get("metadata", {}),
                        "id": result.get("id"),
                        "distance": result.get("distance", 0.0),
                    },
                )
                documents.append(doc)

            logger.info(
                f"✅ Retrieved {len(documents)} documents from {self.collection_name}"
            )

            return documents

        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            return []


def get_retriever_tool(
    collection_name: str,
    user_id: str,
    top_k: int = 5,
) -> Any:
    """
    Create a retriever tool for the workflow.

    Args:
        collection_name: Name of the Milvus collection to search
        user_id: User ID for provider access
        top_k: Number of documents to retrieve

    Returns:
        LangChain retriever tool
    """
    logger.debug(
        f"Creating retriever tool for collection '{collection_name}' with top_k={top_k}"
    )

    # Create the retriever
    retriever = MilvusRetriever(
        collection_name=collection_name,
        user_id=user_id,
        top_k=top_k,
    )

    # Create the tool
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_knowledge_context",
        "Search and return relevant information from the knowledge base. "
        "Always use this tool when you need to find specific information, "
        "answer questions, or provide context from the stored documents.",
    )

    return retriever_tool
