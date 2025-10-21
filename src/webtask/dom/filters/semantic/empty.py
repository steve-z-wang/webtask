"""Remove empty nodes."""

from typing import Optional
from ...domnode import DomNode, Text

# Interactive tags to keep even if empty
INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "label"}


def filter_empty(node: DomNode) -> Optional[DomNode]:
    """
    Remove empty nodes (no attributes and no children).

    Exception: Keeps interactive elements even if empty (button, input, etc.)

    Args:
        node: DomNode to filter

    Returns:
        New DomNode without empty nodes, or None if node itself is empty

    Example:
        >>> div = DomNode(tag='div')  # No attributes, no children
        >>> filtered = filter_empty(div)
        >>> filtered is None
        True
    """
    # Recursively filter children first
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            # Keep text with content
            if child.content.strip():
                filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_empty(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    # Check if node is empty
    has_attributes = bool(node.attrib)
    has_children = len(filtered_children) > 0
    is_interactive = node.tag in INTERACTIVE_TAGS

    # Remove if empty (no attributes, no children) and not interactive
    if not has_attributes and not has_children and not is_interactive:
        return None

    # Create new node
    new_node = node.copy()

    # Add filtered children
    for child in filtered_children:
        new_node.add_child(child)

    return new_node
