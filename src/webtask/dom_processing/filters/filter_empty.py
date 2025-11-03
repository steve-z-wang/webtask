"""Filter to remove empty elements.

Removes elements that have no content and no semantic purpose,
while preserving interactive elements even if empty.
"""

from typing import Optional
from ...dom.domnode import DomNode, Text
from ..knowledge import is_empty_element


def filter_empty(node: DomNode) -> Optional[DomNode]:
    """Remove empty nodes that serve no purpose.

    Uses is_empty_element() to determine if an element should be removed.
    Preserves interactive elements even if they're empty.

    Args:
        node: DOM node to filter

    Returns:
        Filtered node or None if should be removed
    """
    # First, recursively filter children
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            if child.content.strip():
                filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_empty(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    # Check if this node is empty using knowledge function
    if is_empty_element(node, filtered_children):
        return None  # Remove empty element

    # Keep the node and add filtered children
    new_node = node.copy()
    for child in filtered_children:
        new_node.add_child(child)

    return new_node
