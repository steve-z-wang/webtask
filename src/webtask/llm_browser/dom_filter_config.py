"""Configuration for DOM filtering."""

from dataclasses import dataclass, field
from typing import Set, Optional


@dataclass
class DomFilterConfig:
    """Configuration for DOM filtering."""

    filter_non_visible_tags: bool = True
    non_visible_tags: Set[str] = field(default_factory=lambda: {
        "script", "style", "head", "meta", "link", "title", "noscript"
    })
    filter_css_hidden: bool = True
    filter_no_layout: bool = True
    filter_zero_dimensions: bool = True

    filter_attributes: bool = True
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
        "disabled",
        "checked",
        "selected",
    })

    filter_presentational_roles: bool = True
    filter_empty: bool = True
    interactive_tags: Set[str] = field(default_factory=lambda: {
        "a", "button", "input", "select", "textarea", "label"
    })
    interactive_roles: Set[str] = field(default_factory=lambda: {
        "button", "link", "checkbox", "radio", "switch", "tab",
        "menuitem", "menuitemcheckbox", "menuitemradio", "option",
        "textbox", "searchbox", "combobox", "slider", "spinbutton"
    })
    collapse_wrappers: bool = True
