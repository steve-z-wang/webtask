"""Playwright element implementation."""

from typing import List, Optional, Union
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

    async def get_tag_name(self) -> str:
        """
        Get the tag name of the element.

        Returns:
            Tag name (e.g., 'input', 'button', 'a')
        """
        return await self._locator.evaluate("el => el.tagName.toLowerCase()")

    async def get_attribute(self, name: str) -> Optional[str]:
        """
        Get an attribute value from the element.

        Args:
            name: Attribute name (e.g., 'type', 'id', 'class')

        Returns:
            Attribute value or None if not present
        """
        return await self._locator.get_attribute(name)

    async def get_attributes(self) -> dict[str, str]:
        """
        Get all attributes from the element.

        Returns:
            Dictionary of attribute name-value pairs
        """
        attributes = await self._locator.evaluate(
            """
            el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }
        """
        )
        return attributes

    async def get_html(self, outer: bool = True) -> str:
        """
        Get the HTML content of the element.

        Args:
            outer: If True, returns outerHTML (includes the element itself).
                   If False, returns innerHTML (only the element's content).

        Returns:
            HTML string
        """
        if outer:
            return await self._locator.evaluate("el => el.outerHTML")
        else:
            return await self._locator.evaluate("el => el.innerHTML")

    async def get_parent(self) -> Optional["PlaywrightElement"]:
        """
        Get the parent element.

        Returns:
            Parent PlaywrightElement or None if no parent (e.g., root element)
        """
        # Get parent using XPath
        parent_locator = self._locator.locator("xpath=..")
        count = await parent_locator.count()
        if count == 0:
            return None
        return PlaywrightElement(parent_locator)

    async def get_children(self) -> list["PlaywrightElement"]:
        """
        Get all direct child elements.

        Returns:
            List of child PlaywrightElements (may be empty)
        """
        # Get all direct child elements using XPath
        children_locator = self._locator.locator("xpath=./*")
        count = await children_locator.count()
        return [PlaywrightElement(children_locator.nth(i)) for i in range(count)]

    async def click(self):
        """Click the element."""
        await self._locator.click(timeout=30000)

    async def fill(self, text: str):
        """
        Fill the element with text (for input fields).

        Args:
            text: Text to fill
        """
        await self._locator.fill(text, timeout=30000)

    async def type(self, text: str, delay: float = None):
        """
        Type text into the element character by character.

        Args:
            text: Text to type
            delay: Delay between keystrokes in milliseconds (None = instant)
        """
        await self._locator.type(text, delay=delay, timeout=30000)

    async def upload_file(self, file_path: Union[str, List[str]]):
        """
        Upload file(s) to a file input element.

        Args:
            file_path: Single file path or list of file paths
        """
        await self._locator.set_input_files(file_path, timeout=30000)
