"""VerifierBrowser - simplified browser wrapper for verification without element interaction."""

import base64
from ..session_browser import SessionBrowser
from ...context import LLMDomContext


class VerifierBrowser:
    """Verifier-specific browser for observation only."""

    def __init__(self, session_browser: SessionBrowser):
        self._session_browser = session_browser

    async def get_dom_snapshot(self) -> str:
        """Get DOM snapshot without interactive IDs."""

        # Wait for page to be fully loaded before capturing (safety check)
        await self._session_browser.wait_for_load(timeout=10000)

        page = self._session_browser.get_current_page()
        if page is None:
            return "ERROR: No page opened yet."

        # Build LLMDomContext without interactive IDs
        dom_context = await LLMDomContext.from_page(page, include_element_ids=False)
        context_str = dom_context.get_context()

        # Format with URL
        url = page.url
        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        if not context_str:
            lines.append("ERROR: No visible content found on this page.")
            lines.append("")
            lines.append("Possible causes:")
            lines.append("- The page is still loading")
            lines.append("- The page has no visible content")
            lines.append("- All content was filtered out")
        else:
            lines.append(context_str)

        return "\n".join(lines)

    async def get_screenshot(self, full_page: bool = False) -> str:
        """Get screenshot as base64 string."""
        # Wait for page to be fully loaded before capturing (safety check)
        await self._session_browser.wait_for_load(timeout=10000)

        screenshot_bytes = await self._session_browser.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def get_current_url(self) -> str:
        """Get current page URL."""
        page = self._session_browser.get_current_page()
        return page.url if page else "about:blank"
