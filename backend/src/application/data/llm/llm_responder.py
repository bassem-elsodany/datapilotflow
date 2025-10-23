"""
LLM Responder module for generating AI responses to search queries using retrieved knowledge.
"""

import json
import traceback
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
from langchain_core.documents import Document

# LLM manager imports removed - no longer supported
from ..utils.json_utils import parse_llm_response

# Placeholder functions for removed LLM manager functionality
def get_thread_local_llm():
    """Placeholder function - LLM manager no longer supported."""
    raise NotImplementedError("LLM manager functionality has been removed. Please use the new model provider system.")

def get_current_model_id():
    """Placeholder function - LLM manager no longer supported."""
    return "unsupported"

def get_current_endpoint():
    """Placeholder function - LLM manager no longer supported."""
    return "unsupported"
from src.services.conversation.conversation_history_service import conversation_history_service, ConversationMessage
from src.config import settings
from src.domain.llm_prompts import (
    structured_response_prompt,
    no_results_prompt,
    simple_response_prompt,
    context_aware_structured_prompt
)


class PromptManager:
    """Centralized prompt management using domain prompts."""
    
    @staticmethod
    def get_structured_prompt(query: str, formatted_results: str, content_count: int, 
                            total_count: int, context_instruction: str = "") -> str:
        """Generate structured prompt with optional context."""
        return structured_response_prompt.prompt.format(
            query=query,
            formatted_results=formatted_results,
            content_count=content_count,
            total_count=total_count,
            context_instruction=context_instruction
        )

    @staticmethod
    def get_no_results_prompt(query: str, context_instruction: str = "") -> str:
        """Generate prompt for when no search results are found."""
        return no_results_prompt.prompt.format(
            query=query,
            context_instruction=context_instruction
        )

    @staticmethod
    def get_simple_prompt(query: str, formatted_results: str, 
                         conversation_context: str = "") -> str:
        """Generate simple prompt without structured framework."""
        return simple_response_prompt.prompt.format(
            query=query,
            formatted_results=formatted_results,
            conversation_context=conversation_context
        )
    
    @staticmethod
    def get_context_aware_structured_prompt(query: str, formatted_results: str, 
                                          content_count: int, total_count: int,
                                          conversation_context: str = "") -> str:
        """Generate context-aware structured prompt."""
        return context_aware_structured_prompt.prompt.format(
            query=query,
            formatted_results=formatted_results,
            content_count=content_count,
            total_count=total_count,
            conversation_context=conversation_context
        )


class ResponseProcessor:
    """Utility class for processing LLM responses."""
    

    
    @staticmethod
    def extract_source_urls(search_results: List[Dict[str, Any]]) -> List[str]:
        """Extract source URLs from search results."""
        source_urls = []
        for result in search_results:
            metadata = result.get('metadata', {})
            source_url = metadata.get('source_url', '')
            if source_url:
                source_urls.append(source_url)
        return source_urls
    
    @staticmethod
    def count_content_results(search_results: List[Dict[str, Any]]) -> tuple[int, int]:
        """Count results with actual content."""
        content_count = sum(1 for r in search_results if r.get('text', '').strip())
        total_count = len(search_results)
        return content_count, total_count


class ContentAggregator:
    """Utility class for aggregating content from multiple chunks."""
    
    @staticmethod
    def aggregate_chunks_by_document(search_results: List[Dict[str, Any]], max_chunks_per_doc: int = 3) -> List[Dict[str, Any]]:
        """Aggregate multiple chunks from the same document to provide more complete context.
        
        Args:
            search_results: List of search results with chunks
            max_chunks_per_doc: Maximum number of chunks to aggregate per document
            
        Returns:
            List of aggregated search results
        """
        # Group chunks by document
        doc_groups = {}
        for result in search_results:
            metadata = result.get('metadata', {})
            doc_id = metadata.get('document_id') or metadata.get('chunk_id', '').split('_')[0]  # Extract doc ID from chunk ID
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(result)
        
        # Aggregate chunks for each document
        aggregated_results = []
        for doc_id, chunks in doc_groups.items():
            # Sort chunks by chunk_id to maintain order
            chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_id', ''))
            
            # Take up to max_chunks_per_doc
            selected_chunks = chunks[:max_chunks_per_doc]
            
            # Aggregate content
            aggregated_content = []
            for chunk in selected_chunks:
                content = chunk.get('text', '').strip()
                if content:
                    aggregated_content.append(content)
            
            if aggregated_content:
                # Create aggregated result
                first_chunk = selected_chunks[0]
                aggregated_result = {
                    'text': '\n\n'.join(aggregated_content),
                    'metadata': {
                        **first_chunk.get('metadata', {}),
                        'aggregated_chunks': len(selected_chunks),
                        'total_chunks_available': len(chunks)
                    }
                }
                aggregated_results.append(aggregated_result)
        
        return aggregated_results


class ConversationManager:
    """Utility class for managing conversation history."""
    
    @staticmethod
    def store_conversation_history(session_id: str, user_id: str, 
                                 query: str, response_text: str, 
                                 search_results: List[Dict[str, Any]], 
                                 source_urls: List[str]) -> None:
        """Store conversation history for both user and assistant messages."""
        from datetime import datetime
        
        if not session_id or not user_id:
            return
        
        # Add user message
        user_message = ConversationMessage(
            role="user",
            content=query,
            timestamp=datetime.utcnow(),
            search_query=query,
            source_urls=source_urls
        )
        conversation_history_service.add_message(session_id, user_message)
        
        # Add assistant message
        assistant_message = ConversationMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow(),
            search_query=query,
            search_results=search_results,
            source_urls=source_urls
        )
        conversation_history_service.add_message(session_id, assistant_message)


class ErrorHandler:
    """Utility class for handling errors consistently."""
    
    @staticmethod
    def handle_llm_error(error: Exception, query: str) -> str:
        """Handle LLM generation errors and return appropriate error message."""
        logger.error(f"Failed to generate AI response: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "I encountered an error while generating a response. Please try again or contact support if the issue persists."
    
    @staticmethod
    def create_error_response(query: str, error: str, session_id: str = None) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "response": f"I encountered an error while generating a response: {error}. Please try again or contact support if the issue persists.",
            "query": query,
            "results_count": 0,
            "sources": [],
            "session_id": session_id,
            "context_used": False,
            "error": error
        }


class InputValidator:
    """Utility class for input validation."""
    
    MAX_QUERY_LENGTH = 1000
    MAX_SEARCH_RESULTS = 50
    MAX_SESSION_ID_LENGTH = 100
    MAX_USER_ID_LENGTH = 100
    
    @staticmethod
    def validate_query(query: str) -> str:
        """Validate and sanitize query input."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        query = query.strip()
        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            raise ValueError(f"Query length exceeds maximum of {InputValidator.MAX_QUERY_LENGTH} characters")
        
        if not query:
            raise ValueError("Query cannot be empty after trimming")
        
        return query
    
    @staticmethod
    def validate_search_results(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate search results structure."""
        if not isinstance(search_results, list):
            raise ValueError("Search results must be a list")
        
        if len(search_results) > InputValidator.MAX_SEARCH_RESULTS:
            raise ValueError(f"Too many search results: {len(search_results)} > {InputValidator.MAX_SEARCH_RESULTS}")
        
        for i, result in enumerate(search_results):
            if not isinstance(result, dict):
                raise ValueError(f"Search result {i} must be a dictionary")
            
            # Validate required fields
            if 'text' not in result:
                raise ValueError(f"Search result {i} missing 'text' field")
            
            if 'metadata' not in result:
                raise ValueError(f"Search result {i} missing 'metadata' field")
        
        return search_results
    
    @staticmethod
    def validate_session_id(session_id: Optional[str]) -> Optional[str]:
        """Validate session ID format."""
        if session_id is None:
            return None
        
        if not isinstance(session_id, str):
            raise ValueError("Session ID must be a string")
        
        session_id = session_id.strip()
        if len(session_id) > InputValidator.MAX_SESSION_ID_LENGTH:
            raise ValueError(f"Session ID length exceeds maximum of {InputValidator.MAX_SESSION_ID_LENGTH} characters")
        
        if not session_id:
            raise ValueError("Session ID cannot be empty after trimming")
        
        return session_id
    
    @staticmethod
    def validate_user_id(user_id: Optional[str]) -> Optional[str]:
        """Validate user ID format."""
        if user_id is None:
            return None
        
        if not isinstance(user_id, str):
            raise ValueError("User ID must be a string")
        
        user_id = user_id.strip()
        if len(user_id) > InputValidator.MAX_USER_ID_LENGTH:
            raise ValueError(f"User ID length exceeds maximum of {InputValidator.MAX_USER_ID_LENGTH} characters")
        
        if not user_id:
            raise ValueError("User ID cannot be empty after trimming")
        
        return user_id


def format_search_results_for_llm(results: List[Dict[str, Any]]) -> str:
    """Format search results into a structured text for LLM consumption.
    
    Args:
        results: List of search result dictionaries with 'text' and 'metadata' keys
        
    Returns:
        str: Formatted text containing all search results with metadata
    """
    if not results:
        return "No relevant information found."
    
    formatted_results = []
    
    for i, result in enumerate(results, 1):
        text = result.get('text', '').strip()
        metadata = result.get('metadata', {})
        
        if not text:
            continue
            
        # Use title (document name) for display, fallback to knowledge_source, then 'Unknown source'
        title = metadata.get('title')
        source_url = metadata.get('source_url', '')
        knowledge_source = metadata.get('knowledge_source', 'Unknown source')
        
        if title:
            source_display = title
        elif knowledge_source:
            source_display = knowledge_source
        else:
            source_display = 'Unknown source'
        
        # Create formatted result with source prominently displayed, including URL if available
        if source_url:
            formatted_result = f"""
--- KNOWLEDGE SOURCE: {source_display} ---
SOURCE URL: {source_url}
Content:
{text}

"""
        else:
            formatted_result = f"""
--- KNOWLEDGE SOURCE: {source_display} ---
Content:
{text}

"""
        formatted_results.append(formatted_result)
    
    return "\n".join(formatted_results)


def generate_ai_response_sync(
    query: str,
    search_results: List[Dict[str, Any]],
    use_structured_output: bool = True
) -> str:
    """Generate an AI response to a search query using retrieved knowledge.
    
    This function uses synchronous LLM calls to avoid event loop conflicts.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        use_structured_output: Whether to use structured output format
        
    Returns:
        str: Generated AI response
    """
    # Use thread-local LLM client to avoid sharing instances across threads
    llm = get_thread_local_llm()
    
    # Log which model instance is being used
    model_id = get_current_model_id()
    endpoint = get_current_endpoint()
    logger.info(f"Generating AI response using model instance: {model_id} at {endpoint}")
    
    # Format search results for LLM consumption
    formatted_results = format_search_results_for_llm(search_results)
    
    # Debug: Log what's being passed to the LLM
    logger.info(f"Formatted results for LLM (first 500 chars): {formatted_results[:500]}")
    logger.info(f"Number of search results: {len(search_results)}")
    for i, result in enumerate(search_results[:3]):  # Log first 3 results
        metadata = result.get('metadata', {})
        logger.info(f"Result {i+1} metadata: title='{metadata.get('title', 'N/A')}', source_url='{metadata.get('source_url', 'N/A')}', knowledge_source='{metadata.get('knowledge_source', 'N/A')}'")
    
    # Count results with actual content
    content_count, total_count = ResponseProcessor.count_content_results(search_results)
    
    if content_count == 0:
        return "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your query or check if the relevant documents have been ingested."
    
    # Create the prompt
    if use_structured_output:
        # Collect all source URLs for reference
        source_urls = ResponseProcessor.extract_source_urls(search_results)
        
        source_references = "\n".join(source_urls) if source_urls else "No source URLs available"
        
        prompt = PromptManager.get_structured_prompt(query, formatted_results, content_count, total_count)
        
    else:
        prompt = PromptManager.get_simple_prompt(query, formatted_results)
    
    try:
        # Use synchronous LLM call
        response = llm.invoke(prompt)
        
        # Extract text from AIMessage - LLM response is final
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Log response generation for debugging
        logger.debug(f"Generated AI response for query: {query[:100]}...")
        logger.trace(f"AI response preview: {response_text[:200]}...")
        
        return response_text
        
    except Exception as e:
        return ErrorHandler.handle_llm_error(e, query)


async def generate_ai_response_streaming(
    query: str,
    search_results: List[Dict[str, Any]],
    use_structured_output: bool = True
) -> AsyncGenerator[str, None]:
    """Generate an AI response with streaming support.
    
    This function streams the response chunks progressively for real-time display.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        use_structured_output: Whether to use structured output format
        
    Yields:
        str: Response chunks for streaming
    """
    # Use thread-local LLM client to avoid sharing instances across threads
    llm = get_thread_local_llm()
    
    # Log which model instance is being used
    model_id = get_current_model_id()
    endpoint = get_current_endpoint()
    logger.info(f"Generating streaming AI response using model instance: {model_id} at {endpoint}")
    
    # Format search results for LLM consumption
    formatted_results = format_search_results_for_llm(search_results)
    
    # Count results with actual content
    content_count, total_count = ResponseProcessor.count_content_results(search_results)
    
    if content_count == 0:
        yield "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your query or check if the relevant documents have been ingested."
        return
    
    # Create the prompt
    if use_structured_output:
        # Collect all source URLs for reference
        source_urls = ResponseProcessor.extract_source_urls(search_results)
        
        source_references = "\n".join(source_urls) if source_urls else "No source URLs available"
        
        prompt = PromptManager.get_structured_prompt(query, formatted_results, content_count, total_count)
        
    else:
        prompt = PromptManager.get_simple_prompt(query, formatted_results)
    
    try:
        # DEBUG: Log the raw prompt sent to LLM
        logger.info("=" * 80)
        logger.info("DEBUG - RAW PROMPT SENT TO LLM:")
        logger.info("=" * 80)
        logger.info(prompt)
        logger.info("=" * 80)
        
        # Use proper async streaming LLM call
        logger.info(f"Starting async streaming LLM call for query: {query[:50]}...")
        response_stream = llm.astream(prompt)
        
        # Stream the response chunks
        chunk_count = 0
        full_response = ""
        async for chunk in response_stream:
            if hasattr(chunk, "content"):
                content = chunk.content
            else:
                content = str(chunk)
            
            if content:
                chunk_count += 1
                full_response += content
                yield content
        
        # DEBUG: Log the complete LLM response
        logger.info("=" * 80)
        logger.info("DEBUG - COMPLETE RAW LLM RESPONSE:")
        logger.info("=" * 80)
        logger.info(full_response)
        logger.info("=" * 80)
        logger.info(f"DEBUG - RESPONSE LENGTH: {len(full_response)}")
        logger.info(f"DEBUG - TOTAL CHUNKS: {chunk_count}")
        
        # Log streaming completion
        logger.info(f"Completed async streaming AI response for query: {query[:100]}... (Total chunks: {chunk_count})")
        
    except Exception as e:
        yield ErrorHandler.handle_llm_error(e, query)


async def generate_context_aware_response_streaming(
    query: str,
    search_results: List[Dict[str, Any]],
    session_id: str = None,
    user_id: str = None,
    use_structured_output: bool = True
) -> AsyncGenerator[str, None]:
    """Generate a context-aware AI response with streaming support that considers conversation history.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        session_id: Conversation session ID for context
        user_id: User ID for session management
        use_structured_output: Whether to use structured output format
        
    Yields:
        str: Response chunks for streaming
    """
    try:
        # Validate inputs
        query = InputValidator.validate_query(query)
        search_results = InputValidator.validate_search_results(search_results)
        session_id = InputValidator.validate_session_id(session_id)
        user_id = InputValidator.validate_user_id(user_id)
        
        # Get conversation context if session_id is provided
        conversation_context = ""
        if session_id:
            conversation_context = conversation_history_service.get_conversation_context(session_id)
            logger.info(f"Retrieved conversation context for session: {session_id}")
    
        # Use thread-local LLM client
        llm = get_thread_local_llm()
        
        # Log which model instance is being used
        model_id = get_current_model_id()
        endpoint = get_current_endpoint()
        logger.info(f"Generating context-aware streaming AI response using model instance: {model_id} at {endpoint}")
        
        # Format search results for LLM consumption 
        formatted_results = format_search_results_for_llm(search_results)
        
        # Count results with actual content
        content_count, total_count = ResponseProcessor.count_content_results(search_results)
        
        # Handle no results case
        if content_count == 0:
            # Create context instruction if conversation context exists
            context_instruction = ""
            if conversation_context:
                context_instruction = f"""
CONVERSATION CONTEXT:
{conversation_context}

IMPORTANT: Use the conversation history above to understand the context of this interaction. 
- If the user is asking follow-up questions, reference previous information appropriately
- If they're building on previous topics, connect the new information to what was discussed
- If they're asking for clarification, address specific points from the conversation history
- Maintain continuity and avoid repeating information already covered
"""
            
            # Generate appropriate prompt
            if use_structured_output:
                prompt = PromptManager.get_no_results_prompt(query, context_instruction)
            else:
                prompt = PromptManager.get_simple_prompt(query, "", conversation_context)
            
            try:
                # Use proper async streaming LLM call
                response_stream = llm.astream(prompt)
                
                # Stream the response chunks
                chunk_count = 0
                async for chunk in response_stream:
                    if hasattr(chunk, "content"):
                        content = chunk.content
                    else:
                        content = str(chunk)
                    
                    if content and content.strip():
                        chunk_count += 1
                        logger.debug(f"Streaming chunk {chunk_count}: {content[:50]}...")
                        yield content
                
                logger.info(f"Completed context-aware streaming for no results case: {query[:100]}... (Total chunks: {chunk_count})")
                return
                
            except Exception as e:
                yield ErrorHandler.handle_llm_error(e, query)
                return
        
        # Handle with results case
        # Create context instruction if conversation context exists
        context_instruction = ""
        if conversation_context:
            context_instruction = f"""
CONVERSATION CONTEXT:
{conversation_context}

IMPORTANT: Use the conversation history above to understand the context of this interaction. 
- If the user is asking follow-up questions, reference previous information appropriately
- If they're building on previous topics, connect the new information to what was discussed
- If they're asking for clarification, address specific points from the conversation history
- Maintain continuity and avoid repeating information already covered
"""
        
        # Create the prompt
        if use_structured_output:
            prompt = PromptManager.get_context_aware_structured_prompt(query, formatted_results, content_count, total_count, conversation_context)
        else:
            prompt = PromptManager.get_simple_prompt(query, formatted_results, conversation_context)
        
        try:
            # DEBUG: Log the raw prompt sent to LLM
            logger.info("=" * 80)
            logger.info("DEBUG - RAW CONTEXT-AWARE PROMPT SENT TO LLM:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            
            # Use proper async streaming LLM call
            logger.info(f"Starting context-aware async streaming LLM call for query: {query[:50]}...")
            response_stream = llm.astream(prompt)
            
            # Stream the response chunks
            chunk_count = 0
            full_response = ""
            async for chunk in response_stream:
                if hasattr(chunk, "content"):
                    content = chunk.content
                else:
                    content = str(chunk)
                
                if content and content.strip():
                    chunk_count += 1
                    full_response += content
                    yield content
            
            # DEBUG: Log the complete LLM response
            logger.info("=" * 80)
            logger.info("DEBUG - COMPLETE RAW CONTEXT-AWARE LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(full_response)
            logger.info("=" * 80)
            logger.info(f"DEBUG - RESPONSE LENGTH: {len(full_response)}")
            logger.info(f"DEBUG - TOTAL CHUNKS: {chunk_count}")
            
            # Log streaming completion
            logger.info(f"Completed context-aware async streaming AI response for query: {query[:100]}... (Total chunks: {chunk_count})")
            
        except Exception as e:
            yield ErrorHandler.handle_llm_error(e, query)
        
    except ValueError as e:
        logger.error(f"Input validation error in generate_context_aware_response_streaming: {e}")
        yield f"Error: Invalid input - {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in generate_context_aware_response_streaming: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        yield "An unexpected error occurred while generating the response."


def generate_ai_response_with_metadata(
    query: str,
    search_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate an AI response with additional metadata about the response generation.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        
    Returns:
        Dict containing the response and metadata
    """
    try:
        # Generate the response
        response = generate_ai_response_sync(query, search_results)
        
        # Calculate metadata
        content_count, total_count = ResponseProcessor.count_content_results(search_results)
        
        # Extract unique sources
        sources = set()
        for result in search_results:
            metadata = result.get('metadata', {})
            source = metadata.get('source_url') or metadata.get('knowledge_source')
            if source:
                sources.add(source)
        
        # Extract entities and tags from results
        all_entities = []
        all_tags = []
        for result in search_results:
            metadata = result.get('metadata', {})
            graph_data = metadata.get('graph_data', {})
            
            # Collect entities
            entities = graph_data.get('entities', [])
            for entity in entities:
                if isinstance(entity, dict) and 'name' in entity:
                    all_entities.append(entity['name'])
            
            # Collect tags
            tags = graph_data.get('tags', [])
            all_tags.extend(tags)
        
        # Remove duplicates
        unique_entities = list(set(all_entities))[:10]  # Limit to top 10
        unique_tags = list(set(all_tags))[:10]  # Limit to top 10
        
        metadata = {
            "query": query,
            "response": response,
            "search_metadata": {
                "total_results": total_count,
                "results_with_content": content_count,
                "unique_sources": len(sources),
                "sources": list(sources)[:5],  # Limit to top 5 sources
                "entities_found": unique_entities,
                "tags_found": unique_tags,
                "model_used": get_current_model_id(),
                "endpoint_used": get_current_endpoint()
            }
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to generate AI response with metadata: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "query": query,
            "response": f"I encountered an error while generating a response: {str(e)}. Please try again or contact support if the issue persists.",
            "search_metadata": {
                "error": str(e),
                "model_used": get_current_model_id(),
                "endpoint_used": get_current_endpoint()
            }
        }


async def generate_ai_response_async(
    query: str,
    search_results: List[Dict[str, Any]],
    use_structured_output: bool = True
) -> str:
    """Async version of generate_ai_response_sync for proper async contexts.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        use_structured_output: Whether to use structured output format
        
    Returns:
        str: Generated AI response
    """
    try:
        # Validate inputs
        query = InputValidator.validate_query(query)
        search_results = InputValidator.validate_search_results(search_results)
        
        # Use thread-local LLM client
        llm = get_thread_local_llm()
        
        # Log which model instance is being used
        model_id = get_current_model_id()
        endpoint = get_current_endpoint()
        logger.info(f"Generating async AI response using model instance: {model_id} at {endpoint}")
        
        # Format search results for LLM consumption
        formatted_results = format_search_results_for_llm(search_results)
        
        # Count results with actual content
        content_count, total_count = ResponseProcessor.count_content_results(search_results)
        
        if content_count == 0:
            return "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your query or check if the relevant documents have been ingested."
        
        # Generate appropriate prompt
        if use_structured_output:
            prompt = PromptManager.get_structured_prompt(query, formatted_results, content_count, total_count)
        else:
            prompt = PromptManager.get_simple_prompt(query, formatted_results)
        
        # Use proper async LLM call
        response = await llm.ainvoke(prompt)
        
        # Extract text from AIMessage - LLM response is final
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Log response generation for debugging
        logger.debug(f"Generated async AI response for query: {query[:100]}...")
        logger.trace(f"AI response preview: {response_text[:200]}...")
        
        return response_text
        
    except ValueError as e:
        logger.error(f"Input validation error in generate_ai_response_async: {e}")
        return f"Invalid input: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in generate_ai_response_async: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "An unexpected error occurred while generating the response"


async def generate_ai_response_with_metadata_async(
    query: str,
    search_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Async version of generate_ai_response_with_metadata for proper async contexts.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        
    Returns:
        Dict containing the response and metadata
    """
    try:
        # Generate the response using async version
        response = await generate_ai_response_async(query, search_results)
        
        # Calculate metadata
        content_count, total_count = ResponseProcessor.count_content_results(search_results)
        
        # Extract unique sources
        sources = set()
        for result in search_results:
            metadata = result.get('metadata', {})
            source = metadata.get('source_url') or metadata.get('knowledge_source')
            if source:
                sources.add(source)
        
        # Extract entities and tags from results
        all_entities = []
        all_tags = []
        for result in search_results:
            metadata = result.get('metadata', {})
            graph_data = metadata.get('graph_data', {})
            
            # Collect entities
            entities = graph_data.get('entities', [])
            for entity in entities:
                if isinstance(entity, dict) and 'name' in entity:
                    all_entities.append(entity['name'])
            
            # Collect tags
            tags = graph_data.get('tags', [])
            all_tags.extend(tags)
        
        # Remove duplicates
        unique_entities = list(set(all_entities))[:10]  # Limit to top 10
        unique_tags = list(set(all_tags))[:10]  # Limit to top 10
        
        metadata = {
            "query": query,
            "response": response,
            "search_metadata": {
                "total_results": total_count,
                "results_with_content": content_count,
                "unique_sources": len(sources),
                "sources": list(sources)[:5],  # Limit to top 5 sources
                "entities_found": unique_entities,
                "tags_found": unique_tags,
                "model_used": get_current_model_id(),
                "endpoint_used": get_current_endpoint()
            }
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to generate AI response with metadata: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "query": query,
            "response": f"I encountered an error while generating a response: {str(e)}. Please try again or contact support if the issue persists.",
            "search_metadata": {
                "error": str(e),
                "model_used": get_current_model_id(),
                "endpoint_used": get_current_endpoint()
            }
        }


async def generate_context_aware_response(
    query: str,
    search_results: List[Dict[str, Any]],
    session_id: str = None,
    user_id: str = None,
    use_structured_output: bool = True
) -> Dict[str, Any]:
    """Generate a context-aware AI response that considers conversation history.
    
    Args:
        query: The user's search query
        search_results: List of search results from the knowledge base
        session_id: Conversation session ID for context
        user_id: User ID for session management
        use_structured_output: Whether to use structured output format
        
    Returns:
        Dict containing response text, metadata, and session info
    """
    try:
        # Validate inputs
        query = InputValidator.validate_query(query)
        search_results = InputValidator.validate_search_results(search_results)
        session_id = InputValidator.validate_session_id(session_id)
        user_id = InputValidator.validate_user_id(user_id)
        
        # Get conversation context if session_id is provided
        conversation_context = ""
        if session_id:
            conversation_context = conversation_history_service.get_conversation_context(session_id)
    
        # Use thread-local LLM client
        llm = get_thread_local_llm()
        
        # Log which model instance is being used
        model_id = get_current_model_id()
        endpoint = get_current_endpoint()
        logger.info(f"Generating context-aware AI response using model instance: {model_id} at {endpoint}")
        
        # Format search results for LLM consumption 
        formatted_results = format_search_results_for_llm(search_results)
        
        # Count results with actual content
        content_count, total_count = ResponseProcessor.count_content_results(search_results)
        
        # Handle no results case
        if content_count == 0:
            return await _handle_no_results_case(
                query, conversation_context, use_structured_output, 
                session_id, user_id, search_results
            )
        
        # Handle with results case
        return await _handle_with_results_case(
            query, search_results, formatted_results, content_count, total_count,
            conversation_context, use_structured_output, session_id, user_id
        )
        
    except ValueError as e:
        logger.error(f"Input validation error in generate_context_aware_response: {e}")
        return ErrorHandler.create_error_response(query, f"Invalid input: {str(e)}", session_id)
    except Exception as e:
        logger.error(f"Unexpected error in generate_context_aware_response: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ErrorHandler.create_error_response(query, "An unexpected error occurred", session_id)


async def _handle_no_results_case(
    query: str, 
    conversation_context: str, 
    use_structured_output: bool,
    session_id: str, 
    user_id: str, 
    search_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle the case when no search results are found."""
    # Create context instruction if conversation context exists
    context_instruction = ""
    if conversation_context:
        context_instruction = f"""
CONVERSATION CONTEXT:
{conversation_context}

IMPORTANT: Use the conversation history above to understand the context of this interaction. 
- If the user is asking follow-up questions, reference previous information appropriately
- If they're building on previous topics, connect the new information to what was discussed
- If they're asking for clarification, address specific points from the conversation history
- Maintain continuity and avoid repeating information already covered
"""
    
    # Generate appropriate prompt
    if use_structured_output:
        prompt = PromptManager.get_no_results_prompt(query, context_instruction)
    else:
        prompt = PromptManager.get_simple_prompt(query, "", conversation_context)
    
    try:
        # Use proper async LLM call
        llm = get_thread_local_llm()
        response = await llm.ainvoke(prompt)
        
        # Extract text from AIMessage - LLM response is final
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
    except Exception as e:
        response_text = "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your query or check if the relevant documents have been ingested."
    
    # Store conversation history
    if session_id and user_id:
        source_urls = ResponseProcessor.extract_source_urls(search_results)
        ConversationManager.store_conversation_history(session_id, user_id, query, response_text, search_results, source_urls)
    
    return {
        "response": response_text,
        "query": query,
        "results_count": 0,
        "sources": [],
        "session_id": session_id,
        "context_used": bool(conversation_context)
    }


async def _handle_with_results_case(
    query: str,
    search_results: List[Dict[str, Any]],
    formatted_results: str,
    content_count: int,
    total_count: int,
    conversation_context: str,
    use_structured_output: bool,
    session_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Handle the case when search results are found."""
    
    logger.info(f"Starting context-aware AI response with results case")
    # Extract source URLs
    source_urls = ResponseProcessor.extract_source_urls(search_results)
    
    # Create context instruction if conversation context exists
    context_instruction = ""
    if conversation_context:
        context_instruction = f"""
CONVERSATION CONTEXT:
{conversation_context}

IMPORTANT: Use the conversation history above to understand the context of this interaction. 
- If the user is asking follow-up questions, reference previous information appropriately
- If they're building on previous topics, connect the new information to what was discussed
- If they're asking for clarification, address specific points from the conversation history
- Maintain continuity and avoid repeating information already covered
"""
    
    # Generate appropriate prompt
    if use_structured_output:
        prompt = PromptManager.get_context_aware_structured_prompt(query, formatted_results, content_count, total_count, conversation_context)
        logger.info(f"Using structured output prompt: {prompt}")
    else:
        prompt = PromptManager.get_simple_prompt(query, formatted_results, conversation_context)
        logger.info(f"Using simple output prompt: {prompt}")
    try:
        # Use proper async LLM call
        llm = get_thread_local_llm()
        response = await llm.ainvoke(prompt)
        
        # Extract text from AIMessage - LLM response is final
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Store conversation history
        if session_id and user_id:
            ConversationManager.store_conversation_history(session_id, user_id, query, response_text, search_results, source_urls)
        
        # Log response generation for debugging
        logger.debug(f"Generated context-aware AI response for query: {query[:100]}...")
        logger.trace(f"AI response preview: {response_text[:200]}...")
        
        return {
            "response": response_text,
            "query": query,
            "results_count": content_count,
            "sources": source_urls,
            "session_id": session_id,
            "context_used": bool(conversation_context)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate context-aware AI response: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_response = ErrorHandler.handle_llm_error(e, query)
        
        # Store conversation history if session_id is provided (even for errors)
        if session_id and user_id:
            ConversationManager.store_conversation_history(session_id, user_id, query, error_response, [], [])
        
        return ErrorHandler.create_error_response(query, str(e), session_id) 