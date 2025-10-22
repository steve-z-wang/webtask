"""Type tool for typing text into form elements."""

from typing import Type
from pydantic import Field
from ...tool import Tool, ToolParams
from ....llm_browser import LLMBrowser


class TypeParams(ToolParams):
    """Parameters for type tool."""

    element_id: str = Field(description="ID of the element to type into")
    text: str = Field(description="Text to type into the element")


class TypeTool(Tool[TypeParams]):
    """
    Tool for typing text into a form element character by character.

    Types into the element identified by the given ID with realistic keystroke delays.
    Uses 80ms delay between keystrokes for human-like behavior.
    """

    def __init__(self, llm_browser: LLMBrowser):
        """
        Initialize type tool.

        Args:
            llm_browser: LLMBrowser instance to execute type
        """
        self.llm_browser = llm_browser

    @property
    def name(self) -> str:
        return "type"

    @property
    def description(self) -> str:
        return "Type text into an element character by character with realistic delays"

    @property
    def params_class(self) -> Type[TypeParams]:
        return TypeParams

    async def execute(self, params: TypeParams):
        """
        Execute type on element.

        Args:
            params: TypeParams with element_id and text

        Returns:
            None
        """
        await self.llm_browser.type(params.element_id, params.text)
