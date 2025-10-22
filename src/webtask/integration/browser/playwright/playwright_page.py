"""Playwright page implementation."""

from typing import Dict, Any, List
from playwright.async_api import Page as PlaywrightPageType
from ....browser import Page


class PlaywrightPage(Page):
    """
    Playwright implementation of Page.

    Wraps Playwright's Page for page management.
    """

    def __init__(self, page: PlaywrightPageType):
        """
        Initialize PlaywrightPage.

        Args:
            page: Playwright Page instance
        """
        self._page = page

    async def navigate(self, url: str):
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        await self._page.goto(url)

    async def get_cdp_snapshot(self) -> Dict[str, Any]:
        """
        Get a CDP (Chrome DevTools Protocol) snapshot of the current page.

        Returns:
            CDP snapshot data (raw dictionary from DOMSnapshot.captureSnapshot)
        """
        # Get CDP session
        cdp = await self._page.context.new_cdp_session(self._page)

        # Capture snapshot
        snapshot = await cdp.send('DOMSnapshot.captureSnapshot', {
            'computedStyles': ['display', 'visibility', 'opacity'],
            'includePaintOrder': True,
            'includeDOMRects': True
        })

        return snapshot

    async def select(self, selector: str) -> List['PlaywrightElement']:
        """
        Select all elements matching the selector.

        Args:
            selector: CSS selector or XPath string

        Returns:
            List of PlaywrightElement (may be empty)
        """
        from .playwright_element import PlaywrightElement

        elements = await self._page.query_selector_all(selector)
        return [PlaywrightElement(el) for el in elements]

    async def select_one(self, selector: str) -> 'PlaywrightElement':
        """
        Select a single element matching the selector.

        Args:
            selector: CSS selector or XPath string

        Returns:
            Single PlaywrightElement

        Raises:
            ValueError: If no elements match or multiple elements match
        """
        from .playwright_element import PlaywrightElement

        elements = await self._page.query_selector_all(selector)

        if len(elements) == 0:
            raise ValueError(f"No elements found matching selector: {selector}")
        elif len(elements) > 1:
            raise ValueError(f"Multiple elements ({len(elements)}) found matching selector: {selector}")

        return PlaywrightElement(elements[0])

    async def close(self):
        """Close the page."""
        await self._page.close()

    @property
    def url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL of the page
        """
        return self._page.url
