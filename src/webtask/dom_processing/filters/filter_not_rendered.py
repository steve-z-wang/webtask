"""Filter to remove elements not rendered by the browser.

Removes elements that CDP did not include in the render tree (display:none, etc.),
while preserving functional hidden elements like file inputs and hidden form fields.
"""

from typing import Optional
from ...dom.domnode import DomNode, Text
from ..knowledge import is_not_rendered, should_keep_when_not_rendered


def filter_not_rendered(node: DomNode) -> Optional[DomNode]:
    """Remove elements not rendered by the browser, preserving functional hidden elements.

    Uses knowledge functions to determine:
    1. is_not_rendered() - Does this element have layout data from CDP?
    2. should_keep_when_not_rendered() - Should we keep it anyway?

    Args:
        node: DOM node to filter

    Returns:
        Filtered node or None if should be removed
    """
    # Check if element is not rendered (no layout data from CDP)
    if is_not_rendered(node):
        # Keep functional hidden elements (file inputs, hidden inputs, etc.)
        if should_keep_when_not_rendered(node):
            pass  # Keep it
        else:
            return None  # Remove non-functional hidden elements

    # Create new node and recursively filter children
    new_node = node.copy()

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_not_rendered(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
