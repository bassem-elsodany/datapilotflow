"""
Dynamic Tool Factory for Assistant Agent.

This module provides a factory for creating LangChain tools from configuration at runtime,
supporting both prompt-based tools (LLM-powered) and MCP remote tools (external servers).
Uses langchain-mcp-adapters for native MCP integration.
"""

import asyncio
import json
import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from langchain_core.tools import StructuredTool
from loguru import logger

from src.domain.conversation.models import AssistantConfig
from src.domain.tool import PromptBasedToolConfig, Tool, ToolType

if TYPE_CHECKING:
    from src.domain.tool import MCPServerConfig

# Module-level storage for RAG context - injected by supervisor before tool execution
# This is the ONLY reliable way to pass RAG documents across async boundaries
_rag_context_storage: Dict[str, str] = {}


class ToolFactory:
    """Factory for creating LangChain tools from Tool domain model configurations."""

    @staticmethod
    def _build_mcp_auth_headers(mcp_server_config: "MCPServerConfig") -> Dict[str, str]:
        """
        Build authentication headers for MCP server connection (HTTP Streamable).

        Args:
            mcp_server_config: MCP server configuration

        Returns:
            Dictionary of HTTP headers for authentication
        """
        from src.agents.assistant_agent.tools.mcp_auth import build_mcp_auth

        auth = build_mcp_auth(
            mcp_server_config.auth_type, mcp_server_config.auth_credentials
        )

        headers = {}
        if auth:
            if hasattr(auth, "build_request"):
                # httpx.Auth object - extract headers manually
                if mcp_server_config.auth_type == "bearer":
                    token = mcp_server_config.auth_credentials.get(
                        "bearer_token"
                    ) or mcp_server_config.auth_credentials.get("token")
                    if token:
                        headers["Authorization"] = f"Bearer {token.strip()}"
                elif mcp_server_config.auth_type == "api_key":
                    api_key = mcp_server_config.auth_credentials.get("api_key")
                    header_name = mcp_server_config.auth_credentials.get(
                        "header_name", "X-API-Key"
                    )
                    if api_key:
                        headers[header_name] = api_key.strip()
                elif mcp_server_config.auth_type == "basic":
                    import base64

                    username = mcp_server_config.auth_credentials.get("username", "")
                    password = mcp_server_config.auth_credentials.get("password", "")
                    if username and password:
                        credentials = f"{username}:{password}"
                        encoded = base64.b64encode(credentials.encode()).decode()
                        headers["Authorization"] = f"Basic {encoded}"
            elif isinstance(auth, str):
                # Direct token string (for Bearer)
                headers["Authorization"] = f"Bearer {auth.strip()}"

        return headers

    @staticmethod
    def create_prompt_based_tool_from_domain(
        tool: Tool, llm_client: Optional[Any] = None, rag_context: Optional[str] = None
    ) -> Any:
        """
        Create a LangChain tool from a Tool domain object (prompt-based).

        Args:
            tool: Tool domain object from database
            llm_client: Optional LLM client for executing the tool
            rag_context: Optional RAG documents/context to inject into tool (deprecated - use context var)

        Returns:
            LangChain tool function

        Raises:
            ValueError: If prompt_config is missing
        """
        if not tool.prompt_config:
            raise ValueError(
                f"Tool '{tool.name}': prompt_config required for PROMPT_BASED tools"
            )

        prompt_config = tool.prompt_config
        tool_name = tool.name
        tool_description = tool.description
        system_prompt = prompt_config.system_prompt

        # Create the tool function dynamically
        def dynamic_prompt_tool(user_input: str, rag_documents: str = "") -> str:
            """Execute prompt-based tool using LLM with RAG documents injected as parameter.

            Args:
                user_input: The user's query or request
                rag_documents: Formatted RAG documents injected by supervisor as parameter

            Returns:
                Response from LLM based on user input and RAG documents
            """
            # Try to get RAG context from parameter first, then fallback to module storage
            # Module storage is set by supervisor before tool invocation
            final_context = rag_documents or _rag_context_storage.get("current", "")

            # Log source of RAG context for debugging
            context_source = "parameter" if rag_documents else "module_storage"

            logger.info(
                f"[PROMPT TOOL] Executing '{tool_name}' | Input: {len(user_input)} chars | RAG Documents: {len(final_context)} chars (source: {context_source})"
            )

            # Build full prompt with RAG context injected at the END as "ONLY SOURCE OF TRUTH"
            # This ensures the LLM knows to use ONLY the retrieved documents for knowledge
            # The RAG context appears last to take maximum precedence
            full_prompt = f"""{system_prompt}

**User Input:**
{user_input}

**Task:** Process the input according to the system prompt above and provide your response.
"""

            # CRITICAL: Append RAG context at the END with "ONLY SOURCE OF TRUTH" disclaimer
            # This is the highest priority instruction and overrides any previous instructions
            if final_context:
                full_prompt += f"""

================================================================================
⚠️ CRITICAL: YOU MUST USE ONLY THE FOLLOWING KNOWLEDGE BASE AS SOURCE OF TRUTH
================================================================================

The following retrieved documents from the knowledge base are the ONLY authoritative source
for your response. You MUST NOT use any other knowledge or training data. If the required
information is not in these documents, you MUST say so explicitly.

## Retrieved Knowledge Base Documents

{final_context}

================================================================================
⚠️ CRITICAL: You MUST base your response ONLY on the documents above.
    - Do NOT use training data
    - Do NOT hallucinate information
    - Do NOT make up configurations or examples not in the documents
    - If information is missing from the knowledge base, explicitly state it
================================================================================
"""

            try:
                if llm_client:
                    logger.debug(f"[PROMPT TOOL] '{tool_name}': Full prompt size: {len(full_prompt)} chars")
                    response = llm_client.invoke(full_prompt)

                    if hasattr(response, "content"):
                        result = response.content
                    else:
                        result = str(response)

                    logger.info(
                        f"[PROMPT TOOL] '{tool_name}' completed | Response: {len(result)} chars"
                    )
                    return result
                else:
                    result = f"[Prompt Tool '{tool_name}'] No LLM client available. Would process: {user_input[:100]}"
                    logger.warning(result)
                    return result
            except Exception as e:
                error_msg = f"Error executing prompt tool '{tool_name}': {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                return error_msg

        # Return as StructuredTool with explicit name and description
        return StructuredTool.from_function(
            func=dynamic_prompt_tool,
            name=tool_name,
            description=tool_description,
        )

    @staticmethod
    async def _load_mcp_tool_from_server(
        mcp_server_config: "MCPServerConfig", mcp_tool_name: str
    ) -> Optional[Any]:
        """
        DEPRECATED: This method is no longer used. Tools are now loaded in batch via get_dynamic_task_tools().

        Load a specific tool from an MCP server using langchain-mcp-adapters MultiServerMCPClient.

        Args:
            mcp_server_config: MCP server configuration
            mcp_tool_name: Name of the tool on the MCP server

        Returns:
            LangChain tool instance or None if not found

        Raises:
            ImportError: If required libraries are not installed
            Exception: If connection or loading fails
        """
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError as e:
            logger.error(f"Required MCP libraries not installed: {e}")
            raise ImportError(
                "MCP libraries required. Install: pip install langchain-mcp-adapters"
            )

        logger.info(
            f"Loading MCP tool '{mcp_tool_name}' from server: {mcp_server_config.server_url}"
        )

        # Build authentication headers
        headers = ToolFactory._build_mcp_auth_headers(mcp_server_config)

        # Configure server for MultiServerMCPClient
        server_config = {
            "temp_server": {
                "transport": "streamable_http",
                "url": mcp_server_config.server_url,
            }
        }

        # Add headers if authentication is configured
        if headers:
            server_config["temp_server"]["headers"] = headers

        # Create client and load tools
        client = MultiServerMCPClient(server_config)
        all_tools = await client.get_tools()

        logger.debug(
            f"Loaded {len(all_tools)} tools from MCP server, searching for '{mcp_tool_name}'"
        )

        # Find the specific tool by name
        for lc_tool in all_tools:
            if lc_tool.name == mcp_tool_name:
                logger.info(f"Found matching MCP tool: '{mcp_tool_name}' from server")
                return lc_tool

        logger.warning(
            f"Tool '{mcp_tool_name}' not found on server. Available tools: {[t.name for t in all_tools]}"
        )
        return None

    @staticmethod
    async def create_mcp_remote_tool_from_domain(
        tool: Tool, mcp_server_config: "MCPServerConfig"
    ) -> Any:
        """
        DEPRECATED: This method is no longer used. Tools are now loaded in batch via get_dynamic_task_tools().

        Create a LangChain tool from an MCP remote tool using langchain-mcp-adapters.

        This loads the actual tool from the MCP server and returns it directly.
        No manual proxying needed - langchain-mcp-adapters handles everything.

        Args:
            tool: Tool domain object from database
            mcp_server_config: MCP server configuration

        Returns:
            LangChain tool instance

        Raises:
            RuntimeError: If tool cannot be loaded from server
        """
        mcp_tool_name = tool.mcp_tool_name

        logger.info(
            f"Creating MCP remote tool '{tool.name}' (server tool: '{mcp_tool_name}')"
        )

        try:
            # Load the tool from the MCP server (async operation)
            lc_tool = await ToolFactory._load_mcp_tool_from_server(
                mcp_server_config, mcp_tool_name
            )

            if not lc_tool:
                raise RuntimeError(
                    f"Tool '{mcp_tool_name}' not found on MCP server {mcp_server_config.server_url}"
                )

            logger.info(
                f"Successfully loaded MCP tool '{tool.name}' from server {mcp_server_config.name}"
            )
            return lc_tool

        except Exception as e:
            logger.error(f"Failed to load MCP tool '{tool.name}': {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @staticmethod
    async def discover_mcp_tools(
        mcp_server_config: "MCPServerConfig",
    ) -> List[Dict[str, Any]]:
        """
        Discover available tools from an MCP server using langchain-mcp-adapters MultiServerMCPClient.

        Args:
            mcp_server_config: MCP server configuration

        Returns:
            List of tool schemas from the MCP server

        Raises:
            ImportError: If required libraries are not installed
            Exception: If discovery fails
        """
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError as e:
            logger.error(f"Required MCP libraries not installed: {e}")
            raise ImportError(
                "MCP libraries required. Install: pip install langchain-mcp-adapters"
            )

        logger.info(
            f"Discovering tools from MCP server: {mcp_server_config.server_url}"
        )

        # Build authentication headers
        headers = ToolFactory._build_mcp_auth_headers(mcp_server_config)

        # Configure server for MultiServerMCPClient
        server_config = {
            "temp_server": {
                "transport": "streamable_http",
                "url": mcp_server_config.server_url,
            }
        }

        # Add headers if authentication is configured
        if headers:
            server_config["temp_server"]["headers"] = headers

        # Create client and load tools
        client = MultiServerMCPClient(server_config)
        all_tools = await client.get_tools()

        # Convert LangChain tools to our format for API response
        tools = []
        for lc_tool in all_tools:
            tool_data = {
                "name": lc_tool.name,
                "description": lc_tool.description or "",
                "schema": getattr(lc_tool, "args_schema", None),
            }
            tools.append(tool_data)

        logger.info(f"Discovered {len(tools)} tools from MCP server")
        return tools

    # NOTE: Old create_mcp_remote_tool() and create_tools_from_config() methods removed.
    # These accepted AssistantTool which no longer exists. Use get_dynamic_task_tools() instead.


async def get_dynamic_task_tools(
    assistant_config: AssistantConfig,
    llm_client: Optional[Any] = None,
    user_id: Optional[str] = None,
) -> List[Any]:
    """
    Get task tools from assistant configuration by loading them from the database.

    This function loads tools by their IDs stored in assistant_config.tools
    and converts them to LangChain tools ready for the supervisor agent.

    Args:
        assistant_config: Assistant configuration with tool IDs
        llm_client: Optional LLM client for prompt-based tools
        user_id: User ID for fetching tool and MCP server configurations (required)

    Returns:
        List of LangChain tools
    """
    if not assistant_config or not assistant_config.tools:
        logger.warning("No tools configured in assistant_config, returning empty list")
        return []

    if not user_id:
        logger.error("user_id is required to load tools from database")
        return []

    tool_ids = assistant_config.tools
    logger.info(f"Loading {len(tool_ids)} tools by ID: {tool_ids}")

    # Load actual Tool objects from the database
    from src.services.tool import get_tool_service

    tool_service = get_tool_service()

    tools_to_create = []
    for tool_id in tool_ids:
        try:
            tool = tool_service.get_tool_by_id(tool_id, user_id)
            if tool:
                # Only include active tools
                if tool.is_active:
                    tools_to_create.append(tool)
                    logger.debug(f"Loaded active tool: {tool.name} ({tool_id})")
                else:
                    logger.debug(f"Skipping inactive tool: {tool.name} ({tool_id})")
            else:
                logger.warning(f"Tool with ID {tool_id} not found for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to load tool {tool_id}: {e}")
            # Continue with other tools

    if not tools_to_create:
        logger.warning("No active tools found after loading from database")
        return []

    logger.info(
        f"Creating {len(tools_to_create)} LangChain tools from loaded Tool objects"
    )

    # Separate tools by type
    prompt_based_tools = [
        t for t in tools_to_create if t.tool_type.value == "prompt_based"
    ]
    mcp_remote_tools = [t for t in tools_to_create if t.tool_type.value == "mcp_remote"]

    langchain_tools = []

    # 1. Create prompt-based tools (synchronous)
    for tool in prompt_based_tools:
        try:
            if tool.prompt_config:
                lc_tool = ToolFactory.create_prompt_based_tool_from_domain(
                    tool, llm_client
                )
                langchain_tools.append(lc_tool)
                logger.info(f"Created prompt-based tool: {tool.name}")
            else:
                logger.warning(f"Tool {tool.name} has no prompt_config, skipping")
        except Exception as e:
            logger.error(
                f"Failed to create prompt-based tool {tool.name}: {e}\n{traceback.format_exc()}"
            )

    # 2. Load MCP remote tools efficiently (connect once per server)
    if mcp_remote_tools:
        from collections import defaultdict

        from langchain_mcp_adapters.client import MultiServerMCPClient

        from src.services.tool import get_mcp_server_service

        # Group tools by MCP server
        tools_by_server = defaultdict(list)
        for tool in mcp_remote_tools:
            if tool.mcp_server_id and tool.mcp_tool_name:
                tools_by_server[tool.mcp_server_id].append(tool)
            else:
                logger.warning(
                    f"Tool {tool.name} missing mcp_server_id or mcp_tool_name, skipping"
                )

        mcp_server_service = get_mcp_server_service()

        # Load tools from each unique MCP server (once per server)
        for server_id, server_tools in tools_by_server.items():
            try:
                # Get server configuration
                mcp_server_config = mcp_server_service.get_server_by_id(
                    server_id, user_id
                )

                if not mcp_server_config:
                    logger.warning(
                        f"MCP server {server_id} not found, skipping {len(server_tools)} tools"
                    )
                    continue

                logger.info(
                    f"Loading {len(server_tools)} tools from MCP server '{mcp_server_config.name}'"
                )

                # Build auth headers
                headers = ToolFactory._build_mcp_auth_headers(mcp_server_config)

                # Configure client for this server
                server_config = {
                    server_id: {
                        "transport": "streamable_http",
                        "url": mcp_server_config.server_url,
                    }
                }
                if headers:
                    server_config[server_id]["headers"] = headers

                # Connect once and load all tools from this server
                client = MultiServerMCPClient(server_config)
                all_server_tools = await client.get_tools()

                logger.debug(
                    f"Loaded {len(all_server_tools)} tools from server '{mcp_server_config.name}'"
                )

                # Filter to get only the tools we need
                for tool in server_tools:
                    matching_tool = next(
                        (t for t in all_server_tools if t.name == tool.mcp_tool_name),
                        None,
                    )

                    if matching_tool:
                        langchain_tools.append(matching_tool)
                        logger.info(
                            f"Added MCP remote tool: {tool.name} (server tool: {tool.mcp_tool_name})"
                        )
                    else:
                        logger.warning(
                            f"Tool '{tool.mcp_tool_name}' not found on server '{mcp_server_config.name}'. "
                            f"Available: {[t.name for t in all_server_tools]}"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to load tools from MCP server {server_id}: {e}\n{traceback.format_exc()}"
                )
                # Continue with other servers

    logger.info(f"Successfully created {len(langchain_tools)} LangChain tools")
    return langchain_tools


def set_rag_context(context: str) -> None:
    """
    Set RAG context that will be injected into all task tool executions.

    This is called by the supervisor after RAG documents are retrieved and formatted.
    The context is stored in module-level storage accessible to all tool invocations.

    Args:
        context: Formatted RAG documents as string (content only, no metadata)
    """
    global _rag_context_storage
    _rag_context_storage["current"] = context
    logger.info(f"[RAG CONTEXT STORAGE] Stored {len(context)} chars in module-level storage for task tools")


def get_rag_context() -> str:
    """
    Get the currently stored RAG context.

    Returns:
        Formatted RAG documents string, or empty string if none set
    """
    return _rag_context_storage.get("current", "")
