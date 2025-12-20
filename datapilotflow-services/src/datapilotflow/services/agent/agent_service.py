"""
Agent Service

This service handles CRUD operations for AI agents in MongoDB.
Agents are reusable configurations that can be used across multiple conversations.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from loguru import logger
from pymongo import MongoClient

from datapilotflow.config import settings
from datapilotflow.domain.agent.models import Agent, AgentType, EnhancementStrategy
from datapilotflow.domain.conversation.models import (
    AssistantConfig,
    ProviderConfig,
    RerankerConfig,
    VectorDatabaseConfig,
)


class AgentService:
    """Service for managing AI agents in MongoDB."""

    def __init__(self):
        """Initialize the agent service with MongoDB connection."""
        from datapilotflow.infrastructure.mongo.client import get_mongo_client

        self.client = get_mongo_client()
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db["agents"]

        # Create indexes for efficient querying
        self.collection.create_index([("user_id", 1), ("created_at", -1)])
        self.collection.create_index([("_id", 1)])
        self.collection.create_index([("agent_type", 1)])
        self.collection.create_index([("tags", 1)])

        logger.debug("AgentService initialized")

    def create_agent(
        self,
        user_id: str,
        name: str,
        agent_type: AgentType,
        description: Optional[str] = None,
        llm_provider: Optional[ProviderConfig] = None,
        enhancement_strategy: EnhancementStrategy = EnhancementStrategy.NATIVE,
        vector_database: Optional[VectorDatabaseConfig] = None,
        reranker: Optional[RerankerConfig] = None,
        is_llm_generation_enabled: bool = False,
        assistant_config: Optional[AssistantConfig] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new agent.

        Args:
            user_id: Owner of the agent
            name: Display name for the agent
            agent_type: Type of agent (RAG or ASSISTANT)
            description: Optional description
            llm_provider: Primary LLM provider config (for both RAG and ASSISTANT agents)
            enhancement_strategy: Query enhancement strategy (e.g., "native", "augmented", "custom_variants")
            vector_database: Vector DB config (for RAG agents)
            reranker: Reranker config (for RAG agents)
            is_llm_generation_enabled: Whether LLM answer generation is enabled
            assistant_config: Assistant config (for ASSISTANT agents)
            tags: Organizational tags

        Returns:
            str: Created agent ID

        Raises:
            ValueError: If required configuration is missing for agent type
        """
        now = datetime.utcnow()

        # Build agent data
        agent_data = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "agent_type": (
                agent_type.value if isinstance(agent_type, AgentType) else agent_type
            ),
            "created_at": now,
            "updated_at": now,
            "tags": tags or [],
            "llm_provider": asdict(llm_provider) if llm_provider else None,
        }

        # Add RAG configuration (can be used by both RAG and ASSISTANT agents with Knowledge Expert)
        agent_data["enhancement_strategy"] = (
            enhancement_strategy.value
            if isinstance(enhancement_strategy, EnhancementStrategy)
            else enhancement_strategy
        )
        agent_data["vector_database"] = (
            asdict(vector_database) if vector_database else None
        )
        agent_data["reranker"] = asdict(reranker) if reranker else None
        agent_data["is_llm_generation_enabled"] = is_llm_generation_enabled

        # Agent type specific validation and configuration
        if agent_type == AgentType.RAG:
            if not vector_database:
                raise ValueError("RAG agents must have vector_database configuration")
            agent_data["assistant_config"] = None

        elif agent_type == AgentType.ASSISTANT:
            if not assistant_config:
                raise ValueError("ASSISTANT agents must have assistant_config")

            assistant_config_dict = {
                "enabled": assistant_config.enabled,
                "tools": assistant_config.tools if assistant_config.tools else [],
                "instructions": assistant_config.instructions,
            }
            agent_data["assistant_config"] = assistant_config_dict

        # Insert into MongoDB
        result = self.collection.insert_one(agent_data)
        agent_id = str(result.inserted_id)

        logger.debug(f"Created agent {agent_id}")

        return agent_id

    def get_agent(self, agent_id: str, user_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID
            user_id: User ID (for authorization)

        Returns:
            Agent object or None if not found
        """
        try:
            doc = self.collection.find_one(
                {"_id": ObjectId(agent_id), "user_id": user_id}
            )

            if not doc:
                logger.debug(f"Agent {agent_id} not found")
                return None

            return self._deserialize_agent(doc)

        except Exception as e:
            logger.error(f"Error fetching agent: {e}")
            return None

    def get_user_agents(
        self,
        user_id: str,
        agent_type: Optional[AgentType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Agent]:
        """
        Get all agents for a user.

        Args:
            user_id: User ID
            agent_type: Optional filter by agent type
            limit: Maximum number of agents to return
            offset: Number of agents to skip

        Returns:
            List of Agent objects
        """
        try:
            query = {"user_id": user_id}
            if agent_type:
                query["agent_type"] = agent_type.value

            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )

            agents = [self._deserialize_agent(doc) for doc in cursor]
            logger.debug(f"Retrieved {len(agents)} agents")
            return agents

        except Exception as e:
            logger.error(f"Error fetching agents: {e}")
            return []

    def update_agent(
        self,
        agent_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        llm_provider: Optional[ProviderConfig] = None,
        enhancement_strategy: Optional[EnhancementStrategy] = None,
        vector_database: Optional[VectorDatabaseConfig] = None,
        reranker: Optional[RerankerConfig] = None,
        is_llm_generation_enabled: Optional[bool] = None,
        assistant_config: Optional[AssistantConfig] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an agent's configuration.

        Args:
            agent_id: Agent ID
            user_id: User ID (for authorization)
            name: New name (optional)
            description: New description (optional)
            llm_provider: New LLM provider config (optional)
            enhancement_strategy: New enhancement strategy (optional)
            vector_database: New vector DB config (optional)
            reranker: New reranker config (optional)
            is_llm_generation_enabled: Whether LLM generation is enabled (optional)
            assistant_config: New assistant config (optional)
            tags: New tags (optional)

        Returns:
            bool: True if updated successfully
        """
        try:
            update_data = {"$set": {"updated_at": datetime.utcnow()}}

            if name is not None:
                update_data["$set"]["name"] = name
            if description is not None:
                update_data["$set"]["description"] = description
            if tags is not None:
                update_data["$set"]["tags"] = tags
            if llm_provider is not None:
                update_data["$set"]["llm_provider"] = asdict(llm_provider)

            # Update RAG configuration
            if enhancement_strategy is not None:
                update_data["$set"]["enhancement_strategy"] = (
                    enhancement_strategy.value
                    if isinstance(enhancement_strategy, EnhancementStrategy)
                    else enhancement_strategy
                )
            if vector_database is not None:
                update_data["$set"]["vector_database"] = asdict(vector_database)
            if reranker is not None:
                update_data["$set"]["reranker"] = asdict(reranker)
            if is_llm_generation_enabled is not None:
                update_data["$set"][
                    "is_llm_generation_enabled"
                ] = is_llm_generation_enabled

            # Update assistant configuration
            if assistant_config is not None:
                assistant_config_dict = {
                    "enabled": assistant_config.enabled,
                    "tools": assistant_config.tools if assistant_config.tools else [],
                    "instructions": assistant_config.instructions,
                }
                update_data["$set"]["assistant_config"] = assistant_config_dict

            result = self.collection.update_one(
                {"_id": ObjectId(agent_id), "user_id": user_id}, update_data
            )

            if result.modified_count > 0:
                logger.debug(f"Updated agent {agent_id}")
                return True
            else:
                logger.debug(f"No changes made to agent {agent_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            return False

    def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """
        Delete an agent.

        Note: Should check if agent is in use by conversations before deleting.

        Args:
            agent_id: Agent ID
            user_id: User ID (for authorization)

        Returns:
            bool: True if deleted successfully
        """
        try:
            result = self.collection.delete_one(
                {"_id": ObjectId(agent_id), "user_id": user_id}
            )

            if result.deleted_count > 0:
                logger.debug(f"Deleted agent {agent_id}")
                return True
            else:
                logger.debug(f"Agent {agent_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False

    def count_conversations_using_agent(self, agent_id: str) -> int:
        """
        Count how many conversations are using this agent.

        Args:
            agent_id: Agent ID

        Returns:
            int: Number of conversations using this agent
        """
        try:
            # Import here to avoid circular dependency
            from datapilotflow.services.conversation.conversation_history_service import (
                conversation_history_service,
            )

            # Query using both string and ObjectId formats for compatibility
            count = conversation_history_service.collection.count_documents(
                {
                    "$or": [
                        {"agent_id": agent_id},
                        (
                            {"agent_id": ObjectId(agent_id)}
                            if ObjectId.is_valid(agent_id)
                            else {"agent_id": agent_id}
                        ),
                    ]
                }
            )
            return count

        except Exception as e:
            logger.error(f"Error counting conversations: {e}")
            return 0

    def _deserialize_agent(self, doc: Dict) -> Agent:
        """
        Convert MongoDB document to Agent domain model.

        Args:
            doc: MongoDB document

        Returns:
            Agent object
        """

        # Deserialize nested provider configs
        def deserialize_provider(data: Optional[Dict]) -> Optional[ProviderConfig]:
            if not data:
                return None
            return ProviderConfig(id=data["id"], model_name=data["model_name"])

        # Deserialize enhancement strategy (new simplified format)
        # Support backward compatibility with old "enhancement" object format
        enhancement_strategy = EnhancementStrategy.NATIVE
        if "enhancement_strategy" in doc:
            strategy_value = doc["enhancement_strategy"] or "native"
            try:
                enhancement_strategy = EnhancementStrategy(strategy_value)
            except ValueError:
                # Default to NATIVE if invalid value
                enhancement_strategy = EnhancementStrategy.NATIVE
        elif doc.get("enhancement"):
            # Backward compatibility: extract strategy from old enhancement object
            strategy_value = doc["enhancement"].get("strategy", "native")
            try:
                enhancement_strategy = EnhancementStrategy(strategy_value)
            except ValueError:
                enhancement_strategy = EnhancementStrategy.NATIVE

        # Deserialize vector database config
        vector_database = None
        if doc.get("vector_database"):
            vector_database = VectorDatabaseConfig(
                collection_name=doc["vector_database"]["collection_name"],
                top_k=doc["vector_database"]["top_k"],
                embedding_provider=deserialize_provider(doc["vector_database"].get("embedding_provider")),
                vector_dimension=doc["vector_database"].get("vector_dimension", 1536),
            )

        # Deserialize reranker config
        reranker = None
        if doc.get("reranker"):
            reranker = RerankerConfig(
                enabled=doc["reranker"].get("enabled", False),
                provider=deserialize_provider(doc["reranker"].get("provider")),
                relevance_threshold=doc["reranker"].get("relevance_threshold", 0.5),
            )

        # Deserialize LLM generation enabled flag (new simplified format)
        # Support backward compatibility with old "answer_generation" object format
        is_llm_generation_enabled = False
        if "is_llm_generation_enabled" in doc:
            is_llm_generation_enabled = doc.get("is_llm_generation_enabled", False)
        elif doc.get("answer_generation"):
            # Backward compatibility: extract enabled from old answer_generation object
            is_llm_generation_enabled = doc["answer_generation"].get("enabled", False)

        # Deserialize assistant config
        assistant_config = None
        if doc.get("assistant_config"):
            assistant_config = AssistantConfig(
                enabled=doc["assistant_config"]["enabled"],
                tools=doc["assistant_config"].get("tools"),
                instructions=doc["assistant_config"].get("instructions"),
            )

        # Deserialize llm_provider
        llm_provider = deserialize_provider(doc.get("llm_provider"))

        return Agent(
            _id=str(doc["_id"]),
            user_id=doc["user_id"],
            name=doc["name"],
            description=doc.get("description"),
            agent_type=AgentType(doc["agent_type"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            llm_provider=llm_provider,
            enhancement_strategy=enhancement_strategy,
            vector_database=vector_database,
            reranker=reranker,
            is_llm_generation_enabled=is_llm_generation_enabled,
            assistant_config=assistant_config,
            tags=doc.get("tags", []),
        )


# Global instance
_agent_service_instance: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create the global AgentService instance."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance
