"""
Document judger node for DataPilotFlow LangGraph implementation.

This node judges the relevance of retrieved documents to the user's question.
"""

from typing import Any, Dict

import opik

from ..prompts.judge_prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT
from ..state import WorkflowState


@opik.track(name="document_judger", tags=["document_judging"])
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
            f"🔍 Judging documents using {provider.provider_type}/{llm_model_name}"
        )

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
                # Get the prompt text from the Prompt object
                judge_system_text = (
                    JUDGE_SYSTEM_PROMPT.text
                    if hasattr(JUDGE_SYSTEM_PROMPT, "text")
                    else str(JUDGE_SYSTEM_PROMPT)
                )
                judge_user_template = (
                    JUDGE_USER_PROMPT.text
                    if hasattr(JUDGE_USER_PROMPT, "text")
                    else str(JUDGE_USER_PROMPT)
                )

                user_prompt = judge_user_template.format(
                    query=state["query"], document=doc["text"]
                )

                # Call LLM for document judging using LiteLLM
                import litellm

                litellm_model = f"{provider.provider_type}/{llm_model_name}"

                llm_response = litellm.completion(
                    model=litellm_model,
                    messages=[
                        {"role": "system", "content": judge_system_text},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    api_key=provider.api_key,
                    api_base=provider.endpoint if provider.endpoint else None,
                )

                response = llm_response.choices[0].message.content

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
