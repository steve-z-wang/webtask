"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent

from .browser import (
    Browser,
    Session,
    Page,
    Element,
)

from .llm import (
    LLM,
    Text,
    Content,
)

from ._internal.agent.task import TaskExecution, TaskStatus

__version__ = "0.11.0"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    "TaskExecution",
    "TaskStatus",
    # Browser interfaces (for custom implementations)
    "Browser",
    "Session",
    "Page",
    "Element",
    # LLM
    "LLM",
    "Text",
    "Content",
]
