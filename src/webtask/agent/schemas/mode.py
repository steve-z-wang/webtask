"""Mode schemas - unified schema for all agent modes."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from .actions import Action


class Mode(str, Enum):
    """Agent execution modes."""

    VERIFY = "VERIFY"
    PROPOSE = "PROPOSE"
    PLAN = "PLAN"


class Proposal(BaseModel):
    """
    Unified proposal schema for all agent roles.

    Each role proposes:
    - message: Explanation of reasoning
    - next_mode: Which mode should run next
    - actions: List of tool calls (role-specific tools)

    Side effects happen ONLY through tools:
    - PROPOSE mode: navigate, click, fill, type, upload
    - VERIFY mode: mark_complete
    - PLAN mode: create_plan, update_plan
    """

    message: str = Field(description="Explanation of reasoning for these actions")
    next_mode: Mode = Field(description="Which mode should run next")
    actions: List[Action] = Field(
        default_factory=list, description="Actions to execute (role-specific tools)"
    )
