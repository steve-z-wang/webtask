"""Browser module - Abstract base classes for browser automation."""

from .browser import Browser
from .session import Session
from .page import Page
from .element import Element
from .cookies import Cookie, Cookies

__all__ = [
    "Browser",
    "Session",
    "Page",
    "Element",
    "Cookie",
    "Cookies",
]
