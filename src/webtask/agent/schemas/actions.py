"""Action schemas for LLM responses - union by tool type."""

from pydantic import BaseModel, Field
from typing import Union, Literal, Annotated
from .params import ClickParams, FillParams, NavigateParams, TypeParams, UploadParams


# Action types - using nested parameters
class ClickAction(BaseModel):
    """Click action."""

    reason: str = Field(description="Why this action is needed")
    tool: Literal["click"] = Field(description="Tool name")
    parameters: ClickParams = Field(description="Click parameters")


class FillAction(BaseModel):
    """Fill action."""

    reason: str = Field(description="Why this action is needed")
    tool: Literal["fill"] = Field(description="Tool name")
    parameters: FillParams = Field(description="Fill parameters")


class NavigateAction(BaseModel):
    """Navigate action."""

    reason: str = Field(description="Why this action is needed")
    tool: Literal["navigate"] = Field(description="Tool name")
    parameters: NavigateParams = Field(description="Navigate parameters")


class TypeAction(BaseModel):
    """Type action."""

    reason: str = Field(description="Why this action is needed")
    tool: Literal["type"] = Field(description="Tool name")
    parameters: TypeParams = Field(description="Type parameters")


class UploadAction(BaseModel):
    """Upload action."""

    reason: str = Field(description="Why this action is needed")
    tool: Literal["upload"] = Field(description="Tool name")
    parameters: UploadParams = Field(description="Upload parameters")


# Union of all action types
# Discriminator needed for Pydantic deserialization (not used in LLM schema generation)
Action = Annotated[
    Union[ClickAction, FillAction, NavigateAction, TypeAction, UploadAction],
    Field(discriminator="tool"),
]
