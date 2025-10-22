"""JSON parsing utilities."""

import json
from typing import Dict, Any


def parse_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON text with descriptive error handling.

    Automatically handles markdown code fences (```json ... ```).

    Args:
        text: JSON string to parse (may be wrapped in markdown)

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If JSON parsing fails (includes preview of text)
    """
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Show first 500 chars of what failed to parse
        preview = text[:500] if text else "(empty string)"
        raise ValueError(
            f"Failed to parse JSON: {e}\n"
            f"Text preview: {preview}"
        )
