"""Collapse single-child wrapper elements."""

from ....dom.domnode import DomNode, Text
from ....dom.utils import is_interactive_element


def collapse_single_child_wrappers(node: DomNode) -> DomNode:
    """Collapse single-child wrapper elements.

    Never collapses interactive elements (based on web standards) since they
    have semantic meaning that should be preserved for the LLM.
    """
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

    # Never collapse interactive elements - they have semantic meaning
    is_interactive = is_interactive_element(node)

    if (
        not has_attributes
        and len(element_children) == 1
        and not has_meaningful_text
        and not is_interactive
    ):
        return element_children[0]

    new_node = node.copy()

    for child in new_children:
        new_node.add_child(child)

    return new_node
