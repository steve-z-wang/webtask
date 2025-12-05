"""LLM context debugger for saving LLM calls to disk."""

import json
import shutil
from pathlib import Path
from typing import List, TYPE_CHECKING
from ..config import Config

if TYPE_CHECKING:
    from webtask.llm import Message


class LLMContextDebugger:
    """Saves LLM calls (request + response) to disk with shared counter across all instances."""

    # Class-level state shared across all debugger instances
    _call_counter = 0
    _cleaned = False

    def __init__(self):
        """Initialize debugger (uses shared class-level counter)."""
        pass

    def save_call(
        self,
        messages: List["Message"],
        response: "Message",
    ) -> None:
        """Save LLM call (request + response) to a single JSON file."""
        if not Config().is_debug_enabled():
            return

        debug_dir = Path(Config().get_debug_dir())

        # Clean up debug directory on first call (shared across all instances)
        if not LLMContextDebugger._cleaned:
            if debug_dir.exists():
                shutil.rmtree(debug_dir)
            LLMContextDebugger._cleaned = True

        # Increment shared counter
        LLMContextDebugger._call_counter += 1

        debug_dir.mkdir(parents=True, exist_ok=True)

        # Save complete call in one file
        call_path = debug_dir / f"llm_call_{LLMContextDebugger._call_counter}.json"
        with open(call_path, "w") as f:
            json.dump(
                {
                    "call_number": LLMContextDebugger._call_counter,
                    "request": [_message_to_dict(msg) for msg in messages],
                    "response": _message_to_dict(response),
                },
                f,
                indent=2,
                default=str,
            )


def _message_to_dict(message: "Message") -> dict:
    """Convert message to JSON-serializable dict."""
    from webtask.llm import Text, Image, ToolCall, ToolResult

    result = {
        "role": message.role.value,
        "timestamp": message.timestamp.isoformat(),
    }

    # Add content if present
    if message.content:
        result["content"] = []
        for content in message.content:
            if isinstance(content, Text):
                result["content"].append(
                    {
                        "type": "text",
                        "text": content.text,
                    }
                )
            elif isinstance(content, Image):
                # Don't save full base64 image data, just metadata
                result["content"].append(
                    {
                        "type": "image",
                        "mime_type": content.mime_type.value,
                        "size": len(content.data),
                    }
                )
            elif isinstance(content, ToolCall):
                result["content"].append(
                    {
                        "type": "tool_call",
                        "id": content.id,
                        "name": content.name,
                        "arguments": content.arguments,
                    }
                )
            elif isinstance(content, ToolResult):
                result["content"].append(
                    {
                        "type": "tool_result",
                        "tool_call_id": content.tool_call_id,
                        "name": content.name,
                        "status": content.status.value,
                        "error": content.error,
                    }
                )

    return result
