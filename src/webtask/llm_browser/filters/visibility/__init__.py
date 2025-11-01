"""Visibility filters for DOM nodes.

Only one filter is used:
- filter_not_rendered: Remove elements not in CDP's render tree (no layout data)

CDP already handles visibility - if it didn't render it, we don't show it to the LLM.
"""

from .not_rendered import filter_not_rendered

__all__ = [
    "filter_not_rendered",
]
