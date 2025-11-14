"""Dynamic Tool Creation for Supervisor Agent.

Creates LangChain tools from conversation configuration at runtime.
Supports both prompt-based tools (LLM-powered) and MCP tools (external servers).
"""

import asyncio
from typing import Any, Dict, List, Optional

from langchain_core.tools import StructuredTool
from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.domain.conversation.models import AssistantConfig
from src.domain.tool.models import Tool, ToolType


class SupervisorToolFactory:
    """Factory for creating LangChain tools from Tool configurations."""

    @staticmethod
    def create_prompt_based_tool(
        tool: Tool,
        llm_client: BaseChatModel,
        rag_context: str = "",
    ) -> StructuredTool:
        """Create a prompt-based LangChain tool.

        Args:
            tool: Tool domain object with configuration
            llm_client: LLM client for tool execution
            rag_context: RAG documents to inject into tool execution

        Returns:
            LangChain StructuredTool

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

        def execute_tool(user_input: str) -> str:
            """Execute prompt-based tool using LLM with RAG context.

            Args:
                user_input: The user's query or request

            Returns:
                Response from LLM
            """
            logger.info(
                f"Tool '{tool_name}' executing | Input: {len(user_input)} chars | RAG Context: {len(rag_context)} chars"
            )

            # Build prompt with RAG context
            full_prompt = f"""{system_prompt}

**User Input:**
{user_input}

**Task:** Process the input according to the system prompt above and provide your response.
"""

            # Append RAG context if available
            if rag_context:
                full_prompt += f"""

================================================================================
⚠️ CRITICAL: YOU MUST USE ONLY THE FOLLOWING KNOWLEDGE BASE AS SOURCE OF TRUTH
================================================================================

The following retrieved documents from the knowledge base are the ONLY authoritative source
for your response. You MUST NOT use any other knowledge or training data. If the required
information is not in these documents, you MUST say so explicitly.

## Retrieved Knowledge Base Documents

{rag_context}

================================================================================
END OF KNOWLEDGE BASE DOCUMENTS
================================================================================
"""

            # Execute via LLM (SYNC call - not async)
            try:
                response = llm_client.invoke(full_prompt)
                result = response.content if hasattr(response, 'content') else str(response)
                logger.info(f"Tool '{tool_name}' completed | Output: {len(result)} chars")
                return result
            except Exception as e:
                error_msg = f"Tool '{tool_name}' error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        # Create StructuredTool from sync function
        return StructuredTool.from_function(
            func=execute_tool,
            name=tool_name,
            description=tool_description,
        )

    @staticmethod
    async def create_tools_from_config(
        assistant_config: AssistantConfig,
        llm_client: BaseChatModel,
        tool_instances: Dict[str, Tool],
        rag_context: str = "",
    ) -> Dict[str, StructuredTool]:
        """Create all tools from assistant configuration.

        Args:
            assistant_config: Conversation assistant configuration
            llm_client: LLM client for tool execution
            tool_instances: Dict mapping tool IDs to Tool domain objects
            rag_context: RAG documents to inject into tools

        Returns:
            Dict mapping tool names to StructuredTool instances

        Raises:
            ValueError: If tool configuration is invalid
        """
        tools_dict = {}

        if not assistant_config.tools:
            logger.warning("No tools configured in assistant config")
            return tools_dict

        for tool_id in assistant_config.tools:
            try:
                if tool_id not in tool_instances:
                    logger.warning(f"Tool {tool_id} not found in tool_instances")
                    continue

                tool = tool_instances[tool_id]

                if tool.tool_type == ToolType.PROMPT_BASED:
                    logger.info(f"Creating prompt-based tool: {tool.name}")
                    created_tool = SupervisorToolFactory.create_prompt_based_tool(
                        tool=tool,
                        llm_client=llm_client,
                        rag_context=rag_context,
                    )
                    tools_dict[tool.name] = created_tool

                elif tool.tool_type == ToolType.MCP_REMOTE:
                    logger.info(f"MCP tools not yet supported in supervisor: {tool.name}")
                    # Future: Add MCP tool creation logic
                    pass

                else:
                    logger.warning(f"Unknown tool type: {tool.tool_type} for {tool.name}")

            except Exception as e:
                logger.error(f"Failed to create tool '{tool_id}': {e}")
                raise

        logger.info(f"Created {len(tools_dict)} tools from config")
        return tools_dict
