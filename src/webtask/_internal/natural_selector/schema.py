"""Selector schema for LLM response."""

from pydantic import BaseModel, Field
from typing import Optional


class SelectorResponse(BaseModel):
    """Response from selector LLM."""

    interactive_id: Optional[str] = Field(None, description="Matching interactive ID")
    reasoning: Optional[str] = Field(
        None, description="Reasoning for element selection"
    )
    error: Optional[str] = Field(None, description="Error if no match found")
