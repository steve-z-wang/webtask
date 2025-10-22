"""JSON parsing utilities."""

import json
from typing import Dict, Any


def parse_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON text with descriptive error handling.

    Args:
        text: JSON string to parse

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
