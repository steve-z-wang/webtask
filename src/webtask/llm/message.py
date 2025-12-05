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


class Role(str, Enum):
    """Message role."""

    SYSTEM = "system"
    USER = "user"
    MODEL = "model"
    TOOL = "tool"


class Content(BaseModel):
    """Base class for message content."""

    pass


class Text(Content):
    """Text content."""

    text: str

    def __str__(self) -> str:
        if len(self.text) > 100:
            return f"Text({self.text[:100]}...)"
        return f"Text({self.text})"


class Image(Content):
    """Image content (base64-encoded)."""

    data: str  # base64-encoded
    mime_type: ImageMimeType = ImageMimeType.PNG

    def __str__(self) -> str:
        return f"Image(mime_type={self.mime_type.value}, size={len(self.data)} bytes)"


class ToolCall(Content):
    """Tool call from LLM."""

    id: Optional[str] = None  # OpenAI/Anthropic provide ID, Gemini doesn't
    name: str
    arguments: Dict[str, Any]

    def __str__(self) -> str:
        args_str = ", ".join(f"{k}={v}" for k, v in self.arguments.items())
        if len(args_str) > 100:
            args_str = args_str[:100] + "..."
        return f"ToolCall({self.name}, {args_str})"


class ToolResult(Content):
    """Result of tool execution."""

    tool_call_id: Optional[str] = None  # Match by ID if available (OpenAI/Anthropic)
    name: str  # Tool name
    status: ToolResultStatus  # Execution status
    error: Optional[str] = None  # Error message if status is ERROR
    description: str = ""  # Human-readable description of action taken
    terminal: bool = False  # If True, task should stop after this tool

    def __str__(self) -> str:
        parts = [f"{self.name}: {self.status.value}"]
        if self.error:
            parts.append(f"error={self.error}")
        if self.terminal:
            parts.append("terminal")
        return f"ToolResult({', '.join(parts)})"


class Message(BaseModel):
    """Message with role and content."""

    role: Role
    content: Optional[List[Content]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def text(self) -> Optional[str]:
        """Get first text content from message."""
        if self.content:
            for c in self.content:
                if isinstance(c, Text):
                    return c.text
        return None

    @property
    def tool_calls(self) -> List[ToolCall]:
        """Get all tool calls from message content."""
        if not self.content:
            return []
        return [c for c in self.content if isinstance(c, ToolCall)]

    @property
    def tool_results(self) -> List[ToolResult]:
        """Get all tool results from message content."""
        if not self.content:
            return []
        return [c for c in self.content if isinstance(c, ToolResult)]

    def __str__(self) -> str:
        if not self.content:
            return f"Message({self.role.value}, empty)"

        parts = []
        text_parts = [c.text for c in self.content if isinstance(c, Text)]
        image_count = sum(1 for c in self.content if isinstance(c, Image))
        tool_calls = [c for c in self.content if isinstance(c, ToolCall)]
        tool_results = [c for c in self.content if isinstance(c, ToolResult)]

        if text_parts:
            text_str = " ".join(text_parts)
            if len(text_str) > 100:
                text_str = text_str[:100] + "..."
            parts.append(f"text={text_str}")

        if image_count > 0:
            parts.append(f"images={image_count}")

        if tool_calls:
            tool_names = [tc.name for tc in tool_calls]
            parts.append(f"tool_calls=[{', '.join(tool_names)}]")

        if tool_results:
            result_summary = [f"{r.name}:{r.status.value}" for r in tool_results]
            parts.append(f"tool_results=[{', '.join(result_summary)}]")

        return f"Message({self.role.value}, {', '.join(parts)})"
