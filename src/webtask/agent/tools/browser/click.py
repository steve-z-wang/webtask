"""Click tool for clicking elements."""

from typing import Type
from pydantic import Field
from ...tool import Tool, ToolParams
from ....llm_browser import LLMBrowser


class ClickParams(ToolParams):
    """Parameters for click tool."""

    element_id: str = Field(description="ID of the element to click")


class ClickTool(Tool[ClickParams]):
    """
    Tool for clicking an element.

    Clicks the element identified by the given ID.
    """

    def __init__(self, llm_browser: LLMBrowser):
        """
        Initialize click tool.

        Args:
            llm_browser: LLMBrowser instance to execute click
        """
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
        """
        Execute click on element.

        Args:
            params: ClickParams with element_id

        Returns:
            None
        """
        await self.llm_browser.click(params.element_id)
