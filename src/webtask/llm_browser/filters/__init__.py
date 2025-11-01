"""
Filters for LLM context building.

Import individual filters:
    from webtask.llm_browser.filters.visibility import filter_not_rendered
    from webtask.llm_browser.filters.semantic import (
        filter_attributes,
        filter_presentational_roles,
        filter_empty,
        collapse_single_child_wrappers,
    )

Filters are applied directly in DomContextBuilder.
"""

from .visibility import filter_not_rendered
from .semantic import (
    filter_attributes,
    filter_presentational_roles,
    filter_empty,
    collapse_single_child_wrappers,
)

__all__ = [
    # Visibility filters
    "filter_not_rendered",
    # Semantic filters
    "filter_attributes",
    "filter_presentational_roles",
    "filter_empty",
    "collapse_single_child_wrappers",
]
