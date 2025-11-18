"""Browser module - Abstract base classes for browser automation."""

from .browser import Browser
from .context import Context
from .page import Page
from .element import Element
from .cookies import Cookie, Cookies

__all__ = [
    "Browser",
    "Context",
    "Page",
    "Element",
    "Cookie",
    "Cookies",
]
