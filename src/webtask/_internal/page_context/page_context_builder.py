"""PageContextBuilder - builds page context blocks with text and image."""

from typing import Dict, Optional, Tuple
from webtask._internal.llm import Block
from webtask._internal.media import Image
from webtask.browser import Page
from .dom_context_builder import DomContextBuilder


class PageContextBuilder:

    @staticmethod
    async def build(
        page: Page,
        include_element_ids: bool = False,
        with_bounding_boxes: bool = False,
        full_page_screenshot: bool = False,
    ) -> Tuple[Block, Optional[Dict]]:
        """Build page context block with text and screenshot.

        Returns:
            Tuple of (Block with text+image, optional element_map if include_element_ids=True)
        """
        if page is None:
            block = Block(
                heading="Current Page", content="ERROR: No page is currently open."
            )
            return block, None

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

        screenshot_bytes = await page.screenshot(full_page=full_page_screenshot)

        if with_bounding_boxes and element_map:
            from .bounding_box_renderer import BoundingBoxRenderer
            from ..dom_processing.knowledge import is_interactive

            # Filter to only interactive elements for bounding boxes
            interactive_map = {
                elem_id: node
                for elem_id, node in element_map.items()
                if is_interactive(node)
            }
            screenshot_bytes = await BoundingBoxRenderer.render(page, interactive_map)

        image = Image(screenshot_bytes)
        block = Block(heading="Current Page", content="\n".join(lines), image=image)

        return block, element_map if include_element_ids else None
