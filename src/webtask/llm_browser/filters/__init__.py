"""
Filters for LLM context building.

Import main filters:
    from webtask.llm_browser.filters import apply_visibility_filters, apply_semantic_filters

Or import specific filters:
    from webtask.llm_browser.filters.visibility import filter_css_hidden
    from webtask.llm_browser.filters.semantic import filter_attributes
"""

from .apply_visibility_filters import apply_visibility_filters
from .apply_semantic_filters import apply_semantic_filters

__all__ = [
    "apply_visibility_filters",
    "apply_semantic_filters",
]
