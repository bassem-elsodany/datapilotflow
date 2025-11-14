"""Tool initialization pipeline for supervisor agent.

Integrates SupervisorToolFactory, ToolRegistry, and RAG tool creation.
Provides a single entry point for setting up all tools from conversation configuration.
"""

from typing import Optional, Dict, Any, List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from loguru import logger

from src.agents.supervisor_agent.tool_factory import SupervisorToolFactory
from src.agents.supervisor_agent.tools import ToolRegistry
from src.domain.conversation.models import AssistantConfig
from src.domain.tool.models import Tool


def create_knowledge_expert_tool(
    llm_client: BaseChatModel,
) -> StructuredTool:
    """Create the RAG knowledge_expert tool.

    This tool retrieves from the knowledge base using the configured
    RAG pipeline (enhanced queries, multi-query retrieval, reranking, etc).

    Args:
        llm_client: LLM client for knowledge enrichment

    Returns:
        StructuredTool: knowledge_expert tool ready for use
    """
    logger.info("Creating knowledge_expert RAG tool")

    def retrieve_knowledge(search_query: List[str]) -> str:
        """Retrieve documents from knowledge base.

        Args:
            search_query: List of query variants for multi-query retrieval
                         (using RRF fusion or single query strategy)

        Returns:
            Formatted string of retrieved documents for RAG context
        """
        logger.info(
            f"Knowledge expert retrieving documents for {len(search_query)} query variants"
        )

        # This is a placeholder for actual RAG retrieval
        # In production, this would:
        # 1. Call the RAG service with configured enhancement strategy
        # 2. Use multi-query retrieval with configured strategy
        # 3. Apply reranking if configured
        # 4. Format results as structured context
        #
        # For now, we return a template structure showing what would be retrieved
        knowledge_context = f"""
Retrieved Knowledge Base Documents
===================================

Query Variants Searched: {', '.join(search_query)}

Documents Retrieved: [Documents would be retrieved here based on configured RAG pipeline]

Document Sources:
- [Source references would be listed here]
- [Metadata and relevance scores included]

Retrieved Content:
[Actual document content would be formatted here with clear sections]

"""
        return knowledge_context

    tool = StructuredTool.from_function(
        func=retrieve_knowledge,
        name="knowledge_expert",
        description="Retrieves documents from the knowledge base using multi-query retrieval with configured enhancement strategies. Input should be a JSON array of query variants for better coverage.",
    )

    return tool


def initialize_tools_from_config(
    assistant_config: AssistantConfig,
    llm_client: BaseChatModel,
    rag_context: str = "",
    tool_instances: Optional[Dict[str, Tool]] = None,
) -> ToolRegistry:
    """Initialize ToolRegistry from conversation assistant configuration.

    This function:
    1. Creates the knowledge_expert RAG tool
    2. Creates task tools from Tool instances using SupervisorToolFactory
    3. Registers all tools in a ToolRegistry
    4. Returns the populated registry

    Args:
        assistant_config: AssistantConfig specifying which tools are enabled
        llm_client: LLM client for tool execution
        rag_context: RAG documents to inject into tool execution
        tool_instances: Dict mapping tool IDs to Tool domain objects
                       (fetched from database in normal flow)

    Returns:
        ToolRegistry: Initialized registry with all tools ready to use

    Raises:
        ValueError: If configuration is invalid or required tools missing
    """
    logger.info(
        f"Initializing tool registry for assistant config with tools: {assistant_config.tools}"
    )

    registry = ToolRegistry()

    # Step 1: Create and register knowledge_expert RAG tool
    knowledge_tool = create_knowledge_expert_tool(llm_client)
    registry.register("knowledge_expert", knowledge_tool)
    logger.info("Registered knowledge_expert RAG tool")

    # Step 2: Create and register task tools from configuration
    if assistant_config.tools:
        if not tool_instances:
            logger.warning("No tool instances provided - cannot create task tools")
            logger.warning(
                "In production, fetch Tool instances from database using tool IDs"
            )
        else:
            # Create task tools for each configured tool ID
            for tool_id in assistant_config.tools:
                if tool_id not in tool_instances:
                    logger.warning(f"Tool {tool_id} not found in tool_instances dict")
                    continue

                tool_domain = tool_instances[tool_id]

                try:
                    # Use SupervisorToolFactory to create the tool
                    task_tool = SupervisorToolFactory.create_prompt_based_tool(
                        tool=tool_domain,
                        llm_client=llm_client,
                        rag_context=rag_context,
                    )
                    registry.register(tool_domain.name, task_tool)
                    logger.info(f"Registered task tool: {tool_domain.name}")

                except Exception as e:
                    logger.error(f"Failed to create task tool {tool_id}: {e}")
                    raise

    logger.info(
        f"Tool registry initialized with {len(registry)} tools: {registry.list_ids()}"
    )
    return registry


async def initialize_tools_from_config_async(
    assistant_config: AssistantConfig,
    llm_client: BaseChatModel,
    rag_context: str = "",
    tool_instances: Optional[Dict[str, Tool]] = None,
) -> ToolRegistry:
    """Async version of tool initialization.

    Supports tools that require async initialization.

    Args:
        assistant_config: AssistantConfig specifying which tools are enabled
        llm_client: LLM client for tool execution
        rag_context: RAG documents to inject into tool execution
        tool_instances: Dict mapping tool IDs to Tool domain objects

    Returns:
        ToolRegistry: Initialized registry with all tools ready to use

    Raises:
        ValueError: If configuration is invalid or required tools missing
    """
    logger.info(
        f"Async initializing tool registry for assistant config with tools: {assistant_config.tools}"
    )

    registry = ToolRegistry()

    # Step 1: Create and register knowledge_expert RAG tool
    knowledge_tool = create_knowledge_expert_tool(llm_client)
    registry.register("knowledge_expert", knowledge_tool)
    logger.info("Registered knowledge_expert RAG tool")

    # Step 2: Create and register task tools from configuration
    if assistant_config.tools:
        if not tool_instances:
            logger.warning("No tool instances provided - cannot create task tools")
        else:
            # Create task tools for each configured tool ID
            for tool_id in assistant_config.tools:
                if tool_id not in tool_instances:
                    logger.warning(f"Tool {tool_id} not found in tool_instances dict")
                    continue

                tool_domain = tool_instances[tool_id]

                try:
                    # Use SupervisorToolFactory to create the tool
                    task_tool = SupervisorToolFactory.create_prompt_based_tool(
                        tool=tool_domain,
                        llm_client=llm_client,
                        rag_context=rag_context,
                    )
                    registry.register(tool_domain.name, task_tool)
                    logger.info(f"Registered task tool: {tool_domain.name}")

                except Exception as e:
                    logger.error(f"Failed to create task tool {tool_id}: {e}")
                    raise

    logger.info(
        f"Tool registry initialized with {len(registry)} tools: {registry.list_ids()}"
    )
    return registry
