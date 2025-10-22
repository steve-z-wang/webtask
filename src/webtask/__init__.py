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
    apply_visibility_filters,
    apply_semantic_filters,
    DomSnapshot,
    serialize_to_markdown,
)

from .llm import (
    Context,
    Block,
    Tokenizer,
    LLM,
)

__version__ = "0.1.0"

__all__ = [
    # Manager
    'Webtask',

    # Agent
    'Agent',

    # DOM types
    'DomNode',
    'DomNodeData',
    'Text',
    'BoundingBox',

    # Parsers
    'parse_html',
    'parse_cdp',

    # Filters
    'apply_visibility_filters',
    'apply_semantic_filters',

    # Snapshot
    'DomSnapshot',
    'serialize_to_markdown',

    # LLM
    'Context',
    'Block',
    'Tokenizer',
    'LLM',
]
