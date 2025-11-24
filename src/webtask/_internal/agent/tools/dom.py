"""DOM-based tools that interact with elements by ID."""

from typing import List, TYPE_CHECKING
from dodo import tool

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser
    from webtask._internal.agent.file_manager import FileManager


@tool
class ClickTool:
    """Click an element on the page."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, element_id: str, description: str) -> str:
        """
        Args:
            element_id: ID of the element to click
            description: Human-readable description of what element you're clicking (e.g., 'Submit button', 'Login link')
        """
        element = await self.browser.select(element_id)
        await element.click()
        await self.browser.wait()
        return f"Clicked {description}"


@tool
class FillTool:
    """Fill a form element with a value (fast, direct value setting)."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, element_id: str, value: str, description: str) -> str:
        """
        Args:
            element_id: ID of the element to fill
            value: Value to fill into the element
            description: Human-readable description of what element you're filling (e.g., 'Email input field', 'Password field')
        """
        element = await self.browser.select(element_id)
        await element.fill(value)
        await self.browser.wait()
        return f"Filled {description} with '{value}'"


@tool
class TypeTool:
    """Type text into an element character by character with realistic delays (appends to existing text - use fill to replace)."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, element_id: str, text: str, description: str) -> str:
        """
        Args:
            element_id: ID of the element to type into
            text: Text to type into the element
            description: Human-readable description of what element you're typing into (e.g., 'Search box', 'Comment field')
        """
        element = await self.browser.select(element_id)
        await element.type(text)
        await self.browser.wait()
        return f"Typed '{text}' into {description}"


@tool
class UploadTool:
    """Upload files to a file input element. Use file indexes shown in the Files section."""

    def __init__(self, browser: "AgentBrowser", file_manager: "FileManager"):
        self.browser = browser
        self.file_manager = file_manager

    async def run(
        self, element_id: str, file_indexes: List[int], description: str
    ) -> str:
        """
        Args:
            element_id: Element ID of the file input (e.g., '[input-5]')
            file_indexes: List of file indexes to upload (e.g., [0] or [0, 1])
            description: Human-readable description of what file input you're uploading to (e.g., 'Profile photo upload', 'Document attachment field')
        """
        paths = self.file_manager.get_paths(file_indexes)
        file_path = paths if len(paths) > 1 else paths[0]

        element = await self.browser.select(element_id)
        await element.upload_file(file_path)
        await self.browser.wait()

        indexes_str = ", ".join(f"[{i}]" for i in file_indexes)
        return f"Uploaded files {indexes_str} to {description}"
