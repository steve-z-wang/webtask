"""Filter to keep only semantic attributes.

Removes non-semantic attributes to reduce noise for the LLM,
keeping only attributes that provide meaningful information.
"""

from typing import Set
from ...dom.domnode import DomNode, Text


def filter_attributes(node: DomNode, keep: Set[str]) -> DomNode:
    """Keep only specified semantic attributes.

    Args:
        node: DOM node to filter
        keep: Set of attribute names to keep (e.g., {"role", "type", "name"})

    Returns:
        Filtered node with only kept attributes
    """
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
