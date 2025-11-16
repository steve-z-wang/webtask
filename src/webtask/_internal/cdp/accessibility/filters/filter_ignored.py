"""Filter to remove ignored nodes from accessibility tree."""

from typing import Optional
from ..axnode import AXNode
from .filter_by_predicate import filter_by_predicate


def filter_ignored_nodes(root: AXNode) -> Optional[AXNode]:
    """
    Filter accessibility tree to remove ignored nodes.
    """
    return filter_by_predicate(root, lambda node: node.ignored)
