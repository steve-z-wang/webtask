"""Remove elements not rendered by the browser.

Chrome DevTools Protocol (CDP) only provides layout data (bounds and computed styles)
for nodes that are actually rendered in the browser's layout tree. Elements that are
not rendered (e.g., display:none, detached from DOM, etc.) will have no layout data.

This filter removes nodes that CDP did not include in the render tree, as indicated
by the absence of both bounds and styles.
"""

from typing import Optional
from ....dom.domnode import DomNode, Text


def filter_not_rendered(node: DomNode) -> Optional[DomNode]:
    """Remove elements not rendered by the browser.

    CDP does NOT add layout data (bounds/styles) for nodes that are not rendered.
    This filter removes those non-rendered elements.
    """
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None

    # If CDP provided no layout data, the element is not rendered
    if not has_styles and not has_bounds:
        return None

    new_node = node.copy()

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_not_rendered(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
