"""Task tools - all tools available to the worker."""

from typing import Any, List, TYPE_CHECKING, Optional, Type
from pydantic import BaseModel, Field, create_model
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus
from .run import TaskResult, TaskStatus
from ..utils.wait import wait

if TYPE_CHECKING:
    from .agent_browser import AgentBrowser
    from .file_manager import FileManager


# Browser action tools


class GotoTool(Tool):
    """Go to a URL."""

    name = "goto"
    description = "Go to a URL"

    class Params(BaseModel):
        """Parameters for goto tool."""

        url: str = Field(description="URL to go to")

    def __init__(self, browser: "AgentBrowser"):
        """Initialize goto tool with worker browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute goto."""
        await self.browser.goto(params.url)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went to {params.url}",
        )


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


class WaitTool(Tool):
    """Wait for a specified duration."""

    name = "wait"
    description = "Wait for specified seconds (useful after actions that trigger page changes, modals, or dynamic content loading)"

    class Params(BaseModel):
        """Parameters for wait tool."""

        seconds: float = Field(
            description="Seconds to wait (max 10)",
            ge=0.1,
            le=10.0,
        )

    async def execute(self, params: Params) -> ToolResult:
        """Wait for the specified duration."""
        await wait(params.seconds)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Waited {params.seconds} seconds",
        )


# Page management tools


class OpenTabTool(Tool):
    """Open a new browser tab."""

    name = "open_tab"
    description = "Open a new blank browser tab and switch to it"

    class Params(BaseModel):
        """Parameters for open_tab tool."""

        description: str = Field(
            description="Why you are opening a new tab (e.g., 'Open new tab to search for product')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize open_tab tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Open a new tab."""
        await self.browser.open_tab()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Opened new tab: {params.description}",
        )


class SwitchTabTool(Tool):
    """Switch to a different browser tab."""

    name = "switch_tab"
    description = (
        "Switch to a different browser tab by its index (shown in Tabs section)"
    )

    class Params(BaseModel):
        """Parameters for switch_tab tool."""

        tab_index: int = Field(
            description="The tab index to switch to (0-based, as shown in Tabs section)",
            ge=0,
        )
        description: str = Field(
            description="Why you are switching to this tab (e.g., 'Switch back to main tab')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize switch_tab tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Switch to specified tab."""
        self.browser.focus_tab(params.tab_index)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Switched to tab [{params.tab_index}]: {params.description}",
        )


# Control tools


class CompleteWorkTool(Tool):
    """Signal that the worker has successfully completed the subtask with optional output data."""

    name = "complete_work"
    description = "Signal that you have successfully completed the subtask. Optionally provide structured output data to return to the user."

    # Default Params class (will be overridden in __init__ if output_schema is provided)
    class Params(BaseModel):
        """Parameters for complete_work tool."""

        feedback: str = Field(
            description="Brief 1-2 sentence summary of what you accomplished"
        )
        output: Optional[Any] = Field(
            default=None,
            description="Optional structured data to return to the user (e.g., extracted information, results)",
        )

    def __init__(
        self, task_result: "TaskResult", output_schema: Optional[Type[BaseModel]] = None
    ):
        """Initialize with reference to worker result and optional output schema.

        Args:
            task_result: TaskResult object to store completion status and data
            output_schema: Optional Pydantic model class defining the expected output structure
        """
        self.task_result = task_result

        # Dynamically create Params class if output_schema is provided
        if output_schema:
            # Inherit from base Params and only override the output field with the schema
            # This shadows the class-level Params attribute for this instance
            self.Params = create_model(  # type: ignore[misc]
                "CompleteWorkParams",
                __base__=CompleteWorkTool.Params,
                output=(
                    Optional[output_schema],
                    Field(
                        default=None,
                        description="Structured output data matching the specified schema",
                    ),
                ),
            )
        # Otherwise, the default class-level Params will be used

    async def execute(self, params: Params) -> ToolResult:
        """Signal that work is complete and store feedback and optional output."""
        self.task_result.status = TaskStatus.COMPLETED
        self.task_result.feedback = params.feedback
        if params.output is not None:
            self.task_result.output = params.output

        desc = f"Completed: {params.feedback}"
        if params.output is not None:
            try:
                import json

                output_str = json.dumps(params.output, indent=2, ensure_ascii=False)
                desc += f"\nOutput data:\n{output_str}"
            except (TypeError, ValueError):
                desc += f"\nOutput data: {params.output}"

        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=desc,
            terminal=True,
        )


class AbortWorkTool(Tool):
    """Signal that the worker cannot proceed further with the subtask."""

    name = "abort_work"
    description = "Signal that you cannot proceed further with this subtask (stuck, blocked, error, or impossible to complete)"

    class Params(BaseModel):
        """Parameters for abort_work tool."""

        reason: str = Field(
            description="Explain why you cannot continue and provide any relevant context about what went wrong or what is blocking you"
        )

    def __init__(self, task_result: "TaskResult"):
        """Initialize with reference to worker result."""
        self.task_result = task_result

    async def execute(self, params: Params) -> ToolResult:
        """Signal that work is aborted and store reason as feedback."""
        self.task_result.status = TaskStatus.ABORTED
        self.task_result.feedback = params.reason

        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Aborted: {params.reason}",
            terminal=True,
        )
