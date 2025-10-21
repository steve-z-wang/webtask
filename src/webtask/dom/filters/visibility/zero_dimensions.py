"""Remove zero-dimension elements."""

from typing import Optional
from ...domnode import DomNode, Text


def filter_zero_dimensions(node: DomNode) -> Optional[DomNode]:
    """
    Remove zero-dimension elements (width=0 or height=0).

    Exception: Keeps zero-dimension elements that have visible children
    (e.g., absolutely positioned popups/modals).

    Args:
        node: DomNode to filter

    Returns:
        New DomNode without zero-dimension elements, or None if removed

    Example:
        >>> div = DomNode(tag='div', bounds=BoundingBox(0, 0, 0, 0))
        >>> filtered = filter_zero_dimensions(div)
        >>> filtered is None  # Removed if no visible children
        True
    """
    # First, recursively filter children
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_zero_dimensions(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    # Check if this node has zero dimensions
    has_zero_size = node.bounds and (node.bounds.width == 0 or node.bounds.height == 0)

    if has_zero_size:
        # Keep if it has visible children (e.g., positioned popup)
        has_visible_children = any(isinstance(c, DomNode) for c in filtered_children)
        if not has_visible_children:
            return None

    # Create new node
    new_node = node.copy()

    # Add filtered children
    for child in filtered_children:
        new_node.add_child(child)

    return new_node
