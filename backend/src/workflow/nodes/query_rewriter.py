"""
Query rewriter node for TrustRAG LangGraph implementation.

This node expands user queries with related terms to improve document retrieval.
"""

from typing import Dict, Any
from ..state import WorkflowState
from ..prompts.rewrite_prompts import REWRITE_SYSTEM_PROMPT, REWRITE_USER_PROMPT


def query_rewriter(state: WorkflowState) -> WorkflowState:
    """
    Rewrite and expand user query with related terms.
    
    Args:
        state: Current workflow state containing the user query
        
    Returns:
        Updated state with rewritten query and expanded terms
    """
    try:
        # Add processing step
        state["processing_steps"].append("query_rewriting")
        
        # Get LLM client from config
        llm_client = state["config"].get("llm_client")
        if not llm_client:
            raise ValueError("LLM client not found in config")
        
        # Format the rewrite prompt
        user_prompt = REWRITE_USER_PROMPT.format(query=state["query"])
        
        # Call LLM for query rewriting
        response = llm_client.chat(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1
        )
        
        # Parse the response to extract expanded terms
        expanded_terms = []
        if response:
            # Split by semicolon and clean up
            terms = [term.strip() for term in response.split(";") if term.strip()]
            expanded_terms = terms[:5]  # Limit to 5 terms
        
        # Format rewritten query
        if expanded_terms:
            formatted_terms = "\n".join(f"{i+1}. {term};" for i, term in enumerate(expanded_terms))
            rewritten_query = f"{state['query']} {formatted_terms}"
        else:
            rewritten_query = state["query"]
        
        # Update state
        state["rewritten_query"] = rewritten_query
        state["expanded_terms"] = expanded_terms
        
        print(f"✅ Query rewritten: {len(expanded_terms)} terms expanded")
        
    except Exception as e:
        error_msg = f"Query rewriting failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # Fallback to original query
        state["rewritten_query"] = state["query"]
        state["expanded_terms"] = []
    
    return state
