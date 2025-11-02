"""Click tool for clicking elements."""

from typing import Type
from ...tool import Tool
from ...schemas import ClickParams
from ....llm_browser import LLMBrowser


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
