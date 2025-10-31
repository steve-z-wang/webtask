"""Collapse single-child wrapper elements."""

from ...domnode import DomNode, Text


def collapse_single_child_wrappers(node: DomNode) -> DomNode:
    """Collapse single-child wrapper elements."""
    new_children = []
    for child in node.children:
        if isinstance(child, Text):
            new_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            collapsed_child = collapse_single_child_wrappers(child)
            new_children.append(collapsed_child)

    has_attributes = bool(node.attrib)
    element_children = [c for c in new_children if isinstance(c, DomNode)]
    text_children = [c for c in new_children if isinstance(c, Text)]

    has_meaningful_text = any(c.content.strip() for c in text_children)

    if not has_attributes and len(element_children) == 1 and not has_meaningful_text:
        return element_children[0]

    new_node = node.copy()

    for child in new_children:
        new_node.add_child(child)

    return new_node
