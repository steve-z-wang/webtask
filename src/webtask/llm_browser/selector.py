"""Natural language element selector."""

import json
from typing import TYPE_CHECKING
from pydantic import ValidationError
from ..llm import LLM, Context, Block
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

        # Generate and validate response with automatic retry
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Generate JSON response
                response = await self.llm.generate(context, use_json=True)

                # Parse JSON (handles markdown fences)
                cleaned_json_dict = parse_json(response)

                # Validate with Pydantic
                selector_response = SelectorResponse.model_validate(cleaned_json_dict)
                break

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # If not the last attempt, append error feedback and retry
                if attempt < max_retries - 1:
                    error_type = type(e).__name__
                    error_msg = str(e)

                    # Append error feedback to context
                    feedback = (
                        f"\n❌ ERROR: Your previous JSON response was invalid.\n\n"
                        f"Error type: {error_type}\n"
                        f"Error details: {error_msg}\n\n"
                        f"Please provide a valid JSON response that matches the required schema."
                    )
                    context.append(Block(feedback))
                else:
                    # Last attempt failed, raise error
                    raise ValueError(
                        f"Failed to parse LLM response after {max_retries} attempts. "
                        f"Last error: {type(e).__name__}: {str(e)}"
                    ) from last_error

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
