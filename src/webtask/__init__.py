"""webtask - Web automation framework with LLM-powered agents."""

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
    ContextProvider,
    Context,
    Tokenizer,
    LLM,
)

__version__ = "0.1.0"

__all__ = [
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
    'ContextProvider',
    'Context',
    'Tokenizer',
    'LLM',
]
