"""
Conversation History Service

This service manages conversations and messages in the new agent-based architecture:
- Conversations are stored in 'agent_conversation_sessions' collection (metadata only)
- Messages are stored in separate 'agent_conversation_session_messages' collection
- Agent configuration is fetched from 'agents' collection via agent_id
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from loguru import logger
from pymongo import MongoClient

from src.config import settings
from src.domain.conversation import ConversationMessage, ConversationSession

# Collection names
CONVERSATIONS_COLLECTION = "agent_conversation_sessions"
MESSAGES_COLLECTION = "agent_conversation_session_messages"


class ConversationHistoryService:
    """Service for managing conversations and messages."""

    def __init__(self):
        from src.infrastructure.mongo.client import get_mongo_client

        self.client = get_mongo_client()
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db[CONVERSATIONS_COLLECTION]
        self.messages_collection = self.db[MESSAGES_COLLECTION]

        # Create indexes
        self.collection.create_index([("user_id", 1), ("last_updated", -1)])
        self.collection.create_index([("agent_id", 1)])
        self.collection.create_index([("_id", 1)])

        self.messages_collection.create_index(
            [("conversation_id", 1), ("message_index", 1)]
        )
        self.messages_collection.create_index([("user_id", 1)])
        self.messages_collection.create_index([("timestamp", -1)])

        logger.info("✅ ConversationHistoryService initialized")

    def create_conversation(
        self,
        user_id: str,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new conversation.

        Args:
            user_id: User ID
            agent_id: Agent ID (REQUIRED)
            name: Conversation name
            description: Description
            tags: Tags

        Returns:
            str: Created conversation ID
        """
        now = datetime.utcnow()

        conversation_data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "name": name or f"Conversation {now.strftime('%Y-%m-%d %H:%M')}",
            "description": description,
            "created_at": now,
            "last_updated": now,
            "last_message_at": None,
            "is_archived": False,
            "tags": tags or [],
        }

        result = self.collection.insert_one(conversation_data)
        conversation_id = str(result.inserted_id)

        logger.info(
            f"✅ Created conversation {conversation_id} for user {user_id} with agent {agent_id}"
        )

        return conversation_id

    def get_conversation(
        self, conversation_id: str, user_id: Optional[str] = None
    ) -> Optional[ConversationSession]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for authorization

        Returns:
            ConversationSession or None
        """
        try:
            query: Dict[str, Any] = {"_id": ObjectId(conversation_id)}
            if user_id:
                query["user_id"] = user_id

            doc = self.collection.find_one(query)

            if not doc:
                return None

            # Handle agent_id as either string or ObjectId
            doc_agent_id = doc.get("agent_id")
            if isinstance(doc_agent_id, ObjectId):
                doc_agent_id = str(doc_agent_id)

            return ConversationSession(
                _id=str(doc["_id"]),
                user_id=doc["user_id"],
                agent_id=doc_agent_id or "",
                name=doc.get("name"),
                description=doc.get("description"),
                created_at=doc["created_at"],
                last_updated=doc["last_updated"],
                last_message_at=doc.get("last_message_at"),
                is_archived=doc.get("is_archived", False),
                tags=doc.get("tags", []),
            )

        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            return None

    def get_user_conversations(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConversationSession]:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID
            agent_id: Optional filter by agent
            limit: Max results
            offset: Skip results

        Returns:
            List of ConversationSession
        """
        try:
            query: Dict[str, Any] = {"user_id": user_id}
            if agent_id:
                # Handle both string and ObjectId formats for agent_id
                if ObjectId.is_valid(agent_id):
                    query["$or"] = [
                        {"agent_id": agent_id},
                        {"agent_id": ObjectId(agent_id)},
                    ]
                else:
                    query["agent_id"] = agent_id

            logger.debug(f"Querying conversations with: {query}")

            cursor = (
                self.collection.find(query)
                .sort("last_updated", -1)
                .skip(offset)
                .limit(limit)
            )

            conversations = []
            for doc in cursor:
                # Handle agent_id as either string or ObjectId
                doc_agent_id = doc.get("agent_id")
                if isinstance(doc_agent_id, ObjectId):
                    doc_agent_id = str(doc_agent_id)

                conversations.append(
                    ConversationSession(
                        _id=str(doc["_id"]),
                        user_id=doc["user_id"],
                        agent_id=doc_agent_id or "",
                        name=doc.get("name"),
                        description=doc.get("description"),
                        created_at=doc["created_at"],
                        last_updated=doc["last_updated"],
                        last_message_at=doc.get("last_message_at"),
                        is_archived=doc.get("is_archived", False),
                        tags=doc.get("tags", []),
                    )
                )

            logger.info(
                f"Found {len(conversations)} conversations for user {user_id}, agent_id={agent_id}"
            )
            return conversations

        except Exception as e:
            logger.error(f"Error fetching conversations for user {user_id}: {e}")
            return []

    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_archived: Optional[bool] = None,
    ) -> bool:
        """Update conversation metadata."""
        try:
            set_data: Dict[str, Any] = {"last_updated": datetime.utcnow()}

            if name is not None:
                set_data["name"] = name
            if description is not None:
                set_data["description"] = description
            if tags is not None:
                set_data["tags"] = tags
            if is_archived is not None:
                set_data["is_archived"] = is_archived

            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id},
                {"$set": set_data},
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            return False

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)

        Returns:
            bool: Success
        """
        try:
            # Delete conversation
            result = self.collection.delete_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id}
            )

            if result.deleted_count > 0:
                # Delete all messages
                self.messages_collection.delete_many(
                    {"conversation_id": conversation_id}
                )
                logger.info(
                    f"✅ Deleted conversation {conversation_id} and its messages"
                )
                return True
            else:
                logger.warning(f"Conversation {conversation_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False

    # ========================================================================
    # MESSAGE METHODS
    # ========================================================================

    def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        source_links: Optional[List[Dict]] = None,
        enhancement_strategy_used: Optional[str] = None,
        enhanced_queries: Optional[List[str]] = None,
        processing_time_ms: Optional[int] = None,
        document_count: Optional[int] = None,
    ) -> str:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            role: "user" or "assistant"
            content: Message content
            source_links: Optional source links
            enhancement_strategy_used: Optional strategy used
            enhanced_queries: Optional enhanced queries
            processing_time_ms: Optional processing time
            document_count: Optional document count

        Returns:
            str: Created message ID
        """
        try:
            # Get current message count for indexing
            message_count = self.messages_collection.count_documents(
                {"conversation_id": conversation_id}
            )

            message_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "message_index": message_count,
                "source_links": source_links,
                "enhancement_strategy_used": enhancement_strategy_used,
                "enhanced_queries": enhanced_queries,
                "processing_time_ms": processing_time_ms,
                "document_count": document_count,
            }

            result = self.messages_collection.insert_one(message_data)
            message_id = str(result.inserted_id)

            # Update conversation's last_message_at
            self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "last_message_at": datetime.utcnow(),
                        "last_updated": datetime.utcnow(),
                    }
                },
            )

            logger.debug(
                f"Added message {message_id} to conversation {conversation_id}"
            )
            return message_id

        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise

    def get_conversation_messages(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Get all messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit (returns latest N messages)

        Returns:
            List of ConversationMessage (ordered by message_index)
        """
        try:
            # Try both string and ObjectId formats for conversation_id
            if ObjectId.is_valid(conversation_id):
                query = {
                    "$or": [
                        {"conversation_id": conversation_id},
                        {"conversation_id": ObjectId(conversation_id)},
                    ]
                }
            else:
                query = {"conversation_id": conversation_id}

            if limit:
                # Get latest N messages - count first, then skip
                total_count = self.messages_collection.count_documents(query)
                skip_count = max(0, total_count - limit)
                cursor = (
                    self.messages_collection.find(query)
                    .sort("message_index", 1)
                    .skip(skip_count)
                )
            else:
                cursor = self.messages_collection.find(query).sort("message_index", 1)

            messages = []
            for doc in cursor:
                # Convert conversation_id to string if it's an ObjectId
                conv_id = doc["conversation_id"]
                if isinstance(conv_id, ObjectId):
                    conv_id = str(conv_id)

                messages.append(
                    ConversationMessage(
                        _id=str(doc["_id"]),
                        conversation_id=conv_id,
                        user_id=doc["user_id"],
                        role=doc["role"],
                        content=doc["content"],
                        timestamp=doc["timestamp"],
                        message_index=doc.get("message_index", 0),
                        source_links=doc.get("source_links"),
                        enhancement_strategy_used=doc.get("enhancement_strategy_used"),
                        enhanced_queries=doc.get("enhanced_queries"),
                        processing_time_ms=doc.get("processing_time_ms"),
                        document_count=doc.get("document_count"),
                    )
                )

            return messages

        except Exception as e:
            logger.error(
                f"Error fetching messages for conversation {conversation_id}: {e}"
            )
            return []

    def get_message_count(self, conversation_id: str) -> int:
        """Get the number of messages in a conversation."""
        return self.messages_collection.count_documents(
            {"conversation_id": conversation_id}
        )

    def reset_conversation_messages(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete all messages in a conversation and clear LangGraph checkpoint data.

        This function deletes:
        1. Messages from our app's messages collection
        2. LangGraph checkpoint data (so agent forgets conversation history)
        3. LangGraph writes data

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)

        Returns:
            bool: Success
        """
        try:
            logger.info(f"🔄 [RESET START] conversation_id={conversation_id}, user_id={user_id}")

            # Verify conversation belongs to user
            conversation = self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.error(f"❌ [RESET FAILED] Conversation {conversation_id} not found or unauthorized")
                return False

            # 1. Delete all messages from our app's collection
            logger.info(f"📝 [DELETING APP MESSAGES] conversation_id={conversation_id}")
            result = self.messages_collection.delete_many(
                {"conversation_id": conversation_id}
            )
            logger.info(
                f"✅ [APP MESSAGES DELETED] Deleted {result.deleted_count} messages from app DB for conversation {conversation_id}"
            )

            # 2. Delete LangGraph checkpoint data AND memory store
            # The checkpointer uses conversation_id as thread_id
            try:
                checkpoint_db = self.client[
                    settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME
                ]

                # Delete from checkpoints collection
                # LangGraph stores thread_id in nested structure: thread_id.thread_id
                logger.info(f"🔍 [CHECKING CHECKPOINTS] conversation_id={conversation_id}")
                checkpoints_collection = checkpoint_db[
                    settings.MONGO_AGENT_STATE_CHECKPOINT_COLLECTION
                ]

                # Debug: Check what checkpoints exist before deletion
                # Note: LangGraph MongoDBSaver stores thread_id as a simple field (not nested)
                # and checkpoint_ns defaults to "" (empty string)
                checkpoint_query = {
                    "thread_id": conversation_id,
                    "checkpoint_ns": ""
                }
                existing_checkpoints = list(checkpoints_collection.find(checkpoint_query))
                logger.info(f"📊 [CHECKPOINTS BEFORE DELETE] Found {len(existing_checkpoints)} checkpoint(s) for thread_id={conversation_id}, checkpoint_ns=''")
                if existing_checkpoints:
                    logger.debug(f"📋 [CHECKPOINT DETAILS] {existing_checkpoints[0]}")

                checkpoint_result = checkpoints_collection.delete_many(checkpoint_query)
                logger.info(
                    f"✅ [CHECKPOINTS DELETED] Deleted {checkpoint_result.deleted_count} checkpoint entries for thread {conversation_id}"
                )

                # Delete from writes collection
                logger.info(f"🔍 [CHECKING WRITES] conversation_id={conversation_id}")
                writes_collection = checkpoint_db[
                    settings.MONGO_AGENT_STATE_WRITES_COLLECTION
                ]

                # Debug: Check what writes exist before deletion
                # Note: LangGraph MongoDBSaver stores thread_id as a simple field (not nested)
                # and checkpoint_ns defaults to "" (empty string)
                writes_query = {
                    "thread_id": conversation_id,
                    "checkpoint_ns": ""
                }
                existing_writes = list(writes_collection.find(writes_query))
                logger.info(f"📊 [WRITES BEFORE DELETE] Found {len(existing_writes)} write entry(ies) for thread_id={conversation_id}, checkpoint_ns=''")
                if existing_writes:
                    logger.debug(f"📋 [WRITES DETAILS] {existing_writes[0]}")

                writes_result = writes_collection.delete_many(writes_query)
                logger.info(
                    f"✅ [WRITES DELETED] Deleted {writes_result.deleted_count} writes entries for thread {conversation_id}"
                )

                # Delete from agent-specific memory store
                # MongoDBStore uses agent-specific collections with namespace-based storage
                # Collection format: "persistent_storage_{agent_id}"
                # Namespace format: "user:{user_id}:conversation:{conversation_id}"
                logger.info(f"🔍 [CHECKING MEMORY STORE] conversation_id={conversation_id}, agent_id={conversation.agent_id}")

                # Get agent_id from conversation to determine which memory collection to delete from
                if conversation.agent_id:
                    memory_collection_name = f"persistent_storage_{conversation.agent_id}"
                    memory_store_collection = checkpoint_db[memory_collection_name]

                    # Memory store items are stored with namespace matching this pattern
                    memory_namespace = f"user:{user_id}:conversation:{conversation_id}"

                    # Debug: Check what memories exist before deletion
                    existing_memories = list(memory_store_collection.find(
                        {"namespace": memory_namespace}
                    ))
                    logger.info(f"📊 [MEMORY STORE BEFORE DELETE] Found {len(existing_memories)} memory item(s) in collection {memory_collection_name} with namespace: {memory_namespace}")
                    if existing_memories:
                        logger.debug(f"📋 [MEMORY STORE DETAILS] First item: {existing_memories[0]}")

                    memory_result = memory_store_collection.delete_many(
                        {"namespace": memory_namespace}
                    )
                    logger.info(
                        f"✅ [MEMORY STORE DELETED] Deleted {memory_result.deleted_count} memory items from {memory_collection_name} for conversation {conversation_id}"
                    )
                else:
                    logger.warning(f"⚠️ [NO AGENT_ID] Conversation {conversation_id} has no agent_id, skipping memory store deletion")

            except Exception as checkpoint_error:
                # Log but don't fail - checkpoint/memory deletion is best-effort
                logger.error(
                    f"❌ [CHECKPOINT DELETE ERROR] Could not delete LangGraph checkpoint/memory data for {conversation_id}: {checkpoint_error}",
                    exc_info=True
                )

            # Verify deletion was successful
            logger.info(f"✅ [RESET COMPLETE] Verifying deletion for conversation {conversation_id}")
            verify_messages = self.messages_collection.count_documents(
                {"conversation_id": conversation_id}
            )
            logger.info(f"✅ [VERIFICATION] Remaining messages after reset: {verify_messages}")

            if verify_messages > 0:
                logger.warning(f"⚠️ [RESET WARNING] {verify_messages} messages still exist after reset for {conversation_id}")

            return True

        except Exception as e:
            logger.error(f"❌ [RESET ERROR] Error resetting conversation {conversation_id}: {e}", exc_info=True)
            return False

    def get_conversation_context(
        self, conversation_id: str, max_messages: int = 10
    ) -> str:
        """
        Get conversation context as formatted string.

        Args:
            conversation_id: Conversation ID
            max_messages: Maximum number of recent messages to include

        Returns:
            Formatted conversation history string
        """
        messages = self.get_conversation_messages(conversation_id, limit=max_messages)

        if not messages:
            return ""

        context_parts = []
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role_label}: {msg.content}")

        return "\n".join(context_parts)


# Global instance
conversation_history_service = ConversationHistoryService()
