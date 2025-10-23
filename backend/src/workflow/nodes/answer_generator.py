"""
Answer generator node for DataPilotFlow LangGraph implementation.

This node generates the final answer based on the user's question and relevant documents.
"""

from typing import Dict, Any
from ..state import WorkflowState
from ..prompts.generation_prompts import GENERATION_SYSTEM_PROMPT, GENERATION_USER_PROMPT


def answer_generator(state: WorkflowState) -> WorkflowState:
    """
    Generate final answer based on relevant documents.
    
    Args:
        state: Current workflow state containing judged documents
        
    Returns:
        Updated state with final answer and context
    """
    try:
        # Add processing step
        state["processing_steps"].append("answer_generation")
        
        # Get LLM client from config
        llm_client = state["config"].get("llm_client")
        if not llm_client:
            raise ValueError("LLM client not found in config")
        
        judged_docs = state.get("judged_documents", [])
        
        # Filter relevant documents (label = 1)
        relevant_docs = [doc for doc in judged_docs if doc.get("relevance_label", 0) == 1]
        
        if not relevant_docs:
            print("⚠️ No relevant documents found, using all retrieved documents")
            relevant_docs = judged_docs
        
        # Build context from relevant documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"{i}. {doc['text']}")
        
        context = "\n".join(context_parts)
        
        # Format the generation prompt
        user_prompt = GENERATION_USER_PROMPT.format(
            context=context,
            question=state["query"]
        )
        
        # Call LLM for answer generation
        response = llm_client.chat(
            system_prompt=GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3
        )
        
        # Update state
        state["context"] = context
        state["final_answer"] = response
        
        print(f"✅ Generated answer using {len(relevant_docs)} relevant documents")
        
    except Exception as e:
        error_msg = f"Answer generation failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # Set fallback answer
        state["context"] = ""
        state["final_answer"] = "I apologize, but I encountered an error while generating the answer. Please try again."
    
    return state
