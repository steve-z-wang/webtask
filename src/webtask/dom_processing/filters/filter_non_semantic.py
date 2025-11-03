"""Filter non-semantic elements and attributes."""

from typing import Optional
from ...dom.domnode import DomNode, Text
from ..knowledge import has_semantic_value, is_semantic_attribute


def filter_non_semantic(node: DomNode) -> Optional[DomNode]:
    """Apply all semantic filters: attributes, elements, and wrapper collapse."""
    # 1. Remove non-semantic attributes
    node = _remove_non_semantic_attributes(node)

    # 2. Remove elements with no semantic value
    node = _remove_non_semantic_elements(node)
    if node is None:
        return None

    # 3. Collapse wrapper elements
    node = _collapse_non_semantic_wrappers(node)

    return node


def _remove_non_semantic_attributes(node: DomNode) -> DomNode:
    """Keep only semantic attributes."""
    new_node = node.deepcopy()
    new_node.attrib = {k: v for k, v in node.attrib.items() if is_semantic_attribute(k)}

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = _remove_non_semantic_attributes(child)
            new_node.add_child(filtered_child)

    return new_node


def _remove_non_semantic_elements(node: DomNode) -> Optional[DomNode]:
    """Remove nodes that have no semantic value."""
    filtered_children = []
    for child in node.children:
        if isinstance(child, Text):
            if child.content.strip():
                filtered_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = _remove_non_semantic_elements(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)

    has_children = len(filtered_children) > 0
    if not has_semantic_value(node) and not has_children:
        return None

    new_node = node.copy()
    for child in filtered_children:
        new_node.add_child(child)

    return new_node


def _collapse_non_semantic_wrappers(node: DomNode) -> DomNode:
    """Collapse wrapper elements with no semantic value and one element child."""
    new_children = []
    for child in node.children:
        if isinstance(child, Text):
            if child.content.strip():
                new_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            collapsed_child = _collapse_non_semantic_wrappers(child)
            new_children.append(collapsed_child)

    element_children = [c for c in new_children if isinstance(c, DomNode)]
    text_children = [c for c in new_children if isinstance(c, Text)]

    # Collapse if: exactly one element child AND no semantic value AND no text children
    if (
        len(element_children) == 1
        and not has_semantic_value(node)
        and len(text_children) == 0
    ):
        return element_children[0]

    new_node = node.copy()
    for child in new_children:
        new_node.add_child(child)

    return new_node
