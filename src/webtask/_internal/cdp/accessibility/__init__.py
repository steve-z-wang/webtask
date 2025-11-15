"""Accessibility tree intermediate representation.

This module provides classes and utilities for working with accessibility trees
from Chrome DevTools Protocol (CDP). The accessibility tree provides semantic
information about page elements that complements the DOM tree.

Key components:
- AXNode: Intermediate representation of accessibility tree nodes
- Parsers: Convert CDP accessibility data to AXNode trees
"""

from .axnode import AXNode, AXProperty, AXValue

__all__ = [
    "AXNode",
    "AXProperty",
    "AXValue",
]
