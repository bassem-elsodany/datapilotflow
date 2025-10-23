"""
Conversation History Service for Knowledge Search

This module provides conversation history management for knowledge search sessions,
enabling context-aware responses that understand previous interactions.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger
from pymongo import MongoClient
from src.config import settings


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    search_query: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    source_urls: Optional[List[str]] = None


@dataclass
class ConversationSession:
    """Represents a conversation session with history."""
    _id: str  # MongoDB _id as primary identifier
    user_id: str
    created_at: datetime
    last_updated: datetime
    messages: List[ConversationMessage]
    name: Optional[str] = None
    context_summary: Optional[str] = None
    topics_discussed: List[str] = None
    knowledge_sources_used: List[str] = None
    
    def __post_init__(self):
        if self.topics_discussed is None:
            self.topics_discussed = []
        if self.knowledge_sources_used is None:
            self.knowledge_sources_used = []
        # Generate default name if none provided
        if self.name is None:
            self.name = f"Session {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def message_count(self) -> int:
        """Get the number of messages in this session."""
        return len(self.messages)


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
        self.collection.create_index([("last_updated", 1)], expireAfterSeconds=86400 * 30)  # 30 days TTL
    
    def create_conversation(self, user_id: str, name: Optional[str] = None) -> str:
        """Create a new conversation."""
        # Create conversation data without _id (MongoDB will generate it)
        conversation_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "messages": [],
            "name": name,
            "context_summary": None,
            "topics_discussed": [],
            "knowledge_sources_used": []
        }
        
        # Insert and get the MongoDB _id
        result = self.collection.insert_one(conversation_data)
        conversation_id = str(result.inserted_id)
        
        logger.info(f"Created new conversation: {conversation_id} for user: {user_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str, user_id: str = None) -> Optional[ConversationSession]:
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
                        source_urls=msg_doc.get("source_urls")
                    )
                    messages.append(msg)
                
                session = ConversationSession(
                    _id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    created_at=doc["created_at"],
                    last_updated=doc["last_updated"],
                    messages=messages,
                    name=doc.get("name"),
                    context_summary=doc.get("context_summary"),
                    topics_discussed=doc.get("topics_discussed", []),
                    knowledge_sources_used=doc.get("knowledge_sources_used", [])
                )
                return session
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
            return None
    
    def get_conversation_messages(self, conversation_id: str, user_id: str = None) -> List[Dict[str, Any]]:
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
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[ConversationSession]:
        """Get recent conversation sessions for a user."""
        docs = self.collection.find(
            {"user_id": user_id}
        ).sort("last_updated", -1).limit(limit)
        
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
                    source_urls=msg_doc.get("source_urls")
                )
                messages.append(msg)
            
            session = ConversationSession(
                _id=str(doc["_id"]),
                user_id=doc["user_id"],
                created_at=doc["created_at"],
                last_updated=doc["last_updated"],
                messages=messages,
                name=doc.get("name"),
                context_summary=doc.get("context_summary"),
                topics_discussed=doc.get("topics_discussed", []),
                knowledge_sources_used=doc.get("knowledge_sources_used", [])
            )
            sessions.append(session)
        
        return sessions
    
    def get_session_messages(self, session_id: str, user_id: str = None) -> List[Dict[str, Any]]:
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
                "$set": {"last_updated": datetime.utcnow()}
            }
            
            # Update topics and sources if available
            if message.search_query:
                update_data["$addToSet"] = {"topics_discussed": message.search_query}
            
            if message.source_urls:
                update_data["$addToSet"] = {"knowledge_sources_used": {"$each": message.source_urls}}
            
            from bson import ObjectId
            result = self.collection.update_one(
                {"_id": ObjectId(session_id)},
                update_data
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
                context_parts.append(f"  Sources: {', '.join(msg.source_urls[:3])}")  # Limit to 3 sources
        
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
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating context summary for session {session_id}: {e}")
            return False
    
    def rename_conversation(self, conversation_id: str, new_name: str, user_id: str = None) -> bool:
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
                {
                    "$set": {
                        "name": new_name.strip(),
                        "last_updated": datetime.utcnow()
                    }
                }
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
    
    def reset_conversation_messages(self, conversation_id: str, user_id: str = None) -> bool:
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
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Reset messages for session {conversation_id}")
                return True
            else:
                logger.warning(f"Failed to reset messages for session {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error resetting messages for session {conversation_id}: {e}")
            return False
    
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        try:
            result = self.collection.delete_many({
                "last_updated": {"$lt": cutoff_date}
            })
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
                    context_parts.append(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Get last few messages from this session
                    recent_messages = session.messages[-3:]  # Last 3 messages
                    for msg in recent_messages:
                        role = "User" if msg.role == "user" else "Assistant"
                        timestamp = msg.timestamp.strftime("%H:%M")
                        context_parts.append(f"[{timestamp}] {role}: {msg.content[:100]}...")  # Truncate long messages
                    
                    context_parts.append("-" * 30)
            
            context_parts.append("=" * 50)
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting recent context for user {user_id}: {e}")
            return ""


# Global instance
conversation_history_service = ConversationHistoryService() 