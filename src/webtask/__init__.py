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

from .media import Image

__version__ = "0.11.0"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    # Browser interfaces (for custom implementations)
    "Browser",
    "Session",
    "Page",
    "Element",
    # LLM
    "LLM",
    "Text",
    "Content",
    # Media
    "Image",
]
