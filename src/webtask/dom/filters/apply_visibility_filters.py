"""Apply all visibility filters."""

from typing import Optional
from ..domnode import DomNode
from .visibility import filter_non_visible_tags, filter_css_hidden, filter_zero_dimensions


def apply_visibility_filters(node: DomNode) -> Optional[DomNode]:
    """
    Apply all visibility filters.

    Removes:
    - Non-visible tags (script, style, head, meta, etc.)
    - CSS-hidden elements (display:none, visibility:hidden, opacity:0)
    - Zero-dimension elements (except positioned popups)

    Args:
        node: DomNode to filter

    Returns:
        Filtered DomNode with only visible elements, or None if all removed

    Example:
        >>> from webtask.dom.parsers import parse_html
        >>> from webtask.dom.filters import apply_visibility_filters
        >>> html = '<div><script>x</script><button>Click</button></div>'
        >>> root = parse_html(html)
        >>> filtered = apply_visibility_filters(root)
        >>> len(filtered.children)  # Only button remains
        1
    """
    result = filter_non_visible_tags(node)
    if result is not None:
        result = filter_css_hidden(result)
    if result is not None:
        result = filter_zero_dimensions(result)
    return result
