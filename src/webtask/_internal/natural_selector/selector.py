"""Natural language element selector."""

import base64
import json
from typing import TYPE_CHECKING, Optional
from pydantic import ValidationError
from webtask.llm import LLM, SystemMessage, UserMessage, TextContent, ImageContent
from ..prompts import build_selector_prompt
from webtask.browser import Element
from ..context import LLMDomContext
from ..utils.logger import get_logger
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
        mode: str = "accessibility",
    ):
        self._llm = llm
        self._session_browser = session_browser
        self._max_retries = max_retries
        self._include_screenshot = include_screenshot
        self._mode = mode
        self._dom_context: Optional[LLMDomContext] = None
        self._logger = get_logger(__name__)

    async def select(self, description: str) -> Element:
        """Select element by natural language description."""
        self._logger.info(f"Natural selector - Query: {description}")

        self._logger.debug("Getting current page...")
        page = self._session_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        self._logger.debug(f"Current page URL: {page.url}")

        # Build LLMDomContext with interactive IDs
        self._logger.debug("Building DOM context...")
        self._dom_context = await LLMDomContext.from_page(
            page, include_element_ids=True
        )
        page_context = self._dom_context.get_context(mode=self._mode)
        context_size = len(page_context)
        self._logger.debug(
            f"DOM context built successfully - Size: {context_size} chars ({context_size / 1024:.1f} KB)"
        )

        system = build_selector_prompt()

        # Build messages for LLM
        messages = [
            SystemMessage(content=[TextContent(text=system)]),
            UserMessage(content=[TextContent(text=page_context)]),
        ]

        # Add full page screenshot
        if self._include_screenshot:
            self._logger.debug("Capturing screenshot...")
            screenshot_bytes = await page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            messages.append(UserMessage(content=[ImageContent(data=screenshot_b64)]))

        messages.append(
            UserMessage(
                content=[
                    TextContent(
                        text=f'\nWhich element_id matches this description: "{description}"?'
                    )
                ]
            )
        )

        # Generate and validate response with automatic retry
        last_error = None

        for attempt in range(self._max_retries):
            try:
                self._logger.debug("Sending LLM request...")
                selector_response = await self._llm.generate_response(
                    messages, SelectorResponse
                )
                self._logger.info(
                    f"Received LLM response - Selected: {selector_response.element_id}"
                )
                break

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e
                self._logger.warning(
                    f"LLM response validation failed (attempt {attempt + 1}/{self._max_retries}): {type(e).__name__}"
                )

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

        if not selector_response.element_id:
            if selector_response.error:
                raise ValueError(
                    f"No matching element found: {selector_response.error}"
                )
            raise ValueError("LLM response missing 'element_id' field")

        # Get DOM node from element ID
        self._logger.debug(
            f"Converting element_id '{selector_response.element_id}' to element..."
        )
        node = self._dom_context.get_dom_node(selector_response.element_id)
        if node is None:
            raise ValueError(
                f"Element ID '{selector_response.element_id}' not found in page context"
            )

        xpath = node.get_x_path()
        element = await page.select_one(xpath)
        self._logger.info("Natural selector - Element found successfully")
        return element
