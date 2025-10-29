"""Configuration for DOM context processing and filtering."""

from dataclasses import dataclass, field
from typing import Set, Optional


@dataclass
class DomContextConfig:
    """
    Configuration for how DOM snapshots are filtered and processed for LLM context.

    Controls each filtering step individually with fine-grained options.

    Examples:
        >>> # Default config (standard filtering)
        >>> config = DomContextConfig()
        >>> agent = Agent(llm, page, dom_context_config=config)

        >>> # Add data-test attribute for Poshmark
        >>> config = DomContextConfig(
        ...     kept_attributes={
        ...         "role", "type", "name", "placeholder", "value",
        ...         "data-test"  # Poshmark uses this
        ...     }
        ... )

        >>> # Disable specific filters
        >>> config = DomContextConfig(
        ...     filter_zero_dimensions=False,
        ...     collapse_wrappers=False
        ... )
    """

    # ==========================================
    # Visibility Filters
    # ==========================================

    filter_non_visible_tags: bool = True
    """Remove non-visible tags (script, style, head, meta, link, title, noscript)."""

    non_visible_tags: Set[str] = field(default_factory=lambda: {
        "script", "style", "head", "meta", "link", "title", "noscript"
    })
    """Tags to remove when filter_non_visible_tags=True. Customize for specific sites."""

    filter_css_hidden: bool = True
    """Remove elements with display:none, visibility:hidden, or opacity:0."""

    filter_zero_dimensions: bool = True
    """Remove elements with zero width or height (except positioned popups)."""

    # ==========================================
    # Attribute Filters
    # ==========================================

    filter_attributes: bool = True
    """Keep only semantic attributes, remove presentational ones (class, style, etc.)."""

    kept_attributes: Set[str] = field(default_factory=lambda: {
        "role",
        "aria-label",
        "aria-labelledby",
        "aria-describedby",
        "aria-checked",
        "aria-selected",
        "aria-expanded",
        "aria-hidden",
        "aria-disabled",
        "type",
        "name",
        "placeholder",
        "value",
        "alt",
        "title",
        "href",
        "disabled",
        "checked",
        "selected",
    })
    """Attributes to keep when filter_attributes=True. Add site-specific attributes."""

    # ==========================================
    # Semantic Filters
    # ==========================================

    filter_presentational_roles: bool = True
    """Remove elements with role='none' or role='presentation'."""

    filter_empty: bool = True
    """Remove empty nodes (no attributes, no children, no meaningful text)."""

    collapse_wrappers: bool = True
    """Collapse single-child wrapper elements (like <div><button>...</button></div>)."""
