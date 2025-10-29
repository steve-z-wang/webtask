"""Remove elements with no layout data (not in layout tree)."""

from typing import Optional
from ...domnode import DomNode, Text


def filter_no_layout(node: DomNode) -> Optional[DomNode]:
    """
    Remove elements that have no layout data.

    CDP (Chrome DevTools Protocol) excludes elements with display:none,
    visibility:hidden, and other non-rendered elements from the layout tree.
    These elements will have empty styles dict and no bounding box.

    This filter catches hidden elements that CSS filters might miss because
    CDP doesn't provide computed styles for non-rendered elements.

    Args:
        node: DomNode to filter

    Returns:
        New DomNode without non-rendered elements, or None if node itself has no layout

    Example:
        >>> # Modal with display:none has no layout data
        >>> modal = DomNode(tag='div', styles={}, bounds=None)
        >>> filtered = filter_no_layout(modal)
        >>> filtered is None
        True

        >>> # Visible element has layout data
        >>> button = DomNode(tag='button', styles={'display': 'block'}, bounds=BoundingBox(0, 0, 100, 50))
        >>> filtered = filter_no_layout(button)
        >>> filtered is not None
        True
    """
    # Check if element has no layout data
    # Elements not in the layout tree (display:none, etc.) have empty styles and no bounds
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None

    # If element has neither styles nor bounds, it's not rendered - filter it out
    if not has_styles and not has_bounds:
        return None

    # Create new node
    new_node = node.copy()

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            # Keep text nodes
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_no_layout(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
