"""Configuration for DOM filtering."""

from dataclasses import dataclass, field
from typing import Set


@dataclass
class DomFilterConfig:
    """Configuration for DOM filtering.

    Visibility Filtering Philosophy:
    - Only use filter_not_rendered - if CDP didn't include it in the render tree, remove it
    - Trust CDP's rendering decisions - it already excludes script, style, display:none, etc.
    - Don't filter by CSS properties - interactive elements may use opacity:0, etc.
    """

    # ACTIVE FILTER: Remove elements not in CDP's render tree
    filter_not_rendered: bool = True

    # DEPRECATED FILTERS (kept for backwards compatibility, not used):
    # - filter_non_visible_tags: CDP already excludes <script>, <style>, etc.
    # - filter_css_hidden: Too aggressive, removes opacity:0 file inputs
    # - filter_zero_dimensions: Too aggressive, removes hidden interactive elements

    filter_attributes: bool = True
    kept_attributes: Set[str] = field(
        default_factory=lambda: {
            "role",
            "aria-label",
            "aria-labelledby",
            "aria-describedby",
            "aria-checked",
            "aria-selected",
            "aria-expanded",
            "aria-hidden",
            "aria-disabled",
            "aria-haspopup",  # Indicates interactive popup/menu elements
            "tabindex",  # Indicates keyboard focusable elements
            "onclick",  # Indicates click handler
            "type",
            "name",
            "placeholder",
            "value",
            "alt",
            "title",
            "disabled",
            "checked",
            "selected",
        }
    )

    filter_presentational_roles: bool = True
    filter_empty: bool = True
    collapse_wrappers: bool = True
