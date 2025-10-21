"""Apply all semantic filters."""

from typing import Optional
from ..domnode import DomNode
from .semantic import (
    filter_attributes,
    filter_empty,
    collapse_single_child_wrappers,
    filter_presentational_roles,
)


def apply_semantic_filters(node: DomNode) -> Optional[DomNode]:
    """
    Apply all semantic filters.

    - Keeps only semantic attributes (role, aria-*, type, name, etc.)
    - Filters presentational roles (removes role='none' or role='presentation')
    - Removes empty nodes (no attributes, no children)
    - Collapses single-child wrapper elements

    Args:
        node: DomNode to filter

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
    result = filter_attributes(node)
    result = filter_presentational_roles(result) if result is not None else None
    result = filter_empty(result) if result is not None else None
    result = collapse_single_child_wrappers(result) if result is not None else None
    return result
