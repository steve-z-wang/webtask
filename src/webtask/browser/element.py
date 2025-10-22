"""Element base class for browser element management."""

from abc import ABC, abstractmethod


class Element(ABC):
    """
    Abstract base class for browser element.

    Simple adapter over browser automation library elements (Playwright, Selenium, etc.).
    Provides basic action methods for element interaction.
    """

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

        Simulates keyboard input with delays between keystrokes for more realistic behavior.

        Args:
            text: Text to type
            delay: Delay between keystrokes in milliseconds (None = instant)
        """
        pass

    @abstractmethod
    async def upload_file(self, file_path: str):
        """
        Upload a file to a file input element.

        Args:
            file_path: Path to the file to upload
        """
        pass
