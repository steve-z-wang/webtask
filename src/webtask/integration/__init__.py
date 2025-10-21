"""Integration module - Concrete implementations for browsers and LLMs."""

from .browser import (
    PlaywrightBrowser,
    PlaywrightSession,
    PlaywrightPage,
    PlaywrightElement,
)

from .llm import (
    OpenAILLM,
    GeminiLLM,
)

__all__ = [
    # Playwright
    'PlaywrightBrowser',
    'PlaywrightSession',
    'PlaywrightPage',
    'PlaywrightElement',

    # LLM
    'OpenAILLM',
    'GeminiLLM',
]
