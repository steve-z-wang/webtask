"""Context builder for LLMBrowser."""

from typing import TYPE_CHECKING
from ...llm import Block

if TYPE_CHECKING:
    from ...llm_browser import LLMBrowser


class LLMBrowserContextBuilder:
    """Builds LLM context blocks from LLMBrowser."""

    def __init__(self, llm_browser: "LLMBrowser"):
        self._llm_browser = llm_browser

    async def build_page_context(self) -> Block:
        """Get formatted page context for LLM."""
        return await self._llm_browser.get_page_context()
