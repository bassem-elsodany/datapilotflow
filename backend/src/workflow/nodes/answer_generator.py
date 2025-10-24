"""
Answer generator node for DataPilotFlow LangGraph implementation.

This node generates the final answer based on the user's question and relevant documents.
"""

from typing import Any, Dict

import opik

from ..prompts.generation_prompts import (
    GENERATION_SYSTEM_PROMPT,
    GENERATION_USER_PROMPT,
)
from ..state import WorkflowState


@opik.track(name="answer_generator", tags=["answer_generation"])
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

        # Get LLM configuration from state
        config = state.get("config", {})
        llm_provider_id = config.get("llm_provider_id")
        llm_model_name = config.get("llm_model_name")
        user_id = config.get("user_id")

        if not llm_provider_id or not llm_model_name or not user_id:
            raise ValueError(
                "LLM provider ID, model name, and user ID are required in config"
            )

        # Get LLM provider
        from loguru import logger

        from src.services.model_provider.model_provider_service import (
            get_model_provider_service,
        )

        model_provider_service = get_model_provider_service()
        provider = model_provider_service.get_model_provider(llm_provider_id, user_id)

        if not provider:
            raise ValueError(f"LLM provider not found: {llm_provider_id}")

        if not provider.generative:
            raise ValueError(
                f"Generative model not configured for provider: {provider.name}"
            )

        logger.info(
            f"💬 Generating answer using {provider.provider_type}/{llm_model_name}"
        )

        judged_docs = state.get("judged_documents", [])

        # Filter relevant documents (label = 1)
        relevant_docs = [
            doc for doc in judged_docs if doc.get("relevance_label", 0) == 1
        ]

        if not relevant_docs:
            print("⚠️ No relevant documents found, using all retrieved documents")
            relevant_docs = judged_docs

        # Build context from relevant documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"{i}. {doc['text']}")

        context = "\n".join(context_parts)

        # Format the generation prompt
        # Get the prompt text from the Prompt object
        generation_system_text = (
            GENERATION_SYSTEM_PROMPT.text
            if hasattr(GENERATION_SYSTEM_PROMPT, "text")
            else str(GENERATION_SYSTEM_PROMPT)
        )
        generation_user_template = (
            GENERATION_USER_PROMPT.text
            if hasattr(GENERATION_USER_PROMPT, "text")
            else str(GENERATION_USER_PROMPT)
        )

        user_prompt = generation_user_template.format(
            context=context, question=state["query"]
        )

        # Call LLM for answer generation using LiteLLM
        import litellm

        litellm_model = f"{provider.provider_type}/{llm_model_name}"

        llm_response = litellm.completion(
            model=litellm_model,
            messages=[
                {"role": "system", "content": generation_system_text},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            api_key=provider.api_key,
            api_base=provider.endpoint if provider.endpoint else None,
        )

        response = llm_response.choices[0].message.content

        # Get query information to show user the difference
        original_query = state["query"]
        enhanced_query_data = state.get("enhanced_query", {})

        # Build query comparison info
        query_info = {
            "original_query": original_query,
            "enhanced_query": None,
            "strategy_used": None,
        }

        if enhanced_query_data:
            # Get the enhanced query that was actually used for search
            if enhanced_query_data.get("multi_query_variants"):
                query_info["enhanced_query"] = enhanced_query_data[
                    "multi_query_variants"
                ][0]
                query_info["strategy_used"] = "Multi-Query"
            elif enhanced_query_data.get("fusion_perspectives"):
                query_info["enhanced_query"] = enhanced_query_data[
                    "fusion_perspectives"
                ][0]
                query_info["strategy_used"] = "Query Fusion"
            elif enhanced_query_data.get("step_back_query"):
                query_info["enhanced_query"] = enhanced_query_data["step_back_query"]
                query_info["strategy_used"] = "Step-Back"
            elif enhanced_query_data.get("hypothetical_answer"):
                query_info["enhanced_query"] = enhanced_query_data[
                    "hypothetical_answer"
                ]
                query_info["strategy_used"] = "HyDE"

        # Update state
        state["context"] = context
        state["final_answer"] = response
        state["query_info"] = query_info  # Add query comparison info

        print(f"✅ Generated answer using {len(relevant_docs)} relevant documents")

    except Exception as e:
        error_msg = f"Answer generation failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")

        # Set fallback answer
        state["context"] = ""
        state["final_answer"] = (
            "I apologize, but I encountered an error while generating the answer. Please try again."
        )

    return state
