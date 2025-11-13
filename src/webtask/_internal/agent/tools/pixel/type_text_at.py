"""Type text at pixel coordinates tool."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class TypeTextAtTool(Tool):
    """Click at coordinates then type text."""

    name = "type_text_at"
    description = "Click at x, y coordinates then type text. Automatically clears existing content and presses Enter after typing. Coordinates are normalized 0-1000."

    class Params(BaseModel):
        x: int = Field(description="X coordinate (0-1000, normalized to screen width)")
        y: int = Field(description="Y coordinate (0-1000, normalized to screen height)")
        text: str = Field(description="Text to type")
        press_enter: bool = Field(
            default=True, description="Press Enter after typing (default: True)"
        )
        clear_before_typing: bool = Field(
            default=True,
            description="Clear existing content before typing (default: True)",
        )

    async def execute(self, params: Params, page: "Page") -> str:
        """Execute type text at coordinates.

        Args:
            params: Validated parameters
            page: Page to type on

        Returns:
            Success message
        """
        # Get screen size
        viewport = await page.get_viewport_size()
        screen_width = viewport["width"]
        screen_height = viewport["height"]

        # Denormalize coordinates
        actual_x = int((params.x / 1000) * screen_width)
        actual_y = int((params.y / 1000) * screen_height)

        # Click at coordinates first
        await page.click_at(actual_x, actual_y)

        # Clear existing content if requested
        if params.clear_before_typing:
            # Select all and delete
            await page.keyboard_press("Control+A" if not page._is_mac else "Meta+A")
            await page.keyboard_press("Backspace")

        # Type the text
        await page.keyboard_type(params.text)

        # Press enter if requested
        if params.press_enter:
            await page.keyboard_press("Enter")

        action = f"Typed '{params.text}' at ({params.x}, {params.y})"
        if params.press_enter:
            action += " and pressed Enter"
        return action
