"""Selector utilities for browser element selection."""


class XPath:
    """XPath selector for browser element selection."""

    def __init__(self, path: str):
        self.path = path

    def for_playwright(self) -> str:
        """Convert to Playwright locator format."""
        return f"xpath={self.path}"

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"XPath({self.path!r})"
