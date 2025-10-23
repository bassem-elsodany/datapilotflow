"""
Graph response handler for SkillPilot conversation workflows.

This module provides functions to handle responses from the SkillPilot LangGraph,
including both synchronous and streaming response handling with MongoDB checkpointing.
"""

import logging
import uuid
from typing import Any, AsyncGenerator, Union

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from opik.integrations.langchain import OpikTracer

from src.config import settings

logger = logging.getLogger(__name__)


async def get_response(
    messages: str | list[str] | list[dict[str, Any]],
    candidate_id: str,
    interview_context: dict[str, str],
    new_thread: bool = False,
) -> tuple[str, SkillPilotState]:
    """Run a conversation through the SkillPilot LangGraph.

    Args:
        messages: Initial prompt or conversation history.
        candidate_id: Unique identifier for the candidate.
        interview_context: Dict with context (e.g. role, seniority, tags).
        new_thread: Start a new interview thread (vs resume).

    Returns:
        Tuple[str, SkillPilotState]:
            - Last message content from AI
            - Final SkillPilot state
    """
    graph_builder = build_graph()

    try:
        async with AsyncMongoDBSaver.from_conn_string(
            conn_string=settings.MONGO_CONN_STR,
            db_name=settings.MONGO_DB_NAME,
            checkpoint_collection_name=settings.MONGO_STATE_CHECKPOINT_COLLECTION,
            writes_collection_name=settings.MONGO_STATE_WRITES_COLLECTION,
        ) as checkpointer:
            output_state = await _process_graph(graph_builder, checkpointer, messages, candidate_id, interview_context, new_thread)

        # Ensure output_state is not None
        if output_state is None:
            logger.error("Output state is None")
            raise RuntimeError("Graph execution returned None output state")
            
        # Ensure output_state has messages
        if "messages" not in output_state or not output_state["messages"]:
            logger.error(f"Output state missing messages. Available keys: {list(output_state.keys())}")
            output_state["messages"] = [AIMessage(content="Error: No messages in response")]

        last_message = output_state["messages"][-1]
        return last_message.content, SkillPilotState(**output_state)

    except Exception as e:
        raise RuntimeError(f"Error running SkillPilot interview flow: {str(e)}") from e


async def get_streaming_response(
    messages: str | list[str] | list[dict[str, Any]],
    candidate_id: str,
    interview_context: dict[str, str],
    new_thread: bool = False,
) -> AsyncGenerator[str, None]:
    """Stream a response from the SkillPilot LangGraph.

    Args:
        messages: Prompt or prior message history.
        candidate_id: Unique candidate ID.
        interview_context: Dictionary with metadata and role setup.
        new_thread: Start fresh or resume.

    Yields:
        AIMessage content chunks.
    """
    graph_builder = build_graph()

    try:
        async with AsyncMongoDBSaver.from_conn_string(
            conn_string=settings.MONGO_CONN_STR,
            db_name=settings.MONGO_DB_NAME,
            checkpoint_collection_name=settings.MONGO_STATE_CHECKPOINT_COLLECTION,
            writes_collection_name=settings.MONGO_STATE_WRITES_COLLECTION,
        ) as checkpointer:
            async for chunk in _stream_graph(graph_builder, checkpointer, messages, candidate_id, interview_context, new_thread):
                yield chunk

    except Exception as e:
        raise RuntimeError(f"Error during SkillPilot streaming flow: {str(e)}") from e


def __format_messages(messages: Union[str, list[dict[str, Any]]]) -> list[Union[HumanMessage, AIMessage]]:
    """Convert user messages to LangChain-compatible objects."""
    if isinstance(messages, str):
        return [HumanMessage(content=messages)]

    if isinstance(messages, list):
        if not messages:
            return []

        if isinstance(messages[0], dict) and "role" in messages[0]:
            result = []
            for msg in messages:
                if msg["role"] == "user":
                    result.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    result.append(AIMessage(content=msg["content"]))
            return result

        return [HumanMessage(content=m) for m in messages]

    return []


def _ensure_messages_in_input(input_dict: dict) -> dict:
    if "messages" not in input_dict or not isinstance(input_dict["messages"], list):
        input_dict["messages"] = []
    return input_dict


def _debug_state_messages(state: dict, node_name: str) -> dict:
    """Debug function to track when 'messages' key is lost."""
    if "messages" not in state:
        logger.error(f"CRITICAL: 'messages' key missing in state after {node_name}")
        logger.error(f"State keys: {list(state.keys())}")
        # Add empty messages list to prevent further errors
        state["messages"] = []
    return state


async def _process_graph(
    graph_builder,
    checkpointer,
    messages: str | list[str] | list[dict[str, Any]],
    candidate_id: str,
    interview_context: dict[str, str],
    new_thread: bool,
) -> dict:
    """Process the graph with the given checkpointer.

    Args:
        graph_builder: The graph builder instance.
        checkpointer: The storage checkpointer instance.
        messages: Initial prompt or conversation history.
        candidate_id: Unique identifier for the candidate.
        interview_context: Dict with context.
        new_thread: Start a new interview thread.

    Returns:
        The output state from the graph.
    """
    graph = graph_builder.compile(checkpointer=checkpointer)
    opik_tracer = OpikTracer(graph=graph.get_graph(xray=True))

    # Ensure candidate_id is not None or empty
    if not candidate_id or candidate_id.strip() == "":
        logger.warning(f"Invalid candidate_id: '{candidate_id}', generating new thread_id")
        candidate_id = f"unknown-{uuid.uuid4()}"
    
    # Ensure candidate_id is not None or empty
    if not candidate_id or candidate_id.strip() == "":
        logger.warning(f"Invalid candidate_id: '{candidate_id}', generating new thread_id")
        candidate_id = f"unknown-{uuid.uuid4()}"
    
    thread_id = candidate_id if not new_thread else f"{candidate_id}-{uuid.uuid4()}"
    
    # Ensure thread_id is valid
    if not thread_id or thread_id.strip() == "":
        logger.error(f"Generated invalid thread_id: '{thread_id}', using fallback")
        thread_id = f"fallback-{uuid.uuid4()}"
    
    logger.info(f"Using thread_id: {thread_id}")
    
    # Ensure thread_id is valid
    if not thread_id or thread_id.strip() == "":
        logger.error(f"Generated invalid thread_id: '{thread_id}', using fallback")
        thread_id = f"fallback-{uuid.uuid4()}"
    
    logger.info(f"Using thread_id: {thread_id}")
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [opik_tracer],
        "recursion_limit": 50,  # Increase recursion limit to prevent infinite loops
    }

    # Ensure interview_context is not None
    if interview_context is None:
        logger.warning("interview_context is None, using empty dict")
        interview_context = {}
    
    input_data = {
        "messages": __format_messages(messages),
        **interview_context,
    }
    input_data = _ensure_messages_in_input(input_data)
    
    # Log input data for debugging
    logger.info(f"Input data keys: {list(input_data.keys())}")
    logger.info(f"Messages count: {len(input_data.get('messages', []))}")

    try:
        result = await graph.ainvoke(
            input=input_data,
            config=config,
        )
        
        # Ensure result is not None
        if result is None:
            logger.error("Graph returned None result")
            raise RuntimeError("Graph execution returned None result")
            
        # Ensure result has messages
        if "messages" not in result:
            logger.error(f"Result missing 'messages' key. Available keys: {list(result.keys())}")
            result["messages"] = [AIMessage(content="Error: No messages in response")]
            
        return result
        
    except KeyError as e:
        if "'messages'" in str(e):
            logger.error(f"CRITICAL: 'messages' key error in graph execution")
            logger.error(f"Input data keys: {list(input_data.keys())}")
            logger.error(f"Input data messages: {input_data.get('messages', 'NOT_FOUND')}")
            raise RuntimeError(f"State lost 'messages' key during graph execution: {e}")
        else:
            raise
    except Exception as e:
        logger.error(f"Graph execution error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        if "'messages'" in str(e):
            logger.error(f"CRITICAL: 'messages' key error in graph execution")
            logger.error(f"Input data keys: {list(input_data.keys())}")
            logger.error(f"Input data messages: {input_data.get('messages', 'NOT_FOUND')}")
            raise RuntimeError(f"State lost 'messages' key during graph execution: {e}")
        else:
            raise


async def _stream_graph(
    graph_builder,
    checkpointer,
    messages: str | list[str] | list[dict[str, Any]],
    candidate_id: str,
    interview_context: dict[str, str],
    new_thread: bool,
) -> AsyncGenerator[str, None]:
    """Stream the graph with the given checkpointer.

    Args:
        graph_builder: The graph builder instance.
        checkpointer: The storage checkpointer instance.
        messages: Initial prompt or conversation history.
        candidate_id: Unique identifier for the candidate.
        interview_context: Dict with context.
        new_thread: Start a new interview thread.

    Yields:
        AIMessage content chunks.
    """
    graph = graph_builder.compile(checkpointer=checkpointer)
    opik_tracer = OpikTracer(graph=graph.get_graph(xray=True))

    # Ensure candidate_id is not None or empty
    if not candidate_id or candidate_id.strip() == "":
        logger.warning(f"Invalid candidate_id: '{candidate_id}', generating new thread_id")
        candidate_id = f"unknown-{uuid.uuid4()}"
    
    thread_id = candidate_id if not new_thread else f"{candidate_id}-{uuid.uuid4()}"
    
    # Ensure thread_id is valid
    if not thread_id or thread_id.strip() == "":
        logger.error(f"Generated invalid thread_id: '{thread_id}', using fallback")
        thread_id = f"fallback-{uuid.uuid4()}"
    
    logger.info(f"Using thread_id: {thread_id}")
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [opik_tracer],
        "recursion_limit": 50,  # Increase recursion limit to prevent infinite loops
    }

    input_data = {
        "messages": __format_messages(messages),
        **interview_context,
    }
    input_data = _ensure_messages_in_input(input_data)

    try:
        async for chunk in graph.astream(
            input=input_data,
            config=config,
            stream_mode="messages",
        ):
            if chunk[1]["langgraph_node"] == "capture_answer" and isinstance(
                chunk[0], AIMessageChunk
            ):
                yield chunk[0].content
    except KeyError as e:
        if "'messages'" in str(e):
            logger.error(f"CRITICAL: 'messages' key error in streaming graph execution")
            logger.error(f"Input data keys: {list(input_data.keys())}")
            logger.error(f"Input data messages: {input_data.get('messages', 'NOT_FOUND')}")
            raise RuntimeError(f"State lost 'messages' key during streaming graph execution: {e}")
        else:
            raise
    except Exception as e:
        if "'messages'" in str(e):
            logger.error(f"CRITICAL: 'messages' key error in streaming graph execution")
            logger.error(f"Input data keys: {list(input_data.keys())}")
            logger.error(f"Input data messages: {input_data.get('messages', 'NOT_FOUND')}")
            raise RuntimeError(f"State lost 'messages' key during streaming graph execution: {e}")
        else:
            raise