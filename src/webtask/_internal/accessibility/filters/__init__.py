"""Filters for accessibility trees.

Filters remove or transform nodes in the accessibility tree based on criteria.
"""

from .filter_ignored import filter_ignored_nodes
from .filter_duplicate_names import filter_duplicate_text
from .filter_non_semantic_role import filter_non_semantic_role

__all__ = [
    "filter_ignored_nodes",
    "filter_duplicate_text",
    "filter_non_semantic_role",
]
