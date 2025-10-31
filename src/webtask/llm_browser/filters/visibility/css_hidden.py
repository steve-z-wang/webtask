"""Remove CSS-hidden elements."""

from typing import Optional
from ....dom.domnode import DomNode, Text


def filter_css_hidden(node: DomNode) -> Optional[DomNode]:
    """Remove CSS-hidden elements."""
    display = node.styles.get("display", "").lower()
    visibility = node.styles.get("visibility", "").lower()
    opacity = node.styles.get("opacity", "1")

    if display == "none":
        return None
    if visibility == "hidden":
        return None
    try:
        if float(opacity) == 0:
            return None
    except (ValueError, TypeError):
        pass

    if "hidden" in node.attrib:
        return None

    if node.tag == "input" and node.attrib.get("type", "").lower() == "hidden":
        return None

    new_node = node.copy()

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_css_hidden(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
