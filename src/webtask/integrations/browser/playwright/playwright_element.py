"""Playwright element implementation."""

from playwright.async_api import Locator
from ....browser import Element


class PlaywrightElement(Element):
    """
    Playwright implementation of Element.

    Wraps Playwright's Locator/ElementHandle for element interaction.
    """

    def __init__(self, locator: Locator):
        """
        Initialize PlaywrightElement.

        Args:
            locator: Playwright Locator or ElementHandle
        """
        self._locator = locator

    async def click(self):
        """Click the element."""
        await self._locator.click()

    async def fill(self, text: str):
        """
        Fill the element with text (for input fields).

        Args:
            text: Text to fill
        """
        await self._locator.fill(text)

    async def type(self, text: str, delay: float = None):
        """
        Type text into the element character by character.

        Args:
            text: Text to type
            delay: Delay between keystrokes in milliseconds (None = instant)
        """
        await self._locator.type(text, delay=delay)

    async def upload_file(self, file_path: str):
        """
        Upload a file to a file input element.

        Args:
            file_path: Path to the file to upload
        """
        await self._locator.set_input_files(file_path)
