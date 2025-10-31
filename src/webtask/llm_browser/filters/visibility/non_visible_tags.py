"""Remove non-visible tags."""

from typing import Optional, Set
from ....dom.domnode import DomNode, Text


def filter_non_visible_tags(
    node: DomNode, non_visible_tags: Set[str]
) -> Optional[DomNode]:
    """Remove non-visible tags."""

    if node.tag in non_visible_tags:
        return None

    new_node = node.copy()

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_non_visible_tags(child, non_visible_tags)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
