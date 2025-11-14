"""Upload tool for file uploads."""

from typing import List, Dict, TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool

if TYPE_CHECKING:
    from ..worker_browser import WorkerBrowser


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

    def __init__(self, worker_browser: "WorkerBrowser", resources: Dict[str, str]):
        """Initialize upload tool with worker browser and resources."""
        self.worker_browser = worker_browser
        self.resources = resources

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
        element = await self.worker_browser.select(params.element_id)
        await element.upload_file(paths if len(paths) > 1 else paths[0])
