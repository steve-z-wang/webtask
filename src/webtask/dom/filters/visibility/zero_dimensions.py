"""Remove zero-dimension elements."""

from typing import Optional
from ...domnode import DomNode, Text


def filter_zero_dimensions(node: DomNode) -> Optional[DomNode]:
    """Remove zero-dimension elements."""
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_zero_dimensions(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    has_zero_size = node.bounds and (node.bounds.width == 0 or node.bounds.height == 0)

    if has_zero_size:
        has_visible_children = any(isinstance(c, DomNode) for c in filtered_children)
        if not has_visible_children:
            return None

    new_node = node.copy()

    for child in filtered_children:
        new_node.add_child(child)

    return new_node
