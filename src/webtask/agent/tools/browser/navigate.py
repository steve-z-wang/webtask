"""Navigate tool for navigating to URLs."""

from typing import Type
from pydantic import Field
from ...tool import Tool, ToolParams
from ....llm_browser import LLMBrowser


class NavigateParams(ToolParams):
    """Parameters for navigate tool."""

    url: str = Field(description="URL to navigate to")


class NavigateTool(Tool[NavigateParams]):
    """
    Tool for navigating to a URL.

    Navigates the browser page to the specified URL.
    """

    def __init__(self, llm_browser: LLMBrowser):
        """
        Initialize navigate tool.

        Args:
            llm_browser: LLMBrowser instance to execute navigation
        """
        self.llm_browser = llm_browser

    @property
    def name(self) -> str:
        return "navigate"

    @property
    def description(self) -> str:
        return "Navigate to a URL"

    @property
    def params_class(self) -> Type[NavigateParams]:
        return NavigateParams

    async def execute(self, params: NavigateParams):
        """
        Execute navigation to URL.

        Args:
            params: NavigateParams with url

        Returns:
            None
        """
        await self.llm_browser.navigate(params.url)
