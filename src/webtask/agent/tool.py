"""Tool base class for agent tools."""

from pydantic import BaseModel


class Tool:
    """Base class for agent tools.

    Tools must define:
    - name: str - Tool identifier
    - description: str - What the tool does
    - Params: BaseModel - Nested Pydantic model for parameters
    - async execute(params: Params, **kwargs) -> None
    - @staticmethod describe(params: Params) -> str

    Example:
        class ClickTool(Tool):
            name = "click"
            description = "Click an element on the page"

            class Params(BaseModel):
                element_id: str = Field(description="ID of element to click")
                description: str = Field(description="What you're clicking")

            @staticmethod
            def describe(params: Params) -> str:
                return f"Clicked {params.description}"

            async def execute(self, params: Params) -> None:
                await browser.click(params.element_id)
    """

    name: str
    description: str
    Params: type[BaseModel]
    is_terminal: bool = False  # True for control tools that end execution

    def is_enabled(self) -> bool:
        """Check if tool should be available to LLM.

        Returns:
            True if tool should be shown (default), False to hide
        """
        return True

    @staticmethod
    def describe(params: BaseModel) -> str:
        """Generate human-readable description of tool action.

        Args:
            params: Validated Params instance

        Returns:
            Semantic description of the action
        """
        raise NotImplementedError("Tool must implement describe()")

    async def execute(self, params: BaseModel, **kwargs) -> None:
        """Execute the tool with validated parameters.

        Args:
            params: Validated Params instance
            **kwargs: Additional dependencies (browser, resources, etc.)
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")
