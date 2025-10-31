"""JSON parsing utilities."""

import json
from typing import Dict, Any


def parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON text, handling markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:500] if text else "(empty string)"
        raise ValueError(f"Failed to parse JSON: {e}\n" f"Text preview: {preview}")
