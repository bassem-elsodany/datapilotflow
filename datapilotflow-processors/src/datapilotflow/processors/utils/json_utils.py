"""
JSON utilities module for parsing and repairing LLM responses.
"""

import json
import re
from typing import Dict, Any
from loguru import logger


def repair_json_response(response_text: str) -> str:
    """Repair common JSON syntax errors in LLM responses.
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        str: Repaired JSON string
    """
    # Remove any leading/trailing text that's not JSON
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    if json_start == -1 or json_end == 0:
        logger.warning(f"No JSON object found in response: {response_text[:100]}...")
        return response_text
    
    json_text = response_text[json_start:json_end]
    
    # Common LLM JSON errors and their fixes
    repairs = [
        # Fix missing quotes around property names (like "a name" -> "name")
        (r'{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'{"\1":'),
        # Fix missing quotes around property names with spaces
        (r'{\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*:', r'{"\1":'),
        # Fix specific case like "{ a name": -> {"name":
        (r'{\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*"', r'{"\1"'),
        # Fix the exact error case: { a name": -> {"name":
        (r'{\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*"([^"]*?)"', r'{"\1": "\2"'),
        # Fix trailing commas in arrays and objects
        (r',(\s*[}\]])', r'\1'),
        # Fix missing quotes around string values
        (r':\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*([,}])', r': "\1"\2'),
        # Fix extra spaces in property names
        (r'"\s*([^"]*?)\s*"', r'"\1"'),
        # Fix double quotes in property names
        (r'""([^"]*?)""', r'"\1"'),
        # Fix unquoted string values in arrays
        (r'\[\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*([,\]])', r'["\1"\2'),
        # Fix unquoted string values at end of arrays
        (r'\[\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*\]', r'["\1"]'),
        # Fix missing quotes around entity names and types
        (r'{\s*name:\s*([^,}]+)', r'{"name": "\1"'),
        (r'{\s*type:\s*([^,}]+)', r'{"type": "\1"'),
        # Fix missing quotes around relationship fields
        (r'source:\s*([^,}]+)', r'"source": "\1"'),
        (r'target:\s*([^,}]+)', r'"target": "\1"'),
        (r'relation:\s*([^,}]+)', r'"relation": "\1"'),
    ]
    
    for pattern, replacement in repairs:
        json_text = re.sub(pattern, replacement, json_text)
    
    logger.trace(f"Repaired JSON: {json_text[:200]}...")
    return json_text


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response with error handling and JSON repair.
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Dict[str, Any]: Parsed JSON response
    """
    # Clean the response - remove think tags and their content
    cleaned_response = response_text.strip()
    
    # Remove all <think>...</think> tags and their content
    cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL)
    
    # Remove any remaining think-related content
    cleaned_response = re.sub(r'<think>.*', '', cleaned_response, flags=re.DOTALL)
    cleaned_response = re.sub(r'</think>.*', '', cleaned_response, flags=re.DOTALL)
    
    # Remove any other common LLM artifacts
    cleaned_response = re.sub(r'<no_think>.*?</no_think>', '', cleaned_response, flags=re.DOTALL)
    cleaned_response = re.sub(r'/no_think', '', cleaned_response)
    
    cleaned_response = cleaned_response.strip()
    
    try:
        # First try to parse as-is
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parsing failed: {e}")
        logger.trace(f"Response text: {cleaned_response[:300]}...")
        
        # Try to repair common JSON errors
        repaired_json = repair_json_response(cleaned_response)
        logger.trace(f"Attempting to repair JSON: {repaired_json[:200]}...")
        
        try:
            return json.loads(repaired_json)
        except json.JSONDecodeError as e2:
            logger.debug(f"Repaired JSON parsing also failed: {e2}")
            
            # Try to extract JSON using regex as last resort
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                try:
                    extracted_json = json_match.group(0)
                    logger.trace(f"Extracted JSON with regex: {extracted_json[:200]}...")
                    return json.loads(extracted_json)
                except json.JSONDecodeError as e3:
                    logger.debug(f"Regex extracted JSON parsing failed: {e3}")
            
            # If all parsing attempts fail, raise the original error
            logger.error(f"All JSON parsing attempts failed. Original error: {e}")
            raise e 