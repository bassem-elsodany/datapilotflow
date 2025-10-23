"""
Document retriever node for DataPilotFlow LangGraph implementation.

This node retrieves relevant documents using semantic search.
"""

from typing import Dict, Any
from ..state import WorkflowState


def document_retriever(state: WorkflowState) -> WorkflowState:
    """
    Retrieve relevant documents using semantic search.
    
    Args:
        state: Current workflow state containing the rewritten query
        
    Returns:
        Updated state with retrieved documents and scores
    """
    try:
        # Add processing step
        state["processing_steps"].append("document_retrieval")
        
        # Get embedding generator and vector store from config
        embedding_generator = state["config"].get("embedding_generator")
        vector_store = state["config"].get("vector_store")
        
        if not embedding_generator or not vector_store:
            raise ValueError("Embedding generator or vector store not found in config")
        
        # Use rewritten query if available, otherwise use original query
        search_query = state.get("rewritten_query", state["query"])
        
        # Generate query embedding
        query_embedding = embedding_generator.generate_embedding(search_query)
        
        # Search vector store
        retrieved_docs = vector_store.search(
            query_embedding=query_embedding,
            top_k=state["top_k"]
        )
        
        # Extract documents and scores
        documents = [doc["text"] for doc in retrieved_docs]
        scores = [doc["score"] for doc in retrieved_docs]
        
        # Update state
        state["retrieved_documents"] = retrieved_docs
        state["document_scores"] = scores
        
        print(f"✅ Retrieved {len(retrieved_docs)} documents")
        
    except Exception as e:
        error_msg = f"Document retrieval failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # Set empty results
        state["retrieved_documents"] = []
        state["document_scores"] = []
    
    return state
