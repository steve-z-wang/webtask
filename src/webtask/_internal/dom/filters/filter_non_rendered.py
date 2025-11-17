"""Filter non-rendered elements."""

from typing import Optional, Union
from ..domnode import DomNode, Text
from ..knowledge import is_not_rendered, should_keep_when_not_rendered
from ...utils.filter_tree_by_predicate import filter_tree_by_predicate


def filter_non_rendered(node: DomNode) -> Optional[DomNode]:
    """Remove elements that are not rendered.

    Non-rendered wrapper elements are flattened - children are promoted.
    Text nodes are always kept (they don't have rendering info).
    """

    def should_remove(n: Union[DomNode, Text]) -> bool:
        """Check if node should be removed (not rendered and not special)."""
        return is_not_rendered(n) and not should_keep_when_not_rendered(n)

    return filter_tree_by_predicate(node, should_remove, on_remove="delete")
