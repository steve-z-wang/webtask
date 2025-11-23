"""DOM-based tools that interact with elements by ID."""

from typing import List, TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser
    from webtask._internal.agent.file_manager import FileManager


class ClickTool(Tool):
    """Click an element on the page."""

    name = "click"
    description = "Click an element on the page"

    class Params(BaseModel):
        """Parameters for click tool."""

        element_id: str = Field(description="ID of the element to click")
        description: str = Field(
            description="Human-readable description of what element you're clicking (e.g., 'Submit button', 'Login link')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize click tool with worker browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute click on element."""
        await self.browser.click(params.element_id)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Clicked {params.description}",
        )


class FillTool(Tool):
    """Fill a form element with a value."""

    name = "fill"
    description = "Fill a form element with a value (fast, direct value setting)"

    class Params(BaseModel):
        """Parameters for fill tool."""

        element_id: str = Field(description="ID of the element to fill")
        value: str = Field(description="Value to fill into the element")
        description: str = Field(
            description="Human-readable description of what element you're filling (e.g., 'Email input field', 'Password field')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize fill tool with worker browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute fill on element."""
        await self.browser.fill(params.element_id, params.value)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Filled {params.description} with '{params.value}'",
        )


class TypeTool(Tool):
    """Type text into an element character by character."""

    name = "type"
    description = "Type text into an element character by character with realistic delays (appends to existing text - use fill to replace)"

    class Params(BaseModel):
        """Parameters for type tool."""

        element_id: str = Field(description="ID of the element to type into")
        text: str = Field(description="Text to type into the element")
        description: str = Field(
            description="Human-readable description of what element you're typing into (e.g., 'Search box', 'Comment field')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize type tool with worker browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute type on element."""
        await self.browser.type(params.element_id, params.text)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Typed '{params.text}' into {params.description}",
        )


class UploadTool(Tool):
    """Upload files to a file input element."""

    name = "upload"
    description = "Upload files to a file input element. Use file indexes shown in the Files section."

    class Params(BaseModel):
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
        """Initialize upload tool with worker browser and file manager."""
        self.browser = browser
        self.file_manager = file_manager

    async def execute(self, params: Params) -> ToolResult:
        """Execute file upload."""
        # Resolve file indexes to paths
        paths = self.file_manager.get_paths(params.file_indexes)

        # Upload files (single file or multiple)
        file_path = paths if len(paths) > 1 else paths[0]
        await self.browser.upload(params.element_id, file_path)

        indexes_str = ", ".join(f"[{i}]" for i in params.file_indexes)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Uploaded files {indexes_str} to {params.description}",
        )
