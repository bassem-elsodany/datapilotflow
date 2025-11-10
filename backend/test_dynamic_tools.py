"""
Test script for dynamic tools system.

This script validates the implementation of the dynamic tools system.
"""

from src.agents.assistant_agent.tools.default_tools import get_default_tools
from src.agents.assistant_agent.tools.tool_factory import ToolFactory
from src.domain.conversation.models import (
    AssistantConfig,
    AssistantTool,
    MCPRemoteToolConfig,
    PromptBasedToolConfig,
    ToolType,
)


def test_domain_models():
    """Test domain models for tools."""
    print("=" * 80)
    print("TEST 1: Domain Models")
    print("=" * 80)

    # Test PromptBasedToolConfig
    prompt_config = PromptBasedToolConfig(
        system_prompt="Test prompt",
        temperature=0.7,
    )
    print(f"✓ Created PromptBasedToolConfig: {prompt_config.system_prompt}")

    # Test MCPRemoteToolConfig
    mcp_config = MCPRemoteToolConfig(
        server_url="http://localhost:3000",
        tool_name="test_tool",
        server_type="http",
    )
    print(f"✓ Created MCPRemoteToolConfig: {mcp_config.server_url}")

    # Test AssistantTool (prompt-based)
    tool = AssistantTool(
        id="test-id",
        name="test_tool",
        display_name="Test Tool",
        description="A test tool",
        tool_type=ToolType.PROMPT_BASED,
        prompt_config=prompt_config,
    )
    print(f"✓ Created AssistantTool (prompt-based): {tool.name}")

    # Test AssistantConfig
    config = AssistantConfig(
        enabled=True,
        tools=[tool],
    )
    active_tools = config.get_active_tools()
    print(f"✓ Created AssistantConfig with {len(active_tools)} active tools")

    print("\n" + "=" * 80)
    print("TEST 1: PASSED ✓")
    print("=" * 80 + "\n")


def test_default_tools():
    """Test default tool configurations."""
    print("=" * 80)
    print("TEST 2: Default Tools")
    print("=" * 80)

    default_tools = get_default_tools()
    print(f"✓ Retrieved {len(default_tools)} default tools")

    for tool in default_tools:
        print(f"  - {tool.display_name} ({tool.name})")
        assert tool.tool_type == ToolType.PROMPT_BASED
        assert tool.prompt_config is not None
        assert tool.is_active is True

    print("\n" + "=" * 80)
    print("TEST 2: PASSED ✓")
    print("=" * 80 + "\n")


def test_tool_factory():
    """Test tool factory creation."""
    print("=" * 80)
    print("TEST 3: Tool Factory")
    print("=" * 80)

    # Create test tool configuration
    test_tool = AssistantTool(
        id="factory-test",
        name="factory_test_tool",
        display_name="Factory Test Tool",
        description="Test tool for factory",
        tool_type=ToolType.PROMPT_BASED,
        prompt_config=PromptBasedToolConfig(
            system_prompt="You are a test assistant.",
            temperature=0.5,
        ),
    )

    # Test tool creation (without LLM client for now)
    langchain_tool = ToolFactory.create_prompt_based_tool(test_tool, llm_client=None)
    print(f"✓ Created LangChain tool: {langchain_tool.name}")
    print(f"  Description: {langchain_tool.description[:50]}...")

    # Test batch creation
    default_tools = get_default_tools()
    langchain_tools = ToolFactory.create_tools_from_config(
        default_tools, llm_client=None
    )
    print(f"✓ Created {len(langchain_tools)} LangChain tools from config")

    print("\n" + "=" * 80)
    print("TEST 3: PASSED ✓")
    print("=" * 80 + "\n")


def test_assistant_config_with_tools():
    """Test AssistantConfig with multiple tools."""
    print("=" * 80)
    print("TEST 4: AssistantConfig with Tools")
    print("=" * 80)

    # Get default tools
    tools = get_default_tools()

    # Create assistant config
    config = AssistantConfig(
        enabled=True,
        system_prompt_tasks=None,
        tools=tools,
    )

    # Test active tools retrieval
    active_tools = config.get_active_tools()
    print(f"✓ AssistantConfig has {len(active_tools)} active tools")

    # Disable one tool
    tools[0].is_active = False
    active_tools = config.get_active_tools()
    print(f"✓ After disabling 1 tool, {len(active_tools)} active tools remain")

    print("\n" + "=" * 80)
    print("TEST 4: PASSED ✓")
    print("=" * 80 + "\n")


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("*" * 80)
    print("  DYNAMIC TOOLS SYSTEM - TEST SUITE")
    print("*" * 80)
    print("\n")

    try:
        test_domain_models()
        test_default_tools()
        test_tool_factory()
        test_assistant_config_with_tools()

        print("\n")
        print("*" * 80)
        print("  ALL TESTS PASSED ✓✓✓")
        print("*" * 80)
        print("\n")
        print("Dynamic tools system is working correctly!")
        print("\nNext steps:")
        print("1. Create API endpoints for tool management (Phase 4)")
        print("2. Test with real LLM client for prompt-based tools")
        print("3. Test MCP remote tools with actual MCP server")
        print("4. Test end-to-end with supervisor agent")
        return True

    except Exception as e:
        print("\n")
        print("*" * 80)
        print("  TESTS FAILED ✗✗✗")
        print("*" * 80)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
