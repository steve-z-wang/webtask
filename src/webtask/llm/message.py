"""Message types for conversational LLM history with tool calling support."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, model_validator


# ========== Content Types ==========

class TextContent(BaseModel):
    text: str


class ImageContent(BaseModel):
    data: str  # base64-encoded
    mime_type: str = "image/png"


# ========== Tool Types ==========

class ToolCall(BaseModel):
    """Tool call from LLM"""
    id: Optional[str] = None  # OpenAI/Anthropic provide ID, Gemini doesn't
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result from tool execution"""
    tool_call_id: Optional[str] = None  # Match by ID if available
    name: Optional[str] = None  # Match by name if no ID (Gemini)
    content: List[Union[TextContent, ImageContent]]
    metadata: Optional[Dict[str, Any]] = None


# ========== Message Types ==========

class SystemMessage(BaseModel):
    content: List[Union[TextContent, ImageContent]]


class UserMessage(BaseModel):
    content: List[Union[TextContent, ImageContent]]


class AssistantMessage(BaseModel):
    content: Optional[List[Union[TextContent, ImageContent]]] = None
    tool_calls: Optional[List[ToolCall]] = None

    @model_validator(mode='after')
    def check_at_least_one(self):
        if not self.content and not self.tool_calls:
            raise ValueError("AssistantMessage must have content or tool_calls")
        return self


class ToolResultMessage(BaseModel):
    results: List[ToolResult]


Message = Union[SystemMessage, UserMessage, AssistantMessage, ToolResultMessage]


# ========== Helper Functions ==========

def get_message_role(message: Message) -> str:
    """Convert message type to role string for LLM APIs"""
    if isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, UserMessage):
        return "user"
    elif isinstance(message, AssistantMessage):
        return "assistant"
    elif isinstance(message, ToolResultMessage):
        return "user"
    else:
        raise ValueError(f"Unknown message type: {type(message)}")
