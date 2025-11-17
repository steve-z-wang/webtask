"""Filter to remove ignored nodes from accessibility tree."""

from typing import Optional
from ..axnode import AXNode
from ...utils.filter_tree_by_predicate import filter_tree_by_predicate


def filter_ignored_nodes(root: AXNode) -> Optional[AXNode]:
    """
    Filter accessibility tree to remove ignored nodes.

    Ignored nodes (aria-hidden, etc.) are flattened - children are promoted.
    """
    return filter_tree_by_predicate(
        root, lambda node: node.ignored, on_remove="promote"
    )
