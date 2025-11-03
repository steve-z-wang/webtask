"""DOM filters - transform DOM trees by removing or modifying elements.

All filters in this module take a DomNode and return a transformed version.
They use knowledge functions from dom_processing.knowledge to make decisions.
"""

from .filter_not_rendered import filter_not_rendered
from .filter_presentational import filter_presentational_roles
from .filter_empty import filter_empty
from .filter_attributes import filter_attributes
from .filter_wrappers import collapse_single_child_wrappers

__all__ = [
    "filter_not_rendered",
    "filter_presentational_roles",
    "filter_empty",
    "filter_attributes",
    "collapse_single_child_wrappers",
]
