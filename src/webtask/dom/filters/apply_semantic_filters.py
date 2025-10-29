"""Apply all semantic filters."""

from typing import Optional
from ..domnode import DomNode
from ..dom_context_config import DomContextConfig
from .semantic import (
    filter_attributes,
    filter_empty,
    collapse_single_child_wrappers,
    filter_presentational_roles,
)


def apply_semantic_filters(
    node: DomNode, config: Optional[DomContextConfig] = None
) -> Optional[DomNode]:
    """
    Apply all semantic filters based on config.

    - Keeps only semantic attributes (role, aria-*, type, name, etc.)
    - Filters presentational roles (removes role='none' or role='presentation')
    - Removes empty nodes (no attributes, no children)
    - Collapses single-child wrapper elements

    Args:
        node: DomNode to filter
        config: Configuration for filtering. If None, uses default config.

    Returns:
        Filtered DomNode with clean semantic structure, or None if all removed

    Example:
        >>> node = DomNode(tag='div', attrib={'class': 'wrapper', 'role': 'button'})
        >>> child = DomNode(tag='span', attrib={'id': 'x'})
        >>> node.add_child(child)
        >>> filtered = apply_semantic_filters(node)
        >>> filtered.attrib
        {'role': 'button'}
    """
    if config is None:
        config = DomContextConfig()

    result = node

    # Apply each filter based on config
    if config.filter_attributes and result is not None:
        result = filter_attributes(result, config.kept_attributes)

    if config.filter_presentational_roles and result is not None:
        result = filter_presentational_roles(result)

    if config.filter_empty and result is not None:
        result = filter_empty(result)

    if config.collapse_wrappers and result is not None:
        result = collapse_single_child_wrappers(result)

    return result
