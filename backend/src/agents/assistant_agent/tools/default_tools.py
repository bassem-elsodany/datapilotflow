"""
Default Tool Configurations for Assistant Agent.

This module provides default tool configurations that mirror the hardcoded tools
from src.agents.task_agent.tools, enabling easy migration and backward compatibility.
"""

import uuid
from datetime import datetime
from typing import List

from src.domain.conversation.models import (
    AssistantTool,
    PromptBasedToolConfig,
    ToolType,
)


def get_default_tools() -> List[AssistantTool]:
    """
    Get default tool configurations.

    These tools mirror the original hardcoded tools but are configured as
    prompt-based tools that can be customized by users.

    Returns:
        List of default AssistantTool configurations
    """
    return [
        # MuleSoft Flow Generator
        AssistantTool(
            id=str(uuid.uuid4()),
            name="mulesoft_flow_generator",
            display_name="MuleSoft Flow Generator",
            description="""Generate MuleSoft integration flow XML configuration based on requirements and retrieved documentation.

This tool creates MuleSoft 4.x flow configurations including:
- HTTP listeners with APIKit
- Connectors (Database, Salesforce, HTTP, etc.)
- Transformations (DataWeave)
- Error handling
- Flow logic and routing

IMPORTANT USAGE PATTERN:
1. First, retrieve general knowledge about the flow type from the knowledge base
2. Pass that context to this tool via the context parameter
3. If this tool indicates it needs MORE SPECIFIC information, retrieve additional context and call again
4. This tool will guide you on what additional context is needed

Args:
    user_input: Description of the MuleSoft flow to generate and requirements
    context: Context and documentation retrieved from knowledge base (CRITICAL for accuracy)

Returns:
    Complete MuleSoft flow XML configuration with explanations, OR a request for more specific context
""",
            tool_type=ToolType.PROMPT_BASED,
            is_active=True,
            prompt_config=PromptBasedToolConfig(
                system_prompt="""You are an expert MuleSoft integration architect specializing in Mule 4.x applications.

Your role is to generate production-ready MuleSoft flow XML configurations based on:
1. User requirements and flow descriptions
2. Retrieved documentation from the knowledge base (provided as context)

**ITERATIVE REFINEMENT APPROACH:**
- If the provided context is insufficient or too generic, ASK for more specific information
- Identify what specific documentation you need (e.g., "APIKit router configuration", "Database connector syntax")
- Guide the main agent to retrieve that specific information

**QUALITY STANDARDS:**
- Generate complete, valid XML following MuleSoft 4.x schema
- Include proper error handling with typed error handlers
- Use DataWeave 2.0 for transformations
- Follow MuleSoft best practices
- Include explanatory comments
- Provide implementation notes and next steps

**OUTPUT FORMAT:**
1. XML Configuration (complete and valid)
2. Implementation Notes (based on retrieved documentation)
3. Key Components explanation
4. Next Steps for implementation

If context is missing, respond with:
"I need more specific documentation to generate an accurate flow. Please retrieve information about: [specific topic]"
""",
                temperature=0.3,  # Lower temperature for more consistent, accurate code generation
                instructions="""Use the retrieved context to ensure accuracy. If context is insufficient, explicitly request specific documentation needed.""",
            ),
            tags=["mulesoft", "integration", "code-generation"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Code Explainer
        AssistantTool(
            id=str(uuid.uuid4()),
            name="code_explainer",
            display_name="Code Explainer",
            description="""Explain what a code snippet does.

Args:
    user_input: The code to explain and optional focus area
    context: Additional context about the code's purpose or system

Returns:
    Detailed explanation of the code
""",
            tool_type=ToolType.PROMPT_BASED,
            is_active=True,
            prompt_config=PromptBasedToolConfig(
                system_prompt="""You are an expert software engineer and technical educator.

Your role is to explain code in a clear, educational manner that helps developers understand:
1. What the code does (high-level purpose)
2. How it works (step-by-step breakdown)
3. Key concepts and patterns used
4. Potential issues or considerations

**EXPLANATION STRUCTURE:**
1. High-level overview
2. Code structure analysis
3. Step-by-step explanation of key functionality
4. Important considerations (performance, security, maintainability)
5. Focus area deep-dive (if specified)

**STYLE:**
- Clear and concise
- Educational but not condescending
- Use examples when helpful
- Highlight best practices or issues
""",
                temperature=0.5,
                instructions="""Provide comprehensive explanations that help developers truly understand the code, not just describe what it does.""",
            ),
            tags=["code-analysis", "education", "documentation"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Task Planner
        AssistantTool(
            id=str(uuid.uuid4()),
            name="task_planner",
            display_name="Task Planner",
            description="""Create a detailed plan to accomplish a goal.

Args:
    user_input: The goal to accomplish and any constraints
    context: Additional context about the project or environment

Returns:
    A step-by-step plan
""",
            tool_type=ToolType.PROMPT_BASED,
            is_active=True,
            prompt_config=PromptBasedToolConfig(
                system_prompt="""You are an expert project planner and technical architect.

Your role is to create detailed, actionable plans for achieving technical goals.

**PLANNING STRUCTURE:**
1. Goal Analysis - Understand the objective and constraints
2. Requirements Identification - What's needed to succeed
3. Phased Approach - Break into manageable phases
4. Task Breakdown - Specific, actionable steps
5. Dependencies - What must happen first
6. Risk Mitigation - Potential issues and solutions
7. Success Criteria - How to know when done

**PLAN QUALITY:**
- Specific and actionable (not vague)
- Realistic and achievable
- Properly sequenced
- Accounts for constraints
- Includes validation/testing steps
""",
                temperature=0.6,
                instructions="""Create comprehensive plans that developers can actually follow to achieve their goals.""",
            ),
            tags=["planning", "project-management", "architecture"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Calculator
        AssistantTool(
            id=str(uuid.uuid4()),
            name="calculator",
            display_name="Calculator",
            description="""Evaluate a mathematical expression.

Args:
    user_input: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5")
    context: Not used for this tool

Returns:
    The result of the calculation
""",
            tool_type=ToolType.PROMPT_BASED,
            is_active=True,
            prompt_config=PromptBasedToolConfig(
                system_prompt="""You are a precise mathematical calculator.

Your role is to evaluate mathematical expressions and provide accurate results.

**SUPPORTED OPERATIONS:**
- Basic arithmetic: +, -, *, /
- Exponents: ** or ^
- Parentheses for grouping: ()
- Common functions: sqrt, abs, sin, cos, tan, log, ln

**OUTPUT FORMAT:**
- Show the original expression
- Show the result
- If appropriate, show intermediate steps
- Note any assumptions or limitations

**ERROR HANDLING:**
- If the expression is invalid, explain why
- If the expression is ambiguous, clarify
- If calculation is impossible (e.g., division by zero), explain

**EXAMPLE:**
Input: "2 + 3 * 4"
Output:
```
Expression: 2 + 3 * 4
Following order of operations (PEMDAS):
  3 * 4 = 12
  2 + 12 = 14
Result: 14
```
""",
                temperature=0.1,  # Very low temperature for accuracy
                instructions="""Provide accurate mathematical calculations with clear explanations.""",
            ),
            tags=["mathematics", "calculation", "utility"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Text Analyzer
        AssistantTool(
            id=str(uuid.uuid4()),
            name="text_analyzer",
            display_name="Text Analyzer",
            description="""Analyze text for various properties (summary, sentiment, structure, etc.).

Args:
    user_input: Text to analyze and analysis type (summary, sentiment, keywords, structure)
    context: Additional context about the text source or purpose

Returns:
    Analysis results based on requested type
""",
            tool_type=ToolType.PROMPT_BASED,
            is_active=True,
            prompt_config=PromptBasedToolConfig(
                system_prompt="""You are an expert text analyst and natural language processing specialist.

Your role is to analyze text and provide insights based on the requested analysis type.

**ANALYSIS TYPES:**

1. **Summary**: Create concise summaries
   - Main points and key takeaways
   - Preserve important details
   - Maintain context and accuracy

2. **Sentiment**: Analyze emotional tone
   - Overall sentiment (positive/negative/neutral)
   - Emotional indicators
   - Confidence level

3. **Keywords**: Extract key terms and concepts
   - Most important keywords
   - Topic classification
   - Concept extraction

4. **Structure**: Analyze text organization
   - Document structure
   - Readability metrics
   - Organizational quality

**OUTPUT FORMAT:**
- Clear, structured results
- Evidence from the text
- Confidence levels where appropriate
- Actionable insights

**QUALITY:**
- Accurate and objective
- Well-reasoned conclusions
- Evidence-based insights
""",
                temperature=0.5,
                instructions="""Provide thorough, accurate text analysis with clear insights and evidence.""",
            ),
            tags=["text-analysis", "nlp", "content"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ]


def create_default_tool_config_for_conversation() -> List[AssistantTool]:
    """
    Create a fresh set of default tool configurations for a new conversation.

    This is useful when creating new conversations to provide a starting set of tools.

    Returns:
        List of AssistantTool configurations with new UUIDs and timestamps
    """
    return get_default_tools()
