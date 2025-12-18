"""
Assistant Agent Factory.

Creates and configures assistant agents with DataPilotFlow integration.
Handles model setup, tool loading, backend configuration, and memory.
Uses LangChain's Deep Agents library under the hood.
"""

from typing import Any, List, Optional

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.store.mongodb import MongoDBStore
from loguru import logger

from src.config import settings


async def load_user_tools_for_assistant_agent(
    user_id: str, conversation_id: str
) -> List[Any]:
    """
    Load user-selected tools from conversation configuration.

    Standalone implementation for Assistant Agent - loads both prompt-based and MCP tools.

    Args:
        user_id: User ID
        conversation_id: Conversation ID

    Returns:
        List of LangChain tool instances
    """
    try:
        import traceback
        from collections import defaultdict

        from langchain_core.tools import StructuredTool
        from langchain_mcp_adapters.client import MultiServerMCPClient

        from src.domain.tool.models import ToolType
        from src.services.agent.agent_service import get_agent_service
        from src.services.conversation.conversation_history_service import (
            conversation_history_service,
        )
        from src.services.model_provider.model_provider_service import (
            get_model_provider_service,
        )
        from src.services.tool.mcp_server_service import get_mcp_server_service
        from src.services.tool.tool_service import get_tool_service

        # Get conversation and linked agent
        conversation = conversation_history_service.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return []

        # NEW ARCHITECTURE: Get assistant_config from Agent, not ConversationSession
        agent = None
        if conversation.agent_id:
            agent_service = get_agent_service()
            agent = agent_service.get_agent(conversation.agent_id, user_id)

        if not agent or not agent.assistant_config:
            logger.warning(
                f"No assistant config found for agent linked to conversation {conversation_id}"
            )
            return []

        tool_ids = agent.assistant_config.tools or []
        if not tool_ids:
            logger.info("No tools configured in assistant config")
            return []

        logger.info(f"Loading {len(tool_ids)} tools for deep agent: {tool_ids}")

        # Load tools from database
        tool_service = get_tool_service()
        tools_from_db = []

        for tool_id in tool_ids:
            try:
                result = tool_service.get_tool_by_id(tool_id, user_id)
                if result:
                    _, tool_domain = result
                    if tool_domain.is_active:
                        tools_from_db.append(tool_domain)
                        logger.debug(f"Loaded tool: {tool_domain.name} ({tool_id})")
                    else:
                        logger.debug(f"Skipping inactive tool: {tool_id}")
                else:
                    logger.warning(f"Tool {tool_id} not found")
            except Exception as e:
                logger.error(f"Failed to load tool {tool_id}: {e}")

        if not tools_from_db:
            logger.warning("No active tools found")
            return []

        logger.info(f"Creating LangChain tools from {len(tools_from_db)} tool configs")

        langchain_tools = []
        provider_service = get_model_provider_service()

        # 1. Create prompt-based tools
        prompt_based_tools = [
            t for t in tools_from_db if t.tool_type == ToolType.PROMPT_BASED
        ]

        for tool in prompt_based_tools:
            try:
                if not tool.prompt_config:
                    logger.warning(f"Tool {tool.name} missing prompt_config")
                    continue

                # Get LLM provider for this tool
                llm_provider_id = tool.prompt_config.llm_provider_id
                llm_model_name = tool.prompt_config.llm_model_name

                if not llm_provider_id or not llm_model_name:
                    logger.warning(f"Tool {tool.name} missing LLM config")
                    continue

                provider = provider_service.get_model_provider(llm_provider_id, user_id)
                if not provider:
                    logger.warning(
                        f"Provider {llm_provider_id} not found for tool {tool.name}"
                    )
                    continue

                # Create LLM client for this tool
                model_string = f"{provider.provider_type}/{llm_model_name}"
                tool_llm_client = ChatLiteLLM(
                    model=model_string,
                    api_key=provider.api_key,
                    api_base=provider.endpoint if provider.endpoint else None,
                    temperature=tool.prompt_config.temperature,
                    max_tokens=4096,
                )

                # Create tool function
                system_prompt = tool.prompt_config.system_prompt

                def create_prompt_tool_func(llm, prompt, name):
                    """Factory to create tool function with closure."""

                    def tool_func(user_input: str) -> str:
                        """Execute prompt-based tool."""
                        try:
                            full_prompt = f"{prompt}\n\nUser Input: {user_input}"
                            response = llm.invoke(full_prompt)
                            return (
                                response.content
                                if hasattr(response, "content")
                                else str(response)
                            )
                        except Exception as e:
                            return f"Error executing tool '{name}': {str(e)}"

                    return tool_func

                lc_tool = StructuredTool.from_function(
                    func=create_prompt_tool_func(
                        tool_llm_client, system_prompt, tool.name
                    ),
                    name=tool.name,
                    description=tool.description,
                )

                langchain_tools.append(lc_tool)
                logger.info(f"Created prompt-based tool: {tool.name}")

            except Exception as e:
                logger.error(
                    f"Failed to create prompt tool {tool.name}: {e}\n{traceback.format_exc()}"
                )

        # 2. Load MCP remote tools (batch per server)
        mcp_tools = [t for t in tools_from_db if t.tool_type == ToolType.MCP_REMOTE]

        if mcp_tools:
            # Group tools by MCP server
            tools_by_server = defaultdict(list)
            for tool in mcp_tools:
                if tool.mcp_server_id and tool.mcp_tool_name:
                    tools_by_server[tool.mcp_server_id].append(tool)
                else:
                    logger.warning(
                        f"Tool {tool.name} missing mcp_server_id or mcp_tool_name"
                    )

            mcp_server_service = get_mcp_server_service()

            # Load tools from each MCP server
            for server_id, server_tools in tools_by_server.items():
                try:
                    # Get server config
                    result = mcp_server_service.get_server_by_id(server_id, user_id)
                    if not result:
                        logger.warning(f"MCP server {server_id} not found")
                        continue

                    _, mcp_server_config = result

                    logger.info(
                        f"Loading {len(server_tools)} tools from MCP server '{mcp_server_config.name}'"
                    )

                    # Build auth headers
                    headers = {}
                    if (
                        mcp_server_config.auth_type
                        and mcp_server_config.auth_credentials
                    ):
                        if mcp_server_config.auth_type == "bearer":
                            token = mcp_server_config.auth_credentials.get(
                                "token"
                            ) or mcp_server_config.auth_credentials.get("bearer_token")
                            if token:
                                headers["Authorization"] = f"Bearer {token.strip()}"
                        elif mcp_server_config.auth_type == "api_key":
                            api_key = mcp_server_config.auth_credentials.get("api_key")
                            header_name = mcp_server_config.auth_credentials.get(
                                "header_name", "X-API-Key"
                            )
                            if api_key:
                                headers[header_name] = api_key.strip()

                    # Connect to MCP server
                    server_config: dict = {
                        server_id: {
                            "transport": "streamable_http",
                            "url": mcp_server_config.server_url,
                        }
                    }
                    if headers:
                        server_config[server_id]["headers"] = headers

                    # Load all tools from this server
                    client = MultiServerMCPClient(server_config)  # type: ignore
                    all_server_tools = await client.get_tools()

                    logger.debug(
                        f"Loaded {len(all_server_tools)} tools from MCP server"
                    )

                    # Find the specific tools we need
                    for tool in server_tools:
                        matching_tool = next(
                            (
                                t
                                for t in all_server_tools
                                if t.name == tool.mcp_tool_name
                            ),
                            None,
                        )

                        if matching_tool:
                            langchain_tools.append(matching_tool)
                            logger.info(
                                f"Added MCP tool: {tool.name} (server tool: {tool.mcp_tool_name})"
                            )
                        else:
                            logger.warning(
                                f"Tool '{tool.mcp_tool_name}' not found on server. "
                                f"Available: {[t.name for t in all_server_tools]}"
                            )

                except Exception as e:
                    logger.error(
                        f"Failed to load MCP tools from server {server_id}: {e}\n{traceback.format_exc()}"
                    )

        logger.info(
            f"Successfully created {len(langchain_tools)} LangChain tools for deep agent"
        )
        return langchain_tools

    except Exception as e:
        logger.error(f"Error loading tools for deep agent: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


async def create_assistant_agent_for_conversation(
    conversation_id: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    system_prompt: Optional[str] = None,
    custom_tools: Optional[List[Any]] = None,
    checkpointer: Optional[Any] = None,
    store: Optional[Any] = None,
) -> CompiledStateGraph:
    """
    Create a deep agent configured for a specific conversation.

    Uses LangChain's hybrid storage pattern:
    - Transient files (default paths) stored in StateBackend (ephemeral, per-thread)
    - Persistent files (/memories/ paths) stored in StoreBackend (cross-thread, long-term)

    Args:
        conversation_id: Conversation ID
        user_id: User ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        system_prompt: Optional custom system prompt (from assistant config)
        custom_tools: Optional list of custom tools (overrides conversation tools)
        checkpointer: Optional checkpointer for state persistence (recommended)
        store: Optional Store for long-term memory (InMemoryStore if not provided)

    Returns:
        Compiled deep agent graph ready for execution

    Raises:
        ValueError: If provider or configuration is invalid
    """
    logger.info(
        f"Creating deep agent for conversation {conversation_id}, user {user_id}"
    )

    # Get LLM provider configuration
    from src.services.model_provider.model_provider_service import (
        get_model_provider_service,
    )

    provider_service = get_model_provider_service()
    provider = provider_service.get_model_provider(llm_provider_id, user_id)

    if not provider:
        raise ValueError(f"Provider not found: {llm_provider_id}")

    if not provider.is_active:
        raise ValueError(f"Provider is not active: {provider.name}")

    # Create LLM client
    model_string = f"{provider.provider_type}/{llm_model_name}"
    generative_config = provider.generative.config if provider.generative else {}
    temperature = generative_config.get("temperature", 0.7)
    max_tokens = generative_config.get("max_tokens", 4096)

    llm_client = ChatLiteLLM(
        model=model_string,
        api_key=provider.api_key,
        api_base=provider.endpoint if provider.endpoint else None,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=True,
    )

    logger.info(f"Created LLM client: {model_string}")

    # Load user-selected tools (unless custom tools provided)
    if custom_tools is not None:
        tools = custom_tools
        logger.info(f"Using {len(tools)} custom tools")
    else:
        tools = await load_user_tools_for_assistant_agent(user_id, conversation_id)
        logger.info(f"Loaded {len(tools)} tools from conversation config")

    # Import services (needed for system prompt and tool context)
    from src.services.agent.agent_service import get_agent_service
    from src.services.conversation.conversation_history_service import (
        conversation_history_service,
    )

    # Get conversation and linked agent
    conversation = conversation_history_service.get_conversation(conversation_id)
    agent_config = None
    if conversation and conversation.agent_id:
        agent_service = get_agent_service()
        agent_config = agent_service.get_agent(conversation.agent_id, user_id)

    # Get system prompt (from agent's assistant config or default)
    if not system_prompt:
        # NEW ARCHITECTURE: Get instructions from Agent, not ConversationSession
        if (
            agent_config
            and agent_config.assistant_config
            and agent_config.assistant_config.instructions
        ):
            system_prompt = agent_config.assistant_config.instructions
        else:
            system_prompt = "You are a helpful AI assistant with planning and research capabilities."

    # Add memory persistence instructions
    memory_instructions = """

## File System

Files starting with `/memories/` persist across all conversations. All other files are temporary and lost when the thread ends.
"""

    system_prompt = system_prompt + memory_instructions

    # Add conversation context for tools that need it (like knowledge_expert MCP tool)
    # NEW ARCHITECTURE: Get config from Agent, not ConversationSession
    if agent_config:
        collection_name = (
            agent_config.vector_database.collection_name
            if agent_config.vector_database
            else "LongTermMemory"
        )

        # Embedding provider configuration (from vector database collection)
        embedding_provider_id = (
            agent_config.vector_database.embedding_provider.id
            if agent_config.vector_database and agent_config.vector_database.embedding_provider
            else ""
        )
        embedding_model_name = (
            agent_config.vector_database.embedding_provider.model_name
            if agent_config.vector_database and agent_config.vector_database.embedding_provider
            else ""
        )
        vector_dimension = (
            agent_config.vector_database.vector_dimension
            if agent_config.vector_database
            else 1536
        )

        # LLM provider configuration (from agent's primary LLM provider)
        llm_provider = (
            agent_config.llm_provider.id
            if agent_config.llm_provider
            else ""
        )
        llm_model = (
            agent_config.llm_provider.model_name
            if agent_config.llm_provider
            else ""
        )

        # Reranking configuration (controlled by supervisor logic)
        # Set to true if agent has LLM provider configured for reranking
        enable_reranking = bool(llm_provider and llm_model)

        top_k_value = (
            agent_config.vector_database.top_k if agent_config.vector_database else 5
        )

        system_prompt += f"""

## MCP Tool Parameters (Required for knowledge_expert and similar tools):

### Embedding Configuration (REQUIRED - from vector database):
- collection_name: "{collection_name}"
- embedding_provider_id: "{embedding_provider_id}"
- embedding_model_name: "{embedding_model_name}"
- vector_dimension: {vector_dimension}

### Reranking Configuration:
- enable_reranking: {str(enable_reranking).lower()}

### LLM Configuration (for reranking - required if enable_reranking is True):
- llm_provider_id: "{llm_provider}"
- llm_model_name: "{llm_model}"

### General Context:
- user_id: "{user_id}"
- conversation_id: "{conversation_id}"
- top_k: {top_k_value}

When calling knowledge_expert or similar RAG tools, ALWAYS provide:
1. embedding_provider_id, embedding_model_name, vector_dimension (REQUIRED)
2. enable_reranking flag (set to {str(enable_reranking).lower()})
3. llm_provider_id, llm_model_name (REQUIRED if enable_reranking is true)
4. user_id, conversation_id, collection_name, top_k (REQUIRED)
"""
    else:
        logger.warning(
            f"No agent found for conversation {conversation_id}, using default context"
        )

    logger.info(f"Using system prompt: {system_prompt[:100]}...")

    # Create Store if not provided
    if store is None:
        from src.infrastructure.mongo.client import get_mongo_client

        # MongoDBStore requires a collection object (not connection string like Postgres)
        collection = get_mongo_client()[settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME][
            "agent_memory_store"
        ]
        store = MongoDBStore(collection=collection)
        logger.info("Using MongoDBStore for long-term memory")

    # Create deep agent
    logger.info("Creating assistant agent with create_deep_agent...")
    agent = create_deep_agent(
        model=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        backend=lambda runtime: CompositeBackend(
            default=StateBackend(runtime),  # type: ignore[abstract]
            routes={"/memories/": StoreBackend(runtime)},  # type: ignore[abstract]
        ),
        checkpointer=checkpointer,
        store=store,
    )

    logger.info("Deep agent created successfully")
    return agent
