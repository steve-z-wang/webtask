"""Filter non-semantic elements and attributes."""

from typing import Optional, Union
from ..domnode import DomNode, Text
from ..knowledge import has_semantic_value, is_semantic_attribute
from ...utils.filter_tree_by_predicate import filter_tree_by_predicate


def filter_non_semantic(node: DomNode) -> Optional[DomNode]:
    """Apply all semantic filters: attributes, elements, and wrapper collapse."""
    # 1. Remove non-semantic attributes
    node = _remove_non_semantic_attributes(node)

    # 2. Remove non-semantic elements (promote children)
    # Note: script/style tags already removed by filter_non_rendered
    def should_remove(n: Union[DomNode, Text]) -> bool:
        """Remove nodes without semantic value."""
        return not has_semantic_value(n)

    return filter_tree_by_predicate(node, should_remove, on_remove="promote")


def _remove_non_semantic_attributes(node: DomNode) -> DomNode:
    """Keep only semantic attributes."""
    new_node = node.deepcopy()
    new_node.attrib = {k: v for k, v in node.attrib.items() if is_semantic_attribute(k)}

    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = _remove_non_semantic_attributes(child)
            filtered_children.append(filtered_child)

    new_node.children = filtered_children
    for child in new_node.children:
        child.parent = new_node

    return new_node
