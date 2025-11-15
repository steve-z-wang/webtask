"""DOM module - Pure data structure classes for DOM representation."""

from .domnode import DomNode, DomNodeData, Text, BoundingBox
from .parsers import parse_html, parse_cdp
from .selector import XPath

__all__ = [
    "DomNode",
    "DomNodeData",
    "Text",
    "BoundingBox",
    "parse_html",
    "parse_cdp",
    "XPath",
]
