"""DOM-based tools that interact with elements by ID."""

from typing import List, TYPE_CHECKING
from pydantic import Field
from webtask.llm.tool import Tool, ToolParams
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser
    from webtask._internal.agent.file_manager import FileManager


class ClickTool(Tool):
    """Click an element on the page."""

    name = "click"
    description = "Click an element on the page"

    class Params(ToolParams):
        """Parameters for click tool."""

        element_id: str = Field(description="ID of the element to click")
        description: str = Field(
            description="Human-readable description of what element you're clicking (e.g., 'Submit button', 'Login link')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize click tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute click on element."""
        element = await self.browser.select(params.element_id)
        await element.click()
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Clicked {params.description}",
        )


class TypeTool(Tool):
    """Type text into an element."""

    name = "type"
    description = "Type text into an input field or text area"

    class Params(ToolParams):
        """Parameters for type tool."""

        element_id: str = Field(description="ID of the input element to type into")
        text: str = Field(description="Text to type")
        clear: bool = Field(
            default=True,
            description="Clear existing text before typing",
        )
        description: str = Field(
            description="Human-readable description of what you're typing (e.g., 'Search query', 'Email address')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize type tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute type into element (clicks to focus, then types)."""
        element = await self.browser.select(params.element_id)
        await element.click()
        page = self.browser.get_current_page()
        await page.keyboard_type(params.text, clear=params.clear)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Typed {params.description}"
            + (" (cleared first)" if params.clear else ""),
        )


class UploadTool(Tool):
    """Upload files to a file input element."""

    name = "upload"
    description = "Upload files to a file input element. Use file indexes shown in the Files section."

    class Params(ToolParams):
        """Parameters for upload tool."""

        element_id: str = Field(
            description="Element ID of the file input (e.g., '[input-5]')"
        )
        file_indexes: List[int] = Field(
            description="List of file indexes to upload (e.g., [0] or [0, 1])"
        )
        description: str = Field(
            description="Human-readable description of what file input you're uploading to (e.g., 'Profile photo upload', 'Document attachment field')"
        )

    def __init__(
        self,
        browser: "AgentBrowser",
        file_manager: "FileManager",
    ):
        """Initialize upload tool with browser and file manager."""
        self.browser = browser
        self.file_manager = file_manager

    async def execute(self, params: Params) -> ToolResult:
        """Execute file upload."""
        paths = self.file_manager.get_paths(params.file_indexes)
        file_path = paths if len(paths) > 1 else paths[0]

        element = await self.browser.select(params.element_id)
        await element.upload_file(file_path)
        await self.browser.wait()

        indexes_str = ", ".join(f"[{i}]" for i in params.file_indexes)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Uploaded files {indexes_str} to {params.description}",
        )
