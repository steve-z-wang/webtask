"""Proposal schema for LLM response."""

from pydantic import BaseModel, Field
from typing import List, Union, Literal
from .actions import Action


class Proposal(BaseModel):
    """Base proposal with common fields."""

    complete: bool = Field(description="Whether task is complete")
    message: str = Field(description="Status explanation")

    def get_actions(self) -> List[Action]:
        """Get actions - returns empty list for FinalProposal, actual actions for ActionProposal."""
        if isinstance(self, ActionProposal):
            return self.actions
        return []


class FinalProposal(Proposal):
    """Proposal when task is complete - no actions needed."""

    complete: Literal[True]


class ActionProposal(Proposal):
    """Proposal when task needs more actions."""

    complete: Literal[False]
    actions: List[Action] = Field(description="Actions to execute")


# Discriminated union - Pydantic will choose the right class based on 'complete' field
ProposalResponse = Union[FinalProposal, ActionProposal]
