
from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class ScrollDocumentTool(Tool):

    name = "scroll_document"
    description = 'Scroll the entire webpage in a direction: "up", "down", "left", or "right".'

    class Params(BaseModel):
        direction: Literal["up", "down", "left", "right"] = Field(
            description='Direction to scroll: "up", "down", "left", or "right"'
        )

    async def execute(self, params: Params, page: "Page") -> str:
        # Scroll the page
        await page.scroll(direction=params.direction)

        return f"Scrolled document {params.direction}"
