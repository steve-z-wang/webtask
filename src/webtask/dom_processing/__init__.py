"""DOM processing - knowledge, filters, and serializers for DOM manipulation.

This module contains all DOM processing logic:
- knowledge/: Pure functions answering questions about DOM elements
- filters/: Functions that transform DOM trees
- serializers/: Functions that convert DOM trees to output formats
"""

# Main sub-modules (users can import from these)
from . import knowledge
from . import filters
from . import serializers

__all__ = [
    "knowledge",
    "filters",
    "serializers",
]
