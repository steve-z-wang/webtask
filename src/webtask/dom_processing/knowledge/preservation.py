"""Knowledge: Determine if hidden elements should be preserved.

Pure function that answers: "Should we keep this element even when it's hidden (display:none)?"
This is separate from interactivity - elements can be non-interactive but functionally important.
"""

from ...dom.domnode import DomNode


def should_keep_when_not_rendered(node: DomNode) -> bool:
    """Check if a hidden element should be kept in the DOM tree.

    This function determines if elements that are not rendered (display:none, etc.)
    should still be preserved in the filtered DOM for the LLM.

    Elements to keep when hidden:
    - File inputs (almost always hidden with display:none, but critical for uploads)
    - Hidden form inputs (carry data in forms, not interactive but functionally important)

    Args:
        node: DOM node that has no styles/bounds from CDP (not rendered)

    Returns:
        True if element should be kept despite being hidden, False to remove

    Example:
        >>> # File input - always keep
        >>> node = DomNode(tag="input", attrib={"type": "file"})
        >>> should_keep_when_not_rendered(node)
        True

        >>> # Hidden input - always keep
        >>> node = DomNode(tag="input", attrib={"type": "hidden"})
        >>> should_keep_when_not_rendered(node)
        True

        >>> # Regular div - don't keep when hidden
        >>> node = DomNode(tag="div")
        >>> should_keep_when_not_rendered(node)
        False
    """
    tag = node.tag
    input_type = node.attrib.get("type", "").lower()

    # File inputs - almost always hidden with display:none but critical for uploads
    if tag == "input" and input_type == "file":
        return True

    # Hidden inputs - carry form data, not interactive but functionally important
    if tag == "input" and input_type == "hidden":
        return True

    # For now, only keep these critical cases
    # Can expand if we discover other patterns
    return False
