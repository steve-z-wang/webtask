"""Protocol for tree node structures."""

from typing import Protocol, Optional, Sequence


class TreeNode(Protocol):
    """Protocol for tree nodes that can be filtered.

    Both AXNode, DomNode, and Text implement this protocol to enable
    generic tree filtering operations.
    """

    children: Sequence["TreeNode"]
    parent: Optional["TreeNode"]

    def copy(
        self, children: Sequence["TreeNode"], parent: Optional["TreeNode"]
    ) -> "TreeNode":
        """Create a copy of this node with new children and parent.

        Args:
            children: List of child nodes for the new node
            parent: Parent node for the new node (None for root)

        Returns:
            New node instance with specified children and parent
        """
        ...
