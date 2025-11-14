"""PageContextBuilder - builds page context string with DOM text."""

from typing import Dict, Optional, Tuple
from webtask.browser import Page
from .dom_context_builder import DomContextBuilder


class PageContextBuilder:

    @staticmethod
    async def build(
        page: Page,
        include_element_ids: bool = False,
        with_bounding_boxes: bool = False,
        full_page_screenshot: bool = False,
    ) -> Tuple[str, Optional[Dict]]:
        """Build page context string with DOM text.

        Returns:
            Tuple of (context_string, optional element_map if include_element_ids=True)
        """
        if page is None:
            return "ERROR: No page is currently open.", None

        url = page.url
        context_str, element_map = await DomContextBuilder.build_context(
            page=page, include_element_ids=include_element_ids
        )

        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        if context_str is None:
            lines.append("ERROR: No visible interactive elements found on this page.")
            lines.append("")
            lines.append("Possible causes:")
            lines.append("- The page is still loading")
            lines.append("- The page has no interactive elements")
            lines.append("- All elements were filtered out")
        else:
            lines.append(context_str)

        return "\n".join(lines), element_map if include_element_ids else None
