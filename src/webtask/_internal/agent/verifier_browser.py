"""VerifierBrowser - simplified browser wrapper for verification without element interaction."""

from .agent_browser import AgentBrowser
from ..page_context.dom_context_builder import DomContextBuilder


class VerifierBrowser:
    """Verifier-specific browser for observation only.

    Wraps AgentBrowser and provides read-only access to page state.
    Verifier only observes - no element mapping or interaction needed.
    """

    def __init__(self, agent_browser: AgentBrowser):
        """Initialize VerifierBrowser.

        Args:
            agent_browser: Shared AgentBrowser instance
        """
        self._agent_browser = agent_browser

    async def get_dom_snapshot(self) -> str:
        """Get DOM snapshot as formatted string without element IDs.

        Verifier only needs to read the page state, not interact with elements.

        Returns:
            Formatted DOM snapshot string with URL and page content
        """
        page = self._agent_browser.get_current_page()
        if page is None:
            return "ERROR: No page opened yet."

        # Wait for page to be idle before capturing context (max 5s)
        await page.wait_for_idle(timeout=5000)

        # Build DOM context without element IDs
        context_str, _ = await DomContextBuilder.build_context(
            page=page, include_element_ids=False
        )

        # Format with URL
        url = page.url
        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        if context_str is None:
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
        """Get screenshot as base64 string.

        Args:
            full_page: Whether to capture full page screenshot

        Returns:
            Base64-encoded screenshot string, or empty string if no page
        """
        import base64

        page = self._agent_browser.get_current_page()
        if page is None:
            return ""

        # Get screenshot bytes
        screenshot_bytes = await page.screenshot(full_page=full_page)

        # Convert to base64
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def get_current_url(self) -> str:
        """Get current page URL.

        Returns:
            Current URL or "about:blank" if no page
        """
        page = self._agent_browser.get_current_page()
        return page.url if page else "about:blank"
