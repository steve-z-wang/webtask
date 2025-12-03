"""Agent tools organized by category."""

# DOM-based tools (element ID)
from .dom import ClickTool, UploadTool

# Pixel-based tools (screen coordinates)
from .pixel import (
    ClickAtTool,
    HoverAtTool,
    ScrollAtTool,
    ScrollDocumentTool,
    DragAndDropTool,
)

# Navigation and keyboard tools
from .navigation import (
    GotoTool,
    GoBackTool,
    GoForwardTool,
    SearchTool,
    KeyCombinationTool,
    KeyboardTypeTool,
)

# Tab management tools
from .tab import OpenTabTool, SwitchTabTool

# Control tools
from .control import CompleteWorkTool, AbortWorkTool

__all__ = [
    # DOM
    "ClickTool",
    "UploadTool",
    # Pixel
    "ClickAtTool",
    "HoverAtTool",
    "ScrollAtTool",
    "ScrollDocumentTool",
    "DragAndDropTool",
    # Navigation & Keyboard
    "GotoTool",
    "GoBackTool",
    "GoForwardTool",
    "SearchTool",
    "KeyCombinationTool",
    "KeyboardTypeTool",
    # Tab
    "OpenTabTool",
    "SwitchTabTool",
    # Control
    "CompleteWorkTool",
    "AbortWorkTool",
]
