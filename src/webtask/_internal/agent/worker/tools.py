"""Worker tools - all tools available to the worker."""

from typing import Dict, List, TYPE_CHECKING, Optional, Any
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool
from ...utils.wait import wait
from .worker_session import WorkerEndReason

if TYPE_CHECKING:
    from .worker_browser import WorkerBrowser
    from .worker import EndReason, OutputStorage


# Browser action tools


class NavigateTool(Tool):
    """Navigate to a URL."""

    name = "navigate"
    description = "Navigate to a URL"

    class Params(BaseModel):
        """Parameters for navigate tool."""

        url: str = Field(description="URL to navigate to")

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize navigate tool with worker browser."""
        self.worker_browser = worker_browser

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of navigation action."""
        return f"Navigated to {params.url}"

    async def execute(self, params: Params) -> None:
        """Execute navigation."""
        await self.worker_browser.navigate(params.url)


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

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize click tool with worker browser."""
        self.worker_browser = worker_browser

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of click action."""
        return f"Clicked {params.description}"

    async def execute(self, params: Params) -> None:
        """Execute click on element."""
        await self.worker_browser.click(params.element_id)


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

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize fill tool with worker browser."""
        self.worker_browser = worker_browser

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of fill action."""
        return f"Filled {params.description} with '{params.value}'"

    async def execute(self, params: Params) -> None:
        """Execute fill on element."""
        await self.worker_browser.fill(params.element_id, params.value)


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

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize type tool with worker browser."""
        self.worker_browser = worker_browser

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of type action."""
        return f"Typed '{params.text}' into {params.description}"

    async def execute(self, params: Params) -> None:
        """Execute type on element."""
        await self.worker_browser.type(params.element_id, params.text)


class UploadTool(Tool):
    """Upload file resources to a file input element."""

    name = "upload"
    description = "Upload file resources to a file input element. Use resource names that were provided with the task."

    class Params(BaseModel):
        """Parameters for upload tool."""

        element_id: str = Field(
            description="Element ID of the file input (e.g., 'input-5')"
        )
        resource_names: List[str] = Field(
            description="List of resource names to upload (e.g., ['photo1', 'photo2'])"
        )
        description: str = Field(
            description="Human-readable description of what file input you're uploading to (e.g., 'Profile photo upload', 'Document attachment field')"
        )

    def __init__(
        self,
        worker_browser: "WorkerBrowser",
        resources: Optional[Dict[str, str]] = None,
    ):
        """Initialize upload tool with worker browser and resources."""
        self.worker_browser = worker_browser
        self.resources = resources

    def is_enabled(self) -> bool:
        """Only enabled if resources are provided."""
        return self.resources is not None

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of upload action."""
        resources_str = ", ".join(params.resource_names)
        return f"Uploaded {resources_str} to {params.description}"

    async def execute(self, params: Params) -> None:
        """Execute file upload."""
        # Resolve resource names to file paths
        paths = []
        for resource_name in params.resource_names:
            path = self.resources.get(resource_name)
            if path is None:
                raise ValueError(f"Resource not found: {resource_name}")
            paths.append(path)

        # Upload files (single file or multiple)
        file_path = paths if len(paths) > 1 else paths[0]
        await self.worker_browser.upload(params.element_id, file_path)


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

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of wait action."""
        return f"Waited {params.seconds} seconds"

    async def execute(self, params: Params) -> None:
        """Wait for the specified duration."""
        await wait(params.seconds)


# Control tools


class SetOutputTool(Tool):
    """Store structured output data that will be returned to the user."""

    name = "set_output"
    description = "Store structured output data (dict, list, etc.) that will be returned to the user as the result"

    class Params(BaseModel):
        """Parameters for set_output tool."""

        data: Any = Field(
            description="Structured data to return (e.g., dict with extracted information, list of items, etc.)"
        )

    def __init__(self, output_storage: "OutputStorage"):
        """Initialize with reference to output storage wrapper."""
        self.output_storage = output_storage

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of set_output action."""
        # Convert data to readable string representation
        try:
            import json

            data_str = json.dumps(params.data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback to string representation
            data_str = str(params.data)

        return f"Set output data:\n{data_str}"

    async def execute(self, params: Params) -> None:
        """Store the output data."""
        self.output_storage.value = params.data


class CompleteWorkTool(Tool):
    """Signal that the worker has successfully completed the subtask."""

    name = "complete_work"
    description = "Signal that you have successfully completed the subtask"
    is_terminal = True

    class Params(BaseModel):
        """Parameters for complete_work tool."""

        feedback: str = Field(
            description="Describe what you accomplished and provide any important context or knowledge that might be useful for future subtasks in this task"
        )

    def __init__(self, end_reason: "EndReason"):
        """Initialize with reference to end_reason wrapper."""
        self.end_reason = end_reason

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of complete_work action."""
        return f"Completed work: {params.feedback}"

    async def execute(self, params: Params) -> None:
        """Signal that work is complete."""
        self.end_reason.value = WorkerEndReason.COMPLETE_WORK


class AbortWorkTool(Tool):
    """Signal that the worker cannot proceed further with the subtask."""

    name = "abort_work"
    description = "Signal that you cannot proceed further with this subtask (stuck, blocked, error, or impossible to complete)"
    is_terminal = True

    class Params(BaseModel):
        """Parameters for abort_work tool."""

        reason: str = Field(
            description="Explain why you cannot continue and provide any relevant context about what went wrong or what is blocking you"
        )

    def __init__(self, end_reason: "EndReason"):
        """Initialize with reference to end_reason wrapper."""
        self.end_reason = end_reason

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of abort_work action."""
        return f"Aborted work: {params.reason}"

    async def execute(self, params: Params) -> None:
        """Signal that work is aborted."""
        self.end_reason.value = WorkerEndReason.ABORT_WORK
