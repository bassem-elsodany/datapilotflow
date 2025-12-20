"""RAG Agent service implementation."""

from typing import Any, Dict, List, Optional

from langchain_community.chat_models import ChatLiteLLM
from loguru import logger

from src.agents.common.agent_interface import AgentService
from src.agents.common.agent_state import AgentState, RAGContext
from src.agents.rag_agent.state import RAGWorkflowState, create_initial_state


class RAGAgentService(AgentService):
    """
    RAG (Retrieval-Augmented Generation) Agent.

    Responsibilities:
    - Retrieve relevant documents from knowledge base
    - Judge document relevance
    - Rank documents by relevance
    - Filter documents based on threshold
    - Return ranked, filtered documents

    This agent encapsulates the entire RAG pipeline that was previously
    in src/workflow/ and related services.
    """

    def __init__(
        self,
        llm_client: ChatLiteLLM,
        rag_graph: Any,  # The compiled LangGraph for RAG
        conversation_service: Any = None,
    ):
        """
        Initialize RAG Agent.

        Args:
            llm_client: LangChain LLM client
            rag_graph: Compiled LangGraph for RAG pipeline
            conversation_service: Service for conversation management
        """
        self.llm_client = llm_client
        self.rag_graph = rag_graph
        self.conversation_service = conversation_service
        logger.info("✅ RAG Agent initialized")

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the RAG pipeline.

        Takes user query from messages.
        Returns state with RAGContext populated containing:
        - retrieved_documents: All documents retrieved
        - judged_documents: Documents ranked by relevance
        - relevance_scores: Relevance scores for each document
        - Execution metadata

        Args:
            state: Current AgentState

        Returns:
            Updated AgentState with rag_context populated
        """
        try:
            logger.info("🔍 RAG Agent: Starting document retrieval and ranking")

            # Extract query from latest message
            messages = state.get("messages", [])
            if not messages:
                raise ValueError("No messages in state")

            user_message = messages[-1]
            query = user_message.get("content", "")

            if not query:
                raise ValueError("Empty query in message")

            logger.debug(f"📝 RAG Agent: Processing query: {query[:100]}...")

            # Get RAG config from state
            config = state.get("config", {}) or {}
            top_k = config.get("top_k", 5)

            # Create initial RAG state
            rag_state = create_initial_state(
                query=query,
                top_k=top_k,
                config=config,
                conversation_description=state.get("conversation_description"),
            )

            logger.debug(f"⚙️  RAG Agent: Running RAG graph with top_k={top_k}")

            # Execute RAG graph
            result = await self.rag_graph.ainvoke(rag_state)

            logger.info(
                f"✅ RAG Agent: Retrieved {len(result.get('retrieved_documents', []))} documents, "
                f"Ranked {len(result.get('judged_documents', []))} as relevant"
            )

            # Extract results and populate RAGContext
            retrieved_docs = result.get("retrieved_documents", [])
            judged_docs = result.get("judged_documents", [])
            relevance_scores = result.get("relevance_scores", [])
            relevance_threshold = config.get("reranking_config", {}).get(
                "relevance_threshold", 0.5
            )

            relevant_count = sum(
                1 for score in relevance_scores if score >= relevance_threshold
            )

            rag_context = RAGContext(
                query=query,
                original_documents=retrieved_docs,
                judged_documents=judged_docs,
                retrieved_count=len(retrieved_docs),
                relevant_count=relevant_count,
                relevance_threshold=relevance_threshold,
                relevance_scores=relevance_scores,
                execution_time_ms=result.get("execution_time_ms", 0),
            )

            # Update state with RAG results
            state["rag_context"] = rag_context

            # Add summary message to message history
            summary_message = {
                "role": "assistant",
                "content": f"✅ RAG Complete: Retrieved {len(retrieved_docs)} documents, ranked {relevant_count} as relevant above threshold ({relevance_threshold})",
            }
            state["messages"] = state.get("messages", []) + [summary_message]

            logger.info("🎉 RAG Agent: Execution complete")
            return state

        except Exception as e:
            logger.error(f"❌ RAG Agent error: {e}")
            error_message = {
                "role": "assistant",
                "content": f"❌ RAG Agent failed: {str(e)}",
            }
            # FIX: Access state as dict, not object attribute
            state["messages"] = state.get("messages", []) + [error_message]
            raise

    def get_agent_name(self) -> str:
        """Return agent name."""
        return "RAG Agent"

    def get_supported_intents(self) -> List[str]:
        """Return supported intent types."""
        return ["rag_only", "rag_then_task"]

    def get_description(self) -> str:
        """Return agent description."""
        return (
            "Retrieves and ranks relevant documents from the knowledge base. "
            "Handles document filtering based on relevance thresholds and provides "
            "context for other agents."
        )
