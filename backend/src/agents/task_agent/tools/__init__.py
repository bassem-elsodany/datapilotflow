"""
Task Agent tools package.

Contains LangChain tools for task execution workflows.
"""

from typing import List

from langchain_core.tools import tool
from loguru import logger


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

    IMPORTANT USAGE PATTERN:
    1. First, retrieve general knowledge about the flow type from the knowledge base
    2. Pass that context to this tool via retrieved_context parameter
    3. If this tool indicates it needs MORE SPECIFIC information, retrieve additional context and call again
    4. This tool will guide you on what additional context is needed

    ITERATIVE REFINEMENT:
    - If context is insufficient, this tool will return a message requesting specific additional information
    - You (the main agent) should then retrieve that specific information and call this tool again
    - This allows for precise, documentation-grounded flow generation

    Args:
        flow_description: Description of the MuleSoft flow to generate (e.g., "HTTP listener with APIKit")
        retrieved_context: Context and documentation retrieved from knowledge base (CRITICAL for accuracy)
        requirements: Additional specific requirements or constraints

    Returns:
        Complete MuleSoft flow XML configuration with explanations, OR a request for more specific context
    """
    logger.info(f"Generating MuleSoft flow: {flow_description[:80]}...")
    logger.debug(
        f"Context length: {len(retrieved_context)} chars, Requirements: {requirements[:50] if requirements else 'None'}"
    )

    # Check if we have sufficient context
    has_sufficient_context = len(retrieved_context) > 200  # Basic check

    # Identify what specific information might be needed
    flow_lower = flow_description.lower()
    needs_apikit = "apikit" in flow_lower or "api kit" in flow_lower
    needs_database = (
        "database" in flow_lower or "db" in flow_lower or "sql" in flow_lower
    )
    needs_salesforce = "salesforce" in flow_lower or "sfdc" in flow_lower
    needs_http = (
        "http" in flow_lower or "rest" in flow_lower or "listener" in flow_lower
    )

    # If context is insufficient and we can identify specific needs, request more
    if not has_sufficient_context and (
        needs_apikit or needs_database or needs_salesforce
    ):
        missing_topics = []
        if needs_apikit:
            missing_topics.append("APIKit configuration and RAML/OAS setup")
        if needs_database:
            missing_topics.append("Database connector configuration")
        if needs_salesforce:
            missing_topics.append("Salesforce connector setup")

        return f"""⚠️ INSUFFICIENT CONTEXT - Need More Specific Documentation

To generate an accurate MuleSoft flow for: "{flow_description}"

I need more detailed documentation about:
{chr(10).join(f"  - {topic}" for topic in missing_topics)}

**Action Required:**
Please retrieve additional knowledge about these specific topics and call me again with the enriched context.

**Example Query to Retrieve:**
"Detailed documentation on {missing_topics[0]}"

Once you provide the specific documentation, I'll generate a complete, accurate flow configuration."""

    # Note: This is a structured template generator
    # In production, this would use the retrieved_context to generate
    # accurate flows based on actual MuleSoft documentation

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
