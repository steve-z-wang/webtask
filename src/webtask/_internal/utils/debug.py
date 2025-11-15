"""Debug utilities for saving LLM calls to disk."""

import json
from pathlib import Path
from typing import List, TYPE_CHECKING
from ..config import Config

if TYPE_CHECKING:
    from webtask.llm import Message


class LLMDebugger:
    """Saves LLM calls (request + response) to disk with internal counter."""

    def __init__(self):
        """Initialize debugger with counter at 0."""
        self._call_counter = 0

    def save_call(
        self,
        messages: List["Message"],
        response: "Message",
    ) -> None:
        """Save LLM call (request + response) to a single JSON file.

        Args:
            messages: Messages sent to LLM
            response: LLM response

        Files saved:
            - {debug_dir}/llm_call_{counter}.json: Complete call with request and response
        """
        if not Config().is_debug_enabled():
            return

        # Increment counter
        self._call_counter += 1

        debug_dir = Path(Config().get_debug_dir())
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Save complete call in one file
        call_path = debug_dir / f"llm_call_{self._call_counter}.json"
        with open(call_path, "w") as f:
            json.dump(
                {
                    "call_number": self._call_counter,
                    "request": [_message_to_dict(msg) for msg in messages],
                    "response": _message_to_dict(response),
                },
                f,
                indent=2,
                default=str,
            )


def _message_to_dict(message: "Message") -> dict:
    """Convert message to JSON-serializable dict.

    Args:
        message: Message to convert

    Returns:
        Dictionary representation of message
    """
    from webtask.llm import (
        AssistantMessage,
        ToolResultMessage,
        TextContent,
        ImageContent,
    )

    result = {
        "type": message.__class__.__name__,
        "timestamp": message.timestamp.isoformat(),
    }

    # Add content if present
    if message.content:
        result["content"] = []
        for content in message.content:
            if isinstance(content, TextContent):
                result["content"].append(
                    {
                        "type": "text",
                        "text": content.text,
                        "tag": content.tag,
                    }
                )
            elif isinstance(content, ImageContent):
                # Don't save full base64 image data, just metadata
                result["content"].append(
                    {
                        "type": "image",
                        "mime_type": content.mime_type.value,
                        "size": len(content.data),
                        "tag": content.tag,
                    }
                )

    # Add tool calls if present (AssistantMessage)
    if isinstance(message, AssistantMessage) and message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "name": tc.name,
                "arguments": tc.arguments,
            }
            for tc in message.tool_calls
        ]

    # Add tool results if present (ToolResultMessage)
    if isinstance(message, ToolResultMessage):
        result["results"] = [
            {
                "tool_call_id": tr.tool_call_id,
                "name": tr.name,
                "status": tr.status.value,
                "error": tr.error,
            }
            for tr in message.results
        ]

    return result
