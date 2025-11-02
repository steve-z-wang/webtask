"""Fill tool for filling form elements."""

from typing import Type
from ...tool import Tool
from ...schemas import FillParams
from ....llm_browser import LLMBrowser


class FillTool(Tool[FillParams]):
    """
    Tool for filling a form element with a value.

    Fills the element identified by the given ID with the specified value.
    """

    def __init__(self, llm_browser: LLMBrowser):
        """
        Initialize fill tool.

        Args:
            llm_browser: LLMBrowser instance to execute fill
        """
        self.llm_browser = llm_browser

    @property
    def name(self) -> str:
        return "fill"

    @property
    def description(self) -> str:
        return "Fill an element with a value"

    @property
    def params_class(self) -> Type[FillParams]:
        return FillParams

    async def execute(self, params: FillParams):
        """
        Execute fill on element.

        Args:
            params: FillParams with element_id and value

        Returns:
            None
        """
        await self.llm_browser.fill(params.element_id, params.value)
