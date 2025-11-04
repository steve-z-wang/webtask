"""Natural language element selector."""

from typing import TYPE_CHECKING
from ..llm import LLM, Context, ValidatedLLM
from ..prompts import get_prompt
from ..browser import Element
from ..agent.schemas import SelectorResponse

if TYPE_CHECKING:
    from .llm_browser import LLMBrowser


class NaturalSelector:
    """Selects elements using natural language descriptions."""

    def __init__(self, llm: LLM, llm_browser: "LLMBrowser"):
        self.validated_llm = ValidatedLLM(llm)
        self.llm_browser = llm_browser

    async def select(self, description: str) -> Element:
        """Select element by natural language description."""
        # Use full_page=True to see elements below the fold
        page_context = await self.llm_browser.get_page_context(full_page=True)

        system = get_prompt("selector_system")

        context = Context(system=system)
        context.append(page_context)  # Keep Block with image, don't convert to string
        context.append(f'\nWhich element_id matches this description: "{description}"?')

        # Generate and validate response with automatic retry on parse/validation errors
        selector_response = await self.validated_llm.generate_validated(
            context, validator=SelectorResponse.model_validate
        )

        if not selector_response.element_id:
            if selector_response.error:
                raise ValueError(
                    f"No matching element found: {selector_response.error}"
                )
            raise ValueError("LLM response missing 'element_id' field")

        try:
            xpath = self.llm_browser._get_xpath(selector_response.element_id)
        except KeyError:
            raise ValueError(
                f"Element ID '{selector_response.element_id}' not found in page context"
            )

        page = self.llm_browser.get_current_page()
        element = await page.select_one(xpath)
        return element
