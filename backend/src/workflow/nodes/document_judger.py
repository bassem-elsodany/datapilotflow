"""
Document judger node for DataPilotFlow LangGraph implementation.

This node judges the relevance of retrieved documents to the user's question.
"""

from typing import Dict, Any
from ..state import WorkflowState
from ..prompts.judge_prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT


def document_judger(state: WorkflowState) -> WorkflowState:
    """
    Judge the relevance of retrieved documents.
    
    Args:
        state: Current workflow state containing retrieved documents
        
    Returns:
        Updated state with judged documents and relevance labels
    """
    try:
        # Add processing step
        state["processing_steps"].append("document_judging")
        
        # Get LLM client from config
        llm_client = state["config"].get("llm_client")
        if not llm_client:
            raise ValueError("LLM client not found in config")
        
        retrieved_docs = state.get("retrieved_documents", [])
        if not retrieved_docs:
            print("⚠️ No documents to judge")
            state["judged_documents"] = []
            state["relevance_labels"] = []
            return state
        
        judged_docs = []
        relevance_labels = []
        
        # Judge each document
        for doc in retrieved_docs:
            try:
                # Format the judge prompt
                user_prompt = JUDGE_USER_PROMPT.format(
                    query=state["query"],
                    document=doc["text"]
                )
                
                # Call LLM for document judging
                response = llm_client.chat(
                    system_prompt=JUDGE_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.1
                )
                
                # Parse judgment result
                try:
                    judgment = int(response.strip())
                    if judgment not in [0, 1]:
                        judgment = 0  # Default to not relevant
                except (ValueError, AttributeError):
                    judgment = 0  # Default to not relevant if parsing fails
                
                # Add judgment to document
                judged_doc = doc.copy()
                judged_doc["relevance_label"] = judgment
                judged_docs.append(judged_doc)
                relevance_labels.append(judgment)
                
            except Exception as e:
                print(f"⚠️ Failed to judge document: {e}")
                # Default to not relevant
                judged_doc = doc.copy()
                judged_doc["relevance_label"] = 0
                judged_docs.append(judged_doc)
                relevance_labels.append(0)
        
        # Update state
        state["judged_documents"] = judged_docs
        state["relevance_labels"] = relevance_labels
        
        relevant_count = sum(relevance_labels)
        print(f"✅ Judged {len(judged_docs)} documents, {relevant_count} relevant")
        
    except Exception as e:
        error_msg = f"Document judging failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # Set empty results
        state["judged_documents"] = []
        state["relevance_labels"] = []
    
    return state
