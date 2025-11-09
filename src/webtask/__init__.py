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
    Context,
    Block,
    LLM,
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
    "Context",
    "Block",
    "LLM",
    # Media
    "Image",
]
