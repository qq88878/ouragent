"""
Shared utilities for the agent system.
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_llm_json(response: str, fallback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Parse JSON from an LLM response, handling markdown code fences.

    Strips ```json ... ``` or ``` ... ``` wrappers, parses the JSON,
    and on failure returns a fallback dict merged with the raw response.

    Args:
        response: Raw LLM response string
        fallback: Base dict to return on parse failure (raw_response will be merged in)

    Returns:
        Parsed JSON dict, or fallback + {"raw_response": response} on failure

    Examples:
        >>> parse_llm_json('{"key": "value"}')
        {"key": "value"}
        >>> parse_llm_json('```json\\n{"key": "value"}\\n```')
        {"key": "value"}
        >>> parse_llm_json('not json', fallback={"default": True})
        {"default": True, "raw_response": "not json"}
    """
    cleaned = response.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        last_fence = cleaned.rfind("```")
        if last_fence != -1:
            cleaned = cleaned[:last_fence]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON, using fallback")
        result = dict(fallback) if fallback else {}
        result["raw_response"] = response
        return result
