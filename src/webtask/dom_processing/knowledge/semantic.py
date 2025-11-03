"""Knowledge: Determine if elements have semantic value."""

from ...dom.domnode import DomNode
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


def has_semantic_value(node: DomNode) -> bool:
    """Check if element has semantic value (should be kept)."""
    if is_presentational_role(node):
        return False

    has_semantic_attributes = any(is_semantic_attribute(k) for k in node.attrib.keys())
    is_interactive_elem = is_interactive(node)

    return has_semantic_attributes or is_interactive_elem
