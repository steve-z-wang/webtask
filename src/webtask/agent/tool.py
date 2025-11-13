"""Tool base class for agent tools."""

from typing import Any
from pydantic import BaseModel


class Tool:
    """Base class for agent tools.

    Tools must define:
    - name: str - Tool identifier
    - description: str - What the tool does
    - Params: BaseModel - Nested Pydantic model for parameters
    - async execute(params: Params, **kwargs) -> Any

    Example:
        class ClickTool(Tool):
            name = "click"
            description = "Click an element on the page"

            class Params(BaseModel):
                element_id: str = Field(description="ID of element to click")

            async def execute(self, params: Params, browser) -> None:
                await browser.click(params.element_id)
    """

    name: str
    description: str
    Params: type[BaseModel]

    async def execute(self, params: BaseModel, **kwargs) -> Any:
        """Execute the tool with validated parameters.

        Args:
            params: Validated Params instance
            **kwargs: Additional dependencies (browser, resources, etc.)

        Returns:
            Tool execution result
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")
