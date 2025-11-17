"""Accessibility tree node intermediate representation.

AXNode represents a node in the accessibility tree with semantic information
that complements the DOM tree. It provides:
- Semantic roles (button, menu, textbox, etc.)
- Computed accessible names
- Element states (expanded, checked, selected, etc.)
- Relationships between elements (controls, labelledby, etc.)
- Visibility/ignored status
- Link back to DOM node via backendDOMNodeId
"""

from dataclasses import dataclass, field, replace
from typing import Optional, List, Dict, Any
from enum import Enum


class AXValueType(str, Enum):
    """Types of values in accessibility tree properties."""

    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    IDREF = "idref"
    IDREF_LIST = "idrefList"
    NODE_LIST = "nodeList"
    COMPUTED_STRING = "computedString"
    TOKEN = "token"
    TOKEN_LIST = "tokenList"


@dataclass
class AXValue:
    """Value in accessibility tree (role, name, property, etc.)."""

    type: str  # AXValueType
    value: Any = None
    sources: List[Dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        if self.value is None:
            return ""
        return str(self.value)

    def __bool__(self) -> bool:
        """Allow truthiness check on value."""
        return self.value is not None and self.value != ""


@dataclass
class AXProperty:
    """Property of an accessibility node."""

    name: str
    value: AXValue

    def __str__(self) -> str:
        return f"{self.name}={self.value}"


@dataclass
class AXNode:
    """
    Accessibility tree node with semantic information.

    Represents a node in the browser's accessibility tree, providing
    semantic information about the element that goes beyond the DOM.
    """

    # Identity
    node_id: str
    backend_dom_node_id: Optional[int] = None

    # Accessibility info
    ignored: bool = False
    ignored_reasons: List[Dict[str, Any]] = field(default_factory=list)

    # Semantics
    role: Optional[AXValue] = None
    chrome_role: Optional[AXValue] = None
    name: Optional[AXValue] = None
    description: Optional[AXValue] = None
    value: Optional[AXValue] = None

    # Properties (states, relationships, etc.)
    properties: List[AXProperty] = field(default_factory=list)

    # Tree structure - only actual node references
    parent: Optional["AXNode"] = field(default=None, repr=False)
    children: List["AXNode"] = field(default_factory=list)

    # Additional metadata
    frame_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy(self, children: List["AXNode"], parent: Optional["AXNode"]) -> "AXNode":
        """Create a copy of this node with new children and parent.

        Args:
            children: List of child nodes for the new node
            parent: Parent node for the new node (None for root)

        Returns:
            New AXNode instance with specified children and parent
        """
        return replace(self, children=list(children), parent=parent)

    def traverse(self) -> "AXNode":
        """
        Generator that yields this node and all descendants in depth-first order.

        Yields:
            AXNode objects in depth-first traversal order
        """
        yield self
        for child in self.children:
            yield from child.traverse()

    @classmethod
    def from_cdp(cls, cdp_data: Dict[str, Any]) -> "AXNode":
        """
        Create AXNode tree from CDP accessibility tree data.
        """
        from .parsers.cdp import parse_cdp_accessibility

        return parse_cdp_accessibility(cdp_data)

    def __repr__(self) -> str:
        role = str(self.role.value) if self.role and self.role.value else "unknown"
        name = str(self.name.value) if self.name and self.name.value else ""
        ignored_str = " (ignored)" if self.ignored else ""
        name_str = f' "{name}"' if name else ""
        return f"AXNode({role}{name_str}{ignored_str})"
