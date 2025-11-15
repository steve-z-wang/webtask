"""Chrome DevTools Protocol (CDP) data structures.

This module contains data structures and parsers for CDP-based representations:
- DOM: Document Object Model tree representation
- Accessibility: Accessibility tree representation
"""

from .dom import DomNode, DomNodeData, Text, BoundingBox, XPath
from .accessibility import AXNode, AXProperty, AXValue

__all__ = [
    # DOM
    "DomNode",
    "DomNodeData",
    "Text",
    "BoundingBox",
    "XPath",
    # Accessibility
    "AXNode",
    "AXProperty",
    "AXValue",
]
