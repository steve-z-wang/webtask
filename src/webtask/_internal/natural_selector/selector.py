"""Natural language element selector."""

import json
from typing import TYPE_CHECKING, Dict
from pydantic import ValidationError
from webtask.llm import LLM, SystemMessage, UserMessage, TextContent
from ..prompts import build_selector_prompt
from webtask.browser import Element
from ..page_context import PageContextBuilder
from .schema import SelectorResponse

if TYPE_CHECKING:
    from ..agent.agent_browser import AgentBrowser


class NaturalSelector:
    """Selects elements using natural language descriptions."""

    def __init__(self, llm: LLM, agent_browser: "AgentBrowser"):
        self._llm = llm
        self._agent_browser = agent_browser
        self._element_map: Dict = {}

    async def select(self, description: str) -> Element:
        """Select element by natural language description."""
        page = self._agent_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        page_context, element_map = await PageContextBuilder.build(
            page=page,
            include_element_ids=True,
            with_bounding_boxes=False,
            full_page_screenshot=True,
        )
        self._element_map = element_map if element_map else {}

        system = build_selector_prompt()

        # Build messages for LLM
        messages = [
            SystemMessage(content=[TextContent(text=system)]),
            UserMessage(content=[TextContent(text=page_context)]),
            UserMessage(
                content=[
                    TextContent(
                        text=f'\nWhich element_id matches this description: "{description}"?'
                    )
                ]
            ),
        ]

        # Generate and validate response with automatic retry
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                selector_response = await self._llm.generate_response(
                    messages, SelectorResponse
                )
                break

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # If not the last attempt, append error feedback and retry
                if attempt < max_retries - 1:
                    error_type = type(e).__name__
                    error_msg = str(e)

                    feedback = (
                        f"\n❌ ERROR: Your previous JSON response was invalid.\n\n"
                        f"Error type: {error_type}\n"
                        f"Error details: {error_msg}\n\n"
                        f"Please provide a valid JSON response that matches the required schema."
                    )
                    messages.append(UserMessage(content=[TextContent(text=feedback)]))
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

        if selector_response.element_id not in self._element_map:
            raise ValueError(
                f"Element ID '{selector_response.element_id}' not found in page context"
            )

        node = self._element_map[selector_response.element_id]
        xpath = node.get_x_path()
        element = await page.select_one(xpath)
        return element
