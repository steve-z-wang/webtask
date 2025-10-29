"""Apply all visibility filters."""

from typing import Optional
from ..domnode import DomNode
from ..dom_context_config import DomContextConfig
from .visibility import filter_non_visible_tags, filter_css_hidden, filter_zero_dimensions


def apply_visibility_filters(
    node: DomNode, config: Optional[DomContextConfig] = None
) -> Optional[DomNode]:
    """
    Apply all visibility filters based on config.

    Removes:
    - Non-visible tags (script, style, head, meta, etc.)
    - CSS-hidden elements (display:none, visibility:hidden, opacity:0)
    - Zero-dimension elements (except positioned popups)

    Args:
        node: DomNode to filter
        config: Configuration for filtering. If None, uses default config.

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
    if config is None:
        config = DomContextConfig()

    result = node

    # Apply each filter based on config
    if config.filter_non_visible_tags and result is not None:
        result = filter_non_visible_tags(result, config.non_visible_tags)

    if config.filter_css_hidden and result is not None:
        result = filter_css_hidden(result)

    if config.filter_zero_dimensions and result is not None:
        result = filter_zero_dimensions(result)

    return result
