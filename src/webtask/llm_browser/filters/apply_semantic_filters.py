"""Apply all semantic filters."""

from typing import Optional
from ...dom.domnode import DomNode
from ..dom_filter_config import DomFilterConfig
from .semantic import (
    filter_attributes,
    filter_empty,
    collapse_single_child_wrappers,
    filter_presentational_roles,
)


def apply_semantic_filters(
    node: DomNode, config: Optional[DomFilterConfig] = None
) -> Optional[DomNode]:
    """Apply all semantic filters based on config."""
    if config is None:
        config = DomFilterConfig()

    result = node

    if config.filter_attributes and result is not None:
        result = filter_attributes(result, config.kept_attributes)

    if config.filter_presentational_roles and result is not None:
        result = filter_presentational_roles(result)

    if config.filter_empty and result is not None:
        result = filter_empty(result, config.interactive_tags)

    if config.collapse_wrappers and result is not None:
        result = collapse_single_child_wrappers(result)

    return result
