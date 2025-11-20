"""
Standalone Tools API Router

RESTful API for managing user tools (prompt-based and MCP remote).
Tools are user-level entities, not tied to conversations.
"""

import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from langchain_community.chat_models import ChatLiteLLM
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.tool import PromptBasedToolConfig, Tool, ToolType
from src.domain.user import User
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)
from src.services.tool import get_tool_service

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PromptConfigRequest(BaseModel):
    """Request model for prompt-based tool configuration."""

    system_prompt: str
    llm_provider_id: Optional[str] = None
    llm_model_name: Optional[str] = None
    temperature: float = 0.7
    instructions: Optional[str] = None


class CreateToolRequest(BaseModel):
    """Request model for creating a tool."""

    name: str = Field(..., description="Internal tool name (used by LLM)")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Tool description for LLM")
    tool_type: str = Field(..., description="'prompt_based' or 'mcp_remote'")
    is_active: bool = True
    # For prompt_based tools
    prompt_config: Optional[PromptConfigRequest] = None
    # For mcp_remote tools
    mcp_server_id: Optional[str] = Field(
        None, description="MCP server ID (for mcp_remote tools)"
    )
    mcp_tool_name: Optional[str] = Field(
        None, description="Tool name on MCP server (for mcp_remote tools)"
    )
    tags: List[str] = Field(default_factory=list)


class UpdateToolRequest(BaseModel):
    """Request model for updating a tool."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    prompt_config: Optional[PromptConfigRequest] = None
    mcp_server_id: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    tags: Optional[List[str]] = None


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: str
    name: str
    display_name: str
    description: str
    tool_type: str
    is_active: bool
    prompt_config: Optional[dict] = None
    mcp_server_id: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    tags: List[str]
    created_at: str
    updated_at: str


class GenerateInstructionsRequest(BaseModel):
    """Request model for generating tool orchestration instructions."""

    tool_ids: List[str] = Field(
        ..., description="List of tool IDs to generate instructions for"
    )
    llm_provider_id: str = Field(
        ..., description="LLM provider ID to use for generation"
    )
    llm_model_name: str = Field(
        ..., description="LLM model name to use for generation"
    )
    user_context: Optional[str] = Field(
        None,
        description="Optional context about what the user wants to achieve",
    )


class AssistantInstructionsContext(BaseModel):
    """Context for generating assistant instructions."""

    persona: str = Field(..., description="Who is this assistant? What role does it play?")
    personality: str = Field(..., description="Communication style (professional, friendly, etc.)")
    response_style: Optional[str] = Field(None, description="How should responses be formatted?")
    task_approach: Optional[str] = Field(None, description="How should the assistant handle user requests?")
    tool_strategy: Optional[str] = Field(None, description="How should tools be used together?")
    selected_tools: Optional[List[dict]] = Field(None, description="Information about selected tools")


class GenerateAssistantInstructionsRequest(BaseModel):
    """Request model for generating complete assistant instructions."""

    tool_ids: List[str] = Field(
        default_factory=list, description="List of tool IDs (optional, can be empty)"
    )
    llm_provider_id: str = Field(
        ..., description="LLM provider ID to use for generation"
    )
    model_name: str = Field(
        ..., description="LLM model name to use for generation"
    )
    context: AssistantInstructionsContext = Field(
        ..., description="Context about assistant persona, personality, and behavior"
    )


class GenerateAssistantInstructionsResponse(BaseModel):
    """Response model for generated assistant instructions."""

    instructions: str = Field(..., description="Generated assistant instructions")
    metadata: dict = Field(default_factory=dict, description="Generation metadata")


class GenerateInstructionsResponse(BaseModel):
    """Response model for generated tool orchestration instructions."""

    instructions: str = Field(..., description="Generated orchestration instructions")
    pattern: str = Field(
        ..., description="Suggested pattern: sequential, conditional, or parallel"
    )
    reasoning: str = Field(..., description="Explanation of why these instructions")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def tool_to_response(tool: Tool) -> ToolResponse:
    """Convert Tool domain object to API response."""
    response_dict = {
        "id": tool.id,
        "name": tool.name,
        "display_name": tool.display_name,
        "description": tool.description,
        "tool_type": tool.tool_type.value,
        "is_active": tool.is_active,
        "tags": tool.tags,
        "created_at": tool.created_at.isoformat() if tool.created_at else "",
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else "",
    }

    if tool.prompt_config:
        response_dict["prompt_config"] = {
            "system_prompt": tool.prompt_config.system_prompt,
            "llm_provider_id": tool.prompt_config.llm_provider_id,
            "llm_model_name": tool.prompt_config.llm_model_name,
            "temperature": tool.prompt_config.temperature,
            "instructions": tool.prompt_config.instructions,
        }

    if tool.mcp_server_id:
        response_dict["mcp_server_id"] = tool.mcp_server_id
    if tool.mcp_tool_name:
        response_dict["mcp_tool_name"] = tool.mcp_tool_name

    return ToolResponse(**response_dict)


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    request: CreateToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tool.

    Args:
        request: Tool creation data
        user_data: Authenticated user data

    Returns:
        Created tool data

    Raises:
        HTTPException: If validation fails or creation errors occur
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        # Validate tool type
        try:
            tool_type = ToolType(request.tool_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tool_type. Must be 'prompt_based' or 'mcp_remote'",
            )

        # Validate configuration based on type
        prompt_config = None

        if tool_type == ToolType.PROMPT_BASED:
            if not request.prompt_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="prompt_config is required for prompt_based tools",
                )
            prompt_config = PromptBasedToolConfig(
                system_prompt=request.prompt_config.system_prompt,
                llm_provider_id=request.prompt_config.llm_provider_id,
                llm_model_name=request.prompt_config.llm_model_name,
                temperature=request.prompt_config.temperature,
                instructions=request.prompt_config.instructions,
            )

        elif tool_type == ToolType.MCP_REMOTE:
            if not (request.mcp_server_id and request.mcp_tool_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="mcp_server_id and mcp_tool_name are required for mcp_remote tools",
                )

        # Create tool object
        tool = Tool(
            id=str(uuid.uuid4()),
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            tool_type=tool_type,
            user_id=user_id,
            is_active=request.is_active,
            prompt_config=prompt_config,
            mcp_server_id=request.mcp_server_id,
            mcp_tool_name=request.mcp_tool_name,
            tags=request.tags,
        )

        # Save via service
        tool_service = get_tool_service()
        created_tool = tool_service.create_tool(tool)

        return tool_to_response(created_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tool: {str(e)}",
        )


@router.get("", response_model=List[ToolResponse])
async def list_tools(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
):
    """
    List all tools for the authenticated user.

    Args:
        is_active: Optional filter by active status
        user_data: Authenticated user data

    Returns:
        List of tools
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        tools = tool_service.get_user_tools(user_id, is_active=is_active)

        return [tool_to_response(tool) for tool in tools]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}",
        )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific tool by ID.

    Args:
        tool_id: Tool ID
        user_data: Authenticated user data

    Returns:
        Tool data

    Raises:
        HTTPException: If tool not found
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        tool = tool_service.get_tool_by_id(tool_id, user_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

        return tool_to_response(tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}",
        )


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing tool.

    Args:
        tool_id: Tool ID
        request: Tool update data
        user_data: Authenticated user data

    Returns:
        Updated tool data

    Raises:
        HTTPException: If tool not found or update fails
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()

        # Check if tool exists
        existing_tool = tool_service.get_tool_by_id(tool_id, user_id)
        if not existing_tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

        # Build updates dictionary
        updates = {}
        
        # For MCP_REMOTE tools, only allow updating is_active and tags
        if existing_tool.tool_type == ToolType.MCP_REMOTE:
            if request.is_active is not None:
                updates["is_active"] = request.is_active
            if request.tags is not None:
                updates["tags"] = request.tags
            
            logger.info(f"User {user_id} updating MCP remote tool {tool_id} (is_active={request.is_active}, tags={request.tags})")
        
        # For PROMPT_BASED tools, allow full updates
        elif existing_tool.tool_type == ToolType.PROMPT_BASED:
            if request.name is not None:
                updates["name"] = request.name
            if request.display_name is not None:
                updates["display_name"] = request.display_name
            if request.description is not None:
                updates["description"] = request.description
            if request.is_active is not None:
                updates["is_active"] = request.is_active
            if request.tags is not None:
                updates["tags"] = request.tags
            
            if request.prompt_config:
                updates["prompt_config"] = {
                    "system_prompt": request.prompt_config.system_prompt,
                    "llm_provider_id": request.prompt_config.llm_provider_id,
                    "llm_model_name": request.prompt_config.llm_model_name,
                    "temperature": request.prompt_config.temperature,
                    "instructions": request.prompt_config.instructions,
                }

        # Perform update
        success = tool_service.update_tool(tool_id, user_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tool",
            )

        # Fetch updated tool
        updated_tool = tool_service.get_tool_by_id(tool_id, user_id)

        return tool_to_response(updated_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tool: {str(e)}",
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a tool.

    Args:
        tool_id: Tool ID
        user_data: Authenticated user data

    Raises:
        HTTPException: If tool not found or deletion fails
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        success = tool_service.delete_tool(tool_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tool: {str(e)}",
        )


@router.post(
    "/instructions/generate",
    response_model=GenerateInstructionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate tool orchestration instructions using LLM",
    description="Generate AI-powered tool orchestration instructions based on selected tools",
)
async def generate_tool_instructions(
    request: GenerateInstructionsRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateInstructionsResponse:
    """
    Generate tool orchestration instructions using LLM.

    This endpoint analyzes the selected tools and generates intelligent instructions
    for how they should work together. The LLM considers tool descriptions, purposes,
    and suggests an appropriate pattern (sequential, conditional, or parallel).

    Args:
        request: Request containing tool IDs, LLM provider, and optional context
        current_user: Authenticated user

    Returns:
        Generated instructions with suggested pattern and reasoning

    Raises:
        400: Invalid request or no tools found
        500: LLM generation failed
    """
    try:
        # Validate request
        if not request.tool_ids or len(request.tool_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one tool ID must be provided",
            )

        logger.info(
            f"Generating instructions for {len(request.tool_ids)} tools by user {current_user.id}"
        )

        # Get tool service and fetch tool details
        tool_service = get_tool_service()
        tools_info = []
        skipped_tools = []

        for tool_id in request.tool_ids:
            tool = tool_service.get_tool_by_id(tool_id, current_user.id or "")
            if not tool:
                logger.warning(
                    f"Tool {tool_id} not found or not accessible for user {current_user.id}, skipping for instruction generation"
                )
                skipped_tools.append(tool_id)
                continue
            tools_info.append(
                {
                    "name": tool.name,
                    "display_name": tool.display_name,
                    "description": tool.description,
                    "type": tool.tool_type,
                }
            )

        # Check if we have any valid tools left
        if not tools_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"None of the provided tools were found or accessible. Skipped: {', '.join(skipped_tools)}",
            )

        if skipped_tools:
            logger.info(
                f"Skipped {len(skipped_tools)} inaccessible tools during instruction generation"
            )

        # Get LLM provider
        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(
            request.llm_provider_id, current_user.id or ""
        )

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LLM provider {request.llm_provider_id} not found",
            )

        # Initialize LLM client
        model_string = f"{provider.provider_type}/{request.llm_model_name}"
        llm_client = ChatLiteLLM(
            model=model_string,
            temperature=0.7,
            api_key=provider.api_key,
        )

        # Build prompt for instruction generation
        tools_description = "\n".join(
            [
                f"- {tool['display_name']} ({tool['name']}): {tool['description']}"
                for tool in tools_info
            ]
        )

        user_context_part = (
            f"\nUser's specific context/goal: {request.user_context}"
            if request.user_context
            else ""
        )

        prompt = f"""You are an expert in designing tool orchestration workflows.
Analyze the following tools and generate intelligent instructions for how they should work together.

AVAILABLE TOOLS:
{tools_description}
{user_context_part}

TASK:
Generate clear, practical instructions for orchestrating these tools. Consider:
1. The purpose of each tool
2. Dependencies between tools (what must run before what)
3. Whether tools can run in parallel or must be sequential
4. Conditional logic based on tool outputs
5. The optimal pattern: sequential (run one after another), conditional (based on results), or parallel (simultaneous)

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "instructions": "Clear step-by-step instructions for using these tools together. Use numbered steps or bullet points. Be specific about when each tool should be used and how outputs flow between them.",
  "pattern": "sequential|conditional|parallel",
  "reasoning": "Brief explanation of why this pattern and these instructions are optimal for these tools"
}}

Remember: Be practical, concise, and actionable. The supervisor agent will follow these instructions."""

        # Call LLM
        response = llm_client.invoke(prompt)
        response_text = response.content if isinstance(response.content, str) else str(response.content)

        # Parse JSON response
        import json

        try:
            # Try to extract JSON from response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed_response = json.loads(json_str)

                # Validate response structure
                if not all(
                    key in parsed_response
                    for key in ["instructions", "pattern", "reasoning"]
                ):
                    raise ValueError("Missing required fields in LLM response")

                # Convert instructions to string if it's a list (LLM sometimes returns as array)
                if isinstance(parsed_response["instructions"], list):
                    parsed_response["instructions"] = "\n".join(
                        str(item) for item in parsed_response["instructions"]
                    )

                # Convert reasoning to string if it's a list
                if isinstance(parsed_response["reasoning"], list):
                    parsed_response["reasoning"] = "\n".join(
                        str(item) for item in parsed_response["reasoning"]
                    )

                # Validate pattern
                if parsed_response["pattern"] not in [
                    "sequential",
                    "conditional",
                    "parallel",
                ]:
                    parsed_response["pattern"] = "sequential"  # Default fallback

                logger.info(
                    f"Successfully generated instructions for {len(request.tool_ids)} tools"
                )

                return GenerateInstructionsResponse(**parsed_response)
            else:
                raise ValueError("Could not find JSON in LLM response")

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Raw response: {response_text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse LLM response: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tool instructions: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate instructions: {str(e)}",
        )


@router.post(
    "/generate-instructions",
    response_model=GenerateAssistantInstructionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate complete assistant instructions using AI",
    description="Generate personalized assistant instructions based on persona, personality, and tools",
)
async def generate_assistant_instructions(
    request: GenerateAssistantInstructionsRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateAssistantInstructionsResponse:
    """
    Generate complete assistant instructions using LLM.

    This endpoint creates comprehensive instructions for the assistant based on:
    - Persona (who the assistant is)
    - Personality (communication style)
    - Response style
    - Task approach
    - Tool usage strategy
    - Selected tools (if any)

    Args:
        request: Request containing context and LLM details
        current_user: Authenticated user

    Returns:
        Generated instructions

    Raises:
        400: Invalid request
        500: LLM generation failed
    """
    try:
        logger.info(
            f"Generating assistant instructions for user {current_user.id} with persona: {request.context.persona[:50]}..."
        )

        # Build comprehensive prompt for instruction generation
        tools_section = ""
        if request.context.selected_tools and len(request.context.selected_tools) > 0:
            tools_list = "\n".join([
                f"- {tool.get('name')}: {tool.get('description', 'No description')} (Type: {tool.get('type')})"
                for tool in request.context.selected_tools
            ])
            tools_section = f"""

**Available Tools:**
{tools_list}

**Tool Usage Strategy:**
{request.context.tool_strategy or 'Use tools effectively to provide comprehensive responses.'}"""

        generation_prompt = f"""You are an expert at creating detailed, effective instructions for AI assistants.

Generate comprehensive instructions for an AI assistant based on the following requirements:

**Persona:**
{request.context.persona}

**Personality:**
{request.context.personality}

**Response Style:**
{request.context.response_style or 'Clear and helpful'}

**Approach to Tasks:**
{request.context.task_approach or 'Methodical and thorough'}{tools_section}

---

**Generate detailed instructions that:**
1. Define the assistant's identity and role clearly
2. Specify the communication style and tone
3. Explain how to handle different types of user requests
4. Include guidelines for response formatting
5. {"Explain how to use the available tools effectively" if tools_section else "Provide general best practices"}
6. Cover error handling and edge cases
7. Emphasize the RAG-first principle (use knowledge_expert tool for all information)

**Important Guidelines:**
- Be specific and actionable
- Use clear, direct language
- Include concrete examples where helpful
- Structure instructions logically
- Make them easy to follow

**Output the complete instructions in a clear, structured format suitable for an AI assistant to follow.**"""

        # Initialize LLM client
        from litellm import acompletion

        logger.info(f"Calling LLM: {request.llm_provider_id}/{request.model_name}")

        response = await acompletion(
            model=f"{request.llm_provider_id}/{request.model_name}",
            messages=[
                {"role": "system", "content": "You are an expert at creating AI assistant instructions."},
                {"role": "user", "content": generation_prompt},
            ],
            temperature=0.7,
        )

        instructions = response.choices[0].message.content

        logger.info(
            f"Successfully generated {len(instructions)} characters of instructions"
        )

        return GenerateAssistantInstructionsResponse(
            instructions=instructions,
            metadata={
                "persona": request.context.persona,
                "personality": request.context.personality,
                "tools_count": len(request.context.selected_tools) if request.context.selected_tools else 0,
                "generated_by": f"{request.llm_provider_id}/{request.model_name}",
            },
        )

    except Exception as e:
        logger.error(f"Failed to generate assistant instructions: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate instructions: {str(e)}",
        )


# Note: MCP tool discovery is now handled by the mcp_servers_router
# via the GET /mcp-servers/{server_id}/discover endpoint
