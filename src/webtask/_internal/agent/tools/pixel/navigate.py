
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    from webtask._internal.browser import Page


class NavigateTool(Tool):

    name = "navigate"
    description = "Navigate directly to a specified URL."

    class Params(BaseModel):
        url: str = Field(description="URL to navigate to (must include protocol, e.g., https://)")

    async def execute(self, params: Params, page: "Page") -> str:
        await page.goto(params.url)
        return f"Navigated to {params.url}"
