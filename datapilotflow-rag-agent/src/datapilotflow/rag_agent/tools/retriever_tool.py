"""
Retriever tool for DataPilotFlow workflow.

This module provides a LangChain retriever tool that searches the vector database
for relevant context to enrich the agent's responses.
"""

import asyncio
from typing import Any, Dict

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import create_retriever_tool
from loguru import logger

from datapilotflow.persistence.vectordb.milvus.client import MilvusClientWrapper
# TODO: from datapilotflow.services.knowledge.vectordb_collection_service import (
    get_vectordb_collection_service,
)
# TODO: from datapilotflow.services.model_provider.model_provider_service import (
    get_model_provider_service,
)


class MilvusRetriever(BaseRetriever):
    """Custom retriever that uses Milvus for vector search with collection-specific embedding config."""

    collection_name: str
    user_id: str
    top_k: int = 5
    # Optional embedding configuration from workflow (used if provided, otherwise fetched from collection)
    embedding_provider_id: str | None = None
    embedding_model_name: str | None = None
    vector_dimension: int | None = None

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
            logger.info("   " + "▼" * 50)
            logger.info(f"   🔎 MILVUS RETRIEVER: Starting vector search")
            logger.info(f"   📝 Query: '{query[:150]}...'")

            # Determine embedding configuration
            # Priority: Use provided config from MCP tool, otherwise fetch from collection
            if self.embedding_provider_id and self.embedding_model_name and self.vector_dimension:
                # Use provided embedding config from workflow
                embedding_provider_id = self.embedding_provider_id
                embedding_model_name = self.embedding_model_name
                vector_dimension = self.vector_dimension
                logger.info(f"   ℹ️  Using embedding config from workflow (MCP tool parameters)")
            else:
                # Fallback: Fetch from collection configuration
                logger.info(f"   ℹ️  Fetching embedding config from collection...")
                vectordb_service = get_vectordb_collection_service()
                collection_config = vectordb_service.get_collection_by_name(
                    self.collection_name
                )

                if not collection_config:
                    raise ValueError(f"Collection not found: {self.collection_name}")

                embedding_provider_id = collection_config.embedding_model_provider_id
                embedding_model_name = collection_config.embedding_model_name
                vector_dimension = collection_config.vector_dimension

            logger.info(f"   ⚙️  Collection: {self.collection_name}")
            logger.info(f"   ⚙️  Embedding provider ID: {embedding_provider_id}")
            logger.info(f"   ⚙️  Embedding model: {embedding_model_name}")
            logger.info(f"   ⚙️  Vector dimension: {vector_dimension}")
            logger.info(f"   ⚙️  Top K: {self.top_k}")

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
            from datapilotflow.domain.rag.rag_file_upload import RagFileUpload

            milvus_client = MilvusClientWrapper(
                model=RagFileUpload,
                collection_name=self.collection_name,
                vector_dimension=vector_dimension,
            )

            # Generate query embedding
            import litellm

            litellm_model = f"{provider.provider_type}/{embedding_model_name}"
            logger.info(f"   🧮 Generating embedding vector using {litellm_model}...")

            embedding_response = litellm.embedding(
                model=litellm_model,
                input=[query],
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
                dimensions=vector_dimension,
            )

            query_vector = embedding_response.data[0]["embedding"]
            logger.info(
                f"   ✅ Embedding vector generated: {len(query_vector)} dimensions"
            )
            logger.info(f"   ✅ First 5 dimensions: {query_vector[:5]}")

            # Search Milvus
            logger.info(
                f"   🔍 Searching Milvus collection '{self.collection_name}' with top_k={self.top_k}..."
            )
            results = milvus_client.search_with_vector(
                query_vector=query_vector,
                limit=self.top_k,
            )
            logger.info(f"   ✅ Milvus search complete: Found {len(results)} results")

            # Convert to LangChain Documents
            documents = []
            for i, result in enumerate(results):
                # Milvus search results have structure: {id, distance, score, properties}
                # The actual document fields are in 'properties'
                properties = result.get("properties", {})
                content = properties.get("page_content", properties.get("text", ""))

                # Debug logging for first result
                if i == 0:
                    logger.info(f"   📊 First result structure:")
                    logger.info(f"      Result keys: {list(result.keys())}")
                    logger.info(f"      Properties keys: {list(properties.keys())}")
                    logger.info(f"      Distance: {result.get('distance', 'N/A')}")

                doc = Document(
                    page_content=content,
                    metadata={
                        **{k: v for k, v in properties.items() if k != "page_content"},
                        "id": result.get("id"),
                        "distance": result.get("distance", 0.0),
                    },
                )
                documents.append(doc)

            logger.info(
                f"   ✅✅ MILVUS SEARCH COMPLETE: Retrieved {len(documents)} documents from {self.collection_name}"
            )
            logger.info("   " + "▲" * 50)

            return documents

        except Exception as e:
            logger.error(f"   ❌❌ MILVUS RETRIEVAL FAILED: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun = None
    ) -> list[Document]:
        """
        Async version: Retrieve relevant documents from Milvus without blocking event loop.

        This is the CORRECT method for async contexts (RAG agent). All blocking I/O
        operations are wrapped in asyncio.to_thread() to prevent event loop blocking.

        Args:
            query: The search query
            run_manager: Async callback manager for the retriever run

        Returns:
            List of relevant documents
        """
        try:
            logger.info("   " + "▼" * 50)
            logger.info(
                f"   🔎 MILVUS RETRIEVER (ASYNC): Starting vector search , Query: '{query[:150]}...'"
            )

            # Determine embedding configuration
            # Priority: Use provided config from MCP tool, otherwise fetch from collection
            if self.embedding_provider_id and self.embedding_model_name and self.vector_dimension:
                # Use provided embedding config from workflow
                embedding_provider_id = self.embedding_provider_id
                embedding_model_name = self.embedding_model_name
                vector_dimension = self.vector_dimension
                logger.info(f"   ℹ️  Using embedding config from workflow (MCP tool parameters)")
            else:
                # Fallback: Fetch from collection configuration
                logger.info(f"   ℹ️  Fetching embedding config from collection...")
                # Get collection configuration (MongoDB call - wrap in thread)
                vectordb_service = get_vectordb_collection_service()
                collection_config = await asyncio.to_thread(
                    vectordb_service.get_collection_by_name, self.collection_name
                )

                if not collection_config:
                    raise ValueError(f"Collection not found: {self.collection_name}")

                embedding_provider_id = collection_config.embedding_model_provider_id
                embedding_model_name = collection_config.embedding_model_name
                vector_dimension = collection_config.vector_dimension

            logger.info(
                f"   ⚙️  Collection: {self.collection_name}, Embedding provider: {embedding_provider_id}, "
                f"Embedding model: {embedding_model_name}, Vector dimension: {vector_dimension}, Top K: {self.top_k}"
            )
            model_provider_service = get_model_provider_service()
            provider = await asyncio.to_thread(
                model_provider_service.get_model_provider,
                embedding_provider_id,
                self.user_id,
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
            from datapilotflow.domain.rag.rag_file_upload import RagFileUpload

            milvus_client = MilvusClientWrapper(
                model=RagFileUpload,
                collection_name=self.collection_name,
                vector_dimension=vector_dimension,
            )

            # Generate query embedding (API call - wrap in thread)
            import litellm

            litellm_model = f"{provider.provider_type}/{embedding_model_name}"
            logger.info(f"   🧮 Generating embedding vector using {litellm_model}...")

            embedding_response = await asyncio.to_thread(
                litellm.embedding,
                model=litellm_model,
                input=[query],
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
                dimensions=vector_dimension,
            )

            query_vector = embedding_response.data[0]["embedding"]
            logger.info(
                f"   ✅ Embedding vector generated: {len(query_vector)} dimensions"
            )
            logger.info(f"   ✅ First 5 dimensions: {query_vector[:5]}")

            # Search Milvus (Milvus call - wrap in thread)
            logger.info(
                f"   🔍 Searching Milvus collection '{self.collection_name}' with top_k={self.top_k}..."
            )
            results = await asyncio.to_thread(
                milvus_client.search_with_vector,
                query_vector=query_vector,
                limit=self.top_k,
            )
            logger.info(f"   ✅ Milvus search complete: Found {len(results)} results")

            # Convert to LangChain Documents
            documents = []
            for i, result in enumerate(results):
                properties = result.get("properties", {})
                content = properties.get("page_content", properties.get("text", ""))

                if i == 0:
                    logger.info(f"   📊 First result structure:")
                    logger.info(f"      Result keys: {list(result.keys())}")
                    logger.info(f"      Properties keys: {list(properties.keys())}")
                    logger.info(f"      Distance: {result.get('distance', 'N/A')}")

                doc = Document(
                    page_content=content,
                    metadata={
                        **{k: v for k, v in properties.items() if k != "page_content"},
                        "id": result.get("id"),
                        "distance": result.get("distance", 0.0),
                    },
                )
                documents.append(doc)

            logger.info(
                f"   ✅✅ MILVUS ASYNC SEARCH COMPLETE: Retrieved {len(documents)} documents from {self.collection_name}"
            )
            logger.info("   " + "▲" * 50)

            return documents

        except Exception as e:
            logger.error(f"   ❌❌ MILVUS ASYNC RETRIEVAL FAILED: {e}")
            import traceback

            logger.error(traceback.format_exc())
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
