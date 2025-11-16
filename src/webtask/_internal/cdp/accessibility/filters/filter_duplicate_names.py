"""Filter to remove nodes with duplicate names from accessibility tree."""

from typing import Optional
from ..axnode import AXNode
from .filter_by_predicate import filter_by_predicate


def filter_duplicate_names(root: AXNode) -> Optional[AXNode]:
    """
    Filter accessibility tree to remove nodes whose name duplicates an ancestor's name.
    """

    def has_duplicate_name(node: AXNode) -> bool:
        """Check if node's name is contained in nearest ancestor's name."""
        node_name = node.name.value if node.name and node.name.value else None
        if not node_name:
            return False

        # Walk up parent chain to find nearest ancestor with a name
        current = node.parent
        while current is not None:
            ancestor_name = (
                current.name.value if current.name and current.name.value else None
            )
            if ancestor_name:
                # Found nearest ancestor with name - check if child text is in parent text
                return node_name in ancestor_name
            current = current.parent

        return False

    return filter_by_predicate(root, has_duplicate_name)
