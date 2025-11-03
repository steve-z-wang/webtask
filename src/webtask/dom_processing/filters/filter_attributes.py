"""Filter to keep only semantic attributes.

Removes non-semantic attributes to reduce noise for the LLM,
keeping only attributes that provide meaningful information.
"""

from ...dom.domnode import DomNode, Text
from ..knowledge import is_semantic_attribute


def filter_attributes(node: DomNode) -> DomNode:
    """Keep only semantic attributes.

    Uses is_semantic_attribute() to determine which attributes to keep.

    Args:
        node: DOM node to filter

    Returns:
        Filtered node with only semantic attributes
    """
    new_node = node.deepcopy()
    new_node.attrib = {k: v for k, v in node.attrib.items() if is_semantic_attribute(k)}

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_attributes(child)
            new_node.add_child(filtered_child)

    return new_node
