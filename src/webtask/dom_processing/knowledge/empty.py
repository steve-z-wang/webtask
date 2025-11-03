"""Knowledge: Determine if elements are semantically empty.

Pure function that answers: "Is this element empty and useless?"
An element is empty if it has no content, no attributes, and no semantic purpose.
"""

from ...dom.domnode import DomNode
from .interactive import is_interactive


def is_empty_element(node: DomNode, filtered_children: list) -> bool:
    """Check if an element is semantically empty and can be removed.

    An element is considered empty if ALL of these are true:
    - No attributes (no class, id, data-*, etc.)
    - No children (after filtering)
    - Not interactive (buttons, inputs, etc. kept even if empty)

    Args:
        node: DOM node to check
        filtered_children: List of children after recursive filtering

    Returns:
        True if element is empty and can be removed, False otherwise

    Example:
        >>> # Empty div with no attributes - can remove
        >>> node = DomNode(tag="div")
        >>> is_empty_element(node, filtered_children=[])
        True

        >>> # Empty div with class attribute - keep it
        >>> node = DomNode(tag="div", attrib={"class": "foo"})
        >>> is_empty_element(node, filtered_children=[])
        False

        >>> # Empty button - keep it (interactive)
        >>> node = DomNode(tag="button")
        >>> is_empty_element(node, filtered_children=[])
        False
    """
    has_attributes = bool(node.attrib)
    has_children = len(filtered_children) > 0
    is_interactive_elem = is_interactive(node)

    # Element is empty if: no attributes AND no children AND not interactive
    return not has_attributes and not has_children and not is_interactive_elem
