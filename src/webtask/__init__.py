"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent, Result, Verdict, Tool
from .exceptions import (
    WebtaskError,
    TaskAbortedError,
)

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

__version__ = "0.21.2"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    "Result",
    "Verdict",
    "Tool",
    # Exceptions
    "WebtaskError",
    "TaskAbortedError",
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
