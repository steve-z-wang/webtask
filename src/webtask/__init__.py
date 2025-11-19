"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent, Tool

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

from ._internal.agent.task_execution import TaskExecution, TaskResult

__version__ = "0.16.0"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    "Tool",
    "TaskExecution",
    "TaskResult",
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
