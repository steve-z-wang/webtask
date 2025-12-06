"""Agent tools organized by category."""

# DOM-based tools (element ID)
from .dom import ClickTool, TypeTool, UploadTool

# Pixel-based tools (screen coordinates)
from .pixel import (
    ClickAtTool,
    TypeAtTool,
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
)

# Tab management tools
from .tab import OpenTabTool, SwitchTabTool

# Control tools
from .control import CompleteWorkTool, AbortWorkTool

__all__ = [
    # DOM
    "ClickTool",
    "TypeTool",
    "UploadTool",
    # Pixel
    "ClickAtTool",
    "TypeAtTool",
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
    # Tab
    "OpenTabTool",
    "SwitchTabTool",
    # Control
    "CompleteWorkTool",
    "AbortWorkTool",
]
