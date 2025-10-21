"""Semantic filters for DOM nodes."""

from .attributes import filter_attributes, SEMANTIC_ATTRIBUTES
from .empty import filter_empty, INTERACTIVE_TAGS
from .wrappers import collapse_single_child_wrappers
from .presentational import filter_presentational_roles

__all__ = [
    'filter_attributes',
    'filter_empty',
    'collapse_single_child_wrappers',
    'filter_presentational_roles',
    'SEMANTIC_ATTRIBUTES',
    'INTERACTIVE_TAGS',
]
