"""Mode schemas - Mode enum and all mode result classes."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from .actions import Action


class Mode(str, Enum):
    """Agent execution modes."""

    VERIFY = "VERIFY"
    PROPOSE = "PROPOSE"
    # PLAN = "PLAN"


class ModeResult(BaseModel):
    """
    Base class for all mode results.

    All modes must return a result with:
    - message: Explanation of what happened
    - next_mode: Which mode should run next
    """

    message: str = Field(description="Explanation of what happened in this mode")
    next_mode: Mode = Field(description="Which mode should run next")


class VerifyResult(ModeResult):
    """Result from verify mode - checks if task is complete."""

    complete: bool = Field(description="Whether the task is complete")


class ProposeResult(ModeResult):
    """Result from propose mode - suggests actions to take."""

    actions: List[Action] = Field(description="Actions to execute")
