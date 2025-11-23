"""Tool base class for agent tools."""

from abc import ABC, abstractmethod
from pydantic import BaseModel

from webtask.llm.message import ToolResult


class Tool(ABC):
    """Base class for agent tools.

    Tools must define:
    - name: str - Tool identifier
    - description: str - What the tool does
    - Params: BaseModel - Nested Pydantic model for parameters
    - async execute(params: Params) -> ToolResult

    Example:
        class ClickTool(Tool):
            name = "click"
            description = "Click an element on the page"

            class Params(BaseModel):
                element_id: str = Field(description="ID of element to click")
                description: str = Field(description="What you're clicking")

            async def execute(self, params: Params) -> ToolResult:
                await self.browser.click(params.element_id)
                return ToolResult(
                    name=self.name,
                    status=ToolResultStatus.SUCCESS,
                    description=f"Clicked {params.description}",
                )
    """

    name: str
    description: str
    Params: type[BaseModel]

    @abstractmethod
    async def execute(self, params: BaseModel) -> ToolResult:
        """Execute the tool with validated parameters.

        Args:
            params: Validated Params instance

        Returns:
            ToolResult with status, description, and optional terminal flag
        """
        pass
