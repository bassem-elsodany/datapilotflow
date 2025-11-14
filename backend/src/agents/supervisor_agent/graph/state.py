"""State definitions for Supervisor ReAct agent.

Based on react-agent pattern with extensions for RAG context and tool tracking.
"""

from typing import Any, Dict, List, Optional, Annotated
from dataclasses import dataclass, field

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


@dataclass
class SupervisorReActState:
    """
    Extended ReAct state for supervisor agent.

    Inherits message handling pattern from MessagesState but as dataclass.
    Adds RAG context and tool tracking for custom supervision logic.

    Fields:
        messages: Conversation history. New messages are merged using add_messages reducer.
        rag_documents: Retrieved documents from RAG tool
        rag_context: Formatted context string from RAG documents
        rag_context_size: Size of RAG context in characters
        tools_used: List of tool names used during execution
    """

    # Messages with add_messages reducer (like MessagesState)
    messages: Annotated[List[AnyMessage], add_messages] = field(default_factory=list)

    # RAG context - accumulated during execution
    rag_documents: Dict[str, Any] = field(default_factory=dict)
    rag_context: str = ""
    rag_context_size: int = 0

    # Tool tracking for observability
    tools_used: List[str] = field(default_factory=list)

    def add_tool_used(self, tool_name: str) -> None:
        """Record a tool being used."""
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)

    def set_rag_context(self, documents: List[Dict[str, Any]], context_str: str) -> None:
        """Store RAG documents and formatted context."""
        self.rag_documents = {"documents": documents}
        self.rag_context = context_str
        self.rag_context_size = len(context_str)
