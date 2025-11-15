"""Natural language element selector."""

import base64
import json
from typing import TYPE_CHECKING, Optional
from pydantic import ValidationError
from webtask.llm import LLM, SystemMessage, UserMessage, TextContent, ImageContent
from ..prompts import build_selector_prompt
from webtask.browser import Element
from ..context import LLMDomContext
from .schema import SelectorResponse

if TYPE_CHECKING:
    from ..agent.session_browser import SessionBrowser


class NaturalSelector:
    """Selects elements using natural language descriptions."""

    def __init__(
        self,
        llm: LLM,
        session_browser: "SessionBrowser",
        max_retries: int = 3,
        include_screenshot: bool = True,
    ):
        self._llm = llm
        self._session_browser = session_browser
        self._max_retries = max_retries
        self._include_screenshot = include_screenshot
        self._dom_context: Optional[LLMDomContext] = None

    async def select(self, description: str) -> Element:
        """Select element by natural language description."""
        page = self._session_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        # Build LLMDomContext with interactive IDs
        self._dom_context = await LLMDomContext.from_page(
            page, include_interactive_ids=True
        )
        page_context = self._dom_context.get_context()

        system = build_selector_prompt()

        # Build messages for LLM
        messages = [
            SystemMessage(content=[TextContent(text=system)]),
            UserMessage(content=[TextContent(text=page_context)]),
        ]

        # Add full page screenshot
        if self._include_screenshot:
            screenshot_bytes = await page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            messages.append(UserMessage(content=[ImageContent(data=screenshot_b64)]))

        messages.append(
            UserMessage(
                content=[
                    TextContent(
                        text=f'\nWhich interactive_id matches this description: "{description}"?'
                    )
                ]
            )
        )

        # Generate and validate response with automatic retry
        last_error = None

        for attempt in range(self._max_retries):
            try:
                selector_response = await self._llm.generate_response(
                    messages, SelectorResponse
                )
                break

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # If not the last attempt, append error feedback and retry
                if attempt < self._max_retries - 1:
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
                        f"Failed to parse LLM response after {self._max_retries} attempts. "
                        f"Last error: {type(e).__name__}: {str(e)}"
                    ) from last_error

        if not selector_response.interactive_id:
            if selector_response.error:
                raise ValueError(
                    f"No matching element found: {selector_response.error}"
                )
            raise ValueError("LLM response missing 'interactive_id' field")

        # Get DOM node from interactive ID
        node = self._dom_context.get_dom_node(selector_response.interactive_id)
        if node is None:
            raise ValueError(
                f"Interactive ID '{selector_response.interactive_id}' not found in page context"
            )

        xpath = node.get_x_path()
        element = await page.select_one(xpath)
        return element
