"""Integration module - Concrete implementations for browsers and LLMs."""

from .browser import (
    PlaywrightBrowser,
    PlaywrightContext,
    PlaywrightPage,
    PlaywrightElement,
)

from .llm import (
    Gemini,
)

__all__ = [
    # Playwright
    "PlaywrightBrowser",
    "PlaywrightContext",
    "PlaywrightPage",
    "PlaywrightElement",
    # LLM
    "Gemini",
]
