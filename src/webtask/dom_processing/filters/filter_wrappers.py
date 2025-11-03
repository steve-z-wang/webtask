"""Filter to collapse single-child wrapper elements.

Removes unnecessary wrapper elements that don't add semantic value,
while preserving interactive elements.
"""

from ...dom.domnode import DomNode, Text
from ..knowledge import is_interactive


def collapse_single_child_wrappers(node: DomNode) -> DomNode:
    """Collapse single-child wrapper elements.

    Removes wrapper elements that have:
    - No attributes
    - Exactly one element child
    - No meaningful text
    - Not interactive

    Uses is_interactive() to preserve interactive wrappers.

    Args:
        node: DOM node to filter

    Returns:
        Filtered node (possibly collapsed to its child)
    """
    # Recursively process children first
    new_children = []
    for child in node.children:
        if isinstance(child, Text):
            new_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            collapsed_child = collapse_single_child_wrappers(child)
            new_children.append(collapsed_child)

    # Analyze this node
    has_attributes = bool(node.attrib)
    element_children = [c for c in new_children if isinstance(c, DomNode)]
    text_children = [c for c in new_children if isinstance(c, Text)]
    has_meaningful_text = any(c.content.strip() for c in text_children)

    # Check if this is a collapsible wrapper
    # Never collapse interactive elements - they have semantic meaning
    if (
        not has_attributes
        and len(element_children) == 1
        and not has_meaningful_text
        and not is_interactive(node)
    ):
        # Collapse: return the single child instead of this wrapper
        return element_children[0]

    # Keep the node with its children
    new_node = node.copy()
    for child in new_children:
        new_node.add_child(child)

    return new_node
