"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent, Status, Result, Tool

from .browser import (
    Browser,
    Context,
    Page,
    Element,
)

from .llm import (
    LLM,
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ToolCall,
    ToolResult,
    ToolResultStatus,
)

__version__ = "0.17.5"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    "Status",
    "Result",
    "Tool",
    # Browser interfaces (for custom implementations)
    "Browser",
    "Context",
    "Page",
    "Element",
    # LLM interface
    "LLM",
    "Message",
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "ToolResultMessage",
    "TextContent",
    "ImageContent",
    "ToolCall",
    "ToolResult",
    "ToolResultStatus",
]
