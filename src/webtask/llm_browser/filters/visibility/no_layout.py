"""Remove elements with no layout data."""

from typing import Optional
from ....dom.domnode import DomNode, Text


def filter_no_layout(node: DomNode) -> Optional[DomNode]:
    """Remove elements with no layout data."""
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None

    if not has_styles and not has_bounds:
        return None

    new_node = node.copy()

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_no_layout(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
