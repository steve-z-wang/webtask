"""Proposal schema for LLM response."""

from pydantic import BaseModel, Field
from typing import List
from .actions import Action


class Proposal(BaseModel):
    """Proposal from LLM with actions and completion status."""

    complete: bool = Field(description="Whether task is complete")
    message: str = Field(description="Status explanation")
    actions: List[Action] = Field(
        default_factory=list, description="Actions to execute"
    )
