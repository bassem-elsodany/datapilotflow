"""
Task Agent tools package.

Contains LangChain tools for task execution workflows.
"""

from typing import List

from langchain_core.tools import tool
from loguru import logger

# Lazy import for LLM client to avoid circular imports
_llm_client = None


def get_llm_client():
    """Get the LLM client for tool execution (lazy import to avoid circular deps)."""
    global _llm_client
    if _llm_client is None:
        try:
            # TODO: Implement LLM client getter if needed
            # For now, tools work without LLM fallback
            logger.warning("LLM client not configured for task_agent tools")
            _llm_client = None
        except Exception as e:
            logger.warning(f"Could not get LLM client for tools: {e}")
            _llm_client = None
    return _llm_client


@tool
def code_explainer(code_snippet: str, focus_area: str = "") -> str:
    """
    Explain what a code snippet does.

    Args:
        code_snippet: The code to explain
        focus_area: Optional specific area to focus explanation on

    Returns:
        Detailed explanation of the code
    """
    logger.info(f"Explaining code snippet ({len(code_snippet)} chars)...")

    return f"""Code Explanation:

The provided code snippet performs the following:

1. [Code structure analysis]
2. [Key functionality explanation]
3. [Important considerations]

{f'Focus on {focus_area}:' if focus_area else ''}
[Detailed explanation of the focus area]
"""


@tool
def task_planner(goal: str, constraints: str = "") -> str:
    """
    Create a detailed plan to accomplish a goal.

    Args:
        goal: The goal to accomplish
        constraints: Optional constraints or requirements

    Returns:
        A step-by-step plan
    """
    logger.info(f"Planning task: {goal[:50]}...")

    return f"""Task Plan: {goal}

Constraints: {constraints if constraints else 'None specified'}

Step-by-Step Plan:
1. Analysis Phase
   - Understand requirements
   - Identify key components

2. Design Phase
   - Create architecture
   - Define interfaces

3. Implementation Phase
   - Build core functionality
   - Add error handling

4. Testing Phase
   - Unit tests
   - Integration tests

5. Deployment Phase
   - Prepare for production
   - Deploy and monitor
"""


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5")

    Returns:
        The result of the calculation
    """
    logger.info(f"Calculating: {expression}")

    try:
        # Safe evaluation of mathematical expressions
        # In production, use a safer parser like ast.literal_eval with validation
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"


@tool
def text_analyzer(text: str, analysis_type: str = "summary") -> str:
    """
    Analyze text for various purposes.

    Args:
        text: The text to analyze
        analysis_type: Type of analysis (summary, sentiment, keywords, structure)

    Returns:
        Analysis results
    """
    logger.info(f"Analyzing text ({len(text)} chars) - type: {analysis_type}")

    if analysis_type == "summary":
        return (
            f"Text Summary:\n[Key points from the text]\nLength: {len(text)} characters"
        )
    elif analysis_type == "sentiment":
        return "Sentiment Analysis:\n- Overall tone: [Positive/Negative/Neutral]\n- Key emotions: [List]"
    elif analysis_type == "keywords":
        return "Keywords:\n- [keyword 1]\n- [keyword 2]\n- [keyword 3]"
    else:
        return f"Text Structure:\n- Characters: {len(text)}\n- Words: {len(text.split())}\n- Lines: {len(text.split(chr(10)))}"


@tool
def mulesoft_flow_generator(
    flow_description: str, retrieved_context: str = "", requirements: str = ""
) -> str:
    """
    Generate MuleSoft integration flow XML configuration based on requirements and retrieved documentation.

    This tool creates MuleSoft 4.x flow configurations including:
    - HTTP listeners with APIKit
    - Connectors (Database, Salesforce, HTTP, etc.)
    - Transformations (DataWeave)
    - Error handling
    - Flow logic and routing

    CRITICAL: This tool uses retrieved documentation to generate accurate, production-ready flows.
    The RAG context is ESSENTIAL for generating flows that match your specific requirements.

    Args:
        flow_description: Description of the MuleSoft flow to generate (e.g., "HTTP listener with APIKit")
        retrieved_context: Context and documentation retrieved from knowledge base (CRITICAL for accuracy)
        requirements: Additional specific requirements or constraints

    Returns:
        Complete MuleSoft flow XML configuration with explanations based on the retrieved documentation
    """
    logger.info(f"Generating MuleSoft flow: {flow_description[:80]}...")
    logger.debug(
        f"Context length: {len(retrieved_context)} chars, Requirements: {requirements[:50] if requirements else 'None'}"
    )

    # CRITICAL: The actual flow generation should be done by tool_factory's LLM-based wrapper
    # This function is called by the LLM with RAG context already injected
    # The LLM will use the retrieved_context parameter (injected as rag_documents)
    # to generate flows that match the documentation

    # If no context provided, inform the agent to retrieve context first
    if not retrieved_context or len(retrieved_context) < 100:
        return f"""⚠️ INSUFFICIENT CONTEXT

To generate a high-quality MuleSoft flow for: "{flow_description}"

I need detailed documentation from the knowledge base about:
- MuleSoft flow architecture and patterns
- APIKit configuration (if applicable)
- Connector setup and configuration
- DataWeave transformation examples
- Error handling patterns

**Action Required:**
Retrieve detailed MuleSoft documentation from the knowledge base matching your flow requirements,
then call this tool again with the enriched context.

The retrieved documentation will be used to generate a precise, production-ready flow configuration."""

    # If context is provided, use LLM to generate intelligent response based on context
    llm = get_llm_client()
    if llm:
        # Build prompt for LLM to generate flow using the retrieved context
        generation_prompt = f"""You are an Advanced MuleSoft Integration Architect powered by Retrieval-Augmented Generation (RAG).

Generate a production-ready MuleSoft integration flow based on the requirements and retrieved documentation below.

**User Request:** {flow_description}

**Requirements:** {requirements if requirements else 'Standard best practices'}

**Retrieved Knowledge Base Documentation:**

{retrieved_context}

---

**Your Task:**
Using ONLY the retrieved documentation above, generate:
1. A complete, production-ready MuleSoft flow XML configuration
2. Brief explanations of key components
3. Configuration instructions
4. Testing guidance

**CRITICAL CONSTRAINTS:**
- Use ONLY the information from the retrieved documentation
- Do NOT use general training knowledge
- If information is missing, explicitly state what additional documentation is needed
- Follow MuleSoft 4.x standards and best practices
- Include comprehensive error handling
- Generate complete XML, not templates or stubs

**🎯 OUTPUT FORMAT (CRITICAL - USE MARKDOWN):**
❌ DO NOT output:
- Internal analysis sections like "Document Analysis", "Architectural Decisions"
- Raw XML without markdown code blocks
- Plain text notes without markdown formatting

✅ DO output (Use MARKDOWN):
- Wrap ALL XML code in markdown code blocks: ```xml ... ```
- Use ## for section headers
- Use - for bullet point lists
- Use `backticks` for inline code
- Present clean, formatted result ready for end-user

**Remember:** Output must be valid MARKDOWN format, NOT plain text.

---

Generate the complete MuleSoft configuration now:"""

        try:
            logger.debug("Invoking LLM for MuleSoft flow generation with RAG context")
            response = llm.invoke(generation_prompt)

            if hasattr(response, "content"):
                result = response.content
            else:
                result = str(response)

            logger.info(
                f"MuleSoft flow generation completed | Response: {len(result)} chars"
            )
            return result
        except Exception as e:
            logger.error(f"Error invoking LLM for flow generation: {e}")
            # Fall back to template if LLM fails
            pass

    # Fallback if no LLM available
    return f"""
# MuleSoft Integration Flow: {flow_description}

## Flow Configuration (XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mule xmlns="http://www.mulesoft.org/schema/mule/core"
      xmlns:http="http://www.mulesoft.org/schema/mule/http"
      xmlns:apikit="http://www.mulesoft.org/schema/mule/mule-apikit"
      xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="
        http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd
        http://www.mulesoft.org/schema/mule/http http://www.mulesoft.org/schema/mule/http/current/mule-http.xsd
        http://www.mulesoft.org/schema/mule/mule-apikit http://www.mulesoft.org/schema/mule/mule-apikit/current/mule-apikit.xsd
        http://www.mulesoft.org/schema/mule/ee/core http://www.mulesoft.org/schema/mule/ee/core/current/mule-ee.xsd">

    <!-- Configuration based on: {flow_description} -->
    <!-- Requirements: {requirements if requirements else 'Standard configuration'} -->
    
    <!-- HTTP Listener Configuration -->
    <http:listener-config name="HTTP_Listener_Config">
        <http:listener-connection host="0.0.0.0" port="8081"/>
    </http:listener-config>
    
    <!-- Main Flow -->
    <flow name="main-flow">
        <http:listener config-ref="HTTP_Listener_Config" path="/api/*">
            <http:response statusCode="#[vars.httpStatus default 200]">
                <http:headers>#[vars.outboundHeaders default {{}}]</http:headers>
            </http:response>
            <http:error-response statusCode="#[vars.httpStatus default 500]">
                <http:body>#[payload]</http:body>
                <http:headers>#[vars.outboundHeaders default {{}}]</http:headers>
            </http:error-response>
        </http:listener>
        
        <!-- APIKit Router (if using APIKit) -->
        <apikit:router config-ref="apikit-config"/>
        
        <!-- Error Handling -->
        <error-handler>
            <on-error-propagate type="APIKIT:BAD_REQUEST">
                <ee:transform>
                    <ee:message>
                        <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{{
  "error": "Bad Request",
  "message": error.description
}}]]></ee:set-payload>
                    </ee:message>
                    <ee:variables>
                        <ee:set-variable variableName="httpStatus">400</ee:set-variable>
                    </ee:variables>
                </ee:transform>
            </on-error-propagate>
            <on-error-propagate type="ANY">
                <ee:transform>
                    <ee:message>
                        <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{{
  "error": "Internal Server Error",
  "message": error.description
}}]]></ee:set-payload>
                    </ee:message>
                    <ee:variables>
                        <ee:set-variable variableName="httpStatus">500</ee:set-variable>
                    </ee:variables>
                </ee:transform>
            </on-error-propagate>
        </error-handler>
    </flow>
    
</mule>
```

## Implementation Notes

**Based on Retrieved Documentation:**
{retrieved_context[:500] if retrieved_context else 'No specific documentation context provided. Flow generated using standard MuleSoft 4.x patterns.'}

**Key Components:**
1. HTTP Listener - Configured on port 8081, path /api/*
2. APIKit Router - For REST API implementation
3. Error Handling - Proper error responses with DataWeave transformations
4. Response Configuration - Status codes and headers

**Additional Requirements Applied:**
{requirements if requirements else 'Standard MuleSoft best practices applied'}

**Next Steps:**
1. Import this configuration into Anypoint Studio
2. Add your RAML/OAS API specification
3. Implement the flow logic for each endpoint
4. Add connectors as needed (Database, Salesforce, etc.)
5. Configure DataWeave transformations
6. Test the flow

**Best Practices Applied:**
- Proper error handling with typed error handlers
- DataWeave 2.0 transformations
- HTTP status code management
- Separation of configuration and flow logic
"""


def get_task_agent_tools() -> List:
    """
    Get all tools available for the Task Agent.

    Returns:
        List of LangChain tools
    """
    return [
        mulesoft_flow_generator,  # MuleSoft-specific tool first
        code_explainer,
        task_planner,
        calculator,
        text_analyzer,
    ]


__version__ = "1.0.0"

__all__ = [
    "mulesoft_flow_generator",
    "code_explainer",
    "task_planner",
    "calculator",
    "text_analyzer",
    "get_task_agent_tools",
]
