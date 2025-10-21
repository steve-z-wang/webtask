"""Remove CSS-hidden elements (display:none, visibility:hidden, opacity:0)."""

from typing import Optional
from ...domnode import DomNode, Text


def filter_css_hidden(node: DomNode) -> Optional[DomNode]:
    """
    Remove CSS-hidden elements (display:none, visibility:hidden, opacity:0).

    Also removes:
    - Elements with hidden attribute
    - <input type="hidden">

    Args:
        node: DomNode to filter

    Returns:
        New DomNode without CSS-hidden elements, or None if node itself is hidden

    Example:
        >>> div = DomNode(tag='div', styles={'display': 'none'})
        >>> filtered = filter_css_hidden(div)
        >>> filtered is None
        True
    """
    # Check computed styles
    display = node.styles.get("display", "").lower()
    visibility = node.styles.get("visibility", "").lower()
    opacity = node.styles.get("opacity", "1")

    # Filter CSS-hidden elements
    if display == "none":
        return None
    if visibility == "hidden":
        return None
    try:
        if float(opacity) == 0:
            return None
    except (ValueError, TypeError):
        pass

    # Check hidden attribute
    if "hidden" in node.attrib:
        return None

    # Check for hidden input
    if node.tag == "input" and node.attrib.get("type", "").lower() == "hidden":
        return None

    # Create new node
    new_node = node.copy()

    # Recursively filter children
    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_css_hidden(child)
            if filtered_child is not None:
                new_node.add_child(filtered_child)

    return new_node
