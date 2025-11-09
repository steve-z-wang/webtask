"""DOM knowledge functions - pure predicates about HTML elements.

All functions in this module are pure functions that answer questions about DOM elements
based on web standards (HTML, ARIA, etc.). They don't modify anything, just return True/False.
"""

from .interactive import is_interactive
from .semantic import has_semantic_value, is_presentational_role, is_semantic_attribute
from .rendering import is_not_rendered, should_keep_when_not_rendered

__all__ = [
    "is_interactive",
    "should_keep_when_not_rendered",
    "is_presentational_role",
    "has_semantic_value",
    "is_not_rendered",
    "is_semantic_attribute",
]
