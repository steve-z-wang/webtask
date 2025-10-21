"""Add original node reference to metadata for tracking."""

from ..domnode import DomNode


def add_node_reference(root: DomNode) -> DomNode:
    """
    Add reference to original node in metadata.

    Traverses the tree and adds 'original_node' reference to each node's metadata,
    pointing to itself. This allows tracking back to the unfiltered node after filtering.

    Args:
        root: Root DomNode of the tree

    Returns:
        Root DomNode (same instance, modified in place)
    """
    for node in root.traverse():
        if isinstance(node, DomNode):
            # Add reference to the node itself
            node.metadata['original_node'] = node

    return root
