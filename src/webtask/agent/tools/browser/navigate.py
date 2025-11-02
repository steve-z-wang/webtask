"""Navigate tool for navigating to URLs."""

from typing import Type
from ...tool import Tool
from ...schemas import NavigateParams
from ....llm_browser import LLMBrowser


class NavigateTool(Tool[NavigateParams]):
    """Tool for navigating to a URL."""

    def __init__(self, llm_browser: LLMBrowser):
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
        """Execute navigation to URL."""
        await self.llm_browser.navigate(params.url)
