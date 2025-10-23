"""Natural language element selector."""

from typing import TYPE_CHECKING
from ..llm import LLM, Context
from ..prompts import get_prompt
from ..utils import parse_json
from ..browser import Element

if TYPE_CHECKING:
    from .llm_browser import LLMBrowser


class NaturalSelector:
    """
    Selects elements using natural language descriptions.

    Uses LLM to match descriptions to element IDs from page context.
    """

    def __init__(self, llm: LLM, llm_browser: 'LLMBrowser'):
        """
        Initialize natural selector.

        Args:
            llm: LLM instance for matching
            llm_browser: LLMBrowser instance for context and selection
        """
        self.llm = llm
        self.llm_browser = llm_browser

    async def select(self, description: str) -> Element:
        """
        Select element by natural language description.

        Args:
            description: Natural language description of element

        Returns:
            Browser Element instance

        Raises:
            ValueError: If no matching element found or LLM response invalid
        """
        # Get page context with element IDs
        page_context = await self.llm_browser.to_context_block()

        # Build prompt for LLM
        system = get_prompt("selector_system")

        context = Context(system=system)
        context.append(str(page_context))
        context.append(f"\nWhich element_id matches this description: \"{description}\"?")

        # Call LLM
        response = await self.llm.generate(context)

        # Parse response
        data = parse_json(response)

        element_id = data.get("element_id")
        error = data.get("error")

        if not element_id:
            if error:
                raise ValueError(f"No matching element found: {error}")
            raise ValueError("LLM response missing 'element_id' field")

        # Convert element_id to selector
        try:
            selector = self.llm_browser._get_selector(element_id)
        except KeyError:
            raise ValueError(f"Element ID '{element_id}' not found in page context")

        # Select and return element
        page = self.llm_browser.get_current_page()
        element = await page.select_one(selector)
        return element
