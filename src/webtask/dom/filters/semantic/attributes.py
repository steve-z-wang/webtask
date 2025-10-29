"""Filter attributes to keep only semantic ones."""

from typing import Set
from ...domnode import DomNode, Text


def filter_attributes(node: DomNode, keep: Set[str]) -> DomNode:
    """
    Keep only semantic attributes, remove all others.

    Args:
        node: DomNode to filter
        keep: Set of attributes to keep

    Returns:
        New DomNode with only semantic attributes

    Example:
        >>> node = DomNode(tag='div', attrib={'class': 'foo', 'role': 'button'})
        >>> filtered = filter_attributes(node, keep={'role', 'type'})
        >>> filtered.attrib
        {'role': 'button'}
    """

    # Create new node with copied data (since we'll modify attributes)
    new_node = node.deepcopy()
    new_node.attrib = {k: v for k, v in node.attrib.items() if k in keep}

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_attributes(child, keep)
            new_node.add_child(filtered_child)

    return new_node
