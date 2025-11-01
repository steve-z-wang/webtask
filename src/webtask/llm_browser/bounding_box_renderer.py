"""BoundingBoxRenderer - visualizes element_map with bounding boxes."""

from typing import Dict
from ..browser import Page
from ..dom.domnode import DomNode
from ..media import Image


class BoundingBoxRenderer:
    """Renders screenshots with bounding boxes and element IDs using browser-side drawing."""

    @staticmethod
    def _generate_draw_script(
        element_map: Dict[str, DomNode],
        color: str,
        line_width: int,
        font_size: int,
    ) -> str:
        """Generate JavaScript to draw bounding boxes in the browser."""

        # Build element data for JavaScript
        elements_data = []
        for element_id, node in element_map.items():
            xpath = str(node.get_x_path())  # Convert XPath object to string
            elements_data.append(f'{{"id": "{element_id}", "xpath": {repr(xpath)}}}')

        elements_json = "[" + ", ".join(elements_data) + "]"

        script = f"""
        (() => {{
            // Create overlay container
            const overlay = document.createElement('div');
            overlay.id = '__webtask_bbox_overlay__';
            overlay.style.position = 'absolute';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.pointerEvents = 'none';
            overlay.style.zIndex = '999999';
            document.body.appendChild(overlay);

            const elements = {elements_json};

            elements.forEach(item => {{
                // Find element by XPath
                const result = document.evaluate(
                    item.xpath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                );
                const element = result.singleNodeValue;

                if (!element) return;

                // Get element bounds
                const rect = element.getBoundingClientRect();
                const scrollX = window.scrollX || window.pageXOffset;
                const scrollY = window.scrollY || window.pageYOffset;

                // Create box div
                const box = document.createElement('div');
                box.style.position = 'absolute';
                box.style.left = (rect.left + scrollX) + 'px';
                box.style.top = (rect.top + scrollY) + 'px';
                box.style.width = rect.width + 'px';
                box.style.height = rect.height + 'px';
                box.style.border = '{line_width}px solid {color}';
                box.style.boxSizing = 'border-box';
                box.style.pointerEvents = 'none';
                overlay.appendChild(box);

                // Create label div
                const label = document.createElement('div');
                label.textContent = item.id;
                label.style.position = 'absolute';
                label.style.backgroundColor = '{color}';
                label.style.color = 'white';
                label.style.fontSize = '{font_size}px';
                label.style.fontFamily = 'monospace';
                label.style.fontWeight = 'bold';
                label.style.padding = '2px 6px';
                label.style.pointerEvents = 'none';
                label.style.opacity = '0.9';
                label.style.whiteSpace = 'nowrap';

                // Smart label positioning: above if room, otherwise below
                const labelHeight = {font_size} + 8;
                if (rect.top >= labelHeight) {{
                    // Room above - position above the box (left side)
                    label.style.left = (rect.left + scrollX) + 'px';
                    label.style.top = (rect.top + scrollY - labelHeight) + 'px';
                    label.style.transformOrigin = 'left bottom';
                    label.style.transform = 'rotate(-45deg)';
                }} else {{
                    // No room above - position below the box (right side)
                    // Position so label's top-right aligns with box's bottom-right
                    label.style.left = (rect.left + scrollX + rect.width) + 'px';
                    label.style.top = (rect.top + scrollY + rect.height) + 'px';
                    label.style.transformOrigin = 'right top';
                    label.style.transform = 'translateX(-100%) rotate(-45deg)';
                }}

                overlay.appendChild(label);
            }});

            return elements.length;
        }})();
        """

        return script

    @staticmethod
    def _generate_remove_script() -> str:
        """Generate JavaScript to remove the bounding box overlay."""
        return """
        (() => {
            const overlay = document.getElementById('__webtask_bbox_overlay__');
            if (overlay) {
                overlay.remove();
            }
        })();
        """

    @staticmethod
    async def render(
        page: Page,
        element_map: Dict[str, DomNode],
        color: str = "red",
        line_width: int = 2,
        font_size: int = 12,
        full_page: bool = False,
    ) -> Image:
        """Render screenshot with bounding boxes for each element in element_map.

        Args:
            page: Browser page to screenshot
            element_map: Map of element_id -> DomNode (from DomContextBuilder)
            color: Box and label color (default: "red")
            line_width: Border width in pixels (default: 2)
            font_size: Label font size (default: 12)
            full_page: Capture full scrollable page (default: False, viewport only)

        Returns:
            Image object with bounding boxes
        """
        # Draw boxes in browser
        draw_script = BoundingBoxRenderer._generate_draw_script(
            element_map, color, line_width, font_size
        )
        await page.evaluate(draw_script)

        # Take screenshot
        screenshot_bytes = await page.screenshot(full_page=full_page)

        # Remove boxes from browser
        remove_script = BoundingBoxRenderer._generate_remove_script()
        await page.evaluate(remove_script)

        return Image(screenshot_bytes, format="png")

    @staticmethod
    async def save(
        page: Page,
        element_map: Dict[str, DomNode],
        output_path: str,
        color: str = "red",
        line_width: int = 2,
        font_size: int = 12,
    ) -> None:
        """Render and save screenshot with bounding boxes.

        Args:
            page: Browser page to screenshot
            element_map: Map of element_id -> DomNode
            output_path: Path to save the image (e.g., "screenshot.png")
            color: Box and label color (default: "red")
            line_width: Border width in pixels (default: 2)
            font_size: Label font size (default: 12)
        """
        image = await BoundingBoxRenderer.render(
            page=page,
            element_map=element_map,
            color=color,
            line_width=line_width,
            font_size=font_size,
        )

        # Save using Image's save method
        image.save(output_path)
