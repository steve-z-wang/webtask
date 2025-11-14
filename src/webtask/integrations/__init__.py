"""Integration module - Concrete implementations for browsers and LLMs."""

from .browser import (
    PlaywrightBrowser,
    PlaywrightSession,
    PlaywrightPage,
    PlaywrightElement,
)

from .llm import (
    GeminiLLM,
)

__all__ = [
    # Playwright
    "PlaywrightBrowser",
    "PlaywrightSession",
    "PlaywrightPage",
    "PlaywrightElement",
    # LLM
    "GeminiLLM",
]
