"""Knowledge: Determine if elements are rendered by the browser.

Pure function that answers: "Did CDP include this element in the render tree?"
Based on presence of layout data (bounds and styles) from Chrome DevTools Protocol.
"""

from ...dom.domnode import DomNode


def is_not_rendered(node: DomNode) -> bool:
    """Check if element is not rendered (no layout data from CDP).

    CDP only provides layout data (bounds and computed styles) for elements
    in the browser's render tree. Elements with display:none, hidden attribute,
    or not attached to DOM will have no layout data.

    Args:
        node: DOM node to check

    Returns:
        True if element has no layout data (not rendered), False otherwise

    Example:
        >>> # Visible element with layout data
        >>> node = DomNode(tag="div", styles={"display": "block"}, bounds=BoundingBox(...))
        >>> is_not_rendered(node)
        False

        >>> # Hidden element with no layout data
        >>> node = DomNode(tag="div", styles={}, bounds=None)
        >>> is_not_rendered(node)
        True
    """
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None

    # Element is "not rendered" if CDP gave us no layout data
    return not has_styles and not has_bounds
