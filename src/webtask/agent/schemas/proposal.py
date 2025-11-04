"""Role schemas - unified schema for all agent roles."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List


class Action(BaseModel):
    """
    Unified action schema.

    LLM returns actions in this format. Each Tool validates its own parameters.

    Fields:
    - reason: Why this action is needed
    - tool: Tool name (matches Tool.name in ToolRegistry)
    - parameters: Tool-specific parameters as dict (validated by Tool)
    """

    reason: str = Field(description="Why this action is needed")
    tool: str = Field(description="Tool name")
    parameters: Dict[str, Any] = Field(description="Tool-specific parameters")


class RoleType(str, Enum):
    """Agent role types."""

    VERIFY = "VERIFY"
    PROPOSE = "PROPOSE"
    PLAN = "PLAN"


class Proposal(BaseModel):
    """
    Unified proposal schema for all agent roles.

    Each role proposes:
    - message: Explanation of reasoning
    - next_role: Which role should run next
    - actions: List of tool calls (role-specific tools)

    Side effects happen ONLY through tools:
    - PROPOSE role: navigate, click, fill, type, upload
    - VERIFY role: mark_complete
    - PLAN role: create_plan, update_plan
    """

    message: str = Field(description="Explanation of reasoning for these actions")
    actions: List[Action] = Field(
        default_factory=list, description="Actions to execute (role-specific tools)"
    )
    next_role: RoleType = Field(description="Which role should run next")
