"""Filter attributes."""

from typing import Set
from ....dom.domnode import DomNode, Text


def filter_attributes(node: DomNode, keep: Set[str]) -> DomNode:
    """Keep only semantic attributes."""

    new_node = node.deepcopy()
    new_node.attrib = {k: v for k, v in node.attrib.items() if k in keep}

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_attributes(child, keep)
            new_node.add_child(filtered_child)

    return new_node
