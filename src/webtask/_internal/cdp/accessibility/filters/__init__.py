"""Filters for accessibility trees.

Filters remove or transform nodes in the accessibility tree based on criteria.
"""

from .filter_by_predicate import filter_by_predicate
from .filter_ignored import filter_ignored_nodes
from .filter_duplicate_names import filter_duplicate_names
from .filter_generic import filter_generic_nodes
from .filter_none import filter_none_nodes

__all__ = [
    "filter_by_predicate",
    "filter_ignored_nodes",
    "filter_duplicate_names",
    "filter_generic_nodes",
    "filter_none_nodes",
]
