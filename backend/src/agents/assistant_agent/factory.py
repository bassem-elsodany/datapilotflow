"""
Assistant Agent Factory.

Creates and configures assistant agents with DataPilotFlow integration.
Handles model setup, tool loading, backend configuration, and memory.
Uses LangChain's Deep Agents library under the hood.
"""

import asyncio
from typing import Any, List, Optional

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.store.mongodb import MongoDBStore
from loguru import logger

from src.config import settings


async def _load_prompt_based_tools(
    tools: List[Any], user_id: str, provider_service: Any
) -> List[Any]:
    """Load prompt-based tools asynchronously."""
    import traceback

    from langchain_core.tools import StructuredTool

    langchain_tools = []

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

    for tool in tools:
        try:
            if not tool.prompt_config:
                logger.warning(f"Tool {tool.name} missing prompt_config")
                continue

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

            model_string = f"{provider.provider_type}/{llm_model_name}"
            tool_llm_client = ChatLiteLLM(
                model=model_string,
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
                temperature=tool.prompt_config.temperature,
                max_tokens=4096,
            )

            system_prompt = tool.prompt_config.system_prompt
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
            logger.error(f"Failed to create prompt tool {tool.name}: {e}\n{traceback.format_exc()}")

    return langchain_tools


async def _load_mcp_tools(
    tools: List[Any], user_id: str, mcp_server_service: Any
) -> List[Any]:
    """Load MCP remote tools asynchronously."""
    import traceback
    from collections import defaultdict

    from langchain_mcp_adapters.client import MultiServerMCPClient

    langchain_tools = []

    # Group tools by MCP server
    tools_by_server = defaultdict(list)
    for tool in tools:
        if tool.mcp_server_id and tool.mcp_tool_name:
            tools_by_server[tool.mcp_server_id].append(tool)
        else:
            logger.warning(f"Tool {tool.name} missing mcp_server_id or mcp_tool_name")

    # Load tools from each MCP server concurrently
    async def load_from_server(server_id, server_tools):
        try:
            result = mcp_server_service.get_server_by_id(server_id, user_id)
            if not result:
                logger.warning(f"MCP server {server_id} not found")
                return []

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

            server_config: dict = {
                server_id: {
                    "transport": "streamable_http",
                    "url": mcp_server_config.server_url,
                }
            }
            if headers:
                server_config[server_id]["headers"] = headers

            client = MultiServerMCPClient(server_config)  # type: ignore
            all_server_tools = await client.get_tools()

            logger.debug(f"Loaded {len(all_server_tools)} tools from MCP server")

            server_langchain_tools = []
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
                    server_langchain_tools.append(matching_tool)
                    logger.info(
                        f"Added MCP tool: {tool.name} (server tool: {tool.mcp_tool_name})"
                    )
                else:
                    logger.warning(
                        f"Tool '{tool.mcp_tool_name}' not found on server. "
                        f"Available: {[t.name for t in all_server_tools]}"
                    )

            return server_langchain_tools

        except Exception as e:
            logger.error(
                f"Failed to load MCP tools from server {server_id}: {e}\n{traceback.format_exc()}"
            )
            return []

    # Run all server loads concurrently
    tasks = [
        load_from_server(server_id, server_tools)
        for server_id, server_tools in tools_by_server.items()
    ]
    results = await asyncio.gather(*tasks)

    # Flatten results
    for server_tools in results:
        langchain_tools.extend(server_tools)

    return langchain_tools


async def load_user_tools_for_assistant_agent(
    user_id: str, conversation_id: str
) -> List[Any]:
    """
    Load user-selected tools from conversation configuration.

    Standalone implementation for Assistant Agent - loads both prompt-based and MCP tools.
    Loads prompt-based and MCP tools in parallel for better performance.

    Args:
        user_id: User ID
        conversation_id: Conversation ID

    Returns:
        List of LangChain tool instances
    """
    try:
        import traceback

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

        # Separate tools by type
        prompt_based_tools = [
            t for t in tools_from_db if t.tool_type == ToolType.PROMPT_BASED
        ]
        mcp_tools = [t for t in tools_from_db if t.tool_type == ToolType.MCP_REMOTE]

        # Load services
        provider_service = get_model_provider_service()
        mcp_server_service = get_mcp_server_service()

        # Load prompt-based and MCP tools in parallel
        prompt_task = (
            _load_prompt_based_tools(prompt_based_tools, user_id, provider_service)
            if prompt_based_tools
            else asyncio.sleep(0)  # no-op if no prompt tools
        )
        mcp_task = (
            _load_mcp_tools(mcp_tools, user_id, mcp_server_service)
            if mcp_tools
            else asyncio.sleep(0)  # no-op if no MCP tools
        )

        results = await asyncio.gather(prompt_task, mcp_task)
        prompt_langchain_tools = results[0] if isinstance(results[0], list) else []
        mcp_langchain_tools = results[1] if isinstance(results[1], list) else []

        langchain_tools = prompt_langchain_tools + mcp_langchain_tools

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
    agent_id: Optional[str] = None,
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
        agent_id: Optional Agent ID (for agent-specific persistent storage)
        system_prompt: Optional custom system prompt (from assistant config)
        custom_tools: Optional list of custom tools (overrides conversation tools)
        checkpointer: Optional checkpointer for state persistence (recommended)
        store: Optional Store for long-term memory (MongoDBStore if not provided)

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
    temperature = generative_config.get("temperature", None)
    max_tokens = generative_config.get("max_tokens", None)

    llm_client = ChatLiteLLM(
        model=model_string,
        api_key=provider.api_key,
        api_base=provider.endpoint if provider.endpoint else None,
        temperature=temperature if temperature is not None else None,
        max_tokens=max_tokens if max_tokens is not None else None,
        streaming=True,
    )

    logger.info(f"Created LLM client: {model_string}")

    # Import services (needed for system prompt and tool context)
    from src.services.agent.agent_service import get_agent_service
    from src.services.conversation.conversation_history_service import (
        conversation_history_service,
    )

    # Get conversation and linked agent once (reused for tool loading and system prompt)
    conversation = conversation_history_service.get_conversation(conversation_id)
    agent_config = None
    if conversation and conversation.agent_id:
        agent_service = get_agent_service()
        agent_config = agent_service.get_agent(conversation.agent_id, user_id)

    # Load user-selected tools (unless custom tools provided)
    if custom_tools is not None:
        tools = custom_tools
        logger.info(f"Using {len(tools)} custom tools")
    else:
        tools = await load_user_tools_for_assistant_agent(user_id, conversation_id)
        logger.info(f"Loaded {len(tools)} tools from conversation config")

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

    # Add memory persistence instructions (multi-agent aware)
    memory_instructions = f"""

## CRITICAL: File Storage Behavior

There are TWO types of file storage with DIFFERENT lifespans:

### 1. PERSISTENT FILES (Survives between conversations):
**RULE: Use `/memories/` prefix for ANY file you want to keep**

Files saved with paths starting with `/memories/` are PERSISTENT and will survive:
- Between different conversation threads
- After the current conversation ends
- Across different sessions for this agent

Examples of persistent file paths:
- `/memories/notes.txt` - Session notes
- `/memories/knowledge/research.md` - Knowledge base
- `/memories/context/user_profile.json` - Long-term context
- `/memories/sources/references.md` - Source citations
- `/memories/projects/active_tasks.md` - Project tracking
- `/memories/instructions.txt` - Self-improving instructions

**RECOMMENDED Persistent File Structure:**
- `/memories/notes.txt` - Your thoughts and observations
- `/memories/knowledge/` - Facts and information learned
- `/memories/context/` - User preferences and domain context
- `/memories/sources/` - References and citations
- `/memories/projects/` - Ongoing projects and tasks

### 2. TRANSIENT FILES (Lost at end of conversation):
**RULE: Do NOT use `/memories/` prefix for temporary work**

Files saved WITHOUT the `/memories/` prefix are TEMPORARY and will be deleted when:
- The current conversation thread ends
- You close the session
- A new conversation starts

Examples of transient file paths:
- `/scratch.txt` - Temporary calculations
- `/temp_analysis.json` - Working notes
- `/current_task.md` - In-progress work

Use transient files ONLY for:
- Intermediate calculations and scratch work
- Temporary data processing
- One-off analysis that won't be needed later

### STORAGE RULES SUMMARY:
✅ MUST use `/memories/` prefix: Important info, research, notes, context
❌ MUST NOT use `/memories/` prefix: Temporary/scratch files

### CRITICAL ENFORCEMENT:
When writing files that should persist, ALWAYS include the `/memories/` prefix in the path.
Examples:
- CORRECT: write_file("/memories/notes.txt", "content")
- WRONG: write_file("/notes.txt", "content") - This will be lost!

Agent ID: {agent_id if agent_id else "default"}
"""

    system_prompt = system_prompt + memory_instructions

    # Add conversation context for tools that need it (like knowledge_expert MCP tool)
    # NEW ARCHITECTURE: Get config from Agent, not ConversationSession
    # Initialize defaults first
    collection_name = "LongTermMemory"
    embedding_provider_id = ""
    embedding_model_name = ""
    vector_dimension = 1536
    llm_provider = ""
    llm_model = ""
    enable_reranking = False
    top_k_value = 5

    if agent_config:
        logger.info(f"Agent config found for agent_id: {agent_id}")
        logger.info(f"Agent config object: {agent_config}")
        logger.debug(f"Agent config vector_database: {agent_config.vector_database}")
        logger.debug(f"Agent config llm_provider: {agent_config.llm_provider}")

        collection_name = (
            agent_config.vector_database.collection_name
            if agent_config.vector_database
            else "LongTermMemory"
        )
        logger.debug(f"Collection name: {collection_name}")

        # Embedding provider configuration (from vector database collection)
        if agent_config.vector_database:
            logger.info(f"Vector DB config exists: {agent_config.vector_database}")
            logger.info(f"Vector DB embedding_provider: {agent_config.vector_database.embedding_provider}")
            if agent_config.vector_database.embedding_provider:
                logger.info(f"Embedding provider ID: {agent_config.vector_database.embedding_provider.id}")
                logger.info(f"Embedding provider model: {agent_config.vector_database.embedding_provider.model_name}")

        embedding_provider_id = (
            agent_config.vector_database.embedding_provider.id
            if agent_config.vector_database
            and agent_config.vector_database.embedding_provider
            else ""
        )
        embedding_model_name = (
            agent_config.vector_database.embedding_provider.model_name
            if agent_config.vector_database
            and agent_config.vector_database.embedding_provider
            else ""
        )
        logger.info(f"Final embedding config - provider_id: '{embedding_provider_id}', model_name: '{embedding_model_name}'")

        vector_dimension = (
            agent_config.vector_database.vector_dimension
            if agent_config.vector_database
            else 1536
        )
        logger.debug(f"Vector dimension: {vector_dimension}")

        # LLM provider configuration (from agent's primary LLM provider)
        llm_provider = agent_config.llm_provider.id if agent_config.llm_provider else ""
        llm_model = (
            agent_config.llm_provider.model_name if agent_config.llm_provider else ""
        )
        logger.debug(f"LLM provider_id: '{llm_provider}', model: '{llm_model}'")

        # Reranking configuration (from agent.reranker.enabled)
        # This field explicitly controls whether reranking is enabled
        enable_reranking = (
            agent_config.reranker.enabled if agent_config.reranker else False
        )
        logger.debug(f"Enable reranking: {enable_reranking}")

        top_k_value = (
            agent_config.vector_database.top_k if agent_config.vector_database else 5
        )
        logger.debug(f"Top k value: {top_k_value}")
    else:
        logger.warning(
            f"No agent found for conversation {conversation_id}, using default context and empty parameters"
        )

    system_prompt += f"""

## MCP Tool Parameters (CRITICAL - MANDATORY for knowledge_expert and RAG tool calls):

When calling the knowledge_expert tool or any RAG tools, you MUST use these EXACT parameter values. Do NOT use defaults, do NOT skip parameters, do NOT use empty strings:

**Required Parameters for knowledge_expert:**
- collection_name: "{collection_name}"
- embedding_provider_id: "{embedding_provider_id}"
- embedding_model_name: "{embedding_model_name}"
- vector_dimension: {vector_dimension}
- user_id: "{user_id}"
- conversation_id: "{conversation_id}"
- top_k: {top_k_value}
- enable_reranking: {str(enable_reranking).lower()}
- llm_provider_id: "{llm_provider}"
- llm_model_name: "{llm_model}"

**STRICT ENFORCEMENT:**
- ALL string parameters must be enclosed in quotes and match exactly as shown
- numeric parameters (vector_dimension, top_k) must be numbers without quotes
- boolean parameters (enable_reranking) must be lowercase (true/false)
- If any parameter appears empty here, it is intentional - pass it as an empty string ""
- NEVER try to "improve" or guess values - use exactly what is shown above
"""

    logger.info(f"Injected MCP Parameters - collection: {collection_name}, embedding_provider: {embedding_provider_id}, embedding_model: {embedding_model_name}, vector_dim: {vector_dimension}, top_k: {top_k_value}")
    logger.debug(f"Using system prompt: {system_prompt[:200]}...")

    # Create Store if not provided
    if store is None:
        from src.infrastructure.mongo.client import get_mongo_client

        # MongoDBStore requires a collection object (not connection string like Postgres)
        # Use agent-specific collection for multi-agent isolation
        collection_name = (
            f"persistent_storage_{agent_id}"
            if agent_id
            else "persistent_storage_default"
        )
        collection = get_mongo_client()[settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME][
            collection_name
        ]
        store = MongoDBStore(collection=collection)
        logger.info(
            f"Using MongoDBStore for long-term memory (collection: {collection_name})"
        )

    # Create deep agent
    logger.info("Creating assistant agent with create_deep_agent...")
    agent = create_deep_agent(
        model=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        store=store,
        backend=lambda rt: CompositeBackend(
            default=StateBackend(rt),  # type: ignore[abstract]
            routes={"/memories/": StoreBackend(rt)},  # type: ignore[abstract]
        ),
        checkpointer=checkpointer if checkpointer else None,
    )

    logger.info("Deep agent created successfully")
    return agent
