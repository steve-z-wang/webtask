"""Upload tool for file uploads."""

from typing import List
from pydantic import BaseModel, Field
from ...tool import Tool


class UploadTool(Tool):
    """Upload file resources to a file input element."""

    name = "upload"
    description = "Upload file resources to a file input element. Use resource names that were provided with the task."

    class Params(BaseModel):
        """Parameters for upload tool."""

        element_id: str = Field(description="Element ID of the file input (e.g., 'input-5')")
        resource_names: List[str] = Field(description="List of resource names to upload (e.g., ['photo1', 'photo2'])")

    async def execute(self, params: Params, **kwargs) -> str:
        """Execute file upload.

        Args:
            params: Validated parameters
            **kwargs: llm_browser and resources injected by ToolRegistry

        Returns:
            Success message
        """
        llm_browser = kwargs.get("llm_browser")
        resources = kwargs.get("resources", {})

        # Resolve resource names to file paths
        paths = []
        for resource_name in params.resource_names:
            path = resources.get(resource_name)
            if path is None:
                raise ValueError(f"Resource not found: {resource_name}")
            paths.append(path)

        # Upload files (single file or multiple)
        await llm_browser.upload(
            params.element_id, paths if len(paths) > 1 else paths[0]
        )

        return f"Uploaded {len(paths)} file(s) to element {params.element_id}"
