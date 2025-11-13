"""Message types for conversational LLM history with tool calling support."""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ImageMimeType(str, Enum):
    """Supported image MIME types."""

    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    GIF = "image/gif"


class TextContent(BaseModel):
    """Text content part."""

    text: str


class ImageContent(BaseModel):
    """Image content part (base64-encoded)."""

    data: str  # base64-encoded
    mime_type: ImageMimeType = ImageMimeType.PNG


class ToolCall(BaseModel):
    """Tool call from LLM."""

    id: Optional[str] = None  # OpenAI/Anthropic provide ID, Gemini doesn't
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Acknowledgment of tool execution."""

    tool_call_id: Optional[str] = None  # Match by ID if available (OpenAI/Anthropic)
    name: str  # Tool name
    status: str  # "success" or "error"
    error: Optional[str] = None  # Error message if status is "error"


class Message(BaseModel):
    """Base message with automatic timestamp."""

    timestamp: datetime = Field(default_factory=datetime.now)


class SystemMessage(Message):
    """System instruction message."""

    content: List[TextContent]


class UserMessage(Message):
    """User message with text/images."""

    content: List[Union[TextContent, ImageContent]]


class AssistantMessage(Message):
    """Assistant response with optional tool calls."""

    content: Optional[List[Union[TextContent, ImageContent]]] = None
    tool_calls: Optional[List[ToolCall]] = None


class ToolResultMessage(Message):
    """Tool execution results with page state."""

    results: List[ToolResult]  # Acknowledgment for each tool call
    content: List[Union[TextContent, ImageContent]]  # Page state after all tools execute


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
