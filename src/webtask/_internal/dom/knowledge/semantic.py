"""Knowledge: Determine if elements have semantic value."""

from typing import Union
from ..domnode import DomNode, Text
from .interactive import is_interactive

# Semantic attributes that provide meaningful information
SEMANTIC_ATTRIBUTES = {
    # ARIA attributes (accessibility/interactivity)
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-checked",
    "aria-selected",
    "aria-expanded",
    "aria-hidden",
    "aria-disabled",
    "aria-haspopup",
    # Form/input attributes
    "type",
    "name",
    "placeholder",
    "value",
    "accept",
    "alt",
    "title",
    "disabled",
    "checked",
    "selected",
    # Interaction attributes
    "tabindex",
    "onclick",
}


def is_semantic_attribute(attr_name: str) -> bool:
    """Check if an attribute is semantically meaningful."""
    return attr_name in SEMANTIC_ATTRIBUTES


def is_presentational_role(node: DomNode) -> bool:
    """Check if element has role="presentation" or role="none"."""
    role = node.attrib.get("role", "").lower().strip()
    return role in ("presentation", "none")


def has_semantic_value(node: Union[DomNode, Text]) -> bool:
    """Check if node has semantic value (should be kept).

    Text nodes with content have semantic value.
    DomNodes have semantic value if they have semantic attributes or are interactive.
    Script and style tags are filtered out (not useful for LLM context).
    """
    # Text nodes with content have semantic value
    if isinstance(node, Text):
        return bool(node.content.strip())

    # DomNode checks
    # Filter out script and style tags (code/CSS not useful for LLM)
    if node.tag.lower() in ("script", "style"):
        return False

    if is_presentational_role(node):
        return False

    has_semantic_attributes = any(is_semantic_attribute(k) for k in node.attrib.keys())
    is_interactive_elem = is_interactive(node)

    return has_semantic_attributes or is_interactive_elem
