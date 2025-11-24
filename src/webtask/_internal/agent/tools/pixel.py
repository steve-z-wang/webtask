"""Pixel-based tools that use screen coordinates."""

from typing import Literal, TYPE_CHECKING
from dodo import tool

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


@tool
class ClickAtTool:
    """Click at specific screen coordinates."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, x: int, y: int, description: str) -> str:
        """
        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
            description: What you're clicking (e.g., 'Submit button', 'Login link')
        """
        page = self.browser.get_current_page()
        scaled_x, scaled_y = self.browser.scale_coordinates(x, y)
        await page.mouse_click(scaled_x, scaled_y)
        await self.browser.wait()
        return f"Clicked {description}"


@tool
class HoverAtTool:
    """Hover at specific screen coordinates (useful for dropdowns, tooltips)."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, x: int, y: int, description: str) -> str:
        """
        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
            description: What you're hovering over (e.g., 'Dropdown menu', 'Tooltip trigger')
        """
        page = self.browser.get_current_page()
        scaled_x, scaled_y = self.browser.scale_coordinates(x, y)
        await page.mouse_move(scaled_x, scaled_y)
        await self.browser.wait()
        return f"Hovered over {description}"


@tool
class TypeTextAtTool:
    """Click at coordinates and type text."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(
        self,
        x: int,
        y: int,
        text: str,
        description: str,
        press_enter: bool = True,
        clear_before_typing: bool = True,
    ) -> str:
        """
        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
            text: Text to type
            description: What you're typing into (e.g., 'Search box', 'Email field')
            press_enter: Press Enter after typing
            clear_before_typing: Clear existing text before typing
        """
        page = self.browser.get_current_page()
        scaled_x, scaled_y = self.browser.scale_coordinates(x, y)
        await page.mouse_click(scaled_x, scaled_y)
        if clear_before_typing:
            await page.keyboard_press("Control+a")
            await page.keyboard_press("Backspace")
        await page.keyboard_type(text)
        if press_enter:
            await page.keyboard_press("Enter")
        await self.browser.wait()
        return f"Typed '{text}' into {description}"


@tool
class ScrollAtTool:
    """Scroll at specific coordinates (useful for scrollable elements)."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        description: str,
        magnitude: int = 800,
    ) -> str:
        """
        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)
            direction: Scroll direction
            description: What you're scrolling (e.g., 'Product list', 'Chat history')
            magnitude: Scroll amount in pixels
        """
        page = self.browser.get_current_page()
        scaled_x, scaled_y = self.browser.scale_coordinates(x, y)
        delta_x, delta_y = 0, 0
        if direction == "up":
            delta_y = -magnitude
        elif direction == "down":
            delta_y = magnitude
        elif direction == "left":
            delta_x = -magnitude
        elif direction == "right":
            delta_x = magnitude
        await page.mouse_wheel(scaled_x, scaled_y, delta_x, delta_y)
        await self.browser.wait()
        return f"Scrolled {direction} on {description}"


@tool
class ScrollDocumentTool:
    """Scroll the entire webpage."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(
        self, direction: Literal["up", "down", "left", "right"], description: str
    ) -> str:
        """
        Args:
            direction: Scroll direction
            description: Why you're scrolling (e.g., 'Scroll to see more results')
        """
        page = self.browser.get_current_page()
        key = {
            "up": "PageUp",
            "down": "PageDown",
            "left": "Home",
            "right": "End",
        }.get(direction, "PageDown")
        await page.keyboard_press(key)
        await self.browser.wait()
        return f"Scrolled page {direction}: {description}"


@tool
class DragAndDropTool:
    """Drag from one position and drop at another."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(
        self, x: int, y: int, dest_x: int, dest_y: int, description: str
    ) -> str:
        """
        Args:
            x: Start X coordinate (pixels)
            y: Start Y coordinate (pixels)
            dest_x: Destination X coordinate (pixels)
            dest_y: Destination Y coordinate (pixels)
            description: What you're dragging (e.g., 'Drag slider to 50%', 'Move file to folder')
        """
        page = self.browser.get_current_page()
        scaled_x, scaled_y = self.browser.scale_coordinates(x, y)
        scaled_dest_x, scaled_dest_y = self.browser.scale_coordinates(dest_x, dest_y)
        await page.mouse_drag(scaled_x, scaled_y, scaled_dest_x, scaled_dest_y)
        await self.browser.wait()
        return f"Dragged: {description}"
