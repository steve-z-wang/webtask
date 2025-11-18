"""Browser integrations."""

from .playwright import (
    PlaywrightBrowser,
    PlaywrightContext,
    PlaywrightPage,
    PlaywrightElement,
)

__all__ = [
    "PlaywrightBrowser",
    "PlaywrightContext",
    "PlaywrightPage",
    "PlaywrightElement",
]
