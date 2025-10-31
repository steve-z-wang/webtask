"""Apply all visibility filters."""

from typing import Optional
from ..domnode import DomNode
from ..dom_context_config import DomContextConfig
from .visibility import filter_non_visible_tags, filter_css_hidden, filter_no_layout, filter_zero_dimensions


def apply_visibility_filters(
    node: DomNode, config: Optional[DomContextConfig] = None
) -> Optional[DomNode]:
    """Apply all visibility filters based on config."""
    if config is None:
        config = DomContextConfig()

    result = node

    if config.filter_non_visible_tags and result is not None:
        result = filter_non_visible_tags(result, config.non_visible_tags)

    if config.filter_css_hidden and result is not None:
        result = filter_css_hidden(result)

    if config.filter_no_layout and result is not None:
        result = filter_no_layout(result)

    if config.filter_zero_dimensions and result is not None:
        result = filter_zero_dimensions(result)

    return result
