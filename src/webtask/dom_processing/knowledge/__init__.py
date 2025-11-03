"""DOM knowledge functions - pure predicates about HTML elements.

All functions in this module are pure functions that answer questions about DOM elements
based on web standards (HTML, ARIA, etc.). They don't modify anything, just return True/False.
"""

from .interactive import is_interactive
from .preservation import should_keep_when_not_rendered
from .presentational import is_presentational_role
from .empty import is_empty_element
from .rendering import is_not_rendered
from .attributes import is_semantic_attribute

__all__ = [
    "is_interactive",
    "should_keep_when_not_rendered",
    "is_presentational_role",
    "is_empty_element",
    "is_not_rendered",
    "is_semantic_attribute",
]
