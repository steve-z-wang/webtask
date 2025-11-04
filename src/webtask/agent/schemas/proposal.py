"""Proposal schema for LLM response."""

from pydantic import BaseModel, Field
from typing import List, Union, Literal
from .actions import Action


class Proposal(BaseModel):
    """Base proposal with common fields."""

    complete: bool = Field(description="Whether task is complete")
    message: str = Field(description="Status explanation")


class FinalProposal(Proposal):
    """Proposal when task is complete - no actions needed."""

    complete: Literal[True]

    @property
    def actions(self) -> List[Action]:
        """Always returns empty list for FinalProposal."""
        return []


class ActionProposal(Proposal):
    """Proposal when task needs more actions."""

    complete: Literal[False]
    actions: List[Action] = Field(description="Actions to execute")


# Discriminated union - Pydantic will choose the right class based on 'complete' field
ProposalResponse = Union[FinalProposal, ActionProposal]
