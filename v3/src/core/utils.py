"""
Shared utilities for the agent system.
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_llm_json(response: str, fallback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Parse JSON from an LLM response, handling markdown code fences and surrounding text.
    """
    cleaned = response.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        last_fence = cleaned.rfind("```")
        if last_fence != -1:
            cleaned = cleaned[:last_fence]
        cleaned = cleaned.strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    import re
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse LLM response as JSON, using fallback")
    result = dict(fallback) if fallback else {}
    result["raw_response"] = response
    return result
