"""Message types for conversational LLM history with tool calling support."""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ImageMimeType(str, Enum):
    """Supported image MIME types."""

    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    GIF = "image/gif"


class ToolResultStatus(str, Enum):
    """Tool execution result status."""

    SUCCESS = "success"
    ERROR = "error"


class Content(BaseModel):
    """Base class for message content parts."""

    tag: Optional[str] = (
        None  # Tag for processing/filtering (e.g., "observation", "dom", "screenshot")
    )


class TextContent(Content):
    """Text content part."""

    text: str

    def __str__(self) -> str:
        # Truncate long text
        if len(self.text) > 100:
            return f"TextContent({self.text[:100]}...)"
        return f"TextContent({self.text})"


class ImageContent(Content):
    """Image content part (base64-encoded)."""

    data: str  # base64-encoded
    mime_type: ImageMimeType = ImageMimeType.PNG

    def __str__(self) -> str:
        return f"ImageContent(mime_type={self.mime_type.value}, size={len(self.data)} bytes)"


class ToolCall(BaseModel):
    """Tool call from LLM."""

    id: Optional[str] = None  # OpenAI/Anthropic provide ID, Gemini doesn't
    name: str
    arguments: Dict[str, Any]

    def __str__(self) -> str:
        args_str = ", ".join(f"{k}={v}" for k, v in self.arguments.items())
        if len(args_str) > 100:
            args_str = args_str[:100] + "..."
        return f"ToolCall({self.name}, {args_str})"


class ToolResult(BaseModel):
    """Acknowledgment of tool execution."""

    tool_call_id: Optional[str] = None  # Match by ID if available (OpenAI/Anthropic)
    name: str  # Tool name
    status: ToolResultStatus  # Execution status
    error: Optional[str] = None  # Error message if status is ERROR

    def __str__(self) -> str:
        parts = [f"{self.name}: {self.status.value}"]
        if self.error:
            parts.append(f"error={self.error}")
        return f"ToolResult({', '.join(parts)})"


class Message(BaseModel):
    """Base message with automatic timestamp."""

    timestamp: datetime = Field(default_factory=datetime.now)
    content: Optional[List[Content]] = None


class SystemMessage(Message):
    """System instruction message."""

    def __str__(self) -> str:
        texts = [part.text for part in self.content]
        combined = " ".join(texts)
        if len(combined) > 200:
            combined = combined[:200] + "..."
        return f"SystemMessage({combined})"


class UserMessage(Message):
    """User message with text/images."""

    def __str__(self) -> str:
        text_parts = [
            part.text for part in self.content if isinstance(part, TextContent)
        ]
        image_count = sum(1 for part in self.content if isinstance(part, ImageContent))

        text_str = " ".join(text_parts)
        if len(text_str) > 200:
            text_str = text_str[:200] + "..."

        if image_count > 0:
            return f"UserMessage(text={text_str}, images={image_count})"
        return f"UserMessage({text_str})"


class AssistantMessage(Message):
    """Assistant response with optional tool calls."""

    tool_calls: Optional[List[ToolCall]] = None

    def __str__(self) -> str:
        parts = []

        # Add content summary
        if self.content:
            text_parts = [
                part.text for part in self.content if isinstance(part, TextContent)
            ]
            image_count = sum(
                1 for part in self.content if isinstance(part, ImageContent)
            )

            if text_parts:
                text_str = " ".join(text_parts)
                if len(text_str) > 100:
                    text_str = text_str[:100] + "..."
                parts.append(f"text={text_str}")

            if image_count > 0:
                parts.append(f"images={image_count}")

        # Add tool calls summary
        if self.tool_calls:
            tool_names = [tc.name for tc in self.tool_calls]
            parts.append(f"tools=[{', '.join(tool_names)}]")

        if parts:
            return f"AssistantMessage({', '.join(parts)})"
        return "AssistantMessage(empty)"


class ToolResultMessage(Message):
    """Tool execution results with observation content."""

    results: List[ToolResult]  # Acknowledgment for each tool call

    def __str__(self) -> str:
        # Summary of results
        result_summary = [f"{r.name}:{r.status}" for r in self.results]
        results_str = ", ".join(result_summary)

        # Count content types
        text_count = sum(1 for part in self.content if isinstance(part, TextContent))
        image_count = sum(1 for part in self.content if isinstance(part, ImageContent))

        return f"ToolResultMessage(results=[{results_str}], text_parts={text_count}, images={image_count})"


# ========== Helper Functions ==========


def get_message_role(message: Message) -> str:
    """Convert message type to role string for LLM APIs.

    Args:
        message: Message instance

    Returns:
        Role string: "system", "user", or "assistant"

    Raises:
        ValueError: If message type is unknown
    """
    if isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, UserMessage):
        return "user"
    elif isinstance(message, AssistantMessage):
        return "assistant"
    elif isinstance(message, ToolResultMessage):
        return "user"  # Tool results come back as user messages
    else:
        raise ValueError(f"Unknown message type: {type(message)}")
