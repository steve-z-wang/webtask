"""Natural language element selector."""

from typing import TYPE_CHECKING
from ..llm import LLM, Context
from ..prompts import get_prompt
from ..browser import Element
from ..agent.schemas import SelectorResponse
from ..utils.json_parser import parse_json

if TYPE_CHECKING:
    from .llm_browser import LLMBrowser


class NaturalSelector:
    """Selects elements using natural language descriptions."""

    def __init__(self, llm: LLM, llm_browser: "LLMBrowser"):
        self.llm = llm
        self.llm_browser = llm_browser

    async def select(self, description: str) -> Element:
        """Select element by natural language description."""
        # Use full_page=True to see elements below the fold
        page_context = await self.llm_browser.get_page_context(full_page=True)

        system = get_prompt("selector_system")

        context = Context(system=system)
        context.append(page_context)  # Keep Block with image, don't convert to string
        context.append(f'\nWhich element_id matches this description: "{description}"?')

        response = await self.llm.generate(context, use_json=True)

        # Clean JSON (remove markdown fences if present) and parse into Pydantic model
        cleaned_json_dict = parse_json(response)
        selector_response = SelectorResponse.model_validate(cleaned_json_dict)

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
