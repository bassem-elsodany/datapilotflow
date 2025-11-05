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
class ProviderConfig:
    """Provider and model configuration."""

    id: str  # Provider ID
    model_name: str  # Model name


@dataclass
class EnhancementConfig:
    """Query enhancement configuration for a conversation."""

    strategy: str  # "native", "multi_query", "augmented", "hyde", "decomposition"
    provider: Optional[ProviderConfig] = None  # Provider for enhancement (e.g., embedding model)


@dataclass
class VectorDatabaseConfig:
    """Vector database configuration."""

    collection_name: str = "LongTermMemory"
    top_k: int = 5  # Number of documents to retrieve


@dataclass
class RerankerConfig:
    """Document reranker configuration."""

    provider: Optional[ProviderConfig] = None  # Reranker provider
    relevance_threshold: float = 0.5  # Relevance score threshold (0-1)


@dataclass
class AnswerGenerationConfig:
    """Answer generation configuration."""

    provider: Optional[ProviderConfig] = None  # LLM provider for answer generation


@dataclass
class SystemPrompt:
    """Embedded system prompt for a conversation."""

    id: str  # UUID identifier
    title: str  # Prompt title
    content: str  # Actual prompt content


# Legacy class kept for backwards compatibility during migration
@dataclass
class EnhancementConfiguration:
    """Query enhancement configuration for a conversation."""

    strategy: str = "none"
    enabled: bool = False
    config: Optional[Dict[str, Any]] = None
    configured_at: Optional[datetime] = None


@dataclass
class SystemPromptTask:
    """Represents a reusable system prompt template for a conversation."""

    id: str  # UUID identifier
    user_id: str
    conversation_id: str
    name: str  # e.g., "Code Reviewer", "Document Summarizer", "Technical Writer"
    description: Optional[str] = None  # Description of what this prompt does
    system_prompt: str = ""  # The actual system prompt template
    tags: Optional[List[str]] = None  # Tags for organization and filtering
    is_active: bool = True  # Whether this prompt is active and available for use
    usage_count: int = 0  # Number of times this prompt has been used
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None  # User who created this prompt
    version: int = 1  # Version number for tracking changes

    def __post_init__(self):
        if self.id is None or self.id == "":
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.created_by is None:
            self.created_by = self.user_id

    @property
    def is_empty(self) -> bool:
        """Check if the prompt is empty."""
        return not self.system_prompt or self.system_prompt.strip() == ""


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    search_query: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    source_urls: Optional[List[str]] = None
    chunk_ids: Optional[List[str]] = None
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
    # Nested configuration structures
    system_prompt: Optional[SystemPrompt] = None  # Embedded system prompt
    enhancement: Optional[EnhancementConfig] = None  # Query enhancement configuration
    vector_database: Optional[VectorDatabaseConfig] = None  # Vector database configuration
    reranker: Optional[RerankerConfig] = None  # Document reranker configuration
    answer_generation: Optional[AnswerGenerationConfig] = None  # Answer generation configuration
    # Tags for organization
    tags: Optional[List[str]] = None
    # Multi-agent orchestration configuration
    # True = Supervisor Agent (multi-agent orchestration)
    # False = RAG Agent (retrieval + generation only)
    enable_knowledge_assistant: bool = False

    def __post_init__(self):
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
    def agent_type(self) -> str:
        """Get agent type based on enable_knowledge_assistant flag."""
        return "supervisor" if self.enable_knowledge_assistant else "rag"

    @property
    def has_answer_generation(self) -> bool:
        """Check if answer generation is configured."""
        return self.answer_generation is not None and self.answer_generation.provider is not None

    @property
    def has_enhancement(self) -> bool:
        """Check if enhancement configuration is set."""
        return self.enhancement is not None and self.enhancement.strategy != "native"

    @property
    def current_strategy(self) -> str:
        """Get current enhancement strategy."""
        if self.enhancement:
            return self.enhancement.strategy
        return "native"

    @property
    def has_system_prompt(self) -> bool:
        """Check if system prompt is configured."""
        return self.system_prompt is not None and bool(self.system_prompt.content.strip())

    @property
    def has_reranker(self) -> bool:
        """Check if reranker is configured."""
        return self.reranker is not None and self.reranker.provider is not None


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
        selected_system_prompt_id: Optional[str] = None,
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
            "selected_system_prompt_id": selected_system_prompt_id,
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
        """Get messages for a specific session with all metadata."""
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

            # Build metadata object with all available fields
            metadata = {}
            if msg.search_query:
                metadata["search_query"] = msg.search_query
            if msg.source_urls:
                metadata["source_urls"] = msg.source_urls
            if msg.chunk_ids:
                metadata["chunk_ids"] = msg.chunk_ids
            if msg.document_count is not None:
                metadata["document_count"] = msg.document_count
            if msg.enhancement_strategy_used:
                metadata["enhancement_strategy"] = msg.enhancement_strategy_used
            if msg.enhanced_queries:
                metadata["enhanced_queries"] = msg.enhanced_queries
            if msg.processing_time_ms is not None:
                metadata["processing_time_ms"] = msg.processing_time_ms

            # Only add metadata if it's not empty
            if metadata:
                message_dict["metadata"] = metadata

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
        selected_system_prompt_id: Optional[str] = None,
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

            # Update selected system prompt ID
            if selected_system_prompt_id is not None:
                update_data["$set"]["selected_system_prompt_id"] = selected_system_prompt_id

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

    # ============ System Prompt Tasks Management (Phase 1 - Core CRUD) ============

    def create_system_prompt(
        self,
        user_id: str,
        conversation_id: str,
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[SystemPromptTask]:
        """
        Create a new system prompt task for a conversation.

        Args:
            user_id: User who owns the conversation
            conversation_id: Conversation ID
            name: Name of the system prompt (e.g., "Code Reviewer")
            system_prompt: The actual system prompt content
            description: Optional description of what this prompt does
            tags: Optional tags for organization

        Returns:
            Created SystemPromptTask or None if failed
        """
        try:
            from bson import ObjectId

            # Validate conversation exists and belongs to user
            doc = self.collection.find_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id}
            )
            if not doc:
                logger.warning(
                    f"Conversation not found: {conversation_id} for user {user_id}"
                )
                return None

            # Create the system prompt task
            task = SystemPromptTask(
                id="",  # Will be generated in __post_init__
                user_id=user_id,
                conversation_id=conversation_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                tags=tags or [],
                is_active=True,
                usage_count=0,
                created_by=user_id,
                version=1,
            )

            # Convert to dict for storage
            task_dict = asdict(task)

            # Add to conversation's system_prompt_tasks array
            update_result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"system_prompt_tasks": task_dict},
                    "$set": {"last_updated": datetime.utcnow()},
                },
            )

            if update_result.modified_count > 0:
                logger.info(
                    f"Created system prompt '{name}' for conversation {conversation_id}"
                )
                return task
            else:
                logger.warning(
                    f"Failed to create system prompt for conversation {conversation_id}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating system prompt: {e}")
            return None

    def get_system_prompt(
        self, conversation_id: str, prompt_id: str, user_id: str = None
    ) -> Optional[SystemPromptTask]:
        """
        Get a specific system prompt by ID.

        Args:
            conversation_id: Conversation ID
            prompt_id: System prompt ID
            user_id: Optional user ID for validation

        Returns:
            SystemPromptTask or None if not found
        """
        try:
            from bson import ObjectId

            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            doc = self.collection.find_one(
                query, {"system_prompt_tasks": {"$elemMatch": {"id": prompt_id}}}
            )

            if doc and "system_prompt_tasks" in doc and len(doc["system_prompt_tasks"]) > 0:
                prompt_dict = doc["system_prompt_tasks"][0]
                return self._dict_to_system_prompt(prompt_dict)

            logger.debug(f"System prompt not found: {prompt_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving system prompt {prompt_id}: {e}")
            return None

    def list_system_prompts(
        self, conversation_id: str, user_id: str = None, active_only: bool = False
    ) -> List[SystemPromptTask]:
        """
        List all system prompts for a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for validation
            active_only: If True, return only active prompts

        Returns:
            List of SystemPromptTask objects
        """
        try:
            from bson import ObjectId

            query = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            doc = self.collection.find_one(query)

            if not doc or "system_prompt_tasks" not in doc:
                return []

            prompts = []
            for prompt_dict in doc.get("system_prompt_tasks", []):
                if active_only and not prompt_dict.get("is_active", True):
                    continue
                prompts.append(self._dict_to_system_prompt(prompt_dict))

            return prompts

        except Exception as e:
            logger.error(f"Error listing system prompts for {conversation_id}: {e}")
            return []

    def update_system_prompt(
        self,
        conversation_id: str,
        prompt_id: str,
        user_id: str,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        Update a system prompt.

        Args:
            conversation_id: Conversation ID
            prompt_id: System prompt ID
            user_id: User ID for validation
            name: New name (optional)
            system_prompt: New prompt content (optional)
            description: New description (optional)
            tags: New tags (optional)
            is_active: New active status (optional)

        Returns:
            True if updated successfully
        """
        try:
            from bson import ObjectId

            # Build update dict
            update_fields = {"last_updated": datetime.utcnow()}

            if name is not None:
                update_fields["system_prompt_tasks.$.name"] = name
            if system_prompt is not None:
                update_fields["system_prompt_tasks.$.system_prompt"] = system_prompt
                update_fields["system_prompt_tasks.$.version"] = (
                    update_fields.get("system_prompt_tasks.$.version", 0) + 1
                )
            if description is not None:
                update_fields["system_prompt_tasks.$.description"] = description
            if tags is not None:
                update_fields["system_prompt_tasks.$.tags"] = tags
            if is_active is not None:
                update_fields["system_prompt_tasks.$.is_active"] = is_active

            update_fields["system_prompt_tasks.$.updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                    "system_prompt_tasks.id": prompt_id,
                },
                {"$set": update_fields},
            )

            if result.modified_count > 0:
                logger.info(f"Updated system prompt {prompt_id}")
                return True
            else:
                logger.warning(f"System prompt {prompt_id} not found or not updated")
                return False

        except Exception as e:
            logger.error(f"Error updating system prompt {prompt_id}: {e}")
            return False

    def delete_system_prompt(
        self, conversation_id: str, prompt_id: str, user_id: str
    ) -> bool:
        """
        Delete a system prompt.

        Args:
            conversation_id: Conversation ID
            prompt_id: System prompt ID
            user_id: User ID for validation

        Returns:
            True if deleted successfully
        """
        try:
            from bson import ObjectId

            result = self.collection.update_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                },
                {
                    "$pull": {"system_prompt_tasks": {"id": prompt_id}},
                    "$set": {"last_updated": datetime.utcnow()},
                },
            )

            if result.modified_count > 0:
                logger.info(f"Deleted system prompt {prompt_id}")
                return True
            else:
                logger.warning(f"System prompt {prompt_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error deleting system prompt {prompt_id}: {e}")
            return False

    def select_system_prompt(
        self, conversation_id: str, prompt_id: Optional[str], user_id: str
    ) -> bool:
        """
        Select a system prompt for the conversation.

        Args:
            conversation_id: Conversation ID
            prompt_id: System prompt ID to select (None to deselect)
            user_id: User ID for validation

        Returns:
            True if selection successful
        """
        try:
            from bson import ObjectId

            result = self.collection.update_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                },
                {
                    "$set": {
                        "selected_system_prompt_id": prompt_id,
                        "last_updated": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count > 0:
                action = f"selected {prompt_id}" if prompt_id else "deselected system prompt"
                logger.info(f"System prompt {action} for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"Conversation {conversation_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error selecting system prompt: {e}")
            return False

    def increment_prompt_usage(
        self, conversation_id: str, prompt_id: str, user_id: str
    ) -> bool:
        """
        Increment the usage count for a system prompt.

        Args:
            conversation_id: Conversation ID
            prompt_id: System prompt ID
            user_id: User ID for validation

        Returns:
            True if incremented successfully
        """
        try:
            from bson import ObjectId

            result = self.collection.update_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                    "system_prompt_tasks.id": prompt_id,
                },
                {
                    "$inc": {"system_prompt_tasks.$.usage_count": 1},
                    "$set": {"last_updated": datetime.utcnow()},
                },
            )

            if result.modified_count > 0:
                return True
            else:
                logger.warning(f"Failed to increment usage for prompt {prompt_id}")
                return False

        except Exception as e:
            logger.error(f"Error incrementing prompt usage: {e}")
            return False

    @staticmethod
    def _dict_to_system_prompt(prompt_dict: Dict[str, Any]) -> SystemPromptTask:
        """Convert a dictionary to SystemPromptTask object."""
        return SystemPromptTask(
            id=prompt_dict.get("id", ""),
            user_id=prompt_dict.get("user_id", ""),
            conversation_id=prompt_dict.get("conversation_id", ""),
            name=prompt_dict.get("name", ""),
            description=prompt_dict.get("description"),
            system_prompt=prompt_dict.get("system_prompt", ""),
            tags=prompt_dict.get("tags", []),
            is_active=prompt_dict.get("is_active", True),
            usage_count=prompt_dict.get("usage_count", 0),
            created_at=prompt_dict.get("created_at"),
            updated_at=prompt_dict.get("updated_at"),
            created_by=prompt_dict.get("created_by"),
            version=prompt_dict.get("version", 1),
        )


# Global instance
conversation_history_service = ConversationHistoryService()
