"""Type tool for typing text using keyboard (no selector needed)."""

from typing import Type
from pydantic import Field
from ...tool import Tool, ToolParams
from ....llm_browser import LLMBrowser


class TypeParams(ToolParams):
    """Parameters for type tool."""

    text: str = Field(description="Text to type into the currently focused element")
    clear: bool = Field(default=True, description="Clear existing text before typing (default: True)")


class TypeTool(Tool[TypeParams]):
    """Tool for typing text into the currently focused element."""

    def __init__(self, llm_browser: LLMBrowser):
        self.llm_browser = llm_browser

    @property
    def name(self) -> str:
        return "type"

    @property
    def description(self) -> str:
        return "Type text into the currently focused element using keyboard (must click element first to focus). Use clear=True to clear existing text first."

    @property
    def params_class(self) -> Type[TypeParams]:
        return TypeParams

    async def execute(self, params: TypeParams):
        """Execute type using keyboard."""
        await self.llm_browser.keyboard_type(params.text, clear=params.clear)
