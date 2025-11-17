"""Generic filter function for tree nodes (works with any tree structure)."""

from typing import Callable, Optional, TypeVar, Any
from .tree_protocol import TreeNode


T = TypeVar("T", bound=TreeNode)


def filter_tree_by_predicate(
    root: T, should_remove: Callable[[Any], bool], on_remove: str = "promote"
) -> Optional[T]:
    """
    Filter tree nodes based on a predicate function.

    Works with any tree structure (AXNode, DomNode, etc.) that has children and copy().

    Behavior when node matches predicate (should_remove returns True):
    - "promote": Always promote all children (flatten wrapper nodes)
    - "delete": Delete node and all descendants (entire subtree)
    - "keep_wrapper": Keep node only if it has children (wrappers); delete if leaf

    Note: The root node is always kept, even if it matches the predicate.

    Args:
        root: Root node to filter (always kept)
        should_remove: Predicate function returning True if node should be removed
        on_remove: Behavior when removing nodes - "promote", "delete", or "keep_wrapper"
    """
    if on_remove not in ("promote", "delete", "keep_wrapper"):
        raise ValueError(
            f"on_remove must be 'promote', 'delete', or 'keep_wrapper', got: {on_remove}"
        )

    def _filter_node(node: T) -> list[T]:
        """Returns list of nodes (0, 1, or many)."""
        # Check early if we should delete entire subtree
        if on_remove == "delete" and should_remove(node):
            # Delete node and all descendants - don't even process children
            return []

        # Bottom-up: recursively filter all children first
        filtered_children_lists = [_filter_node(child) for child in node.children]
        filtered_children = [c for sublist in filtered_children_lists for c in sublist]

        # Check if current node should be removed
        if should_remove(node):
            if on_remove == "promote":
                # Always promote all children (flatten wrapper)
                return filtered_children
            elif on_remove == "keep_wrapper":
                # Keep wrapper only if it has children; delete if leaf
                if filtered_children:
                    new_node = node.copy(children=filtered_children, parent=None)
                    for child in new_node.children:
                        child.parent = new_node
                    return [new_node]
                else:
                    # It's a leaf (no children), not a wrapper - delete it
                    return []
            # on_remove == "delete" already handled above
        else:
            # Node doesn't match predicate - keep it with filtered children
            new_node = node.copy(children=filtered_children, parent=None)
            for child in new_node.children:
                child.parent = new_node
            return [new_node]

    # Filter root's children (root itself is always kept)
    filtered_children_lists = [_filter_node(child) for child in root.children]
    filtered_children = [c for sublist in filtered_children_lists for c in sublist]

    # Return root with filtered children
    new_root = root.copy(children=filtered_children, parent=None)
    for child in new_root.children:
        child.parent = new_root

    return new_root
