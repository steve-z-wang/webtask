"""DOM filters - transform DOM trees by removing or modifying elements.

All filters in this module take a DomNode and return a transformed version.
They use knowledge functions from dom_processing.knowledge to make decisions.
"""

from .filter_non_rendered import filter_non_rendered
from .filter_non_semantic import filter_non_semantic

__all__ = [
    "filter_non_rendered",
    "filter_non_semantic",
]
