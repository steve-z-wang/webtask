"""webtask - Web automation framework with LLM-powered agents."""

from .webtask import Webtask
from .agent import Agent

from .dom import (
    DomNode,
    DomNodeData,
    Text,
    BoundingBox,
    parse_html,
    parse_cdp,
    DomSnapshot,
)

from .llm import (
    Context,
    Block,
    LLM,
)

from .media import Image

__version__ = "0.1.0"

__all__ = [
    # Manager
    "Webtask",
    # Agent
    "Agent",
    # DOM types
    "DomNode",
    "DomNodeData",
    "Text",
    "BoundingBox",
    # Parsers
    "parse_html",
    "parse_cdp",
    # Snapshot
    "DomSnapshot",
    # LLM
    "Context",
    "Block",
    "LLM",
    # Media
    "Image",
]
