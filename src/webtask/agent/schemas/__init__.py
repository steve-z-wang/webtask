"""LLM response schemas - all Pydantic models for structured LLM outputs."""

from .params import (
    ToolParams,
    ClickParams,
    FillParams,
    NavigateParams,
    TypeParams,
    UploadParams,
)
from .actions import (
    Action,
    ClickAction,
    FillAction,
    NavigateAction,
    TypeAction,
    UploadAction,
)
from .proposal import Proposal
from .selector import SelectorResponse

__all__ = [
    # Base class
    "ToolParams",
    # Action union and types
    "Action",
    "ClickAction",
    "FillAction",
    "NavigateAction",
    "TypeAction",
    "UploadAction",
    # Parameter types
    "ClickParams",
    "FillParams",
    "NavigateParams",
    "TypeParams",
    "UploadParams",
    # Response models
    "Proposal",
    "SelectorResponse",
]
