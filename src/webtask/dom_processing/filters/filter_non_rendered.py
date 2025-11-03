"""Filter non-rendered elements."""

from typing import Optional
from ...dom.domnode import DomNode, Text
from ..knowledge import is_not_rendered, should_keep_when_not_rendered


def filter_non_rendered(node: DomNode) -> Optional[DomNode]:
    """Remove elements that are not rendered."""
    return _remove_non_rendered_elements(node)


def _remove_non_rendered_elements(node: DomNode) -> Optional[DomNode]:
    """Remove elements without layout data from CDP."""
    if is_not_rendered(node) and not should_keep_when_not_rendered(node):
        return None

    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = _remove_non_rendered_elements(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    new_node = node.copy()
    for child in filtered_children:
        new_node.add_child(child)

    return new_node
