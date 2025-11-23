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
        await self.browser.click_at(params.x, params.y)
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
        await self.browser.hover_at(params.x, params.y)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Hovered over {params.description}",
        )


class TypeTextAtTool(Tool):
    """Type text at screen coordinates."""

    name = "type_text_at"
    description = "Click at coordinates and type text"

    class Params(BaseModel):
        """Parameters for type_text_at tool."""

        x: int = Field(description="X coordinate (pixels)")
        y: int = Field(description="Y coordinate (pixels)")
        text: str = Field(description="Text to type")
        description: str = Field(
            description="What you're typing into (e.g., 'Search box', 'Email field')"
        )
        press_enter: bool = Field(default=True, description="Press Enter after typing")
        clear_before_typing: bool = Field(
            default=True, description="Clear existing text before typing"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize type_text_at tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute type at coordinates."""
        await self.browser.type_text_at(
            params.x,
            params.y,
            params.text,
            press_enter=params.press_enter,
            clear_before_typing=params.clear_before_typing,
        )
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Typed '{params.text}' into {params.description}",
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
        await self.browser.scroll_at(
            params.x, params.y, params.direction, params.magnitude
        )
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Scrolled {params.direction} on {params.description}",
        )


class ScrollDocumentTool(Tool):
    """Scroll the entire document."""

    name = "scroll_document"
    description = "Scroll the entire webpage"

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
        """Execute document scroll."""
        await self.browser.scroll_document(params.direction)
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
        await self.browser.drag_and_drop(
            params.x, params.y, params.dest_x, params.dest_y
        )
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Dragged: {params.description}",
        )
