"""Filter to remove nodes with non-semantic roles from accessibility tree."""

from ..axnode import AXNode
from ...utils.filter_tree_by_predicate import filter_tree_by_predicate


def filter_non_semantic_role(root: AXNode) -> AXNode:
    """
    Filter accessibility tree to remove nodes with non-semantic roles.

    This includes:
    - Nodes with role="generic" (non-semantic container elements like <div>)
    - Nodes with role="none" (elements with presentational role)

    These wrapper nodes are flattened - children are promoted.
    """

    def has_non_semantic_role(node: AXNode) -> bool:
        """Check if node has a non-semantic role (generic or none)."""
        role = str(node.role.value) if node.role and node.role.value else "unknown"
        return role in ("generic", "none")

    result = filter_tree_by_predicate(root, has_non_semantic_role, on_remove="promote")
    # filter_tree_by_predicate returns Optional[AXNode], but we should always have a root
    return result if result is not None else root.copy(children=[], parent=None)
