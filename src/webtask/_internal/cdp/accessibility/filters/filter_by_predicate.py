"""Generic filter function for accessibility tree nodes."""

from typing import Callable, Optional
from ..axnode import AXNode


def filter_by_predicate(
    root: AXNode, should_remove: Callable[[AXNode], bool]
) -> Optional[AXNode]:
    """
    Filter accessibility tree nodes based on a predicate function.

    Uses bottom-up DFS with consistent behavior:
    1. Recursively filter all children first
    2. If current node matches predicate:
       - No children → delete (return None)
       - One child → promote that child
       - Multiple children → keep wrapper (return node with children)
    3. If current node doesn't match → keep with filtered children

    Args:
        root: Root AXNode to filter
        should_remove: Predicate function returning True if node should be removed

    Returns:
        Filtered tree or None if root should be deleted

    Example:
        # Remove all generic nodes
        filter_by_predicate(root, lambda n: n.role.value == "generic")

        # Remove all ignored nodes
        filter_by_predicate(root, lambda n: n.ignored)
    """
    # Bottom-up: recursively filter ALL children first
    filtered_children = []
    for child in root.children:
        filtered_child = filter_by_predicate(child, should_remove)
        if filtered_child is not None:
            filtered_children.append(filtered_child)

    # Check if current node should be removed
    if should_remove(root):
        # Node matches predicate - apply promotion rules
        if len(filtered_children) == 0:
            return None  # No children - delete this node
        elif len(filtered_children) == 1:
            return filtered_children[0]  # One child - promote it
        else:
            # Multiple children - keep wrapper
            new_node = root.copy(children=filtered_children, parent=None)
            # Update parent references
            for child in new_node.children:
                child.parent = new_node
            return new_node
    else:
        # Node doesn't match predicate - keep it with filtered children
        new_node = root.copy(children=filtered_children, parent=None)
        # Update parent references
        for child in new_node.children:
            child.parent = new_node
        return new_node
