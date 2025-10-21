"""Collapse single-child wrapper elements."""

from ...domnode import DomNode, Text


def collapse_single_child_wrappers(node: DomNode) -> DomNode:
    """
    Collapse single-child wrapper elements.

    If an element has no attributes and exactly one element child,
    promote the child to replace the wrapper.

    Args:
        node: DomNode to process

    Returns:
        New DomNode with collapsed wrappers

    Example:
        >>> wrapper = DomNode(tag='div')  # No attributes
        >>> child = DomNode(tag='button', attrib={'role': 'button'})
        >>> wrapper.add_child(child)
        >>> collapsed = collapse_single_child_wrappers(wrapper)
        >>> collapsed.tag
        'button'
    """
    # Recursively process children first
    new_children = []
    for child in node.children:
        if isinstance(child, Text):
            new_children.append(Text(child.content))
        elif isinstance(child, DomNode):
            collapsed_child = collapse_single_child_wrappers(child)
            new_children.append(collapsed_child)

    # Check if this is a wrapper to collapse
    has_attributes = bool(node.attrib)
    element_children = [c for c in new_children if isinstance(c, DomNode)]
    text_children = [c for c in new_children if isinstance(c, Text)]

    # Collapse if:
    # - No attributes
    # - Exactly one element child
    # - No text content (or only whitespace)
    has_meaningful_text = any(c.content.strip() for c in text_children)

    if not has_attributes and len(element_children) == 1 and not has_meaningful_text:
        # Promote the child
        return element_children[0]

    # Otherwise, keep this node
    new_node = node.copy()

    for child in new_children:
        new_node.add_child(child)

    return new_node
