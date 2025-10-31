"""Add node reference to metadata."""

from ..domnode import DomNode


def add_node_reference(root: DomNode) -> DomNode:
    """Add node reference to metadata."""
    for node in root.traverse():
        if isinstance(node, DomNode):
            node.metadata['original_node'] = node

    return root
