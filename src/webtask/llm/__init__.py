"""LLM module - LLM base class, message types, and content types."""

from .llm import LLM
from .content import Text, Image, Content, ImageType
from .message import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ImageMimeType,
    ToolCall,
    ToolResult,
)

__all__ = [
    # Old interface (backward compatibility)
    "LLM",
    "Text",
    "Image",
    "Content",
    "ImageType",
    # New message-based interface
    "Message",
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "ToolResultMessage",
    "TextContent",
    "ImageContent",
    "ImageMimeType",
    "ToolCall",
    "ToolResult",
]
