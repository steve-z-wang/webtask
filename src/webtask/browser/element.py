"""Element base class for browser element management."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Element(ABC):
    """
    Abstract base class for browser element.

    Simple adapter over browser automation library elements (Playwright, Selenium, etc.).
    """

    @abstractmethod
    async def get_tag_name(self) -> str:
        """
        Get the tag name of the element.

        Returns:
            Tag name (e.g., 'input', 'button', 'a')
        """
        pass

    @abstractmethod
    async def get_attribute(self, name: str) -> Optional[str]:
        """
        Get an attribute value from the element.

        Args:
            name: Attribute name (e.g., 'type', 'id', 'class')

        Returns:
            Attribute value or None if not present
        """
        pass

    @abstractmethod
    async def get_attributes(self) -> Dict[str, str]:
        """
        Get all attributes from the element.

        Returns:
            Dictionary of attribute name-value pairs
        """
        pass

    @abstractmethod
    async def get_html(self, outer: bool = True) -> str:
        """
        Get the HTML content of the element.

        Args:
            outer: If True, returns outerHTML (includes the element itself).
                   If False, returns innerHTML (only the element's content).

        Returns:
            HTML string
        """
        pass

    @abstractmethod
    async def get_parent(self) -> Optional["Element"]:
        """
        Get the parent element.

        Returns:
            Parent Element or None if no parent (e.g., root element)
        """
        pass

    @abstractmethod
    async def get_children(self) -> List["Element"]:
        """
        Get all direct child elements.

        Returns:
            List of child Elements (may be empty)
        """
        pass

    @abstractmethod
    async def click(self):
        """Click the element."""
        pass

    @abstractmethod
    async def fill(self, text: str):
        """
        Fill the element with text (for input fields).

        Args:
            text: Text to fill
        """
        pass

    @abstractmethod
    async def type(self, text: str, delay: float = None):
        """
        Type text into the element character by character.

        Args:
            text: Text to type
            delay: Delay between keystrokes in milliseconds (None = instant)
        """
        pass

    @abstractmethod
    async def upload_file(self, file_path: Union[str, List[str]]):
        """
        Upload file(s) to a file input element.

        Args:
            file_path: Single file path (str) or multiple file paths (List[str])
        """
        pass
