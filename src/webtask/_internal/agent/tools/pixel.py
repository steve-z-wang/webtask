"""Pixel-based tools that use screen coordinates."""

from typing import Literal, TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


class ClickAtTool(Tool):
    """Click at screen coordinates."""

    name = "click_at"
    description = "Click at specific screen coordinates"

    class Params(BaseModel):
        """Parameters for click_at tool."""

        x: int = Field(description="X coordinate (pixels)")
        y: int = Field(description="Y coordinate (pixels)")
        description: str = Field(
            description="What you're clicking (e.g., 'Submit button', 'Login link')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize click_at tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute click at coordinates."""
        page = self.browser.get_current_page()
        x, y = self.browser.scale_coordinates(params.x, params.y)
        await page.mouse_click(x, y)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Clicked {params.description}",
        )


class HoverAtTool(Tool):
    """Hover at screen coordinates."""

    name = "hover_at"
    description = (
        "Hover at specific screen coordinates (useful for dropdowns, tooltips)"
    )

    class Params(BaseModel):
        """Parameters for hover_at tool."""

        x: int = Field(description="X coordinate (pixels)")
        y: int = Field(description="Y coordinate (pixels)")
        description: str = Field(
            description="What you're hovering over (e.g., 'Dropdown menu', 'Tooltip trigger')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize hover_at tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute hover at coordinates."""
        page = self.browser.get_current_page()
        x, y = self.browser.scale_coordinates(params.x, params.y)
        await page.mouse_move(x, y)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Hovered over {params.description}",
        )


class ScrollAtTool(Tool):
    """Scroll at specific screen coordinates."""

    name = "scroll_at"
    description = "Scroll at specific coordinates (useful for scrollable elements)"

    class Params(BaseModel):
        """Parameters for scroll_at tool."""

        x: int = Field(description="X coordinate (pixels)")
        y: int = Field(description="Y coordinate (pixels)")
        direction: Literal["up", "down", "left", "right"] = Field(
            description="Scroll direction"
        )
        description: str = Field(
            description="What you're scrolling (e.g., 'Product list', 'Chat history')"
        )
        magnitude: int = Field(default=800, description="Scroll amount in pixels")

    def __init__(self, browser: "AgentBrowser"):
        """Initialize scroll_at tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute scroll at coordinates."""
        page = self.browser.get_current_page()
        x, y = self.browser.scale_coordinates(params.x, params.y)
        delta_x, delta_y = 0, 0
        if params.direction == "up":
            delta_y = -params.magnitude
        elif params.direction == "down":
            delta_y = params.magnitude
        elif params.direction == "left":
            delta_x = -params.magnitude
        elif params.direction == "right":
            delta_x = params.magnitude
        await page.mouse_wheel(x, y, delta_x, delta_y)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Scrolled {params.direction} on {params.description}",
        )


class ScrollDocumentTool(Tool):
    """Scroll the entire document."""

    name = "scroll_document"
    description = "Scroll the entire webpage by 50% of viewport (maintains context, won't cut elements in half)"

    class Params(BaseModel):
        """Parameters for scroll_document tool."""

        direction: Literal["up", "down", "left", "right"] = Field(
            description="Scroll direction"
        )
        description: str = Field(
            description="Why you're scrolling (e.g., 'Scroll to see more results')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize scroll_document tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute document scroll using 50% viewport scroll."""
        page = self.browser.get_current_page()
        width, height = page.viewport_size()

        # Scroll by 50% of viewport to maintain context
        if params.direction == "down":
            await page.evaluate(f"window.scrollBy(0, {height // 2})")
        elif params.direction == "up":
            await page.evaluate(f"window.scrollBy(0, -{height // 2})")
        elif params.direction == "right":
            await page.evaluate(f"window.scrollBy({width // 2}, 0)")
        elif params.direction == "left":
            await page.evaluate(f"window.scrollBy(-{width // 2}, 0)")

        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Scrolled page {params.direction}: {params.description}",
        )


class DragAndDropTool(Tool):
    """Drag and drop between coordinates."""

    name = "drag_and_drop"
    description = "Drag from one position and drop at another"

    class Params(BaseModel):
        """Parameters for drag_and_drop tool."""

        x: int = Field(description="Start X coordinate (pixels)")
        y: int = Field(description="Start Y coordinate (pixels)")
        dest_x: int = Field(description="Destination X coordinate (pixels)")
        dest_y: int = Field(description="Destination Y coordinate (pixels)")
        description: str = Field(
            description="What you're dragging (e.g., 'Drag slider to 50%', 'Move file to folder')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize drag_and_drop tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute drag and drop."""
        page = self.browser.get_current_page()
        x, y = self.browser.scale_coordinates(params.x, params.y)
        dest_x, dest_y = self.browser.scale_coordinates(params.dest_x, params.dest_y)
        await page.mouse_drag(x, y, dest_x, dest_y)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Dragged: {params.description}",
        )
