"""Filter to remove presentational role attributes.

ARIA roles "none" and "presentation" indicate elements are purely decorative.
This filter removes those role attributes to reduce noise for the LLM.
"""

from ...dom.domnode import DomNode, Text
from ..knowledge import is_presentational_role


def filter_presentational_roles(node: DomNode) -> DomNode:
    """Remove presentational role attributes from elements.

    Uses is_presentational_role() to identify which roles to remove.

    Args:
        node: DOM node to filter

    Returns:
        Filtered node with presentational roles removed
    """
    new_node = node.deepcopy()

    # Remove presentational role attribute if present
    if is_presentational_role(node):
        del new_node.attrib["role"]

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_presentational_roles(child)
            new_node.add_child(filtered_child)

    return new_node
