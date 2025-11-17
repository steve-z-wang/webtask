"""Filter to remove text nodes with duplicate names from accessibility tree."""

from typing import Optional
from ..axnode import AXNode
from ...utils.filter_tree_by_predicate import filter_tree_by_predicate


def filter_duplicate_text(root: AXNode) -> Optional[AXNode]:
    """
    Filter accessibility tree to remove text-only nodes whose name duplicates an ancestor's name.
    Only removes StaticText/InlineTextBox nodes to preserve interactive elements.
    """

    def is_duplicate_text(node: AXNode) -> bool:
        """Check if node is text-only with duplicate name in ancestor."""
        # Only filter text nodes (StaticText, InlineTextBox)
        role = str(node.role.value) if node.role and node.role.value else ""
        if role not in ("StaticText", "InlineTextBox"):
            return False  # Don't filter non-text nodes

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

    return filter_tree_by_predicate(root, is_duplicate_text, on_remove="keep_wrapper")
