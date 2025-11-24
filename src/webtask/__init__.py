"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent
from .result import Result, Verdict
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

# Re-export from dodo
from dodo import (
    LLM,
    Tool,
    tool,
    Text,
    Image,
    Content,
    ToolResult,
    ToolResultStatus,
    Message,
    SystemMessage,
    UserMessage,
    ModelMessage,
)

__version__ = "0.20.0"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    "Result",
    "Verdict",
    # Tool
    "Tool",
    "tool",
    # Exceptions
    "WebtaskError",
    "TaskAbortedError",
    # Browser interfaces (for custom implementations)
    "Browser",
    "Context",
    "Page",
    "Element",
    # LLM interface (from dodo)
    "LLM",
    "Text",
    "Image",
    "Content",
    "ToolResult",
    "ToolResultStatus",
    "Message",
    "SystemMessage",
    "UserMessage",
    "ModelMessage",
]
