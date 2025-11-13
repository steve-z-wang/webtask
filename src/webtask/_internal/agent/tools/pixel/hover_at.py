
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class HoverAtTool(Tool):

    name = "hover_at"
    description = "Hover at specific x, y coordinates. Useful for exploring sub-menus that appear on hover. Coordinates are normalized 0-1000."

    class Params(BaseModel):
        x: int = Field(description="X coordinate (0-1000, normalized to screen width)")
        y: int = Field(description="Y coordinate (0-1000, normalized to screen height)")

    async def execute(self, params: Params, page: "Page") -> str:
        # Get screen size
        viewport = await page.get_viewport_size()
        screen_width = viewport["width"]
        screen_height = viewport["height"]

        # Denormalize coordinates
        actual_x = int((params.x / 1000) * screen_width)
        actual_y = int((params.y / 1000) * screen_height)

        # Hover at coordinates
        await page.hover_at(actual_x, actual_y)

        return f"Hovered at coordinates ({params.x}, {params.y}) -> actual ({actual_x}, {actual_y})"
