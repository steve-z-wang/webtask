"""Agent tools organized by category."""

# DOM-based tools (element ID)
from .dom import ClickTool, FillTool, TypeTool, UploadTool

# Pixel-based tools (screen coordinates)
from .pixel import (
    ClickAtTool,
    HoverAtTool,
    TypeTextAtTool,
    ScrollAtTool,
    ScrollDocumentTool,
    DragAndDropTool,
)

# Navigation tools
from .navigation import (
    GotoTool,
    GoBackTool,
    GoForwardTool,
    SearchTool,
    KeyCombinationTool,
)

# Tab management tools
from .tab import OpenTabTool, SwitchTabTool

# Utility tools
from .utility import WaitTool

# Control tools
from .control import CompleteWorkTool, AbortWorkTool

__all__ = [
    # DOM
    "ClickTool",
    "FillTool",
    "TypeTool",
    "UploadTool",
    # Pixel
    "ClickAtTool",
    "HoverAtTool",
    "TypeTextAtTool",
    "ScrollAtTool",
    "ScrollDocumentTool",
    "DragAndDropTool",
    # Navigation
    "GotoTool",
    "GoBackTool",
    "GoForwardTool",
    "SearchTool",
    "KeyCombinationTool",
    # Tab
    "OpenTabTool",
    "SwitchTabTool",
    # Utility
    "WaitTool",
    # Control
    "CompleteWorkTool",
    "AbortWorkTool",
]
