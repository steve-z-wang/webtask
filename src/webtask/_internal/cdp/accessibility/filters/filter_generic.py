"""Filter to remove generic wrapper nodes from accessibility tree."""

from ..axnode import AXNode
from .filter_by_predicate import filter_by_predicate


def filter_generic_nodes(root: AXNode) -> AXNode:
    """
    Filter accessibility tree to remove generic wrapper nodes.

    Generic nodes are non-semantic container elements (like <div> in HTML).
    They don't provide meaningful information for LLM context.

    Args:
        root: Root AXNode to filter

    Returns:
        New filtered tree with generic nodes removed

    Example:
        Before:
            [button-0] "Click me"
              └─ [generic-10]
                  └─ [StaticText-0] "Click me"

        After:
            [button-0] "Click me"
              └─ [StaticText-0] "Click me"
    """

    def is_generic(node: AXNode) -> bool:
        role = str(node.role.value) if node.role and node.role.value else "unknown"
        return role == "generic"

    result = filter_by_predicate(root, is_generic)
    # filter_by_predicate returns Optional[AXNode], but we should always have a root
    return result if result is not None else root.copy(children=[], parent=None)
