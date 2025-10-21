"""Action - represents a tool invocation with parameters."""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class Action:
    """
    Represents an action to be executed.

    Pure data structure with tool name and parameters.
    """

    reason: str
    tool_name: str
    parameters: Dict[str, Any]
