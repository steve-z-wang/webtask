"""Filter to remove ignored nodes from accessibility tree."""

from typing import Optional
from ..axnode import AXNode
from .filter_by_predicate import filter_by_predicate


def filter_ignored_nodes(root: AXNode) -> Optional[AXNode]:
    """
    Filter accessibility tree to remove ignored nodes.

    Args:
        root: Root AXNode to filter

    Returns:
        New filtered tree with ignored nodes removed, or None if root is ignored
        and has no non-ignored descendants

    Example:
        Before:
            [RootWebArea] (not ignored)
              └─ [none] (ignored)
                  ├─ [generic] (not ignored)
                  └─ [textbox] (not ignored)

        After:
            [RootWebArea] (not ignored)
              ├─ [generic] (not ignored)  ← Promoted!
              └─ [textbox] (not ignored)  ← Promoted!
    """
    return filter_by_predicate(root, lambda node: node.ignored)
