
from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class ScrollAtTool(Tool):

    name = "scroll_at"
    description = "Scroll up, down, left, or right at specific x, y coordinates by magnitude. Useful for scrolling within specific elements. Coordinates are normalized 0-1000."

    class Params(BaseModel):
        x: int = Field(description="X coordinate (0-1000, normalized to screen width)")
        y: int = Field(description="Y coordinate (0-1000, normalized to screen height)")
        direction: Literal["up", "down", "left", "right"] = Field(
            description='Direction to scroll: "up", "down", "left", or "right"'
        )
        magnitude: int = Field(
            default=800, description="Scroll distance in pixels (default: 800)"
        )

    async def execute(self, params: Params, page: "Page") -> str:
        # Get screen size
        viewport = await page.get_viewport_size()
        screen_width = viewport["width"]
        screen_height = viewport["height"]

        # Denormalize coordinates
        actual_x = int((params.x / 1000) * screen_width)
        actual_y = int((params.y / 1000) * screen_height)

        # Denormalize magnitude based on direction
        if params.direction in ("up", "down"):
            actual_magnitude = int((params.magnitude / 1000) * screen_height)
        else:  # left, right
            actual_magnitude = int((params.magnitude / 1000) * screen_width)

        # Scroll at coordinates
        await page.scroll_at(
            x=actual_x, y=actual_y, direction=params.direction, amount=actual_magnitude
        )

        return f"Scrolled {params.direction} by {params.magnitude} at ({params.x}, {params.y})"
