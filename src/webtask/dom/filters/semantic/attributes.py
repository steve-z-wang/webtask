"""Filter attributes to keep only semantic ones."""

from typing import Set
from ...domnode import DomNode, Text

# Semantic attributes to preserve
SEMANTIC_ATTRIBUTES: Set[str] = {
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-checked",
    "aria-selected",
    "aria-expanded",
    "aria-hidden",
    "aria-disabled",
    "type",
    "name",
    "placeholder",
    "value",
    "alt",
    "title",
    "href",
    "disabled",
    "checked",
    "selected",
}


def filter_attributes(node: DomNode, keep: Set[str] = None) -> DomNode:
    """
    Keep only semantic attributes, remove all others.

    Args:
        node: DomNode to filter
        keep: Set of attributes to keep (defaults to SEMANTIC_ATTRIBUTES)

    Returns:
        New DomNode with only semantic attributes

    Example:
        >>> node = DomNode(tag='div', attrib={'class': 'foo', 'role': 'button'})
        >>> filtered = filter_attributes(node)
        >>> filtered.attrib
        {'role': 'button'}
    """
    if keep is None:
        keep = SEMANTIC_ATTRIBUTES

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
