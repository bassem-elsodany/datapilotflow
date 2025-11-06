"""
Conversation History Service for Knowledge Search

This module provides conversation history management for knowledge search sessions,
enabling context-aware responses that understand previous interactions.

NESTED CONFIGURATION STRUCTURE
===============================

The conversation configuration has been restructured into organized, nested dataclasses:

1. **SystemPrompt**: Embedded system prompt for the conversation
   - id: UUID identifier
   - title: Prompt title
   - content: Actual prompt content

2. **EnhancementConfig**: Query enhancement strategy and provider
   - strategy: "native", "multi_query", "augmented", "hyde", "decomposition"
   - provider: Optional provider for enhancement (e.g., embedding model)

3. **VectorDatabaseConfig**: Vector database settings
   - collection_name: Database collection name (default: "LongTermMemory")
   - top_k: Number of documents to retrieve (default: 5)

4. **RerankerConfig**: Document reranking settings
   - provider: Optional reranker provider
   - relevance_threshold: Score threshold for document filtering (0-1, default: 0.5)

5. **AnswerGenerationConfig**: LLM-based answer generation
   - provider: Optional LLM provider for answer generation

BOUNDARY PATTERN ARCHITECTURE
==============================

The service uses a boundary pattern where:
- API endpoints and WebSocket handlers perform conversion at boundaries
- Core business logic remains unchanged
- extract_conversation_config() helper flattens nested structure for agents
- Deserialization inlined in get_conversation() and get_user_conversations()
- asdict() converts dataclass objects to MongoDB-compatible dictionaries

SINGLE STRUCTURED IMPLEMENTATION
=================================

Only the nested configuration structure is supported:
- create_conversation() - Creates conversations with nested config
- update_conversation_config() - Updates conversations with nested config

No backwards compatibility is maintained - all methods use nested dataclasses.

USE EXTRACT_CONVERSATION_CONFIG FOR AGENT CODE
==============================================

When passing conversation config to agents, always use:
  config = extract_conversation_config(conversation)

This ensures agents work with the flat parameter structure they expect,
while the database maintains the organized nested structure.
"""

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from pymongo import MongoClient

from src.config import settings
from src.domain.conversation import (
    AnswerGenerationConfig,
    AssistantConfig,
    ConversationMessage,
    ConversationSession,
    EnhancementConfig,
    ProviderConfig,
    RerankerConfig,
    SystemPromptTask,
    VectorDatabaseConfig,
)


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
        description: Optional[str] = None,
        enhancement: Optional[EnhancementConfig] = None,
        vector_database: Optional[VectorDatabaseConfig] = None,
        reranker: Optional[RerankerConfig] = None,
        answer_generation: Optional[AnswerGenerationConfig] = None,
        tags: Optional[List[str]] = None,
        assistant_config: Optional[AssistantConfig] = None,
    ) -> str:
        """Create a new conversation with nested configuration structure.

        Args:
            user_id: User ID
            name: Conversation name
            description: Conversation description
            enhancement: Enhancement configuration
            vector_database: Vector database configuration
            reranker: Reranker configuration
            answer_generation: Answer generation configuration
            tags: Tags for organization
            assistant_config: Complex nested configuration for Assistant mode
                Required - contains enabled boolean and optional system_prompt_tasks
        """

        # Validate enhancement provider if provided
        if enhancement and enhancement.provider:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider(
                    enhancement.provider.id, user_id
                )

                if not provider or not provider.is_active:
                    logger.warning(
                        f"Enhancement provider not found or inactive: {enhancement.provider.id}"
                    )
                    enhancement = None
            except Exception as e:
                logger.error(f"Error validating enhancement provider: {e}")
                enhancement = None

        # Validate answer generation provider if provided
        if answer_generation and answer_generation.provider:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider(
                    answer_generation.provider.id, user_id
                )

                if not provider or not provider.is_active:
                    logger.warning(
                        f"Answer generation provider not found or inactive: {answer_generation.provider.id}"
                    )
                    answer_generation = None
            except Exception as e:
                logger.error(f"Error validating answer generation provider: {e}")
                answer_generation = None

        # Validate reranker provider if provided
        if reranker and reranker.provider:
            try:
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                provider_service = get_model_provider_service()
                provider = provider_service.get_model_provider(
                    reranker.provider.id, user_id
                )

                if not provider or not provider.is_active:
                    logger.warning(
                        f"Reranker provider not found or inactive: {reranker.provider.id}"
                    )
                    reranker = None
                elif not provider.reranker:
                    logger.warning(
                        f"Provider does not support reranking: {provider.name}"
                    )
                    reranker = None
            except Exception as e:
                logger.error(f"Error validating reranker provider: {e}")
                reranker = None

        # Build conversation data
        conversation_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "messages": [],
            "name": name,
            "description": description,
            "enhancement": asdict(enhancement) if enhancement else None,
            "vector_database": asdict(vector_database) if vector_database else None,
            "reranker": asdict(reranker) if reranker else None,
            "answer_generation": asdict(answer_generation) if answer_generation else None,
            "tags": tags or [],
        }

        # Assistant config is required - always serialize it
        if not assistant_config:
            raise ValueError("assistant_config is required - must specify enabled mode")

        assistant_config_dict = {
            "enabled": assistant_config.enabled,
        }
        if assistant_config.system_prompt_tasks:
            assistant_config_dict["system_prompt_tasks"] = [
                asdict(task) for task in assistant_config.system_prompt_tasks
            ]
        else:
            assistant_config_dict["system_prompt_tasks"] = None
        conversation_data["assistant_config"] = assistant_config_dict

        # Insert and get the MongoDB _id
        result = self.collection.insert_one(conversation_data)
        conversation_id = str(result.inserted_id)

        # Determine agent type from assistant_config
        agent_type = "supervisor" if assistant_config.enabled else "rag"

        logger.info(
            f"Created conversation {conversation_id} for user {user_id} "
            f"with agent_type: {agent_type}, "
            f"strategy: {enhancement.strategy if enhancement else 'native'}"
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
                        chunk_ids=msg_doc.get("chunk_ids"),
                        enhancement_strategy_used=msg_doc.get(
                            "enhancement_strategy_used"
                        ),
                        enhanced_queries=msg_doc.get("enhanced_queries"),
                        processing_time_ms=msg_doc.get("processing_time_ms"),
                        document_count=msg_doc.get("document_count"),
                    )
                    messages.append(msg)

                # Deserialize enhancement config
                enhancement = None
                if doc.get("enhancement"):
                    enh = doc["enhancement"]
                    provider = None
                    if enh.get("provider"):
                        p = enh["provider"]
                        provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                    enhancement = EnhancementConfig(
                        strategy=enh.get("strategy", "native"), provider=provider
                    )

                # Deserialize vector database config
                vector_database = None
                if doc.get("vector_database"):
                    vdb = doc["vector_database"]
                    vector_database = VectorDatabaseConfig(
                        collection_name=vdb.get("collection_name", "LongTermMemory"),
                        top_k=vdb.get("top_k", 5),
                    )

                # Deserialize reranker config
                reranker = None
                if doc.get("reranker"):
                    rer = doc["reranker"]
                    provider = None
                    if rer.get("provider"):
                        p = rer["provider"]
                        provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                    reranker = RerankerConfig(
                        enabled=rer.get("enabled", bool(provider)),  # Enabled if provider is set
                        provider=provider,
                        relevance_threshold=rer.get("relevance_threshold", 0.5),
                    )

                # Deserialize answer generation config
                answer_generation = None
                if doc.get("answer_generation"):
                    ag = doc["answer_generation"]
                    provider = None
                    if ag.get("provider"):
                        p = ag["provider"]
                        provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                    answer_generation = AnswerGenerationConfig(
                        enabled=ag.get("enabled", bool(provider)),  # Enabled if provider is set
                        provider=provider
                    )

                # Deserialize assistant config
                assistant_config = None
                if doc.get("assistant_config"):
                    ac = doc["assistant_config"]
                    system_prompt_tasks = None
                    if ac.get("system_prompt_tasks"):
                        system_prompt_tasks = []
                        for spt_dict in ac["system_prompt_tasks"]:
                            spt = self._dict_to_system_prompt_task(spt_dict)
                            system_prompt_tasks.append(spt)
                    assistant_config = AssistantConfig(
                        enabled=ac.get("enabled", False),
                        system_prompt_tasks=system_prompt_tasks,
                    )

                session = ConversationSession(
                    _id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    created_at=doc["created_at"],
                    last_updated=doc["last_updated"],
                    messages=messages,
                    name=doc.get("name"),
                    description=doc.get("description"),
                    enhancement=enhancement,
                    vector_database=vector_database,
                    reranker=reranker,
                    answer_generation=answer_generation,
                    tags=doc.get("tags", []),
                    assistant_config=assistant_config,
                )
                return session
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}", exc_info=True)
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
                    chunk_ids=msg_doc.get("chunk_ids"),
                    enhancement_strategy_used=msg_doc.get("enhancement_strategy_used"),
                    enhanced_queries=msg_doc.get("enhanced_queries"),
                    processing_time_ms=msg_doc.get("processing_time_ms"),
                    document_count=msg_doc.get("document_count"),
                )
                messages.append(msg)

            # Deserialize enhancement config
            enhancement = None
            if doc.get("enhancement"):
                enh = doc["enhancement"]
                provider = None
                if enh.get("provider"):
                    p = enh["provider"]
                    provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                enhancement = EnhancementConfig(
                    strategy=enh.get("strategy", "native"), provider=provider
                )

            # Deserialize vector database config
            vector_database = None
            if doc.get("vector_database"):
                vdb = doc["vector_database"]
                vector_database = VectorDatabaseConfig(
                    collection_name=vdb.get("collection_name", "LongTermMemory"),
                    top_k=vdb.get("top_k", 5),
                )

            # Deserialize reranker config
            reranker = None
            if doc.get("reranker"):
                rer = doc["reranker"]
                provider = None
                if rer.get("provider"):
                    p = rer["provider"]
                    provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                reranker = RerankerConfig(
                    enabled=rer.get("enabled", bool(provider)),  # Enabled if provider is set
                    provider=provider,
                    relevance_threshold=rer.get("relevance_threshold", 0.5),
                )

            # Deserialize answer generation config
            answer_generation = None
            if doc.get("answer_generation"):
                ag = doc["answer_generation"]
                provider = None
                if ag.get("provider"):
                    p = ag["provider"]
                    provider = ProviderConfig(id=p.get("id"), model_name=p.get("model_name"))
                answer_generation = AnswerGenerationConfig(
                    enabled=ag.get("enabled", bool(provider)),  # Enabled if provider is set
                    provider=provider
                )

            # Deserialize assistant config
            assistant_config = None
            if doc.get("assistant_config"):
                ac = doc["assistant_config"]
                system_prompt_tasks = None
                if ac.get("system_prompt_tasks"):
                    system_prompt_tasks = []
                    for spt_dict in ac["system_prompt_tasks"]:
                        spt = self._dict_to_system_prompt_task(spt_dict)
                        system_prompt_tasks.append(spt)
                assistant_config = AssistantConfig(
                    enabled=ac.get("enabled", False),
                    system_prompt_tasks=system_prompt_tasks,
                )

            session = ConversationSession(
                _id=str(doc["_id"]),
                user_id=doc["user_id"],
                created_at=doc["created_at"],
                last_updated=doc["last_updated"],
                messages=messages,
                name=doc.get("name"),
                description=doc.get("description"),
                enhancement=enhancement,
                vector_database=vector_database,
                reranker=reranker,
                answer_generation=answer_generation,
                tags=doc.get("tags", []),
                assistant_config=assistant_config,
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
        enhancement: Optional[EnhancementConfig] = None,
        vector_database: Optional[VectorDatabaseConfig] = None,
        reranker: Optional[RerankerConfig] = None,
        answer_generation: Optional[AnswerGenerationConfig] = None,
        tags: Optional[List[str]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        assistant_config: Optional[AssistantConfig] = None,
    ) -> bool:
        """Update conversation configuration with nested structure support.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            enhancement: Enhancement configuration
            vector_database: Vector database configuration
            reranker: Reranker configuration
            answer_generation: Answer generation configuration
            tags: Tags for organization
            name: Conversation name
            description: Conversation description
            assistant_config: Complex nested configuration for Assistant mode
        """
        from bson import ObjectId

        try:
            update_data = {"$set": {"last_updated": datetime.utcnow()}}

            # Update basic fields
            if name is not None:
                update_data["$set"]["name"] = name
            if description is not None:
                update_data["$set"]["description"] = description
            if tags is not None:
                update_data["$set"]["tags"] = tags

            # Update enhancement configuration
            if enhancement is not None:
                enhancement_dict = {
                    "strategy": enhancement.strategy,
                    "provider": asdict(enhancement.provider) if enhancement.provider else None,
                }
                update_data["$set"]["enhancement"] = enhancement_dict

            # Update vector database configuration
            if vector_database is not None:
                update_data["$set"]["vector_database"] = asdict(vector_database)

            # Update reranker configuration
            if reranker is not None:
                reranker_dict = {
                    "provider": asdict(reranker.provider) if reranker.provider else None,
                    "relevance_threshold": reranker.relevance_threshold,
                }
                update_data["$set"]["reranker"] = reranker_dict

            # Update answer generation configuration
            if answer_generation is not None:
                answer_gen_dict = {
                    "provider": asdict(answer_generation.provider) if answer_generation.provider else None,
                }
                update_data["$set"]["answer_generation"] = answer_gen_dict

            # Update assistant_config (complex nested structure for Assistant mode)
            if assistant_config is not None:
                assistant_config_dict = {
                    "enabled": assistant_config.enabled,
                }
                if assistant_config.system_prompt_tasks:
                    assistant_config_dict["system_prompt_tasks"] = [
                        asdict(task) for task in assistant_config.system_prompt_tasks
                    ]
                else:
                    assistant_config_dict["system_prompt_tasks"] = None
                update_data["$set"]["assistant_config"] = assistant_config_dict

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
            logger.error(f"Error updating conversation configuration {conversation_id}: {e}")
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

    @staticmethod
    def _dict_to_system_prompt_task(prompt_dict: Dict[str, Any]) -> SystemPromptTask:
        """Convert a dictionary to SystemPromptTask object (alias for _dict_to_system_prompt)."""
        return ConversationHistoryService._dict_to_system_prompt(prompt_dict)


# Global instance
conversation_history_service = ConversationHistoryService()
