"""Agent tools organized by category."""

# DOM-based tools (element ID)
from .dom import ClickTool, FillTool, TypeTool, UploadTool

# Navigation tools
from .navigation import GotoTool

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
    # Navigation
    "GotoTool",
    # Tab
    "OpenTabTool",
    "SwitchTabTool",
    # Utility
    "WaitTool",
    # Control
    "CompleteWorkTool",
    "AbortWorkTool",
]
