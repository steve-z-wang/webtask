"""JSON parsing utilities."""

import json
from typing import Dict, Any


def parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON text, handling markdown code fences and common malformations."""
    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Handle missing opening brace (LLM sometimes starts with "message": instead of {"message":)
    if text.startswith('"') and not text.startswith("{"):
        text = "{" + text

    # Handle missing closing brace
    if text.endswith("}") is False and text.count("{") > text.count("}"):
        text = text + "}"

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:500] if text else "(empty string)"
        raise ValueError(f"Failed to parse JSON: {e}\n" f"Text preview: {preview}")
