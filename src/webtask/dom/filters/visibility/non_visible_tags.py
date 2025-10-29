"""Remove non-visible tags (script, style, head, etc.)."""

from typing import Optional, Set
from ...domnode import DomNode, Text


def filter_non_visible_tags(
    node: DomNode, non_visible_tags: Set[str]
) -> Optional[DomNode]:
    """
    Remove non-visible tags (script, style, head, meta, etc.).

    Args:
        node: DomNode to filter
        non_visible_tags: Set of tag names to remove

    Returns:
        New DomNode without non-visible tags, or None if node itself is non-visible

    Example:
        >>> root = DomNode(tag='div')
        >>> root.add_child(DomNode(tag='script'))
        >>> root.add_child(DomNode(tag='button'))
        >>> tags = {"script", "style"}
        >>> filtered = filter_non_visible_tags(root, tags)
        >>> len(filtered.children)  # Only button remains
        1
    """

    # Check if this node should be removed
    if node.tag in non_visible_tags:
        return None

    # Create new node with same properties
    new_node = node.copy()

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            # Keep text nodes
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_non_visible_tags(child, non_visible_tags)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
