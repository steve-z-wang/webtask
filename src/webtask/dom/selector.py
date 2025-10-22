"""Selector utilities for browser element selection."""


class XPath:
    """
    Represents an XPath selector.

    XPath is a W3C standard for selecting elements in XML/HTML documents.
    This class encapsulates an XPath string and provides methods to format it
    for different browser automation tools.
    """

    def __init__(self, path: str):
        """
        Initialize XPath.

        Args:
            path: XPath string (e.g., "/html/body/div[1]/button[2]")
        """
        self.path = path

    def for_playwright(self) -> str:
        """
        Convert to Playwright locator format.

        Returns:
            Playwright locator string (e.g., "xpath=/html/body/div")
        """
        return f"xpath={self.path}"

    def __str__(self) -> str:
        """String representation (returns raw XPath)."""
        return self.path

    def __repr__(self) -> str:
        """Developer representation."""
        return f"XPath({self.path!r})"
