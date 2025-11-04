"""
Conversation History Service for Knowledge Search

This module provides conversation history management for knowledge search sessions,
enabling context-aware responses that understand previous interactions.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger
from pymongo import MongoClient

from src.config import settings


class QueryEnhancementStrategy(str, Enum):
    """Available query enhancement strategies."""

    NONE = "none"
    AUGMENTED = "augmented"
    MULTI_QUERY = "multi_query"
    HYDE = "hyde"
    DECOMPOSITION = "decomposition"
    QUERY_FUSION = "query_fusion"


class RetrievalStrategy(str, Enum):
    """Available multi-query retrieval strategies."""

    SINGLE_QUERY = "single_query"  # Use only first query variant (fast, less coverage)
    RECIPROCAL_RANK_FUSION = (
        "reciprocal_rank_fusion"  # Use all variants with RRF (slower, better quality)
    )


@dataclass
class EnhancementConfiguration:
    """Query enhancement configuration for a conversation."""

    strategy: str = "none"
    enabled: bool = False
    config: Optional[Dict[str, Any]] = None
    configured_at: Optional[datetime] = None


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    search_query: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    source_urls: Optional[List[str]] = None
    # Enhancement metadata
    enhancement_strategy_used: Optional[str] = None
    enhanced_queries: Optional[List[str]] = None
    # Performance metrics
    processing_time_ms: Optional[int] = None
    document_count: Optional[int] = None


@dataclass
class ConversationSession:
    """Represents a conversation session with history."""

    _id: str  # MongoDB _id as primary identifier
    user_id: str
    created_at: datetime
    last_updated: datetime
    messages: List[ConversationMessage]
    name: Optional[str] = None
    description: Optional[str] = None
    context_summary: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    knowledge_sources_used: Optional[List[str]] = None
    # LLM Provider reference
    llm_provider_id: Optional[str] = None
    llm_model_name: Optional[str] = None
    # Query Enhancement configuration
    enhancement_config: Optional[EnhancementConfiguration] = None
    # Collection configuration
    collection_name: str = "LongTermMemory"
    # Reranking configuration
    enable_reranking: bool = False  # Enable document judging/reranking by default
    relevance_threshold: float = 0.5  # Relevance score threshold for filtering documents
    reranker_provider_id: Optional[str] = (
        None  # Dedicated reranker provider (Cohere/Voyage)
    )
    reranker_model_name: Optional[str] = None  # Reranker model name
    # Answer generation configuration
    enable_llm_generation: bool = (
        False  # Enable LLM answer generation (False = raw results by default, True = generated answers)
    )
    # Vector search configuration
    top_k: int = 5  # Number of documents to retrieve from vector database
    # Multi-agent orchestration configuration
    enable_knowledge_assistant: bool = (
        True  # Enable Knowledge Assistant for RAG→Task workflow (True = multi-agent orchestration, False = RAG only)
    )
    # Session statistics
    total_queries: int = 0
    total_documents_retrieved: int = 0
    average_response_time_ms: Optional[float] = None
    # Tags for organization
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.topics_discussed is None:
            self.topics_discussed = []
        if self.knowledge_sources_used is None:
            self.knowledge_sources_used = []
        if self.tags is None:
            self.tags = []
        # Generate default name if none provided
        if self.name is None:
            self.name = f"Session {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def message_count(self) -> int:
        """Get the number of messages in this session."""
        return len(self.messages)

    @property
    def has_llm_provider(self) -> bool:
        """Check if LLM provider is configured."""
        return self.llm_provider_id is not None

    @property
    def has_enhancement_config(self) -> bool:
        """Check if enhancement configuration is set."""
        return self.enhancement_config is not None

    @property
    def current_strategy(self) -> str:
        """Get current enhancement strategy."""
        if self.enhancement_config and self.enhancement_config.enabled:
            return self.enhancement_config.strategy
        return "none"


class ConversationHistoryService:
    """Service for managing conversation history for knowledge search."""

    def __init__(self):
        from src.infrastructure.mongo.client import get_mongo_client

        self.client = get_mongo_client()
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db["knowledge_conversation_history"]

        # Create indexes for efficient querying
        self.collection.create_index([("user_id", 1), ("last_updated", -1)])
        self.collection.create_index([("_id", 1)])
        self.collection.create_index(
            [("last_updated", 1)], expireAfterSeconds=86400 * 30
        )  # 30 days TTL

    def create_conversation(
        self,
        user_id: str,
        name: Optional[str] = None,
        llm_provider_id: Optional[str] = None,
        llm_model_name: Optional[str] = None,
        enhancement_strategy: Optional[str] = None,
        collection_name: str = "LongTermMemory",
        enable_reranking: bool = False,
        relevance_threshold: float = 0.5,
        reranker_provider_id: Optional[str] = None,
        reranker_model_name: Optional[str] = None,
        enable_llm_generation: bool = False,
        top_k: int = 5,
        enable_knowledge_assistant: bool = True,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> str:
        """Create a new conversation with optional configuration."""

        # Validate LLM provider exists if provided
        if llm_provider_id:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider(llm_provider_id, user_id)

                if not provider:
                    logger.warning(f"LLM provider not found: {llm_provider_id}")
                    llm_provider_id = None
                elif not provider.is_active:
                    logger.warning(f"LLM provider is not active: {provider.name}")
                    llm_provider_id = None
            except Exception as e:
                logger.error(f"Error validating LLM provider: {e}")
                llm_provider_id = None

        # Validate reranker provider exists if provided
        if reranker_provider_id:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider(
                    reranker_provider_id, user_id
                )

                if not provider:
                    logger.warning(
                        f"Reranker provider not found: {reranker_provider_id}"
                    )
                    reranker_provider_id = None
                    reranker_model_name = None
                elif not provider.is_active:
                    logger.warning(f"Reranker provider is not active: {provider.name}")
                    reranker_provider_id = None
                    reranker_model_name = None
                elif not provider.reranker:
                    logger.warning(
                        f"Provider does not support reranking: {provider.name}"
                    )
                    reranker_provider_id = None
                    reranker_model_name = None
            except Exception as e:
                logger.error(f"Error validating reranker provider: {e}")
                reranker_provider_id = None
                reranker_model_name = None

        # Create enhancement configuration
        enhancement_config = None
        if enhancement_strategy and enhancement_strategy != "none":
            enhancement_config = {
                "strategy": enhancement_strategy,
                "enabled": True,
                "config": None,
                "configured_at": datetime.utcnow(),
            }
        else:
            enhancement_config = {
                "strategy": "none",
                "enabled": False,
                "config": None,
                "configured_at": datetime.utcnow(),
            }

        # Create conversation data
        conversation_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "messages": [],
            "name": name,
            "description": description,
            "context_summary": None,
            "topics_discussed": [],
            "knowledge_sources_used": [],
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "enhancement_config": enhancement_config,
            "collection_name": collection_name,
            "enable_reranking": enable_reranking,
            "relevance_threshold": relevance_threshold,
            "reranker_provider_id": reranker_provider_id,
            "reranker_model_name": reranker_model_name,
            "enable_llm_generation": enable_llm_generation,
            "top_k": top_k,
            "enable_knowledge_assistant": enable_knowledge_assistant,
            "total_queries": 0,
            "total_documents_retrieved": 0,
            "average_response_time_ms": None,
            "tags": tags or [],
        }

        # Insert and get the MongoDB _id
        result = self.collection.insert_one(conversation_data)
        conversation_id = str(result.inserted_id)

        logger.info(
            f"Created conversation {conversation_id} for user {user_id} "
            f"with provider: {llm_provider_id}, strategy: {enhancement_strategy}"
        )
        return conversation_id

    def get_conversation(
        self, conversation_id: str, user_id: str = None
    ) -> Optional[ConversationSession]:
        """Retrieve a conversation by ID."""
        from bson import ObjectId

        try:
            # Query by MongoDB _id
            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            doc = self.collection.find_one(query)
            if doc:
                # Convert back to ConversationSession
                messages = []
                for msg_doc in doc.get("messages", []):
                    msg = ConversationMessage(
                        role=msg_doc["role"],
                        content=msg_doc["content"],
                        timestamp=msg_doc["timestamp"],
                        search_query=msg_doc.get("search_query"),
                        search_results=msg_doc.get("search_results"),
                        source_urls=msg_doc.get("source_urls"),
                        enhancement_strategy_used=msg_doc.get(
                            "enhancement_strategy_used"
                        ),
                        enhanced_queries=msg_doc.get("enhanced_queries"),
                        processing_time_ms=msg_doc.get("processing_time_ms"),
                        document_count=msg_doc.get("document_count"),
                    )
                    messages.append(msg)

                # Parse enhancement config
                enhancement_config = None
                if doc.get("enhancement_config"):
                    ec = doc["enhancement_config"]
                    enhancement_config = EnhancementConfiguration(
                        strategy=ec.get("strategy", "none"),
                        enabled=ec.get("enabled", False),
                        config=ec.get("config"),
                        configured_at=ec.get("configured_at"),
                    )

                session = ConversationSession(
                    _id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    created_at=doc["created_at"],
                    last_updated=doc["last_updated"],
                    messages=messages,
                    name=doc.get("name"),
                    description=doc.get("description"),
                    context_summary=doc.get("context_summary"),
                    topics_discussed=doc.get("topics_discussed", []),
                    knowledge_sources_used=doc.get("knowledge_sources_used", []),
                    llm_provider_id=doc.get("llm_provider_id"),
                    llm_model_name=doc.get("llm_model_name"),
                    enhancement_config=enhancement_config,
                    collection_name=doc.get("collection_name", "LongTermMemory"),
                    enable_reranking=doc.get("enable_reranking", False),
                    reranker_provider_id=doc.get("reranker_provider_id"),
                    reranker_model_name=doc.get("reranker_model_name"),
                    enable_llm_generation=doc.get("enable_llm_generation", False),
                    total_queries=doc.get("total_queries", 0),
                    total_documents_retrieved=doc.get("total_documents_retrieved", 0),
                    average_response_time_ms=doc.get("average_response_time_ms"),
                    tags=doc.get("tags", []),
                    top_k=doc.get("top_k", 5),
                    enable_knowledge_assistant=doc.get("enable_knowledge_assistant", True),
                )
                return session
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
            return None

    def get_conversation_messages(
        self, conversation_id: str, user_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific session."""
        session = self.get_conversation(conversation_id, user_id)
        if not session:
            return []

        # Convert messages to dictionary format for API response
        messages = []
        for msg in session.messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            if msg.search_query:
                message_dict["search_query"] = msg.search_query
            if msg.source_urls:
                message_dict["source_urls"] = msg.source_urls
            messages.append(message_dict)

        return messages

    def get_user_conversations(
        self, user_id: str, limit: int = 10
    ) -> List[ConversationSession]:
        """Get recent conversation sessions for a user."""
        docs = (
            self.collection.find({"user_id": user_id})
            .sort("last_updated", -1)
            .limit(limit)
        )

        sessions = []
        for doc in docs:
            # Convert messages
            messages = []
            for msg_doc in doc.get("messages", []):
                msg = ConversationMessage(
                    role=msg_doc["role"],
                    content=msg_doc["content"],
                    timestamp=msg_doc["timestamp"],
                    search_query=msg_doc.get("search_query"),
                    search_results=msg_doc.get("search_results"),
                    source_urls=msg_doc.get("source_urls"),
                    enhancement_strategy_used=msg_doc.get("enhancement_strategy_used"),
                    enhanced_queries=msg_doc.get("enhanced_queries"),
                    processing_time_ms=msg_doc.get("processing_time_ms"),
                    document_count=msg_doc.get("document_count"),
                )
                messages.append(msg)

            # Parse enhancement config
            enhancement_config = None
            if doc.get("enhancement_config"):
                ec = doc["enhancement_config"]
                enhancement_config = EnhancementConfiguration(
                    strategy=ec.get("strategy", "none"),
                    enabled=ec.get("enabled", False),
                    config=ec.get("config"),
                    configured_at=ec.get("configured_at"),
                )

            session = ConversationSession(
                _id=str(doc["_id"]),
                user_id=doc["user_id"],
                created_at=doc["created_at"],
                last_updated=doc["last_updated"],
                messages=messages,
                name=doc.get("name"),
                description=doc.get("description"),
                context_summary=doc.get("context_summary"),
                topics_discussed=doc.get("topics_discussed", []),
                knowledge_sources_used=doc.get("knowledge_sources_used", []),
                llm_provider_id=doc.get("llm_provider_id"),
                llm_model_name=doc.get("llm_model_name"),
                enhancement_config=enhancement_config,
                collection_name=doc.get("collection_name", "LongTermMemory"),
                total_queries=doc.get("total_queries", 0),
                total_documents_retrieved=doc.get("total_documents_retrieved", 0),
                average_response_time_ms=doc.get("average_response_time_ms"),
                tags=doc.get("tags", []),
            )
            sessions.append(session)

        return sessions

    def get_session_messages(
        self, session_id: str, user_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific session."""
        session = self.get_conversation(session_id, user_id)
        if not session:
            return []

        messages = []
        for msg in session.messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            if msg.search_query:
                message_dict["search_query"] = msg.search_query
            if msg.source_urls:
                message_dict["source_urls"] = msg.source_urls
            messages.append(message_dict)

        return messages

    def add_message(self, session_id: str, message: ConversationMessage) -> bool:
        """Add a message to a conversation session."""
        try:
            # Update the session with new message
            update_data = {
                "$push": {"messages": asdict(message)},
                "$set": {"last_updated": datetime.utcnow()},
            }

            # Update topics and sources if available
            if message.search_query:
                update_data["$addToSet"] = {"topics_discussed": message.search_query}

            if message.source_urls:
                update_data["$addToSet"] = {
                    "knowledge_sources_used": {"$each": message.source_urls}
                }

            from bson import ObjectId

            result = self.collection.update_one(
                {"_id": ObjectId(session_id)}, update_data
            )

            if result.modified_count > 0:
                logger.debug(f"Added message to session: {session_id}")
                return True
            else:
                logger.warning(f"Failed to add message to session: {session_id}")
                return False

        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False

    def get_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Get conversation context for LLM prompt."""
        session = self.get_conversation(session_id)
        if not session or not session.messages:
            return ""

        # Get recent messages
        recent_messages = session.messages[-max_messages:]

        context_parts = []
        context_parts.append("CONVERSATION HISTORY:")
        context_parts.append("=" * 50)

        for msg in recent_messages:
            role = "User" if msg.role == "user" else "Assistant"
            timestamp = msg.timestamp.strftime("%H:%M")
            context_parts.append(f"[{timestamp}] {role}: {msg.content}")

            # Add search context if available
            if msg.search_query and msg.source_urls:
                context_parts.append(f"  Search Query: {msg.search_query}")
                context_parts.append(
                    f"  Sources: {', '.join(msg.source_urls[:3])}"
                )  # Limit to 3 sources

        context_parts.append("=" * 50)

        return "\n".join(context_parts)

    def update_context_summary(self, session_id: str, summary: str) -> bool:
        """Update the context summary for a session."""
        from bson import ObjectId

        try:
            result = self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "context_summary": summary,
                        "last_updated": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(
                f"Error updating context summary for session {session_id}: {e}"
            )
            return False

    def rename_conversation(
        self, conversation_id: str, new_name: str, user_id: str = None
    ) -> bool:
        """Rename a conversation session."""
        from bson import ObjectId

        try:
            if not new_name or not new_name.strip():
                logger.warning(f"Cannot rename session {conversation_id} to empty name")
                return False

            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            result = self.collection.update_one(
                query,
                {"$set": {"name": new_name.strip(), "last_updated": datetime.utcnow()}},
            )

            if result.modified_count > 0:
                logger.info(f"Renamed session {conversation_id} to: {new_name}")
                return True
            else:
                logger.warning(f"Failed to rename session {conversation_id}")
                return False

        except Exception as e:
            logger.error(f"Error renaming session {conversation_id}: {e}")
            return False

    def delete_conversation(self, conversation_id: str, user_id: str = None) -> bool:
        """Delete a conversation session."""
        from bson import ObjectId

        try:
            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False

    def reset_conversation_messages(
        self, conversation_id: str, user_id: str = None
    ) -> bool:
        """Reset messages for a specific conversation session."""
        from bson import ObjectId

        try:
            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            result = self.collection.update_one(
                query,
                {
                    "$set": {
                        "messages": [],
                        "context_summary": None,
                        "topics_discussed": [],
                        "knowledge_sources_used": [],
                        "last_updated": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(f"Reset messages for session {conversation_id}")
                return True
            else:
                logger.warning(
                    f"Failed to reset messages for session {conversation_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error resetting messages for session {conversation_id}: {e}")
            return False

    def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        try:
            result = self.collection.delete_many({"last_updated": {"$lt": cutoff_date}})
            logger.info(f"Cleaned up {result.deleted_count} old conversations")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            return 0

    def get_recent_context(self, user_id: str, limit: int = 5) -> str:
        """Get recent conversation context for a user."""
        try:
            # Get recent sessions
            recent_sessions = self.get_user_conversations(user_id, limit=limit)

            if not recent_sessions:
                return ""

            context_parts = []
            context_parts.append("RECENT CONVERSATION CONTEXT:")
            context_parts.append("=" * 50)

            for session in recent_sessions:
                if session.messages:
                    context_parts.append(f"Session: {session.name}")
                    context_parts.append(
                        f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )

                    # Get last few messages from this session
                    recent_messages = session.messages[-3:]  # Last 3 messages
                    for msg in recent_messages:
                        role = "User" if msg.role == "user" else "Assistant"
                        timestamp = msg.timestamp.strftime("%H:%M")
                        context_parts.append(
                            f"[{timestamp}] {role}: {msg.content[:100]}..."
                        )  # Truncate long messages

                    context_parts.append("-" * 30)

            context_parts.append("=" * 50)
            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting recent context for user {user_id}: {e}")
            return ""

    def update_conversation_config(
        self,
        conversation_id: str,
        user_id: str,
        llm_provider_id: Optional[str] = None,
        llm_model_name: Optional[str] = None,
        enhancement_strategy: Optional[str] = None,
        collection_name: Optional[str] = None,
        enable_reranking: Optional[bool] = None,
        relevance_threshold: Optional[float] = None,
        reranker_provider_id: Optional[str] = None,
        reranker_model_name: Optional[str] = None,
        enable_llm_generation: Optional[bool] = None,
        top_k: Optional[int] = None,
        tags: Optional[List[str]] = None,
        enable_knowledge_assistant: Optional[bool] = None,
    ) -> bool:
        """Update conversation configuration."""
        from bson import ObjectId

        try:
            update_data = {"$set": {"last_updated": datetime.utcnow()}}

            # Update LLM provider
            if llm_provider_id is not None:
                # Validate provider if provided
                if llm_provider_id:
                    from src.services.model_provider.model_provider_service import (
                        get_model_provider_service,
                    )

                    provider_service = get_model_provider_service()
                    provider = provider_service.get_model_provider(
                        llm_provider_id, user_id
                    )

                    if not provider:
                        logger.warning(f"LLM provider not found: {llm_provider_id}")
                        return False
                    if not provider.is_active:
                        logger.warning(f"LLM provider is not active: {provider.name}")
                        return False

                update_data["$set"]["llm_provider_id"] = llm_provider_id

            # Update model name
            if llm_model_name is not None:
                update_data["$set"]["llm_model_name"] = llm_model_name

            # Update enhancement config
            if enhancement_strategy is not None:
                update_data["$set"]["enhancement_config"] = {
                    "strategy": enhancement_strategy,
                    "enabled": enhancement_strategy != "none",
                    "config": None,
                    "configured_at": datetime.utcnow(),
                }

            # Update collection name
            if collection_name is not None:
                update_data["$set"]["collection_name"] = collection_name

            # Update reranking settings
            if enable_reranking is not None:
                update_data["$set"]["enable_reranking"] = enable_reranking

            # Update relevance threshold
            if relevance_threshold is not None:
                update_data["$set"]["relevance_threshold"] = relevance_threshold

            # Update reranker provider
            if reranker_provider_id is not None:
                # Validate reranker provider if provided
                if reranker_provider_id:
                    from src.services.model_provider.model_provider_service import (
                        get_model_provider_service,
                    )

                    provider_service = get_model_provider_service()
                    provider = provider_service.get_model_provider(
                        reranker_provider_id, user_id
                    )

                    if not provider:
                        logger.warning(
                            f"Reranker provider not found: {reranker_provider_id}"
                        )
                        return False
                    if not provider.is_active:
                        logger.warning(
                            f"Reranker provider is not active: {provider.name}"
                        )
                        return False
                    if not provider.reranker:
                        logger.warning(
                            f"Provider does not support reranking: {provider.name}"
                        )
                        return False

                update_data["$set"]["reranker_provider_id"] = reranker_provider_id

            # Update reranker model name
            if reranker_model_name is not None:
                update_data["$set"]["reranker_model_name"] = reranker_model_name

            # Update LLM generation settings
            if enable_llm_generation is not None:
                update_data["$set"]["enable_llm_generation"] = enable_llm_generation

            # Update top_k
            if top_k is not None:
                if top_k < 3 or top_k > 10:
                    logger.warning(
                        f"Invalid top_k value: {top_k}. Must be between 3 and 10"
                    )
                    return False
                update_data["$set"]["top_k"] = top_k

            # Update tags
            if tags is not None:
                update_data["$set"]["tags"] = tags

            # Update enable_knowledge_assistant (Enable Knowledge Assistant)
            if enable_knowledge_assistant is not None:
                update_data["$set"]["enable_knowledge_assistant"] = enable_knowledge_assistant

            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id}, update_data
            )

            if result.modified_count > 0:
                logger.info(f"Updated configuration for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"No changes made to conversation {conversation_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating conversation config {conversation_id}: {e}")
            return False

    def get_conversation_with_provider(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with expanded provider details."""
        session = self.get_conversation(conversation_id, user_id)
        if not session:
            return None

        result = {"session": session, "llm_provider": None}

        # Fetch provider details if configured
        if session.llm_provider_id:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider_response(
                    session.llm_provider_id, user_id
                )

                if provider:
                    result["llm_provider"] = {
                        "id": provider.id,
                        "name": provider.name,
                        "provider_type": provider.provider_type,
                        "is_active": provider.is_active,
                        "generative": provider.generative,
                    }
            except Exception as e:
                logger.error(f"Error fetching provider details: {e}")

        return result

    def update_conversation_statistics(
        self,
        conversation_id: str,
        document_count: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
    ) -> bool:
        """Update conversation statistics after a query."""
        from bson import ObjectId

        try:
            # Get current session to calculate averages
            session = self.get_conversation(conversation_id)
            if not session:
                return False

            update_data = {
                "$inc": {"total_queries": 1},
                "$set": {"last_updated": datetime.utcnow()},
            }

            if document_count is not None:
                update_data["$inc"]["total_documents_retrieved"] = document_count

            # Calculate average response time
            if processing_time_ms is not None:
                if session.average_response_time_ms is None:
                    # First query
                    update_data["$set"]["average_response_time_ms"] = float(
                        processing_time_ms
                    )
                else:
                    # Calculate moving average
                    total_time = (
                        session.average_response_time_ms * session.total_queries
                    )
                    new_average = (total_time + processing_time_ms) / (
                        session.total_queries + 1
                    )
                    update_data["$set"]["average_response_time_ms"] = new_average

            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)}, update_data
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(
                f"Error updating conversation statistics {conversation_id}: {e}"
            )
            return False


# Global instance
conversation_history_service = ConversationHistoryService()
