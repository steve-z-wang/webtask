"""Click tool for clicking elements."""

from typing import Type
from pydantic import Field
from ...tool import Tool
from ...schemas.params import ToolParams
from ....llm_browser import LLMBrowser


class ClickParams(ToolParams):
    """Parameters for click action."""

    element_id: str = Field(description="ID of the element to click")


class ClickTool(Tool[ClickParams]):
    """Tool for clicking an element."""

    def __init__(self, llm_browser: LLMBrowser):
        self.llm_browser = llm_browser

    @property
    def name(self) -> str:
        return "click"

    @property
    def description(self) -> str:
        return "Click an element"

    @property
    def params_class(self) -> Type[ClickParams]:
        return ClickParams

    async def execute(self, params: ClickParams):
        """Execute click on element."""
        await self.llm_browser.click(params.element_id)
