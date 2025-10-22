"""DOM module - Pure data structure classes for DOM representation."""

from .domnode import DomNode, DomNodeData, Text, BoundingBox
from .parsers import parse_html, parse_cdp
from .filters import apply_visibility_filters, apply_semantic_filters
from .snapshot import DomSnapshot
from .serializers import serialize_to_markdown
from .selector import XPath

__all__ = [
    'DomNode',
    'DomNodeData',
    'Text',
    'BoundingBox',
    'parse_html',
    'parse_cdp',
    'apply_visibility_filters',
    'apply_semantic_filters',
    'DomSnapshot',
    'serialize_to_markdown',
    'XPath',
]
