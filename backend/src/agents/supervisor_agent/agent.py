"""Supervisor Agent service implementation."""

import json
from typing import Any, Dict, List, Optional

from langchain_community.chat_models import ChatLiteLLM
from loguru import logger

from src.agents.common.agent_interface import AgentService
from src.agents.common.agent_state import AgentState
from src.agents.supervisor_agent.chains import get_intent_detection_chain


class SupervisorAgentService(AgentService):
    """
    Supervisor Agent - Intelligent Orchestrator.

    Responsibilities:
    - Detect user intent from the input
    - Route to appropriate agent(s): RAG only, Task only, or RAG → Task
    - Coordinate multi-step workflows
    - Inject RAG context to Task Agent when available
    - Synthesize final response from agent outputs
    - Handle errors and recovery

    This is NOT itself a worker agent. It's a coordinator that:
    1. Understands what the user needs
    2. Decides which agents to activate
    3. Passes context between agents
    4. Returns the final result to the user
    """

    def __init__(
        self,
        llm_client: ChatLiteLLM,
        rag_agent: Optional[Any] = None,
        task_agent: Optional[Any] = None,
    ):
        """
        Initialize Supervisor Agent.

        Args:
            llm_client: LangChain LLM client for intent detection
            rag_agent: RAGAgentService instance
            task_agent: TaskAgentService instance
        """
        self.llm_client = llm_client
        self.rag_agent = rag_agent
        self.task_agent = task_agent
        logger.info("✅ Supervisor Agent initialized")

    def set_agents(self, rag_agent: Any, task_agent: Any) -> None:
        """
        Set the worker agents (called after initialization if needed).

        Args:
            rag_agent: RAGAgentService instance
            task_agent: TaskAgentService instance
        """
        self.rag_agent = rag_agent
        self.task_agent = task_agent
        logger.info("✅ Supervisor: Worker agents registered")

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute supervisor logic: detect intent and route to agents.

        This is the main orchestration method.

        Args:
            state: Current AgentState with user input in messages

        Returns:
            Final AgentState with all agent results and final response
        """
        try:
            logger.info("🎯 Supervisor: Starting intent detection and routing")

            # Step 1: Detect user intent
            intent = await self._detect_intent(state)
            state["intent"] = intent
            logger.info(f"🔍 Supervisor: Detected intent: {intent}")

            # Step 2: Route to agents based on intent
            # Knowledge base is the ONLY source of truth - all requests must be grounded in it
            if intent == "rag_only":
                logger.info("📚 Supervisor: Routing to RAG Agent for retrieval only")
                state = await self.rag_agent.execute(state)

            elif intent == "rag_then_task":
                logger.info(
                    "📚 Supervisor: Routing to RAG Agent first, then Task Agent"
                )
                state = await self.rag_agent.execute(state)
                state = await self.task_agent.execute(state)

            else:
                logger.warning(
                    f"⚠️  Supervisor: Unknown intent '{intent}', defaulting to rag_only"
                )
                state = await self.rag_agent.execute(state)

            logger.info("🎉 Supervisor: Orchestration complete")
            return state

        except Exception as e:
            logger.error(f"❌ Supervisor error: {e}")
            raise

    async def _detect_intent(self, state: AgentState) -> str:
        """
        Detect user intent using LLM chain with enhanced search planning.

        Returns one of:
        - "rag_only": User wants to search/retrieve information from knowledge base
        - "rag_then_task": User wants to do a task using retrieved knowledge from knowledge base

        Also extracts and stores in state:
        - search_queries: List of targeted search queries for comprehensive context retrieval
        - task_description: Description of the task to perform (for rag_then_task)
        - intent_reasoning: Why this intent was chosen

        Knowledge base is the ONLY source of truth - all requests must be grounded in it.

        Args:
            state: Current AgentState

        Returns:
            Detected intent string
        """
        messages = state.get("messages", [])
        if not messages:
            logger.warning("No messages for intent detection, defaulting to rag_only")
            state["search_queries"] = []
            return "rag_only"

        user_message = messages[-1]
        user_input = user_message.get("content", "")

        try:
            # Use the intent detection chain with enhanced JSON response
            chain = get_intent_detection_chain(self.llm_client)

            # Invoke the chain with user input
            response = chain.invoke({"user_input": user_input})
            response_text = response.content.strip()

            # Extract JSON from response (handle markdown code blocks if present)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON response
            intent_data = json.loads(json_text)

            # Extract intent
            intent = intent_data.get("intent", "rag_only").strip().lower()

            # Validate intent - only rag_only and rag_then_task are supported
            valid_intents = ["rag_only", "rag_then_task"]
            if intent not in valid_intents:
                logger.warning(
                    f"Invalid intent returned: {intent}, defaulting to rag_only"
                )
                intent = "rag_only"

            # Extract task planning information
            task_description = intent_data.get("task_description")
            execution_plan = intent_data.get("execution_plan")
            reasoning = intent_data.get("reasoning", "")

            # Store in state for Task agent to use
            state["task_description"] = task_description
            state["execution_plan"] = execution_plan
            state["intent_reasoning"] = reasoning

            logger.info(f"✅ Intent: {intent} | Reasoning: {reasoning}")
            if task_description:
                logger.info(f"🎯 Task: {task_description}")
            if execution_plan:
                logger.info(f"📋 Execution Plan: {execution_plan}")

            return intent

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse intent JSON: {e}, response: {response_text[:200]}"
            )
            logger.warning("Falling back to simple intent detection")
            # Fallback: try to extract just the intent from the response
            response_lower = response_text.lower()
            if "rag_then_task" in response_lower:
                return "rag_then_task"
            return "rag_only"

        except Exception as e:
            logger.error(f"Error detecting intent: {e}, defaulting to rag_only")
            return "rag_only"

    def get_agent_name(self) -> str:
        """Return agent name."""
        return "Supervisor Agent"

    def get_supported_intents(self) -> List[str]:
        """Return supported intent types."""
        return ["routing"]

    def get_description(self) -> str:
        """Return agent description."""
        return (
            "Intelligent supervisor and orchestrator. Detects user intent and routes "
            "between RAG and Task agents. Coordinates multi-step workflows and injects "
            "RAG context into Task Agent when needed."
        )
