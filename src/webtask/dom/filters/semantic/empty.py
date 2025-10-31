"""Remove empty nodes."""

from typing import Optional
from ...domnode import DomNode, Text

INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "label"}


def filter_empty(node: DomNode) -> Optional[DomNode]:
    """Remove empty nodes."""
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            if child.content.strip():
                filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_empty(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    has_attributes = bool(node.attrib)
    has_children = len(filtered_children) > 0
    is_interactive = node.tag in INTERACTIVE_TAGS

    if not has_attributes and not has_children and not is_interactive:
        return None

    new_node = node.copy()

    for child in filtered_children:
        new_node.add_child(child)

    return new_node
