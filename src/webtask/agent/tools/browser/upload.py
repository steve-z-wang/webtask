"""Upload tool for file uploads."""

from typing import Type, TYPE_CHECKING
from ...tool import Tool
from ...schemas import UploadParams

if TYPE_CHECKING:
    from ....llm_browser import LLMBrowser
    from ...task import Task


class UploadTool(Tool[UploadParams]):
    """Tool for uploading file resources to input elements."""

    def __init__(self, llm_browser: "LLMBrowser", task_context: "Task"):
        """
        Initialize upload tool.

        Args:
            llm_browser: LLMBrowser for element selection
            task_context: TaskContext for resource access
        """
        self.llm_browser = llm_browser
        self.task_context = task_context

    @property
    def name(self) -> str:
        return "upload"

    @property
    def description(self) -> str:
        return "Upload file resources to a file input element. Use resource names that were provided with the task."

    @property
    def params_class(self) -> Type[UploadParams]:
        return UploadParams

    async def execute(self, params: UploadParams):
        """Execute file upload."""
        # Resolve resource names to file paths
        paths = []
        for resource_name in params.resource_names:
            path = self.task_context.resources.get(resource_name)
            if path is None:
                raise ValueError(f"Resource not found: {resource_name}")
            paths.append(path)

        # Upload files (single file or multiple)
        await self.llm_browser.upload(
            params.element_id, paths if len(paths) > 1 else paths[0]
        )
